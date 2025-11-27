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

# def execute_vector_query(query, conn, cursor, model, top_k, threshold):
#     """
#     * Worker function: Executes the raw semantic (vector) search query against the database.

#     * This function handles model encoding and the PostgreSQL query execution.
#     * Returns: list of (doc_id, content, score, languages, created_at)
#     """

#     # 1. Model Encoding
#     query_vec = model.encode(query).tolist()
#     clean_vec = []
#     for val in query_vec:
#         if math.isnan(val) or math.isinf(val):
#             clean_vec.append(0.0)
#         else:
#             clean_vec.append(val)
#     vec_str = f"[{','.join(map(str, clean_vec))}]"


#     cursor.execute("""
#             SELECT d.id, d.content, (1 - (e.embedding <=> %s::vector)) AS similarity,
#                    d.language, d.created_at
#             FROM document d
#             JOIN document_embedding e ON d.id = e.doc_id
#             WHERE (1 - (e.embedding <=> %s::vector)) >= %s
#             ORDER BY similarity DESC
#             LIMIT %s
#     """, (vec_str, vec_str, threshold, top_k * 2))

#     rows = cursor.fetchall()
#     results = []
#     for row in rows:
#             doc_id = row[0]
#             content = row[1] or ""
#             similarity = float(row[2]) if row[2] is not None else 0.0
#             language = row[3] or "en"
#             created_at = row[4].strftime("%Y-%m-%d %H:%M") if row[4] else "unknown"
#             results.append((doc_id, content, similarity, language, created_at))
#     return results


def execute_vector_query(query, conn, cursor, model, top_k, threshold):
    """
    * Worker function: Executes the raw semantic (vector) search query against the database.
    * This function handles model encoding and the PostgreSQL query execution.
    * Returns: list of (doc_id, content, score, languages, created_at)
    """
    
    try:
        # 1. Model Encoding
        query_vec = model.encode(query)
        
        # 2. Check for Model Issues
        if query_vec is None or len(query_vec) == 0:
            print(f"{cs.RED}Error: Model generated empty vector{cs.RESET}")
            return []

        # 3. Convert to list and clean NaN/Inf values
        vec_list = query_vec.tolist()
        clean_vec = []
        for val in vec_list:
            if math.isnan(val) or math.isinf(val):
                clean_vec.append(0.0)
            else:
                clean_vec.append(float(val))
        
        # 4. Format vector as string for pgvector (PostgreSQL array format)
        vec_str = f"[{','.join(map(str, clean_vec))}]"
        
        # 5. Execute SQL query
        # Note: We use the same vector string for both similarity calculation and ordering
        sql = """
            SELECT 
                d.id, 
                d.content, 
                (1 - (e.embedding <=> %s::vector)) AS similarity,
                d.language, 
                d.created_at
            FROM document d
            INNER JOIN document_embedding e ON d.id = e.doc_id
            WHERE (1 - (e.embedding <=> %s::vector)) >= %s
            ORDER BY similarity DESC
            LIMIT %s
        """
        
        cursor.execute(sql, (vec_str, vec_str, threshold, top_k * 2))
        rows = cursor.fetchall()
        
        # 6. Process results
        results = []
        print(f"\n{cs.CYAN}--- Debug: Raw Top Match Scores for '{query}' ---{cs.RESET}")
        
        for idx, row in enumerate(rows):
            doc_id = row[0]
            content = row[1] or ""
            similarity = float(row[2]) if row[2] is not None else 0.0
            language = row[3] or "en"
            created_at = row[4].strftime("%Y-%m-%d %H:%M") if row[4] else "unknown"
            
            # DEBUG PRINT: Show top 3 results
            if idx < 3: 
                preview = content[:50].replace('\n', ' ')
                print(f"{cs.GREEN}ID: {doc_id} | Score: {similarity:.4f} | Preview: {preview}...{cs.RESET}")
            
            results.append((doc_id, content, similarity, language, created_at))
        
        print(f"{cs.YELLOW}Total semantic results: {len(results)}{cs.RESET}\n")
        return results
        
    except Exception as e:
        print(f"{cs.RED}Error in execute_vector_query: {str(e)}{cs.RESET}")
        import traceback
        traceback.print_exc()
        return []


def execute_bm25_query(query, cursor, top_k):
    """
    * Worker function: Executes the raw BM25 (keyword) search query against the database.
    * Returns: list of (doc_id, content, score, languages, created_at)
    """
    cursor.execute("""
        SELECT d.id, d.content,
               ts_rank(to_tsvector('english', d.content), plainto_tsquery('english', %s)) AS rank,
               d.language, d.created_at
        FROM document d
        WHERE to_tsvector('english', d.content) @@ plainto_tsquery('english', %s)
        ORDER BY rank DESC
        LIMIT %s
    """, (query, query, top_k))

    rows = cursor.fetchall()
    results = []
    for row in rows:
        doc_id = row[0]
        content = row[1] or ""
        rank = float(row[2]) if row[2] is not None else 0.0
        language = row[3] or "en"
        created_at = row[4].strftime("%Y-%m-%d %H:%M") if row[4] else "unknown"
        results.append((doc_id, content, rank, language, created_at))
    
    return results