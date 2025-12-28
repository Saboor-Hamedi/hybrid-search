import os
from typing import List, Tuple, Dict, Any

from core.db.algorithms.RRFScoores import RRFScorer
from core.db.operations.search_queries import execute_vector_query
import core.utils.bm25_utils as bm25_utils
from core.utils.ColorScheme import ColorScheme
from core.utils.console_stats import display_search_stats
from core.utils.helper_functions import check_if_empty_input, measure_time
from core.utils.rich_console import display_in_table
from core.utils.text_properties import normalize_content

cs = ColorScheme()

def search_rrf(
    query: str, conn, cursor, model, top_k=100, k=60
) -> Tuple[List[Tuple], Dict[str, Any]]:
    """
    Executes a hybrid search using Reciprocal Rank Fusion (RRF).
    """
    if check_if_empty_input(query):
        return [], {}

    get_elapsed = measure_time()

    # 1. Semantic Search
    # We use a lower threshold or no threshold for RRF to get a decent candidate list for ranking
    sem_results = execute_vector_query(query, conn, cursor, model, top_k=top_k, threshold=0.1)

    # 2. BM25 Search
    bm25_utils.update_bm25_index(cursor, normalize_content)
    bm25_results = []
    if bm25_utils.bm25_index and bm25_utils.bm25_corpus:
        scores = bm25_utils.bm25_index.get_scores(normalize_content(query).split())
        for i, (doc_id, content) in enumerate(bm25_utils.bm25_corpus):
            raw = scores[i]
            if raw > 0:
                bm25_results.append((doc_id, content, raw))
        
        # Sort BM25 results by raw score to establish rank
        bm25_results.sort(key=lambda x: x[2], reverse=True)
        bm25_results = bm25_results[:top_k]

    # 3. Apply RRF Fusion
    scorer = RRFScorer(k=k)
    final, components = scorer.combine(sem_results, bm25_results, top_k=top_k)

    # 4. Display and Stats
    display_in_table(final, query=query, mode="rrf")
    # We can pass an empty third list or adapt display_search_stats if needed
    display_search_stats(sem_results, bm25_results, get_elapsed, mode="rrf (Reciprocal Rank Fusion)")

    stats = {
        "sem_results": sem_results,
        "bm25_results": bm25_results,
        "components": components,
        "k_constant": k,
        "search_type": "rrf"
    }

    return final, stats
