"""Browser Playwright E2E tests for the Streamlit UI (requires running servers)."""

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e

CHAT_PLACEHOLDER = "Ask OmniTest Tutor about Math, Science, Reading, Writing, or your progress..."


def test_login_and_chat(page: Page):
    """Test Demo Student sign-in and RAG tutor response."""
    page.goto("http://localhost:8501")
    page.wait_for_load_state("networkidle")

    page.get_by_role("button", name="Demo Student").click()
    page.wait_for_load_state("networkidle")

    chat_input = page.get_by_placeholder(CHAT_PLACEHOLDER)
    expect(chat_input).to_be_visible()
    chat_input.fill("What is the formula for slope of a line?")
    chat_input.press("Enter")
    page.wait_for_load_state("networkidle")

    chat_messages = page.locator(".stChatMessage")
    expect(chat_messages.last).to_contain_text("slope", timeout=30000)


def test_admin_materials_crud(page: Page):
    """Test Demo Admin sign-in and Study Library authoring controls."""
    page.goto("http://localhost:8501")
    page.wait_for_load_state("networkidle")

    page.get_by_role("button", name="Demo Admin").click()
    page.wait_for_load_state("networkidle")

    page.get_by_role("radio", name="Study Library").click()
    page.wait_for_load_state("networkidle")

    page.locator("summary").filter(has_text="Admin: Add or Upload Study Material").click()
    expect(page.get_by_role("button", name="Create & ingest material")).to_be_visible()


def test_quiz_flow(page: Page):
    """Test Practice Quizzes tab rendering and attempt submission."""
    page.goto("http://localhost:8501")
    page.wait_for_load_state("networkidle")

    page.get_by_role("button", name="Demo Student").click()
    page.wait_for_load_state("networkidle")

    page.get_by_role("radio", name="Practice Quizzes").click()
    page.wait_for_load_state("networkidle")

    expect(page.get_by_role("combobox", name="Select a practice quiz")).to_be_visible()
    submit_button = page.get_by_role("button", name="Submit Quiz")
    expect(submit_button).to_be_visible()
    page.locator('[data-testid="stForm"] .stRadio [role="radiogroup"] label').first.click()
    submit_button.click()
    page.wait_for_load_state("networkidle")
    expect(page.get_by_text("Quiz Results")).to_be_visible(timeout=15000)
