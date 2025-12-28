'''
 ! This is my Flask app.
'''
import logging
import os
import sys

import requests

#  Add project root so we can import db_connection
from db.db_connection import db_connection
from flask import Flask, redirect, render_template, request
from frontend.graphs.analyze import generate_query_graph

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
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
            "fusion_strategy": fusion_strategy
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

            # we calculate a test value to ensure the buttons render.
            if total_results > 0 and total_pages <= 1 and page_size > 0:
                # Calculate the correct total pages based on the results count

                test_total_pages = (total_results // page_size) + (1 if total_results % page_size != 0 else 0)

                # Use the calculated value if it's greater than 1
                if test_total_pages > 1:
                    total_pages = test_total_pages
                    print(f"DEBUG: Forcing total_pages to {total_pages} for front-end rendering test.")
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
                "router_choice": raw.get("metrics", {}).get("router_choice", "Hybrid")
            }
            graph_img = generate_query_graph(
                mode=mode,
                latency_ms=stats['query_time_ms'],
                results_count=total_results,
                semantic_count=stats.get('semantic_count', 0),
                bm25_count=stats.get('bm25_count', 0)
            )


        except requests.RequestException as e:
            results = []
            stats = {"error": str(e)}
            print("Backend error:", e)

    # pagination helpers
    prev_page = page - 1 if page > 1 else None
    next_page = page + 1 if page < total_pages else None

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
        use_ai=use_ai  # Pass to template
    )


# ------------------------------------------------------------------ #
#  /document/<id> – Wikipedia-style page
# ------------------------------------------------------------------ #
def _db():

    conn = db_connection()
    if not conn:
        raise RuntimeError("DB connection failed")
    return conn, conn.cursor()


@app.route("/document/<int:doc_id>")
def document_page(doc_id: int):
    conn, cursor = _db()

    # Retrieve back-link parameters from URL arguments
    back_query = request.args.get("q", "")
    back_mode = request.args.get("mode", "hybrid")

    try:
        # 1. Fetch document (include score if you have it)
        cursor.execute(
            """
            SELECT id, content, language, created_at
            FROM document
            WHERE id = %s
            """,
            (doc_id,),
        )
        row = cursor.fetchone()
        if not row:
            return render_template(
                "404.html",
                doc_id=doc_id,
                error=f"Document {doc_id} not found in the database."
            ), 404

        # 2. Build doc dict (safe defaults)
        doc = {
            "doc_id": row[0],
            "content": row[1] or "",
            "language": row[2] or "en",
            "created_at": row[3].strftime("%Y-%m-%d %H:%M") if row[3] else "unknown",
            "score": 0.0,
        }

        try:
            score = float(request.args.get("score", 0))
            doc["score"] = round(score, 4)
        except Exception as e:
            print("DB error:", e)
        # Optional component scores passed from search results
        def _get_float_arg(name, default=None):
            v = request.args.get(name)
            if v is None:
                return default
            try:
                return round(float(v), 4)
            except Exception:
                return default

        doc["semantic_score"] = _get_float_arg("semantic_score", None)
        doc["bm25_score"] = _get_float_arg("bm25_score", None)
        doc["semantic_weight"] = _get_float_arg("semantic_weight", None)
        doc["bm25_weight"] = _get_float_arg("bm25_weight", None)

        # If both component weights are present and > 0, this visit most likely
        # originated from a hybrid search — override the back_mode for display.
        try:
            sw = doc.get("semantic_weight")
            bw = doc.get("bm25_weight")
            if sw is not None and bw is not None:
                # treat small floats as truthy only if greater than 0
                if float(sw) > 0.0 and float(bw) > 0.0:
                    back_mode = "hybrid"
        except Exception:
            # Leave back_mode as-is on any parse error
            pass


        # 3. Related docs: prefer fetching similarity+component scores from backend
        related = []
        try:
            # Use a trimmed excerpt of the document as the query to find similar docs
            excerpt = (doc.get("content") or "").strip()[:512]
            payload = {"query": excerpt, "mode": back_mode or "hybrid", "page": 1, "page_size": 6}
            resp = requests.post(f"{API_URL}/search", json=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])
            for r in results:
                # skip the same document if present in results
                if int(r.get("doc_id") or 0) == int(doc_id):
                    continue
                related.append(
                    {
                        "doc_id": r.get("doc_id"),
                        "title": (r.get("content")[:60] + "...") if r.get("content") and len(r.get("content")) > 60 else (r.get("title") or r.get("content") or f"Document #{r.get('doc_id')}") ,
                        "language": r.get("language") or "en",
                        "created_at": (r.get("created_at") or "")[:8],
                        "score": r.get("score", 0.0),
                        "semantic_score": r.get("semantic_score"),
                        "bm25_score": r.get("bm25_score"),
                        "semantic_weight": r.get("semantic_weight"),
                        "bm25_weight": r.get("bm25_weight"),
                    }
                )
                if len(related) >= 5:
                    break
        except requests.RequestException:
            # fallback: simple DB-backed recent-same-language list (no scores)
            cursor.execute(
                """
                SELECT id, content, language, created_at
                FROM document
                WHERE language = %s AND id != %s
                ORDER BY created_at DESC
                LIMIT 5
                """,
                (doc["language"], doc_id),
            )
            related = [
                {
                    "doc_id": r[0],
                    "title": (r[1][:60] + "...") if len(r[1]) > 60 else r[1],
                    "language": r[2] or "en",
                    "created_at": r[3].strftime("%y-%m-%d") if r[3] else "unknown",
                    "score": 0.0 # placeholder score
                }
                for r in cursor.fetchall()
            ]


        # Display graphs

        return render_template(
            "document.html",
            doc=doc,
            related=related,
            back_query = back_query,
            back_mode = back_mode,
            query=back_query,  # For header search bar
            mode=back_mode     # For header mode selector
        )

    except Exception as e:
        print("DB error:", e)
        return render_template(
            "404.html",
            doc_id=doc_id,
            error=f"Database error: {str(e)}"
        ), 500
    finally:
        cursor.close()
        conn.close()

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
    try:
        r = requests.post(
            f"{API_URL}/documents/{doc_id}/update",
            json={"content": content, "language": language},
            timeout=20,
        )
        r.raise_for_status()
    except requests.RequestException as e:
        print("Update post error:", e)
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
                print(f"Background thread error for {filename}: {e}")
                if os.path.exists(path):
                    os.remove(path)
                if conn:
                    conn.close()

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

#  Run
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
