create table document (
id serial primary key,
content text,
languages vorchar(50),
created_at timestamp default current_timestamp
);
drop table document_embedding
ALTER TABLE document_comments RENAME TO document_embedding;
alter table document_embedding add column embedding VECTOR(384); -- For MiniLM-L12-v2

create table document_embedding(
id SERIAL PRIMARY KEY,
doc_id INTEGER REFERENCES document(id),
embedding VECTOR(384) -- For MiniLM-L12-v2
);
CREATE TABLE IF NOT EXISTS search_logs (
    id SERIAL PRIMARY KEY,
    query TEXT NOT NULL,
    search_type VARCHAR(20) NOT NULL,
    top_k INT DEFAULT 0,
    results_count INT DEFAULT 0,
    latency_ms DOUBLE PRECISION DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);
select * from document;


ALTER TABLE document ADD COLUMN content_tsvector tsvector;

UPDATE document SET content_tsvector = to_tsvector('simple', content);

CREATE INDEX idx_document_content_tsvector ON document USING GIN (content_tsvector);


CREATE OR REPLACE FUNCTION update_tsvector_column()
RETURNS TRIGGER AS $$
BEGIN
    -- Update the tsvector column whenever 'content' changes
    NEW.content_tsvector := to_tsvector('simple', NEW.content);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_tsvector
    BEFORE INSERT OR UPDATE OF content ON document
    FOR EACH ROW
    EXECUTE FUNCTION update_tsvector_column();


CREATE INDEX ON document_embedding USING hnsw (embedding vector_cosine_ops);

SELECT id, content, ts_rank(content_tsvector, plainto_tsquery('simple', %s)) AS score, ...
FROM document
WHERE content_tsvector @@ plainto_tsquery('simple', %s)
ORDER BY score DESC;


-- Semantic Search Query
SELECT d.id, d.content, (1 - (e.embedding <=> %s::vector)) AS similarity, ...
FROM document d
JOIN document_embedding e ON d.id = e.doc_id
WHERE (1 - (e.embedding <=> %s::vector)) >= %s
ORDER BY e.embedding <=> %s::vector DESC
LIMIT %s

