'''
 ! This is my Flask app.
'''
import logging
import os
import sys

# Ensure 'src' is in path BEFORE importing local modules that might rely on 'core' package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import requests

from db.db_connection import db_connection
from flask import Flask, redirect, render_template, request
from frontend.graphs.analyze import generate_query_graph

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "frontend", "templates")
STATIC_DIR = os.path.join(BASE_DIR, "frontend", "static")
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
API_URL = "http://127.0.0.1:8000"  # FastAPI backend
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0


#  Helper: highlight query words
def highlight_text(text: str, query: str) -> str:
    if not query or not text:
        return text
    import re
    terms = re.escape(query).split()
    pattern = "|".join(terms)
    return re.sub(f"({pattern})", r"<mark>\1</mark>", text, flags=re.IGNORECASE)


#  / – search page
@app.route("/", methods=["GET", "POST"])
def home():
    results = []
    stats = {}
    query = ""
    mode = "hybrid"
    fusion_strategy = "linear"
    use_ltr = False
    page = 1
    page_size = 10
    total_pages = 0
    total_results = 0
    # Show graph for searchs
    graph_img = None

    input_source = request.form if request.method == "POST" else request.args


    # 1. Initialize/Retrieve Search Parameters
    query = input_source.get("query", "").strip()
    mode = input_source.get("mode", "hybrid")
    fusion_strategy = input_source.get("fusion_strategy", "linear")
    use_ltr = input_source.get("use_ltr") == "true" or input_source.get("use_ltr") == "on"
    use_ai = input_source.get("use_ai") == "true" or input_source.get("use_ai") == "on"  # AI Toggle
    alpha = input_source.get("alpha")
    if alpha:
        try:
            alpha = float(alpha) / 100.0  # Slider is 0-100, backend wants 0.0-1.0
        except:
            alpha = None
    try:
        page = int(input_source.get("page", 1))
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = int(input_source.get("page_size", 10))
    except (TypeError, ValueError):
        page_size = 10


    if query:
        # Determine actual API mode based on LTR toggle
        api_mode = mode
        if use_ltr and "hybrid" in mode:
             api_mode = "ltr"

        payload = {
            "query": query,
            "page": page,
            "page_size": page_size,
            "mode": api_mode,
            "fusion_strategy": fusion_strategy,
            "alpha": alpha
        }

        try:
            r = requests.post(f"{API_URL}/search", json=payload, timeout=15)
            r.raise_for_status()
            data = r.json()
            # ----- results -----
            results = data.get("results", [])
            for r in results:
                r["content_highlighted"] = highlight_text(r["content"], query)

            # ----- pagination -----
            pagination = data.get("pagination", {})
            total_pages = pagination.get("total_pages", 0)
            total_results = pagination.get("total_results", 0)

            total_pages = 1
            total_results = len(results)
            # ---------------------------------------------


            # ----- stats -----
            raw = data.get("stats", {})
            stats = {
                "query_time_ms": round(raw.get("query_time_ms", 0), 2),
                "semantic_count": raw.get("semantic_count", 0),
                "bm25_count": raw.get("bm25_count", 0),
                "returned": raw.get("returned", 0),
                # Thesis Metrics (Placeholders for now, to be calculated via Evaluation Service)
                "precision_at_k": raw.get("metrics", {}).get("precision", "N/A"),
                "recall_at_k": raw.get("metrics", {}).get("recall", "N/A"),
                "map_score": raw.get("metrics", {}).get("map", "N/A"),
                "ndcg_score": raw.get("metrics", {}).get("ndcg", "N/A"),
                "qpms": raw.get("metrics", {}).get("qpms", "N/A"),
                "router_accuracy": raw.get("metrics", {}).get("router_acc", "N/A"),
                "router_choice": raw.get("metrics", {}).get("router_choice", "Hybrid"),
                "rank_debug": raw.get("rank_debug", {}),
                "latency_stats": raw.get("latency_stats", {})
            }
            graph_img = generate_query_graph(
                mode=mode,
                latency_ms=stats['query_time_ms'],
                results_count=total_results,
                semantic_count=stats.get('semantic_count', 0),
                bm25_count=stats.get('bm25_count', 0)
            )

        except Exception as e:
            results = []
            stats = {"error": str(e), "returned": 0, "query_time_ms": 0}
            print("Backend error:", e)
            total_pages = 0
            total_results = 0

    # pagination helpers
    prev_page = page - 1 if page > 1 else None
    next_page = page + 1 if page < total_pages else None

    # Detect AJAX request (Header or URL Param)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or \
              request.args.get('ajax') == '1' or \
              request.form.get('ajax') == '1'

    if is_ajax:
        return {
            "results": results,
            "stats": stats,
            "query": query,
            "mode": mode,
            "page": page,
            "prev_page": prev_page,
            "next_page": next_page,
            "total_pages": total_pages,
            "total_results": total_results,
            "use_ai": use_ai,
            "fusion_strategy": fusion_strategy,
            "page_size": page_size
        }

    return render_template(
        "index.html",
        results=results,
        stats=stats,
        query=query,
        mode=mode,
        fusion_strategy=fusion_strategy,
        use_ltr=use_ltr,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        total_results=total_results,
        prev_page=prev_page,
        next_page=next_page,
        graph_img=graph_img,
        use_ai=use_ai,
        alpha=alpha if alpha is not None else 0.5
    )


#  /document/<id> – JSON API for Preview Modal
@app.route("/api/document/<int:doc_id>")
def get_document_api(doc_id: int):
    conn, cursor = _db()
    try:
        cursor.execute("SELECT id, content, language, created_at FROM document WHERE id = %s", (doc_id,))
        row = cursor.fetchone()
        if not row:
            return {"error": "Document not found"}, 404
        
        return {
            "doc_id": row[0],
            "content": row[1] or "",
            "language": (row[2] or "en").upper(),
            "created_at": row[3].strftime("%Y-%m-%d %H:%M") if row[3] else "unknown"
        }
    except Exception as e:
        return {"error": str(e)}, 500
    finally:
        cursor.close()


def _db():

    conn = db_connection()
    if not conn:
        raise RuntimeError("DB connection failed")
    return conn, conn.cursor()


# ------------------------------------------------------------------ #
#  /search_debug – debug page for RAG/Scores
# ------------------------------------------------------------------ #
@app.post("/document/<int:doc_id>/reembed")
def reembed_document(doc_id: int):
    back_query = request.form.get("q", "")
    back_mode = request.form.get("mode", "hybrid")
    try:
        r = requests.post(f"{API_URL}/documents/{doc_id}/update", json={}, timeout=15)
        r.raise_for_status()
    except requests.RequestException as e:
        print("Re-embed error:", e)
    return redirect(f"/document/{doc_id}?q={back_query}&mode={back_mode}")

@app.post("/document/<int:doc_id>/update_post")
def update_post(doc_id: int):
    back_query = request.form.get("q", "")
    back_mode = request.form.get("mode", "hybrid")
    content = request.form.get("content", "")
    language = request.form.get("language", "en")
    redirect_to = request.form.get("redirect_to", "document")
    
    try:
        r = requests.post(
            f"{API_URL}/documents/{doc_id}/update",
            json={"content": content, "language": language},
            timeout=20,
        )
        r.raise_for_status()
    except requests.RequestException as e:
        print("Update post error:", e)
    
    if redirect_to == "home":
        return redirect(f"/?query={back_query}&mode={back_mode}")
    return redirect(f"/document/{doc_id}?q={back_query}&mode={back_mode}")

@app.post("/document/new_post")
def new_post():
    back_query = request.form.get("q", "")
    back_mode = request.form.get("mode", "hybrid")
    content = request.form.get("content", "")
    language = request.form.get("language", "en")
    try:
        r = requests.post(
            f"{API_URL}/documents/insert",
            json={"content": content, "language": language},
            timeout=20,
        )
        r.raise_for_status()
        data = r.json()
        doc_id = data.get("doc_id")
        if doc_id:
            return redirect(f"/document/{doc_id}?q={back_query}&mode={back_mode}")
    except requests.RequestException as e:
        print("New post error:", e)
    return redirect(f"/?query={back_query}&mode={back_mode}")

@app.post("/document/<int:doc_id>/delete_post")
def delete_post(doc_id: int):
    back_query = request.form.get("q", "")
    back_mode = request.form.get("mode", "hybrid")
    try:
        r = requests.delete(f"{API_URL}/documents/{doc_id}", timeout=15)
        r.raise_for_status()
    except requests.RequestException as e:
        print("Delete post error:", e)
    return redirect(f"/?query={back_query}&mode={back_mode}")
    
@app.route("/upload-pdf", methods=["POST"])
def UploadPDF():
    """Handle PDF file upload and process it into chunks (Background Thread)"""
    import tempfile
    import threading
    from werkzeug.utils import secure_filename
    from ingestion.insert_pdf_chunks import insert_pdf
    
    if 'pdfFile' not in request.files:
        return {"success": False, "error": "No file provided"}, 400
    
    file = request.files['pdfFile']
    
    if file.filename == '':
        return {"success": False, "error": "No file selected"}, 400
    
    if not file.filename.lower().endswith('.pdf'):
        return {"success": False, "error": "Only PDF files are allowed"}, 400
    
    try:
        # Create a temporary file to save the PDF
        secure_name = secure_filename(file.filename)
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"upload_{secure_name}")
        
        # Save the uploaded file synchronously so the thread has access to it
        file.save(temp_path)
        
        # Define background task
        def process_background(path, filename):
            conn = None
            try:
                # New DB connection for this thread
                conn, cursor = _db()
                print(f"Starting background processing for {filename}...")
                success = insert_pdf(path, conn, cursor)
                
                # Cleanup
                if os.path.exists(path):
                    os.remove(path)
                
                cursor.close()
                conn.close()
                
                status = "SUCCESS" if success else "FAILED"
                print(f"Background processing finished for {filename}: {status}")
                
                # In a real app, we'd update a DB status here so the frontend can poll:
                # UPDATE uploads SET status='done' WHERE filename=...
                
            except Exception as e:
                import traceback
                print(f"❌ Background thread error for {filename}: {e}")
                traceback.print_exc()
                
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except:
                        pass
                if conn:
                    try:
                        conn.close()
                    except:
                        pass

        # Start Thread
        thread = threading.Thread(target=process_background, args=(temp_path, secure_name))
        thread.daemon = True # ensure thread doesn't block shutdown
        thread.start()
        
        # Return immediately
        return {"success": True, "message": "PDF processing started in background"}, 202
            
    except Exception as e:
        return {"success": False, "error": str(e)}, 500

@app.route("/generate", methods=["POST"])
def proxy_generate():
    try:
        data = request.get_json()
        resp = requests.post(f"{API_URL}/generate", json=data, timeout=30)
        return resp.json(), resp.status_code
    except requests.RequestException as e:
        return {"answer": f"Backend Error: {str(e)}"}, 500

@app.route("/api/quick-chat", methods=["POST"])
def quick_chat_proxy():
    """Simple proxy for the Global Chat widget to talk to Ollama"""
    
    data = request.json
    user_message = data.get("message", "")
    
    if not user_message:
        return {"error": "No message provided"}, 400

    # Configuration for Ollama
    OLLAMA_URL = "http://localhost:11434/api/generate"
    # Use same model as main app or a faster one
    MODEL = "qwen3:0.6b" 
    
    payload = {
        "model": MODEL,
        "prompt": user_message,
        "stream": False,
        "system": "You are a helpful, concise AI assistant."
    }
    
    try:
        # Forward request to Ollama
        resp = requests.post(OLLAMA_URL, json=payload, timeout=30)
        
        if resp.status_code == 200:
            ollama_data = resp.json()
            return {"reply": ollama_data.get("response", "")}, 200
        else:
            return {"error": f"Ollama Error: {resp.text}"}, 500
            
    except Exception as e:
        print(f"Global Chat Proxy Error: {e}")
        return {"error": "Could not connect to Ollama. Is it running?"}, 500

#  Run
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
