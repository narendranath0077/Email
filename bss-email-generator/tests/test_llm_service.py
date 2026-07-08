from unittest.mock import MagicMock, patch

import pytest

from backend.llm_service import invoke_with_retry, LLMAuthError, LLMProviderError


@pytest.fixture(autouse=True)
def reset_llm_singleton():
    """_get_llm caches a singleton - reset it between tests so mocks don't leak."""
    import backend.llm_service as mod
    mod._llm_instance = None
    yield
    mod._llm_instance = None


class TestInvokeWithRetry:
    @patch("backend.llm_service._get_llm")
    def test_succeeds_first_try_no_retry(self, mock_get_llm):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = "  hello world  "
        mock_get_llm.return_value = mock_llm

        result = invoke_with_retry([{"role": "user", "content": "hi"}])
        assert result == "hello world"
        assert mock_llm.invoke.call_count == 1

    @patch("backend.llm_service.time.sleep", return_value=None)
    @patch("backend.llm_service._get_llm")
    def test_retries_on_transient_error_then_succeeds(self, mock_get_llm, mock_sleep):
        mock_llm = MagicMock()
        success_response = MagicMock()
        success_response.content = "recovered"
        mock_llm.invoke.side_effect = [ConnectionError("timeout"), success_response]
        mock_get_llm.return_value = mock_llm

        result = invoke_with_retry([{"role": "user", "content": "hi"}], max_attempts=3)
        assert result == "recovered"
        assert mock_llm.invoke.call_count == 2
        mock_sleep.assert_called_once()

    @patch("backend.llm_service.time.sleep", return_value=None)
    @patch("backend.llm_service._get_llm")
    def test_exhausts_retries_raises_provider_error(self, mock_get_llm, mock_sleep):
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = ConnectionError("still down")
        mock_get_llm.return_value = mock_llm

        with pytest.raises(LLMProviderError):
            invoke_with_retry([{"role": "user", "content": "hi"}], max_attempts=3)
        assert mock_llm.invoke.call_count == 3

    @patch("backend.llm_service.time.sleep", return_value=None)
    @patch("backend.llm_service._get_llm")
    def test_auth_error_does_not_retry(self, mock_get_llm, mock_sleep):
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = Exception("401 invalid api key")
        mock_get_llm.return_value = mock_llm

        with pytest.raises(LLMAuthError):
            invoke_with_retry([{"role": "user", "content": "hi"}], max_attempts=3)
        assert mock_llm.invoke.call_count == 1  # no retry wasted on a bad key
        mock_sleep.assert_not_called()

    def test_get_llm_raises_auth_error_when_no_key(self, monkeypatch):
        monkeypatch.setattr("backend.llm_service.settings.GROQ_API_KEY", "")
        with pytest.raises(LLMAuthError):
            invoke_with_retry([{"role": "user", "content": "hi"}])
