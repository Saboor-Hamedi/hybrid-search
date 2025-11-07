CREATE EXTENSION vector;
SELECT * FROM pg_available_extensions WHERE name = 'vector';

CREATE TABLE document (
id serial PRIMARY KEY,
content TEXT,
languages VARCHAR(50),
created_at timestamp DEFAULT CURRENT_TIMESTAMP
);
select * from document;
select * from document_embedding;
drop table document;

CREATE TABLE IF NOT EXISTS document_comments (
    id SERIAL PRIMARY KEY,
    doc_id INTEGER REFERENCES document(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
truncate document_embedding;
truncate document;

CREATE TABLE IF NOT EXISTS search_logs (
    id SERIAL PRIMARY KEY,
    query TEXT NOT NULL,
    search_type VARCHAR(20) NOT NULL,
    top_k INT DEFAULT 0,
    results_count INT DEFAULT 0,
    latency_ms DOUBLE PRECISION DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);




