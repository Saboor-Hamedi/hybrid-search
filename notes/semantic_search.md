# Semantic Search Feature Documentation

## Overview

Semantic search uses machine learning models to understand the **meaning** of queries and documents, rather than just matching keywords. This allows finding relevant documents even when they don't contain the exact search terms.

## How It Works

### 1. **Document Embedding**
When documents are ingested:
```python
# Each document is converted to a vector (embedding)
document = "Machine learning is a subset of artificial intelligence"
embedding = model.encode(document)  # Returns 384-dimensional vector
# embedding = [0.123, -0.456, 0.789, ..., 0.234]
```

### 2. **Query Embedding**
When a user searches:
```python
query = "AI and ML concepts"
query_embedding = model.encode(query)  # Same 384-dimensional space
```

### 3. **Similarity Calculation**
Find documents closest to the query in vector space:
```sql
SELECT 
    d.id, 
    d.content, 
    (1 - (e.embedding <=> %s::vector)) AS similarity
FROM document d
JOIN document_embedding e ON d.id = e.doc_id
WHERE (1 - (e.embedding <=> %s::vector)) >= 0.25
ORDER BY similarity DESC
LIMIT 100
```

The `<=>` operator is cosine distance:
- **1.0** = Identical meaning
- **0.5** = Somewhat related
- **0.0** = Completely unrelated

## Implementation

### File: `src/core/db/operations/search_flask/semantic_search.py`

```python
def search_semantic(query: str, conn, cursor, model, top_k=100, threshold=0.25):
    """
    Execute semantic search
    
    Args:
        query: User's search query
        conn: Database connection
        cursor: Database cursor
        model: Sentence transformer model
        top_k: Maximum results to return
        threshold: Minimum similarity score (0.0-1.0)
    
    Returns:
        Tuple: (results, stats)
    """
    # Encode query to vector
    results = execute_vector_query(query, conn, cursor, model, top_k, threshold)
    
    # Display and return
    display_in_table(results, query=query, mode="semantic")
    return results, {}
```

### File: `src/core/db/operations/search_queries.py`

```python
def execute_vector_query(query, conn, cursor, model, top_k, threshold):
    """
    Core vector search implementation
    """
    # 1. Encode query
    query_vec = model.encode(query)
    
    # 2. Clean NaN/Inf values
    clean_vec = [0.0 if math.isnan(v) or math.isinf(v) else float(v) 
                 for v in query_vec.tolist()]
    
    # 3. Format for PostgreSQL
    vec_str = f"[{','.join(map(str, clean_vec))}]"
    
    # 4. Execute similarity search
    cursor.execute(sql, (vec_str, vec_str, threshold, top_k * 2))
    
    # 5. Process and return results
    return results
```

## Configuration

### Threshold
Controls minimum similarity score:
```python
THRESHOLD = 0.25  # Default

# Lower = More results, less precise
THRESHOLD = 0.20  # More recall

# Higher = Fewer results, more precise
THRESHOLD = 0.40  # More precision
```

### Top K
Maximum candidates to retrieve:
```python
TOP_K = 100  # Default

# Increase for more comprehensive results
TOP_K = 200

# Decrease for faster queries
TOP_K = 50
```

## Model Selection

### Current Model: `all-MiniLM-L6-v2`
- **Dimensions:** 384
- **Speed:** Very fast (⚡⚡⚡)
- **Accuracy:** Good (⭐⭐⭐)
- **Size:** 80 MB
- **Best for:** General purpose, speed-critical applications

### Upgrade Options

#### 1. all-mpnet-base-v2 (Recommended)
```python
model = SentenceTransformer("all-mpnet-base-v2")
```
- **Dimensions:** 768
- **Speed:** Fast (⚡⚡)
- **Accuracy:** Excellent (⭐⭐⭐⭐⭐)
- **Size:** 420 MB
- **Best for:** Best overall quality

#### 2. multi-qa-mpnet-base-dot-v1
```python
model = SentenceTransformer("multi-qa-mpnet-base-dot-v1")
```
- **Dimensions:** 768
- **Speed:** Fast (⚡⚡)
- **Accuracy:** Excellent for Q&A (⭐⭐⭐⭐⭐)
- **Best for:** Question-answering systems

#### 3. paraphrase-multilingual-mpnet-base-v2
```python
model = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")
```
- **Dimensions:** 768
- **Languages:** 50+
- **Best for:** Multilingual applications

## Performance Optimization

### 1. Database Indexing

#### Current (IVFFlat)
```sql
CREATE INDEX ON document_embedding 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

#### Better (HNSW)
```sql
CREATE INDEX ON document_embedding 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

HNSW is faster and more accurate for most use cases.

### 2. Batch Processing
For multiple queries:
```python
queries = ["query1", "query2", "query3"]
embeddings = model.encode(queries)  # Batch encode
```

### 3. Caching
Cache frequent queries:
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_search(query):
    return search_semantic(query, conn, cursor, model)
```

## Advanced Techniques

### 1. Query Expansion
Improve recall by expanding queries:
```python
def expand_query(query):
    """Add synonyms and related terms"""
    expansions = {
        'ML': 'machine learning artificial intelligence',
        'DB': 'database sql postgresql',
    }
    
    for term, expansion in expansions.items():
        if term.lower() in query.lower():
            query += ' ' + expansion
    
    return query
```

### 2. Re-ranking
Use cross-encoder for better accuracy:
```python
from sentence_transformers import CrossEncoder

reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

def rerank_results(query, results, top_k=10):
    pairs = [[query, r[1]] for r in results]
    scores = reranker.predict(pairs)
    
    # Update scores and re-sort
    reranked = [(r[0], r[1], score, r[3], r[4]) 
                for r, score in zip(results, scores)]
    reranked.sort(key=lambda x: x[2], reverse=True)
    
    return reranked[:top_k]
```

### 3. Fine-tuning
Train model on your specific domain:
```python
from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader

# Prepare training data
train_examples = [
    InputExample(texts=['query', 'positive_doc', 'negative_doc']),
    # ... more examples
]

# Load base model
model = SentenceTransformer('all-mpnet-base-v2')

# Train
train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=16)
train_loss = losses.TripletLoss(model=model)

model.fit(
    train_objectives=[(train_dataloader, train_loss)],
    epochs=3,
    warmup_steps=100
)

# Save custom model
model.save('models/custom-domain-model')
```

## Troubleshooting

### Issue: No Results Found
**Solutions:**
1. Lower threshold: `THRESHOLD = 0.20`
2. Check if documents are embedded
3. Verify model is loaded correctly

### Issue: Irrelevant Results
**Solutions:**
1. Raise threshold: `THRESHOLD = 0.35`
2. Upgrade to better model
3. Implement re-ranking
4. Fine-tune on your data

### Issue: Slow Performance
**Solutions:**
1. Add HNSW index
2. Reduce TOP_K
3. Use smaller model
4. Implement caching

### Issue: 500 Error
**Solutions:**
1. Check for NaN/Inf in embeddings
2. Verify vector dimensions match
3. Check database connection
4. Review error logs

## Testing

### Unit Test
```python
def test_semantic_search():
    query = "machine learning"
    results, _ = search_semantic(query, conn, cursor, model)
    
    assert len(results) > 0
    assert all(r[2] >= 0.25 for r in results)  # Check threshold
    assert results[0][2] >= results[-1][2]  # Check sorting
```

### Performance Test
```python
import time

def benchmark_semantic_search():
    queries = ["AI", "database", "python", "search", "algorithm"]
    
    times = []
    for query in queries:
        start = time.time()
        results, _ = search_semantic(query, conn, cursor, model)
        elapsed = time.time() - start
        times.append(elapsed)
    
    avg_time = sum(times) / len(times)
    print(f"Average query time: {avg_time*1000:.2f}ms")
```

## Best Practices

1. **Always normalize text** before embedding
2. **Handle edge cases** (empty queries, special characters)
3. **Monitor performance** (latency, accuracy)
4. **Use appropriate threshold** for your use case
5. **Consider hybrid search** for best results
6. **Cache frequent queries** to improve speed
7. **Update index regularly** as documents change
8. **Test with real user queries** to validate quality

## Related Documentation

- [BM25 Algorithm](./bm25_algorithm.md)
- [Hybrid Search](./hybrid_search.md)
- [Database Schema](./database_schema.md)
- [API Reference](./api_reference.md)
