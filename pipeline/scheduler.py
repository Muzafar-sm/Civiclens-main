import logging
import time
import schedule
from run_pipeline import run_full_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def scheduled_pipeline_run():
    """Run the ETL pipeline on a schedule."""
    logger.info("Starting scheduled pipeline run")
    # Default sources (can be extended)
    default_sources = []
    try:
        run_full_pipeline(default_sources)
        logger.info("Scheduled pipeline run completed successfully")
    except Exception as e:
        logger.error(f"Scheduled pipeline run failed: {e}")


def main():
    # Schedule to run every day at 6:00 AM
    schedule.every().day.at("06:00").do(scheduled_pipeline_run)
    
    logger.info("Scheduler started. Waiting for 06:00 AM...")
    
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
