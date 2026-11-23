def test_upload_without_file_returns_validation_error(client, mock_analysis):
    response = client.post("/api/documents/upload")

    assert response.status_code == 422
    body = response.json()
    assert isinstance(body["detail"], list)
    assert body["detail"]
    assert any("file" in item.get("loc", []) for item in body["detail"])
    assert mock_analysis == []


def test_unsupported_file_type_returns_400(client, mock_analysis):
    response = client.post(
        "/api/documents/upload",
        files={
            "file": (
                "note.docx",
                b"not a word document",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert isinstance(detail, str)
    assert "Unsupported file type" in detail
    assert mock_analysis == []


def test_empty_text_file_returns_400(client, mock_analysis):
    response = client.post(
        "/api/documents/upload",
        files={"file": ("empty.txt", b"", "text/plain")},
    )

    assert response.status_code == 400
    assert "No text content" in response.json()["detail"]
    assert mock_analysis == []


def test_text_upload_returns_analysis_contract(client, mock_analysis):
    source = "The council approved longer library hours on Tuesday."

    response = client.post(
        "/api/documents/upload",
        files={"file": ("note.txt", source.encode("utf-8"), "text/plain")},
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"id", "title", "summary", "sentiment", "translations"}
    assert body["id"].startswith("doc_")
    assert body["title"] == "note.txt"
    assert body["summary"] == "fixture-summary"
    assert body["sentiment"] == {"positive": 0.25, "negative": 0.25, "neutral": 0.5}
    assert body["translations"] == {"es": "fixture-es", "fr": "fixture-fr"}
    assert mock_analysis == [source]
