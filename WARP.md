
# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is a **Hybrid Search System** that combines semantic (vector-based) and keyword (BM25) search capabilities. It provides multiple interfaces: a CLI menu system, a FastAPI backend, and a Flask frontend for document search and management.

The system stores documents in PostgreSQL with pgvector for embeddings and uses full-text search (FTS) for keyword matching. Documents are searchable via three modes: semantic, keyword (BM25), or hybrid (combined).

## Development Commands

### Environment Setup
```powershell
# Install dependencies
pip install -r requirements.txt

# Configure environment (copy and edit)
cp src\.env.example src\.env
# Edit src\.env with your PostgreSQL credentials and model name
```

### Running the Applications

**CLI Interface** (Interactive menu for document management):
```powershell
python src\core\main.py
```

**FastAPI Backend** (REST API on port 8000):
```powershell
cd src\core
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

**Flask Frontend** (Web UI on port 5000):
```powershell
python src\core\flask_app.py
```

**Full Stack** (Run both backend and frontend):
```powershell
# Terminal 1: Start FastAPI backend
cd src\core
uvicorn app:app --reload --host 127.0.0.1 --port 8000

# Terminal 2: Start Flask frontend
python src\core\flask_app.py
```

### Testing
```powershell
# Run search debug test
python src\core\test_search_debug.py
```

## Architecture

### System Flow
1. **Document Ingestion**: Text/PDF → Normalization → Language Detection → Embedding Generation → PostgreSQL (document + document_embedding tables)
2. **Search Flow**: Query → Model Encoding → Semantic Search (pgvector) + Keyword Search (BM25/FTS) → Score Combination → Results

### Core Components

**Entry Points**:
- `src/core/main.py` - CLI menu interface for document operations
- `src/core/app.py` - FastAPI REST API server
- `src/core/flask_app.py` - Flask web frontend (proxies to FastAPI)

**Database Layer** (`src/core/db/`):
- `db_connection.py` - PostgreSQL connection and model loading (singleton pattern)
- `operations/document_management.py` - Insert/delete document operations
- `operations/search_queries.py` - Raw semantic and BM25 query execution
- `operations/search_flask/` - Search implementations returning formatted results
  - `hybrid_search.py` - Combines semantic + BM25 with weighted scoring (α=0.5)
  - `semantic_search.py` - Pure vector similarity search
  - `keyword_search.py` - Pure BM25/FTS search
- `algorithms/BM25Algorithm.py` - BM25 implementation with caching

**Ingestion** (`src/core/ingestion/`):
- `insert_pdf_chunks.py` - PDF parsing → chunking (500 chars, 50 overlap) → batch insertion
- `unstructured_pdf_elements.py` - PDF element extraction

**Models** (`src/core/models/`):
- `ai_model.py` - Sentence transformer model loader

**Utilities** (`src/core/utils/`):
- `text_properties.py` - Text normalization (lowercase, whitespace collapse)
- `text_cleansing.py` - Heavy text cleaning for PDFs (remove headers/footers/URLs)
- `languages.py` - Language detection
- `bm25_utils.py` - BM25 index management (global state)
- `ColorScheme.py` - Console color formatting
- `rich_console.py` - Rich table/paragraph display

### Database Schema

**document** table:
- `id` (serial primary key)
- `content` (text) - normalized document text
- `language` (VARCHAR) - detected language code
- `content_tsvector` (tsvector) - full-text search vector (auto-updated via trigger)
- `created_at` (timestamp)

**document_embedding** table:
- `id` (serial primary key)
- `doc_id` (foreign key to document)
- `embedding` (VECTOR(384)) - sentence transformer embedding
- HNSW index on embedding for fast similarity search

**search_logs** table:
- Tracks query performance (query, search_type, latency_ms, results_count)

### Hybrid Search Algorithm

The hybrid search combines semantic and keyword results using weighted scoring:

```python
final_score = (semantic_score × (1 - α)) + (normalized_bm25_score × α)
```

Where:
- **α = 0.5** (default) - Equal weight for semantic and BM25
- Semantic scores are cosine similarity (0-1)
- BM25 scores are normalized via min-max to (0-1) range
- Results are merged by doc_id and sorted by final_score

**Configuration** in `src/core/db/operations/search_flask/hybrid_search.py`:
- `ALPHA = 0.5` - Adjust for more semantic (lower) or keyword (higher) weight
- `THRESHOLD = 0.65` - Minimum semantic similarity to include
- `TOP_K = 100` - Max candidates before pagination

## Key Implementation Details

### Model Loading
- Model is loaded once at startup (singleton pattern in `db_connection.py`)
- Model name from `EMBEDDER_MODEL` env var (typically `paraphrase-multilingual-MiniLM-L12-v2`)
- Produces 384-dimensional embeddings

### Text Normalization Pipeline
1. **normalize_content()** - Lowercase + collapse whitespace (for embeddings/storage)
2. **clean_page_content()** - Aggressive cleaning for PDFs (remove artifacts, URLs, emails)
3. **detect_language()** - Langdetect-based language identification

### BM25 Index Management
- Global BM25 index stored in `bm25_utils` module
- `needs_update` flag triggers rebuild after insert/delete
- Index built on-demand by `update_bm25_index()`
- Uses `rank_bm25` library with k1=1.5, b=0.75

### PDF Ingestion Process
1. Parse PDF with unstructured library
2. Detect language from first substantial text samples
3. Split into chunks (500 chars, 50 overlap) via RecursiveCharacterTextSplitter
4. Clean each chunk (headers/footers/short content filtered)
5. Batch insert with commit at end

### API Pagination
- FastAPI retrieves up to MAX_CANDIDATES=1000 results
- Pagination applied in Python (not SQL) for flexibility
- Flask frontend passes page/page_size to backend

### Environment Variables
Required in `src/.env`:
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` - PostgreSQL connection
- `EMBEDDER_MODEL` - Sentence transformer model name

## Development Patterns

### Adding a New Search Mode
1. Create function in `src/core/db/operations/search_flask/`
2. Return list of tuples: `(doc_id, content, score, language, created_at)`
3. Add endpoint in `app.py` under `/search` mode parameter
4. Update Flask frontend to handle new mode

### Modifying Hybrid Scoring
Edit `src/core/db/operations/search_flask/hybrid_search.py`:
- Change `ALPHA` for weight adjustment
- Modify normalization in BM25 score processing
- Consider implementing Reciprocal Rank Fusion (see `notes/hybrid_search.md`)

### Adding Document Processing
1. Add processing function in `src/core/ingestion/` or `src/core/utils/`
2. Call `insert_document()` with normalized content
3. Ensure `bm25_utils.needs_update = True` after batch operations

### Database Migrations
Use `queries.sql` as reference for schema. Key points:
- pgvector extension required
- tsvector trigger auto-updates on content changes
- HNSW index for vector similarity

## Important Notes

- **Windows Paths**: Use raw strings or double backslashes for file paths
- **Model Loading**: First run downloads model (~500MB), subsequent runs use cache
- **BM25 Index**: Rebuilds on first search after document changes (can be slow for large datasets)
- **Embedding Consistency**: Changing EMBEDDER_MODEL requires re-embedding all documents
- **PostgreSQL Extensions**: Requires `pgvector` extension installed
- **CORS**: FastAPI allows localhost:5000, 8000, 8080 origins

## Performance Characteristics

- **Semantic Search**: ~440ms (pgvector cosine similarity)
- **Keyword Search**: ~400ms (PostgreSQL FTS with GIN index)
- **Hybrid Search**: ~1550ms (sequential execution of both)
- **Optimization**: Consider parallel execution for hybrid search in production

## Related Documentation

See `notes/` directory for detailed algorithm explanations:
- `hybrid_search.md` - Comprehensive hybrid search documentation
- `semantic_search.md` - Vector search details
- `bm25_algorithm.md` - BM25 keyword search
