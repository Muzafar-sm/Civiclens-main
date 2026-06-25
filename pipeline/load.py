import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, Column, Integer, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(Text, nullable=False)
    source_url = Column(Text)
    ingested_at = Column(DateTime, nullable=False)
    raw_text = Column(Text)
    word_count = Column(Integer)
    page_count = Column(Integer)


class Insight(Base):
    __tablename__ = "insights"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    summary = Column(Text)
    sentiment_label = Column(Text)
    sentiment_score = Column(Float)
    model_name = Column(Text)
    generated_at = Column(DateTime, nullable=False)


def get_db_session():
    """Create and return a SQLAlchemy session."""
    db_user = os.getenv("POSTGRES_USER", "admin")
    db_password = os.getenv("POSTGRES_PASSWORD", "secret")
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "civiclens")
    
    db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    return Session()


def load_documents_and_insights(
    ingestion_metadata: list[dict],
    extraction_results: list[dict],
    insights_data: Optional[list[dict]] = None
):
    """Load documents and insights into PostgreSQL."""
    session = get_db_session()
    insights_data = insights_data or []
    
    try:
        for ingest_meta in ingestion_metadata:
            filename = ingest_meta["filename"]
            
            existing_doc = session.query(Document).filter_by(filename=filename).first()
            
            extraction_data = next(
                (er for er in extraction_results if er["filename"] == filename),
                None
            )
            
            if existing_doc:
                logger.info(f"Updating existing document: {filename}")
                existing_doc.source_url = ingest_meta["source_url"]
                existing_doc.ingested_at = ingest_meta["ingested_at"]
                if extraction_data:
                    existing_doc.raw_text = extraction_data["raw_text"]
                    existing_doc.word_count = extraction_data["word_count"]
                    existing_doc.page_count = extraction_data["page_count"]
            else:
                logger.info(f"Inserting new document: {filename}")
                doc = Document(
                    filename=filename,
                    source_url=ingest_meta["source_url"],
                    ingested_at=ingest_meta["ingested_at"],
                    raw_text=extraction_data["raw_text"] if extraction_data else None,
                    word_count=extraction_data["word_count"] if extraction_data else None,
                    page_count=extraction_data["page_count"] if extraction_data else None
                )
                session.add(doc)
                session.flush()
                
                doc_id = doc.id
                for insight in insights_data:
                    if insight.get("filename") == filename:
                        insight_entry = Insight(
                            document_id=doc_id,
                            summary=insight.get("summary"),
                            sentiment_label=insight.get("sentiment_label"),
                            sentiment_score=insight.get("sentiment_score"),
                            model_name=insight.get("model_name"),
                            generated_at=datetime.now()
                        )
                        session.add(insight_entry)
        
        session.commit()
        logger.info("Data loaded successfully into PostgreSQL")
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to load data: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    sample_ingest_meta = [
        {"filename": "test.pdf", "source_url": "local", "ingested_at": datetime.now()}
    ]
    sample_extraction = [
        {"filename": "test.pdf", "raw_text": "Test text", "word_count": 2, "page_count": 1}
    ]
    load_documents_and_insights(sample_ingest_meta, sample_extraction)
