import logging
from datetime import datetime
from dotenv import load_dotenv
from load import get_db_session, Document, Insight

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


def run_data_quality_checks():
    """Run data quality checks on the database."""
    session = get_db_session()
    checks_passed = True
    
    try:
        # Check 1: No null raw_text and word_count > 0 in documents
        logger.info("Running check 1: Documents - no null raw_text, word_count > 0")
        null_text_docs = session.query(Document).filter(Document.raw_text.is_(None)).count()
        low_word_count_docs = session.query(Document).filter(Document.word_count <= 0).count()
        
        if null_text_docs > 0 or low_word_count_docs > 0:
            logger.error(f"Check 1 failed: {null_text_docs} docs with null raw_text, {low_word_count_docs} docs with word_count <=0")
            checks_passed = False
        else:
            logger.info("Check 1 passed")
        
        # Check 2: Sentiment score between -1.0 and 1.0
        logger.info("Running check 2: Insights - sentiment_score between -1 and 1")
        invalid_sentiment = session.query(Insight).filter(
            (Insight.sentiment_score < -1.0) | (Insight.sentiment_score > 1.0)
        ).count()
        
        if invalid_sentiment > 0:
            logger.error(f"Check 2 failed: {invalid_sentiment} insights with invalid sentiment score")
            checks_passed = False
        else:
            logger.info("Check 2 passed")
        
        # Check 3: No duplicate filenames in documents
        logger.info("Running check 3: Documents - no duplicate filenames")
        from sqlalchemy import func
        duplicates = session.query(
            Document.filename, func.count(Document.id).label('count')
        ).group_by(Document.filename).having(func.count(Document.id) > 1).all()
        
        if duplicates:
            logger.error(f"Check 3 failed: Duplicate filenames found: {duplicates}")
            checks_passed = False
        else:
            logger.info("Check 3 passed")
        
        return checks_passed
    except Exception as e:
        logger.error(f"Data quality checks failed: {e}")
        return False
    finally:
        session.close()


if __name__ == "__main__":
    run_data_quality_checks()
