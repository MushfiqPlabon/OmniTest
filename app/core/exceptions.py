"""Custom application exceptions and global FastAPI error handlers.

Why this exists:
Services raise domain errors (`NotFoundError`, `ConflictError`, etc.) without
importing HTTP response logic. FastAPI maps every failure to `ErrorResponse` JSON.
"""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from google.genai.errors import APIError as GeminiAPIError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.schemas import ErrorResponse

logger = logging.getLogger("omnitest.errors")

_HTTP_ERROR_TYPES = {
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    409: "conflict",
    422: "validation_error",
}


class AppException(Exception):
    """Base domain error mapped automatically to structured JSON HTTP responses."""

    status_code: int = 500
    error_type: str = "internal_error"

    def __init__(self, message: str, details: dict[str, Any] | None = None, headers: dict[str, str] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.headers = headers


class NotFoundError(AppException):
    """Raised when a requested record does not exist (HTTP 404)."""

    status_code = 404
    error_type = "not_found"


class ConflictError(AppException):
    """Raised on duplicate unique resources such as existing emails (HTTP 409)."""

    status_code = 409
    error_type = "conflict"


class UnauthorizedError(AppException):
    """Raised when authentication credentials are missing, expired, or wrong (HTTP 401)."""

    status_code = 401
    error_type = "unauthorized"

    def __init__(self, message: str, details: dict[str, Any] | None = None, headers: dict[str, str] | None = None):
        super().__init__(message, details=details, headers=headers or {"WWW-Authenticate": "Bearer"})


class ForbiddenError(AppException):
    """Raised when an authenticated user lacks the required role (HTTP 403)."""

    status_code = 403
    error_type = "forbidden"


class ValidationError(AppException):
    """Raised on domain-level input validation failures (HTTP 422)."""

    status_code = 422
    error_type = "validation_error"


async def app_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Convert any `AppException` subclass into a uniform `ErrorResponse` JSON response."""
    assert isinstance(exc, AppException)
    body = ErrorResponse(error=exc.error_type, message=exc.message, details=exc.details).model_dump()
    return JSONResponse(status_code=exc.status_code, content=body, headers=exc.headers)


async def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Convert FastAPI request validation errors into a uniform 422 `ErrorResponse`."""
    assert isinstance(exc, RequestValidationError)
    body = ErrorResponse(
        error="validation_error",
        message="Invalid request parameters or payload",
        details={"errors": jsonable_encoder(exc.errors())},
    ).model_dump()
    return JSONResponse(status_code=422, content=body)


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Convert Starlette/FastAPI HTTP exceptions while preserving status and response headers."""
    assert isinstance(exc, StarletteHTTPException)
    error_type = _HTTP_ERROR_TYPES.get(exc.status_code, "http_error")
    body = ErrorResponse(error=error_type, message=str(exc.detail), details={}).model_dump()
    return JSONResponse(status_code=exc.status_code, content=body, headers=exc.headers)


def _map_gemini_status(upstream_code: int) -> tuple[int, str, str]:
    """Map a Google GenAI status code into a safe HTTP status, error slug, and message."""
    if upstream_code == 429:
        return 429, "ai_rate_limited", "AI service rate limit exceeded. Please try again shortly."
    if upstream_code >= 500:
        return 503, "ai_unavailable", "AI service is temporarily unavailable. Please try again shortly."
    return 502, "ai_upstream_error", "AI service request failed. Check AI provider configuration."


async def gemini_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Map upstream Gemini API failures into sanitized 429/503/502 `ErrorResponse` payloads."""
    assert isinstance(exc, GeminiAPIError)
    upstream_code = int(exc.code or 502)
    logger.warning(
        "Gemini API error %s on %s %s (%s)", upstream_code, request.method, request.url.path, exc.status or "ERROR"
    )
    status_code, error_type, message = _map_gemini_status(upstream_code)
    body = ErrorResponse(error=error_type, message=message, details={"upstream_status": upstream_code}).model_dump()
    return JSONResponse(status_code=status_code, content=body)


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Log unexpected server errors privately and return a sanitized 500 JSON payload."""
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path, exc_info=exc)
    body = ErrorResponse(
        error="internal_server_error",
        message="An unexpected error occurred. Please try again later.",
        details={},
    ).model_dump()
    return JSONResponse(status_code=500, content=body)


def register_exception_handlers(app: FastAPI) -> None:
    """Register all global FastAPI exception mappers in one place."""
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(GeminiAPIError, gemini_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
