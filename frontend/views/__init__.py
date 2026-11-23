"""Streamlit workspace view exports."""

from views.analytics_tab import render_analytics_tab
from views.chat import render_chat_tab
from views.essays import render_essays_tab
from views.materials import render_materials_tab
from views.quizzes import render_quizzes_tab
from views.sidebar import render_sidebar
from views.welcome import render_welcome

__all__ = [
    "render_analytics_tab",
    "render_chat_tab",
    "render_essays_tab",
    "render_materials_tab",
    "render_quizzes_tab",
    "render_sidebar",
    "render_welcome",
]
