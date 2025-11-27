# BM25 Algorithm Documentation

## Overview

BM25 (Best Matching 25) is a probabilistic ranking function used for keyword-based document retrieval. It's the gold standard for traditional full-text search and is used by major search engines including Elasticsearch and Apache Lucene.

## The Algorithm

### Formula

```
BM25(D, Q) = Σ IDF(qi) × (f(qi, D) × (k1 + 1)) / (f(qi, D) + k1 × (1 - b + b × |D| / avgdl))
```

Where:
- **D**: Document being scored
- **Q**: Query
- **qi**: i-th query term
- **f(qi, D)**: Frequency of qi in document D
- **|D|**: Length of document D (in words)
- **avgdl**: Average document length in the collection
- **k1**: Term frequency saturation parameter (typically 1.2-2.0)
- **b**: Length normalization parameter (typically 0.75)
- **IDF(qi)**: Inverse Document Frequency of term qi

### IDF (Inverse Document Frequency)

```
IDF(qi) = log((N - n(qi) + 0.5) / (n(qi) + 0.5))
```

Where:
- **N**: Total number of documents
- **n(qi)**: Number of documents containing term qi

## How It Works

### Example

**Document Collection:**
```
Doc 1: "Machine learning is a subset of AI"
Doc 2: "Deep learning is a type of machine learning"
Doc 3: "AI and machine learning are transforming industries"
```

**Query:** "machine learning"

**Step 1: Calculate IDF**
```
N = 3 (total documents)
n("machine") = 3 (appears in all docs)
n("learning") = 3 (appears in all docs)

IDF("machine") = log((3 - 3 + 0.5) / (3 + 0.5)) = log(0.5/3.5) ≈ -1.95
IDF("learning") = log((3 - 3 + 0.5) / (3 + 0.5)) ≈ -1.95
```

**Step 2: Calculate Term Frequency**
```
Doc 1: f("machine", Doc1) = 1, f("learning", Doc1) = 1
Doc 2: f("machine", Doc2) = 1, f("learning", Doc2) = 2
Doc 3: f("machine", Doc3) = 1, f("learning", Doc3) = 1
```

**Step 3: Apply BM25 Formula**
With k1=1.5, b=0.75, avgdl=7:
```
BM25(Doc1, Q) = IDF("machine") × TF_component("machine", Doc1) 
                + IDF("learning") × TF_component("learning", Doc1)
```

## Implementation

### File: `src/core/db/algorithms/bm25_algorithm.py`

```python
class BM25Search:
    """BM25 Search Engine with caching and optimization"""
    
    def __init__(self, k1=1.5, b=0.75):
        self.k1 = k1  # Term frequency saturation
        self.b = b    # Length normalization
        self.bm25_index = None
        self.corpus = None
    
    def build_index(self, cursor, normalize_fn=None):
        """Build BM25 index from database"""
        # Fetch documents
        cursor.execute("SELECT id, content, language, created_at FROM document")
        rows = cursor.fetchall()
        
        # Build corpus
        self.corpus = []
        for row in rows:
            doc_id, content, language, created_at = row
            if normalize_fn:
                content = normalize_fn(content)
            self.corpus.append((doc_id, content, language, created_at))
        
        # Create BM25 index
        tokenized = [doc[1].lower().split() for doc in self.corpus]
        self.bm25_index = BM25Okapi(tokenized, k1=self.k1, b=self.b)
        
        return len(self.corpus)
    
    def search(self, query, top_k=50, min_score=0.0):
        """Search using BM25"""
        query_tokens = query.lower().split()
        scores = self.bm25_index.get_scores(query_tokens)
        
        # Create results
        results = []
        for idx, score in enumerate(scores):
            if score > min_score:
                doc_id, content, lang, date = self.corpus[idx]
                results.append((doc_id, content, float(score), lang, date))
        
        # Sort and return top_k
        results.sort(key=lambda x: x[2], reverse=True)
        return results[:top_k]
```

### Usage

```python
from core.db.algorithms.bm25_algorithm import BM25Search

# Initialize
bm25 = BM25Search(k1=1.5, b=0.75)

# Build index
bm25.build_index(cursor)

# Search
results = bm25.search("machine learning", top_k=50)

for doc_id, content, score, lang, date in results:
    print(f"Doc {doc_id}: {score:.4f} - {content[:100]}")
```

## Parameter Tuning

### k1 (Term Frequency Saturation)

Controls how quickly term frequency saturates:

```python
# Low k1 (0.5-1.0): Quick saturation
# - Multiple occurrences matter less
# - Good for short documents
# - Reduces spam/keyword stuffing

# Medium k1 (1.2-1.5): Balanced (DEFAULT)
# - Standard setting
# - Works well for most cases

# High k1 (2.0-3.0): Slow saturation
# - Multiple occurrences matter more
# - Good for long documents
# - Rewards keyword density
```

**Example:**
```python
# For short tweets/messages
bm25 = BM25Search(k1=0.8, b=0.75)

# For long articles/documents
bm25 = BM25Search(k1=2.0, b=0.75)
```

### b (Length Normalization)

Controls document length penalty:

```python
# Low b (0.0-0.5): Weak normalization
# - Longer documents favored
# - Good when length indicates quality

# Medium b (0.75): Balanced (DEFAULT)
# - Standard setting
# - Fair treatment of all lengths

# High b (0.9-1.0): Strong normalization
# - Shorter documents favored
# - Good for mixed-length collections
```

**Example:**
```python
# For collections with similar-length docs
bm25 = BM25Search(k1=1.5, b=0.5)

# For mixed-length collections
bm25 = BM25Search(k1=1.5, b=0.9)
```

## Score Normalization

BM25 scores are unbounded. Normalize to 0-1 range:

```python
def normalize_scores(results):
    """Min-Max normalization"""
    if not results:
        return []
    
    scores = [r[2] for r in results]
    min_score = min(scores)
    max_score = max(scores)
    range_score = max_score - min_score
    
    if range_score == 0:
        return [(r[0], r[1], 1.0, r[3], r[4]) for r in results]
    
    normalized = []
    for doc_id, content, score, lang, date in results:
        norm_score = (score - min_score) / range_score
        normalized.append((doc_id, content, norm_score, lang, date))
    
    return normalized
```

## Optimization Techniques

### 1. Index Caching

```python
# Global instance for reuse
_bm25_engine = None

def get_bm25_engine():
    global _bm25_engine
    if _bm25_engine is None:
        _bm25_engine = BM25Search()
        _bm25_engine.build_index(cursor)
    return _bm25_engine
```

### 2. Incremental Updates

```python
def add_document(self, doc_id, content, language, created_at):
    """Add single document to index"""
    # Add to corpus
    self.corpus.append((doc_id, content, language, created_at))
    
    # Rebuild index (or use incremental update)
    tokenized = [doc[1].lower().split() for doc in self.corpus]
    self.bm25_index = BM25Okapi(tokenized, k1=self.k1, b=self.b)
```

### 3. Query Preprocessing

```python
def preprocess_query(query):
    """Clean and normalize query"""
    # Lowercase
    query = query.lower()
    
    # Remove special characters
    query = re.sub(r'[^\w\s]', '', query)
    
    # Remove stopwords (optional)
    stopwords = {'the', 'a', 'an', 'and', 'or', 'but'}
    words = [w for w in query.split() if w not in stopwords]
    
    return ' '.join(words)
```

## Advanced Features

### 1. BM25+ (Improved Version)

```python
def bm25_plus_score(tf, df, N, dl, avgdl, k1=1.5, b=0.75, delta=1.0):
    """
    BM25+ adds a small constant to prevent zero scores
    """
    idf = math.log((N - df + 0.5) / (df + 0.5))
    tf_component = ((k1 + 1) * tf) / (k1 * (1 - b + b * (dl / avgdl)) + tf)
    
    return idf * (tf_component + delta)
```

### 2. BM25L (Length Normalization)

```python
def bm25l_score(tf, df, N, dl, avgdl, k1=1.5, b=0.75):
    """
    BM25L uses different length normalization
    """
    idf = math.log((N + 1) / (df + 0.5))
    c_d = 1 - b + b * (dl / avgdl)
    tf_component = ((k1 + 1) * tf) / (k1 * c_d + tf)
    
    return idf * tf_component
```

### 3. Field-Weighted BM25

```python
def field_weighted_bm25(query, doc):
    """
    Weight different fields differently
    """
    title_score = bm25_score(query, doc.title) * 2.0  # Title more important
    content_score = bm25_score(query, doc.content) * 1.0
    tags_score = bm25_score(query, doc.tags) * 1.5
    
    return title_score + content_score + tags_score
```

## Comparison with Other Algorithms

| Algorithm | Type | Pros | Cons |
|-----------|------|------|------|
| **BM25** | Probabilistic | Fast, effective, interpretable | Keyword-only, no semantics |
| **TF-IDF** | Statistical | Simple, fast | Less effective than BM25 |
| **Vector Search** | Semantic | Understands meaning | Slower, needs ML model |
| **Hybrid** | Combined | Best of both | More complex |

## When to Use BM25

✅ **Use BM25 when:**
- Searching for specific terms/keywords
- Technical documentation
- Code search
- Legal documents
- Exact phrase matching needed
- Speed is critical
- No ML infrastructure available

❌ **Don't use BM25 when:**
- Need semantic understanding
- Queries are natural language questions
- Synonyms and related concepts important
- Multilingual search required

## Troubleshooting

### Issue: All Scores Are Zero
**Cause:** Query terms not in any document
**Solution:** 
- Check tokenization
- Verify documents are indexed
- Try broader query terms

### Issue: Scores Too High/Low
**Cause:** Improper normalization
**Solution:**
- Use score normalization
- Adjust k1 and b parameters
- Check document lengths

### Issue: Poor Ranking
**Cause:** Default parameters not optimal
**Solution:**
- Tune k1 and b for your data
- Try BM25+ or BM25L variants
- Consider field weighting

## Testing

```python
def test_bm25():
    # Test basic search
    bm25 = BM25Search()
    bm25.build_index(cursor)
    
    results = bm25.search("test query", top_k=10)
    assert len(results) <= 10
    assert all(r[2] > 0 for r in results)
    
    # Test score ordering
    scores = [r[2] for r in results]
    assert scores == sorted(scores, reverse=True)
    
    # Test normalization
    normalized = bm25.normalize_scores(results)
    norm_scores = [r[2] for r in normalized]
    assert max(norm_scores) <= 1.0
    assert min(norm_scores) >= 0.0
```

## Best Practices

1. **Tune parameters** for your specific corpus
2. **Normalize scores** before combining with other methods
3. **Cache the index** to avoid rebuilding
4. **Preprocess queries** consistently
5. **Monitor performance** and adjust as needed
6. **Consider hybrid approach** for best results
7. **Update index** when documents change
8. **Test with real queries** to validate quality

## Related Documentation

- [Semantic Search](./semantic_search.md)
- [Hybrid Search](./hybrid_search.md)
- [Performance Optimization](./performance_optimization.md)
