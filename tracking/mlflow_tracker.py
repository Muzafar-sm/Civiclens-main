import logging
import mlflow
import json
from pathlib import Path
from .config import MLFLOW_TRACKING_URI, EXPERIMENT_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def log_inference(doc_id, model_name, params, metrics, output):
    """Log inference run to MLflow."""
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT_NAME)
    
    with mlflow.start_run(run_name=f"inference-doc-{doc_id}"):
        mlflow.log_param("model_name", model_name)
        for key, value in params.items():
            mlflow.log_param(key, value)
        
        for key, value in metrics.items():
            mlflow.log_metric(key, value)
        
        output_path = Path("mlflow_artifacts")
        output_path.mkdir(exist_ok=True)
        output_file = output_path / f"doc_{doc_id}_output.json"
        with open(output_file, "w") as f:
            json.dump(output, f)
        
        mlflow.log_artifact(str(output_file))
        logger.info(f"Logged inference for doc {doc_id} to MLflow")


if __name__ == "__main__":
    log_inference(
        doc_id=1,
        model_name="test-model",
        params={"chunk_size": 1000, "max_summary_length": 130},
        metrics={"summary_length": 100, "sentiment_score": 0.8, "inference_time_seconds": 2.5},
        output={"summary": "Test summary", "sentiment": "positive"}
    )
