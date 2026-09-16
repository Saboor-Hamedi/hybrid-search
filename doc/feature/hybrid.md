# Hybrid Search (Fusion Engine)

**Orchestrator**: `src/core/db/operations/search_flask/hybrid_search.py` (109 lines)
**Scorer**: `src/core/db/operations/search_flask/HybridScorer.py` (147 lines)

## Flow

1. Execute **semantic** search via `execute_vector_query(query, conn, cursor, model, top_k, threshold)`
2. Execute **keyword** search via `execute_bm25_query(query, cursor, top_k)`
3. Determine α (BM25 weight) via priority chain
4. Normalize both score lists to [0,1] independently
5. Apply selected fusion strategy (linear/combsum/combmnz)
6. Sort by fused score descending, return top_k
7. Return component scores per document for frontend analysis

## Alpha Priority Chain

```python
# Priority: API param > BM25_WEIGHT env > SEMANTIC_WEIGHT env > 0.5
if alpha_param is not None:         ALPHA = float(alpha_param)
elif BM25_WEIGHT env exists:        ALPHA = float(BM25_WEIGHT)
elif SEMANTIC_WEIGHT env exists:    ALPHA = 1.0 - float(SEMANTIC_WEIGHT)
else:                               ALPHA = 0.5
```

## Score Normalization

### HybridScorer._normalize_values(scores, method)

| Method | Formula | Notes |
|--------|---------|-------|
| `max` (default) | `s / max_s` | Preserves relative ratios |
| `log` | `log1p(s) / log1p(max_s)` | Good for outlier-heavy distributions |
| `minmax` | `(s - min_s) / (max_s - min_s)` | Always uses full [0,1] range |

For combSUM/combMNZ, BM25 normalization is forced to `max` (minmax would zero out the lowest score).

## Fusion Strategies

### 1. Linear Weighted (Default)
```
score = (b_norm * α) + (s_norm * (1 - α))
```
Range: [0, 1]

### 2. CombSUM
```
score = s_norm + b_norm
```
Range: [0, 2]. Forces BM25 normalization to `max`.

### 3. CombMNZ
```
count = (s_norm > 1e-6) + (b_norm > 1e-6)
score = (s_norm + b_norm) * count
```
Penalizes docs found by only one retrieval method. Forces BM25 normalization to `max`.

## Component Output

```python
components[doc_id] = {
    "semantic_score": 0.85,      # normalized
    "bm25_score": 0.42,          # normalized
    "semantic_rank": 1,
    "bm25_rank": 7,
    "semantic_weight": 1 - α if linear else 1.0,
    "bm25_weight": α if linear else 1.0,
    "strategy": "linear" | "combsum" | "combmnz"
}
```

## Latency Stats

```python
stats["latency_stats"] = {
    "semantic": (t_sem - t_start) * 1000,   # ms
    "keyword":  (t_key - t_sem) * 1000,     # ms
    "fusion":   (t_fuse - t_key) * 1000,    # ms
}
```

## Debug Mode

Set env `DEBUG_QUERY` to exact query string to print all intermediate scores:

```bash
DEBUG_QUERY="attention mechanism" uvicorn app:app
# Prints: raw scores, normalized scores, per-doc components
```

## Pipeline

```mermaid
graph TD
    Q[Query] --> PAR[Parallel execution]
    PAR --> SEM[execute_vector_query<br/>top_k=10, threshold=0.15]
    PAR --> BM25[execute_bm25_query<br/>top_k=10, ts_rank english]

    SEM --> SN[Normalize semantic<br/>method: max]
    BM25 --> BN[Normalize BM25<br/>method: HYBRID_BM25_NORM]

    SN --> FUSE{Strategy?}
    BN --> FUSE

    FUSE -->|linear| L[score = a*BM + (1-a)*Sem]
    FUSE -->|combsum| CS[score = Sem + BM]
    FUSE -->|combmnz| CM[score = (Sem + BM) * count]

    L & CS & CM --> SORT[Sort desc by score]
    SORT --> TOP[Top-K results]
    SORT --> LAT[latency_stats + components]
```

## Parameters

| Parameter | Default | Source | Used In |
|-----------|---------|--------|---------|
| `top_k` | 10 | Env `TOP_K` | LIMIT |
| `threshold` | 0.15 | Env `BASE_THRESHOLD` | Semantic filter |
| `fusion_strategy` | "linear" | API call | Fusion method |
| `alpha` | 0.5 | Priority chain | Linear weight |

## Config

| Env Var | Default | Effect |
|---------|---------|--------|
| `BASE_THRESHOLD` | 0.15 | Semantic similarity cutoff |
| `TOP_K` | 10 | Results per query |
| `BM25_WEIGHT` | null | Override alpha |
| `SEMANTIC_WEIGHT` | null | Override alpha (1-x) |
| `HYBRID_BM25_NORM` | max | BM25 normalization method |
| `DEBUG_QUERY` | null | Debug print trigger |

## Full Source: `HybridScorer.py`

```python
import math
import os
from typing import Any, Dict, List, Tuple


class HybridScorer:
    """Normalize scores + fuse using Linear / CombSUM / CombMNZ.

    Usage:
        scorer = HybridScorer(alpha=0.5)
        final, comps = scorer.combine(sem_results, bm25_results, strategy="linear")
        final, comps = scorer.combine(sem_results, bm25_results, strategy="combsum")
    """

    def __init__(self, alpha: float = 0.5):
        if not 0.0 <= alpha <= 1.0:
            raise ValueError("alpha must be between 0 and 1")
        self.alpha = float(alpha)

    def _normalize_values(self, scores: List[float], method: str = "max") -> List[float]:
        if not scores:
            return []
        min_s, max_s = min(scores), max(scores)
        if method == "log":
            denom = math.log1p(max_s) if max_s > 0 else 1.0
            return [(math.log1p(s) / denom) if max_s > 0 else 0.0 for s in scores]
        if method == "minmax":
            denom = max_s - min_s if max_s != min_s else 1.0
            return [(s - min_s) / denom if max_s != min_s else (1.0 if s > 0 else 0.0) for s in scores]
        denom = max_s if max_s > 0 else 1.0
        return [(s / denom) if denom > 0 else 0.0 for s in scores]

    def combine(
        self,
        sem_results: List[Tuple[int, str, float, Any, Any]],
        bm25_results: List[Tuple[int, str, float]],
        top_k: int = 10,
        strategy: str = "linear"
    ):
        bm25_method = os.getenv("HYBRID_BM25_NORM", "max").strip().lower()
        if strategy in ["combsum", "combmnz"]:
            bm25_method = "max"

        bm25_scores_raw = [r[2] for r in bm25_results]
        bm25_scores_norm = self._normalize_values(bm25_scores_raw, bm25_method)
        bm25_map = {r[0]: s for r, s in zip(bm25_results, bm25_scores_norm)}

        sem_scores_raw = [r[2] for r in sem_results]
        sem_scores_norm = self._normalize_values(sem_scores_raw, "max")
        sem_map = {r[0]: s for r, s in zip(sem_results, sem_scores_norm)}

        sem_ranks = {r[0]: i + 1 for i, r in enumerate(sem_results)}
        bm25_ranks = {r[0]: i + 1 for i, r in enumerate(bm25_results)}

        all_ids = set(bm25_map.keys()) | set(sem_map.keys())
        content_lookup = {}
        for r in sem_results:
            content_lookup[r[0]] = (r[1], r[3], r[4])
        for r in bm25_results:
            if r[0] not in content_lookup:
                content_lookup[r[0]] = (r[1], None, None)

        result_map = {}
        for doc_id in all_ids:
            s_norm = sem_map.get(doc_id, 0.0)
            b_norm = bm25_map.get(doc_id, 0.0)
            score = 0.0
            if strategy == "combsum":
                score = s_norm + b_norm
            elif strategy == "combmnz":
                count = (1 if s_norm > 1e-6 else 0) + (1 if b_norm > 1e-6 else 0)
                score = (s_norm + b_norm) * count
            else:
                score = (b_norm * self.alpha) + (s_norm * (1 - self.alpha))
            content, lang, created = content_lookup.get(doc_id, (None, None, None))
            result_map[doc_id] = {
                "content": content, "language": lang, "created_at": created,
                "semantic_score": s_norm, "bm25_score": b_norm, "final_score": score,
            }

        final_list = []
        components = {}
        for doc_id, v in result_map.items():
            final_list.append(
                (doc_id, v["content"], float(v["final_score"]), v["language"], v["created_at"])
            )
            components[doc_id] = {
                "semantic_score": v["semantic_score"],
                "bm25_score": v["bm25_score"],
                "semantic_rank": sem_ranks.get(doc_id),
                "bm25_rank": bm25_ranks.get(doc_id),
                "semantic_weight": 1 - self.alpha if strategy == "linear" else 1.0,
                "bm25_weight": self.alpha if strategy == "linear" else 1.0,
                "strategy": strategy,
            }

        final_sorted = sorted(final_list, key=lambda x: x[2], reverse=True)[:top_k]
        return final_sorted, components
```
