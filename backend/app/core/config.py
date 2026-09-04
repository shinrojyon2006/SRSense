"""
Core Configuration — Pydantic Settings management.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── Application ──────────────────────────────────────────
    APP_NAME: str = "SRSense AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # ── Database (PostgreSQL 18) ─────────────────────────────
    DATABASE_URL: str = (
        "postgresql+asyncpg://srsense:srsense_secret_2026@localhost:5432/srsense_db"
    )

    # ── Security & CORS ──────────────────────────────────────
    SECRET_KEY: str = "your-super-secret-key-change-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    RATE_LIMIT_PER_MINUTE: int = 300
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost",
    ]

    # ── AI Provider Configuration ────────────────────────────
    # Phase B: Environment-driven provider selection.
    # "heuristic" = deterministic engine (CI-safe, no external calls, default)
    # "gemini"    = Google Gemini API (requires GEMINI_API_KEY in backend env)
    # "openai"    = OpenAI API (requires OPENAI_API_KEY in backend env)
    # SECURITY: Keys MUST be backend-only env vars. Never in frontend, source, or git.
    AI_PROVIDER: str = "heuristic"
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    AI_REQUEST_TIMEOUT_SECONDS: int = 30
    AI_MAX_RETRIES: int = 2

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Return cached Settings instance."""
    return Settings()
