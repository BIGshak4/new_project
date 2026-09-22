"""LLM providers behind one small interface.

    ScriptedProvider   canned replies, for tests and persona runs
    ManualProvider     writes each prompt to a file and waits for a reply file, so the
                       whole loop can run (and be inspected) before an API key exists
    AnthropicProvider  Claude Opus 5, effort per engine role, prompt caching, refusal handling

The engine never talks to an SDK directly. Swapping providers is configuration.
"""

from __future__ import annotations

import asyncio
import base64
import json
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, ValidationError

# Effort per engine role (MVP_Build_Guide §7.1). One model keeps one prompt cache.
# feedback measured on the real model (2026-09-19): low effort gives the same card in ~10 s instead of ~16 s
ROLE_EFFORT = {"evaluator": "low", "generator": "medium", "tip": "low", "report": "medium", "feedback": "low"}
ROLE_MAX_TOKENS = {"evaluator": 8000, "generator": 8000, "tip": 2000, "report": 4000, "feedback": 2000}

# USD per million tokens. Cache reads bill at 0.1x input, cache writes at 1.25x.
PRICES = {"claude-opus-5": (5.00, 25.00), "claude-sonnet-5": (2.00, 10.00), "claude-haiku-4-5": (1.00, 5.00)}


class LLMError(Exception):
    """The call failed. `retryable` tells the caller whether trying again can help."""

    def __init__(self, message: str, *, retryable: bool = False):
        super().__init__(message)
        self.retryable = retryable


class LLMRefusal(LLMError):
    """The model (or a safety classifier) declined. Never retried on the same model."""


@dataclass
class LLMUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0

    def cost_usd(self, model: str) -> float | None:
        """Estimated cost, or None when the model's price is not known. Unknown is never treated as free."""
        if model not in PRICES:
            return None
        price_in, price_out = PRICES[model]
        return round((self.input_tokens * price_in + self.cache_read_tokens * price_in * 0.1
                      + self.cache_write_tokens * price_in * 1.25 + self.output_tokens * price_out) / 1_000_000, 6)


@dataclass
class LLMRequest:
    role: str                                   # evaluator | generator | tip | feedback | report
    system: list[str]                           # stable blocks, most stable first; the last one is the cache breakpoint
    user: str                                   # everything that changes per call
    schema: type[BaseModel] | None = None       # structured output when set
    prompt_version: str = ""
    effort: str | None = None
    max_tokens: int | None = None
    images: list[tuple[str, bytes]] = field(default_factory=list)   # (mime, bytes) the model should look at

    def resolved_effort(self) -> str:
        return self.effort or ROLE_EFFORT.get(self.role, "medium")

    def resolved_max_tokens(self) -> int:
        return self.max_tokens or ROLE_MAX_TOKENS.get(self.role, 8000)


@dataclass
class LLMResponse:
    text: str
    parsed: BaseModel | None = None
    usage: LLMUsage = field(default_factory=LLMUsage)
    model: str = ""
    latency_ms: int = 0
    stop_reason: str | None = None


class Provider(Protocol):
    name: str
    model: str

    async def complete(self, request: LLMRequest) -> LLMResponse: ...


# A model call that never returns must not hold a user forever. The SDK has its own timeout;
# this one also covers the manual provider and anything a future provider might do.
CALL_TIMEOUT_SECONDS: dict[str, float] = {"evaluator": 90, "generator": 60, "tip": 30, "feedback": 60, "report": 90}


async def call(provider: Provider, request: LLMRequest, *, timeout_seconds: float | None = None) -> LLMResponse:
    """provider.complete() with a role-appropriate deadline. A timeout is a retryable LLMError."""
    timeout = timeout_seconds or CALL_TIMEOUT_SECONDS.get(request.role, 120)
    if getattr(provider, "name", "") == "manual":
        timeout = max(timeout, getattr(provider, "timeout_seconds", timeout))     # a person is typing the reply
    try:
        return await asyncio.wait_for(provider.complete(request), timeout=timeout)
    except TimeoutError as exc:
        raise LLMError(f"{request.role} call exceeded {timeout:.0f}s", retryable=True) from exc


def _parse(schema: type[BaseModel], text: str) -> BaseModel:
    """Validate a JSON reply. Tolerates a fenced ```json block, which people paste in manual mode."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
        cleaned = cleaned.rsplit("```", 1)[0]
    try:
        return schema.model_validate_json(cleaned)
    except ValidationError as exc:
        raise LLMError(f"reply did not match {schema.__name__}: {exc.errors()[:3]}", retryable=True) from exc


# ----------------------------------------------------------------------------- scripted


Reply = str | dict | BaseModel
Responder = Callable[[LLMRequest], Reply | Awaitable[Reply]]


class ScriptedProvider:
    """Replies from a function or a queue. Records every request for assertions."""

    name = "scripted"
    model = "scripted"

    def __init__(self, responder: Responder | list[Reply]):
        self._responder = responder
        self.requests: list[LLMRequest] = []

    async def complete(self, request: LLMRequest) -> LLMResponse:
        self.requests.append(request)
        if callable(self._responder):
            reply = self._responder(request)
            if asyncio.iscoroutine(reply):
                reply = await reply
        else:
            if not self._responder:
                raise LLMError("scripted provider ran out of replies")
            reply = self._responder.pop(0)
        if isinstance(reply, Exception):
            raise reply
        if isinstance(reply, BaseModel):
            return LLMResponse(text=reply.model_dump_json(), parsed=reply, model=self.model)
        text = json.dumps(reply, ensure_ascii=False) if isinstance(reply, dict) else str(reply)
        parsed = _parse(request.schema, text) if request.schema else None
        return LLMResponse(text=text, parsed=parsed, model=self.model)


# ----------------------------------------------------------------------------- manual


class ManualProvider:
    """Human-in-the-loop provider.

    Each call writes `NNN_<role>.request.md` into `directory` and waits for
    `NNN_<role>.response.json` (structured) or `.response.md` (text). Whoever plays
    the model reads the request and writes the reply file.
    """

    name = "manual"
    model = "manual"

    def __init__(self, directory: Path, *, poll_seconds: float = 1.0, timeout_seconds: float = 3600.0,
                 on_wait: Callable[[Path, Path], None] | None = None):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.poll_seconds = poll_seconds
        self.timeout_seconds = timeout_seconds
        self.on_wait = on_wait
        self._counter = len(list(self.directory.glob("*.request.md")))

    async def complete(self, request: LLMRequest) -> LLMResponse:
        self._counter += 1
        stem = f"{self._counter:03d}_{request.role}"
        request_path = self.directory / f"{stem}.request.md"
        suffix = "json" if request.schema else "md"
        response_path = self.directory / f"{stem}.response.{suffix}"

        parts = [f"# {request.role} request {self._counter:03d}",
                 f"prompt_version: {request.prompt_version} | effort: {request.resolved_effort()}"]
        for index, block in enumerate(request.system, start=1):
            parts.append(f"\n## system block {index}\n\n{block}")
        parts.append(f"\n## user\n\n{request.user}")
        if request.schema:
            parts.append("\n## reply format\n\nWrite JSON matching this schema to "
                         f"`{response_path.name}`:\n\n```json\n"
                         f"{json.dumps(request.schema.model_json_schema(), indent=1)}\n```")
        else:
            parts.append(f"\n## reply format\n\nWrite plain text to `{response_path.name}`.")
        request_path.write_text("\n".join(parts), encoding="utf-8")

        if self.on_wait:
            self.on_wait(request_path, response_path)
        started = time.perf_counter()
        while not response_path.exists():
            if time.perf_counter() - started > self.timeout_seconds:
                raise LLMError(f"no reply written to {response_path} within {self.timeout_seconds:.0f}s", retryable=True)
            await asyncio.sleep(self.poll_seconds)
        await asyncio.sleep(0.2)                       # let the writer finish
        text = response_path.read_text(encoding="utf-8")
        parsed = _parse(request.schema, text) if request.schema else None
        return LLMResponse(text=text, parsed=parsed, model=self.model,
                           latency_ms=int((time.perf_counter() - started) * 1000))


# ----------------------------------------------------------------------------- anthropic


class AnthropicProvider:
    """Claude through the official SDK.

    * One model for every engine role, effort tuned per role, so all roles share a prompt cache.
    * System blocks are sent most-stable-first with a cache breakpoint on the last one;
      everything per-call goes in the user message (MVP_Build_Guide §7.2).
    * `stop_reason` is checked before content is read. Server-side fallbacks
      (`fallbacks: "default"`) are on unless disabled, so a classifier false positive
      on a hardware question does not break a session.
    * Thinking is left at the model default (adaptive on Opus 5); effort controls depth.
    """

    name = "anthropic"
    FALLBACK_BETA = "server-side-fallback-2026-07-01"

    def __init__(self, *, model: str = "claude-opus-5", api_key: str | None = None,
                 enable_fallbacks: bool = True, timeout_seconds: float = 120.0, max_retries: int = 2,
                 role_models: dict[str, str] | None = None):
        import anthropic

        self._anthropic = anthropic
        self.model = model                                    # the judge (evaluator) and any role not listed below
        # cheaper models for the prose roles: the card and the tip only reword a judgement already made
        self.role_models = dict(role_models or {})
        self.enable_fallbacks = enable_fallbacks
        self._schema_unsupported = False
        self.client = anthropic.AsyncAnthropic(api_key=api_key, timeout=timeout_seconds, max_retries=max_retries)

    def model_for(self, role: str) -> str:
        return self.role_models.get(role, self.model)

    def _system_blocks(self, request: LLMRequest) -> list[dict]:
        """Two cache points: the role's instructions (shared by every question) and the question block
        (shared by everyone answering that question). A breakpoint only on the last block would cache the
        pair as one unit, so the instructions would be re-sent for every new question."""
        blocks = [{"type": "text", "text": text} for text in request.system if text]
        if blocks:
            blocks[0]["cache_control"] = {"type": "ephemeral"}
            blocks[-1]["cache_control"] = {"type": "ephemeral"}
        return blocks

    def _extras(self) -> dict:
        if not self.enable_fallbacks:
            return {}
        return {"extra_headers": {"anthropic-beta": self.FALLBACK_BETA}, "extra_body": {"fallbacks": "default"}}

    async def _send(self, request: LLMRequest, common: dict):
        """One API call, with two one-way downgrades for account/feature mismatches:
        a 400 that names the fallbacks beta disables fallbacks for this process; a 400 that
        rejects the structured-output schema switches structured requests to JSON-in-text."""
        anthropic = self._anthropic
        try:
            if request.schema is not None and not self._schema_unsupported:
                return await self.client.messages.parse(output_format=request.schema, **common)
            if request.schema is not None:
                common = {**common, "messages": [{"role": "user",
                                                  "content": self._user_content(request, self._json_instruction(request))}]}
            async with self.client.messages.stream(**common) as stream:
                return await stream.get_final_message()
        except anthropic.APIStatusError as exc:
            text = str(getattr(exc, "message", exc)).lower()
            if exc.status_code == 400 and self.enable_fallbacks and ("fallback" in text or "beta" in text):
                self.enable_fallbacks = False                       # this account has no fallbacks beta: go without
                common = {k: v for k, v in common.items() if k not in ("extra_headers", "extra_body")}
                return await self._send(request, common)
            if exc.status_code == 400 and request.schema is not None and not self._schema_unsupported \
                    and ("output_format" in text or "schema" in text or "structured" in text):
                self._schema_unsupported = True                     # ask for JSON in the text instead
                return await self._send(request, common)
            raise

    @staticmethod
    def _json_instruction(request: LLMRequest) -> str:
        return ("\n\nReply with a single JSON object and nothing else, matching this JSON schema exactly:\n"
                + json.dumps(request.schema.model_json_schema()))

    @staticmethod
    def _user_content(request: LLMRequest, suffix: str = ""):
        """Plain text, or image blocks followed by the text when the answer includes photos or drawings."""
        text = request.user + suffix
        if not request.images:
            return text
        blocks = [{"type": "image", "source": {"type": "base64", "media_type": mime,
                                               "data": base64.b64encode(data).decode("ascii")}}
                  for mime, data in request.images]
        return [*blocks, {"type": "text", "text": text}]

    async def complete(self, request: LLMRequest) -> LLMResponse:
        anthropic = self._anthropic
        started = time.perf_counter()
        common = dict(
            model=self.model_for(request.role), max_tokens=request.resolved_max_tokens(), system=self._system_blocks(request),
            messages=[{"role": "user", "content": self._user_content(request)}],
            output_config={"effort": request.resolved_effort()}, **self._extras(),
        )
        try:
            message = await self._send(request, common)
        except anthropic.RateLimitError as exc:
            raise LLMError(f"rate limited: {exc.message}", retryable=True) from exc
        except anthropic.APIStatusError as exc:
            raise LLMError(f"API error {exc.status_code}: {exc.message}", retryable=exc.status_code >= 500) from exc
        except anthropic.APIConnectionError as exc:
            raise LLMError(f"connection error: {exc}", retryable=True) from exc

        if message.stop_reason == "refusal":
            category = getattr(getattr(message, "stop_details", None), "category", None)
            raise LLMRefusal(f"request declined (category: {category})")

        text = "".join(block.text for block in message.content if block.type == "text")
        parsed = None
        if request.schema is not None:
            parsed = getattr(message, "parsed_output", None)
            if parsed is None:
                if message.stop_reason == "max_tokens":
                    raise LLMError("structured reply was cut off by max_tokens", retryable=True)
                parsed = _parse(request.schema, text)
        usage = LLMUsage(
            input_tokens=message.usage.input_tokens or 0, output_tokens=message.usage.output_tokens or 0,
            cache_read_tokens=getattr(message.usage, "cache_read_input_tokens", 0) or 0,
            cache_write_tokens=getattr(message.usage, "cache_creation_input_tokens", 0) or 0,
        )
        return LLMResponse(text=text, parsed=parsed, usage=usage, model=message.model,
                           latency_ms=int((time.perf_counter() - started) * 1000), stop_reason=message.stop_reason)


def build_provider(kind: str, *, manual_dir: Path | None = None, **kwargs) -> Provider:
    if kind == "anthropic":
        return AnthropicProvider(**kwargs)
    if kind == "manual":
        return ManualProvider(manual_dir or Path("workdir/manual_llm"))
    raise ValueError(f"unknown provider {kind!r} (expected 'anthropic' or 'manual')")
