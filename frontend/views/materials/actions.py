"""Admin card actions (edit, re-ingest embeddings, delete) for Study Materials."""

from __future__ import annotations

from typing import Any

import streamlit as st
from api import APIError, api
from views.common import CREATOR_DIFFICULTIES, CREATOR_SUBJECTS, show_api_error


def _safe_index(options: list[str], value: str, default: int = 0) -> int:
    """Find `value`'s selectbox index safely without crashing on unknown values."""
    return options.index(value) if value in options else default


def _build_material_patch(original: dict[str, Any], updated: dict[str, Any]) -> dict[str, Any]:
    """Return only fields that changed so metadata edits never trigger needless re-embedding."""
    return {key: new_val for key, new_val in updated.items() if original.get(key) != new_val}


def _submit_material_edit(token: str, mat: dict[str, Any], updated: dict[str, Any]) -> None:
    """Send changed material fields to `PATCH /materials/{id}`."""
    patch = _build_material_patch(mat, updated)
    if not patch:
        st.toast("No changes detected.")
        return
    try:
        saved = api.materials.update(token, mat["id"], patch)
        st.toast(f"Updated '{saved['title']}'!")
        st.rerun()
    except APIError as exc:
        show_api_error(exc, "Could not update material")


def _edit_form_fields(mat: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    """Render inline edit form inputs and return `(submitted, normalized_values)`."""
    mat_id = mat["id"]
    with st.form(f"edit_material_form_{mat_id}"):
        title = st.text_input("Title", value=mat["title"], key=f"edit_title_{mat_id}")
        col_s, col_t, col_d = st.columns(3)
        subj_idx = _safe_index(CREATOR_SUBJECTS, mat["subject"])
        diff_idx = _safe_index(CREATOR_DIFFICULTIES, mat["difficulty"], default=1)
        subject = col_s.selectbox("Subject", CREATOR_SUBJECTS, index=subj_idx, key=f"edit_subj_{mat_id}")
        topic = col_t.text_input("Topic", value=mat["topic"], key=f"edit_topic_{mat_id}")
        difficulty = col_d.selectbox("Difficulty", CREATOR_DIFFICULTIES, index=diff_idx, key=f"edit_diff_{mat_id}")
        source = st.text_input("Source", value=mat.get("source") or "", key=f"edit_src_{mat_id}")
        content = st.text_area("Content", value=mat["content"], height=140, key=f"edit_cnt_{mat_id}")
        saved = st.form_submit_button("Save changes", type="primary", width="stretch")

    updated = {
        "title": title.strip(),
        "subject": subject,
        "topic": topic.strip().lower(),
        "difficulty": difficulty,
        "source": source.strip() or None,
        "content": content.strip(),
    }
    return saved, updated


def _render_edit_material_expander(token: str, mat: dict[str, Any]) -> None:
    """Inline edit form (`PATCH /materials/{id}`) for updating a material card in place."""
    with st.expander("Edit material"):
        saved, updated = _edit_form_fields(mat)
        if saved:
            _submit_material_edit(token, mat, updated)


def _render_reingest_btn(token: str, mat_id: int) -> None:
    """Render Re-ingest button to rebuild pgvector embeddings for one material."""
    if not st.button("Re-ingest embeddings", width="stretch", key=f"reingest_mat_{mat_id}"):
        return
    try:
        res = api.materials.reingest(token, mat_id)
        st.toast(f"Re-ingested {res['chunks_created']} vector chunk(s)!")
    except APIError as exc:
        show_api_error(exc, "Re-ingestion failed")


def _render_delete_btn(token: str, mat_id: int, title: str) -> None:
    """Render Delete Material button."""
    if not st.button("Delete material", width="stretch", key=f"delete_mat_{mat_id}"):
        return
    try:
        api.materials.delete(token, mat_id)
        st.toast(f"Deleted '{title}'.")
        st.rerun()
    except APIError as exc:
        show_api_error(exc, "Delete failed")


def render_admin_card_actions(token: str, mat: dict[str, Any]) -> None:
    """Render Re-ingest, Delete, and Edit controls inside an admin's material card."""
    col_reingest, col_delete = st.columns(2)
    with col_reingest:
        _render_reingest_btn(token, mat["id"])
    with col_delete:
        _render_delete_btn(token, mat["id"], mat["title"])
    _render_edit_material_expander(token, mat)
