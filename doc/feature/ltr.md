# LTR Search — Learning to Rank (Cross-Encoder)

**File**: `src/core/db/operations/search_flask/ltr_search.py` (68 lines)
**Scorer**: `src/core/db/operations/search_flask/LTRScorer.py` (61 lines)

## Two-Stage Architecture

```
Stage 1 (Retrieval):     Hybrid search → 50 candidates
Stage 2 (Re-ranking):    Cross-Encoder → score each (query, doc) pair → re-sort
```

## Stage 1: Hybrid Retrieval

| Parameter | Value | Notes |
|-----------|-------|-------|
| Semantic threshold | 0.1 | Low for broad recall |
| `candidate_k` | 50 | Configurable via API |
| Hybrid alpha | 0.5 | Hardcoded |
| BM25 engine | **Python rank_bm25** | NOT PostgreSQL ts_rank |

Uses Python rank_bm25 (via `bm25_utils` cache) instead of PostgreSQL FTS for more granular per-query BM25 scoring.

```python
# Stage 1
sem_results = execute_vector_query(query, conn, cursor, model, top_k=50, threshold=0.1)

bm25_utils.update_bm25_index(cursor, normalize_content)
scores = bm25_utils.bm25_index.get_scores(normalize_content(query).split())
bm25_results = [(doc_id, content, raw) for i, (doc_id, content) in enumerate(bm25_utils.bm25_corpus) if scores[i] > 0]

scorer = HybridScorer(alpha=0.5)
candidates, components = scorer.combine(sem_results, bm25_results, top_k=50)
```

## Stage 2: Cross-Encoder Re-ranking

```python
pairs = [[query, doc_content[:2000]] for doc in candidates]  # Truncate to 2000 chars
scores = model.predict(pairs)                                 # Cross-Encoder scores

# Replace original scores with Cross-Encoder scores, re-sort
for idx, score in enumerate(scores):
    new_tuple = (original[0], original[1], float(score), original[3], original[4])
    
scored_candidates.sort(key=lambda x: x[2], reverse=True)
return scored_candidates[:top_k]  # Final top-10
```

## LTRScorer Singleton

```python
class LTRScorer:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            from sentence_transformers import CrossEncoder   # Lazy import
            cls._model = CrossEncoder(
                'cross-encoder/ms-marco-MiniLM-L-6-v2',     # Lightweight
                max_length=512                               # Token limit
            )
        return cls._instance
```

| Property | Value |
|----------|-------|
| Model | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| Max tokens | 512 |
| Content truncation | First 2000 characters |
| Score range | Unbounded (typically -10 to +10) |
| Loading | Singleton, lazy, thread-safe |

## Performance

| Stage | Candidates | Time | Notes |
|-------|-----------|------|-------|
| Stage 1 (Hybrid) | 50 | ~200ms | pgvector + Python BM25 |
| Stage 2 (Cross-Encoder) | 50 | ~500-700ms | 50 model predictions |
| **Total** | — | **~800ms** | 3-4x slower than hybrid |

## Pipeline

```mermaid
graph TD
    Q[Query] --> S1[Stage 1: Retrieval]

    S1 --> SEM[pgvector cosine<br/>top_k=50, threshold=0.1]
    S1 --> BM25[Python rank_bm25<br/>via bm25_utils]

    SEM --> HYB[Hybrid Linear α=0.5]
    BM25 --> HYB
    HYB --> TOP50[Top 50 candidates]

    TOP50 --> S2[Stage 2: Re-ranking]

    S2 --> PAIR[Create (query, doc) pairs<br/>doc truncated to 2000 chars]
    PAIR --> CE[Cross-Encoder predict<br/>ms-marco-MiniLM]
    CE --> RERANK[Re-sort by CE score]
    RERANK --> FINAL[Top-10 final results]
```

## When to Use LTR

| Scenario | Recommendation |
|----------|---------------|
| Precision is critical | Use LTR |
| Latency < 500ms required | Use hybrid or semantic instead |
| Large candidate pool | Increase candidate_k (tradeoff: latency) |
| Short queries (< 5 words) | LTR helps disambiguate |
