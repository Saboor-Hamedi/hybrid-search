"""
    :NOTE

    * Description:
        ! this files is used to query the database for semantic search

"""



import math
import os
import sys

# Ensure path is set correctly
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Import necessary utility functions
from core.utils.ColorScheme import ColorScheme

cs = ColorScheme()

def execute_vector_query(query, conn, cursor, model, top_k, threshold):
    """
    * Worker function: Executes the raw semantic (vector) search query against the database.

    * This function handles model encoding and the PostgreSQL query execution.
    * Returns: list of (doc_id, content, score, languages, created_at)
    """

    # 1. Model Encoding
    query_vec = model.encode(query).tolist()
    clean_vec = []
    for val in query_vec:
        if math.isnan(val) or math.isinf(val):
            clean_vec.append(0.0)
        else:
            clean_vec.append(val)
    vec_str = f"[{','.join(map(str, clean_vec))}]"


    cursor.execute("""
            SELECT d.id, d.content, (1 - (e.embedding <=> %s::vector)) AS similarity,
                   d.language, d.created_at
            FROM document d
            JOIN document_embedding e ON d.id = e.doc_id
            WHERE (1 - (e.embedding <=> %s::vector)) >= %s
            ORDER BY similarity DESC
            LIMIT %s
    """, (vec_str, vec_str, threshold, top_k * 2))

    rows = cursor.fetchall()
    results = []
    for row in rows:
            doc_id = row[0]
            content = row[1] or ""
            similarity = float(row[2]) if row[2] is not None else 0.0
            language = row[3] or "en"
            created_at = row[4].strftime("%Y-%m-%d %H:%M") if row[4] else "unknown"
            results.append((doc_id, content, similarity, language, created_at))
    return results


