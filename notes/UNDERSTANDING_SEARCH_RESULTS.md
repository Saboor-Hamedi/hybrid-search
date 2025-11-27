# Understanding Your Search Results

## What You're Seeing

### Semantic Search (Standalone)
- **Returns:** 964 results
- **Why:** Uses vector similarity with threshold 0.25
- **Behavior:** Finds semantically similar documents based on meaning

### Hybrid Search
- **Semantic Count:** 964 (same as standalone semantic)
- **BM25 Count:** Should now show up!
- **Final Results:** 200 (after combining and ranking)
- **Why fewer results:** Hybrid combines both methods and returns top 100 (or your configured TOP_K)

## How Hybrid Search Works

```
Step 1: Semantic Search
├─ Finds 964 documents with similarity >= 0.25
└─ Each gets a semantic score (0.0 - 1.0)

Step 2: BM25 Keyword Search  
├─ Finds documents matching keywords
├─ Normalizes BM25 scores to (0.0 - 1.0)
└─ Each gets a BM25 score

Step 3: Combine with Weights
├─ ALPHA = 0.5 (50% weight for each)
├─ Semantic weight: 0.5 (1 - ALPHA)
├─ BM25 weight: 0.5 (ALPHA)
└─ Final Score = (semantic_score × 0.5) + (bm25_score × 0.5)

Step 4: Sort & Return Top Results
└─ Returns top 100 results (TOP_K)
```

## Why You See 200 Results Sometimes

Looking at your code, the issue might be:
1. **Pagination:** The API might be returning 2 pages × 100 results
2. **TOP_K × 2:** Some queries use `top_k * 2` for initial retrieval

## What I Fixed

### Before:
```python
# hybrid_search.py
return final, {}  # Empty stats! ❌
```

### After:
```python
# hybrid_search.py
stats = {
    "sem_results": sem_results,    # Now includes semantic results
    "bm25_results": bm25_results,  # Now includes BM25 results
}
return final, stats  # ✅
```

## Now Your API Response Will Show:

```json
{
  "results": [...],
  "stats": {
    "search_type": "hybrid",
    "query_time_ms": 245.67,
    "total_candidates": 200,
    "returned": 50,
    "semantic_count": 964,  // ✅ Now shows!
    "bm25_count": 342       // ✅ Now shows!
  },
  "pagination": {...}
}
```

## Expected Behavior

| Search Mode | Semantic Count | BM25 Count | Final Results |
|-------------|----------------|------------|---------------|
| **Semantic** | 964 | 0 | 964 (or TOP_K) |
| **Keyword** | 0 | 342 | 342 (or TOP_K) |
| **Hybrid** | 964 | 342 | 100 (TOP_K) |

## Tuning the Hybrid Balance

You can adjust the weights in `hybrid_search.py`:

```python
# Current (Equal weight)
ALPHA = 0.5  # 50% semantic, 50% BM25

# More semantic focus
ALPHA = 0.3  # 70% semantic, 30% BM25

# More keyword focus  
ALPHA = 0.7  # 30% semantic, 70% BM25
```

## Testing

After the servers reload, try a search and check:
1. ✅ Semantic count shows in hybrid mode
2. ✅ BM25 count shows in hybrid mode
3. ✅ Both counts are accurate
4. ✅ Final results are properly ranked

The stats should now display correctly! 🎉
