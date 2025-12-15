import core.utils.bm25_utils as bm25_utils
from core.db.operations.search_flask.hybrid_scoring import HybridScorer
from core.db.operations.search_queries import execute_vector_query
from core.utils.ColorScheme import ColorScheme
from core.utils.console_stats import display_search_stats
from core.utils.helper_functions import check_if_empty_input, measure_time
from core.utils.rich_console import display_in_table
from core.utils.text_properties import normalize_content

cs = ColorScheme()
TRASHOLD = 0.65  # Increased to 0.65 to filter out high-scoring noise like 'vi' (0.64)
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

    # 3. Combine with HybridScorer (normalizes BM25 internally)
    ALPHA = 0.5
    scorer = HybridScorer(alpha=ALPHA)
    final, components = scorer.combine(sem_results, bm25_results, top_k=top_k)



    display_in_table(final, query=query, mode="hybrid")
    display_search_stats(sem_results, bm25_results, get_elapsed, mode="hybrid")

    # Return stats for API (include components mapping)
    stats = {
        "sem_results": sem_results,
        "bm25_results": bm25_results,
        "components": components,
        "alpha": ALPHA,
    }

    return final, stats
