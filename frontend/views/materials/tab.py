"""Study Library & RAG Knowledge Base tab (`frontend/views/materials/tab.py`)."""

from __future__ import annotations

from typing import Any

import streamlit as st
from api import api
from views.common import fetch_paginated_items, is_admin, render_metadata_badges
from views.materials.actions import render_admin_card_actions
from views.materials.admin import render_admin_materials_panel


def _render_material_card(token: str, mat: dict[str, Any]) -> None:
    """Render one bordered study guide card with badges, source citation, and content body."""
    with st.container(border=True):
        st.markdown(f"### {mat['title']}")
        render_metadata_badges(mat["subject"], mat["topic"], mat["difficulty"])
        if mat.get("source"):
            st.caption(f"Source: {mat['source']}")
        with st.expander("Read study material"):
            st.markdown(mat["content"])
        if is_admin():
            render_admin_card_actions(token, mat)


def render_materials_tab(token: str) -> None:
    """Render the study material explorer and admin authoring/upload workspace."""
    st.subheader("Study Library & RAG Knowledge Base")
    if is_admin():
        render_admin_materials_panel(token)

    materials = fetch_paginated_items(
        "materials",
        api.materials.list,
        token,
        search_placeholder="Search study materials...",
        error_context="Could not load study materials",
    )
    if materials is None:
        return
    if not materials:
        st.info("No study materials matched your filters.")
        return

    for mat in materials:
        _render_material_card(token, mat)
