import time
from pydoc import doc

import utils.bm25_utils as bm25_utils
from regex import B
from utils.helper_functions import check_if_empty_input, measure_time
from utils.text_properties import normalize_content

from core.db.operations.search_queries import execute_vector_query
from core.utils.ColorScheme import ColorScheme
from core.utils.console_stats import display_search_stats
from core.utils.rich_console import display_in_table

cs = ColorScheme()

TRASHOLD = 0.4
TOP_K = 100


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

    # 3. Combine (simple: take semantic, boost with BM25)
    result_map = {r[0]: r for r in sem_results}
    for doc_id, content, score in bm25_results:
        if doc_id in result_map:
            result_map[doc_id] = (*result_map[doc_id][:2], result_map[doc_id][2] + score, *result_map[doc_id][3:])
        else:
            result_map[doc_id] = (doc_id, content, score, None, None)

    final = sorted(result_map.values(), key=lambda x: x[2], reverse=True)[:top_k]

    display_in_table(final, query=query, mode="hybrid")
    display_search_stats(sem_results, bm25_results, get_elapsed, mode="hybrid")
    return final, {}
