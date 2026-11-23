"""Shared Streamlit UI helpers used across Quizzes, Essays, Library, Analytics, and Sidebar."""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any, Literal

import streamlit as st
from api import APIError

BadgeColor = Literal["red", "orange", "yellow", "blue", "green", "violet", "gray", "grey", "primary"]

SUBJECT_OPTIONS = ["All", "math", "science", "reading", "writing", "social_studies", "general"]
CREATOR_SUBJECTS = ["math", "science", "reading", "writing", "social_studies", "general"]
DIFFICULTY_OPTIONS = ["All", "easy", "medium", "hard"]
CREATOR_DIFFICULTIES = ["easy", "medium", "hard"]
DIFFICULTY_COLOR: dict[str, BadgeColor] = {"easy": "green", "medium": "orange", "hard": "red"}


def _format_subject_label(subject: str) -> str:
    """Turn internal slugs like `'social_studies'` into readable `'Social Studies'` labels."""
    return "All" if subject == "All" else subject.replace("_", " ").title()


def is_admin() -> bool:
    """Return True when the authenticated user has the admin role."""
    user = st.session_state.get("user") or {}
    return user.get("role") == "admin"


def show_api_error(exc: APIError, context: str = "Action failed") -> None:
    """Display an error banner and clear stale session state on expired 401 tokens."""
    if exc.status_code == 401 and st.session_state.get("token"):
        st.session_state.pop("token", None)
        st.session_state.pop("user", None)
        st.error("Your session expired or is invalid. Please sign in again.")
        return
    st.error(f"{context}: {exc.message}")


def render_metadata_badges(subject: str, topic: str, difficulty: str) -> None:
    """Render native high-contrast badges for subject, topic, and difficulty."""
    diff_color = DIFFICULTY_COLOR.get(difficulty.lower(), "gray")
    with st.container(horizontal=True, gap="small"):
        st.badge(subject.replace("_", " ").title(), color="blue")
        st.badge(topic.replace("_", " ").title(), color="gray")
        st.badge(difficulty.upper(), color=diff_color)


def _clean_selection(value: Any) -> str | None:
    """Normalize filter selections by dropping empty or `'All'` values."""
    if not value or value == "All":
        return None
    return str(value)


def render_filter_bar(
    prefix: str,
    search_placeholder: str = "Search by title or topic...",
) -> tuple[str | None, str | None, str | None]:
    """Render shared Subject pills, Difficulty control, and Search box."""
    subject = st.pills(
        "Filter by subject",
        SUBJECT_OPTIONS,
        default="All",
        format_func=_format_subject_label,
        key=f"{prefix}_subject",
    )
    col_diff, col_search = st.columns([2, 3])
    with col_diff:
        difficulty = st.segmented_control(
            "Filter by difficulty",
            DIFFICULTY_OPTIONS,
            default="All",
            format_func=str.title,
            key=f"{prefix}_difficulty",
        )
    with col_search:
        search = st.text_input("Search", placeholder=search_placeholder, key=f"{prefix}_search")

    return _clean_selection(subject), _clean_selection(difficulty), search.strip() or None


def _page_step_button(label: str, page_key: str, target_page: int, disabled: bool, key: str) -> None:
    """Render a pagination button that navigates to `target_page` on click."""
    if st.button(label, width="stretch", disabled=disabled, key=key):
        st.session_state[page_key] = target_page
        st.rerun()


def render_pagination(prefix: str, total: int, size: int = 20) -> int:
    """Render compact Previous / Next pagination when items exceed one page."""
    page_key = f"{prefix}_page"
    current = int(st.session_state.get(page_key, 1))
    total_pages = max(1, math.ceil(total / max(size, 1)))
    if current > total_pages:
        st.session_state[page_key] = 1
        st.rerun()
    if total <= size:
        return current

    col_prev, col_info, col_next = st.columns([1, 2, 1], vertical_alignment="center")
    with col_prev:
        _page_step_button("Previous", page_key, current - 1, current <= 1, f"{prefix}_prev")
    with col_info:
        st.caption(f"Page {current} of {total_pages} ({total} total)")
    with col_next:
        _page_step_button("Next", page_key, current + 1, current >= total_pages, f"{prefix}_next")
    return current


def fetch_paginated_items(
    prefix: str,
    fetcher: Callable[..., dict[str, Any]],
    token: str,
    search_placeholder: str,
    error_context: str,
) -> list[dict[str, Any]] | None:
    """Shared filter bar + paginated API fetch + pagination controls for explorer tabs."""
    subject, difficulty, search = render_filter_bar(prefix, search_placeholder=search_placeholder)
    page = int(st.session_state.get(f"{prefix}_page", 1))
    try:
        listing = fetcher(token, subject=subject, difficulty=difficulty, search=search, page=page, size=20)
    except APIError as exc:
        show_api_error(exc, error_context)
        return None
    render_pagination(prefix, listing.get("total", 0), size=20)
    return list(listing.get("items", []))
