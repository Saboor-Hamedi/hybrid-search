# FastAPI backend for Hybrid Search
import os
import sys
import time
from datetime import datetime

import psycopg2
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Setup path and load model
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from core.db.operations.database_operations import search
from db.db_connection import db_connection, get_model
from core.db.operations.db_controller import update_record

# Performance optimizations load model at startup
model = None
app = FastAPI(title="Hybrid Search API")
app.mount('/static', StaticFiles(directory='static'), name='static')


@app.on_event("startup")
def load_model_on_startup():
    global model
    model = get_model()
    if model:
        print("✅ Model loaded successfully at startup")
    else:
        print("⚠️ Model failed to load at startup")
# CORS
app.add_middleware(
    CORSMiddleware,
    # Allow the common dev origins used by the frontend. In development you
    # can set this to ["*"] but it's safer to list the exact origins.
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

# Initialize database connection and model at startup
def get_db_connection_and_cursor():
    conn = db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="DB connection failed")
    cursor = conn.cursor()
    return conn, cursor


# Models
class SearchRequest(BaseModel):
    query: str
    page: int = 1
    page_size: int = 10
    use_hybrid: bool = True

class SearchResult(BaseModel):
    doc_id: int
    content: str
    score: float
    language: str
    created_at: str

class UpdateRequest(BaseModel):
    doc_id: int
    content: str
    language: str = 'unknown'
    embedding: list[float] | None = None

class DocumentUpdate(BaseModel):
    content: str
    language: str = 'en'
@app.put("/documents/{doc_id}", response_model=dict)

def update_document_endpoint(doc_id: int, document: DocumentUpdate):
    conn, cursor = get_db_connection_and_cursor()
    model = get_model()
    try:
        embedding = None
        if model and document.content:
            embedding = model.encode([document.content])[0].tolist()
        success = update_record(
            conn=conn,
            cursor=cursor,
            doc_id=doc_id,
            content=document.content,
            language=document.language,
            embedding=embedding
        )
        if success:
            conn.commit()
            return True
        else:
            conn.rollback()
            raise HTTPException(status_code=404, detail=f"Document with ID {doc_id} not found")
    except psycopg2.Error as e: # Catch database-specific errors
        conn.rollback() # Rollback on error
        raise HTTPException(status_code=500, detail=f"Database update failed: {str(e)}")
    except Exception as e: # Catch any other errors during update
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")
    finally:
        cursor.close() # Always close the cursor
        conn.close() # Always close the connection
# Metrics endpoint
@app.get("/metrics")
def get_metrics():

    conn, cursor = get_db_connection_and_cursor()

    try:
        cursor.execute("""
            SELECT
                search_type,
                ROUND(AVG(latency_ms)::NUMERIC, 2) as avg_latency,
                ROUND(AVG(results_count)::NUMERIC, 1) as avg_results,
                COUNT(*) as total_queries
            FROM search_logs
            GROUP BY search_type
        """)
        rows = cursor.fetchall()
        return {
            row[0]: {
                "avg_latency_ms": float(row[1]),
                "avg_results": float(row[2]),
                "total_queries": row[3]
            }
            for row in rows
        }
    finally:
        cursor.close()
        conn.close()
@app.post("/update", response_model=dict)
def update_endpoint(request: UpdateRequest):
    """Legacy update endpoint - consider using PUT /documents/{doc_id} instead"""
    conn, cursor = get_db_connection_and_cursor()

    try:
        success = update_record(
            conn=conn,
            cursor=cursor,
            doc_id=request.doc_id,
            content=request.content,
            language=request.language,
            embedding=request.embedding
        )
        if success:
            conn.commit()
            return {"message": "Document updated successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Document with ID {request.doc_id} not found")

    except psycopg2.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")
    finally:
        cursor.close()
        conn.close()
# Search endpoint with pagination
@app.post("/search")
def search_endpoint(request: SearchRequest):
    start = time.time()
    conn, cursor = get_db_connection_and_cursor()
    model = get_model()


    offset = (request.page - 1) * request.page_size
    limit = min(request.page_size, 50)  # Safety cap
    all_results = []
    hybrid_stats ={}

    try:
        if request.use_hybrid:
            # Fetch MORE results to enable pagination (top_k = offset + limit)
            all_results, hybrid_stats = search(
                query=request.query,
                conn=conn,
                cursor=cursor,
                model=model,
                top_k=offset + limit  # Critical: fetch enough for current page
            )
            # Paginate in Python
            paginated = all_results[offset:offset + limit]
            search_type = "hybrid"
        else:
            # Keyword search with OFFSET/LIMIT in SQL
            cursor.execute("""
                SELECT id, content, ts_rank(content_tsvector, plainto_tsquery('simple', %s)) AS score,
                       languages, created_at::text
                FROM document
                WHERE content_tsvector @@ plainto_tsquery('simple', %s)
                ORDER BY score DESC
                LIMIT %s OFFSET %s
            """, (request.query, request.query, limit, offset))
            paginated = [
                (row[0], row[1], float(row[2]), row[3] or "unknown", row[4])
                for row in cursor.fetchall()
            ]
            search_type = "keyword"

        # Log
        latency = (time.time() - start) * 1000
        if search_type == "hybrid":
            hybrid_stats = {
                    "keyword_time_ms": round(latency, 2),
                    "keyword_count": len(paginated),
                }
        cursor.execute("""
            INSERT INTO search_logs (query, search_type, top_k, results_count, latency_ms)
            VALUES (%s, %s, %s, %s, %s)
        """, (request.query, search_type, limit, len(paginated), latency))
        conn.commit()

        # Format results
        formatted = []
        cosine_scores = []
        for r in paginated:
            created_at_val = r[4] if len(r) > 4 else None
            created_at_str = (
                created_at_val.isoformat() if isinstance(created_at_val, datetime)
                else str(created_at_val or "unknown")
            )
            lang = r[3] if len(r) > 3 else "unknown"
            score_val = float(r[2]) if r[2] is not None else 0.0
            cosine_scores.append(score_val)

            formatted.append({
                "doc_id": r[0],
                "content": r[1] or "",
                "score": score_val,
                "language": str(lang),
                "created_at": created_at_str
            })

        #  Compute average cosine
        avg_cosine = (
            sum(cosine_scores) / len(cosine_scores)
            if cosine_scores else 0
        )

        #  Return structured response with stats
        response_data = {
            "results": formatted,
            "stats": {
                "search_type": search_type,
                "query_time_ms": round(latency, 2),
                "num_candidates": len(formatted),
                "average_cosine": round(avg_cosine, 4),
                **hybrid_stats
            },
        }

        return JSONResponse(content=response_data)

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.get('/')
async def root():
    return RedirectResponse(url="/docs")
