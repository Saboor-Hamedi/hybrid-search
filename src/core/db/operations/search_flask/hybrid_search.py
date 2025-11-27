from core.db.operations.search_queries import execute_vector_query

import core.utils.bm25_utils as bm25_utils
from core.utils.ColorScheme import ColorScheme
from core.utils.console_stats import display_search_stats
from core.utils.helper_functions import check_if_empty_input, measure_time
from core.utils.rich_console import display_in_table
from core.utils.text_properties import normalize_content

cs = ColorScheme()
TRASHOLD = 0.25  # Lowered from 0.4 for better recall
TOP_K = 100      # Increased from 50 for more candidates

def search_hybrid(
    query: str, conn, cursor, model, top_k=TOP_K, threshold=TRASHOLD
):
    if check_if_empty_input(query):
        print(f"{cs.RED}Input cannot be empty.{cs.RESET}")
        return []
    get_elapsed = measure_time()

    # Semantic Search
    sem_results = execute_vector_query(query, conn, cursor, model, top_k, threshold)
    # BM25 Search
    bm25_utils.update_bm25_index(cursor, normalize_content)
    if bm25_utils.bm25_index and bm25_utils.bm25_corpus:
        scores = bm25_utils.bm25_index.get_scores(normalize_content(query).split())
        bm25_results = [
            (doc_id, content, scores[i])
            for i, (doc_id, content) in enumerate(bm25_utils.bm25_corpus)
            if scores[i] > 0
        ]
    else:
        bm25_results = []

    # 3. Combine with Normalization
    # ---------------------------------------------------------
    # A. Normalize BM25 scores (Min-Max)
    if bm25_results:
        scores = [s for _, _, s in bm25_results]
        min_s, max_s = min(scores), max(scores)
        denom = max_s - min_s if max_s != min_s else 1.0
        
        # Replace raw score with normalized score in bm25_results
        # (doc_id, content, raw_score) -> (doc_id, content, norm_score)
        bm25_norm = []
        for doc_id, content, raw_score in bm25_results:
            norm_score = (raw_score - min_s) / denom if max_s != min_s else (1.0 if raw_score > 0 else 0.0)
            bm25_norm.append((doc_id, content, norm_score))
    else:
        bm25_norm = []

    # B. Weighted Combination
    # Default weight: 0.5 for each (or configurable)
    ALPHA = 0.5 
    
    result_map = {}
    
    # Add Semantic Scores (weighted)
    for r in sem_results:
        # r = (doc_id, content, score, language, created_at)
        doc_id = r[0]
        weighted_score = r[2] * (1 - ALPHA)
        result_map[doc_id] = {
            "data": r,
            "score": weighted_score
        }

    # Add BM25 Scores (weighted)
    for doc_id, content, score in bm25_norm:
        weighted_score = score * ALPHA
        if doc_id in result_map:
            result_map[doc_id]["score"] += weighted_score
        else:
            # For pure BM25 results, we need to construct the tuple structure
            # (doc_id, content, score, language, created_at)
            # We don't have language/created_at easily here, so use None
            result_map[doc_id] = {
                "data": (doc_id, content, 0.0, None, None), # 0.0 placeholder
                "score": weighted_score
            }

    # Reconstruct final list
    final_list = []
    for val in result_map.values():
        r = val["data"]
        final_score = val["score"]
        # Update the score in the tuple
        new_tuple = (r[0], r[1], final_score, r[3], r[4])
        final_list.append(new_tuple)

    final = sorted(final_list, key=lambda x: x[2], reverse=True)[:top_k]



    display_in_table(final, query=query, mode="hybrid")
    display_search_stats(sem_results, bm25_results, get_elapsed, mode="hybrid")
    
    # Return stats for API
    stats = {
        "sem_results": sem_results,
        "bm25_results": bm25_results,
    }
    
    return final, stats
