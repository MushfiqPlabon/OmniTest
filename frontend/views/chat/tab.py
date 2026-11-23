"""AI Tutor & RAG Chat tab view (`frontend/views/chat/tab.py`)."""

from __future__ import annotations

from typing import Any

import streamlit as st
from api import APIError, api
from views.chat.sessions import render_session_toolbar
from views.common import show_api_error

STARTER_PROMPTS = [
    "Explain quadratic vertex form with an example",
    "Generate a 5-question medium algebra quiz",
    "Summarize cellular respiration vs photosynthesis",
    "Review my study progress and weak spots",
]


def _render_sources(sources: list[str]) -> None:
    """Render deduplicated RAG document source badges under an assistant turn."""
    unique = list(dict.fromkeys(sources))
    if not unique:
        return
    with st.container(horizontal=True, gap="small"):
        for src in unique:
            st.badge(f"Source: {src}", color="blue")


def _render_tool_calls(tool_calls: list[dict[str, Any]]) -> None:
    """Render executed backend tool details inside a collapsible panel."""
    if not tool_calls:
        return
    with st.expander(f"Tools executed ({len(tool_calls)})"):
        for call in tool_calls:
            st.markdown(f"**{call.get('tool', 'tool')}**")
            st.json(call.get("result") or call.get("arguments") or {})


def render_message(msg: dict[str, Any]) -> None:
    """Render one chat bubble together with RAG source badges and collapsible tool logs."""
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        _render_sources(msg.get("sources") or [])
        _render_tool_calls(msg.get("tool_calls") or [])


def _save_reply(history: list[dict[str, Any]], response: dict[str, Any]) -> None:
    """Persist assistant turn and active session ID into Streamlit session state."""
    st.session_state["active_session_id"] = response.get("session_id")
    st.session_state["_sync_session_picker"] = response.get("session_id")
    history.append(
        {
            "role": "assistant",
            "content": str(response.get("message") or ""),
            "sources": response.get("sources", []),
            "tool_calls": response.get("tool_calls", []),
        }
    )


def _send_chat_message(token: str, prompt: str) -> None:
    """Send a question to `/chat`, save the reply in session state, and redraw."""
    history = st.session_state.setdefault("chat_history", [])
    api_history = [{"role": m["role"], "content": m["content"]} for m in history]
    history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        with st.spinner("Thinking..."):
            session_id = st.session_state.get("active_session_id")
            response = api.chat.send(token, prompt, history=api_history, session_id=session_id)
    except APIError as exc:
        history.pop()
        show_api_error(exc, "Tutor chat failed")
        return

    _save_reply(history, response)
    st.rerun()


def _render_starter_prompts(token: str, history: list[dict[str, Any]]) -> bool:
    """Render suggested starter pills on an empty thread; return True if one was clicked."""
    if history:
        return False
    st.info("Start a conversation below or pick a study prompt:")
    starter = st.pills("Suggested study prompts", STARTER_PROMPTS, default=None, key="chat_starter_pill")
    if not starter:
        return False
    _send_chat_message(token, str(starter))
    return True


def render_chat_tab(token: str) -> None:
    """Render the multi-turn RAG AI Tutor tab with session history and starter pills."""
    st.subheader("AI Tutor & Study Assistant")
    st.caption("Ask GED & SAT questions grounded in ingested study guides, or request custom practice quizzes.")
    render_session_toolbar(token)

    history: list[dict[str, Any]] = st.session_state.setdefault("chat_history", [])
    if _render_starter_prompts(token, history):
        return

    for msg in history:
        render_message(msg)

    prompt = st.chat_input("Ask OmniTest Tutor about Math, Science, Reading, Writing, or your progress...")
    if prompt and prompt.strip():
        _send_chat_message(token, prompt.strip())
