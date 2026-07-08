"""
Central place for every environment-driven setting.
Nothing else in the codebase should call os.getenv() directly - that keeps
config changes to a single file, and makes it obvious what's configurable.
"""
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)


class Settings:
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/emails.db")

    # Comma-separated list, e.g. "http://localhost:8501,https://my-app.streamlit.app"
    ALLOWED_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:8501,http://localhost:8000,http://localhost:8001,http://localhost:8080,http://127.0.0.1:8501,http://127.0.0.1:8000,http://127.0.0.1:8001,http://127.0.0.1:8080,http://127.0.0.1:3000,http://localhost:3000",
        ).split(",")
        if origin.strip()
    ]

    # Requests per minute per IP on the endpoints that cost money to call.
    RATE_LIMIT: str = os.getenv("RATE_LIMIT", "15/minute")


settings = Settings()

logger = logging.getLogger("bss.config")

if not settings.GROQ_API_KEY:
    logger.warning(
        "GROQ_API_KEY is not set. Copy .env.example to .env and add your key "
        "from https://console.groq.com/keys before generating emails."
    )
