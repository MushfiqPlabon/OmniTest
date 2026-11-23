"""Admin quiz authoring controls for the Practice Quizzes tab."""

from __future__ import annotations

from typing import Any

import streamlit as st
from api import APIError, api
from views.common import CREATOR_DIFFICULTIES, CREATOR_SUBJECTS, show_api_error


def _collect_mcq_options(idx: int, q_type: str) -> list[str] | None:
    """Render MCQ option textarea when `q_type == 'mcq'` and return non-empty lines."""
    if q_type != "mcq":
        return None
    raw = st.text_area(
        f"Question {idx + 1} options (one per line)",
        placeholder="A. 2\nB. 3\nC. -2\nD. 1/2",
        height=100,
        key=f"quiz_new_qopts_{idx}",
    )
    options = [line.strip() for line in raw.splitlines() if line.strip()]
    return options or None


def _collect_question_payload(idx: int) -> dict[str, Any]:
    """Render form inputs for one question inside the admin quiz builder."""
    with st.container(border=True):
        st.markdown(f"**Question {idx + 1}**")
        q_type = st.selectbox(
            f"Question {idx + 1} type",
            ["mcq", "fill_blank", "short_answer"],
            key=f"quiz_new_qtype_{idx}",
        )
        prompt = st.text_input(
            f"Question {idx + 1} prompt",
            placeholder="What is the slope of y = 2x + 3?",
            key=f"quiz_new_qprompt_{idx}",
        )
        options = _collect_mcq_options(idx, q_type)
        ans_hint = "A" if q_type == "mcq" else "2"
        correct = st.text_input(f"Question {idx + 1} correct answer", placeholder=ans_hint, key=f"quiz_new_qans_{idx}")
        explanation = st.text_input(f"Question {idx + 1} explanation (optional)", key=f"quiz_new_qexp_{idx}")

    return {
        "type": q_type,
        "prompt": prompt.strip(),
        "options": options,
        "correct_answer": correct.strip(),
        "explanation": explanation.strip() or None,
        "order_num": idx + 1,
    }


def _missing_question_fields(questions: list[dict[str, Any]]) -> bool:
    """Return True if any question lacks a 3+ char prompt or a correct answer."""
    return any(len(q["prompt"]) < 3 or not q["correct_answer"] for q in questions)


def _has_valid_quiz_inputs(title: str, topic: str, questions: list[dict[str, Any]]) -> bool:
    """Validate quiz title, topic, and every question's prompt and answer."""
    if not title.strip() or not topic.strip():
        st.error("Title and topic are required.")
        return False
    if _missing_question_fields(questions):
        st.error("Every question needs a prompt (3+ chars) and a correct answer.")
        return False
    return True


def _submit_new_quiz(
    token: str,
    title: str,
    subject: str,
    topic: str,
    difficulty: str,
    questions: list[dict[str, Any]],
) -> None:
    """Validate and send a new quiz creation payload to the backend."""
    if not _has_valid_quiz_inputs(title, topic, questions):
        return
    payload = {
        "title": title.strip(),
        "subject": subject,
        "topic": topic.strip(),
        "difficulty": difficulty,
        "questions": questions,
    }
    try:
        created = api.quizzes.create(token, payload)
        st.toast(f"Created quiz '{created['title']}'!")
        st.rerun()
    except APIError as exc:
        show_api_error(exc, "Could not create quiz")


def render_admin_quiz_creator(token: str) -> None:
    """Admin-only builder for creating a quiz and its questions via `/api/v1/quizzes`."""
    with st.expander("Admin: Create New Quiz"):
        col_a, col_b = st.columns(2)
        title = col_a.text_input("Quiz title", placeholder="GED Algebra Checkup", key="quiz_new_title")
        subject = col_a.selectbox("Subject", CREATOR_SUBJECTS, key="quiz_new_subject")
        topic = col_b.text_input("Topic", placeholder="linear_equations", key="quiz_new_topic")
        difficulty = col_b.selectbox("Difficulty", CREATOR_DIFFICULTIES, index=1, key="quiz_new_diff")

        q_count = int(st.number_input("Number of questions", min_value=1, max_value=10, value=1, key="quiz_new_qcount"))
        questions = [_collect_question_payload(idx) for idx in range(q_count)]
        if st.button("Create quiz", type="primary", width="stretch", key="quiz_create_btn"):
            _submit_new_quiz(token, title, subject, topic, difficulty, questions)
