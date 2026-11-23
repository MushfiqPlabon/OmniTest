"""Adaptive Practice Quizzes tab explorer (`frontend/views/quizzes/tab.py`)."""

from __future__ import annotations

from typing import Any

import streamlit as st
from api import APIError, api
from views.common import fetch_paginated_items, is_admin, render_metadata_badges, show_api_error
from views.quizzes.admin import render_admin_quiz_creator
from views.quizzes.runner import render_quiz_runner


def _render_delete_quiz_btn(token: str, quiz_id: int) -> None:
    """Render admin-only Delete Quiz button."""
    if not is_admin():
        return
    if not st.button("Delete quiz", width="stretch", key=f"del_quiz_{quiz_id}"):
        return
    try:
        api.quizzes.delete(token, quiz_id)
        st.session_state.pop("quiz_result", None)
        st.toast("Quiz deleted.")
        st.rerun()
    except APIError as exc:
        show_api_error(exc, "Could not delete quiz")


def _render_quiz_header(token: str, active_quiz: dict[str, Any]) -> None:
    """Display active quiz title, metadata badges, and admin delete control."""
    with st.container(border=True):
        header_col, action_col = st.columns([4, 1])
        with header_col:
            st.markdown(f"### {active_quiz['title']}")
            render_metadata_badges(active_quiz["subject"], active_quiz["topic"], active_quiz["difficulty"])
        with action_col:
            _render_delete_quiz_btn(token, active_quiz["id"])


def _select_and_load_quiz(token: str, quizzes: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Render quiz dropdown and fetch full question details for the chosen quiz."""
    quiz_map = {q["id"]: q for q in quizzes}
    selected_id = st.selectbox(
        "Select a practice quiz",
        list(quiz_map.keys()),
        format_func=lambda qid: f"#{qid} — {quiz_map[qid]['title']} ({quiz_map[qid]['subject'].title()})",
        key="quiz_selector",
    )
    try:
        return api.quizzes.get(token, selected_id)
    except APIError as exc:
        show_api_error(exc, "Could not load quiz questions")
        return None


def render_quizzes_tab(token: str) -> None:
    """Render the interactive practice quizzes explorer, runner, and admin builder."""
    st.subheader("Adaptive Practice Quizzes")
    if is_admin():
        render_admin_quiz_creator(token)

    quizzes = fetch_paginated_items(
        "quizzes",
        api.quizzes.list,
        token,
        search_placeholder="Search quizzes by title or topic...",
        error_context="Could not load quizzes",
    )
    if not quizzes:
        if quizzes is not None:
            st.info("No quizzes matched your filters.")
        return

    active_quiz = _select_and_load_quiz(token, quizzes)
    if not active_quiz:
        return
    _render_quiz_header(token, active_quiz)
    render_quiz_runner(token, active_quiz)
