"""LLM providers behind one small interface.

    ScriptedProvider   canned replies, for tests and persona runs
    ManualProvider     writes each prompt to a file and waits for a reply file, so the
                       whole loop can run (and be inspected) before an API key exists
    OpenAIProvider     the real provider: GPT through the Responses API, reasoning effort per engine role,
                       prefix caching, structured output, refusal handling
    AnthropicProvider  the fallback: Claude, effort per engine role, prompt caching, refusal handling

The engine never talks to an SDK directly. Swapping providers is configuration (LLM_PROVIDER).
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
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

# USD per million tokens. Anthropic: cache reads bill at 0.1x input, cache writes at 1.25x.
PRICES = {"claude-opus-5-5": (4.00, 20.00), "claude-opus-5": (5.00, 25.00), "claude-sonnet-5": (2.00, 10.00), "claude-haiku-4-5": (1.00, 5.00)}
# OpenAI (developers.openai.com/api/docs/pricing, read 2026-10-29): (input, cached input, output); no cache-write charge.
OPENAI_PRICES = {"gpt-6-astra": (10.00, 1.00, 50.00), "gpt-6.1-sol": (2.00, 0.10, 10.00), "gpt-6.1-terra": (1.00, 0.05, 5.00),
                 "gpt-6-luna": (0.10, 0.01, 0.50), "gpt-6-sol": (2.00, 0.20, 10.00), "gpt-5.6-sol": (4.00, 0.40, 20.00),
                 "gpt-5.6-terra": (2.00, 0.20, 12.00), "gpt-5.6-luna": (0.20, 0.02, 1.20), "gpt-5.5": (5.00, 0.50, 30.00),
                 "gpt-5.4": (2.50, 0.25, 15.00), "gpt-5.4-mini": (0.75, 0.075, 4.50), "gpt-5.4-nano": (0.20, 0.02, 1.25)}


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
        base = _openai_base(model)
        if base in OPENAI_PRICES:                                 # input_tokens here excludes the cached part
            price_in, price_cached, price_out = OPENAI_PRICES[base]
            return round((self.input_tokens * price_in + self.cache_read_tokens * price_cached
                          + self.output_tokens * price_out) / 1_000_000, 6)
        if model not in PRICES:
            return None
        price_in, price_out = PRICES[model]
        return round((self.input_tokens * price_in + self.cache_read_tokens * price_in * 0.1
                      + self.cache_write_tokens * price_in * 1.25 + self.output_tokens * price_out) / 1_000_000, 6)


def _openai_base(model: str) -> str:
    """'gpt-6.1-sol-2026-09-01' prices as 'gpt-6.1-sol': the dated snapshot the API reports back."""
    if model in OPENAI_PRICES:
        return model
    for known in sorted(OPENAI_PRICES, key=len, reverse=True):
        if model.startswith(known + "-"):
            return known
    return model


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
                    and ("output_format" in text or "schema" in text or "structured" in text or "grammar" in text):   # "compiled grammar is too large" = the schema is too big for structured output
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
        except ValidationError as exc:
            # the SDK parses the structured reply itself; malformed JSON (a trailing comma, seen from Sonnet 5 on
            # 2026-10-03) is retried like any other bad reply instead of escaping as a crash (same rule as _parse)
            raise LLMError(f"structured reply did not parse as {request.schema.__name__ if request.schema else 'JSON'}: "
                           f"{exc.errors()[:2]}", retryable=True) from exc

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


class OpenAIProvider:
    """OpenAI through the official SDK's Responses API, behind the same interface as the Anthropic provider
    (Shaked, 2026-10-29: "change the api key to open ai key").

    * The system blocks go in `instructions`, most stable first, so OpenAI's automatic prefix cache catches the
      role's instructions and the question block; `prompt_cache_key` groups a role's calls on one cache.
    * Structured replies use `responses.parse` with the pydantic schema (strict JSON schema). An account or model
      that rejects the schema switches, once per process, to JSON-in-text with the schema in the prompt.
    * The per-role effort maps straight onto `reasoning.effort` (the same words); reasoning tokens bill as output.
    * `status == "incomplete"` is checked before content is read: a cut-off reply is retried, a content filter
      is a refusal (never retried), like `stop_reason` on the Anthropic side.
    * Usage: OpenAI counts cached tokens inside `input_tokens`; they are split out so `LLMUsage` keeps one
      meaning across providers (input = uncached input).
    """

    name = "openai"

    def __init__(self, *, model: str = "gpt-6.1-sol", api_key: str | None = None, timeout_seconds: float = 120.0,
                 max_retries: int = 2, role_models: dict[str, str] | None = None):
        import openai

        self._openai = openai
        self.model = model                                    # the judge (evaluator) and any role not listed below
        self.role_models = dict(role_models or {})            # cheaper models for the prose roles
        self._schema_unsupported = False
        api_key = api_key or os.environ.get("OPENAI_API_KEY") or None       # an empty OPENAI_API_KEY= line is no key
        if api_key is None:
            # No key in the settings and none in the environment. The Anthropic SDK accepts that and fails at the
            # first request; this SDK raises at construction, which would take down app startup, /health and every
            # script. Same behaviour as the other side: the app comes up, the first model call fails with a clear reason.
            self.client = None
        else:
            self.client = openai.AsyncOpenAI(api_key=api_key, timeout=timeout_seconds, max_retries=max_retries)

    def model_for(self, role: str) -> str:
        return self.role_models.get(role, self.model)

    @staticmethod
    def _instructions(request: LLMRequest) -> str:
        return "\n\n".join(text for text in request.system if text)

    @staticmethod
    def _json_instruction(request: LLMRequest) -> str:
        return ("\n\nReply with a single JSON object and nothing else, matching this JSON schema exactly:\n"
                + json.dumps(request.schema.model_json_schema()))

    @staticmethod
    def _input(request: LLMRequest, suffix: str = ""):
        """Plain text, or the images followed by the text when the answer includes photos or drawings."""
        text = request.user + suffix
        if not request.images:
            return text
        parts = [{"type": "input_image", "detail": "auto",
                  "image_url": f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"} for mime, data in request.images]
        return [{"role": "user", "content": [*parts, {"type": "input_text", "text": text}]}]

    async def _send(self, request: LLMRequest, common: dict):
        """One API call; a 400 that rejects the structured-output schema switches, for this process, to JSON in text."""
        openai = self._openai
        try:
            if request.schema is not None and not self._schema_unsupported:
                return await self.client.responses.parse(text_format=request.schema, **common)
            if request.schema is not None:
                common = {**common, "input": self._input(request, self._json_instruction(request)),
                          "text": {"format": {"type": "json_object"}}}
            return await self.client.responses.create(**common)
        except openai.BadRequestError as exc:
            text = str(getattr(exc, "message", exc)).lower()
            if request.schema is not None and not self._schema_unsupported and ("schema" in text or "structured" in text
                                                                                 or "text_format" in text or "format" in text):
                self._schema_unsupported = True
                return await self._send(request, common)
            raise

    async def complete(self, request: LLMRequest) -> LLMResponse:
        if self.client is None:
            raise LLMError("OPENAI_API_KEY is not set (put it in backend/.env or the host's environment)", retryable=False)
        openai = self._openai
        started = time.perf_counter()
        common = dict(model=self.model_for(request.role), instructions=self._instructions(request), input=self._input(request),
                      max_output_tokens=request.resolved_max_tokens(), reasoning={"effort": request.resolved_effort()},
                      prompt_cache_key=f"jobrun:{request.role}", store=False)
        try:
            response = await self._send(request, common)
        except openai.RateLimitError as exc:
            raise LLMError(f"rate limited: {exc.message}", retryable=True) from exc
        except openai.APIStatusError as exc:
            raise LLMError(f"API error {exc.status_code}: {exc.message}", retryable=exc.status_code >= 500) from exc
        except openai.APIConnectionError as exc:                  # includes the SDK's timeout
            raise LLMError(f"connection error: {exc}", retryable=True) from exc
        except ValidationError as exc:
            raise LLMError(f"structured reply did not parse as {request.schema.__name__ if request.schema else 'JSON'}: "
                           f"{exc.errors()[:2]}", retryable=True) from exc

        status = getattr(response, "status", None)
        reason = getattr(getattr(response, "incomplete_details", None), "reason", None)
        for item in getattr(response, "output", None) or []:
            for part in getattr(item, "content", None) or []:
                if getattr(part, "type", "") == "refusal":
                    raise LLMRefusal(f"request declined: {getattr(part, 'refusal', '')[:200]}")
        if status == "incomplete" and reason == "content_filter":
            raise LLMRefusal("request declined (content filter)")
        text = getattr(response, "output_text", "") or ""
        parsed = None
        if request.schema is not None:
            parsed = getattr(response, "output_parsed", None)
            if parsed is None:
                if status == "incomplete" and reason == "max_output_tokens":
                    raise LLMError("structured reply was cut off by max_output_tokens", retryable=True)
                parsed = _parse(request.schema, text)
        elif status == "incomplete" and reason == "max_output_tokens" and not text:
            raise LLMError("reply was cut off by max_output_tokens", retryable=True)
        usage = getattr(response, "usage", None)
        total_in = int(getattr(usage, "input_tokens", 0) or 0)
        cached = int(getattr(getattr(usage, "input_tokens_details", None), "cached_tokens", 0) or 0)
        return LLMResponse(text=text, parsed=parsed,
                           usage=LLMUsage(input_tokens=max(0, total_in - cached), output_tokens=int(getattr(usage, "output_tokens", 0) or 0),
                                          cache_read_tokens=cached, cache_write_tokens=0),
                           model=getattr(response, "model", "") or self.model_for(request.role),
                           latency_ms=int((time.perf_counter() - started) * 1000), stop_reason=status)


def build_provider(kind: str, *, manual_dir: Path | None = None, **kwargs) -> Provider:
    if kind == "anthropic":
        return AnthropicProvider(**kwargs)
    if kind == "openai":
        return OpenAIProvider(**kwargs)
    if kind == "manual":
        return ManualProvider(manual_dir or Path("workdir/manual_llm"))
    raise ValueError(f"unknown provider {kind!r} (expected 'anthropic', 'openai' or 'manual')")
