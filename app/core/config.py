"""Application configuration loader.

Reads OS environment variables first and `.env` second into the typed
`Settings` object used across the backend. Missing required secrets
(`SECRET_KEY`, `GEMINI_API_KEY`) stop the application immediately at startup.
"""

from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.urls import normalize_async_database_url


class Settings(BaseSettings):
    """Typed settings loaded once at startup from OS env vars and `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Required secrets: the app refuses to boot if either is missing.
    SECRET_KEY: str = Field(..., min_length=16, description="Cryptographic secret key for signing JWTs")
    GEMINI_API_KEY: str = Field(..., min_length=1, description="Google Gemini API key")

    # Free-tier-friendly defaults; `.env` and OS environment variables override these.
    GEMINI_MODEL: str = Field(default="gemini-3.5-flash-lite", description="Gemini chat and structured output model")
    GEMINI_API_VERSION: str = Field(default="v1", description="Gemini API version (e.g. v1)")
    GEMINI_EMBEDDING_MODEL: str = Field(default="gemini-embedding-2", description="Gemini text embedding model")

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://omnitest:devpassword@localhost:5432/omnitest",
        description="Async PostgreSQL connection string",
    )

    # JWT settings
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: Literal["HS256", "HS384", "HS512"] = "HS256"

    # Security & demo toggles
    CORS_ORIGINS: str = Field(default="http://localhost:5173", description="Comma-separated allowed CORS origins")
    ENABLE_DEMO_ACCOUNTS: bool = Field(default=True, description="Seed default demo accounts in non-production setups")

    # App server
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    @model_validator(mode="after")
    def _validate_runtime_settings(self) -> "Settings":
        """Normalize DATABASE_URL for asyncpg and enforce strong SECRET_KEY in production."""
        self.DATABASE_URL = normalize_async_database_url(self.DATABASE_URL)
        if self.ENVIRONMENT.lower() == "production" and len(self.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters in production")
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse comma-separated `CORS_ORIGINS` into a clean list for Starlette middleware."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()  # type: ignore[call-arg]
