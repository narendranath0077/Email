import os
import tempfile
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture()
def client(monkeypatch):
    """
    Spins up the real FastAPI app against a throwaway sqlite file so tests
    never touch data/emails.db, and never hit the real Groq API.
    """
    tmp_dir = tempfile.mkdtemp()
    db_path = os.path.join(tmp_dir, "test.db")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("GROQ_API_KEY", "test-key-not-real")

    # Re-import modules that read settings at import time, using a fresh test db.
    from backend import database as db_module
    test_engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    db_module.engine = test_engine
    db_module.SessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)

    from backend.main import app
    from backend.database import init_db
    init_db()

    with TestClient(app) as test_client:
        yield test_client


def mock_generate_response(subject="Your Interview - Monday", body="Hi Rahul,\n\nSee you Monday at 11."):
    return {
        "mode": "generate", "purpose": "Interview Scheduling", "recipient_name": "Rahul",
        "designation": "", "key_points": "Monday 11am", "tone": "Professional", "length": "Concise",
        "subject": subject, "body": body,
    }


class TestGenerateEndpoint:
    @patch("backend.routers.email.email_graph")
    def test_generate_returns_200_with_subject_and_body(self, mock_graph, client):
        mock_graph.invoke.return_value = mock_generate_response()
        resp = client.post("/api/generate", json={
            "purpose": "Interview Scheduling",
            "recipient_name": "Rahul Sharma",
            "designation": "Senior Developer",
            "key_points": "Monday interview, 11 AM, Teams link to follow",
            "tone": "Professional",
            "length": "Concise",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["subject"] == "Your Interview - Monday"
        assert "Monday" in data["body"]
        assert "id" in data

    @patch("backend.routers.email.email_graph")
    def test_generate_with_empty_key_points_returns_400(self, mock_graph, client):
        mock_graph.invoke.return_value = {"error": "Add at least one key point so the email says something specific."}
        resp = client.post("/api/generate", json={
            "purpose": "Interview Scheduling",
            "recipient_name": "Rahul",
            "key_points": "",
            "tone": "Professional",
            "length": "Concise",
        })
        assert resp.status_code == 400
        assert "key point" in resp.json()["detail"].lower()

    def test_generate_missing_required_field_returns_422(self, client):
        resp = client.post("/api/generate", json={"recipient_name": "Rahul"})
        assert resp.status_code == 422  # purpose and key_points are required by the schema

    @patch("backend.routers.email.email_graph")
    def test_generate_persists_to_history(self, mock_graph, client):
        mock_graph.invoke.return_value = mock_generate_response(subject="Persisted Subject")
        client.post("/api/generate", json={
            "purpose": "Interview Scheduling", "key_points": "Monday 11am",
            "tone": "Professional", "length": "Concise",
        })
        history = client.get("/api/history").json()
        assert any(item["subject"] == "Persisted Subject" for item in history)


class TestRefineEndpoint:
    @patch("backend.routers.email.email_graph")
    def test_refine_unknown_id_returns_404(self, mock_graph, client):
        resp = client.post("/api/refine", json={"email_id": 9999, "refinement_instruction": "make it shorter"})
        assert resp.status_code == 404
        mock_graph.invoke.assert_not_called()

    @patch("backend.routers.email.email_graph")
    def test_refine_existing_email_updates_and_links_parent(self, mock_graph, client):
        mock_graph.invoke.return_value = mock_generate_response(subject="Original")
        create_resp = client.post("/api/generate", json={
            "purpose": "Interview Scheduling", "key_points": "Monday 11am",
            "tone": "Professional", "length": "Concise",
        })
        original_id = create_resp.json()["id"]

        mock_graph.invoke.return_value = {
            "subject": "Shorter Subject", "body": "Short body.",
        }
        refine_resp = client.post("/api/refine", json={
            "email_id": original_id, "refinement_instruction": "make it shorter",
        })
        assert refine_resp.status_code == 200
        assert refine_resp.json()["subject"] == "Shorter Subject"

    def test_refine_missing_instruction_returns_422(self, client):
        resp = client.post("/api/refine", json={"email_id": 1})
        assert resp.status_code == 422


class TestHistoryEndpoint:
    def test_history_empty_by_default(self, client):
        resp = client.get("/api/history")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_history_respects_limit(self, client):
        with patch("backend.routers.email.email_graph") as mock_graph:
            mock_graph.invoke.return_value = mock_generate_response()
            for _ in range(5):
                client.post("/api/generate", json={
                    "purpose": "X", "key_points": "Y", "tone": "Professional", "length": "Standard",
                })
        resp = client.get("/api/history", params={"limit": 2})
        assert len(resp.json()) == 2


class TestHealthAndRoot:
    def test_root_ok(self, client):
        assert client.get("/").status_code == 200

    def test_health_ok(self, client):
        assert client.get("/health").json() == {"status": "healthy"}
