"""Essay rubric drawer and AI feedback breakdown cards (`frontend/views/essays/feedback.py`)."""

from __future__ import annotations

from typing import Any

import streamlit as st


def _extract_criterion_max(rubric: dict[str, Any]) -> dict[str, float]:
    """Build a `{criterion_name: max_points}` lookup table for rubric progress bars."""
    max_lookup: dict[str, float] = {}
    for item in rubric.get("criteria", []):
        if isinstance(item, dict) and item.get("name"):
            max_lookup[str(item["name"])] = float(item.get("max", 4))
    return max_lookup


def render_rubric_details(rubric: dict[str, Any]) -> None:
    """Display the prompt's scoring criteria inside a collapsible panel."""
    criteria = rubric.get("criteria") or []
    max_score = rubric.get("max_score", 12)
    with st.expander(f"View Scoring Rubric (Max Score: {max_score})"):
        if not criteria:
            st.caption("Holistic GED/SAT rubric scoring applied.")
            return
        for crit in criteria:
            if isinstance(crit, dict):
                st.markdown(f"- **{crit.get('name', 'Criterion')}** ({crit.get('max', 4)} pts): {crit.get('desc', '')}")
            else:
                st.markdown(f"- {crit}")


def _render_criteria_cards(criteria_scores: dict[str, Any], rubric: dict[str, Any], max_score: int) -> None:
    """Render per-criterion score cards with normalized progress bars."""
    if not criteria_scores:
        return
    st.markdown("#### Criterion Breakdown")
    max_lookup = _extract_criterion_max(rubric)
    default_crit_max = max(round(max_score / max(len(criteria_scores), 1), 1), 1.0)
    cols = st.columns(min(len(criteria_scores), 3))
    for idx, (name, raw_val) in enumerate(criteria_scores.items()):
        crit_max = max_lookup.get(name, max(float(raw_val), default_crit_max))
        with cols[idx % len(cols)], st.container(border=True):
            st.metric(name, f"{raw_val} / {int(round(crit_max))}")
            st.progress(min(max(float(raw_val) / max(crit_max, 1.0), 0.0), 1.0))


def render_essay_feedback(result: dict[str, Any], rubric: dict[str, Any]) -> None:
    """Display overall essay score, written critique, and per-criterion metric cards."""
    with st.container(border=True):
        st.markdown("### AI Rubric Evaluation")
        score = int(result["score"])
        max_score = max(int(result["max_score"]), 1)
        pct = round((score / max_score) * 100, 1)

        col1, col2 = st.columns(2)
        col1.metric("Rubric Score", f"{score} / {max_score}")
        col2.metric("Percentage", f"{pct}%")
        st.progress(min(max(score / max_score, 0.0), 1.0), text=f"Overall mastery: {pct}%")

        st.markdown("#### Written Feedback")
        st.write(result["feedback"])
        _render_criteria_cards(result.get("criteria_scores") or {}, rubric, max_score)
