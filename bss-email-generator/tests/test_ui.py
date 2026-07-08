"""
UI-side tests for the BSS AI Email Generator Streamlit frontend.

Uses Streamlit's AppTest framework for headless widget-level testing,
plus additional API endpoint tests for the new GET /api/email/{id} route.
"""

import os
import json
import tempfile
from unittest.mock import patch, MagicMock

import pytest
from streamlit.testing.v1 import AppTest


# ---------------------------------------------------------------------------
# Streamlit AppTest fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def app():
    """
    Create a fresh AppTest instance pointing at the frontend app.
    We mock out all `requests.*` calls so we never need the real backend.
    """
    mock_get_response = MagicMock()
    mock_get_response.status_code = 200
    mock_get_response.json.return_value = []

    with patch("requests.get", return_value=mock_get_response), \
         patch("requests.post") as mock_post:
        at = AppTest.from_file("frontend/app.py", default_timeout=10)
        at.run()
        yield at


@pytest.fixture()
def app_with_history():
    """
    Create an AppTest instance with mocked history data in the sidebar.
    """
    history_data = [
        {
            "id": 1,
            "purpose": "Interview Scheduling",
            "recipient_name": "Rahul Sharma",
            "subject": "Your Interview on Monday",
            "created_at": "2026-07-08T10:00:00",
        },
        {
            "id": 2,
            "purpose": "Offer Letter Follow-up",
            "recipient_name": "Priya Menon",
            "subject": "Offer Letter - Next Steps",
            "created_at": "2026-07-08T09:30:00",
        },
    ]

    mock_get_response = MagicMock()
    mock_get_response.status_code = 200
    mock_get_response.json.return_value = history_data

    with patch("requests.get", return_value=mock_get_response), \
         patch("requests.post"):
        at = AppTest.from_file("frontend/app.py", default_timeout=10)
        at.run()
        yield at


# ---------------------------------------------------------------------------
# Template selection tests
# ---------------------------------------------------------------------------

class TestTemplateSelection:
    def test_template_selectbox_exists(self, app):
        """The Quick-Start Template selectbox should be present."""
        selectboxes = app.selectbox
        assert len(selectboxes) >= 1, "Expected at least one selectbox (Quick-Start Template)"

    def test_default_template_is_placeholder(self, app):
        """Default selection should be the placeholder."""
        template_select = app.selectbox[0]
        assert template_select.value == "-- Select a template --"

    def test_selecting_interview_template_populates_fields(self, app):
        """Choosing 'Interview Scheduling' should fill purpose and key_points."""
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = []

        with patch("requests.get", return_value=mock_get_response), \
             patch("requests.post"):
            app.selectbox[0].set_value("Interview Scheduling").run()

        # After selecting template, session state should be populated
        assert app.session_state.purpose == "Interview Scheduling"
        assert "11 AM" in app.session_state.key_points
        assert app.session_state.tone == "Professional"
        assert app.session_state.length == "Concise"

    def test_selecting_offer_template_populates_fields(self, app):
        """Choosing 'Offer Letter Follow-up' should fill purpose and key_points."""
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = []

        with patch("requests.get", return_value=mock_get_response), \
             patch("requests.post"):
            app.selectbox[0].set_value("Offer Letter Follow-up").run()

        assert app.session_state.purpose == "Offer Letter Follow-up"
        assert "offer letter" in app.session_state.key_points.lower()
        assert app.session_state.tone == "Friendly"
        assert app.session_state.length == "Standard"

    def test_selecting_client_update_template(self, app):
        """Choosing 'Client Status Update' populates correctly."""
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = []

        with patch("requests.get", return_value=mock_get_response), \
             patch("requests.post"):
            app.selectbox[0].set_value("Client Status Update").run()

        assert app.session_state.purpose == "Client Status Update"
        assert "shortlisted" in app.session_state.key_points.lower()
        assert app.session_state.tone == "Formal"
        assert app.session_state.length == "Detailed"


# ---------------------------------------------------------------------------
# Reset / Clear form tests
# ---------------------------------------------------------------------------

class TestResetForm:
    def test_reset_clears_all_fields(self, app):
        """Clicking Reset should empty all session state fields."""
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = []

        with patch("requests.get", return_value=mock_get_response), \
             patch("requests.post"):
            # First fill in some data via template
            app.selectbox[0].set_value("Interview Scheduling").run()

        assert app.session_state.purpose == "Interview Scheduling"

        with patch("requests.get", return_value=mock_get_response), \
             patch("requests.post"):
            # Find the Reset button and click it
            reset_buttons = [b for b in app.button if "\U0001F504" in b.label or "Reset" in b.label]
            assert len(reset_buttons) >= 1, "Reset button should exist"
            reset_buttons[0].click().run()

        # After reset, fields should be empty/default
        assert app.session_state.purpose == ""
        assert app.session_state.recipient_name == ""
        assert app.session_state.sender_name == ""
        assert app.session_state.designation == ""
        assert app.session_state.key_points == ""
        assert app.session_state.tone == "Professional"
        assert app.session_state.length == "Standard"
        assert app.session_state.current_email is None

    def test_reset_clears_generated_email(self, app):
        """If an email was generated, Reset should clear it too."""
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = []

        with patch("requests.get", return_value=mock_get_response), \
             patch("requests.post"):
            # Manually set a generated email in session state
            app.session_state.current_email = {
                "id": 1,
                "subject": "Test Subject",
                "body": "Test Body",
            }
            # Click reset
            reset_buttons = [b for b in app.button if "\U0001F504" in b.label or "Reset" in b.label]
            assert len(reset_buttons) >= 1
            reset_buttons[0].click().run()

        assert app.session_state.current_email is None


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------

class TestValidation:
    def test_generate_with_empty_key_points_shows_warning(self, app):
        """Clicking Generate with empty key_points should show a warning."""
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = []

        with patch("requests.get", return_value=mock_get_response), \
             patch("requests.post") as mock_post:
            # Ensure key_points is empty
            app.session_state.key_points = ""
            # Click Generate
            gen_buttons = [b for b in app.button if "Generate" in b.label]
            assert len(gen_buttons) >= 1, "Generate button should exist"
            gen_buttons[0].click().run()

        # Should show a warning, not call the backend
        assert len(app.warning) >= 1
        assert "key point" in app.warning[0].value.lower()


# ---------------------------------------------------------------------------
# Generate flow tests
# ---------------------------------------------------------------------------

class TestGenerateFlow:
    def test_generate_success_stores_email(self, app):
        """Successful generate should populate session_state.current_email."""
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = []

        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {
            "id": 42,
            "subject": "Interview Scheduled - Monday",
            "body": "Dear Rahul,\n\nYour interview is on Monday at 11 AM.\n\nBest,\n[Your Name]",
        }

        with patch("requests.get", return_value=mock_get_response), \
             patch("requests.post", return_value=mock_post_response):
            app.session_state.key_points = "Monday interview at 11 AM"
            app.session_state.purpose = "Interview Scheduling"
            gen_buttons = [b for b in app.button if "Generate" in b.label]
            assert len(gen_buttons) >= 1
            gen_buttons[0].click().run()

        assert app.session_state.current_email is not None
        assert app.session_state.current_email["subject"] == "Interview Scheduled - Monday"

    def test_generate_with_sender_name_replaces_placeholder(self, app):
        """If sender_name is provided, [Your Name] in body should be replaced."""
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = []

        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {
            "id": 43,
            "subject": "Test Subject",
            "body": "Dear Rahul,\n\nContent here.\n\nBest,\n[Your Name]",
        }

        with patch("requests.get", return_value=mock_get_response), \
             patch("requests.post", return_value=mock_post_response):
            app.session_state.key_points = "Some key points"
            app.session_state.sender_name = "Priya Menon"
            gen_buttons = [b for b in app.button if "Generate" in b.label]
            gen_buttons[0].click().run()

        assert app.session_state.current_email is not None
        assert "Priya Menon" in app.session_state.current_email["body"]
        assert "[Your Name]" not in app.session_state.current_email["body"]

    def test_generate_backend_error_shows_error(self, app):
        """Backend 400 error should show an error message."""
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = []

        mock_post_response = MagicMock()
        mock_post_response.status_code = 400
        mock_post_response.json.return_value = {"detail": "Something went wrong."}

        with patch("requests.get", return_value=mock_get_response), \
             patch("requests.post", return_value=mock_post_response):
            app.session_state.key_points = "Some key points"
            gen_buttons = [b for b in app.button if "Generate" in b.label]
            gen_buttons[0].click().run()

        assert len(app.error) >= 1

    def test_generate_connection_error_shows_error(self, app):
        """If backend is unreachable, should show connection error."""
        import requests as req

        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = []

        with patch("requests.get", return_value=mock_get_response), \
             patch("requests.post", side_effect=req.exceptions.ConnectionError("refused")):
            app.session_state.key_points = "Some key points"
            gen_buttons = [b for b in app.button if "Generate" in b.label]
            gen_buttons[0].click().run()

        assert len(app.error) >= 1
        assert "backend" in app.error[0].value.lower() or "reach" in app.error[0].value.lower()


# ---------------------------------------------------------------------------
# Sidebar history tests
# ---------------------------------------------------------------------------

class TestSidebarHistory:
    def test_history_items_render_as_buttons(self, app_with_history):
        """History items should render as clickable buttons in the sidebar."""
        history_buttons = [
            b for b in app_with_history.button
            if b.key and b.key.startswith("history_")
        ]
        assert len(history_buttons) == 2, f"Expected 2 history buttons, got {len(history_buttons)}"

    def test_empty_history_shows_caption(self, app):
        """When there are no drafts, a 'No drafts yet' caption should appear."""
        captions = [c for c in app.caption if "no drafts" in c.value.lower()]
        assert len(captions) >= 1


# ---------------------------------------------------------------------------
# UI element existence tests
# ---------------------------------------------------------------------------

class TestUIElements:
    def test_page_has_generate_button(self, app):
        """The Generate Email primary button must exist."""
        gen_buttons = [b for b in app.button if "Generate" in b.label]
        assert len(gen_buttons) >= 1

    def test_page_has_reset_button(self, app):
        """The Reset button must exist."""
        reset_buttons = [b for b in app.button if "Reset" in b.label]
        assert len(reset_buttons) >= 1

    def test_page_has_all_input_fields(self, app):
        """All expected text inputs should exist."""
        # text_input: purpose, recipient_name, designation, sender_name = 4
        assert len(app.text_input) >= 4, f"Expected >= 4 text inputs, got {len(app.text_input)}"

    def test_page_has_key_points_textarea(self, app):
        """Key Points textarea should exist."""
        assert len(app.text_area) >= 1, "Expected at least one text_area for Key Points"

    def test_page_has_tone_and_length_selectors(self, app):
        """Tone and Length selectors should exist."""
        # selectbox: template, tone, length = 3 total
        assert len(app.selectbox) >= 3, f"Expected >= 3 selectboxes, got {len(app.selectbox)}"

    def test_empty_state_shows_instructions(self, app):
        """When no email is generated, the right panel should show guided instructions."""
        # The empty state uses unsafe_allow_html markdown with specific text
        markdown_texts = [m.value for m in app.markdown]
        has_instructions = any("Your email will appear here" in text for text in markdown_texts)
        assert has_instructions, "Empty state instructions should be visible"


# ---------------------------------------------------------------------------
# API endpoint tests for the new GET /api/email/{id}
# ---------------------------------------------------------------------------

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture()
def api_client(monkeypatch):
    """
    Spins up the real FastAPI app against a throwaway sqlite file so tests
    never touch data/emails.db, and never hit the real Groq API.
    """
    tmp_dir = tempfile.mkdtemp()
    db_path = os.path.join(tmp_dir, "test.db")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("GROQ_API_KEY", "test-key-not-real")

    from backend import database as db_module
    test_engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    db_module.engine = test_engine
    db_module.SessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)

    from backend.main import app
    from backend.database import init_db
    init_db()

    with TestClient(app) as test_client:
        yield test_client


class TestGetEmailEndpoint:
    @patch("backend.routers.email.email_graph")
    def test_get_email_by_id_returns_200(self, mock_graph, api_client):
        """GET /api/email/{id} should return the email if it exists."""
        mock_graph.invoke.return_value = {
            "mode": "generate", "purpose": "Test", "recipient_name": "Rahul",
            "designation": "", "key_points": "Monday", "tone": "Professional",
            "length": "Concise", "subject": "Test Subject", "body": "Test body.",
        }
        create_resp = api_client.post("/api/generate", json={
            "purpose": "Test", "key_points": "Monday",
            "tone": "Professional", "length": "Concise",
        })
        email_id = create_resp.json()["id"]

        resp = api_client.get(f"/api/email/{email_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == email_id
        assert data["subject"] == "Test Subject"
        assert data["body"] == "Test body."

    def test_get_email_by_nonexistent_id_returns_404(self, api_client):
        """GET /api/email/{id} with a non-existent ID should return 404."""
        resp = api_client.get("/api/email/99999")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()
