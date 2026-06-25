import logging
import re
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """Clean text by normalizing whitespace and removing common header/footer patterns."""
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"Page \d+ of \d+", "", text)
    text = re.sub(r"^\d+\s*$", "", text, flags=re.MULTILINE)
    return text


def chunk_text(text: str, max_words: int = 1000) -> list[str]:
    """Split text into chunks of max_words."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_words):
        chunk = " ".join(words[i:i + max_words])
        chunks.append(chunk)
    return chunks


def transform_processed_texts(processed_data_dir: str = "data/processed") -> list[dict]:
    """Transform processed text files into structured data ready for DB insertion."""
    processed_path = Path(processed_data_dir)
    transformed_docs = []
    
    if not processed_path.exists():
        logger.warning(f"Processed data directory not found: {processed_path}")
        return transformed_docs
    
    for txt_file in processed_path.glob("*.txt"):
        try:
            raw_text = txt_file.read_text(encoding="utf-8")
            cleaned_text = clean_text(raw_text)
            chunks = chunk_text(cleaned_text)
            
            doc_data = {
                "filename": txt_file.stem + ".pdf",
                "raw_text": raw_text,
                "cleaned_text": cleaned_text,
                "chunks": chunks,
                "word_count": len(cleaned_text.split())
            }
            transformed_docs.append(doc_data)
            logger.info(f"Transformed {txt_file.name} into {len(chunks)} chunks")
        except Exception as e:
            logger.error(f"Failed to transform {txt_file.name}: {e}")
    
    return transformed_docs


if __name__ == "__main__":
    transform_processed_texts()
