"""FastAPI application entry point, security middleware, and router wiring.

How requests flow through OmniTest:
1. Client sends HTTP request -> security headers & CORS middleware run first.
2. FastAPI matches `/health`, `/mcp` (Bearer-protected FastMCP), or `/api/v1/*`.
3. Global exception handlers (`app.core.exceptions`) return uniform `ErrorResponse` JSON.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import RedirectResponse
from fastapi_pagination import add_pagination
from starlette.middleware import Middleware
from starlette.routing import Route
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import register_exception_handlers
from app.core.schemas import HealthResponse
from app.mcp.auth import MCPBearerAuthMiddleware, document_mcp_openapi
from app.mcp.server import mcp
from app.modules.auth.controllers import router as auth_router
from app.modules.chat.controllers import router as chat_router
from app.modules.essays.controllers import router as essays_router
from app.modules.materials.controllers import router as materials_router
from app.modules.quizzes.controllers import router as quizzes_router

_SECURITY_HEADERS = [
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"referrer-policy", b"no-referrer"),
]


class SecurityHeadersMiddleware:
    """Pure ASGI middleware adding baseline security headers without buffering responses."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def _send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend(_SECURITY_HEADERS)
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, _send_with_headers)


mcp_app = mcp.http_app(path="/mcp", middleware=[Middleware(MCPBearerAuthMiddleware)])


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage FastMCP sub-app lifespan and dispose SQLAlchemy pools on shutdown."""
    try:
        async with mcp_app.lifespan(app):
            yield
    finally:
        await engine.dispose()


app = FastAPI(
    title="OmniTest API",
    description="GED/SAT AI Prep Platform with RAG, Tool Calling, and MCP",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Restrict CORS origins to configured frontends; Bearer JWT uses Authorization headers without cookies.
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

add_pagination(app)

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(materials_router)
api_v1_router.include_router(quizzes_router)
api_v1_router.include_router(essays_router)
api_v1_router.include_router(chat_router)


def _build_health_response() -> HealthResponse:
    """Construct the standard health-check response payload."""
    return HealthResponse(service="omnitest", version="1.0.0", environment=settings.ENVIRONMENT)


@api_v1_router.get("/health", response_model=HealthResponse, tags=["Health"])
async def v1_health_check() -> HealthResponse:
    """Return service readiness under `/api/v1/health`."""
    return _build_health_response()


app.include_router(api_v1_router)
app.router.routes.append(Route("/mcp", endpoint=mcp_app, methods=["GET", "POST", "DELETE"], include_in_schema=False))

def _custom_openapi():
    """Return cached OpenAPI schema with the mounted `/mcp` endpoint documented."""
    if not app.openapi_schema:
        raw = get_openapi(title=app.title, version=app.version, description=app.description, routes=app.routes)
        app.openapi_schema = document_mcp_openapi(raw)
    return app.openapi_schema

app.openapi = _custom_openapi


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    """Redirect root browser visits directly to interactive Swagger docs."""
    return RedirectResponse(url="/docs")


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """Return service readiness at `/health` for container health probes."""
    return _build_health_response()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=(settings.ENVIRONMENT == "development"),
    )
