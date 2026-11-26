"""One error shape for every route: {"error": {"code": ..., "message": ...}}.

The codes are the contract the web app switches on (integration readiness §6):
unauthenticated, forbidden, not_found, validation, conflict, already_submitted,
no_pending_follow_up, nothing_to_retry, usage_limit, evaluation_unavailable.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError, OperationalError
from sqlalchemy.exc import TimeoutError as PoolTimeoutError
from starlette.exceptions import HTTPException as StarletteHTTPException

STATUS_FOR_CODE = {
    "unauthenticated": 401,
    "forbidden": 403,
    "not_found": 404,
    "validation": 422,
    "conflict": 409,
    "already_submitted": 409,
    "no_pending_follow_up": 409,
    "follow_up_not_ready": 409,                # the follow-up is decided but its words are still being written
    "nothing_to_retry": 409,
    "stale_version": 409,
    "no_reviewed_questions": 409,              # the bank has no reviewed question for this role/plan yet
    "usage_limit": 429, "monthly_feedback_limit": 429, "payment_required": 402,
    "consent_required": 403,                   # the privacy consent of sign-up has not been given (services/legal.py)
    "evaluation_unavailable": 503,
    "temporarily_unavailable": 503,
}

# `usage_limit` covers every allowance and every "not enough coins". The screen cannot tell them apart by the code,
# and showed all of them as "daily limit, try tomorrow" (language verification, 2026-11-14), so each one says which
# it is in `error.reason`. The message stays English and is for logs; the web app writes its own words per reason.
USAGE_LIMIT_REASONS = (
    "daily_attempts",            # practice attempts started today
    "daily_interviews",          # mock interviews started today
    "monthly_budget",            # this month's practice allowance (services/budget.py)
    "evaluation_tries",          # one answer sent to the judge too many times; the answer is saved
    "rate_limit",                # too many requests in a minute
    "quiz_rounds",               # the day's practice rounds of the quiz game
    "coins",                     # not enough coins for this purchase or stake (HTTP 402)
    "daily_duels",               # the day's duels
    "duel_winnings_daily",       # the day's ceiling on coins won in duels
    "duel_cooldown",             # the same two players, too soon
    "code_runs_daily",           # the day's code runs
    "code_runs_rate",            # code runs in the last minute
    "code_runner_busy",          # this user's runs in flight
    "company_sightings_daily",   # new companies reported today
)


class ApiError(Exception):
    def __init__(self, code: str, message: str, *, status: int | None = None, headers: dict | None = None,
                 reason: str | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.reason = reason                        # which limit, for `usage_limit` (USAGE_LIMIT_REASONS)
        self.status = status or STATUS_FOR_CODE.get(code, 400)
        self.headers = headers or {}


CONNECTION_ERROR_NAMES = ("ConnectionDoesNotExistError", "ConnectionResetError", "InterfaceError",
                          "ConnectionRefusedError", "TimeoutError", "CancelledError", "OSError")


def is_connection_error(exc: BaseException) -> bool:
    """True for the lost-connection family (asyncpg, socket), at any depth of the cause chain."""
    seen = 0
    while exc is not None and seen < 8:
        if getattr(exc, "connection_invalidated", False) or type(exc).__name__ in CONNECTION_ERROR_NAMES                 or "connection was closed" in str(exc) or "forcibly closed" in str(exc):
            return True
        exc = getattr(exc, "orig", None) or exc.__cause__ or exc.__context__     # SQLAlchemy wraps the driver error in .orig
        seen += 1
    return False


# What Postgres answers when a text holds the NUL character: 22021 for a text column ("invalid byte sequence for
# encoding UTF8: 0x00"), 22P05 for a jsonb column ("unsupported Unicode escape sequence"). The answer intakes and the
# code runner's result drop the character before it gets that far; this is for every other text a request can carry.
UNSTORABLE_TEXT_STATES = ("22021", "22P05")
UNSTORABLE_TEXT_NAMES = ("CharacterNotInRepertoireError", "UntranslatableCharacterError")


def is_unstorable_text(exc: BaseException) -> bool:
    """True when the database refused a value for a character it cannot store, at any depth of the cause chain."""
    seen = 0
    while exc is not None and seen < 8:
        if (getattr(exc, "sqlstate", None) in UNSTORABLE_TEXT_STATES or getattr(exc, "pgcode", None) in UNSTORABLE_TEXT_STATES
                or type(exc).__name__ in UNSTORABLE_TEXT_NAMES):
            return True
        exc = getattr(exc, "orig", None) or exc.__cause__ or exc.__context__
        seen += 1
    return False


def _body(code: str, message: str, details=None, reason: str | None = None) -> dict:
    error = {"code": code, "message": message}
    if reason is not None:
        error["reason"] = reason
    if details is not None:
        error["details"] = details
    return {"error": error}


def install(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(_: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(_body(exc.code, exc.message, reason=exc.reason), status_code=exc.status, headers=exc.headers)

    @app.exception_handler(StarletteHTTPException)
    @app.exception_handler(HTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = {404: "not_found", 405: "method_not_allowed", 413: "payload_too_large", 401: "unauthenticated",
                403: "forbidden"}.get(exc.status_code, "error")
        return JSONResponse(_body(code, str(exc.detail)), status_code=exc.status_code, headers=getattr(exc, "headers", None))

    @app.exception_handler(OperationalError)
    @app.exception_handler(DBAPIError)
    async def _database_unavailable(request: Request, exc: DBAPIError) -> JSONResponse:
        """A dropped or refused database connection. The failed transaction rolled back atomically,
        so the client may simply retry; an accepted answer is never lost by this."""
        if is_unstorable_text(exc):
            # the caller's own text, not a server fault: 500 here told the web app to show "something went wrong"
            # for a pasted NUL character (bug hunt, 2026-11-26). The transaction rolled back; nothing was half-saved.
            return JSONResponse(_body("validation", "the text holds a character that cannot be stored (NUL); "
                                                    "remove it and send again"), status_code=422)
        if not (exc.connection_invalidated or is_connection_error(exc)):
            raise exc                                          # a real query error: let the 500 path log it
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(_body("temporarily_unavailable", "the database connection dropped; please retry",
                                  {"request_id": request_id} if request_id else None), status_code=503,
                            headers={"Retry-After": "2"})

    @app.exception_handler(PoolTimeoutError)
    async def _pool_exhausted(request: Request, exc: PoolTimeoutError) -> JSONResponse:
        """Every connection of the pool stayed in use for the whole pool timeout. Nothing of this request ran, so the
        client may retry. It is not a DBAPIError, so it used to leave as a 500 with no Retry-After (bug hunt,
        2026-11-26)."""
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(_body("temporarily_unavailable", "the server is busy; please retry in a few seconds",
                                  {"request_id": request_id} if request_id else None), status_code=503,
                            headers={"Retry-After": "5"})

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        details = [{"loc": list(e.get("loc", [])), "msg": e.get("msg")} for e in exc.errors()[:10]]
        return JSONResponse(_body("validation", "the request is not valid", details), status_code=422)
