import logging
from datetime import datetime
from pathlib import Path
import pdfplumber

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_path: Path) -> tuple[str, dict]:
    """Extract text from a PDF file using pdfplumber."""
    raw_text = ""
    page_count = 0
    
    with pdfplumber.open(pdf_path) as pdf:
        page_count = len(pdf.pages)
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                raw_text += text + "\n"
    
    word_count = len(raw_text.split())
    metadata = {
        "word_count": word_count,
        "page_count": page_count,
        "extracted_at": datetime.now()
    }
    
    return raw_text, metadata


def process_raw_pdfs(raw_data_dir: str = "data/raw", processed_data_dir: str = "data/processed") -> list[dict]:
    """Process all PDFs in raw_data_dir and save extracted text to processed_data_dir."""
    raw_path = Path(raw_data_dir)
    processed_path = Path(processed_data_dir)
    processed_path.mkdir(parents=True, exist_ok=True)
    
    extraction_results = []
    
    if not raw_path.exists():
        logger.warning(f"Raw data directory not found: {raw_path}")
        return extraction_results
    
    for pdf_file in raw_path.glob("*.pdf"):
        try:
            raw_text, metadata = extract_text_from_pdf(pdf_file)
            
            txt_filename = pdf_file.stem + ".txt"
            txt_path = processed_path / txt_filename
            txt_path.write_text(raw_text, encoding="utf-8")
            
            result = {
                "filename": pdf_file.name,
                "txt_filename": txt_filename,
                "raw_text": raw_text,
                **metadata
            }
            extraction_results.append(result)
            logger.info(f"Extracted text from {pdf_file.name}, saved to {txt_filename}")
        except Exception as e:
            logger.error(f"Failed to process {pdf_file.name}: {e}")
    
    return extraction_results


if __name__ == "__main__":
    process_raw_pdfs()
