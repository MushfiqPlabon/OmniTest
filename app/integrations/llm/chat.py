"""Two-turn Gemini chat gateway with RAG context framing and validated tools.

When & how: Builds recent turns plus `<study_materials>` (or an explicit missing
notice), validates Gemini tool arguments via Pydantic, and sends `FunctionResponse` as `user`.
Why: Isolates prompt formatting, schema checks, and sanitized tool errors from services.
"""

import logging
from collections.abc import Sequence
from typing import Any

from google.genai import types
from pydantic import ValidationError as PydanticValidationError

from app.core.config import settings
from app.core.constants import MAX_CHAT_OUTPUT_TOKENS, MAX_HISTORY_TURNS
from app.integrations.llm.client import get_gemini_client
from app.integrations.llm.tools import ToolSpec, build_function_declaration
from app.modules.chat.schemas import ToolCallRecord

logger = logging.getLogger("omnitest.gemini")

SYSTEM_INSTRUCTION = """You are an expert GED and Digital SAT tutor.
Your role is to help students learn by answering questions, generating practice quizzes, and searching study materials.

Guidelines:
- Ground curriculum answers in the provided study materials and cite their document titles.
- If no relevant study materials were found, explicitly inform the student that no matching study materials were found in the knowledge base instead of guessing from memory.
- Use `search_study_materials` when a follow-up question needs additional guide content.
- Use `generate_practice_quiz` when the student asks to generate or create a practice quiz.
- Use `get_student_progress` when the student asks about their quiz or essay scores or progress.
- Keep explanations clear, accurate, and encouraging.
"""


def _build_chat_config(tools: Sequence[ToolSpec] | None = None) -> types.GenerateContentConfig:
    """Build Gemini chat config with system prompt, token cap, and optional tools."""
    gemini_tools: types.ToolListUnion | None = None
    if tools:
        declarations = [build_function_declaration(spec) for spec in tools]
        gemini_tools = [types.Tool(function_declarations=declarations)]
    return types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        tools=gemini_tools,
        temperature=0.3,
        max_output_tokens=MAX_CHAT_OUTPUT_TOKENS,
    )


def _to_gemini_turn(turn: dict[str, str]) -> types.Content:
    """Convert one saved history message into a Gemini `Content` turn."""
    gemini_role = "user" if turn.get("role") == "user" else "model"
    return types.Content(role=gemini_role, parts=[types.Part.from_text(text=turn.get("content", ""))])


def _build_contents(history: list[dict[str, str]], message: str, rag_context: str | None) -> list[types.Content]:
    """Convert chat history, retrieved study chunks, and user message to Gemini Contents."""
    recent_turns = history[-MAX_HISTORY_TURNS:]
    contents: list[types.Content] = []
    for turn in recent_turns:
        if turn.get("role") != "system":
            contents.append(_to_gemini_turn(turn))

    context_block = "No relevant study materials were found in the knowledge base."
    if rag_context:
        context_block = f"<study_materials>\n{rag_context}\n</study_materials>"

    user_prompt = f"{context_block}\n\nQuestion: {message}"
    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=user_prompt)]))
    return contents


async def _run_single_tool(spec: ToolSpec | None, fn_name: str, fn_args: dict[str, Any]) -> dict[str, Any]:
    """Validate arguments against `spec.args_schema`, invoke handler, and sanitize errors."""
    if spec is None:
        return {"status": "error", "message": f"Unknown tool '{fn_name}'"}
    try:
        validated = spec.args_schema.model_validate(fn_args)
    except PydanticValidationError:
        return {"status": "error", "message": f"Invalid arguments for tool '{fn_name}'"}
    try:
        return await spec.handler(validated)
    except Exception:
        logger.exception("Chat tool '%s' execution failed", fn_name)
        return {"status": "error", "message": "Tool execution failed."}


async def _execute_tool_calls(
    function_calls: list[Any],
    tool_map: dict[str, ToolSpec],
) -> tuple[list[dict[str, Any]], list[types.Part]]:
    """Run Gemini-requested tools and package sanitized results for follow-up synthesis."""
    executed: list[dict[str, Any]] = []
    parts: list[types.Part] = []

    for tool_call in function_calls:
        tool_name = tool_call.name
        tool_args = dict(tool_call.args or {})
        result_data = await _run_single_tool(tool_map.get(tool_name), tool_name, tool_args)
        executed.append(ToolCallRecord(tool=tool_name, arguments=tool_args, result=result_data).model_dump())
        parts.append(types.Part.from_function_response(name=tool_name, response={"result": result_data}))

    return executed, parts


async def _send_turn(contents: list[types.Content], tools: Sequence[ToolSpec] | None = None) -> Any:
    """Execute one Gemini `generate_content` call."""
    client = get_gemini_client()
    return await client.aio.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=contents,
        config=_build_chat_config(tools),
    )


def _extract_reply_text(response: Any, fallback: str) -> str:
    """Extract stripped model reply text or return a safe fallback string."""
    text = getattr(response, "text", None) or ""
    return text.strip() or fallback


def _get_candidate_content(response: Any) -> types.Content | None:
    """Return the first candidate `Content` when function calls are runnable."""
    if not response.function_calls or not response.candidates:
        return None
    return response.candidates[0].content


async def chat_with_tools(
    message: str,
    history: list[dict[str, str]],
    rag_context: str | None,
    tools: Sequence[ToolSpec],
) -> tuple[str, list[dict[str, Any]]]:
    """Send a chat turn to Gemini, execute any requested tools, and return the final reply."""
    contents = _build_contents(history, message, rag_context)
    response = await _send_turn(contents, tools=tools)
    model_content = _get_candidate_content(response)
    if model_content is None:
        return _extract_reply_text(response, "I am here to help you study for GED and SAT exams."), []

    tool_map = {spec.name: spec for spec in tools}
    executed_calls, tool_parts = await _execute_tool_calls(response.function_calls, tool_map)
    contents.append(model_content)
    contents.append(types.Content(role="user", parts=tool_parts))

    final_response = await _send_turn(contents)
    return _extract_reply_text(final_response, "Completed requested action."), executed_calls
