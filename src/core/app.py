# FastAPI backend for Hybrid Search
import os
import sys
import time
from datetime import datetime
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# --------------------------------------------------------------------- #
# Setup path + load model + DB
# --------------------------------------------------------------------- #
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from db.db_connection import db_connection, get_model

from core.db.operations.hybrid_search import search_hybrid
from core.db.operations.keyword_search import search_keyword
from core.db.operations.semantic_search import search_semantic

# Load model once at startup
model = None


app = FastAPI(title="Hybrid Search API")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
def load_model_on_startup():
    global model
    model = get_model()
    print("Model loaded successfully at startup" if model else "Model failed to load")


# --------------------------------------------------------------------- #
# CORS
# --------------------------------------------------------------------- #
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "null",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------- #
# DB Helper
# --------------------------------------------------------------------- #
def get_db():
    conn = db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="DB connection failed")
    return conn, conn.cursor()


# --------------------------------------------------------------------- #
# Pydantic Models
# --------------------------------------------------------------------- #
class SearchRequest(BaseModel):
    query: str
    page: int = 1
    page_size: int = 10
    mode: str = "hybrid"  # semantic | keyword | hybrid


class SearchResult(BaseModel):
    doc_id: int
    content: str
    # score: str
    language: str
    created_at: str


class SearchResponse(BaseModel):
    results: List[SearchResult]
    stats: dict
    pagination: dict


# --------------------------------------------------------------------- #
# Search Endpoint – Uses Your Clean Functions
# --------------------------------------------------------------------- #
@app.post("/search", response_model=SearchResponse)
def search_endpoint(request: SearchRequest):
    start = time.time()
    conn, cursor = get_db()

    try:
        page = max(1, request.page)
        page_size = min(50, max(1, request.page_size))
        offset = (page - 1) * page_size

        # -----------------------------------------------------------------
        # Run the correct search
        # -----------------------------------------------------------------
        if request.mode == "semantic":
            all_results, _ = search_semantic(
                request.query, conn, cursor, model, top_k=offset + page_size
            )
            sem_count = len(all_results)
            bm25_count = 0
            search_type = "semantic"

        elif request.mode == "keyword":
            all_results, _ = search_keyword(
                request.query, cursor, top_k=offset + page_size
            )
            sem_count = 0
            bm25_count = len(all_results)
            search_type = "keyword"

        elif request.mode == "hybrid":
            all_results, stats = search_hybrid(
                request.query, conn, cursor, model, top_k=offset + page_size
            )
            sem_count = len(stats.get("sem_results", []))
            bm25_count = len(stats.get("bm25_results", []))
            search_type = "hybrid"

        else:
            raise HTTPException(400, "Invalid mode. Use: semantic, keyword, hybrid")

        # -----------------------------------------------------------------
        # Paginate in Python
        # -----------------------------------------------------------------
        paginated = all_results[offset : offset + page_size]

        # -----------------------------------------------------------------
        # Format results
        # -----------------------------------------------------------------
        formatted = []
        for r in paginated:
            created_at_str = (
                r[4].strftime("%Y-%m-%d")
                if isinstance(r[4], datetime)
                else str(r[4] or "")
            )
            formatted.append(
                SearchResult(
                    doc_id=r[0],
                    content=r[1],
                    # score=str(r[2]),
                    language=str(r[3] or "unknown"),
                    created_at=created_at_str,
                )
            )

        # -----------------------------------------------------------------
        # Stats + Logging
        # -----------------------------------------------------------------
        latency_ms = round((time.time() - start) * 1000, 2)

        cursor.execute(
            """
            INSERT INTO search_logs (query, search_type, top_k, results_count, latency_ms)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (request.query, search_type, page_size, len(paginated), latency_ms),
        )
        conn.commit()

        # -----------------------------------------------------------------
        # Response
        # -----------------------------------------------------------------
        return SearchResponse(
            results=formatted,
            stats={
                "search_type": search_type,
                "query_time_ms": latency_ms,
                "total_candidates": len(all_results),
                "returned": len(paginated),
                "semantic_count": sem_count,
                "bm25_count": bm25_count,
            },
            pagination={
                "page": page,
                "page_size": page_size,
                "total_pages": (len(all_results) + page_size - 1) // page_size,
                "total_results": len(all_results),
            },
        )

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
    finally:
        cursor.close()
        conn.close()


# --------------------------------------------------------------------- #
# Keep Your Other Endpoints (update, metrics, etc.)
# --------------------------------------------------------------------- #
# ... (your update_document_endpoint, /metrics, etc. stay exactly as-is)
# Just make sure they use `get_db()` instead of inline connection


@app.get("/")
def root():
    return RedirectResponse("/docs")
