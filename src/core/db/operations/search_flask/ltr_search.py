import os
from typing import List, Tuple, Dict, Any

from core.db.operations.search_flask.HybridScorer import HybridScorer
from core.db.operations.search_flask.LTRScorer import LTRScorer
from core.db.operations.search_queries import execute_vector_query
import core.utils.bm25_utils as bm25_utils
from core.utils.ColorScheme import ColorScheme
from core.utils.console_stats import display_search_stats
from core.utils.helper_functions import check_if_empty_input, measure_time
from core.utils.rich_console import display_in_table
from core.utils.text_properties import normalize_content

cs = ColorScheme()

def search_ltr(
    query: str, conn, cursor, model, top_k=10, candidate_k=50
) -> Tuple[List[Tuple], Dict[str, Any]]:
    """
    Executes a 2-Stage Search:
    1. Retrieval: Hybrid Search (Linear) to get top N candidates (default 50).
    2. Re-Ranking: LTR (Cross-Encoder) to re-order the top N candidates.
    """
    if check_if_empty_input(query):
        return [], {}

    get_elapsed = measure_time()

    # --- Stage 1: Retrieval (Hybrid - Linear) ---
    # We fetch more candidates (candidate_k) than we need for the final view (top_k)
    # 1. Semantic
    sem_results = execute_vector_query(query, conn, cursor, model, top_k=candidate_k, threshold=0.1)
    
    # 2. BM25
    bm25_utils.update_bm25_index(cursor, normalize_content)
    bm25_results = []
    if bm25_utils.bm25_index and bm25_utils.bm25_corpus:
        scores = bm25_utils.bm25_index.get_scores(normalize_content(query).split())
        for i, (doc_id, content) in enumerate(bm25_utils.bm25_corpus):
            raw = scores[i]
            if raw > 0:
                bm25_results.append((doc_id, content, raw))
    
    # 3. Hybrid Merge (Linear 0.5 default)
    scorer = HybridScorer(alpha=0.5)
    candidates, _ = scorer.combine(sem_results, bm25_results, top_k=candidate_k, strategy="linear")
    
    stage1_time = (measure_time() - get_elapsed) * 1000 # Rough estimate

    # --- Stage 2: LTR Re-Ranking ---
    ltr = LTRScorer()
    final_results = ltr.rerank(query, candidates, top_n=top_k)
    
    # Stats
    total_time = measure_time()
    
    display_in_table(final_results, query=query, mode="LTR (Re-Ranked)")
    # We pass empty lists for breakdown because LTR obscures the original source components
    display_search_stats([], [], total_time, mode="LTR")

    stats = {
        "search_type": "ltr",
        "candidates_count": len(candidates),
        "stage1_time_ms": stage1_time
    }

    return final_results, stats
