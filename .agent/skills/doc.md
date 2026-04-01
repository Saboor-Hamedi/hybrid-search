---
name: hybrid-search-expert
description: High-fidelity technical reference for the Hybrid Search project. Covers granular scoring mechanics, RAG architecture, database internals, and a comprehensive Feature Matrix.
---


# Hybrid Search — Deep Dive Technical Reference

> **Revision**: 4.0 (System Orchestration & Advanced Search Audit)  
> **Last Verified**: 2026-04-01  
> **Status**: COMPLETED - Low-level implementation details synchronized.

---

## 1. System Architecture & Data Flow

The system employs a **Micro-Service Proxy Pattern** to separate UI concerns from heavy ML/DB compute.

### Data Request Lifecycle:

1.  **Client/UI**: Sends Query via Flask (`localhost:5000`).
2.  **Flask Proxy**: Performs initial cleansing and routes POST to FastAPI (`localhost:8000/search`).
3.  **FastAPI Core**:
    - **Semantic Path**: Encodes query using `SentenceTransformer` (Singleton) ➡️ Executes Cosine Similarity in Postgres via `pgvector`.
    - **Keyword Path**: Executes `ts_rank` on `tsvector` indexed content.
    - **Fusion Path**: Normalizes scores and applies selected strategy (Linear/CombSUM/CombMNZ/RRF).
4.  **RAG Synthesis**: (Optional) Passes top-k context to `MultiAIManager` for LLM response generation.
5.  **Telemetry**: Logs query stats (latency, mode, count) to `search_logs`.

---

## 2. Advanced Search Implementations

### Reciprocal Rank Fusion (RRF)
RRF provides a scale-agnostic way to merge results from Semantic and Keyword systems by focusing on the **rank** rather than the absolute score.

- **Formula**: `sum(1 / (60 + rank))` for each document ID across all source lists.
- **Constant**: Uses `k=60` by default to dampen the impact of low-ranking results.
- **Implementation**: Managed by `RRFScorer.py`, which handles the parallel rank-normalization of disparate result sets.

### Learning-to-Rank (LTR)
The system implements a **2-Stage Retrieval & Re-ranking** architecture:

- **Stage 1 (Retrieval)**: Uses a standard Hybrid-Linear merge to retrieve the top-N (default 50) candidates.
- **Stage 2 (Re-ranking)**: Passes the candidates through a **Cross-Encoder model** (`ms-marco-MiniLM-L-6-v2`) which evaluates the query-document pair directly to produce a high-fidelity relevance score.
- **Performance**: LTR offers the highest precision but is gated by the compute cost of the Cross-Encoder; hence it is only applied to the top candidate pool.

### Dual-BM25 Architecture
The project maintains two distinct BM25 implementation paths for specific use cases:

1. **DB-Native (PostgreSQL)**: Uses `ts_rank` on GIN-indexed `tsvector` columns. Optimized for high-speed retrieval across the entire dataset.
2. **Python-Native (BM25Okapi)**: Uses the `rank_bm25` library for advanced re-ranking scenarios (like LTR) where in-memory document manipulation is required.

---

## 3. System Orchestration & Utilities

### Global System Signaling
The `system_state.py` module provides a centralized manager for cross-worker communication:
- **Stop Signaling**: An in-memory `stop_requested` flag allows the web server to immediately halt long-running indexing or ingestion jobs.
- **Job Tracking**: Tracks the count of active background tasks to ensure graceful shutdowns and database integrity.

### Asynchronous Data Export
The `core_logic.py` module handles high-volume document exports:
- **Batch Processing**: Fetches documents in batches of 500 to maintain low memory overhead.
- **In-Memory Tracking**: Uses a `task_id` based tracking system in `app.py` to allow the frontend to poll for export progress.
- **Auto-Cleanup**: A temporary export directory is automatically pruned of files older than one hour.

---

## 4. Feature Matrix & Capabilities

### A. Advanced Search & Retrieval
- **Multi-Mode Engine**: Support for Semantic, Keyword (BM25), and Hybrid retrieval.
- **Fuzzy-Mode Extensions**: Implementation of RRF and LTR for rank-stabilization.
- **Dynamic Fusion**: User-tunable Alpha Weighting (0-100% via UI slider).
- **Fusion Strategies**: Support for Linear, CombSUM, and CombMNZ normalization.

### B. RAG (Retrieval-Augmented Generation)
- **AI Answer Synthesis**: Live generation of answers based on the retrieved context.
- **Multi-Provider AI**: Standardized `MultiAIManager` supports Ollama, OpenAI, and other API-compliant LLMs.
- **Context Injection**: Intelligent prompt construction that synthesizes fragmented results into a cohesive data source.

### C. Documentation Ingestion Pipeline
- **Asynchronous Processing**: Background PDF ingestion to prevent UI blocking.
- **Throttled Concurrency**: Semaphore-based worker control (max 3 concurrent ingestions).
- **Recursive Chunking**: Smart text splitting (500 chars / 50 overlap) with boundary respect.
- **Dynamic Cleansing**: Automated removal of headers, footers, page numbers, and table-of-contents noise.

---

## 5. Database Internals (PostgreSQL)

### Vector Storage (pgvector)
- **Distance Metric**: Cosine Similarity via `(1 - (embedding <=> query_vector))`.
- **Implementation**: Automatic embedding generation during ingestion; stored as `VECTOR(384)`.

### Full-Text Search
- **Method**: `ts_rank` over `to_tsvector('english', content)`.

---

## 6. Developer Checklist (Hardening)
- [x] **Singleton Reliability**: `get_embedder` and `LTRScorer` prevent redundant model loading.
- [x] **Concurrency Safety**: Async throttlers and global state signaling for background processing.
- [x] **Normalization Control**: `HYBRID_BM25_NORM` environment variable for runtime tuning.
