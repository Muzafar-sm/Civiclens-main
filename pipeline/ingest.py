import os
import logging
from datetime import datetime
from pathlib import Path
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def download_pdf(source: str, output_dir: Path) -> Path:
    """Download a PDF from a URL or copy a local file to output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if source.startswith("http://") or source.startswith("https://"):
        filename = source.split("/")[-1]
        if not filename.endswith(".pdf"):
            filename = f"document_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        response = requests.get(source)
        response.raise_for_status()
        
        output_path = output_dir / filename
        output_path.write_bytes(response.content)
        logger.info(f"Downloaded PDF from {source} to {output_path}")
        return output_path
    else:
        source_path = Path(source)
        if not source_path.exists():
            raise FileNotFoundError(f"Local file not found: {source}")
        
        filename = source_path.name
        output_path = output_dir / filename
        output_path.write_bytes(source_path.read_bytes())
        logger.info(f"Copied local PDF from {source_path} to {output_path}")
        return output_path


def ingest_sources(sources: list[str], raw_data_dir: str = "data/raw") -> list[dict]:
    """Ingest a list of PDF sources and return ingestion metadata."""
    raw_data_path = Path(raw_data_dir)
    ingestion_metadata = []
    
    for source in sources:
        try:
            pdf_path = download_pdf(source, raw_data_path)
            file_size = pdf_path.stat().st_size
            
            metadata = {
                "filename": pdf_path.name,
                "source_url": source,
                "ingested_at": datetime.now(),
                "file_size_bytes": file_size
            }
            ingestion_metadata.append(metadata)
            logger.info(f"Ingested: {metadata}")
        except Exception as e:
            logger.error(f"Failed to ingest {source}: {e}")
    
    return ingestion_metadata


if __name__ == "__main__":
    test_sources = [
        "https://example.com/document.pdf"
    ]
    ingest_sources(test_sources)
