"""Shared Google Gemini SDK client factory.

Why this exists:
Centralizes client creation with `HttpRetryOptions` (automatic exponential
backoff on 429/5xx) so chat, structured JSON, and embeddings share one client.
"""

from functools import lru_cache

from google import genai
from google.genai import types

from app.core.config import settings


@lru_cache(maxsize=2)
def get_gemini_client(api_version: str | None = None) -> genai.Client:
    """Return a cached Gemini client configured with automatic 429/5xx retries."""
    retry_options = types.HttpRetryOptions(
        attempts=4,
        initial_delay=1.5,
        max_delay=10.0,
        exp_base=2.0,
        jitter=0.5,
        http_status_codes=[408, 429, 500, 502, 503, 504],
    )
    version = api_version
    if version is None:
        version = settings.GEMINI_API_VERSION or None
    http_options = types.HttpOptions(api_version=version, retry_options=retry_options)
    return genai.Client(api_key=settings.GEMINI_API_KEY, http_options=http_options)
