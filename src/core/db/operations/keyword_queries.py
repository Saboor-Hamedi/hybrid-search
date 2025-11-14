import os
import sys

# Ensure path is set correctly
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Import necessary utility functions
import time

from utils.ColorScheme import ColorScheme

cs = ColorScheme()

def execute_keyword_query(query, cursor, limit, offset):
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
        LIMIT %s OFFSET %s
    """, (query, query, limit, offset))

    rows = cursor.fetchall()

    # Format the results
    results = [
        (row[0], row[1], float(row[2]), row[3] or "unknown", row[4])
        for row in rows
    ]

    # Calculate time spent on the FTS query
    keyword_time_ms = (time.time() - start_time) * 1000

    # Return results and stats (only time and count)
    stats = {
        "keyword_time_ms": round(keyword_time_ms, 2),
        "keyword_count": len(results),
    }

    return results, stats
