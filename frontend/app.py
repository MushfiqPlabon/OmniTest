"""Main Streamlit entry point for OmniTest.

How Streamlit reruns work (for newcomers):
Unlike React or FastAPI, Streamlit re-executes this script top-to-bottom on every
button click or text submission, storing login tokens and UI state in `st.session_state`.
- Logged-out visitors see the sidebar sign-in form and the welcome overview.
- Signed-in users switch between the five workspace views via `st.segmented_control`.
"""

from __future__ import annotations

import streamlit as st
from views import (
    render_analytics_tab,
    render_chat_tab,
    render_essays_tab,
    render_materials_tab,
    render_quizzes_tab,
    render_sidebar,
    render_welcome,
)

# `set_page_config` must be the very first Streamlit command executed on each page load.
st.set_page_config(
    page_title="OmniTest — AI Exam Prep",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

render_sidebar()

# Ordered pairs let us render navigation pills in a stable order and look up the view function cleanly.
WORKSPACE_VIEWS = [
    ("AI Tutor Chat", render_chat_tab),
    ("Practice Quizzes", render_quizzes_tab),
    ("Essay Grader", render_essays_tab),
    ("Study Library", render_materials_tab),
    ("Progress Analytics", render_analytics_tab),
]
VIEW_NAMES = [name for name, _ in WORKSPACE_VIEWS]
VIEW_HANDLERS = dict(WORKSPACE_VIEWS)

token = st.session_state.get("token")
if not token:
    render_welcome()
else:
    user = st.session_state.get("user") or {}
    st.title("OmniTest Study Workspace")
    st.caption(f"Signed in as {user.get('full_name', 'Student')} ({str(user.get('role', 'student')).upper()})")

    active_view = st.segmented_control(
        "Workspace section",
        VIEW_NAMES,
        default=VIEW_NAMES[0],
        label_visibility="collapsed",
        key="active_workspace_tab",
    )
    if not active_view:
        active_view = VIEW_NAMES[0]
    VIEW_HANDLERS[active_view](token)
