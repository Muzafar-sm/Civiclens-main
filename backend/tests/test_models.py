"""Metadata checks for the physical schema. No database connection is opened."""

import importlib.util
from pathlib import Path

import pytest
from sqlalchemy import DateTime, Float, Integer, Text

from app.core.config import get_settings
from app.database import Base
from app.models import Document, Insight

_REPO_ROOT = Path(__file__).resolve().parents[2]
_UNIT_DATABASE_URL = "postgresql://civiclens:civiclens@127.0.0.1:1/civiclens_unit"


def _pipeline_load():
    spec = importlib.util.spec_from_file_location(
        "civiclens_pipeline_load",
        _REPO_ROOT / "pipeline" / "load.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_documents_table_matches_schema():
    table = Document.__table__

    assert table.name == "documents"
    assert list(table.primary_key.columns.keys()) == ["id"]
    assert isinstance(table.c.id.type, Integer)
    assert table.c.id.nullable is False
    assert [column.name for column in table.columns] == [
        "id",
        "filename",
        "source_url",
        "ingested_at",
        "raw_text",
        "word_count",
        "page_count",
    ]
    assert isinstance(table.c.filename.type, Text)
    assert table.c.filename.nullable is False
    assert isinstance(table.c.source_url.type, Text)
    assert table.c.source_url.nullable is True
    assert isinstance(table.c.ingested_at.type, DateTime)
    assert table.c.ingested_at.type.timezone is False
    assert table.c.ingested_at.nullable is False
    assert isinstance(table.c.raw_text.type, Text)
    assert table.c.raw_text.nullable is True
    assert isinstance(table.c.word_count.type, Integer)
    assert table.c.word_count.nullable is True
    assert isinstance(table.c.page_count.type, Integer)
    assert table.c.page_count.nullable is True
    assert table.c.filename.unique is not True
    assert {index.name for index in table.indexes} == {"idx_documents_ingested_at"}
    assert "title" not in table.c
    assert "content" not in table.c


def test_insights_table_matches_schema():
    table = Insight.__table__
    foreign_keys = list(table.foreign_keys)

    assert table.name == "insights"
    assert list(table.primary_key.columns.keys()) == ["id"]
    assert isinstance(table.c.id.type, Integer)
    assert [column.name for column in table.columns] == [
        "id",
        "document_id",
        "summary",
        "sentiment_label",
        "sentiment_score",
        "model_name",
        "generated_at",
    ]
    assert len(foreign_keys) == 1
    assert foreign_keys[0].column.table.name == "documents"
    assert foreign_keys[0].column.name == "id"
    assert table.c.document_id.nullable is False
    assert isinstance(table.c.summary.type, Text)
    assert table.c.summary.nullable is True
    assert isinstance(table.c.sentiment_label.type, Text)
    assert table.c.sentiment_label.nullable is True
    assert isinstance(table.c.sentiment_score.type, Float)
    assert table.c.sentiment_score.nullable is True
    assert isinstance(table.c.model_name.type, Text)
    assert table.c.model_name.nullable is True
    assert isinstance(table.c.generated_at.type, DateTime)
    assert table.c.generated_at.type.timezone is False
    assert table.c.generated_at.nullable is False
    assert {index.name for index in table.indexes} == {"idx_insights_document_id"}


def test_models_share_backend_metadata():
    assert Document.__table__.metadata is Base.metadata
    assert Insight.__table__.metadata is Base.metadata
    assert set(Base.metadata.tables) == {"documents", "insights"}
    assert Document.insights.property.mapper.class_ is Insight
    assert Insight.document.property.mapper.class_ is Document


def test_pipeline_uses_the_same_model_classes():
    load = _pipeline_load()

    assert load.Document is Document
    assert load.Insight is Insight
    assert not hasattr(load, "Base")


def test_pipeline_session_uses_central_database_url(monkeypatch):
    import app.database as database

    monkeypatch.setenv("DATABASE_URL", _UNIT_DATABASE_URL)
    monkeypatch.setenv("POSTGRES_HOST", "not-the-api-host")
    monkeypatch.setenv("POSTGRES_USER", "pipeline-user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "pipeline-password")
    get_settings.cache_clear()
    database._engine = None
    load = _pipeline_load()
    session = load.get_db_session()
    try:
        bind = session.get_bind()
        assert bind.url.host == "127.0.0.1"
        assert bind.url.port == 1
        assert bind.url.database == "civiclens_unit"
        assert "not-the-api-host" not in bind.url.render_as_string(hide_password=True)
    finally:
        session.close()
        database._engine = None
        get_settings.cache_clear()


def test_pipeline_session_rejects_a_missing_database_url(monkeypatch):
    import app.database as database

    monkeypatch.delenv("DATABASE_URL", raising=False)
    get_settings.cache_clear()
    database._engine = None
    load = _pipeline_load()
    with pytest.raises(RuntimeError, match="DATABASE_URL is not set"):
        load.get_db_session()
    database._engine = None
    get_settings.cache_clear()
