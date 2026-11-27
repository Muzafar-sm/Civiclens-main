"""Importing this package registers the schema tables on the shared metadata."""

from app.models.document import Document, Insight

__all__ = ["Document", "Insight"]
