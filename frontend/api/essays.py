"""Frontend HTTP client helpers for essay prompts and AI rubric submissions."""

from __future__ import annotations

from typing import Any

from api.http import APITransport, build_params


class EssaysAPI:
    """Wraps `/essays` prompt CRUD, essay grading submissions, and history."""

    def __init__(self, transport: APITransport):
        self._http = transport

    def list_prompts(
        self,
        token: str,
        subject: str | None = None,
        topic: str | None = None,
        difficulty: str | None = None,
        search: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> dict[str, Any]:
        """Fetch paginated essay writing prompts and rubrics."""
        params = build_params(page=page, size=size, subject=subject, topic=topic, difficulty=difficulty, search=search)
        return self._http.request("GET", "/essays/prompts", token=token, params=params)

    def create_prompt(self, token: str, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new essay prompt (admin only)."""
        return self._http.request("POST", "/essays/prompts", token=token, json=data)

    def delete_prompt(self, token: str, prompt_id: int) -> None:
        """Delete an essay prompt and its submissions (admin only)."""
        self._http.request("DELETE", f"/essays/prompts/{prompt_id}", token=token)

    def submit(self, token: str, prompt_id: int, response_text: str) -> dict[str, Any]:
        """Submit an essay response for AI rubric evaluation."""
        return self._http.request(
            "POST",
            f"/essays/prompts/{prompt_id}/submit",
            token=token,
            json={"response_text": response_text},
            timeout=60.0,
        )

    def my_essays(self, token: str) -> list[dict[str, Any]]:
        """List the signed-in student's graded essay history."""
        return self._http.request("GET", "/essays/my", token=token)
