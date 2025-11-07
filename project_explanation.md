# 🧠 Master’s Thesis Project: AI-Powered Semantic Search System

My master's thesis project is nearly complete. It implements a **PDF ingestion and semantic search system** using PostgreSQL, sentence-transformers embeddings, and BM25 hybrid retrieval. Here's a clear overview of its current core capabilities:

#### 1. **PDF Ingestion with Embedding**
   - **Input**: Provide the full file path to a PDF (e.g., `A:\Master class\Semester 4\Thesis\Journal lists\An Analysis of Decoding Methods for LLM-based Agents for Faithful Multi-Hop Question Answering.pdf`).
   - **Process**:
     1. The system loads and parses the PDF.
     2. It splits the content into meaningful chunks (e.g., by paragraph or fixed token length).
     3. Each chunk is converted into a dense vector embedding using the **sentence-transformers** model: `paraphrase-multilingual-MiniLM-L12-v2`.
     4. Both the text chunk and its embedding are inserted into a PostgreSQL table (with `pgvector` enabled for vector storage and similarity search).

#### 2. **Direct Text Ingestion (Without PDF)**
   - Users can bypass PDF parsing and directly insert raw text.
   - The text is chunked, embedded using the same model, and stored in the database.

#### 3. **Search & Retrieval**
   - **Keyword Search**: Query the database using keywords.
   - **Hybrid Search**: Combines **BM25** (traditional lexical ranking) with **vector similarity search** (cosine similarity on embeddings) to improve speed and relevance.
   - Results are fetched quickly due to indexed BM25 fields and vector indexes.

#### 4. **Performance Optimization**
   - BM25 is used as a **first-stage retriever** to filter candidates rapidly.
   - Only top BM25 results are re-ranked using embedding similarity, making the search **faster and more efficient** than pure vector search.

---

### Research Focus (Thesis Comparison)
The core of my thesis is a **comparative analysis** between:
- **Traditional full-text search** (PostgreSQL + BM25)
- **Semantic embedding search** (pgvector + cosine similarity)

**Evaluation Metrics**:
- **Accuracy/Relevance**: Which method returns more semantically correct results for complex queries?
- **Speed**: How fast does each method retrieve and rank results?
- **Scalability**: Performance as the document collection grows.

The system currently runs via a **Rich-based terminal interface** (Python `rich` library) and works reliably.

---

### Next Development Steps
1. **API Layer**: Build a **FastAPI** backend to expose:
   - `/upload` (PDF or text)
   - `/search` (hybrid query)
   - `/delete`, `/update` endpoints
2. **Frontend**: Use **Flask** to create a web form for:
   - Uploading PDFs
   - Searching
   - Managing documents (CRUD)
3. **Dataset Curation**:
   - Collect academic papers related to:
     - LLM agents
     - Multi-hop question answering
     - Hybrid retrieval (BM25 + embeddings)
     - Faithful reasoning in LLMs
   - **Sources to explore**:
     - [arXiv.org](https://arxiv.org) (search: `"multi-hop question answering" + LLM`)
     - [Semantic Scholar](https://www.semanticscholar.org)
     - [ACL Anthology](https://aclanthology.org)
     - [PapersWithCode](https://paperswithcode.com)
     - Google Scholar (set alerts)

