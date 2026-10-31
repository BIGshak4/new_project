"""Send signed jobs to a separate microVM broker; NEVER evaluate learner source on this host.

Expected values live in reviewed server fixtures. Browser payloads cannot select a
driver, a testbench, a VM command, a destination, or the result used by the AI.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
import time
import uuid
from pathlib import Path

import httpx
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.api.errors import ApiError
from app.repo.executions import DbExecutionLedger, MemoryExecutionLedger
from app.schemas.bank import BankQuestion
from app.schemas.engine import CheckResult
from app.schemas.execution import ExecutionCapabilities, ExecutionRequest, ExecutionResult

log = logging.getLogger("app.services.code_execution")

LANGUAGES = ("python", "javascript", "c", "cpp", "verilog", "systemverilog", "vhdl")
# A submitted answer waits this long at most for the runner (review 2026-11-01): the HTTP client allows 58 s, but a
# judged duel has a two-minute grace after its deadline and a practice submit holds the attempt's lock meanwhile.
SUBMIT_EXECUTION_SECONDS = 25.0
# What a submission keeps of a run: diagnostics are learner-program output and the cases carry the hidden test
# vectors, so the stored copy is trimmed and keeps the failing cases only (the Run button's own reply is untouched).
STORED_TEXT_CHARS = 4000
ALIASES = {"py": "python", "js": "javascript", "c++": "cpp", "sv": "systemverilog"}


def signing_key(seed: str | None) -> Ed25519PrivateKey | None:
    if not seed:
        return None
    # Domain separation: a signing VM never receives the underlying application secret.
    material = hashlib.sha256(b"JobRun isolated code execution signing v1\0" + seed.encode()).digest()
    return Ed25519PrivateKey.from_private_bytes(material)


def public_key_bytes(key: Ed25519PrivateKey) -> bytes:
    return key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)


def answer_code(answer: str) -> tuple[str, str] | None:
    # Match the editor's terminal block. Earlier examples stay explanation,
    # even when their opening/closing fences have the same length as the final block.
    closing = re.search(r"\n(`{3,})(?:\n)?$", answer)
    if closing is None or closing.end() != len(answer):
        return None
    opening = None
    for candidate in re.finditer(r"(^|\n)(`{3,})(c|cpp|python|javascript|verilog|systemverilog|vhdl|text|py|js|c\+\+|sv)\n", answer):
        if candidate[2] == closing[1] and candidate.end() <= closing.start():
            opening = candidate
    if opening is None:
        return None
    code = answer[opening.end():closing.start()]
    if re.search(r"^" + re.escape(closing[1]) + r"$", code, flags=re.MULTILINE):
        return None
    language = ALIASES.get(opening[3], opening[3])            # the aliases were defined but never applied (review 2026-11-01)
    return (language, code.strip()) if language in LANGUAGES and code.strip() else None


def _unavailable(language: str, detail="No verified execution result is available. The isolated runner is temporarily unavailable."):
    return ExecutionResult(status="unavailable", language=language, detail=detail)


class CodeExecutionService:
    def __init__(self, settings, *, database: bool = False, transport=None):
        self.url = settings.code_execution_url.rstrip("/") if settings.code_execution_url else ""
        self.key = signing_key(settings.code_execution_signing_seed or settings.supabase_service_role_key)
        self.enabled = settings.code_execution_enabled
        limits = dict(daily=settings.code_execution_daily_limit, per_minute=settings.code_execution_per_minute,
                      concurrent=settings.code_execution_concurrency)
        self.ledger = DbExecutionLedger(**limits) if database else MemoryExecutionLedger(**limits)
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(58, connect=5), transport=transport,
                                        follow_redirects=False, trust_env=False)
        self._health: tuple[float, bool] = (0, False)
        self._health_lock = asyncio.Lock()
        self.fixtures = self._load(settings.seeds_dir / "execution_cases.json")

    @staticmethod
    def _load(path: Path) -> dict:
        if not path.exists():
            return {}
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if data.get("version") != 1 or not isinstance(data.get("questions"), dict):
            raise ValueError("execution_cases.json has an unsupported schema")
        return data["questions"]

    async def aclose(self):
        await self.client.aclose()

    async def available(self) -> bool:
        if not self.enabled or not self.url or self.key is None:
            return False
        if time.monotonic() < self._health[0]:
            return self._health[1]
        async with self._health_lock:
            if time.monotonic() < self._health[0]:
                return self._health[1]
            ready = False
            try:
                status_code, body = await self._bounded("GET", f"{self.url}/api/health", 8192, timeout=5)
                health = json.loads(body) if status_code == 200 and body is not None else {}
                if not isinstance(health, dict):                      # a list or a string is not a health report
                    health = {}
                ready = (health.get("available") is True and health.get("key_fingerprint") ==
                         hashlib.sha256(public_key_bytes(self.key)).hexdigest())
            except (httpx.HTTPError, ValueError):
                pass
            self._health = (time.monotonic() + (60 if ready else 5), ready)
            return ready

    async def _bounded(self, method: str, url: str, cap: int, **kwargs) -> tuple[int, bytes | None]:
        """Status and body, reading at most `cap` bytes: a broken or hostile broker cannot fill this process's
        memory with one reply (review 2026-11-01; the old code measured the body after downloading all of it)."""
        async with self.client.stream(method, url, **kwargs) as response:
            declared = response.headers.get("content-length")
            if declared and declared.isdigit() and int(declared) > cap:
                return response.status_code, None
            chunks, size = [], 0
            async for chunk in response.aiter_bytes():
                size += len(chunk)
                if size > cap:
                    return response.status_code, None
                chunks.append(chunk)
            return response.status_code, b"".join(chunks)

    def spec(self, question: BankQuestion, language: str, source: str = "") -> dict | None:
        fixture = self.fixtures.get(question.key, {}).get("languages", {}).get(language)
        if fixture:
            return {k: v for k, v in fixture.items() if k != "starter"}
        old = question.deterministic_check
        if language == "python" and old and old.get("type") == "code_tests":
            spec = old.get("spec", old)
            if spec.get("language", "python") != "python":
                return None
            entries = spec.get("entry", [])
            entries = [entries] if isinstance(entries, str) else entries
            entry = next((name for name in entries if re.search(r"\bdef\s+" + re.escape(name) + r"\s*\(", source)),
                         entries[0] if entries else None)
            if entry and spec.get("cases"):
                return {"kind": "function", "entry": entry, "cases": spec["cases"]}
        return None

    async def capabilities(self, question: BankQuestion) -> ExecutionCapabilities:
        fixture = self.fixtures.get(question.key, {})
        supported = [language for language in LANGUAGES if self.spec(question, language) is not None]
        ready = await self.available()
        return ExecutionCapabilities(available=ready, languages=list(LANGUAGES), tested_languages=supported,
            contract=fixture.get("contract"),
            starters={language: spec["starter"] for language, spec in fixture.get("languages", {}).items()
                      if language in LANGUAGES and spec.get("starter")},
            reason=None if ready else "The isolated runner is unavailable; code is saved and reviewed without execution.")

    async def execute(self, user_id: uuid.UUID, scope: str, question: BankQuestion,
                      request: ExecutionRequest, *, reuse: bool = False) -> ExecutionResult:
        if not request.source.strip():
            raise ApiError("validation", "enter code before running it")
        job = {"language": request.language, "source": request.source.strip(), "stdin": request.stdin}
        spec = self.spec(question, request.language, job["source"])
        if spec:
            job["spec"] = spec
        job_json = json.dumps(job, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        digest = hashlib.sha256(job_json.encode()).hexdigest()
        if len(job_json.encode()) > 120000:
            raise ApiError("validation", "the code and test inputs exceed the execution payload budget")
        # Reuse only a server-produced result for these exact bytes, fixtures, user and attempt.
        if reuse:
            cached = await self.ledger.cached(str(user_id), scope, digest)
            if cached:
                return ExecutionResult.model_validate(cached)
        replay = await self.ledger.replay(str(user_id), scope, request.idempotency_key, digest)
        if replay is not None:
            return ExecutionResult.model_validate(replay)
        if not await self.available():
            return _unavailable(request.language)
        run_id, cached = await self.ledger.reserve(str(user_id), scope, request.idempotency_key, digest)
        if cached:
            return ExecutionResult.model_validate(cached)
        now = int(time.time())
        ticket = jwt.encode({"iss": "jobrun-api", "aud": "jobrun-executor", "sub": str(user_id),
                             "jti": run_id, "iat": now, "exp": now + 90, "sha256": digest}, self.key, algorithm="EdDSA")
        result = _unavailable(request.language)
        interrupted = False
        try:
            status_code, body = await self._bounded("POST", f"{self.url}/api/execute", 131072,
                                                    json={"job_json": job_json, "ticket": ticket})
            if status_code == 200 and body is not None:
                result = ExecutionResult.model_validate(json.loads(body))
                if result.language != request.language:
                    raise ValueError("executor returned a different language")
                if result.status not in ("passed", "failed") and result.passed is not None:
                    raise ValueError("executor assessed correctness without a test outcome")
                if result.status == "failed" and (result.passed is not False or not result.executed):
                    raise ValueError("executor returned inconsistent failure facts")
                if result.passed is not None and result.compiled is False:
                    raise ValueError("executor reported tests for code that did not compile")
                if (result.status == "passed" and (result.passed is not True or not result.executed
                        or not result.cases or any(not c.passed for c in result.cases))):
                    raise ValueError("executor returned inconsistent test facts")
                if result.passed is not None and not spec:
                    raise ValueError("untested execution cannot assess correctness")
            else:
                self._health = (0, False)
        except (httpx.HTTPError, ValueError):
            self._health = (0, False)
            result = _unavailable(request.language)
        except asyncio.CancelledError:
            # The VM may still be alive until its provider deadline. Preserve its reservation.
            interrupted = True
            raise
        finally:
            # A worker death has a bounded 120-second reservation; normal completion is durable.
            if not interrupted:
                await asyncio.shield(self.ledger.finish(run_id, result.model_dump(mode="json")))
        return result

    async def check_answer(self, user_id: uuid.UUID, scope: str, question: BankQuestion, answer: str) -> CheckResult | None:
        code = answer_code(answer)
        if not code:
            return None
        language, source = code
        # Compile-only examples still help the author explicitly, but do not spend a VM on every prose submission.
        if self.spec(question, language, source) is None:
            return None
        try:
            result = await asyncio.wait_for(
                self.execute(user_id, scope, question,
                             ExecutionRequest(language=language, source=source, idempotency_key=f"submit-{uuid.uuid4()}"),
                             reuse=True),
                timeout=SUBMIT_EXECUTION_SECONDS)
        except ApiError as exc:
            result = _unavailable(language, "No execution was performed: " + exc.message)
        except TimeoutError:
            self._health = (0, False)
            result = _unavailable(language, "No execution result arrived in time; the answer is reviewed as written.")
        except Exception:                                   # ledger or broker surprises are a quota problem, not a grade
            log.exception("code execution failed on the submit path (%s); the answer is reviewed as written", scope)
            self._health = (0, False)
            result = _unavailable(language)
        contract = self.fixtures.get(question.key, {}).get("contract", {}).get("en", "")
        failing = [case for case in result.cases if not case.passed][:8]
        stored = result.model_copy(update={"stdout": result.stdout[:STORED_TEXT_CHARS], "stderr": result.stderr[:STORED_TEXT_CHARS],
                                           "compile_output": result.compile_output[:STORED_TEXT_CHARS],
                                           "detail": result.detail[:STORED_TEXT_CHARS], "cases": failing})
        detail = stored.detail + ("\nAutomated test scope: " + contract if contract else "")
        return CheckResult(type="code_tests", passed=result.passed, detail=detail,
            mismatches=[case.model_dump(mode="json") for case in failing],
            runtime_ms=result.runtime_ms, execution=stored)
