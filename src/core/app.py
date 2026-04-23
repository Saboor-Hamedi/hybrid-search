# FastAPI backend for Hybrid Search
import os
import re
import sys
import time
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uuid
import shutil
import tempfile

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
from core.ingestion.insert_pdf_chunks import insert_pdf

from core.export.core_logic import run_export_task

# Load model once at startup
model = None
export_tasks = {} # Global in-memory task tracker
try:
    MAX_CANDIDATES = int(os.environ.get("MAX_CANDIDATES", "10"))
except Exception:
    MAX_CANDIDATES = 10
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
    alpha: Optional[float] = None


class SearchResult(BaseModel):
    doc_id: int
    content: str
    score: float
    language: str
    created_at: str
    semantic_score: Optional[float] = None
    bm25_score: Optional[float] = None
    semantic_rank: Optional[int] = None
    bm25_rank: Optional[int] = None
    semantic_weight: Optional[float] = None
    bm25_weight: Optional[float] = None
    origin_mode: Optional[str] = None
    strategy: Optional[str] = None


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
    provider: Optional[str] = "ollama"
    model: Optional[str] = "qwen2.5:0.5b"
    api_key: Optional[str] = ""
    base_url: Optional[str] = "http://localhost:11434"

# --------------------------------------------------------------------- #
# RAG / LLM Services (High-Fidelity AI System)
# --------------------------------------------------------------------- #
import sys

# Ensure AI clients are importable
ai_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ai_dir not in sys.path:
    sys.path.append(ai_dir)

from ai.MultiAIManager import MultiAIManager

# --------------------------------------------------------------------- #

@app.post("/generate")
def generate_answer(request: GenerateRequest):
    """
    Classic RAG Endpoint: Generates a full AI answer.
    """
    if not request.contexts:
        return {"answer": "No context provided."}

    provider_name = request.provider or "ollama"
    model_name = request.model or "qwen2.5:0.5b"
    api_key = request.api_key or ""
    base_url = request.base_url or "http://localhost:11434"

    client = MultiAIManager.create_client(
        provider_name=provider_name, 
        api_key=api_key,
        model=model_name,
        base_url=base_url
    )

    if not client:
        return {"answer": f"Error: AI Provider '{provider_name}' not available."}
    
    context_dicts = [{"doc_id": c.doc_id, "content": c.content} for c in request.contexts]
    
    try:
        if hasattr(client, 'generate_rag_response'):
            answer = client.generate_rag_response(request.query, context_dicts)
        else:
            context_text = "\n".join([f"Doc {c['doc_id']}: {c['content']}" for c in context_dicts])
            answer = client.generate_response(
                prompt=f"Context Data:\n{context_text}\n\nUser Question: {request.query}",
                system_instruction="You are an Academic Research Assistant."
            )
        return {"answer": answer}
    except Exception as e:
        return {"answer": f"Backend AI Error: {str(e)}"}

@app.post("/generate-stream")
async def generate_answer_stream(request: GenerateRequest):
    """
    Streaming RAG Endpoint: Returns a real-time stream of the AI's response.
    """
    if not request.contexts:
        def err(): yield "No context provided."
        return StreamingResponse(err(), media_type="text/plain")

    provider_name = request.provider or "ollama"
    model_name = request.model or "qwen2.5:0.5b"
    api_key = request.api_key or ""
    base_url = request.base_url or "http://localhost:11434"

    client = MultiAIManager.create_client(
        provider_name=provider_name, 
        api_key=api_key,
        model=model_name,
        base_url=base_url
    )

    if not client:
        def err(): yield f"Error: AI Provider '{provider_name}' not available."
        return StreamingResponse(err(), media_type="text/plain")
    
    context_dicts = [{"doc_id": c.doc_id, "content": c.content} for c in request.contexts]
    
    def stream_logic():
        try:
            # If client has specific RAG stream, use it, else fallback to standard stream
            if hasattr(client, 'generate_rag_stream'):
                for chunk in client.generate_rag_stream(request.query, context_dicts):
                    yield chunk
            else:
                context_text = "\n".join([f"Doc {c['doc_id']}: {c['content']}" for c in context_dicts])
                full_prompt = f"Context Data:\n{context_text}\n\nUser Question: {request.query}"
                for chunk in client.generate_stream(full_prompt):
                    yield chunk
        except Exception as e:
            yield f"\n[Backend Stream Error: {str(e)}]"

    return StreamingResponse(stream_logic(), media_type="text/event-stream")



# --------------------------------------------------------------------- #
# Search Endpoint – Uses Your Clean Functions
# --------------------------------------------------------------------- #
@app.post("/search", response_model=SearchResponse)
def search_endpoint(request: SearchRequest):
    start = time.time()
    conn, cursor = get_db()

    try:
        stats = {}
        page = 1
        page_size = 10
        offset = 0
        top_k = 10
        # Run the correct search
        # Run the correct search
        # --- UNIVERSAL DATA GATHERING (For Thesis/NDCG Comparison) ---
        # We always run both to ensure rank_debug is available for Strategy Comparison
        sem_raw_full, _ = search_semantic(request.query, conn, cursor, model, top_k=50)
        bm25_raw_full, _ = search_keyword(request.query, cursor, top_k=50)

        if request.mode == "semantic":
            all_results = sem_raw_full
            sem_count = len(all_results)
            bm25_count = 0
            search_type = "semantic"

        elif request.mode == "keyword":
            all_results = bm25_raw_full
            sem_count = 0
            bm25_count = len(all_results)
            search_type = "keyword"

        elif request.mode == "hybrid":
            strategy = request.fusion_strategy or "linear"
            search_type = f"hybrid-{strategy}"
            all_results, stats = search_hybrid(
                request.query, conn, cursor, model, top_k=top_k, fusion_strategy=strategy, alpha=request.alpha)
            sem_count = len(stats.get("sem_results") or [])
            bm25_count = len(stats.get("bm25_results") or [])

        elif request.mode == "rrf":
            all_results, stats = search_rrf(
                request.query, conn, cursor, model, top_k=top_k)
            sem_count = len(stats.get("sem_results") or [])
            bm25_count = len(stats.get("bm25_results") or [])
            search_type = "rrf"

        elif request.mode == "ltr":
            candidate_k = 20
            all_results, stats = search_ltr(
                request.query, conn, cursor, model, top_k=top_k, candidate_k=candidate_k)
            search_type = "ltr"
            sem_count = 0
            bm25_count = 0
        
        else:
            raise HTTPException(400, f"Invalid mode '{request.mode}'. Use: semantic, keyword, hybrid, rrf, ltr")
        
        # Ensure stats has the raw results for universal rank_debug handling later
        if not stats: 
             stats = {}
        if "sem_results" not in stats: stats["sem_results"] = sem_raw_full
        if "bm25_results" not in stats: stats["bm25_results"] = bm25_raw_full

        # Paginate in Python
        paginated = all_results[offset : offset + page_size]
        total_results = len(all_results)  # e.g., 842
        total_pages = (total_results + page_size - 1) // page_size  # ceiling division
        paginated = all_results[offset : offset + page_size]

        # Format results
        formatted = []
        # If hybrid, we may have per-doc component scores in stats
        components_map = {}
        if request.mode in ["hybrid", "rrf", "ltr"]:
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
            semantic_rank = None
            bm25_rank = None
            semantic_weight = None
            bm25_weight = None

            # 1) Hybrid/RRF/LTR mode: use components_map/stats
            if request.mode in ["hybrid", "rrf", "ltr"]:
                comp = components_map.get(r[0], {})
                semantic_score = comp.get("semantic_score")
                bm25_score = comp.get("bm25_score")
                semantic_rank = comp.get("semantic_rank")
                bm25_rank = comp.get("bm25_rank")
                semantic_weight = comp.get("semantic_weight")
                bm25_weight = comp.get("bm25_weight")

            # 2) Semantic-only: the main score IS the semantic score
            if request.mode == "semantic":
                semantic_score = float(r[2])
                # Find rank in all_results
                try:
                    semantic_rank = [res[0] for res in all_results].index(r[0]) + 1
                except:
                    pass

            # 3) Keyword-only: the main score IS the bm25 score
            if request.mode == "keyword":
                bm25_score = float(r[2])
                # Find rank in all_results
                try:
                    bm25_rank = [res[0] for res in all_results].index(r[0]) + 1
                except:
                    pass

            formatted.append(
                SearchResult(
                    doc_id=r[0],
                    content=r[1],
                    score=float(r[2]),
                    language=str(r[3] or "en"),
                    created_at=created_at_str,
                    semantic_score=semantic_score,
                    bm25_score=bm25_score,
                    semantic_rank=semantic_rank,
                    bm25_rank=bm25_rank,
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
        
        # High-Fidelity: Skip destructive re.sub(r"\s+", " ", ...) 
        # cleaned = clean_page_content(content)
        # cleaned = re.sub(r"\s+", " ", cleaned).strip()
        embedding = model.encode(content).tolist()
        ok = update_record(conn, cursor, doc_id, content, language, embedding)
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
        # High-Fidelity: Skip aggressive cleaning/normalization for manual entries
        doc_id = insert_document(content, conn, cursor, model, commit=True, silent=True, preserve_fidelity=True)
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

# --------------------------------------------------------------------- #
# PDF Ingestion Endpoint (Offloaded from Flask)
# --------------------------------------------------------------------- #
import asyncio
processing_semaphore = asyncio.Semaphore(3) # Limit to 3 concurrent ingestions to save memory/crashes

@app.post("/upload-pdf")
async def upload_pdf_endpoint(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Handles PDF upload and starts background ingestion with throttling."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    try:
        # Create a temp file to store uploaded PDF
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"fastapi_upload_{uuid.uuid4()}_{file.filename}")
        
        # Save file to disk
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Define background processing wrapper
        async def run_ingestion_throttled(path, filename):
            async with processing_semaphore:
                print(f"🚀 Starting (throttled) ingestion for: {filename}")
                conn = None
                try:
                    # insert_pdf is likely synchronous, we run in thread if needed
                    # but here we'll just call it since add_task handles the loop
                    import functools
                    loop = asyncio.get_event_loop()
                    
                    def sync_wrapper():
                        c, cur = get_db()
                        try:
                            return insert_pdf(path, c, cur)
                        finally:
                            cur.close()
                            c.close()

                    success = await loop.run_in_executor(None, sync_wrapper)
                    print(f"✅ Ingestion for {filename} finished. Success: {success}")
                except Exception as e:
                    print(f"❌ Background ingestion crashed for {filename}: {e}")
                finally:
                    if os.path.exists(path):
                        os.remove(path)

        background_tasks.add_task(run_ingestion_throttled, temp_path, file.filename)
        return {"success": True, "message": "Background ingestion queued", "filename": file.filename}

    except Exception as e:
        print(f"Upload Endpoint Error: {e}")
        raise HTTPException(status_code=500, detail=f"PDF upload failed: {str(e)}")

# --------------------------------------------------------------------- #
# System Health & Stats
# --------------------------------------------------------------------- #
@app.get("/api/system/health")
def get_system_health():
    """Detailed telemetry for HNSW index and storage health."""
    conn, cursor = get_db()
    try:
        # Get counts
        cursor.execute("SELECT COUNT(*) FROM document")
        doc_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM document_embedding")
        embed_count = cursor.fetchone()[0]
        
        # Get HNSW stats
        cursor.execute("""
            SELECT pg_size_pretty(pg_relation_size('document_embedding_embedding_idx'));
        """)
        index_size = cursor.fetchone()[0]
        
        # Get storage size of the table themselves
        cursor.execute("SELECT pg_size_pretty(pg_total_relation_size('document'));")
        doc_storage = cursor.fetchone()[0]
        
        cursor.execute("SELECT pg_size_pretty(pg_total_relation_size('document_embedding'));")
        embed_storage = cursor.fetchone()[0]
        
        return {
            "status": "healthy",
            "document_count": doc_count,
            "embedding_count": embed_count,
            "index_size": index_size,
            "doc_storage": doc_storage,
            "embed_storage": embed_storage,
            "hnsw_config": {
                "index_name": "document_embedding_embedding_idx",
                "m": 16,
                "ef_construction": 64
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health probe failed: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.get("/api/system/stats")
def get_system_stats():
    conn, cursor = get_db()
    try:
        cursor.execute("SELECT COUNT(*) FROM document")
        doc_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM search_logs")
        log_count = cursor.fetchone()[0]
        
        # Connection metadata for high-fidelity auditing
        db_info = {
            "host": os.getenv("DB_HOST", "localhost"),
            "database": os.getenv("DB_NAME", "search"),
            "user": os.getenv("DB_USER", "postgres")
        }
        
        return {
            "document_count": doc_count, 
            "search_log_count": log_count, 
            "db_info": db_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats failed: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.post("/api/system/stop-indexing")
def stop_indexing():
    """Trigger the global stop flag across all workers."""
    from core.utils import system_state
    system_state.request_stop()
    return {"success": True, "message": "Global stop request sent."}

@app.post("/api/system/reset")
def reset_system_data():
    from core.utils import system_state
    system_state.request_stop() # Safety: trigger stop before reset
    
    conn, cursor = get_db()
    try:
        print("🚮 DANGER: Executing full system data reset...")
        
        # Use TRUNCATE CASCADE for speed and certainty. 
        # It handles all foreign key relationships in one go.
        cursor.execute("TRUNCATE TABLE document_embedding, document, search_logs RESTART IDENTITY CASCADE;")
        
        conn.commit()
        print("✅ Data purge committed to Database.")
        
        # Refresh BM25 cache if relevant
        try:
            from core.utils import bm25_utils
            bm25_utils.needs_update = True
        except Exception as e:
            print(f"⚠️ BM25 refresh skipped: {e}")
        
        # Clear the flag after a successful reset
        system_state.clear_stop()
            
        return {"success": True, "message": "All data cleared successfully"}
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Reset failed dramatically: {e}")
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")
    finally:
        cursor.close()
        conn.close()
