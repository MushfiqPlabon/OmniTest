"""ASGI Bearer JWT authentication middleware for the mounted `/mcp` endpoint.

Why this exists:
FastMCP runs as a Starlette sub-app outside FastAPI's `Depends(get_current_user)`.
This middleware enforces valid Bearer tokens on every HTTP request to `/mcp`
and exposes the verified `user_id` via a request-scoped `ContextVar`.
"""

import json
from contextvars import ContextVar

from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.exceptions import UnauthorizedError
from app.core.schemas import ErrorResponse
from app.core.security import decode_access_token

current_mcp_user_id: ContextVar[int | None] = ContextVar("current_mcp_user_id", default=None)


def _extract_bearer_token(headers: list[tuple[bytes, bytes]]) -> str | None:
    """Read the Bearer token from raw ASGI request headers."""
    for raw_key, raw_value in headers:
        if raw_key.lower() == b"authorization":
            scheme, _, token = raw_value.decode("latin-1").partition(" ")
            if scheme.lower() == "bearer" and token.strip():
                return token.strip()
    return None


async def _send_unauthorized(send: Send, message: str) -> None:
    """Send a uniform 401 `ErrorResponse` JSON body with `WWW-Authenticate: Bearer`."""
    payload = ErrorResponse(error="unauthorized", message=message).model_dump()
    body = json.dumps(payload).encode("utf-8")
    headers = [
        (b"content-type", b"application/json"),
        (b"www-authenticate", b"Bearer"),
        (b"content-length", str(len(body)).encode("ascii")),
    ]
    await send({"type": "http.response.start", "status": 401, "headers": headers})
    await send({"type": "http.response.body", "body": body})


class MCPBearerAuthMiddleware:
    """Pure ASGI middleware verifying JWT Bearer tokens for HTTP `/mcp` clients."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        token = _extract_bearer_token(list(scope.get("headers", [])))
        if not token:
            await _send_unauthorized(send, "Authentication token is required")
            return

        try:
            payload = decode_access_token(token)
            user_id = int(payload["sub"])
        except (UnauthorizedError, KeyError, TypeError, ValueError):
            await _send_unauthorized(send, "Invalid or expired token")
            return

        ctx_token = current_mcp_user_id.set(user_id)
        try:
            await self.app(scope, receive, send)
        finally:
            current_mcp_user_id.reset(ctx_token)
