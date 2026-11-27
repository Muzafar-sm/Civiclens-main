from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings

Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False)

_engine = None


def get_engine():
    """Build the SQLAlchemy engine on first use.

    ``create_engine`` does not open a connection. The first query does.
    There is no default URL: a missing ``DATABASE_URL`` is an error here,
    not a connection to some other Postgres instance.
    """
    global _engine
    if _engine is None:
        url = get_settings().database_url
        if not url:
            raise RuntimeError(
                "DATABASE_URL is not set. CivicLens will not fall back to a default database."
            )
        _engine = create_engine(url)
    return _engine


def get_db():
    db = SessionLocal(bind=get_engine())
    try:
        yield db
    finally:
        db.close()
