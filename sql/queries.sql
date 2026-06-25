-- Query 1: Get all documents ingested in the last 7 days
SELECT * FROM documents
WHERE ingested_at >= NOW() - INTERVAL '7 days';

-- Query 2: Get average sentiment score by day
SELECT 
    DATE(generated_at) AS day,
    AVG(sentiment_score) AS average_sentiment
FROM insights
GROUP BY DATE(generated_at)
ORDER BY day;

-- Query 3: Get documents where sentiment is NEGATIVE
SELECT d.*, i.sentiment_label, i.sentiment_score
FROM documents d
JOIN insights i ON d.id = i.document_id
WHERE i.sentiment_label = 'NEGATIVE';

-- Query 4: Count of documents processed per week
SELECT 
    DATE_TRUNC('week', ingested_at) AS week,
    COUNT(*) AS document_count
FROM documents
GROUP BY week
ORDER BY week;
