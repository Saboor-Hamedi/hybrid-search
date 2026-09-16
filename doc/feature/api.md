# API — FastAPI Backend

**File**: `src/app.py` (730 lines)
**Server**: Uvicorn on port 8000

## Server Startup

1. `python-dotenv` loads `src/.env` — makes env vars available
2. All module imports executed (heavy ones deferred via lazy imports)
3. FastAPI app created with title "Hybrid Search API"
4. CORS middleware configured for localhost origins
5. On startup event: `get_model()` loads SentenceTransformer singleton
6. Server ready to accept connections

## Complete Endpoint Reference

### Search

**`POST /search`** — Main search endpoint

Request:
```json
{
  "query": "explain attention mechanism",
  "mode": "hybrid",
  "page": 1,
  "page_size": 10,
  "fusion_strategy": "linear",
  "alpha": 0.5
}
```

| Field | Type | Default | Options |
|-------|------|---------|---------|
| `query` | string | required | Free text |
| `mode` | string | `"hybrid"` | `semantic`, `keyword`, `hybrid`, `rrf`, `ltr` |
| `page` | int | 1 | 1-based |
| `page_size` | int | 10 | 10-200 |
| `fusion_strategy` | string | `"linear"` | `linear`, `combsum`, `combmnz` |
| `alpha` | float | null | 0.0–1.0 (only for `linear`) |

Response:
```json
{
  "results": [
    {
      "doc_id": 123,
      "content": "The attention mechanism allows...",
      "score": 0.8542,
      "language": "en",
      "created_at": "2026-01-15",
      "semantic_score": 0.85,
      "bm25_score": 0.42,
      "semantic_rank": 1,
      "bm25_rank": 7,
      "semantic_weight": 0.5,
      "bm25_weight": 0.5,
      "origin_mode": "hybrid-linear",
      "strategy": "linear"
    }
  ],
  "stats": {
    "search_type": "hybrid-linear",
    "query_time_ms": 445.67,
    "total_candidates": 842,
    "returned": 10,
    "semantic_count": 57,
    "bm25_count": 114,
    "alpha": 0.5,
    "latency_stats": { "semantic": 210.5, "keyword": 65.3, "fusion": 2.1 },
    "rank_debug": {
      "semantic": [123, 456, 789, ...],
      "keyword": [789, 234, 567, ...]
    }
  },
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total_pages": 85,
    "total_results": 842
  }
}
```

### AI / RAG

**`POST /generate`** — Full RAG response (sync)

```json
{ "query": "Explain transformers",
  "contexts": [{"doc_id": "123", "content": "..."}],
  "provider": "ollama",
  "model": "qwen2.5:0.5b",
  "api_key": "",
  "base_url": "http://localhost:11434" }
```

→ `{ "answer": "Transformers are..." }`

**`POST /generate-stream`** — Streaming RAG (text/event-stream)

Same input as `/generate`, yields chunks via `StreamingResponse`.

### Document CRUD

| Method | Endpoint | Input | Returns |
|--------|----------|-------|---------|
| POST | `/documents/insert` | `{content, language}` | `{inserted: bool, doc_id: int}` |
| POST | `/documents/{id}/update` | `{content, language}` | `{updated: bool, doc_id: int}` |
| DELETE | `/documents/{id}` | — | `{deleted: bool, doc_id: int}` |

Update with empty body re-encodes existing content.

### PDF Upload

**`POST /upload-pdf`** — Multipart file upload

```
file: binary PDF (max 3 concurrent, background processing)
```

Returns `{success: true, message: "Background ingestion queued", filename}`. Processing is throttled by semaphore (max 3 concurrent PDFs).

### Export

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/export/start` | POST | Starts background task, returns `task_id` |
| `/export/status/{task_id}` | GET | `{progress: 0-100, status: "processing"}` |
| `/export/download/{task_id}` | GET | Returns JSON file |

Exports in 500-doc batches, cleaned after 1 hour.

### System

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/system/health` | GET | Document count, index sizes, HNSW config |
| `/api/system/stats` | GET | Doc count, search log count, DB info |
| `/api/system/stop-indexing` | POST | Sets global stop flag |
| `/api/system/reset` | POST | TRUNCATE CASCADE all tables |

## Internal Search Logic

```python
# app.py search_endpoint() — simplified
def search(query, mode):
    # Always run both (universal gathering)
    sem_results = search_semantic(query, conn, cursor, model, top_k=50)
    bm25_results = search_keyword(query, cursor, top_k=50)

    if mode == "semantic":   results = sem_results
    elif mode == "keyword":  results = bm25_results
    elif mode == "hybrid":   results, stats = search_hybrid(...)
    elif mode == "rrf":      results, stats = search_rrf(...)
    elif mode == "ltr":      results, stats = search_ltr(...)

    # Paginate
    paginated = results[offset:offset + page_size]

    # Format with component scores
    formatted = [SearchResult(doc_id=r[0], content=r[1], score=float(r[2]), ...)]

    # Log to search_logs
    cursor.execute("INSERT INTO search_logs ...")

    return SearchResponse(results=formatted, stats=response_stats, pagination={...})
```

## Known Bug

Lines 290 and 293: `paginated` is assigned twice identically. No functional impact.

## CORS Configuration

```python
allow_origins = [
    "http://localhost:8080", "http://127.0.0.1:8080",
    "http://localhost:8000", "http://127.0.0.1:8000",
    "http://localhost:5000", "http://127.0.0.1:5000",
    "null",
]
```
