import logging
import time
from transformers import pipeline, AutoModelForSeq2SeqLM, AutoTokenizer, AutoModelForSequenceClassification
import torch
from tracking import log_inference

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

device = "cuda" if torch.cuda.is_available() else "cpu"

# Initialize models
summarization_model = AutoModelForSeq2SeqLM.from_pretrained("facebook/bart-large-cnn").to(device)
summarization_tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large-cnn")
summarization_pipeline = pipeline(
    "summarization",
    model=summarization_model,
    tokenizer=summarization_tokenizer,
    device=0 if torch.cuda.is_available() else -1
)

sentiment_pipeline = pipeline(
    "sentiment-analysis",
    model="distilbert-base-uncased-finetuned-sst-2-english",
    device=0 if torch.cuda.is_available() else -1
)


def summarize(text: str, doc_id: int = None) -> str:
    """Summarize text using Hugging Face model and log to MLflow."""
    start_time = time.time()
    
    # Truncate text for summarization
    encoded_input = summarization_tokenizer(text, truncation=True, max_length=1024, return_tensors="pt")
    truncated_text = summarization_tokenizer.decode(encoded_input['input_ids'][0], skip_special_tokens=True)
    
    summary_response = summarization_pipeline(truncated_text, max_length=130, min_length=30, do_sample=False)
    summary_text = summary_response[0]['summary_text'] if summary_response else "Summary not available."
    
    inference_time = time.time() - start_time
    
    if doc_id:
        log_inference(
            doc_id=doc_id,
            model_name="facebook/bart-large-cnn",
            params={"max_summary_length": 130, "min_summary_length": 30},
            metrics={"summary_length": len(summary_text), "inference_time_seconds": inference_time},
            output={"summary": summary_text}
        )
    
    return summary_text


def analyze_sentiment(text: str, doc_id: int = None) -> dict:
    """Analyze sentiment of text using Hugging Face model and log to MLflow."""
    start_time = time.time()
    
    encoded_input = sentiment_pipeline.tokenizer(text, truncation=True, max_length=512, return_tensors="pt")
    truncated_text = sentiment_pipeline.tokenizer.decode(encoded_input['input_ids'][0], skip_special_tokens=True)
    
    sentiment_response = sentiment_pipeline(truncated_text)
    sentiment_label = sentiment_response[0]['label'] if sentiment_response else "NEUTRAL"
    sentiment_score = float(sentiment_response[0]['score']) if sentiment_response else 0.0
    
    inference_time = time.time() - start_time
    
    if doc_id:
        log_inference(
            doc_id=doc_id,
            model_name="distilbert-base-uncased-finetuned-sst-2-english",
            params={"max_token_length": 512},
            metrics={"sentiment_score": sentiment_score, "inference_time_seconds": inference_time},
            output={"sentiment_label": sentiment_label, "sentiment_score": sentiment_score}
        )
    
    return {
        "label": sentiment_label,
        "score": sentiment_score
    }


if __name__ == "__main__":
    test_text = "This is a test document for CivicLens. It contains sample text to demonstrate summarization and sentiment analysis."
    print("Summary:", summarize(test_text))
    print("Sentiment:", analyze_sentiment(test_text))
