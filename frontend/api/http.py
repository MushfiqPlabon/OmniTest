"""Low-level HTTP transport, connection pooling, and error parsing for the Streamlit UI."""

from __future__ import annotations

import os
from typing import Any

import httpx

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1").rstrip("/")


class APIError(Exception):
    """Structured error raised when a backend API request fails."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(message)


def _format_loc(loc_parts: list[Any]) -> str:
    """Format Pydantic error location path skipping the `'body'` wrapper."""
    parts = [str(part) for part in loc_parts if part != "body"]
    return " -> ".join(parts)


def _first_error_dict(details: Any) -> dict[str, Any] | None:
    """Return the first validation error dict from FastAPI 422 details, if present."""
    if not isinstance(details, dict):
        return None
    errors = details.get("errors")
    if isinstance(errors, list) and errors and isinstance(errors[0], dict):
        return errors[0]
    return None


def _format_validation_error(details: Any) -> str | None:
    """Turn FastAPI 422 `details['errors']` list into a short `'field: reason'` hint."""
    first = _first_error_dict(details)
    if first is None:
        return None
    loc = _format_loc(first.get("loc", []))
    msg = str(first.get("msg", "Invalid input"))
    return f"{loc}: {msg}" if loc else msg


def _parse_json_dict(resp: httpx.Response) -> dict[str, Any] | None:
    """Safely decode a response body as a JSON dict, returning `None` on non-dict/invalid JSON."""
    try:
        data = resp.json()
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def _json_error_text(data: dict[str, Any]) -> str | None:
    """Extract a readable message from an ErrorResponse or FastAPI detail dict."""
    validation_msg = _format_validation_error(data.get("details"))
    if validation_msg:
        return validation_msg
    raw = data.get("message") or data.get("detail")
    return str(raw) if raw else None


def _extract_error_message(resp: httpx.Response) -> str:
    """Parse ErrorResponse JSON or fallback text into a user-friendly string."""
    data = _parse_json_dict(resp)
    if data is not None:
        parsed = _json_error_text(data)
        if parsed:
            return parsed
    return resp.text.strip() or f"Request failed with status {resp.status_code}"


def build_params(page: int = 1, size: int = 20, **filters: Any) -> dict[str, Any]:
    """Drop empty or `'All'` UI filter values so backend queries stay clean."""
    params: dict[str, Any] = {"page": page, "size": size}
    for key, val in filters.items():
        if val not in (None, "", "All"):
            params[key] = val
    return params


def _decode_json_body(resp: httpx.Response) -> Any:
    """Decode successful JSON responses or raise `APIError(502)` on non-JSON replies."""
    if resp.status_code == 204 or not resp.content:
        return None
    try:
        return resp.json()
    except ValueError as exc:
        raise APIError(502, "API server returned an invalid non-JSON response") from exc


class APITransport:
    """Shared `httpx.Client` connection pool handling Bearer headers and safe JSON decoding."""

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
        )

    @staticmethod
    def _headers(token: str | None = None) -> dict[str, str]:
        """Build the `Authorization: Bearer ...` header when signed in."""
        return {"Authorization": f"Bearer {token}"} if token else {}

    def request(
        self,
        method: str,
        path: str,
        token: str | None = None,
        timeout: float = 30.0,
        **kwargs: Any,
    ) -> Any:
        """Send an HTTP request and raise `APIError` on network, HTTP, or JSON failures."""
        url = f"{self.base_url}{path}"
        try:
            resp = self._client.request(method, url, headers=self._headers(token), timeout=timeout, **kwargs)
        except httpx.RequestError as exc:
            raise APIError(503, f"Could not reach API server ({self.base_url}): {exc}") from exc

        if resp.status_code >= 400:
            raise APIError(resp.status_code, _extract_error_message(resp))
        return _decode_json_body(resp)
