# Hybrid Search Feature Documentation

## Overview

Hybrid Search combines the best of both worlds: **semantic (vector-based) search** and **keyword (BM25) search**. By merging these complementary approaches, hybrid search provides superior recall and relevance compared to either method alone.

## How It Works

### The Hybrid Formula

```python
final_score = (semantic_score × (1 - α)) + (bm25_score × α)
```

Where:
- **α (alpha)** = Weight for BM25 (default: 0.5)
- **(1 - α)** = Weight for semantic (default: 0.5)
- **semantic_score** = Cosine similarity (0.0-1.0)
- **bm25_score** = Normalized BM25 score (0.0-1.0)

### Example

**Query:** "machine learning tutorial"

**Step 1: Semantic Search**
```
Doc 1: "ML guide for beginners" → 0.85 (high semantic similarity)
Doc 2: "Introduction to AI" → 0.72
Doc 3: "Python programming" → 0.45
```

**Step 2: BM25 Search**
```
Doc 4: "Machine learning tutorial PDF" → 15.3 (raw BM25)
Doc 1: "ML guide for beginners" → 8.2
Doc 5: "Tutorial on neural networks" → 6.7
```

**Step 3: Normalize BM25 Scores**
```
Min = 6.7, Max = 15.3, Range = 8.6

Doc 4: (15.3 - 6.7) / 8.6 = 1.00
Doc 1: (8.2 - 6.7) / 8.6 = 0.17
Doc 5: (6.7 - 6.7) / 8.6 = 0.00
```

**Step 4: Combine with α=0.5**
```
Doc 1: (0.85 × 0.5) + (0.17 × 0.5) = 0.51
Doc 4: (0.00 × 0.5) + (1.00 × 0.5) = 0.50  (no semantic match)
Doc 2: (0.72 × 0.5) + (0.00 × 0.5) = 0.36  (no BM25 match)
```

**Final Ranking:**
1. Doc 1: 0.51 (matched both!)
2. Doc 4: 0.50 (keyword match only)
3. Doc 2: 0.36 (semantic match only)

## Implementation

### File: `src/core/db/operations/search_flask/hybrid_search.py`

```python
def search_hybrid(query, conn, cursor, model, top_k=100, threshold=0.25):
    """
    Execute hybrid search combining semantic and BM25
    
    Returns:
        Tuple: (results, stats)
    """
    # 1. Get semantic results
    sem_results = execute_vector_query(query, conn, cursor, model, top_k, threshold)
    
    # 2. Get BM25 results
    bm25_utils.update_bm25_index(cursor, normalize_content)
    scores = bm25_utils.bm25_index.get_scores(normalize_content(query).split())
    bm25_results = [(doc_id, content, scores[i]) 
                    for i, (doc_id, content) in enumerate(bm25_utils.bm25_corpus)
                    if scores[i] > 0]
    
    # 3. Normalize BM25 scores (Min-Max)
    if bm25_results:
        scores = [s for _, _, s in bm25_results]
        min_s, max_s = min(scores), max(scores)
        denom = max_s - min_s if max_s != min_s else 1.0
        
        bm25_norm = []
        for doc_id, content, raw_score in bm25_results:
            norm_score = (raw_score - min_s) / denom if max_s != min_s else 1.0
            bm25_norm.append((doc_id, content, norm_score))
    else:
        bm25_norm = []
    
    # 4. Combine with weighted scoring
    ALPHA = 0.5  # BM25 weight
    result_map = {}
    
    # Add semantic scores
    for r in sem_results:
        doc_id = r[0]
        weighted_score = r[2] * (1 - ALPHA)
        result_map[doc_id] = {
            "data": r,
            "score": weighted_score
        }
    
    # Add BM25 scores
    for doc_id, content, score in bm25_norm:
        weighted_score = score * ALPHA
        if doc_id in result_map:
            result_map[doc_id]["score"] += weighted_score
        else:
            result_map[doc_id] = {
                "data": (doc_id, content, 0.0, None, None),
                "score": weighted_score
            }
    
    # 5. Sort and return
    final_list = []
    for val in result_map.values():
        r = val["data"]
        final_score = val["score"]
        new_tuple = (r[0], r[1], final_score, r[3], r[4])
        final_list.append(new_tuple)
    
    final = sorted(final_list, key=lambda x: x[2], reverse=True)[:top_k]
    
    return final, {
        "sem_results": sem_results,
        "bm25_results": bm25_results
    }
```

## Configuration

### Alpha (α) - Search Weight Balance

```python
# In hybrid_search.py
ALPHA = 0.5  # Default: Equal weight

# More semantic focus (better for conceptual queries)
ALPHA = 0.3  # 70% semantic, 30% BM25

# More keyword focus (better for exact terms)
ALPHA = 0.7  # 30% semantic, 70% BM25

# Pure semantic (same as semantic mode)
ALPHA = 0.0  # 100% semantic, 0% BM25

# Pure keyword (same as keyword mode)
ALPHA = 1.0  # 0% semantic, 100% BM25
```

### Threshold

```python
THRESHOLD = 0.25  # Default

# Lower for more recall
THRESHOLD = 0.20

# Higher for more precision
THRESHOLD = 0.35
```

## When to Use Hybrid Search

### ✅ Use Hybrid When:

1. **Maximum Coverage Needed**
   - Want to find all relevant documents
   - Can't afford to miss results
   - Recall is more important than precision

2. **Query Type Unknown**
   - User queries vary widely
   - Mix of natural language and keywords
   - General-purpose search

3. **Best Quality Results**
   - Willing to trade speed for quality
   - Want documents that match both semantically AND by keywords
   - Need robust ranking

4. **Diverse Document Collection**
   - Documents vary in style and length
   - Mix of technical and natural language
   - Multiple domains/topics

### ❌ Don't Use Hybrid When:

1. **Speed is Critical**
   - Hybrid is 3-4x slower than single methods
   - Real-time/interactive search needed
   - High query volume

2. **Clear Query Type**
   - All queries are natural language → Use semantic
   - All queries are keywords → Use BM25
   - Specialized use case

3. **Limited Resources**
   - No ML model available
   - Database can't handle vector operations
   - Memory constraints

## Performance Characteristics

| Metric | Semantic | BM25 | Hybrid |
|--------|----------|------|--------|
| **Speed** | 440ms | 400ms | 1550ms |
| **Recall** | Medium | Medium | High |
| **Precision** | High | Medium | High |
| **Latency** | Low | Low | High |
| **Resource Use** | Medium | Low | High |

## Optimization Strategies

### 1. Parallel Execution

```python
import concurrent.futures

def search_hybrid_parallel(query, conn, cursor, model, top_k, threshold):
    """Execute semantic and BM25 searches in parallel"""
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        # Submit both searches
        sem_future = executor.submit(
            execute_vector_query, query, conn, cursor, model, top_k, threshold
        )
        bm25_future = executor.submit(
            execute_bm25_search, query, cursor, top_k
        )
        
        # Wait for results
        sem_results = sem_future.result()
        bm25_results = bm25_future.result()
    
    # Combine as before
    return combine_results(sem_results, bm25_results, ALPHA)
```

### 2. Caching

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_hybrid_search(query, mode, top_k):
    """Cache frequent queries"""
    return search_hybrid(query, conn, cursor, model, top_k)
```

### 3. Early Termination

```python
def search_hybrid_fast(query, conn, cursor, model, top_k=100):
    """Stop early if one method has enough high-quality results"""
    
    sem_results = execute_vector_query(query, conn, cursor, model, top_k, 0.25)
    
    # If we have many high-quality semantic results, skip BM25
    high_quality = [r for r in sem_results if r[2] >= 0.8]
    if len(high_quality) >= top_k:
        return high_quality[:top_k], {"sem_results": sem_results, "bm25_results": []}
    
    # Otherwise, do full hybrid search
    return search_hybrid(query, conn, cursor, model, top_k)
```

### 4. Adaptive Weighting

```python
def adaptive_alpha(query, sem_results, bm25_results):
    """Adjust alpha based on query characteristics"""
    
    # If query has many keywords, favor BM25
    word_count = len(query.split())
    if word_count >= 5:
        return 0.6  # More BM25 weight
    
    # If semantic results are very strong, favor semantic
    if sem_results and sem_results[0][2] >= 0.9:
        return 0.3  # More semantic weight
    
    # Default
    return 0.5
```

## Advanced Techniques

### 1. Reciprocal Rank Fusion (RRF)

Alternative to weighted scoring:

```python
def reciprocal_rank_fusion(sem_results, bm25_results, k=60):
    """
    RRF: score(d) = Σ 1/(k + rank(d))
    """
    scores = {}
    
    # Add semantic ranks
    for rank, (doc_id, content, score, lang, date) in enumerate(sem_results, 1):
        scores[doc_id] = scores.get(doc_id, 0) + 1/(k + rank)
    
    # Add BM25 ranks
    for rank, (doc_id, content, score) in enumerate(bm25_results, 1):
        scores[doc_id] = scores.get(doc_id, 0) + 1/(k + rank)
    
    # Sort by RRF score
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return ranked
```

### 2. Learning to Rank (LTR)

Train a model to learn optimal weights:

```python
from sklearn.ensemble import RandomForestRegressor

def train_ltr_model(training_data):
    """
    Train model to predict relevance from features
    
    Features:
    - Semantic score
    - BM25 score
    - Query length
    - Document length
    - Overlap score
    """
    X = []  # Features
    y = []  # Relevance labels
    
    for query, doc, relevance in training_data:
        features = [
            semantic_score(query, doc),
            bm25_score(query, doc),
            len(query.split()),
            len(doc.split()),
            overlap_score(query, doc)
        ]
        X.append(features)
        y.append(relevance)
    
    model = RandomForestRegressor()
    model.fit(X, y)
    return model

def search_with_ltr(query, sem_results, bm25_results, ltr_model):
    """Use LTR model for final ranking"""
    scored_docs = []
    
    for doc in all_documents:
        features = extract_features(query, doc, sem_results, bm25_results)
        predicted_relevance = ltr_model.predict([features])[0]
        scored_docs.append((doc, predicted_relevance))
    
    return sorted(scored_docs, key=lambda x: x[1], reverse=True)
```

### 3. Query Classification

Route queries to best search method:

```python
def classify_query(query):
    """Determine best search mode for query"""
    
    # Short queries with technical terms → BM25
    if len(query.split()) <= 3 and has_technical_terms(query):
        return "keyword"
    
    # Natural language questions → Semantic
    if query.startswith(("what", "how", "why", "when", "where")):
        return "semantic"
    
    # Default → Hybrid
    return "hybrid"

def smart_search(query, conn, cursor, model):
    """Auto-select best search mode"""
    mode = classify_query(query)
    
    if mode == "semantic":
        return search_semantic(query, conn, cursor, model)
    elif mode == "keyword":
        return search_keyword(query, cursor)
    else:
        return search_hybrid(query, conn, cursor, model)
```

## Evaluation Metrics

### Measuring Hybrid Search Quality

```python
def evaluate_hybrid_search(test_queries, ground_truth):
    """
    Evaluate search quality
    
    Metrics:
    - Precision@K: Relevant docs in top K
    - Recall@K: % of relevant docs found in top K
    - MAP: Mean Average Precision
    - NDCG: Normalized Discounted Cumulative Gain
    """
    
    precisions = []
    recalls = []
    
    for query, relevant_docs in test_queries:
        results = search_hybrid(query, conn, cursor, model, top_k=10)
        result_ids = [r[0] for r in results]
        
        # Precision@10
        relevant_in_results = len(set(result_ids) & set(relevant_docs))
        precision = relevant_in_results / len(result_ids)
        precisions.append(precision)
        
        # Recall@10
        recall = relevant_in_results / len(relevant_docs)
        recalls.append(recall)
    
    return {
        "avg_precision": sum(precisions) / len(precisions),
        "avg_recall": sum(recalls) / len(recalls)
    }
```

## Troubleshooting

### Issue: Hybrid Slower Than Expected
**Solutions:**
1. Use parallel execution
2. Reduce TOP_K
3. Implement caching
4. Use early termination

### Issue: Results Not Better Than Single Methods
**Solutions:**
1. Tune alpha parameter
2. Check score normalization
3. Try RRF instead of weighted scoring
4. Implement LTR

### Issue: Semantic or BM25 Results Missing
**Solutions:**
1. Check threshold settings
2. Verify both indexes are built
3. Review query preprocessing
4. Check stats dictionary

## Best Practices

1. **Start with α=0.5** and tune based on your data
2. **Monitor both component scores** to understand behavior
3. **Use parallel execution** for production
4. **Cache frequent queries** to improve speed
5. **Normalize scores** before combining
6. **Test with real user queries** to validate
7. **Consider query classification** for optimal routing
8. **Implement A/B testing** to measure impact

## Related Documentation

- [Semantic Search](./semantic_search.md)
- [BM25 Algorithm](./bm25_algorithm.md)
- [Performance Optimization](./performance_optimization.md)
- [API Reference](./api_reference.md)
