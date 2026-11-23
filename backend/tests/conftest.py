"""Test bootstrap.

Importing the FastAPI app executes ``app.ai.models``, which imports Torch and
Transformers at module level. Those imports are replaced here, before the app
is imported, so collection never loads weights or contacts Hugging Face.

``initialize_models()`` is the startup hook that would call
``from_pretrained``. The client fixture replaces it with a no-op. TestClient
still runs the real startup event; the event just does not load models.
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# A mistaken database import must not reach the Postgres already on this machine.
# Port 1 refuses the connection immediately. create_engine() itself does not connect.
os.environ["DATABASE_URL"] = "postgresql://civiclens_test:civiclens_test@127.0.0.1:1/civiclens_tests"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"

_torch = MagicMock()
_torch.cuda.is_available.return_value = False
sys.modules["torch"] = _torch
sys.modules["transformers"] = MagicMock()
sys.modules["pdfminer"] = MagicMock()
sys.modules["pdfminer.high_level"] = MagicMock()
sys.modules["pdfminer.layout"] = MagicMock()

from main import app  # noqa: E402


ANALYSIS_FIXTURE = {
    "summary": "fixture-summary",
    "sentiment": {"positive": 0.25, "negative": 0.25, "neutral": 0.5},
    "translations": {"es": "fixture-es", "fr": "fixture-fr"},
}


@pytest.fixture(autouse=True)
def _isolate_model_imports():
    """Clear stub call history so one test cannot leak a from_pretrained call into the next."""
    import torch
    import transformers

    torch.reset_mock()
    transformers.reset_mock()
    torch.cuda.is_available.return_value = False
    yield


@pytest.fixture
def client(monkeypatch):
    from app.ai.models import ai_models

    monkeypatch.setattr(ai_models, "initialize_models", lambda: None)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_analysis(monkeypatch):
    """Replace document analysis with an in-memory fixture. Returns the texts it received."""
    calls = []

    def fake_analyze(text: str):
        calls.append(text)
        return dict(ANALYSIS_FIXTURE)

    monkeypatch.setattr("app.api.document.analyze_document_backend", fake_analyze)
    return calls
