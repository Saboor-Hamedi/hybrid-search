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
from flask import Flask, Response, redirect, render_template, request
from frontend.graphs.analyze import generate_query_graph

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "frontend", "templates")
STATIC_DIR = os.path.join(BASE_DIR, "frontend", "static")
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
API_URL = "http://127.0.0.1:8000"  # FastAPI backend
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024 # 100MB limit for PDFs


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


    # 1. Initialize/Retrieve Search Parameters (Support both short & long keys)
    query = input_source.get("q", input_source.get("query", "")).strip()
    mode = input_source.get("mode", "hybrid")
    fusion_strategy = input_source.get("fusion", input_source.get("fusion_strategy", "linear"))
    
    # Flags (LTR & AI)
    use_ltr = input_source.get("ltr") == "1" or input_source.get("use_ltr") in ["true", "on"]
    ai_val = input_source.get("ai")
    if ai_val is not None:
        use_ai = ai_val == "1"
    else:
        use_ai = input_source.get("use_ai", "on") in ["true", "on"]

    alpha = input_source.get("alpha")
    if alpha:
        try:
            alpha = float(alpha) / 100.0
        except:
            alpha = None
            
    try:
        page_val = input_source.get("p", input_source.get("page", 1))
        page = int(page_val)
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


#  /document/<id> – View Single Document
@app.route("/document/<int:doc_id>")
def document_page(doc_id: int):
    back_query = request.args.get("q", "")
    back_mode = request.args.get("mode", "hybrid")
    conn, cursor = _db()
    try:
        cursor.execute("SELECT id, content, language, created_at FROM document WHERE id = %s", (doc_id,))
        row = cursor.fetchone()
        if not row:
            return render_template("404.html"), 404
        
        doc = {
            "doc_id": row[0],
            "content": row[1] or "",
            "content_highlighted": highlight_text(row[1] or "", back_query),
            "language": (row[2] or "en").upper(),
            "created_at": row[3].strftime("%Y-%m-%d %H:%M") if row[3] else "unknown",
            "score": 1.0 # Default score for direct view
        }
        
        # Use index.html to render, which will use chat_base.html
        return render_template(
            "index.html",
            results=[doc],
            query=back_query,
            mode=back_mode,
            stats={"returned": 1, "query_time_ms": 0}
        )
    except Exception as e:
        print(f"Document view error: {e}")
        return str(e), 500
    finally:
        cursor.close()
        conn.close()

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
        conn.close()


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
    
    # AJAX Detection
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or \
              request.args.get('ajax') == '1' or \
              request.form.get('ajax') == '1'
              
    try:
        r = requests.post(
            f"{API_URL}/documents/{doc_id}/update",
            json={"content": content, "language": language},
            timeout=20,
        )
        r.raise_for_status()
        
        if is_ajax:
            return {"success": True, "doc_id": doc_id, "message": "Document updated successfully."}
            
    except requests.RequestException as e:
        print("Update post error:", e)
        if is_ajax:
            return {"success": False, "error": str(e)}, 500
    
    if redirect_to == "home":
        return redirect(f"/?query={back_query}&mode={back_mode}")
    return redirect(f"/document/{doc_id}?q={back_query}&mode={back_mode}")

@app.post("/document/new_post")
def new_post():
    back_query = request.form.get("q", "")
    back_mode = request.form.get("mode", "hybrid")
    content = request.form.get("content", "")
    language = request.form.get("language", "en")
    
    # AJAX Detection
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or \
              request.args.get('ajax') == '1' or \
              request.form.get('ajax') == '1'
              
    try:
        r = requests.post(
            f"{API_URL}/documents/insert",
            json={"content": content, "language": language},
            timeout=20,
        )
        r.raise_for_status()
        data = r.json()
        doc_id = data.get("doc_id")
        
        if is_ajax:
            return {"success": True, "doc_id": doc_id, "message": "Document indexed successfully."}
            
        if doc_id:
            return redirect(f"/document/{doc_id}?q={back_query}&mode={back_mode}")
    except requests.RequestException as e:
        print("New post error:", e)
        if is_ajax:
            return {"success": False, "error": str(e)}, 500
            
    return redirect(f"/?query={back_query}&mode={back_mode}")

@app.post("/document/<int:doc_id>/delete_post")
def delete_post(doc_id: int):
    back_query = request.form.get("q", "")
    back_mode = request.form.get("mode", "hybrid")
    
    # AJAX Detection
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or \
              request.args.get('ajax') == '1' or \
              request.form.get('ajax') == '1'
              
    try:
        r = requests.delete(f"{API_URL}/documents/{doc_id}", timeout=15)
        r.raise_for_status()
        
        if is_ajax:
            return {"success": True, "doc_id": doc_id, "message": "Document deleted successfully."}
            
    except requests.RequestException as e:
        print("Delete post error:", e)
        if is_ajax:
            return {"success": False, "error": str(e)}, 500
            
    return redirect(f"/?query={back_query}&mode={back_mode}")
    
@app.route("/upload-pdf", methods=["POST"])
def UploadPDF():
    """Proxy PDF upload to FastAPI for processing"""
    if 'pdfFile' not in request.files:
        return {"success": False, "error": "No file provided"}, 400
    
    file = request.files['pdfFile']
    
    if file.filename == '':
        return {"success": False, "error": "No file selected"}, 400
    
    try:
        # Prepare file for requests forwarding
        files = {'file': (file.filename, file.stream, 'application/pdf')}
        # Using longer timeout for batch uploads to avoid connection drops
        resp = requests.post(f"{API_URL}/upload-pdf", files=files, timeout=300)
        
        if resp.status_code == 200 or resp.status_code == 201 or resp.status_code == 202:
            return resp.json(), 200
        else:
            return {"success": False, "error": f"Backend Error: {resp.status_code}"}, 500
            
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "FastAPI Server unreachable (Connection Reset)"}, 500
    except Exception as e:
        return {"success": False, "error": str(e)}, 500

# --------------------------------------------------------------------- #
# System Stats & Reset Proxy
# --------------------------------------------------------------------- #
@app.route("/api/stats", methods=["GET"])
def proxy_stats():
    try:
        resp = requests.get(f"{API_URL}/api/system/stats", timeout=10)
        return resp.json(), resp.status_code
    except Exception as e:
        return {"error": str(e)}, 500

@app.post("/api/stop-indexing")
def proxy_stop_indexing():
    try:
        resp = requests.post(f"{API_URL}/api/system/stop-indexing", timeout=10)
        return resp.json(), resp.status_code
    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/api/reset", methods=["POST"])
def proxy_reset():
    try:
        resp = requests.post(f"{API_URL}/api/system/reset", timeout=30)
        return resp.json(), resp.status_code
    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/generate", methods=["POST"])
def proxy_generate():
    """Classic non-streaming proxy."""
    try:
        data = request.get_json()
        resp = requests.post(f"{API_URL}/generate", json=data, timeout=30)
        return resp.json(), resp.status_code
    except requests.RequestException as e:
        return {"answer": f"Backend Error: {str(e)}"}, 500

@app.route("/generate-stream", methods=["POST"])
def proxy_generate_stream():
    """Streaming proxy using Response to yield tokens."""
    try:
        data = request.get_json()
        def generate():
            # Set stream=True to process chunks as they arrive from FastAPI
            with requests.post(f"{API_URL}/generate-stream", json=data, stream=True, timeout=60) as r:
                for chunk in r.iter_content(chunk_size=None):
                    if chunk:
                        yield chunk

        return Response(generate(), mimetype="text/event-stream")
    except Exception as e:
        return str(e), 500


@app.route("/api/quick-chat", methods=["POST"])
def quick_chat_proxy():
    """Proxy for Global Chat using standardized MultiAIManager logic"""
    try:
        data = request.get_json()
        user_message = data.get("message", "")
        provider = data.get("provider", "ollama")
        model = data.get("model", "qwen2.5:0.5b")
        api_key = data.get("api_key", "")
        base_url = data.get("base_url", "http://localhost:11434")

        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        from ai.MultiAIManager import MultiAIManager
        
        client = MultiAIManager.create_client(provider_name=provider, api_key=api_key, model=model, base_url=base_url)
        if not client: return {"error": f"AI Provider '{provider}' not available."}, 500
        
        response = client.generate_response(prompt=user_message, system_instruction="You are a helpful and concise AI assistant.")
        return {"reply": response}, 200
    except Exception as e:
        return {"error": f"AI Service error: {str(e)}"}, 500

@app.route("/api/quick-chat-stream", methods=["POST"])
def quick_chat_stream():
    """Streaming Version of Global Chat for real-time responsiveness."""
    try:
        data = request.get_json()
        user_message = data.get("message", "")
        provider = data.get("provider", "ollama")
        model = data.get("model", "qwen2.5:0.5b")
        api_key = data.get("api_key", "")
        base_url = data.get("base_url", "http://localhost:11434")

        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        from ai.MultiAIManager import MultiAIManager
        
        client = MultiAIManager.create_client(provider_name=provider, api_key=api_key, model=model, base_url=base_url)
        if not client: return str(f"Error: {provider} not found."), 500

        def stream_generator():
            try:
                for chunk in client.generate_stream(user_message, system_instruction="You are a helpful and concise AI assistant."):
                    if chunk:
                        yield chunk
            except Exception as e:
                yield f"\n[Streaming Error: {str(e)}]"

        return Response(stream_generator(), mimetype="text/event-stream")
    except Exception as e:
        return str(e), 500


#  Run
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
