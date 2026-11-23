"""Essay Practice & AI Rubric Grader tab (`frontend/views/essays/tab.py`)."""

from __future__ import annotations

from typing import Any

import streamlit as st
from api import APIError, api
from views.common import fetch_paginated_items, is_admin, render_metadata_badges, show_api_error
from views.essays.admin import render_admin_prompt_creator
from views.essays.feedback import render_essay_feedback, render_rubric_details


def _render_delete_prompt_btn(token: str, prompt_id: int) -> None:
    """Render admin-only Delete Prompt button."""
    if not is_admin():
        return
    if not st.button("Delete prompt", width="stretch", key=f"del_prompt_{prompt_id}"):
        return
    try:
        api.essays.delete_prompt(token, prompt_id)
        st.session_state.pop("essay_result", None)
        st.toast("Essay prompt deleted.")
        st.rerun()
    except APIError as exc:
        show_api_error(exc, "Could not delete prompt")


def _render_prompt_header(token: str, active_prompt: dict[str, Any]) -> None:
    """Render the active prompt card, rubric drawer, and admin delete control."""
    with st.container(border=True):
        header_col, action_col = st.columns([4, 1])
        with header_col:
            render_metadata_badges(active_prompt["subject"], active_prompt["topic"], active_prompt["difficulty"])
            st.markdown(active_prompt["prompt_text"])
        with action_col:
            _render_delete_prompt_btn(token, active_prompt["id"])
        render_rubric_details(active_prompt.get("rubric") or {})


def _submit_essay_draft(token: str, prompt_id: int, draft: str) -> None:
    """Send the student's draft to the backend Gemini grader and save feedback in state."""
    try:
        with st.spinner("Evaluating your essay against the rubric with Gemini..."):
            result = api.essays.submit(token, prompt_id, draft)
        st.session_state["essay_result"] = result
        st.toast(f"Essay graded: {result['score']} / {result['max_score']}")
    except APIError as exc:
        show_api_error(exc, "Essay grading failed")


def _render_draft_editor(token: str, active_prompt: dict[str, Any]) -> None:
    """Render essay textarea with live word counter, submit button, and saved feedback."""
    selected_id = active_prompt["id"]
    draft = st.text_area(
        "Write your essay response",
        height=240,
        placeholder="Draft a clear, evidence-backed response (at least 20 characters; aim for 150-400 words)...",
        key=f"essay_draft_{selected_id}",
    )
    words, chars = len(draft.split()), len(draft)
    st.caption(f"Live count: {words} words | {chars} characters (minimum 20 characters required)")

    if st.button(
        "Submit Essay for AI Grading",
        type="primary",
        width="stretch",
        disabled=chars < 20,
        key=f"submit_essay_{selected_id}",
    ):
        _submit_essay_draft(token, selected_id, draft)

    last_result = st.session_state.get("essay_result")
    if last_result and last_result.get("prompt_id") == selected_id:
        render_essay_feedback(last_result, active_prompt.get("rubric") or {})


def _select_prompt(prompts: list[dict[str, Any]]) -> dict[str, Any]:
    """Render prompt selector dropdown and return the chosen prompt dictionary."""
    prompt_map = {p["id"]: p for p in prompts}
    selected_id = st.selectbox(
        "Select an essay prompt",
        list(prompt_map.keys()),
        format_func=lambda pid: (
            f"#{pid} — {prompt_map[pid]['topic'].replace('_', ' ').title()} ({prompt_map[pid]['subject'].title()})"
        ),
        key="essay_prompt_selector",
    )
    return prompt_map[selected_id]


def render_essays_tab(token: str) -> None:
    """Render the essay prompt browser, live drafting workspace, and rubric evaluation."""
    st.subheader("Essay Writing & AI Rubric Grader")
    if is_admin():
        render_admin_prompt_creator(token)

    prompts = fetch_paginated_items(
        "essays",
        api.essays.list_prompts,
        token,
        search_placeholder="Search essay prompts by topic or text...",
        error_context="Could not load essay prompts",
    )
    if not prompts:
        if prompts is not None:
            st.info("No essay prompts matched your filters.")
        return

    active_prompt = _select_prompt(prompts)
    _render_prompt_header(token, active_prompt)
    _render_draft_editor(token, active_prompt)
