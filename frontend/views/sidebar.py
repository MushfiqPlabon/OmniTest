"""Sidebar authentication flow (Sign in, Register, optional Demo buttons, Sign out)."""

from __future__ import annotations

import os
from typing import Any

import streamlit as st
from api import APIError, api
from views.common import BadgeColor, show_api_error

SHOW_DEMO_LOGIN = os.getenv("SHOW_DEMO_LOGIN", "true").lower() == "true"

DEMO_ACCOUNTS = (
    ("Demo Student", "student@omnitest.com", "StudentPass123!"),
    ("Demo Admin", "admin@omnitest.com", "AdminPass123!"),
)

_SESSION_KEYS_TO_CLEAR = (
    "token",
    "user",
    "active_session_id",
    "_sync_session_picker",
    "chat_session_picker",
    "chat_history",
    "quiz_result",
    "essay_result",
)


def _complete_auth(token_payload: dict[str, Any], welcome_prefix: str) -> None:
    """Fetch full profile via `/auth/me`, save auth session state, and reload workspace."""
    token = token_payload["access_token"]
    user = api.auth.get_me(token)
    st.session_state["token"] = token
    st.session_state["user"] = user
    st.toast(f"{welcome_prefix}, {user['full_name']}!")
    st.rerun()


def _attempt_login(email: str, password: str) -> None:
    """Validate login inputs and exchange email + password for a JWT token."""
    if not email.strip() or not password:
        st.error("Please enter both your email address and password.")
        return
    try:
        token_payload = api.auth.login(email.strip(), password)
        _complete_auth(token_payload, "Signed in")
    except APIError as exc:
        show_api_error(exc, "Sign in failed")


def _attempt_register(full_name: str, email: str, password: str) -> None:
    """Create a new student account via `/auth/register` and sign in right away."""
    if len(full_name.strip()) < 2 or not email.strip() or len(password) < 6:
        st.error("Provide a full name (2+ chars), valid email, and password (6+ chars).")
        return
    try:
        token_payload = api.auth.register(email.strip(), password, full_name.strip())
        _complete_auth(token_payload, "Account created")
    except APIError as exc:
        show_api_error(exc, "Registration failed")


def _render_signed_in_panel(user: dict[str, Any]) -> None:
    """Show current user identity, role badge, and Sign out button in the sidebar."""
    st.markdown(f"**{user['full_name']}**")
    st.caption(user["email"])
    role = str(user.get("role", "student"))
    badge_color: BadgeColor = "violet" if role == "admin" else "green"
    st.badge(f"Role: {role.upper()}", color=badge_color)
    st.divider()

    if st.button("Sign out", width="stretch", type="secondary"):
        for key in _SESSION_KEYS_TO_CLEAR:
            st.session_state.pop(key, None)
        st.toast("Signed out cleanly.")
        st.rerun()


def _render_demo_buttons() -> None:
    """Render 1-click demo login buttons when enabled via `SHOW_DEMO_LOGIN`."""
    if not SHOW_DEMO_LOGIN:
        return
    st.caption("1-click seeded demo sign-in")
    col_student, col_admin = st.columns(2)
    with col_student:
        label, demo_email, demo_pw = DEMO_ACCOUNTS[0]
        if st.button(label, width="stretch"):
            _attempt_login(demo_email, demo_pw)
    with col_admin:
        label, demo_email, demo_pw = DEMO_ACCOUNTS[1]
        if st.button(label, width="stretch"):
            _attempt_login(demo_email, demo_pw)


def _render_login_form() -> None:
    """Render standard email/password form plus optional demo buttons."""
    with st.form("sidebar_login_form"):
        email = st.text_input("Email address", placeholder="student@omnitest.com")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        submitted = st.form_submit_button("Sign in", width="stretch", type="primary")
    if submitted:
        _attempt_login(email, password)
    _render_demo_buttons()


def _render_register_form() -> None:
    """Render new-student registration form."""
    with st.form("sidebar_register_form"):
        full_name = st.text_input("Full name", placeholder="Jane Doe")
        email = st.text_input("Email address", placeholder="you@example.com")
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Minimum 6 characters",
            help="Passwords require at least 6 characters.",
        )
        submitted = st.form_submit_button("Create account", width="stretch", type="primary")
    if submitted:
        _attempt_register(full_name, email, password)


def render_sidebar() -> None:
    """Render the navigation sidebar with authentication and account controls."""
    with st.sidebar:
        st.header("OmniTest")
        st.caption("GED & SAT AI Study Platform")

        user = st.session_state.get("user")
        if user:
            _render_signed_in_panel(user)
            return

        mode = st.segmented_control(
            "Authentication mode",
            ["Sign in", "Create account"],
            default="Sign in",
            label_visibility="collapsed",
            key="sidebar_auth_mode",
        )
        if mode == "Create account":
            _render_register_form()
        else:
            _render_login_form()
