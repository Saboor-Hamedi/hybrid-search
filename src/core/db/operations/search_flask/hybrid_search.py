import os

import core.utils.bm25_utils as bm25_utils
from core.db.operations.search_flask.HybridScorer import HybridScorer
from core.db.operations.search_queries import execute_vector_query
from core.utils.ColorScheme import ColorScheme
from core.utils.console_stats import display_search_stats
from core.utils.helper_functions import check_if_empty_input, measure_time
from core.utils.rich_console import display_in_table
from core.utils.text_properties import normalize_content

cs = ColorScheme()
# BASE_THRESHOLD = 0.35
# TOP_K = 1000
try:
    BASE_THRESHOLD = float(os.environ.get("BASE_THRESHOLD", "0.15"))
except Exception:
    BASE_THRESHOLD = 0.15

try:
    TOP_K = int(os.environ.get("TOP_K", "1000"))
except Exception:
    TOP_K = 1000
def search_hybrid(
    query: str, conn, cursor, model, top_k=TOP_K, threshold=BASE_THRESHOLD, fusion_strategy="linear"
):
    if check_if_empty_input(query):
        print(f"{cs.RED}Input cannot be empty.{cs.RESET}")
        return [], {}
    get_elapsed = measure_time()

    # Timing Breakdown
    import time
    t_start = time.time()

    # Semantic Search
    sem_results = execute_vector_query(query, conn, cursor, model, top_k, threshold)
    t_sem = time.time()
    
    # BM25 Search
    bm25_utils.update_bm25_index(cursor, normalize_content)
    bm25_results = []
    bm25_raw_map = {}
    if bm25_utils.bm25_index and bm25_utils.bm25_corpus:
        scores = bm25_utils.bm25_index.get_scores(normalize_content(query).split())
        for i, (doc_id, content) in enumerate(bm25_utils.bm25_corpus):
            raw = scores[i]
            bm25_raw_map[doc_id] = raw
            if raw > 0:
                bm25_results.append((doc_id, content, raw))
    t_key = time.time()

    # Determine alpha (BM25 weight) from environment if provided.
    # Priority: BM25_WEIGHT -> 1 - SEMANTIC_WEIGHT -> default 0.5
    try:
        alpha_val = os.environ.get("BM25_WEIGHT")
        if alpha_val is not None and alpha_val.strip() != "":
            ALPHA = float(alpha_val)
        else:
            sem_w = os.environ.get("SEMANTIC_WEIGHT")
            if sem_w is not None and sem_w.strip() != "":
                ALPHA = max(0.0, min(1.0, 1.0 - float(sem_w)))
            else:
                ALPHA = 0.5
    except Exception:
        ALPHA = 0.5

    scorer = HybridScorer(alpha=ALPHA)
    final, components = scorer.combine(sem_results, bm25_results, top_k=top_k, strategy=fusion_strategy)
    t_fuse = time.time()

    # Calculate Breakdown
    lat_sem = (t_sem - t_start) * 1000
    lat_key = (t_key - t_sem) * 1000
    lat_fuse = (t_fuse - t_key) * 1000

    # Optional debug: if DEBUG_QUERY env var matches the query, print detailed scores
    debug_q = os.environ.get("DEBUG_QUERY")
    try:
        if debug_q and debug_q.strip() and debug_q.strip() == query.strip():
            print("--- HYBRID DEBUG for query:\n", query)
            print("Semantic results (doc_id, sem_score):")
            for d in sem_results:
                print(d[0], d[2])
            print("\nBM25 raw scores (doc_id -> raw):")
            for k, v in list(bm25_raw_map.items())[:50]:
                print(k, v)
            print("\nBM25 results (filtered, raw > 0):")
            for d in bm25_results:
                print(d[0], d[2])
            # (Normalization debug removed as API changed)
            print("\nComponents (per-doc):")
            for k, v in components.items():
                print(k, v)
            print("--- END DEBUG ---")
    except Exception:
        pass

    display_mode = "hybrid" if fusion_strategy == "linear" else f"hybrid-{fusion_strategy}"
    display_in_table(final, query=query, mode=display_mode)
    display_search_stats(sem_results, bm25_results, get_elapsed, mode=display_mode)

    # Return stats for API (include components mapping)
    stats = {
        "sem_results": sem_results,
        "bm25_results": bm25_results,
        "components": components,
        "alpha": ALPHA,
        "search_type": display_mode,
        "latency_stats": {
            "semantic": lat_sem,
            "keyword": lat_key,
            "fusion": lat_fuse
        }
    }

    return final, stats
