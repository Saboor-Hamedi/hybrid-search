# RRF Search — Reciprocal Rank Fusion

**File**: `src/core/db/operations/search_flask/rrf_search.py` (49 lines)
**Scorer**: `src/core/db/algorithms/RRFScores.py` (138 lines)

## Concept

RRF combines ranked lists based on **position**, not score magnitude. It is **scale-agnostic** — the absolute score values don't matter, only the relative ordering. This makes it robust across different retrieval systems with different scoring scales.

## Formula

```
RRF_score(d) = 1 / (k + rank_sem(d))  +  1 / (k + rank_bm25(d))
```

Where:
- `rank_sem(d)` = rank of document d in semantic results (1-based)
- `rank_bm25(d)` = rank of document d in BM25 results (1-based)
- `k` = smoothing constant (default: 60)

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `k` | 60 | Smoothing constant. Higher = less impact from top ranks |
| `top_k` | 10 | Passed through from API call |
| Semantic threshold | 0.1 | Intentionally low for broad recall |
| BM25 query | `execute_bm25_query` | PostgreSQL FTS with english config |

## Algorithm

```python
# Step 1: Get candidates
sem_results = execute_vector_query(query, conn, cursor, model, top_k=10, threshold=0.1)
bm25_results = execute_bm25_query(query, cursor, top_k=10)

# Step 2: Compute RRF scores
for rank, item in enumerate(sem_results, 1):
    rrf_scores[doc_id] += 1.0 / (k + rank)

for rank, item in enumerate(bm25_results, 1):
    rrf_scores[doc_id] += 1.0 / (k + rank)

# Step 3: Sort by RRF score
final = sorted(results, key=lambda x: x[2], reverse=True)[:top_k]
```

## Score Range

| Scenario | Score |
|----------|-------|
| Best case (rank 1 in both) | `1/(60+1) + 1/(60+1)` = **0.0328** |
| Rank 10 in one, not found in other | `1/(60+10)` = **0.0143** |
| Rank 50 in one, rank 50 in other | `1/(60+50) + 1/(60+50)` = **0.0182** |

## RRF vs Linear

| Aspect | RRF | Linear |
|--------|-----|--------|
| Score magnitude | Ignored | Used |
| Normalization | Not needed | Critical |
| Parameters | k (60) | α (0.5) |
| Tuning | Minimal | Must be optimized |
| Robustness | High | Moderate |
| Best for | Diverse domains | Known domain |

## Component Output

```python
components[doc_id] = {
    "semantic_score": score,    # raw semantic score
    "bm25_score": score,        # raw BM25 score
    "semantic_rank": 1..N,
    "bm25_rank": 1..N,
    "rrf_score": 0.0143,        # final RRF score
}
```

## Pipeline

```mermaid
graph LR
    Q[Query] --> SEM[Semantic<br/>top_k=10, threshold=0.1]
    Q --> BM25[BM25 FTS<br/>top_k=10, english]
    SEM --> RRF1[Score: 1/(k+rank_sem)]
    BM25 --> RRF2[Score: 1/(k+rank_bm25)]
    RRF1 --> SUM[Sum scores per doc_id]
    RRF2 --> SUM
    SUM --> SORT[Sort desc by RRF score]
    SORT --> TOP[Top-K results + components]
```

## Dead Code Note

`RRFScores.py` contains a `process_list()` helper function (lines 43-74) that was intended for weighted RRF processing but is **never called**. The actual logic uses the two explicit loops at lines 78-110.
