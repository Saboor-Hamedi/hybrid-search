# Semantic Search (pgvector Cosine)

**File**: `src/core/db/operations/search_flask/semantic_search.py` (84 lines)
**Engine**: `src/core/db/operations/search_queries.py` → `execute_vector_query()`

## How It Works

1. **Encode**: Query → SentenceTransformer → 384-dim vector
2. **Search**: pgvector HNSW index → cosine distance (`<=>`)
3. **Filter**: `1 - distance >= threshold`
4. **Fallback**: If 0 results, reduce threshold by 0.1 (min 0.1) and retry
5. **Boost**: Add term overlap + exact phrase + position + language boosts
6. **Filter**: Remove results shorter than 20 chars
7. **Sort**: By boosted score descending

## Config

| Parameter | Default | Env Var | Description |
|-----------|---------|---------|-------------|
| `BASE_THRESHOLD` | 0.35 | `BASE_THRESHOLD` | Minimum cosine similarity |
| `TOP_K` | 10 | `TOP_K` | Max results (internally `* 2`) |
| Min content length | 20 | hardcoded | Shorter results discarded |

## Dynamic Threshold

```python
def _dynamic_threshold(q):
    tokens = [t for t in q.strip().split() if t]
    n = len(tokens)
    if n <= 1:    return 0.20
    if n <= 3:    return 0.28
    return BASE_THRESHOLD  # 0.35
```

## SQL

```sql
SELECT d.id, d.content,
       (1 - (e.embedding <=> %s::vector)) AS similarity,
       d.language, d.created_at
FROM document d
INNER JOIN document_embedding e ON d.id = e.doc_id
WHERE (1 - (e.embedding <=> %s::vector)) >= %s
ORDER BY similarity DESC
LIMIT %s
```

`LIMIT` is `top_k * 2` to allow room for post-filtering/sorting.

## Boosts Applied (additive)

| Boost | Value | Code | Condition |
|-------|-------|------|-----------|
| Token overlap | +0.05 | `any(t in text.lower() for t in q_tokens)` | Any query word found in doc |
| Exact phrase | +0.06 | `phrase in text.lower()` | Full query appears verbatim |
| Position | 0.00–0.05 | `0.05 * (1 - first_pos / len(text))` | Earlier match = higher |
| Language | +0.02 | `all(ord(c) < 128 for c in query) and lang == 'en'` | ASCII query + English doc |

## Boosting Algorithm

```python
# Token extraction uses re.findall(r"\w+", query.lower())
# Position: min position of all matching tokens
# Ratio: max(0.0, 1.0 - (first_pos / len(text)))
# pos_boost = 0.05 * ratio
```

## Pipeline

```mermaid
graph LR
    Q[Query] --> ENC[SentenceTransformer encode]
    ENC --> VEC[384-dim vector]
    VEC --> SQL[pgvector <=> cosine<br/>LIMIT top_k*2]
    SQL --> THR{score >= threshold?}
    THR -->|No| RETRY[threshold - 0.1<br/>min 0.1]
    RETRY --> SQL
    THR -->|Yes| COLLECT[Collect results]
    COLLECT --> BOOST[Apply boosts]
    BOOST --> FILTER[Filter < 20 chars]
    FILTER --> SORT[Sort desc]
    SORT --> RETURN[return results, {}]
```

## Return Format

```python
# (doc_id, content, boosted_score, language, created_at)
return results, {}  # Semantic returns empty stats dict
```

## Full Source: `semantic_search.py`

```python
import os
import re

from core.db.operations.search_queries import execute_vector_query

BASE_THRESHOLD = float(os.environ.get("BASE_THRESHOLD", "0.35"))
TOP_K = int(os.environ.get("TOP_K", "10"))


def _dynamic_threshold(q: str) -> float:
    tokens = [t for t in q.strip().split() if t]
    n = len(tokens)
    if n <= 1:
        return 0.20
    if n <= 3:
        return 0.28
    return BASE_THRESHOLD


def search_semantic(query: str, conn, cursor, model, top_k=TOP_K, threshold: float = None):
    if not query.strip():
        return [], {}

    thr = threshold if threshold is not None else _dynamic_threshold(query)
    results = execute_vector_query(query, conn, cursor, model, top_k, thr)
    if not results:
        thr_fallback = max(thr - 0.1, 0.1)
        results = execute_vector_query(query, conn, cursor, model, top_k, thr_fallback)

    filtered = []
    q_tokens = re.findall(r"\w+", query.lower())
    prefer_en = all(ord(c) < 128 for c in query)
    phrase = " ".join(q_tokens).strip()

    for doc_id, content, score, language, created_at in results:
        text = (content or "").strip()
        if len(text) < 20:
            continue
        boost = 0.0
        if q_tokens and any(t in text.lower() for t in q_tokens):
            boost += 0.05
        if phrase and phrase in text.lower():
            boost += 0.06
        pos_boost = 0.0
        try:
            positions = []
            for t in q_tokens:
                p = text.lower().find(t)
                if p != -1:
                    positions.append(p)
            if positions:
                first_pos = min(positions)
                ratio = max(0.0, 1.0 - (first_pos / max(1, len(text))))
                pos_boost = 0.05 * ratio
        except Exception:
            pos_boost = 0.0
        boost += pos_boost
        if prefer_en and (language or "").lower() == "en":
            boost += 0.02
        filtered.append((doc_id, content, float(score) + boost, language, created_at))

    filtered.sort(key=lambda x: x[2], reverse=True)
    return filtered, {}
```

## Called By

- `app.py` — universal gathering (always runs top_k=50)
- `hybrid_search.py` — as one of two retrieval paths
- `rrf_search.py` — as one of two retrieval paths
- `ltr_search.py` — as part of stage 1 retrieval
- `main.py` — CLI standalone semantic search
- `auto_eval.py` — evaluation engine
- `thesis_comparator.py` — side-by-side comparison
