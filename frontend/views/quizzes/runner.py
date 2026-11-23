"""Interactive quiz runner and graded question-by-question feedback renderer."""

from __future__ import annotations

from typing import Any

import streamlit as st
from api import APIError, api
from views.common import BadgeColor, show_api_error


def _extract_mcq_answer(choice: str | None) -> str:
    """Normalize MCQ choice labels like `'A. 5'` or `'B) 10'` to the option letter."""
    if not choice:
        return ""
    text = choice.strip()
    if len(text) >= 2 and text[0].isalpha() and text[1] in (".", ")", ":"):
        return text[0]
    return text


def _status_badge(is_correct: bool) -> tuple[str, BadgeColor]:
    """Return display label and color for a graded question."""
    return ("Correct", "green") if is_correct else ("Needs Review", "red")


def _render_result_item(idx: int, item: dict[str, Any]) -> None:
    """Render one graded question review card with correct answer and explanation."""
    status_label, status_color = _status_badge(bool(item["is_correct"]))
    given = item["student_answer"] or "No answer"
    with st.container(border=True):
        with st.container(horizontal=True, gap="small"):
            st.badge(f"Q{idx}", color="gray")
            st.badge(status_label, color=status_color)
        st.markdown(f"**{item['prompt']}**")
        st.write(f"Your answer: `{given}` | Correct answer: `{item['correct_answer']}`")
        if item.get("explanation"):
            st.caption(f"Explanation: {item['explanation']}")


def _render_quiz_result(result: dict[str, Any]) -> None:
    """Display overall quiz score metrics, progress bar, and per-question explanations."""
    assessment = "Mastered" if result["percentage"] >= 80 else "In Progress"
    with st.container(border=True):
        st.markdown("### Quiz Results")
        col1, col2, col3 = st.columns(3)
        col1.metric("Score", f"{result['score']} / {result['max_score']}")
        col2.metric("Percentage", f"{result['percentage']}%")
        col3.metric("Assessment", assessment)

        ratio = min(max(float(result["percentage"]) / 100.0, 0.0), 1.0)
        st.progress(ratio, text=result["feedback"])
        st.markdown("#### Question Review")
        for idx, item in enumerate(result.get("details", []), start=1):
            _render_result_item(idx, item)


def _render_question_input(quiz_id: int, idx: int, question: dict[str, Any]) -> str | None:
    """Render either MCQ radio choices or a free-text input box for one question."""
    st.markdown(f"**Question {idx}.** {question['prompt']}")
    qid = str(question["id"])
    if question.get("type") == "mcq" and question.get("options"):
        val = st.radio(
            f"Question {idx} options",
            question["options"],
            index=None,
            label_visibility="collapsed",
            key=f"q_ans_{quiz_id}_{qid}",
        )
    else:
        val = st.text_input(
            f"Answer for question {idx}",
            placeholder="Type your answer...",
            label_visibility="collapsed",
            key=f"q_ans_{quiz_id}_{qid}",
        )
    st.divider()
    return val


def _submit_quiz_answers(
    token: str,
    quiz_id: int,
    questions: list[dict[str, Any]],
    raw_answers: dict[str, str | None],
) -> None:
    """Normalize collected form answers and submit them to the backend grading endpoint."""
    answers: dict[str, str] = {}
    for q in questions:
        qid = str(q["id"])
        raw = raw_answers.get(qid)
        answers[qid] = _extract_mcq_answer(raw) if q.get("type") == "mcq" else (raw or "").strip()
    try:
        result = api.quizzes.submit_attempt(token, quiz_id, answers)
        st.session_state["quiz_result"] = result
        st.toast(f"Quiz submitted! Score: {result['score']}/{result['max_score']} ({result['percentage']}%)")
    except APIError as exc:
        show_api_error(exc, "Quiz submission failed")


def _maybe_show_last_result(quiz_id: int) -> None:
    """Render graded quiz feedback when the stored result belongs to `quiz_id`."""
    last_result = st.session_state.get("quiz_result")
    if last_result and last_result.get("quiz_id") == quiz_id:
        _render_quiz_result(last_result)


def render_quiz_runner(token: str, quiz: dict[str, Any]) -> None:
    """Render an interactive quiz form and display grading results after submission."""
    questions = sorted(quiz.get("questions", []), key=lambda q: q.get("order_num", 0))
    if not questions:
        st.info("This quiz has no questions yet.")
        return

    quiz_id = quiz["id"]
    with st.form(f"quiz_attempt_form_{quiz_id}"):
        raw_answers = {
            str(q["id"]): _render_question_input(quiz_id, idx, q) for idx, q in enumerate(questions, start=1)
        }
        submitted = st.form_submit_button("Submit Quiz", type="primary", width="stretch")

    if submitted:
        _submit_quiz_answers(token, quiz_id, questions, raw_answers)
    _maybe_show_last_result(quiz_id)
