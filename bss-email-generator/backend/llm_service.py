"""
Thin wrapper around the LLM provider. Nothing else in the codebase should
import ChatGroq directly - that keeps a future provider swap (or a fallback
model) to one file, and gives retry/error-handling one home.
"""
import logging
import time

import httpx
from langchain_groq import ChatGroq

from backend.config import settings

logger = logging.getLogger("bss.llm")


class LLMAuthError(Exception):
    """Raised when the provider rejects our credentials - never worth retrying."""


class LLMProviderError(Exception):
    """Raised when the provider fails after all retry attempts."""


_AUTH_MARKERS = ("401", "invalid api key", "invalid_api_key", "authentication", "unauthorized")


_llm_instance = None


def _get_llm() -> ChatGroq:
    global _llm_instance
    if _llm_instance is None:
        if not settings.GROQ_API_KEY:
            raise LLMAuthError(
                "GROQ_API_KEY is not set. Copy .env.example to .env and add your key "
                "from https://console.groq.com/keys"
            )
        _llm_instance = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model=settings.GROQ_MODEL,
            temperature=0.7,
            timeout=15,
            max_retries=1,
            http_client=httpx.Client(trust_env=False),
        )
    return _llm_instance


def invoke_with_retry(messages: list[dict], max_attempts: int = 2) -> str:
    """
    Calls the model with a short retry path if the provider is unreachable.
    Auth errors fail immediately - retrying a bad API key wastes
    time and hides the real problem from the user.
    Returns the raw text content of the model's reply.
    """
    llm = _get_llm()
    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            response = llm.invoke(messages)
            return response.content.strip()
        except Exception as exc:  # noqa: BLE001 - provider can raise many exception types
            message = str(exc).lower()
            if any(marker in message for marker in _AUTH_MARKERS):
                logger.error("Groq auth error - not retrying: %s", exc)
                raise LLMAuthError(
                    "Groq rejected the API key. Check GROQ_API_KEY in your .env file."
                ) from exc

            last_error = exc
            logger.warning("Groq call failed (attempt %s/%s): %s", attempt, max_attempts, exc)
            if attempt < max_attempts:
                time.sleep(2 ** (attempt - 1))

    raise LLMProviderError(
        f"Groq API did not respond successfully after {max_attempts} attempts."
    ) from last_error
