"""Landing page shown when no user is signed in (`token` missing from `st.session_state`)."""

from __future__ import annotations

import streamlit as st

FEATURES = [
    (
        "AI Tutor & RAG Chat",
        "Ask questions across GED and SAT subjects. Answers are grounded in pgvector-indexed "
        "study guides and can trigger autonomous quiz generation or progress lookups.",
    ),
    (
        "Adaptive Practice Quizzes",
        "Filter quizzes by subject and difficulty, take MCQs or free-response drills, "
        "and receive instant score breakdowns with question explanations.",
    ),
    (
        "Rubric Essay Grader",
        "Draft timed-style analytical responses with a live word counter and receive structured "
        "criterion scores and actionable revision feedback from Gemini.",
    ),
    (
        "Study Library & Analytics",
        "Browse curated materials, upload Markdown/text study guides (Admin), "
        "and track quiz and essay mastery trends on your personal dashboard.",
    ),
]


def render_welcome() -> None:
    """Render an accessible landing overview for unauthenticated visitors."""
    st.title("OmniTest AI Study & Exam Prep")
    st.caption(
        "Full-stack GED & SAT preparation platform combining pgvector RAG tutoring, "
        "adaptive quizzes, rubric essay evaluation, and study analytics."
    )
    st.info(
        "Sign in from the sidebar — or click **Demo Student** / **Demo Admin** "
        "for 1-click access — to start practicing."
    )

    # Arrange the 4 feature cards in a 2x2 grid (`idx % 2` alternates left column / right column).
    cols = st.columns(2)
    for idx, (title, description) in enumerate(FEATURES):
        with cols[idx % 2], st.container(border=True):
            st.subheader(title)
            st.write(description)
