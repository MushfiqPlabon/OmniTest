"""Frontend HTTP client helpers for authentication endpoints."""

from __future__ import annotations

from typing import Any

from api.http import APITransport


class AuthAPI:
    """Wraps `/auth/register`, `/auth/login`, and `/auth/me`."""

    def __init__(self, transport: APITransport):
        self._http = transport

    def register(self, email: str, password: str, full_name: str) -> dict[str, Any]:
        """Register a new student account and return a JWT token bundle."""
        return self._http.request(
            "POST",
            "/auth/register",
            json={"email": email, "password": password, "full_name": full_name},
        )

    def login(self, email: str, password: str) -> dict[str, Any]:
        """Sign in with email and password and return a JWT token bundle."""
        return self._http.request("POST", "/auth/login", json={"email": email, "password": password})

    def get_me(self, token: str) -> dict[str, Any]:
        """Fetch the currently authenticated user's profile."""
        return self._http.request("GET", "/auth/me", token=token)
