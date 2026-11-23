import pytest

UPLOADED_TEXT = "The council approved longer library hours on Tuesday."


def test_summary_response_has_contract_keys(client):
    """Shape only. The summary string is still a placeholder and is not asserted."""
    response = client.get("/api/documents/doc-123/summary", params={"complexity": "expert"})

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"summary", "complexity"}
    assert isinstance(body["summary"], str)
    assert body["summary"]
    assert body["complexity"] == "expert"


def test_sentiment_response_has_contract_keys(client):
    """Shape only. The numeric scores are still placeholders and are not asserted."""
    response = client.get("/api/documents/doc-123/sentiment")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"positive", "negative", "neutral"}
    assert all(isinstance(value, (int, float)) for value in body.values())


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Confirmed defect: POST /{document_id}/ask ignores the saved document and "
        "sends a hardcoded paragraph to the QA pipeline. This assertion is the "
        "future regression test. Do not change it to expect that paragraph."
    ),
)
def test_ask_passes_uploaded_document_to_qa_pipeline(client, mock_analysis, monkeypatch):
    upload = client.post(
        "/api/documents/upload",
        files={"file": ("note.txt", UPLOADED_TEXT.encode("utf-8"), "text/plain")},
    )
    assert upload.status_code == 200
    document_id = upload.json()["id"]

    captured = {}

    def fake_pipeline(question, context):
        captured["question"] = question
        captured["context"] = context
        return {"answer": "longer library hours", "score": 0.99}

    monkeypatch.setattr("app.api.document.ai_models.get_qa_pipeline", lambda: fake_pipeline)

    response = client.post(
        f"/api/documents/{document_id}/ask",
        json={"question": "What did the council approve?"},
    )

    assert response.status_code == 200
    assert captured["question"] == "What did the council approve?"
    assert captured["context"] == UPLOADED_TEXT
