import os
import time

from core.db.operations.search_flask.HybridScorer import HybridScorer
from core.db.operations.search_queries import execute_vector_query, execute_bm25_query
from core.utils.ColorScheme import ColorScheme
from core.utils.console_stats import display_search_stats
from core.utils.helper_functions import check_if_empty_input, measure_time
from core.utils.rich_console import display_in_table

cs = ColorScheme()
# BASE_THRESHOLD = 0.35
# TOP_K = 1000
try:
    BASE_THRESHOLD = float(os.environ.get("BASE_THRESHOLD", "0.15"))
except Exception:
    BASE_THRESHOLD = 0.15

try:
    TOP_K = int(os.environ.get("TOP_K", "10"))
except Exception:
    TOP_K = 10
def search_hybrid(
    query: str, conn, cursor, model, top_k=TOP_K, threshold=BASE_THRESHOLD, fusion_strategy="linear", alpha=None
):
    if check_if_empty_input(query):
        print(f"{cs.RED}Input cannot be empty.{cs.RESET}")
        return [], {}
    get_elapsed = measure_time()

    # Timing Breakdown
    t_start = time.time()

    # Semantic Search
    sem_results = execute_vector_query(query, conn, cursor, model, top_k, threshold)
    t_sem = time.time()
    
    # BM25 Search (DB-Native TS_RANK)
    # Scalable for > 1M documents
    bm25_results = execute_bm25_query(query, cursor, top_k)
    t_key = time.time()

    # Determine alpha (BM25 weight)
    if alpha is not None:
        try:
            ALPHA = float(alpha)
        except (ValueError, TypeError):
            ALPHA = 0.5
    else:
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
            print("\nBM25 results (doc_id, score):")
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
