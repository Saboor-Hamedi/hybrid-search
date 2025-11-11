import os
import sys

# Ensure path is set correctly
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Import necessary utility functions
from utils.ColorScheme import ColorScheme

cs = ColorScheme()

def execute_vector_query(query, conn, cursor, model, top_k, threshold):
    """
    Worker function: Executes the raw semantic (vector) search query against the database.

    This function handles model encoding and the PostgreSQL query execution.
    Returns: list of (doc_id, content, score, languages, created_at)
    """

    # 1. Model Encoding
    query_vec = model.encode(query).tolist()
    vec_str = f"[{','.join(map(str, query_vec))}]"

    # 2. Execute the semantic search
    cursor.execute(
        """
        SELECT d.id, d.content, (1 - (e.embedding <=> %s::vector)) AS similarity,
                d.languages, d.created_at
        FROM document d
        JOIN document_embedding e ON d.id = e.doc_id
        WHERE (1 - (e.embedding <=> %s::vector)) >= %s
        ORDER BY e.embedding <=> %s::vector DESC
        LIMIT %s
    """,
        (vec_str, vec_str, threshold, vec_str, top_k * 2),
    )

    rows = cursor.fetchall()

    return [(row[0], row[1], float(row[2]), row[3], row[4]) for row in rows]
