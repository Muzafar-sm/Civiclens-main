CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    filename TEXT NOT NULL,
    source_url TEXT,
    ingested_at TIMESTAMP NOT NULL,
    raw_text TEXT,
    word_count INT,
    page_count INT
);

CREATE TABLE IF NOT EXISTS insights (
    id SERIAL PRIMARY KEY,
    document_id INT REFERENCES documents(id) NOT NULL,
    summary TEXT,
    sentiment_label TEXT,
    sentiment_score FLOAT,
    model_name TEXT,
    generated_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_documents_ingested_at ON documents(ingested_at);
CREATE INDEX IF NOT EXISTS idx_insights_document_id ON insights(document_id);
