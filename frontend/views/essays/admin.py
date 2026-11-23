"""Admin essay prompt creation form (`frontend/views/essays/admin.py`)."""

from __future__ import annotations

import streamlit as st
from api import APIError, api
from views.common import CREATOR_DIFFICULTIES, CREATOR_SUBJECTS, show_api_error


def _submit_new_prompt(token: str, subject: str, topic: str, difficulty: str, prompt_text: str) -> None:
    """Validate and submit a new essay prompt payload."""
    if not topic.strip() or len(prompt_text.strip()) < 10:
        st.error("Provide a topic and prompt text (10+ characters).")
        return
    payload = {
        "subject": subject,
        "topic": topic.strip(),
        "difficulty": difficulty,
        "prompt_text": prompt_text.strip(),
    }
    try:
        api.essays.create_prompt(token, payload)
        st.toast("Essay prompt created!")
        st.rerun()
    except APIError as exc:
        show_api_error(exc, "Could not create essay prompt")


def _prompt_form_inputs() -> tuple[bool, str, str, str, str]:
    """Render form fields for a new essay prompt and return submitted state + values."""
    with st.form("admin_create_essay_prompt"):
        col_a, col_b, col_c = st.columns(3)
        subject = col_a.selectbox("Subject", CREATOR_SUBJECTS, index=3)
        topic = col_b.text_input("Topic", placeholder="argumentative_writing")
        difficulty = col_c.selectbox("Difficulty", CREATOR_DIFFICULTIES, index=1)
        prompt_text = st.text_area(
            "Prompt instructions",
            height=120,
            placeholder="Write a well-reasoned response evaluating...",
        )
        submitted = st.form_submit_button("Create essay prompt", type="primary", width="stretch")
    return submitted, subject, topic, difficulty, prompt_text


def render_admin_prompt_creator(token: str) -> None:
    """Admin-only form to publish a new essay prompt using the default 12-point rubric."""
    with st.expander("Admin: Create Essay Prompt"):
        submitted, subject, topic, difficulty, prompt_text = _prompt_form_inputs()
        if submitted:
            _submit_new_prompt(token, subject, topic, difficulty, prompt_text)
