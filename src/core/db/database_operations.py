import os
import sys
import time

# Ensure the parent directory is in sys.path for relative imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
# from utils.bm25_utils import update_bm25_index, bm25_index, bm25_corpus
import utils.bm25_utils as bm25_utils
from utils.ColorScheme import ColorScheme
from utils.helper_functions import check_if_empty_input, measure_time
from utils.languages import detect_language
from utils.text_properties import normalize_content

from core.utils.rich_console import display_in_paragraph, display_in_table

cs = ColorScheme()


# call the ColorScheme with re here
DEFAULT_TOP_K = 100
DEFAULT_THRESHOLD = 0.4
BM25_WEIGHT = 0.5


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
        # cursor.execute(
        #     "INSERT INTO document (content, languages) VALUES (%s, %s) RETURNING id;",
        #     (nor_content, language),
        # )
        cursor.execute(
    "INSERT INTO document (content, languages, content_tsvector) VALUES (%s, %s, to_tsvector('simple', %s)) RETURNING id;",
    (nor_content, language, nor_content),
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

        # CONDITIONAL COMMIT

        if commit:
            conn.commit()
            bm25_utils.needs_update = True
            # bm25_utils.update_bm25_index(cursor, normalize_content)  # All update BM25 index
            if not silent:
                print(
                    f"{cs.GREEN}✅ Inserted document (language: {language}). Time: {get_elapsed()} {cs.RESET}"
                )
        else:
            if not silent:
                # SILENT MODE: Don't print anything for batch operationss
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
    Performs the core hybrid search logic (Semantic + BM25 combination).
    Returns (combined_results, semantic_results, bm25_results)
    """
    nor_query = normalize_content(query)
    get_elapsed = measure_time()

    stats = {} # New stats dictionary

    sem_search = time.time()

    # 1. Semantic Search (PostgreSQL)
    semantic_results = _query(query, conn, cursor, model, top_k, threshold)

    stats['semantic_time_ms'] =(time.time() - sem_search) * 1000
    stats['semantic_count'] = len(semantic_results)

    # Update mb25 the show steps
    bm25_update_start = time.time()
    # 2. Update bm25
    bm25_utils.update_bm25_index(cursor, normalize_content)
    bm25_update_get_elapsed = time.time() - bm25_update_start

    if bm25_utils.bm25_index is None or not bm25_utils.bm25_corpus:
        # Fallback to pure semantic search result
        results = semantic_results
        bm25_results = []
        stats['bm25_time_ms'] = bm25_update_get_elapsed * 1000
        stats['bm25_count'] = 0
    else:
        # Get BM25 resutls
        bm25_scores = bm25_utils.bm25_index.get_scores(nor_query.split())
        bm25_results = [
            (doc_id, content, bm25_scores[i])
            for i, (doc_id, content) in enumerate(bm25_utils.bm25_corpus)
        ]
        bm25_results = [r for r in bm25_results if r[2] > 0]

        # Combine scores
        combined_results = {}

        # Calculate max scores for normalization

        max_semantic = (
            max([r[2] for r in semantic_results ] + [0.01]) if semantic_results  else 0.01
        )
        max_bm25 = max([r[2] for r in bm25_results] + [0.01]) if bm25_results else 0.01
        # Determine BM25 term weight
        bm25_term_weight = 1 - bm25_weight
        # Add semantic results

        for doc_id, content, score, lang, created in semantic_results or []:
            combined_results[doc_id] = (
                content,
                score / max_semantic * bm25_weight,  # Normalized semantic score
                lang,
                created,
            )
            # Add BM25 results
        for doc_id, content, score in bm25_results or []:
            normalized_bm25_score = (
                score / max_bm25 * bm25_term_weight if max_bm25 > 0 else 0
            )
            if doc_id in combined_results:
                current_content, current_score, current_lang, current_created = (
                    combined_results[doc_id]
                )
                # Combine scores
                combined_results[doc_id] = (
                    current_content,
                    current_score + normalized_bm25_score,
                    current_lang,
                    current_created,
                )
            else:
                # BM25 result not found in semantic results
                # For simplicity and consistency with the original code, use None for missing info.
                combined_results[doc_id] = (
                    content,
                    normalized_bm25_score,
                    None,
                    None,
                )
        bm25_total_time = (time.time() - bm25_update_start) * 1000
        stats['bm25_time_ms'] = bm25_total_time
        stats['bm25_count'] = len(bm25_results)
        # Final list of combined results
        results = [
            (doc_id, content, score, lang, created)
            for doc_id, (content, score, lang, created) in combined_results.items()

        ]
        results.sort(key=lambda x: x[2], reverse=True)
    # return results, semantic_results, bm25_results
    return results, semantic_results, bm25_results, stats


# Search function


def search(
    query,
    conn,
    cursor,
    model,
    top_k=DEFAULT_TOP_K,
    threshold=DEFAULT_THRESHOLD,
    bm25_weight=BM25_WEIGHT,
):
    """
    Performs a hybrid search combining Semantic (Vector) and BM25 (Keyword) search.
    """
    if check_if_empty_input(query):
        print(f"{cs.RED}Input cannot be empty.{cs.RESET}")
        return []

    get_elapsed = measure_time()

    try:

        results, semantic_results, bm25_results, hybrid_stats =  _hybrid_search_query(
            query, conn, cursor, model, top_k, threshold, bm25_weight
        )

    except Exception as e:
        print(f"{cs.RED}Error during search: {e}{cs.RESET}")
        return [],{}

    if not results:
        print(f"{cs.RED}No relevant results found.{cs.RESET}")
        return [],{}
    # Display results
    display_in_table(results[:top_k], query=query)

    # Clean output
    _search_stats(semantic_results, bm25_results, get_elapsed)

    return results[:top_k],hybrid_stats


def paragraph_search(
    query,
    conn,
    cursor,
    model,
    top_k=DEFAULT_TOP_K,
    threshold=DEFAULT_THRESHOLD,
    bm25_weight=BM25_WEIGHT,
):
    """
    Performs a hybrid search combining Semantic (Vector) and BM25 (Keyword) search.
    """
    if check_if_empty_input(query):
        print(f"{cs.RED}Input cannot be empty.{cs.RESET}")
        return [],{}

    get_elapsed = measure_time()

    try:
        results, semantic_results, bm25_results, hybrid_stats= _hybrid_search_query(
             query, conn, cursor, model, top_k, threshold, bm25_weight
        )


    except Exception as e:
        print(f"{cs.RED}Error during search: {e}{cs.RESET}")
        return [], {}

    if not results:
        print(f"{cs.RED}No relevant results found.{cs.RESET}")
        return []
    # Display results
    display_in_paragraph(results[:top_k], query=query)

    # Clean output
    _search_stats(semantic_results, bm25_results, get_elapsed)

    return results[:top_k], hybrid_stats

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
        ORDER BY e.embedding <=> %s::vector DESC
        LIMIT %s
    """,
        (vec_str, vec_str, threshold, vec_str, top_k * 2),
    )

    rows = cursor.fetchall()
    return [(row[0], row[1], float(row[2]), row[3], row[4]) for row in rows]


