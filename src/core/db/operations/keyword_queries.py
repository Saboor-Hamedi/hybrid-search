import os
import sys

# Ensure path is set correctly
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Import necessary utility functions
import math
import os
import time

from utils.ColorScheme import ColorScheme

cs = ColorScheme()

def execute_keyword_query(query, cursor, limit):
    """
    Worker function: Executes the traditional PostgreSQL Full-Text Search (FTS) query.

    Returns: list of (doc_id, content, score, language, created_at)
    """
    start_time = time.time()

    # Execute the FTS query using ts_rank
    cursor.execute("""
        SELECT id, content, ts_rank(content_tsvector, plainto_tsquery('simple', %s)) AS score,
               language, created_at::text
        FROM document
        WHERE content_tsvector @@ plainto_tsquery('simple', %s)
        ORDER BY score DESC
        LIMIT %s
    """, (query, query, limit))

    rows = cursor.fetchall()

    # Normalize BM25/ts_rank scores according to HYBRID_BM25_NORM
    method = os.getenv("HYBRID_BM25_NORM", "max").strip().lower()
    scores = [float(row[2]) for row in rows]
    results = []
    if not rows:
        return [], {"keyword_count": 0}

    min_score = min(scores)
    max_score = max(scores)

    if method == "log":
        denom = math.log1p(max_score) if max_score > 0 else 1.0
        for row, raw in zip(rows, scores):
            norm = (math.log1p(raw) / denom) if max_score > 0 else 0.0
            results.append((row[0], row[1], float(norm), row[3] or "unknown", row[4]))
    elif method == "max":
        denom = max_score if max_score > 0 else 1.0
        for row, raw in zip(rows, scores):
            norm = (raw / denom) if denom > 0 else 0.0
            results.append((row[0], row[1], float(norm), row[3] or "unknown", row[4]))
    else:
        # min-max fallback
        score_range = max_score - min_score
        if score_range == 0:
            for row, raw in zip(rows, scores):
                results.append((row[0], row[1], 1.0 if raw > 0 else 0.0, row[3] or "unknown", row[4]))
        else:
            for row, raw in zip(rows, scores):
                norm_score = (raw - min_score) / score_range
                results.append((row[0], row[1], float(norm_score), row[3] or "unknown", row[4]))

    # Calculate time spent on the FTS query
    keyword_time_ms = (time.time() - start_time) * 1000

    # Return results and stats (only time and count)
    return results, {"keyword_count": len(results)}
    # stats = {
    #     "keyword_time_ms": round(keyword_time_ms, 2),
    #     "keyword_count": len(results),
    #}

    # return results, stats
