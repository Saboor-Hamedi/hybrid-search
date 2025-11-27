'''
 ! This is my Flask app.
'''
import logging
import os
import sys

import requests

#  Add project root so we can import db_connection
from db.db_connection import db_connection
from flask import Flask, render_template, request
from frontend.graphs.analyze import generate_query_graph

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "frontend", "templates")
STATIC_DIR = os.path.join(BASE_DIR, "frontend", "static")
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
API_URL = "http://127.0.0.1:8000"  # FastAPI backend


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
    page = 1
    page_size = 50
    total_pages = 0
    total_results = 0
    # Show graph for searchs
    graph_img = None

    input_source = request.form if request.method == "POST" else request.args
    

    # 1. Initialize/Retrieve Search Parameters
    query = input_source.get("query", "").strip()
    mode = input_source.get("mode", "hybrid")
    page = int(input_source.get("page", 1))
    page_size = int(input_source.get("page_size", 50))


    if query:
        payload = {
            "query": query,
            "page": page,
            "page_size": page_size,
            "mode": mode,
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
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        total_results=total_results,
        prev_page=prev_page,
        next_page=next_page,
        graph_img=graph_img

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


        # 3. Related docs (same language)
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
            back_mode = back_mode
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
#  Run
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
