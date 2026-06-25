import logging
import argparse
from datetime import datetime
from ingest import ingest_sources
from extract import process_raw_pdfs
from transform import transform_processed_texts
from load import load_documents_and_insights
from data_quality import run_data_quality_checks

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_full_pipeline(sources: list[str]):
    """Run the full ETL pipeline: ingest → extract → transform → load → data quality."""
    logger.info("Starting full ETL pipeline")
    
    try:
        logger.info("Step 1: Ingesting sources")
        ingestion_metadata = ingest_sources(sources)
        
        logger.info("Step 2: Extracting text from PDFs")
        extraction_results = process_raw_pdfs()
        
        logger.info("Step 3: Transforming text data")
        transformed_docs = transform_processed_texts()
        
        logger.info("Step 4: Loading data into database")
        load_documents_and_insights(ingestion_metadata, extraction_results)
        
        logger.info("Step 5: Running data quality checks")
        checks_passed = run_data_quality_checks()
        if not checks_passed:
            logger.warning("Data quality checks failed, but pipeline completed")
        
        logger.info("ETL pipeline completed successfully")
    except Exception as e:
        logger.error(f"ETL pipeline failed: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(description="CivicLens ETL Pipeline")
    parser.add_argument("--source", type=str, nargs="+", required=True, help="List of PDF URLs or local file paths")
    parser.add_argument("--mode", type=str, choices=["full", "incremental"], default="full", help="Pipeline mode")
    args = parser.parse_args()
    
    if args.mode == "full":
        run_full_pipeline(args.source)
    else:
        logger.info("Incremental mode not implemented yet")


if __name__ == "__main__":
    main()
