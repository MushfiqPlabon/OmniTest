"""Admin create and file-upload forms for Study Materials."""

from __future__ import annotations

from typing import Any

import streamlit as st
from api import APIError, api
from views.common import CREATOR_DIFFICULTIES, CREATOR_SUBJECTS, show_api_error


def _has_valid_material_meta(title: str, topic: str) -> bool:
    """Verify required title and topic minimum character lengths."""
    if len(title.strip()) >= 2 and len(topic.strip()) >= 2:
        return True
    st.error("Title and topic require at least 2 characters.")
    return False


def _submit_create_text(
    token: str,
    title: str,
    subject: str,
    topic: str,
    difficulty: str,
    source: str,
    content: str,
) -> None:
    """Validate and create a pasted-text study material."""
    if not _has_valid_material_meta(title, topic):
        return
    if len(content.strip()) < 10:
        st.error("Content requires at least 10 characters.")
        return
    payload = {
        "title": title.strip(),
        "subject": subject,
        "topic": topic.strip(),
        "difficulty": difficulty,
        "source": source.strip() or None,
        "content": content.strip(),
    }
    try:
        created = api.materials.create(token, payload)
        st.toast(f"Created & ingested '{created['title']}'!")
        st.rerun()
    except APIError as exc:
        show_api_error(exc, "Could not create material")


def _render_create_text_tab(token: str) -> None:
    """Admin form to paste and immediately embed a new study material."""
    with st.form("admin_create_material_form"):
        col_a, col_b = st.columns(2)
        title = col_a.text_input("Title", placeholder="SAT Algebra: Systems of Equations")
        subject = col_a.selectbox("Subject", CREATOR_SUBJECTS)
        topic = col_b.text_input("Topic", placeholder="systems_of_equations")
        difficulty = col_b.selectbox("Difficulty", CREATOR_DIFFICULTIES, index=1)
        source = st.text_input("Source (optional)", placeholder="Official SAT Guide")
        content = st.text_area("Study material content", height=160, placeholder="Minimum 10 characters...")
        submitted = st.form_submit_button("Create & ingest material", type="primary", width="stretch")

    if submitted:
        _submit_create_text(token, title, subject, topic, difficulty, source, content)


def _submit_upload_file(
    token: str,
    uploaded: Any,
    title: str,
    subject: str,
    topic: str,
    difficulty: str,
) -> None:
    """Validate uploaded `.md`/`.txt` file inputs and post multipart upload."""
    if not uploaded:
        st.error("Please choose a .md or .txt file first.")
        return
    if not _has_valid_material_meta(title, topic):
        return
    try:
        created = api.materials.upload(
            token,
            title=title.strip(),
            subject=subject,
            topic=topic.strip(),
            difficulty=difficulty,
            filename=uploaded.name,
            file_bytes=uploaded.getvalue(),
        )
        st.toast(f"Uploaded & ingested '{created['title']}'!")
        st.rerun()
    except APIError as exc:
        show_api_error(exc, "File upload failed")


def _render_upload_file_tab(token: str) -> None:
    """Admin uploader sending `.md`/`.txt` bytes straight to `/materials/upload`."""
    uploaded = st.file_uploader(
        "Upload Markdown or text study guide",
        type=["md", "txt"],
        help="UTF-8 .md or .txt files are chunked and embedded into pgvector automatically.",
        key="mat_file_uploader",
    )
    col_a, col_b = st.columns(2)
    title = col_a.text_input("Document title", placeholder="Biology Study Notes", key="mat_upload_title")
    subject = col_a.selectbox("Subject", CREATOR_SUBJECTS, key="mat_upload_subject")
    topic = col_b.text_input("Topic", placeholder="genetics", key="mat_upload_topic")
    difficulty = col_b.selectbox("Difficulty", CREATOR_DIFFICULTIES, index=1, key="mat_upload_diff")

    if st.button("Upload & Ingest Material", type="primary", width="stretch", key="mat_upload_btn"):
        _submit_upload_file(token, uploaded, title, subject, topic, difficulty)


def render_admin_materials_panel(token: str) -> None:
    """Collapsible admin panel offering both pasted-text and file-upload creation tabs."""
    with st.expander("Admin: Add or Upload Study Material"):
        tab_text, tab_upload = st.tabs(["Create Text Material", "Upload .md / .txt File"])
        with tab_text:
            _render_create_text_tab(token)
        with tab_upload:
            _render_upload_file_tab(token)
