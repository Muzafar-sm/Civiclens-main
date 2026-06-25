import os
from dotenv import load_dotenv

load_dotenv()

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "mlruns/")
EXPERIMENT_NAME = "civiclens-nlp-pipeline"
