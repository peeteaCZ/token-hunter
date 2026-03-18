"""
Runtime configuration.
Loads from .env / .env.local files at the project root,
then falls back to environment variables.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# ── Find and load .env files ──────────────────────────────────────────────────
# Project root = two levels up from this file (config/settings.py → project root)
_PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# Load in priority order (later wins):
for _candidate in [
    _PROJECT_ROOT / ".env",
    _PROJECT_ROOT / ".env.local",
    _PROJECT_ROOT / "token_hunter.egg-info" / ".env.local",  # fallback for legacy location
]:
    if _candidate.exists():
        load_dotenv(_candidate, override=False)  # don't override already-set vars


# ── Settings ──────────────────────────────────────────────────────────────────

class Settings:
    # Application
    APP_ENV: str = os.getenv("APP_ENV", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Storage
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///token_hunter.db")

    # Ingestion
    INGESTION_BATCH_SIZE: int = int(os.getenv("INGESTION_BATCH_SIZE", "100"))
    INGESTION_TIMEOUT_SECONDS: int = int(os.getenv("INGESTION_TIMEOUT_SECONDS", "30"))

    # Groq
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    # Localisation
    DEFAULT_COUNTRY: str = os.getenv("DEFAULT_COUNTRY", "cz")
    DEFAULT_LANGUAGE: str = os.getenv("DEFAULT_LANGUAGE", "cs")


settings = Settings()
