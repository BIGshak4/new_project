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
from starlette.exceptions import HTTPException as StarletteHTTPException

STATUS_FOR_CODE = {
    "unauthenticated": 401,
    "forbidden": 403,
    "not_found": 404,
    "validation": 422,
    "conflict": 409,
    "already_submitted": 409,
    "no_pending_follow_up": 409,
    "nothing_to_retry": 409,
    "stale_version": 409,
    "no_reviewed_questions": 409,              # the bank has no reviewed question for this role/plan yet
    "usage_limit": 429,
    "evaluation_unavailable": 503,
    "temporarily_unavailable": 503,
}


class ApiError(Exception):
    def __init__(self, code: str, message: str, *, status: int | None = None, headers: dict | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
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


def _body(code: str, message: str, details=None) -> dict:
    error = {"code": code, "message": message}
    if details is not None:
        error["details"] = details
    return {"error": error}


def install(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(_: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(_body(exc.code, exc.message), status_code=exc.status, headers=exc.headers)

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
        if not (exc.connection_invalidated or is_connection_error(exc)):
            raise exc                                          # a real query error: let the 500 path log it
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(_body("temporarily_unavailable", "the database connection dropped; please retry",
                                  {"request_id": request_id} if request_id else None), status_code=503,
                            headers={"Retry-After": "2"})

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        details = [{"loc": list(e.get("loc", [])), "msg": e.get("msg")} for e in exc.errors()[:10]]
        return JSONResponse(_body("validation", "the request is not valid", details), status_code=422)
