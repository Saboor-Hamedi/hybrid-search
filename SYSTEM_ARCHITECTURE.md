# Hybrid Search System Architecture

## Overview
The Hybrid Search System is a sophisticated information retrieval engine designed to evaluate and optimize the balance between semantic understanding (Deep Learning) and exact keyword matching (Lexical Search).

The system architecture is broken down into three main layers: **Frontend (Evaluation Interface)**, **Backend (Orchestration)**, and **Core Search Algorithms**.

---

## 1. Core Search Algorithms (The Brain settings)

The system does not rely on a single algorithm but fuses two distinct paradigms to achieve high recall and precision.

### A. Semantic Search (Dense Retrieval)
*   **Goal**: Understand user intent and context, even if keywords don't match exactly.
*   **Model**: Uses **Sentence-Transformers** (e.g., `all-MiniLM-L6-v2`) to convert text into high-dimensional vectors (384 dimensions).
*   **Operation**:
    1.  User query is embedded into a vector.
    2.  System calculates **Cosine Similarity** between the query vector and document vectors in the database.
*   **Use Case**: Solves the "synonym problem" (e.g., "AI building blocks" matches "Machine Learning foundations").

### B. Keyword Search (Sparse Retrieval)
*   **Goal**: Find exact term matches and specific technical jargon.
*   **Algorithm**: **BM25 (Best Matching 25)**.
*   **Operation**:
    1.  Tokenizes the query into individual words.
    2.  Calculates scores based on Term Frequency (TF) and Inverse Document Frequency (IDF).
*   **Use Case**: Ensures precise matching for specific entities (e.g., "Doc #14202", "Transformer Architecture").

### C. Hybrid Fusion (The Secret Sauce)
The system combines the two streams using **Reciprocal Rank Fusion (RRF)** or **Linear Weighted Fusion**.
*   **Formula**: `Final_Score = (alpha * Semantic_Score) + ((1 - alpha) * Normalized_BM25_Score)`
*   **Weighting**: The system allows dynamic tuning of `alpha` (e.g., 0.7 Semantic / 0.3 Keyword) to favor one method over the other based on performance.

---

## 2. Backend Orchestration (Flask & PostgreSQL/ChromaDB)

The backend acts as the conductor, managing the data flow and calculations.

*   **Database**:
    *   **PostgreSQL (pgvector)**: Stores the text content and the vector embeddings.
    *   **Full-Text Search Index**: Optimized for fast BM25 lookups.
*   **Orchestration Logic (`flask_app.py`)**:
    *   Receives the user Query.
    *   **Parallel Execution**: Runs Vector Search and Keyword Search simultaneously.
    *   **Normalization**: Scales distinct score ranges (0-1 for vectors, 0-inf for BM25) into a unified distribution (0-1).
    *   **Latency Tracking**: Measures execution time for efficiency metrics (QpMS).

---

## 3. Evaluation Interface (The Frontend)

The frontend is not just a search bar; it is a **scientific instrument** built for thesis data collection.

### Interactive Evaluation
*   **Relevance Feedback**: Users can toggle a "Ground Truth" checkbox on any result. This data is stored mainly in the session state to calculate metrics on-the-fly.
*   **Real-Time Metrics Engine**:
    *   **NDCG@10 (Normalized Discounted Cumulative Gain)**: Measures the quality of the ranking.
    *   **Precision@K**: Measures the density of relevant results.
    *   **QpMS (Quality per Millisecond)**: A custom efficiency metric defined as `NDCG / Latency`.

### Data Collection
*   **Session Analysis Modal**: Aggregates all user interactions (queries + checked results).
*   **Export**: Formats the complex session data (Prompt, Relevant IDs, Calculated Metrics) into a standardized log format for your thesis documentation.

---

## Summary of Flow
1.  **User** Inputs Query ->
2.  **System** Embeds Query (Vector) + Tokenizes Query (Keyword) ->
3.  **DB** Retrieves Top K candidates from both indexes ->
4.  **System** Fuses & Ranks candidates ->
5.  **Frontend** Displays Results ->
6.  **User** Marks Relevance (Ground Truth) ->
7.  **System** Calculates Thesis Metrics (NDCG, QpMS) instantly.
