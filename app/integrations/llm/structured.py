"""Structured JSON generation helper backed by Gemini constrained decoding.

When it runs: Called when generating practice quizzes and grading student essays.
How & why: Sends `response_schema=response_type` and validates with Pydantic `TypeAdapter`
(stripping optional markdown fences) so services receive typed objects, never raw JSON text.
"""

import re

from google.genai import types
from pydantic import TypeAdapter

from app.core.config import settings
from app.core.constants import MAX_STRUCTURED_OUTPUT_TOKENS
from app.integrations.llm.client import get_gemini_client


def strip_markdown_fences(raw: str) -> str:
    """Remove optional ```json ... ``` fences surrounding model JSON output."""
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


async def generate_structured[T](prompt: str, response_type: type[T]) -> T:
    """Ask Gemini for JSON matching `response_type`; `[T]` returns an instance of whichever type you pass."""
    client = get_gemini_client()
    response = await client.aio.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=response_type,
            temperature=0.2,
            max_output_tokens=MAX_STRUCTURED_OUTPUT_TOKENS,
        ),
    )
    if response.parsed is not None:
        return response.parsed  # type: ignore[return-value]

    raw = strip_markdown_fences(response.text or "")
    if not raw:
        raise ValueError("Gemini returned an empty structured response")
    return TypeAdapter(response_type).validate_json(raw)
