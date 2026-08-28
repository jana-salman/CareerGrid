"""Environment loading and application configuration for CareerGrid."""

import logging
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

from constants import (
    ADZUNA_DEFAULT_RESULTS,
    ADZUNA_REQUEST_TIMEOUT_SECONDS,
    DEFAULT_GEMINI_MODEL,
    INTERVIEW_UNLOCK_SCORE,
    MAX_ADZUNA_COMPANY_NAME_LENGTH,
    MAX_INTERVIEW_AUDIO_BYTES,
)

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env", override=False)
logger = logging.getLogger(__name__)


def get_environment_value(name: str, default: str | None = None) -> str | None:
    """Read one environment value after local development settings are loaded."""

    return os.getenv(name, default)


def environment_flag(name: str, *, default: bool = False) -> bool:
    """Parse a conventional boolean environment variable."""

    value = get_environment_value(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def secret_key() -> str:
    """Return the configured key or a non-persistent development key."""

    configured_key = get_environment_value("SECRET_KEY")
    if configured_key:
        return configured_key

    environment = get_environment_value("CAREERGRID_ENV", "development")
    if environment and environment.strip().lower() == "production":
        raise RuntimeError("SECRET_KEY is required when CAREERGRID_ENV=production.")

    logger.warning(
        "SECRET_KEY is not configured; using a temporary development key. "
        "Sessions will reset when the process restarts."
    )
    return secrets.token_urlsafe(32)


def get_gemini_model(default: str = DEFAULT_GEMINI_MODEL) -> str:
    """Return the configured server-side Gemini model name."""

    return get_environment_value("GEMINI_MODEL", default) or default


def build_app_config() -> dict:
    """Build Flask configuration from environment values and stable defaults."""

    return {
        "SECRET_KEY": secret_key(),
        "DEBUG": environment_flag("FLASK_DEBUG"),
        "CAREERGRID_ENV": get_environment_value("CAREERGRID_ENV", "development"),
        "ADZUNA_APP_ID": get_environment_value("ADZUNA_APP_ID"),
        "ADZUNA_APP_KEY": get_environment_value("ADZUNA_APP_KEY"),
        "ADZUNA_DEFAULT_RESULTS": ADZUNA_DEFAULT_RESULTS,
        "ADZUNA_REQUEST_TIMEOUT_SECONDS": ADZUNA_REQUEST_TIMEOUT_SECONDS,
        "MAX_ADZUNA_COMPANY_NAME_LENGTH": MAX_ADZUNA_COMPANY_NAME_LENGTH,
        "INTERVIEW_UNLOCK_SCORE": INTERVIEW_UNLOCK_SCORE,
        "MAX_INTERVIEW_AUDIO_BYTES": MAX_INTERVIEW_AUDIO_BYTES,
        "FRONTEND_DIST_DIR": BASE_DIR / "frontend" / "dist",
    }
