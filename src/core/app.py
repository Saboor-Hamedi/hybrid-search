# FastAPI backend for Hybrid Search
import os
import re
import sys
import time
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uuid

# Setup path + load model + DB
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from core.db.db_connection import db_connection, get_model
from core.db.operations.db_controller import update_record
from core.db.operations.document_management import delete_document, insert_document
from core.db.operations.search_flask.hybrid_search import search_hybrid
from core.db.operations.search_flask.keyword_search import search_keyword
from core.db.operations.search_flask.semantic_search import search_semantic
from core.db.operations.search_flask.rrf_search import search_rrf
from core.db.operations.search_flask.ltr_search import search_ltr
from core.utils.text_cleansing import clean_page_content

from core.export.core_logic import run_export_task

# Load model once at startup
model = None
export_tasks = {} # Global in-memory task tracker
try:
    MAX_CANDIDATES = int(os.environ.get("MAX_CANDIDATES", "1000"))
except Exception:
    MAX_CANDIDATES = 1000
app = FastAPI(title="Hybrid Search API")
# app.mount("/static", StaticFiles(directory="static"), name="static")


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
        "http://localhost:5000",
        "http://127.0.0.1:5000",
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
# Pymantic Models
# --------------------------------------------------------------------- #
class SearchRequest(BaseModel):
    query: str
    page: int = 1
    page_size: int = 10
    mode: str = "hybrid"  # semantic | keyword | hybrid | rrf | ltr
    fusion_strategy: Optional[str] = "linear" # linear | combsum | combmnz


class SearchResult(BaseModel):
    doc_id: int
    content: str
    score: float
    language: str
    created_at: str
    semantic_score: Optional[float] = None
    bm25_score: Optional[float] = None
    semantic_weight: Optional[float] = None
    bm25_weight: Optional[float] = None
    origin_mode: Optional[str] = None


class SearchResponse(BaseModel):
    results: List[SearchResult]
    stats: dict
    pagination: dict

class ContextItem(BaseModel):
    doc_id: str
    content: str

class GenerateRequest(BaseModel):
    query: str
    contexts: List[ContextItem]

# --------------------------------------------------------------------- #
# RAG / LLM Services
# --------------------------------------------------------------------- #
from core.utils.llm_service import OllamaService
ollama_service = OllamaService()

@app.post("/generate")
def generate_answer(request: GenerateRequest):
    """
    RAG Endpoint: Generates an AI answer using Local Ollama.
    Expects 'query' and 'contexts' (list of {doc_id, content}).
    """
    if not request.contexts:
        return {"answer": "No context provided to generate an answer."}
    
    # Convert Pydantic models to list of dicts
    context_dicts = [{"doc_id": c.doc_id, "content": c.content} for c in request.contexts]
    
    # Generate
    answer = ollama_service.generate_rag_response(request.query, context_dicts)
    return {"answer": answer}


# --------------------------------------------------------------------- #
# Search Endpoint – Uses Your Clean Functions
# --------------------------------------------------------------------- #
@app.post("/search", response_model=SearchResponse)
def search_endpoint(request: SearchRequest):
    start = time.time()
    conn, cursor = get_db()

    try:
        stats = {}
        page = max(1, request.page)
        try:
            PAGE_SIZE_MAX = int(os.environ.get("PAGE_SIZE_MAX", "200"))
        except Exception:
            PAGE_SIZE_MAX = 200
        # allow page_size up to PAGE_SIZE_MAX (default 200)
        page_size = min(PAGE_SIZE_MAX, max(1, request.page_size))
        offset = (page - 1) * page_size
        # Always retrieve up to max candidates, regardless of page
        top_k = MAX_CANDIDATES
        # Run the correct search
        # Run the correct search
        if request.mode == "semantic":
            all_results, _ = search_semantic(
                request.query, conn, cursor, model, top_k=top_k)
            sem_count = len(all_results)
            bm25_count = 0
            search_type = "semantic"

        elif request.mode == "keyword":
            all_results, _ = search_keyword(
                request.query, cursor, top_k=top_k *2)
            sem_count = 0
            bm25_count = len(all_results)
            search_type = "keyword"

        elif request.mode == "hybrid":
            strategy = request.fusion_strategy or "linear"
            search_type = f"hybrid-{strategy}"
            all_results, stats = search_hybrid(
                request.query, conn, cursor, model, top_k=top_k, fusion_strategy=strategy)
            
            sem_count = len(stats.get("sem_results") or [])
            bm25_count = len(stats.get("bm25_results") or [])

        elif request.mode == "rrf":
            all_results, stats = search_rrf(
                request.query, conn, cursor, model, top_k=top_k)
            sem_count = len(stats.get("sem_results") or [])
            bm25_count = len(stats.get("bm25_results") or [])
            search_type = "rrf"

        elif request.mode == "ltr":
            candidate_k = max(50, page_size * 2)
            all_results, stats = search_ltr(
                request.query, conn, cursor, model, top_k=candidate_k, candidate_k=candidate_k)
            search_type = "ltr"
            sem_count = 0
            bm25_count = 0

        else:
            raise HTTPException(400, "Invalid mode. Use: semantic, keyword, hybrid, rrf, ltr")

        # Paginate in Python
        paginated = all_results[offset : offset + page_size]
        total_results = len(all_results)  # e.g., 842
        total_pages = (total_results + page_size - 1) // page_size  # ceiling division
        paginated = all_results[offset : offset + page_size]

        # Format results
        formatted = []
        # If hybrid, we may have per-doc component scores in stats
        components_map = {}
        if request.mode == "hybrid":
            components_map = stats.get("components", {}) if isinstance(stats, dict) else {}

        for r in paginated:
            # r: (doc_id, content, score, language, created_at)
            created_at_str = (
                r[4].strftime("%Y-%m-%d")
                if isinstance(r[4], datetime)
                else str(r[4] or "")
            )

            # Default component values (may be filled below)
            semantic_score = None
            bm25_score = None
            semantic_weight = None
            bm25_weight = None

            # 1) Hybrid/RRF/LTR mode: use components_map/stats
            if request.mode in ["hybrid", "rrf", "ltr"]:
                comp = components_map.get(r[0], {})
                semantic_score = comp.get("semantic_score")
                bm25_score = comp.get("bm25_score")
                semantic_weight = comp.get("semantic_weight")
                bm25_weight = comp.get("bm25_weight")

            # 2) Semantic-only: the main score IS the semantic score
            if request.mode == "semantic":
                semantic_score = float(r[2])

            # 3) Keyword-only: the main score IS the bm25 score
            if request.mode == "keyword":
                bm25_score = float(r[2])

            formatted.append(
                SearchResult(
                    doc_id=r[0],
                    content=r[1],
                    score=float(r[2]),
                    language=str(r[3] or "en"),
                    created_at=created_at_str,
                    semantic_score=semantic_score,
                    bm25_score=bm25_score,
                    semantic_weight=semantic_weight,
                    bm25_weight=bm25_weight,
                    origin_mode=search_type,
                    strategy=request.fusion_strategy if request.mode == "hybrid" else None
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

        # Prepare stats to return to frontend; include hybrid-specific values if available
        response_stats = {
            "search_type": search_type,
            "query_time_ms": latency_ms,
            "total_candidates": len(all_results),
            "returned": len(paginated),
            "semantic_count": sem_count,
            "bm25_count": bm25_count,
        }

        # If the underlying search provided extra stats, merge them (Generic for Hybrid/RRF/LTR)
        if isinstance(stats, dict):
            if "alpha" in stats:
                response_stats["alpha"] = stats["alpha"]
            
            # Pass latency breakdown if available
            if "latency_stats" in stats:
                response_stats["latency_stats"] = stats["latency_stats"]
            
            # Extract raw rankings for Thesis Comparison (Top 50 IDs)
            # Assuming sem_results/bm25_results are lists of (id, content, score, ...)
            sem_raw = stats.get("sem_results", []) or []
            bm25_raw = stats.get("bm25_results", []) or []
            
            response_stats["rank_debug"] = {
                "semantic": [r[0] for r in sem_raw[:50]] if sem_raw else [],
                "keyword": [r[0] for r in bm25_raw[:50]] if bm25_raw else []
            }

        # Response
        return SearchResponse(
            results=formatted,
            stats=response_stats,
            pagination={
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "total_results": total_results,
            },
        )

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
    finally:
        cursor.close()
        conn.close()





@app.get("/")
def root():
    return RedirectResponse("/docs")

# --------------------------------------------------------------------- #
# Export Endpoints
# --------------------------------------------------------------------- #
@app.post("/export/start")
def start_export(background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    export_tasks[task_id] = {"progress": 0, "status": "pending"}
    background_tasks.add_task(run_export_task, task_id, export_tasks)
    return {"task_id": task_id}

@app.get("/export/status/{task_id}")
def get_export_status(task_id: str):
    if task_id not in export_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return export_tasks[task_id]

@app.get("/export/download/{task_id}")
def download_export(task_id: str):
    if task_id not in export_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = export_tasks[task_id]
    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="Export not completed")
    
    file_path = task.get("file_path")
    if not file_path or not os.path.exists(file_path):
         raise HTTPException(status_code=404, detail="Export file missing")
    
    return FileResponse(
        path=file_path,
        filename=task.get("file_name", "documents_export.json"),
        media_type="application/json"
    )

class UpdateRequest(BaseModel):
    content: str | None = None
    language: str | None = "en"

@app.post("/documents/{doc_id}/update")
def update_document(doc_id: int, request: UpdateRequest):
    conn, cursor = get_db()
    try:
        global model
        if model is None:
            model = get_model()
        content = request.content
        language = request.language or "en"
        if not content:
            cursor.execute("SELECT content, language FROM document WHERE id = %s", (doc_id,))
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Document not found")
            content = row[0] or ""
            language = row[1] or language
        if model is None:
            raise HTTPException(status_code=500, detail="Embedding model not loaded")
        cleaned = clean_page_content(content)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        embedding = model.encode(cleaned).tolist()
        ok = update_record(conn, cursor, doc_id, cleaned, language, embedding)
        conn.commit()
        return {"updated": bool(ok), "doc_id": doc_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")
    finally:
        cursor.close()
        conn.close()

class InsertRequest(BaseModel):
    content: str
    language: str | None = "en"

@app.post("/documents/insert")
def insert_new_document(request: InsertRequest):
    conn, cursor = get_db()
    try:
        global model
        if model is None:
            model = get_model()
        content = request.content
        language = request.language or "en"
        cleaned = clean_page_content(content)
        # insert_document will normalize and detect language; we pass cleaned
        doc_id = insert_document(cleaned, conn, cursor, model, commit=True, silent=True)
        if not doc_id:
            raise HTTPException(status_code=500, detail="Insert failed")
        return {"inserted": True, "doc_id": doc_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Insert failed: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.delete("/documents/{doc_id}")
def delete_document_endpoint(doc_id: int):
    conn, cursor = get_db()
    try:
        ok = delete_document(doc_id, conn, cursor)
        conn.commit()
        return {"deleted": bool(ok), "doc_id": doc_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")
    finally:
        cursor.close()
        conn.close()
