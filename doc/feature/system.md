# System Management

**Endpoints**: `src/app.py:604-716`
**Global State**: `src/core/utils/system_state.py` (19 lines)

## Endpoints

### Health Check

**`GET /api/system/health`** — Database and index telemetry

```json
{
  "status": "healthy",
  "document_count": 50000,
  "embedding_count": 50000,
  "index_size": "256 MB",
  "doc_storage": "128 MB",
  "embed_storage": "512 MB",
  "hnsw_config": {
    "index_name": "document_embedding_embedding_idx",
    "m": 16,
    "ef_construction": 64
  }
}
```

SQL queries:
```sql
SELECT COUNT(*) FROM document;
SELECT COUNT(*) FROM document_embedding;
SELECT pg_size_pretty(pg_relation_size('document_embedding_embedding_idx'));
SELECT pg_size_pretty(pg_total_relation_size('document'));
SELECT pg_size_pretty(pg_total_relation_size('document_embedding'));
```

### System Stats

**`GET /api/system/stats`** — Document and search log counts

```json
{
  "document_count": 50000,
  "search_log_count": 1250,
  "db_info": {
    "host": "localhost",
    "database": "search",
    "user": "postgres"
  }
}
```

### Stop Indexing

**`POST /api/system/stop-indexing`** — Graceful stop for PDF ingestion

```python
from core.utils import system_state
system_state.request_stop()  # Sets stop_requested = True
```

Checked by `insert_pdf_chunks.py` after each chunk.

### Reset Database

**`POST /api/system/reset`** — Full data wipe

```python
system_state.request_stop()  # Safety: stop before reset
cursor.execute("TRUNCATE TABLE document_embedding, document, search_logs RESTART IDENTITY CASCADE;")
bm25_utils.needs_update = True
system_state.clear_stop()
```

## Global State

```python
# src/core/utils/system_state.py
stop_requested = False
active_indexing_jobs = 0

def request_stop():     # Set flag
def clear_stop():       # Clear flag
def is_stop_requested(): # Check flag
```

## Export System

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/export/start` | POST | Start background task, return `task_id` |
| `/export/status/{task_id}` | GET | Poll progress: `{progress: 0-100, status: "processing"}` |
| `/export/download/{task_id}` | GET | Download completed JSON file |

**Implementation** (`src/core/export/core_logic.py`):
- Fetches documents in batches of 500 via `ORDER BY id ASC LIMIT 500 OFFSET N`
- Writes to `temp_exports/export_{task_id}_{timestamp}.json`
- Cleanup: removes exports older than 1 hour on each new export
- Progress tracking: 10-100% shared via global `export_tasks` dict
- Uses `BackgroundTasks` in FastAPI

## Search Logging

Every search automatically logged:

```sql
INSERT INTO search_logs (query, search_type, top_k, results_count, latency_ms)
VALUES (%s, %s, %s, %s, %s);
```

Fields: raw query, mode name, page_size, returned count, wall-clock time in ms.

## Flask Proxies

Flask proxies system endpoints to FastAPI:

| Flask Route | FastAPI Target |
|-------------|----------------|
| `/api/stats` | `/api/system/stats` |
| `/api/stop-indexing` | `/api/system/stop-indexing` |
| `/api/reset` | `/api/system/reset` |
| `/upload-pdf` | `/upload-pdf` |

## Config (`.env`)

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=hybrid_search
DB_USER=postgres
DB_PASSWORD=your_password
```
