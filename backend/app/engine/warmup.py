"""Warming the judge's prompt cache when a question is opened (Shaked, 2026-11-02: "each user that is connected
warms the cache for him"; "cut the time").

A judge call is one long prompt: the judge's instructions, the question block (solution, common errors) and the
question's figures, then the candidate's answer. OpenAI keeps a recently read prefix for a few minutes and skips
re-reading it on the next call that starts the same way. In production the same question judged twice minutes apart
took 11.4 s cold and 7.8 s with the prefix cached, figures included. Today that only happens by accident.

The warmer sends the judge's exact prefix with an empty answer and a one-token reply the moment a question is shown
(practice start, interview turn, a hint asked for), in the background, so the real verdict a minute later finds the
prefix cached. One warm-up per question and language per few minutes, whoever opens it: the cache is per question,
so one user's warm-up serves everyone on that question in the window. OpenAI only; any failure is counted and
logged, never raised, and never delays the request that triggered it.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable

from app.engine import evaluator, providers
from app.engine.providers import LLMError, LLMRefusal, Provider
from app.schemas.bank import BankQuestion
from app.schemas.engine import CatalogSkill

log = logging.getLogger("app.warm")

TTL_SECONDS = 240                       # OpenAI keeps a prefix for 5-10 minutes of inactivity; warm again before that
MAX_REMEMBERED = 2048                   # (question, language) pairs the warmer remembers; the oldest are forgotten

ImageFetcher = Callable[[BankQuestion], Awaitable[list[tuple[str, bytes]] | None]]


def has_prompt_images(question: BankQuestion) -> bool:
    return any(m.get("role") == "prompt" and m.get("kind") == "image" for m in question.assets.get("bank_media", []))


class JudgeWarmer:
    def __init__(self, provider: Provider | None, *, fetch_images: ImageFetcher | None = None,
                 glossary: list[dict] | None = None, enabled: bool = True, ttl_seconds: float = TTL_SECONDS,
                 clock: Callable[[], float] = time.monotonic):
        self.provider = provider
        self.fetch_images = fetch_images
        self.glossary = glossary
        self.enabled = enabled
        self.ttl = ttl_seconds
        self.clock = clock
        self._warmed: dict[tuple[str, str, bool], float] = {}           # (question key, language, with images) -> when
        self._tasks: set[asyncio.Task] = set()
        self.stats = {"sent": 0, "failed": 0, "skipped_recent": 0, "images_unavailable": 0,
                      "input_tokens": 0, "cached_tokens": 0, "cost_usd": 0.0, "last_latency_ms": None}

    @property
    def active(self) -> bool:
        """Only the OpenAI provider has the automatic prefix cache this warms; a provider without a client
        (no key) or a scripted one makes the warmer a no-op."""
        return (self.enabled and self.provider is not None and getattr(self.provider, "name", None) == "openai"
                and getattr(self.provider, "client", None) is not None)

    # ------------------------------------------------------------------ public

    def schedule(self, question: BankQuestion, language: str, skill: CatalogSkill | None, *,
                 with_images: bool = True) -> bool:
        """Fire and forget from a request handler. True when a warm-up was started."""
        if not self.active or self._recent(question.key, language, with_images):
            return False
        self._remember((question.key, language, with_images))       # before the task runs: two opens in a row warm once
        task = asyncio.get_running_loop().create_task(self.warm(question, language, skill, with_images=with_images))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return True

    async def warm(self, question: BankQuestion, language: str, skill: CatalogSkill | None, *,
                   with_images: bool = True) -> bool:
        """One warm-up call now (awaited; `schedule` is the background form). True when OpenAI took the prefix."""
        if not self.active:
            return False
        key = (question.key, language, with_images)
        self._remember(key)
        images: list[tuple[str, bytes]] = []
        if with_images and has_prompt_images(question) and self.fetch_images is not None:
            try:
                fetched = await self.fetch_images(question)
            except Exception:                                   # noqa: BLE001 - a warm-up never raises
                fetched = None
            if fetched is None:
                self.stats["images_unavailable"] += 1          # the instructions and question block still warm
            else:
                images = fetched
        request = evaluator.warm_request(question_context=evaluator.question_block(question, language, skill),
                                         language=language, difficulty=question.difficulty, glossary=self.glossary,
                                         question_images=images)
        try:
            response = await providers.call(self.provider, request)
        except (LLMError, LLMRefusal) as exc:
            # a reply cut off at the one-token budget (reported as a cut-off or as JSON that does not parse) is the
            # expected outcome: the prefix was read, which is the point
            if any(mark in str(exc) for mark in ("max_output_tokens", "did not parse", "cut off")):
                self.stats["sent"] += 1
                return True
            self.stats["failed"] += 1
            log.info("judge warm-up for %s failed: %s", question.key, exc)
            return False
        except Exception as exc:                                # noqa: BLE001
            self.stats["failed"] += 1
            log.warning("judge warm-up for %s crashed: %s", question.key, exc)
            return False
        self.stats["sent"] += 1
        self.stats["input_tokens"] += response.usage.input_tokens
        self.stats["cached_tokens"] += response.usage.cache_read_tokens
        self.stats["cost_usd"] = round(self.stats["cost_usd"] + (response.usage.cost_usd(response.model) or 0.0), 6)
        self.stats["last_latency_ms"] = response.latency_ms
        return True

    async def drain(self) -> None:
        """Wait for the background warm-ups (tests, shutdown)."""
        if self._tasks:
            await asyncio.gather(*list(self._tasks), return_exceptions=True)

    # ------------------------------------------------------------------ helpers

    def _recent(self, question_key: str, language: str, with_images: bool) -> bool:
        when = self._warmed.get((question_key, language, with_images))
        if when is not None and self.clock() - when < self.ttl:
            self.stats["skipped_recent"] += 1
            return True
        return False

    def _remember(self, key: tuple[str, str, bool]) -> None:
        self._warmed[key] = self.clock()
        if len(self._warmed) > MAX_REMEMBERED:
            for old in sorted(self._warmed, key=self._warmed.get)[: MAX_REMEMBERED // 4]:
                del self._warmed[old]


__all__ = ["JudgeWarmer", "TTL_SECONDS", "has_prompt_images"]
