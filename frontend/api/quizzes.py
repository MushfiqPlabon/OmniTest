"""Frontend HTTP client helpers for practice quizzes and attempt history."""

from __future__ import annotations

import builtins
from typing import Any

from api.http import APITransport, build_params


class QuizzesAPI:
    """Wraps `/quizzes` CRUD, submissions, and student attempt history."""

    def __init__(self, transport: APITransport):
        self._http = transport

    def list(
        self,
        token: str,
        subject: str | None = None,
        topic: str | None = None,
        difficulty: str | None = None,
        search: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> dict[str, Any]:
        """Fetch paginated practice quizzes matching optional filters."""
        params = build_params(page=page, size=size, subject=subject, topic=topic, difficulty=difficulty, search=search)
        return self._http.request("GET", "/quizzes", token=token, params=params)

    def get(self, token: str, quiz_id: int) -> dict[str, Any]:
        """Fetch quiz metadata and questions before starting an attempt."""
        return self._http.request("GET", f"/quizzes/{quiz_id}", token=token)

    def create(self, token: str, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new quiz and question set (admin only)."""
        return self._http.request("POST", "/quizzes", token=token, json=data)

    def delete(self, token: str, quiz_id: int) -> None:
        """Delete a quiz and its recorded attempts (admin only)."""
        self._http.request("DELETE", f"/quizzes/{quiz_id}", token=token)

    def submit_attempt(self, token: str, quiz_id: int, answers: dict[str, str]) -> dict[str, Any]:
        """Submit answers for a quiz and receive immediate grading feedback."""
        return self._http.request("POST", f"/quizzes/{quiz_id}/attempt", token=token, json={"answers": answers})

    def my_attempts(self, token: str) -> builtins.list[dict[str, Any]]:
        """List the signed-in student's quiz attempt history for Analytics."""
        return self._http.request("GET", "/quizzes/attempts/my", token=token)
