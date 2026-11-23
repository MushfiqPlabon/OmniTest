"""Frontend HTTP client helpers for AI tutor chat and saved conversation sessions."""

from __future__ import annotations

from typing import Any

from api.http import APITransport


class ChatAPI:
    """Wraps `/chat` and `/chat/sessions` endpoints."""

    def __init__(self, transport: APITransport):
        self._http = transport

    def send(
        self,
        token: str,
        message: str,
        history: list[dict[str, str]] | None = None,
        session_id: int | None = None,
    ) -> dict[str, Any]:
        """Send a chat turn and wait for the complete tutor response."""
        return self._http.request(
            "POST",
            "/chat",
            token=token,
            json={"message": message, "history": history or [], "session_id": session_id},
            timeout=60.0,
        )

    def list_sessions(self, token: str) -> list[dict[str, Any]]:
        """List saved tutor chat threads belonging to the signed-in user."""
        return self._http.request("GET", "/chat/sessions", token=token)

    def get_session(self, token: str, session_id: int) -> dict[str, Any]:
        """Load the saved message transcript for one chat session."""
        return self._http.request("GET", f"/chat/sessions/{session_id}", token=token)
