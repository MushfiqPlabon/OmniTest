"""Session toolbar and history loading helpers for AI Tutor Chat."""

from __future__ import annotations

import streamlit as st
from api import APIError, api
from views.common import show_api_error


def _valid_session_option(candidate: int | None, options: list[int | None]) -> int | None:
    """Return `candidate` only if it still exists in dropdown `options`."""
    return candidate if candidate in options else None


def _load_saved_session(token: str, session_id: int) -> None:
    """Load an older conversation from PostgreSQL into Streamlit state and redraw."""
    try:
        detail = api.chat.get_session(token, session_id)
    except APIError as exc:
        show_api_error(exc, "Could not load chat session")
        return
    st.session_state["active_session_id"] = session_id
    st.session_state["_sync_session_picker"] = session_id
    st.session_state["chat_history"] = [
        {"role": m["role"], "content": m["content"]} for m in detail.get("messages", [])
    ]
    st.rerun()


def _sync_picker_state(active_id: int | None, options: list[int | None]) -> None:
    """Synchronize the session selectbox key before rendering the widget."""
    if "_sync_session_picker" in st.session_state:
        synced = st.session_state.pop("_sync_session_picker")
        st.session_state["chat_session_picker"] = _valid_session_option(synced, options)
    elif "chat_session_picker" not in st.session_state:
        st.session_state["chat_session_picker"] = _valid_session_option(active_id, options)


def _fetch_session_labels(token: str) -> dict[int | None, str]:
    """Fetch user's saved chat threads and format dropdown labels."""
    try:
        sessions = api.chat.list_sessions(token)
    except APIError as exc:
        show_api_error(exc, "Could not fetch chat sessions")
        sessions = []

    labels: dict[int | None, str] = {None: "New conversation"}
    for item in sessions:
        labels[item["id"]] = f"#{item['id']} — {item['title']}"
    return labels


def _reset_chat_state() -> None:
    """Clear active conversation state and trigger a fresh rerun."""
    st.session_state["active_session_id"] = None
    st.session_state["_sync_session_picker"] = None
    st.session_state["chat_history"] = []
    st.session_state.pop("chat_starter_pill", None)
    st.rerun()


def render_session_toolbar(token: str) -> None:
    """Draw the saved conversation dropdown and New Chat button."""
    labels = _fetch_session_labels(token)
    active_id = st.session_state.get("active_session_id")
    _sync_picker_state(active_id, list(labels.keys()))

    col_select, col_new = st.columns([4, 1], vertical_alignment="bottom")
    with col_select:
        selected = st.selectbox(
            "Saved conversations",
            list(labels.keys()),
            format_func=lambda sid: labels.get(sid, f"Session #{sid}"),
            key="chat_session_picker",
        )
    with col_new:
        if st.button("New chat", width="stretch"):
            _reset_chat_state()

    if selected != active_id:
        if selected is None:
            _reset_chat_state()
        else:
            _load_saved_session(token, selected)
