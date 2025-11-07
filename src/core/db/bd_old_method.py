import os
import sys

# Ensure the parent directory is in sys.path for relative imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from utils.ColorScheme import ColorScheme
from utils.helper_functions import check_if_empty_input, measure_time
from utils.languages import detect_language
from utils.text_properties import normalize_content

# REMOVED: BM25 utils import (no longer needed)
# import utils.bm25_utils as bm25_utils
from core.utils.rich_console import display_in_paragraph, display_in_table

cs = ColorScheme()

# Keep your existing constants
DEFAULT_TOP_K = 100
DEFAULT_THRESHOLD = 0.4
BM25_WEIGHT = 0.5  # We'll still use this for score fusion


def insert_document(content, conn, cursor, model, commit=True, silent=False):
    if check_if_empty_input(content):
        if not silent:
            print(f"{cs.RED}❌ Input cannot be empty.{cs.RESET}")
        return False
    get_elapsed = measure_time()
    nor_content = normalize_content(content)
    language = detect_language(nor_content)

    try:
        emb = model.encode(nor_content).tolist()
        cursor.execute(
            "INSERT INTO document (content, languages) VALUES (%s, %s) RETURNING id;",
            (nor_content, language),
        )
        result = cursor.fetchone()
        if result is None:
            if not silent:
                print(f"{cs.RED}❌ INSERT failed - no ID returned{cs.RESET}")
            return False

        doc_id = result[0]
        cursor.execute(
            "INSERT INTO document_embedding (doc_id, embedding) VALUES (%s, %s)",
            (doc_id, emb),
        )

        if commit:
            conn.commit()
            # REMOVED: bm25_utils.needs_update = True  → PostgreSQL handles FTS automatically!
            if not silent:
                print(
                    f"{cs.GREEN}✅ Inserted document (language: {language}). Time: {get_elapsed()} {cs.RESET}"
                )
        else:
            if not silent:
                print(
                    f"{cs.YELLOW}📝 Queued for batch (language: {language}). Time: {get_elapsed()} {cs.RESET}"
                )
        return True
    except Exception as e:
        print(f"{cs.RED}❌ Error after {get_elapsed()} Error: {e}{cs.RESET}")
        print(f"{cs.YELLOW}   Content: '{nor_content[:80]}...'{cs.RESET}")
        conn.rollback()
        return False


def _hybrid_search_query(query, conn, cursor, model, top_k, threshold, bm25_weight):
    """
    Performs hybrid search:
    - Semantic: PostgreSQL vector search (HNSW)
    - Keyword: PostgreSQL FTS (replaces in-memory BM25)
    Score fusion logic remains identical to your original.
    """
    nor_query = normalize_content(query)

    # 1. Semantic Search (PostgreSQL - unchanged)
    semantic_results = _query(query, conn, cursor, model, top_k, threshold)

    # 2. NEW: Keyword Search via PostgreSQL FTS (replaces bm25_utils)
    cursor.execute("""
        SELECT id, content, ts_rank(content_tsvector, plainto_tsquery('simple', %s)) AS bm25_score,
               languages, created_at
        FROM document
        WHERE content_tsvector @@ plainto_tsquery('simple', %s)
        ORDER BY bm25_score DESC
    """, (nor_query, nor_query))

    raw_bm25_results = cursor.fetchall()
    bm25_results = [
        (row[0], row[1], float(row[2]), row[3], row[4])
        for row in raw_bm25_results
    ]
    # Filter out zero-score results (like your original BM25)
    bm25_results = [r for r in bm25_results if r[2] > 0]

    # 3. FUSION LOGIC: IDENTICAL to your original (preserves your tuning!)
    if not bm25_results:
        results = semantic_results
    else:
        combined_results = {}

        max_semantic = (
            max([r[2] for r in semantic_results] + [0.01]) if semantic_results else 0.01
        )
        max_bm25 = max([r[2] for r in bm25_results] + [0.01]) if bm25_results else 0.01
        bm25_term_weight = 1 - bm25_weight

        # Add semantic results
        for doc_id, content, score, lang, created in semantic_results or []:
            combined_results[doc_id] = (
                content,
                score / max_semantic * bm25_weight,
                lang,
                created,
            )

        # Add BM25 results
        for doc_id, content, score, lang, created in bm25_results or []:
            normalized_bm25_score = score / max_bm25 * bm25_term_weight if max_bm25 > 0 else 0
            if doc_id in combined_results:
                current_content, current_score, current_lang, current_created = combined_results[doc_id]
                combined_results[doc_id] = (
                    current_content,
                    current_score + normalized_bm25_score,
                    current_lang,
                    current_created,
                )
            else:
                combined_results[doc_id] = (
                    content,
                    normalized_bm25_score,
                    lang,
                    created,
                )

        results = [
            (doc_id, content, score, lang, created)
            for doc_id, (content, score, lang, created) in combined_results.items()
        ]
        results.sort(key=lambda x: x[2], reverse=True)

    # Return in same format as before: (combined, semantic, bm25)
    # Note: bm25_results now includes lang/created (unlike old version), but your UI handles None
    return results, semantic_results, [(r[0], r[1], r[2]) for r in bm25_results]


def search(
    query,
    conn,
    cursor,
    model,
    top_k=DEFAULT_TOP_K,
    threshold=DEFAULT_THRESHOLD,
    bm25_weight=BM25_WEIGHT,
):
    if check_if_empty_input(query):
        print(f"{cs.RED}Input cannot be empty.{cs.RESET}")
        return []

    get_elapsed = measure_time()

    try:
        results, semantic_results, bm25_results = _hybrid_search_query(
            query, conn, cursor, model, top_k, threshold, bm25_weight
        )
    except Exception as e:
        print(f"{cs.RED}Error during search: {e}{cs.RESET}")
        return []

    if not results:
        print(f"{cs.RED}No relevant results found.{cs.RESET}")
        return []

    display_in_table(results[:top_k], query=query)
    _search_stats(semantic_results, bm25_results, get_elapsed)
    return results[:top_k]


def paragraph_search(
    query,
    conn,
    cursor,
    model,
    top_k=DEFAULT_TOP_K,
    threshold=DEFAULT_THRESHOLD,
    bm25_weight=BM25_WEIGHT,
):
    if check_if_empty_input(query):
        print(f"{cs.RED}Input cannot be empty.{cs.RESET}")
        return []

    get_elapsed = measure_time()

    try:
        results, semantic_results, bm25_results = _hybrid_search_query(
            query, conn, cursor, model, top_k, threshold, bm25_weight
        )
    except Exception as e:
        print(f"{cs.RED}Error during search: {e}{cs.RESET}")
        return []

    if not results:
        print(f"{cs.RED}No relevant results found.{cs.RESET}")
        return []

    display_in_paragraph(results[:top_k], query=query)
    _search_stats(semantic_results, bm25_results, get_elapsed)
    return results[:top_k]


def _search_stats(semantic_results, bm25_results, get_elapsed):
    print(f"{cs.GREEN}Semantic results: {len(semantic_results)} documents{cs.RESET}")
    if bm25_results:
        print(f"{cs.GREEN}BM25 results: {len(bm25_results)} documents with score > 0{cs.RESET}")
    print(f"{cs.OKBLUE}Search complete. Time: {get_elapsed()} {cs.RESET}")


def _query(query, conn, cursor, model, top_k, threshold):
    """Execute the search query and return results."""
    query_vec = model.encode(query).tolist()
    vec_str = f"[{','.join(map(str, query_vec))}]"

    cursor.execute(
        """
        SELECT d.id, d.content, (1 - (e.embedding <=> %s::vector)) AS similarity,
               d.languages, d.created_at
        FROM document d
        JOIN document_embedding e ON d.id = e.doc_id
        WHERE (1 - (e.embedding <=> %s::vector)) >= %s
        ORDER BY e.embedding <=> %s::vector
        LIMIT %s
        """,
        (vec_str, vec_str, threshold, vec_str, top_k * 2),
    )

    rows = cursor.fetchall()
    return [(row[0], row[1], float(row[2]), row[3], row[4]) for row in rows]
