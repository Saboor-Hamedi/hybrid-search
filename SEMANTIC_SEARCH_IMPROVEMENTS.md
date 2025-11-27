# Semantic Search Issues & Improvements Guide

## Problem Analysis

### 1. **The 500 Internal Server Error**

The error was caused by **SQL parameter mismatch**:

**Broken Code:**
```python
sql = """
    ORDER BY e.embedding <=> %s::vector ASC  # 2nd placeholder
    LIMIT %s                                   # 3rd placeholder
"""
cursor.execute(sql, (vec_str, vec_str, top_k * 2))  # Only 3 params, but SQL had issues
```

**Issues:**
- Used `str(vec_list)` which creates Python format `[1.0, 2.0, 3.0]` instead of PostgreSQL format
- Didn't handle NaN/Inf values from the model
- SQL had inconsistent ordering (ASC vs DESC)
- Missing WHERE clause for threshold filtering

**Fixed Code:**
```python
# Clean NaN/Inf values
clean_vec = []
for val in vec_list:
    if math.isnan(val) or math.isinf(val):
        clean_vec.append(0.0)
    else:
        clean_vec.append(float(val))

# Proper PostgreSQL array format
vec_str = f"[{','.join(map(str, clean_vec))}]"

# Correct SQL with 4 parameters
sql = """
    WHERE (1 - (e.embedding <=> %s::vector)) >= %s
    ORDER BY similarity DESC
    LIMIT %s
"""
cursor.execute(sql, (vec_str, vec_str, threshold, top_k * 2))
```

---

## 2. **Improving Semantic Search Accuracy**

### Current Model: `all-MiniLM-L6-v2`
- **Dimensions:** 384
- **Speed:** Very fast
- **Accuracy:** Good for general use
- **Limitation:** Not specialized for your domain

### Recommended Improvements:

#### **Option 1: Upgrade to Better Models** (Easiest)

Replace in `ai_model.py`:

```python
# Current (Fast but less accurate)
model = SentenceTransformer("all-MiniLM-L6-v2")  # 384 dims

# Better Options:
model = SentenceTransformer("all-mpnet-base-v2")  # 768 dims - BEST BALANCE
# OR
model = SentenceTransformer("multi-qa-mpnet-base-dot-v1")  # 768 dims - Optimized for Q&A
# OR
model = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")  # For multilingual
```

**Performance Comparison:**
| Model | Dimensions | Speed | Accuracy | Use Case |
|-------|-----------|-------|----------|----------|
| all-MiniLM-L6-v2 | 384 | ⚡⚡⚡ | ⭐⭐⭐ | General, Fast |
| all-mpnet-base-v2 | 768 | ⚡⚡ | ⭐⭐⭐⭐⭐ | Best overall |
| multi-qa-mpnet | 768 | ⚡⚡ | ⭐⭐⭐⭐⭐ | Q&A systems |
| paraphrase-multilingual | 768 | ⚡⚡ | ⭐⭐⭐⭐ | Multiple languages |

#### **Option 2: Fine-tune Your Model** (Advanced)

Train the model on your specific domain data:

```python
from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader

# 1. Prepare training data (query, positive_doc, negative_doc)
train_examples = [
    InputExample(texts=['query1', 'relevant_doc1', 'irrelevant_doc1']),
    InputExample(texts=['query2', 'relevant_doc2', 'irrelevant_doc2']),
]

# 2. Load base model
model = SentenceTransformer('all-mpnet-base-v2')

# 3. Define loss function
train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=16)
train_loss = losses.TripletLoss(model=model)

# 4. Train
model.fit(
    train_objectives=[(train_dataloader, train_loss)],
    epochs=1,
    warmup_steps=100
)

# 5. Save
model.save('models/custom-search-model')
```

#### **Option 3: Adjust Search Parameters**

In `semantic_search.py`:

```python
# Current
THRESHOLD = 0.4  # Too high? Missing relevant results
TOP_K = 50       # Too low? Not enough candidates

# Recommended
THRESHOLD = 0.25  # Lower threshold = more results
TOP_K = 100       # More candidates for better ranking
```

#### **Option 4: Implement Query Expansion**

Expand user queries to capture more semantic variations:

```python
def expand_query(query: str) -> str:
    """Add synonyms and related terms to improve recall"""
    # Simple expansion
    expansions = {
        'python': 'python programming language code',
        'error': 'error exception bug issue problem',
        'database': 'database db postgres postgresql sql',
    }
    
    words = query.lower().split()
    expanded = query
    
    for word in words:
        if word in expansions:
            expanded += ' ' + expansions[word]
    
    return expanded

# Usage in search
expanded_query = expand_query(request.query)
results = search_semantic(expanded_query, conn, cursor, model)
```

#### **Option 5: Implement Re-ranking** (Best for Accuracy)

Use a cross-encoder to re-rank top results:

```python
from sentence_transformers import CrossEncoder

# Load re-ranker (do this once at startup)
reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

def rerank_results(query: str, results: list, top_k: int = 10):
    """Re-rank results using cross-encoder for better accuracy"""
    if not results:
        return results
    
    # Prepare pairs for re-ranking
    pairs = [[query, result[1]] for result in results]  # result[1] is content
    
    # Get re-ranking scores
    scores = reranker.predict(pairs)
    
    # Combine with original results
    reranked = []
    for idx, score in enumerate(scores):
        result = list(results[idx])
        result[2] = float(score)  # Replace similarity with rerank score
        reranked.append(tuple(result))
    
    # Sort by new scores
    reranked.sort(key=lambda x: x[2], reverse=True)
    
    return reranked[:top_k]

# Usage in semantic_search.py
results = execute_vector_query(query, conn, cursor, model, top_k=100, threshold=0.2)
results = rerank_results(query, results, top_k=50)
```

---

## 3. **Database Optimization**

### Add HNSW Index for Faster Vector Search

```sql
-- Current (slower for large datasets)
CREATE INDEX ON document_embedding USING ivfflat (embedding vector_cosine_ops);

-- Better (faster, more accurate)
CREATE INDEX ON document_embedding USING hnsw (embedding vector_cosine_ops);
```

### Analyze Your Data Distribution

```sql
-- Check similarity score distribution
SELECT 
    CASE 
        WHEN similarity >= 0.8 THEN '0.8-1.0 (Excellent)'
        WHEN similarity >= 0.6 THEN '0.6-0.8 (Good)'
        WHEN similarity >= 0.4 THEN '0.4-0.6 (Fair)'
        ELSE '0.0-0.4 (Poor)'
    END as score_range,
    COUNT(*) as count
FROM (
    SELECT (1 - (e1.embedding <=> e2.embedding)) as similarity
    FROM document_embedding e1
    CROSS JOIN document_embedding e2
    WHERE e1.doc_id != e2.doc_id
    LIMIT 10000
) scores
GROUP BY score_range
ORDER BY score_range DESC;
```

---

## 4. **Monitoring & Debugging**

### Add Detailed Logging

```python
def execute_vector_query(query, conn, cursor, model, top_k, threshold):
    import time
    
    start = time.time()
    
    # Encode
    encode_start = time.time()
    query_vec = model.encode(query)
    encode_time = time.time() - encode_start
    
    # Query DB
    db_start = time.time()
    cursor.execute(sql, params)
    db_time = time.time() - db_start
    
    # Log performance
    print(f"""
    {cs.CYAN}=== Semantic Search Debug ==={cs.RESET}
    Query: {query}
    Encode Time: {encode_time*1000:.2f}ms
    DB Query Time: {db_time*1000:.2f}ms
    Total Time: {(time.time()-start)*1000:.2f}ms
    Results Found: {len(results)}
    Top Score: {results[0][2] if results else 0:.4f}
    Avg Score: {sum(r[2] for r in results)/len(results) if results else 0:.4f}
    """)
    
    return results
```

---

## 5. **Recommended Implementation Plan**

### Phase 1: Quick Wins (Do Now)
1. ✅ Fix the 500 error (already done)
2. Lower threshold from 0.4 to 0.25
3. Increase TOP_K from 50 to 100
4. Add debug logging

### Phase 2: Model Upgrade (This Week)
1. Switch to `all-mpnet-base-v2`
2. Re-generate all embeddings
3. Test and compare results

### Phase 3: Advanced (Next Week)
1. Implement re-ranking with CrossEncoder
2. Add query expansion
3. Optimize database indexes

### Phase 4: Production (Optional)
1. Fine-tune model on your data
2. Implement A/B testing
3. Monitor and iterate

---

## 6. **Testing Your Changes**

```python
# test_semantic_search.py
test_queries = [
    "python error handling",
    "database connection",
    "machine learning tutorial",
]

for query in test_queries:
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}")
    
    results = search_semantic(query, conn, cursor, model)
    
    print(f"Results: {len(results)}")
    for i, (doc_id, content, score, lang, date) in enumerate(results[:5], 1):
        print(f"{i}. [Score: {score:.4f}] {content[:100]}...")
```

---

## Summary

**Immediate Fix:** ✅ The 500 error is now fixed by properly handling NaN/Inf and correct SQL parameters.

**To Improve Accuracy:**
1. **Easy:** Change model to `all-mpnet-base-v2` (5 min)
2. **Medium:** Lower threshold to 0.25 (1 min)
3. **Advanced:** Add re-ranking with CrossEncoder (30 min)
4. **Expert:** Fine-tune model on your data (hours/days)

Start with #1 and #2, then measure improvement before moving to advanced techniques.
