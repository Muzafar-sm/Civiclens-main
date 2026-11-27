"""Settings tests.

Each test builds ``Settings`` with ``_env_file=None`` so a developer ``.env``
cannot change the result. Nothing in this module opens a socket.
"""

import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings

_UNIT_DATABASE_URL = "postgresql://civiclens:civiclens@127.0.0.1:1/civiclens_unit"

_SETTINGS_ENV = (
    "APP_NAME",
    "ENVIRONMENT",
    "DEBUG",
    "API_HOST",
    "PORT",
    "DATABASE_URL",
    "CORS_ORIGINS",
    "LOG_LEVEL",
)


@pytest.fixture
def clean_env(monkeypatch):
    for key in _SETTINGS_ENV:
        monkeypatch.delenv(key, raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_default_configuration(clean_env):
    settings = Settings(_env_file=None)

    assert settings.app_name == "CivicLens API"
    assert settings.environment == "development"
    assert settings.debug is False
    assert settings.api_host == "0.0.0.0"
    assert settings.api_port == 8000
    assert settings.database_url is None
    assert settings.cors_origin_list == ["*"]
    assert settings.log_level == "INFO"


def test_environment_overrides(clean_env, monkeypatch):
    monkeypatch.setenv("APP_NAME", "CivicLens Test")
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("API_HOST", "127.0.0.1")
    monkeypatch.setenv("PORT", "9001")
    monkeypatch.setenv("DATABASE_URL", _UNIT_DATABASE_URL)
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000, https://example.test")
    monkeypatch.setenv("LOG_LEVEL", "debug")

    settings = Settings(_env_file=None)

    assert settings.app_name == "CivicLens Test"
    assert settings.environment == "production"
    assert settings.debug is True
    assert settings.api_host == "127.0.0.1"
    assert settings.api_port == 9001
    assert settings.database_url == _UNIT_DATABASE_URL
    assert settings.cors_origin_list == ["http://localhost:3000", "https://example.test"]
    assert settings.log_level == "DEBUG"


def test_postgresql_psycopg_scheme_is_valid(clean_env):
    settings = Settings(
        _env_file=None,
        database_url="postgresql+psycopg2://civiclens:civiclens@127.0.0.1:1/civiclens_unit",
    )

    assert settings.database_url.startswith("postgresql+psycopg2://")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("database_url", "mysql://civiclens:civiclens@127.0.0.1:1/civiclens_unit"),
        ("database_url", "   "),
        ("environment", "staging"),
        ("api_port", 0),
        ("api_port", 70000),
        ("log_level", "verbose"),
        ("cors_origins", " , "),
        ("app_name", "  "),
        ("api_host", ""),
    ],
)
def test_invalid_configuration_is_rejected(clean_env, field, value):
    with pytest.raises(ValidationError) as caught:
        Settings(_env_file=None, **{field: value})

    assert any(error["loc"] == (field,) for error in caught.value.errors())


def test_pipeline_postgres_variables_do_not_set_database_url(clean_env, monkeypatch):
    monkeypatch.setenv("POSTGRES_HOST", "127.0.0.1")
    monkeypatch.setenv("POSTGRES_PORT", "5432")
    monkeypatch.setenv("POSTGRES_DB", "civiclens")
    monkeypatch.setenv("POSTGRES_USER", "someone")
    monkeypatch.setenv("POSTGRES_PASSWORD", "not-a-real-password")

    settings = Settings(_env_file=None)

    assert settings.database_url is None


def test_unused_redis_url_is_ignored(clean_env, monkeypatch):
    monkeypatch.setenv("REDIS_URL", "redis://127.0.0.1:1/0")

    settings = Settings(_env_file=None)

    assert not hasattr(settings, "redis_url")
    assert settings.database_url is None


def test_settings_cache_is_isolated_between_reads(clean_env, monkeypatch):
    monkeypatch.setenv("APP_NAME", "First")
    get_settings.cache_clear()
    first = get_settings()

    monkeypatch.setenv("APP_NAME", "Second")
    assert get_settings().app_name == "First"

    get_settings.cache_clear()
    assert get_settings().app_name == "Second"
    assert first.app_name == "First"


def test_importing_settings_does_not_create_an_engine():
    import app.core.config as config

    assert not hasattr(config, "engine")
    assert not hasattr(config, "create_engine")


def test_get_engine_reads_database_url_without_connecting(clean_env, monkeypatch):
    import app.database as database

    monkeypatch.setenv("DATABASE_URL", _UNIT_DATABASE_URL)
    get_settings.cache_clear()
    database._engine = None
    try:
        engine = database.get_engine()
        assert engine.url.host == "127.0.0.1"
        assert engine.url.port == 1
        assert engine.url.database == "civiclens_unit"
    finally:
        database._engine = None


def test_get_engine_rejects_a_missing_database_url(clean_env):
    import app.database as database

    get_settings.cache_clear()
    database._engine = None

    with pytest.raises(RuntimeError, match="DATABASE_URL is not set"):
        database.get_engine()


def test_fastapi_app_uses_configured_name():
    from main import app

    assert app.title == "CivicLens API"
