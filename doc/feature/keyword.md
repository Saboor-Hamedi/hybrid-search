# Keyword Search (PostgreSQL FTS + Python BM25)

**Files**: 
- `src/core/db/operations/search_flask/keyword_search.py` (19 lines) — thin wrapper
- `src/core/db/operations/keyword_queries.py` (77 lines) — FTS with normalization
- `src/core/db/operations/search_queries.py` (122 lines) — BM25 via ts_rank
- `src/core/db/algorithms/BM25Search.py` (251 lines) — Python rank_bm25

## Three Engines

| Engine | Function | Location | FTS Config | tsvector Source | Used By |
|--------|----------|----------|------------|-----------------|---------|
| FTS 1 | `execute_keyword_query` | `keyword_queries.py` | `'simple'` (no stem) | Pre-computed `content_tsvector` column | keyword mode display |
| FTS 2 | `execute_bm25_query` | `search_queries.py` | `'english'` (stemming) | On-the-fly `to_tsvector('english', content)` | hybrid, rrf modes |
| Python | `BM25Search.search()` | `BM25Search.py` | N/A (own tokenizer) | In-memory corpus via `rank_bm25` | LTR stage 1, CLI |

## Engine SQL

### execute_keyword_query
```sql
SELECT id, content,
       ts_rank(content_tsvector, plainto_tsquery('simple', %s)) AS score,
       language, created_at::text
FROM document
WHERE content_tsvector @@ plainto_tsquery('simple', %s)
ORDER BY score DESC LIMIT %s;
```

### execute_bm25_query
```sql
SELECT d.id, d.content,
       ts_rank(to_tsvector('english', d.content), plainto_tsquery('english', %s)) AS rank,
       d.language, d.created_at
FROM document d
WHERE to_tsvector('english', d.content) @@ plainto_tsquery('english', %s)
ORDER BY rank DESC LIMIT %s;
```

## Score Normalization

All raw FTS scores are unbounded. Normalized to [0,1] for fusion:

| Method (`HYBRID_BM25_NORM`) | Formula | When |
|-----------------------------|---------|------|
| `max` (default) | `score / max_score` | All modes |
| `log` | `log1p(score) / log1p(max_score)` | Env override |
| `minmax` | `(score - min) / (max - min)` | Env override |

```python
denom = max_score if max_score > 0 else 1.0
norm = (raw / denom) if denom > 0 else 0.0
```

## Python BM25 (BM25Search)

```python
from rank_bm25 import BM25Okapi
bm25 = BM25Okapi(tokenized_corpus, k1=1.5, b=0.75)

# Parameters
k1 = 1.5  # Term frequency saturation (higher = more TF impact)
b  = 0.75 # Length normalization (0 = no norm, 1 = full norm)
```

**Features**:
- `build_index(cursor)`: Fetches all docs from DB, tokenizes, builds BM25Okapi
- `search(query, top_k, min_score)`: Tokenizes query, gets scores, filters by min, returns top_k
- `normalize_scores(results)`: Post-hoc normalization via max/log/minmax
- Global singleton: `get_bm25_engine()` — built once, cached

## BM25 Utils Cache

**File**: `src/core/utils/bm25_utils.py` (39 lines)

```python
bm25_corpus = []      # [(doc_id, normalized_content), ...]
bm25_index = None     # BM25Okapi instance
needs_update = True    # Set to True on insert/delete

def update_bm25_index(cursor, normalize_fn):
    # Rebuilds entire index from DB
    # Filters out empty token lists
```

## Pipeline

```mermaid
graph LR
    Q[Query] --> SWITCH{Which engine?}

    SWITCH -->|hybrid/rrf| ENG1[execute_bm25_query]
    ENG1 --> SQL1[to_tsvector english]
    SQL1 --> RANK1[ts_rank]
    RANK1 --> NORM[Normalize to [0,1]]

    SWITCH -->|keyword mode| ENG2[execute_keyword_query]
    ENG2 --> SQL2[content_tsvector simple]
    SQL2 --> RANK2[ts_rank]
    RANK2 --> NORM

    SWITCH -->|LTR stage 1| ENG3[Python BM25]
    ENG3 --> BUILD[update_bm25_index]
    BUILD --> TOKEN[tokenize query]
    TOKEN --> SCORE[BM25Okapi.get_scores]
    SCORE --> NORM

    NORM --> TOP[Top-K results]
```

## Called By

- `keyword_search.py` → `app.py` (keyword mode)
- `search_queries.py:execute_bm25_query` → `hybrid_search.py`, `rrf_search.py`
- `bm25_utils.update_bm25_index` → `ltr_search.py`
- `BM25Search.search` → `main.py` (CLI), `thesis_comparator.py`
