from unittest.mock import patch

from backend.graph import generate_node
from backend.llm_service import LLMAuthError, LLMProviderError


def base_state():
    return {
        "mode": "generate",
        "purpose": "Interview Scheduling",
        "recipient_name": "Rahul",
        "key_points": "Monday 11 AM",
        "tone": "Professional",
        "length": "Concise",
        "_prompt": "some built prompt",
    }


class TestGenerateNodeHappyPath:
    @patch("backend.graph.invoke_with_retry")
    def test_valid_json_response_is_parsed(self, mock_invoke):
        mock_invoke.return_value = '{"subject": "Your Interview", "body": "Hi Rahul,\\n\\nSee you Monday at 11."}'
        state = generate_node(base_state())
        assert state["subject"] == "Your Interview"
        assert "Monday at 11" in state["body"]
        assert mock_invoke.call_count == 1

    @patch("backend.graph.invoke_with_retry")
    def test_json_wrapped_in_markdown_fences_is_parsed(self, mock_invoke):
        mock_invoke.return_value = '```json\n{"subject": "Hi", "body": "Test body"}\n```'
        state = generate_node(base_state())
        assert state["subject"] == "Hi"
        assert state["body"] == "Test body"


class TestGenerateNodeSelfHealing:
    @patch("backend.graph.invoke_with_retry")
    def test_malformed_first_response_triggers_repair_call(self, mock_invoke):
        mock_invoke.side_effect = [
            "this is not valid json, oops",
            '{"subject": "Fixed", "body": "Now valid"}',
        ]
        state = generate_node(base_state())
        assert mock_invoke.call_count == 2
        assert state["subject"] == "Fixed"
        assert state["body"] == "Now valid"

    @patch("backend.graph.invoke_with_retry")
    def test_repair_also_fails_falls_back_gracefully(self, mock_invoke):
        mock_invoke.side_effect = ["still not json", "still not json either"]
        state = generate_node(base_state())
        assert mock_invoke.call_count == 2
        # falls back to purpose as subject and raw text as body rather than crashing
        assert state["subject"] == "Interview Scheduling"
        assert state["body"] == "still not json either"


class TestGenerateNodeErrorHandling:
    def test_error_state_short_circuits_without_calling_llm(self):
        state = base_state()
        state["error"] = "blocked earlier"
        with patch("backend.graph.invoke_with_retry") as mock_invoke:
            result = generate_node(state)
            mock_invoke.assert_not_called()
        assert result["error"] == "blocked earlier"

    @patch("backend.graph.invoke_with_retry")
    def test_auth_error_surfaces_as_state_error(self, mock_invoke):
        mock_invoke.side_effect = LLMAuthError("bad key")
        state = generate_node(base_state())
        assert state["error"] == "bad key"

    @patch("backend.graph.invoke_with_retry")
    def test_provider_error_surfaces_as_friendly_state_error(self, mock_invoke):
        mock_invoke.side_effect = LLMProviderError("timeout after retries")
        state = generate_node(base_state())
        assert "didn't respond in time" in state["error"]
