import os
import sys
import time

# Ensure the parent directory is in sys.path for relative imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
# from utils.bm25_utils import update_bm25_index, bm25_index, bm25_corpus
import utils.bm25_utils as bm25_utils
from utils.ColorScheme import ColorScheme
from utils.helper_functions import check_if_empty_input, measure_time
from utils.text_properties import normalize_content

from core.utils.console_stats import display_search_stats
from core.utils.rich_console import display_in_paragraph, display_in_table

from .search_queries import execute_vector_query

cs = ColorScheme()


# call the ColorScheme with re here
DEFAULT_TOP_K = 100
DEFAULT_THRESHOLD = 0.4
BM25_WEIGHT = 0.5


def _hybrid_search_query(query, conn, cursor, model, top_k, threshold, bm25_weight):
    """
    Performs the core hybrid search logic (Semantic + BM25 combination).
    Returns (combined_results, semantic_results, bm25_results)
    """
    nor_query = normalize_content(query)

    stats = {} # New stats dictionary

    sem_search = time.time()


    # 1. Semantic Search (PostgreSQL)

    semantic_results = execute_vector_query(query, conn, cursor, model, top_k, threshold)



    stats['semantic_time_ms'] = (time.time() - sem_search) * 1000
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
    display_search_stats(semantic_results, bm25_results, get_elapsed)

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
    display_search_stats(semantic_results, bm25_results, get_elapsed)

    return results[:top_k], hybrid_stats



