def test_health_returns_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_startup_does_not_load_huggingface_models(client):
    """The TestClient runs startup. Startup must not call from_pretrained or pipeline()."""
    import transformers

    transformers.AutoModelForSeq2SeqLM.from_pretrained.assert_not_called()
    transformers.AutoModelForQuestionAnswering.from_pretrained.assert_not_called()
    transformers.AutoModelForCausalLM.from_pretrained.assert_not_called()
    transformers.AutoTokenizer.from_pretrained.assert_not_called()
    transformers.pipeline.assert_not_called()
