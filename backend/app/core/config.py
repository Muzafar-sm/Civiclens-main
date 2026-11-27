"""Process configuration for the FastAPI backend.

One ``Settings`` object reads environment variables and, when present, the
repository-root ``.env`` file. Importing this module does not open a database
connection and does not create a SQLAlchemy engine.

``DATABASE_URL`` has no default. A missing URL stays unset. ``database.py``
raises when a connection is actually requested, instead of guessing a host.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[3]
_ENV_FILE = _REPO_ROOT / ".env"

_LOG_LEVELS = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}
_POSTGRES_SCHEMES = ("postgresql://", "postgresql+psycopg2://")


class Settings(BaseSettings):
    """Runtime settings. Environment variables override the defaults below."""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE) if _ENV_FILE.is_file() else None,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )

    app_name: str = "CivicLens API"
    environment: Literal["development", "test", "production"] = "development"
    debug: bool = False
    api_host: str = "0.0.0.0"
    api_port: int = Field(default=8000, validation_alias="PORT")
    database_url: str | None = None
    cors_origins: str = "*"
    log_level: str = "INFO"

    @field_validator("app_name", "api_host")
    @classmethod
    def require_text(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("must not be empty")
        return text

    @field_validator("api_port")
    @classmethod
    def port_in_range(cls, value: int) -> int:
        if not 1 <= value <= 65535:
            raise ValueError("PORT must be between 1 and 65535")
        return value

    @field_validator("database_url")
    @classmethod
    def postgres_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        if not text:
            raise ValueError("DATABASE_URL is empty")
        lowered = text.lower()
        if not lowered.startswith(_POSTGRES_SCHEMES):
            raise ValueError(
                "DATABASE_URL must start with postgresql:// or postgresql+psycopg2://"
            )
        return text

    @field_validator("cors_origins")
    @classmethod
    def origins_not_empty(cls, value: str) -> str:
        if not [item for item in value.split(",") if item.strip()]:
            raise ValueError("CORS_ORIGINS must include at least one origin")
        return value

    @field_validator("log_level")
    @classmethod
    def known_log_level(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in _LOG_LEVELS:
            allowed = ", ".join(sorted(_LOG_LEVELS))
            raise ValueError(f"LOG_LEVEL must be one of: {allowed}")
        return normalized

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return the process settings. The first call reads the environment; later calls reuse it."""
    return Settings()
