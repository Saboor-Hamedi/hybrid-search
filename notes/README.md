# Hybrid Search Project - Complete Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Features](#features)
4. [Installation](#installation)
5. [Usage](#usage)
6. [API Reference](#api-reference)

## Project Overview

**Hybrid Search** is an advanced document retrieval system that combines semantic (vector-based) search with traditional keyword (BM25) search to provide the most relevant results.

### Key Technologies
- **Backend**: Python, Flask, FastAPI
- **Database**: PostgreSQL with pgvector extension
- **ML Model**: Sentence Transformers (all-MiniLM-L6-v2)
- **Frontend**: HTML, Bootstrap 5, JavaScript
- **Search Algorithms**: 
  - Semantic: Cosine similarity on embeddings
  - Keyword: BM25 (Best Matching 25)
  - Hybrid: Weighted combination of both

## Architecture

```
hybrid_search/
├── src/
│   └── core/
│       ├── db/
│       │   ├── algorithms/          # Search algorithms
│       │   │   └── bm25_algorithm.py
│       │   ├── operations/          # Database operations
│       │   │   └── search_flask/    # Search implementations
│       │   │       ├── semantic_search.py
│       │   │       ├── keyword_search.py
│       │   │       └── hybrid_search.py
│       │   ├── db_connection.py     # Database connection
│       │   └── search_queries.py    # SQL queries
│       ├── models/
│       │   └── ai_model.py          # ML model loading
│       ├── frontend/
│       │   ├── templates/
│       │   │   ├── components/      # Reusable components
│       │   │   └── portion/         # Base templates
│       │   └── static/              # CSS, JS, images
│       ├── utils/                   # Utility functions
│       ├── app.py                   # FastAPI backend
│       └── flask_app.py             # Flask frontend
└── notes/                           # Documentation
```

## Features

### 1. **Three Search Modes**

#### Semantic Search
- Uses vector embeddings to understand meaning
- Finds conceptually similar documents
- Best for: Natural language queries, conceptual searches
- Speed: ~440ms average

#### Keyword Search (BM25)
- Traditional full-text search
- Matches exact words and phrases
- Best for: Technical terms, specific keywords
- Speed: ~400ms average

#### Hybrid Search
- Combines both semantic and keyword search
- Weighted scoring (50% semantic + 50% BM25)
- Best for: Maximum recall and relevance
- Speed: ~1550ms average

### 2. **Advanced Features**
- ✅ Real-time search with pagination
- ✅ Adjustable page size (10-200 results)
- ✅ Performance statistics and graphs
- ✅ Score-based result ranking
- ✅ Multi-language support
- ✅ Responsive UI design

### 3. **Performance Metrics**
- Query latency tracking
- Semantic vs BM25 result counts
- Visual performance graphs
- Result quality scoring

## Installation

### Prerequisites
```bash
# Python 3.8+
python --version

# PostgreSQL 14+ with pgvector
psql --version
```

### Setup Steps

1. **Clone Repository**
```bash
git clone <repository-url>
cd hybrid_search
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure Database**
```bash
# Create database
createdb hybrid_search

# Enable pgvector extension
psql hybrid_search -c "CREATE EXTENSION vector;"
```

4. **Set Environment Variables**
```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=hybrid_search
export DB_USER=your_username
export DB_PASSWORD=your_password
```

5. **Run Migrations**
```bash
python src/core/db/migrations/create_tables.py
```

6. **Start Services**
```bash
# Terminal 1: FastAPI backend
cd src/core
uvicorn app:app --reload --port 8000

# Terminal 2: Flask frontend
python flask_app.py
```

7. **Access Application**
```
Frontend: http://localhost:5000
API Docs: http://localhost:8000/docs
```

## Usage

### Basic Search

1. Open http://localhost:5000
2. Enter your query in the search box
3. Select search mode (Hybrid/Semantic/Keyword)
4. Click "Search"
5. View results with scores and pagination

### API Usage

#### Search Endpoint
```python
import requests

# Search request
response = requests.post('http://localhost:8000/search', json={
    "query": "machine learning",
    "mode": "hybrid",
    "page": 1,
    "page_size": 50
})

data = response.json()
print(f"Found {len(data['results'])} results")
```

#### Response Format
```json
{
  "results": [
    {
      "doc_id": 123,
      "content": "Document content...",
      "score": 0.8542,
      "language": "en",
      "created_at": "2025-11-27"
    }
  ],
  "stats": {
    "query_time_ms": 445.67,
    "semantic_count": 57,
    "bm25_count": 114,
    "returned": 50
  },
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total_pages": 4,
    "total_results": 160
  }
}
```

## API Reference

### Endpoints

#### POST /search
Search documents using specified mode.

**Request Body:**
```json
{
  "query": "string",
  "mode": "hybrid|semantic|keyword",
  "page": 1,
  "page_size": 50
}
```

**Response:** See Response Format above

#### GET /document/{doc_id}
Get full document details.

**Parameters:**
- `doc_id`: Document ID (integer)
- `q`: Original query (optional)
- `mode`: Search mode (optional)
- `score`: Document score (optional)

### Search Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `semantic` | Vector-based similarity | Conceptual queries |
| `keyword` | BM25 keyword matching | Exact term searches |
| `hybrid` | Combined approach | Best overall results |

### Configuration

#### Search Parameters
```python
# In semantic_search.py
THRESHOLD = 0.25  # Minimum similarity score (0.0-1.0)
TOP_K = 100       # Maximum candidates to retrieve

# In hybrid_search.py
ALPHA = 0.5       # BM25 weight (0.0-1.0)
                  # Semantic weight = 1 - ALPHA
```

#### Model Configuration
```python
# In ai_model.py
model = SentenceTransformer("all-MiniLM-L6-v2")

# Upgrade options:
# model = SentenceTransformer("all-mpnet-base-v2")  # Better accuracy
# model = SentenceTransformer("multi-qa-mpnet-base-dot-v1")  # Q&A optimized
```

## Performance Tuning

### Improving Speed
1. Add database indexes
2. Use connection pooling
3. Cache frequent queries
4. Reduce TOP_K for faster results

### Improving Accuracy
1. Upgrade to better model (mpnet-base-v2)
2. Implement re-ranking
3. Fine-tune on your domain
4. Adjust threshold and weights

## Troubleshooting

### Common Issues

**500 Internal Server Error**
- Check database connection
- Verify pgvector extension installed
- Check model is loaded correctly

**No Results Found**
- Lower threshold (try 0.20 instead of 0.25)
- Try different search mode
- Check if documents exist in database

**Slow Performance**
- Add database indexes
- Reduce page_size
- Use semantic mode instead of hybrid

## Contributing

See individual feature documentation in the `notes/` folder for detailed implementation guides.

## License

[Your License Here]

## Contact

[Your Contact Information]
