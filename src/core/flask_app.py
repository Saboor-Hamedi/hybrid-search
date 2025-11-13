'''
 ! This is my Flask app.
'''
import os
import sys

import requests
from flask import Flask, render_template, request, url_for

#  Add project root so we can import db_connection
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR,  "frontend", "templates")
from db.db_connection import db_connection

app = Flask(__name__, template_folder=TEMPLATE_DIR)
API_URL = "http://127.0.0.1:8000"          # FastAPI backend


#  Helper: highlight query words
def highlight_text(text: str, query: str) -> str:
    if not query or not text:
        return text
    import re
    terms = re.escape(query).split()
    pattern = "|".join(terms)
    return re.sub(f"({pattern})", r"<mark>\1</mark>", text, flags=re.IGNORECASE)


# ------------------------------------------------------------------ #
#  / – search page
# ------------------------------------------------------------------ #
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

    if request.method == "POST":
        query = request.form.get("query", "").strip()
        mode = request.form.get("mode", "hybrid")
        page = int(request.form.get("page", 1))
        page_size = int(request.form.get("page_size", 50))

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

            # ----- stats -----
            raw = data.get("stats", {})
            stats = {
                "query_time_ms": round(raw.get("query_time_ms", 0), 2),
                "semantic_count": raw.get("semantic_count", 0),
                "bm25_count": raw.get("bm25_count", 0),
                "returned": raw.get("returned", 0),
            }

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
    )


# ------------------------------------------------------------------ #
#  /document/<id> – Wikipedia-style page
# ------------------------------------------------------------------ #
def _db():
    """Return (conn, cursor) – same function you use in FastAPI."""
    conn = db_connection()
    if not conn:
        raise RuntimeError("DB connection failed")
    return conn, conn.cursor()


@app.route("/document/<int:doc_id>")
def document_page(doc_id: int):
    conn, cursor = _db()
    try:
        # 1. Fetch document (include score if you have it)
        cursor.execute(
            """
            SELECT id, content, languages, created_at
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
            "language": row[2] or "unknown",
            "created_at": (
                row[3].strftime("%Y-%m-%d %H:%M") if row[3] else "unknown"
            ),
            # "score": float(row[4]) if row[4] is not None else 0.0,
        }

        # 3. Related docs (same language)
        cursor.execute(
            """
            SELECT id, content, languages, created_at
            FROM document
            WHERE languages = %s AND id != %s
            ORDER BY created_at DESC
            LIMIT 5
            """,
            (doc["language"], doc_id),
        )
        related = [
            {
                "doc_id": r[0],
                "title": (r[1][:60] + "...") if len(r[1]) > 60 else r[1],
                "language": r[2] or "unknown",
                "created_at": r[3].strftime("%Y-%m-%d") if r[3] else "unknown",
            }
            for r in cursor.fetchall()
        ]

        back_query = request.args.get("q", "")
        back_mode = request.args.get("mode", "hybrid")

        return render_template(
            "document.html",
            doc=doc,
            related=related,
            back_query=back_query,
            back_mode=back_mode,
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

# ------------------------------------------------------------------ #
#  Run
# ------------------------------------------------------------------ #
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
