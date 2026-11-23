"""Progress Analytics tab rendering student quiz/essay KPIs, score charts, and history."""

from __future__ import annotations

from typing import Any

import streamlit as st
from api import APIError, api
from views.common import BadgeColor, show_api_error


def _safe_pct(score: int | float, max_score: int | float) -> float:
    """Convert raw `score / max_score` to a rounded percentage without zero-division."""
    if not max_score:
        return 0.0
    return round((float(score) / float(max_score)) * 100.0, 1)


def _average_pct(percentages: list[float]) -> float:
    """Compute the mean percentage across attempts, returning `0.0` for empty lists."""
    if not percentages:
        return 0.0
    return round(sum(percentages) / len(percentages), 1)


def _render_kpi_row(attempts: list[dict[str, Any]], essays: list[dict[str, Any]]) -> None:
    """Render the four summary metric cards along the top of the Analytics tab."""
    quiz_pcts = [_safe_pct(a["score"], a["max_score"]) for a in attempts]
    essay_pcts = [_safe_pct(e["score"], e["max_score"]) for e in essays]
    kpis = [
        ("Quizzes Completed", str(len(attempts))),
        ("Average Quiz Score", f"{_average_pct(quiz_pcts)}%"),
        ("Essays Submitted", str(len(essays))),
        ("Average Essay Score", f"{_average_pct(essay_pcts)}%"),
    ]
    cols = st.columns(4)
    for col, (label, value) in zip(cols, kpis, strict=True):
        with col, st.container(border=True):
            st.metric(label, value)


def _render_quiz_chart(attempts: list[dict[str, Any]]) -> None:
    """Plot recent quiz percentage scores oldest-to-newest."""
    st.markdown("#### Quiz Performance (%)")
    if not attempts:
        st.info("Complete a practice quiz to see your score chart.")
        return
    rows = [
        {
            "Quiz": f"#{a['id']} {str(a.get('quiz_title') or 'Quiz')[:22]}",
            "Score (%)": _safe_pct(a["score"], a["max_score"]),
        }
        for a in reversed(attempts[:12])
    ]
    st.bar_chart(rows, x="Quiz", y="Score (%)", alt="Bar chart showing recent quiz score percentages")


def _render_essay_chart(essays: list[dict[str, Any]]) -> None:
    """Plot recent essay rubric percentage scores oldest-to-newest."""
    st.markdown("#### Essay Rubric Performance (%)")
    if not essays:
        st.info("Submit an essay to see your rubric score chart.")
        return
    rows = [
        {"Essay": f"#{e['id']} (Prompt {e['prompt_id']})", "Score (%)": _safe_pct(e["score"], e["max_score"])}
        for e in reversed(essays[:12])
    ]
    st.bar_chart(rows, x="Essay", y="Score (%)", alt="Bar chart showing recent essay rubric score percentages")


def _render_quiz_history(attempts: list[dict[str, Any]]) -> None:
    """Render recent quiz attempt cards."""
    st.markdown("#### Recent Quiz Attempts")
    if not attempts:
        st.caption("No quiz attempts recorded yet.")
        return
    for att in attempts[:10]:
        pct = _safe_pct(att["score"], att["max_score"])
        badge_color: BadgeColor = "green" if pct >= 80 else "blue"
        quiz_title = att.get("quiz_title") or f"Quiz #{att['quiz_id']}"
        with st.container(border=True):
            st.markdown(f"**{quiz_title}**")
            st.badge(f"{att['score']} / {att['max_score']} ({pct}%)", color=badge_color)
            st.caption(f"Completed: {str(att['completed_at'])[:19].replace('T', ' ')}")


def _render_essay_history(essays: list[dict[str, Any]]) -> None:
    """Render recent graded essay cards."""
    st.markdown("#### Recent Essay Submissions")
    if not essays:
        st.caption("No essay submissions recorded yet.")
        return
    for essay in essays[:10]:
        pct = _safe_pct(essay["score"], essay["max_score"])
        with st.container(border=True):
            st.markdown(f"**Prompt #{essay['prompt_id']} — Submission #{essay['id']}**")
            st.badge(f"{essay['score']} / {essay['max_score']} ({pct}%)", color="violet")
            with st.expander("View rubric feedback"):
                st.write(essay["feedback"])


def render_analytics_tab(token: str) -> None:
    """Render student KPIs, score charts, and quiz/essay attempt history."""
    st.subheader("Learning Progress & Mastery Analytics")
    try:
        attempts = api.quizzes.my_attempts(token)
        essays = api.essays.my_essays(token)
    except APIError as exc:
        show_api_error(exc, "Could not load analytics data")
        return

    _render_kpi_row(attempts, essays)
    col_quiz, col_essay = st.columns(2)
    with col_quiz, st.container(border=True):
        _render_quiz_chart(attempts)
    with col_essay, st.container(border=True):
        _render_essay_chart(essays)

    col_q, col_e = st.columns(2)
    with col_q:
        _render_quiz_history(attempts)
    with col_e:
        _render_essay_history(essays)
