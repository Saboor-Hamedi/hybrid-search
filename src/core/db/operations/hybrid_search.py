import core.utils.bm25_utils as bm25_utils
from core.db.operations.search_queries import execute_vector_query
from core.utils.ColorScheme import ColorScheme
from core.utils.console_stats import display_search_stats
from core.utils.helper_functions import check_if_empty_input, measure_time
from core.utils.rich_console import display_in_table
from core.utils.text_properties import normalize_content

cs = ColorScheme()
TRASHOLD = 0.4
TOP_K = 100


# def search_hybrid(
#     query: str, conn, cursor, model, top_k=TOP_K, threshold=TRASHOLD, bm25_weight=0.5
# ):
#     if check_if_empty_input(query):
#         print(f"{cs.RED}Input cannot be empty.{cs.RESET}")
#         return [], {}

#     get_elapsed = measure_time()

#     # 1. Semantic Search
#     sem_results = execute_vector_query(query, conn, cursor, model, top_k, threshold)


#     # Update BM25 index
#     bm25_utils.update_bm25_index(cursor, normalize_content)

#     bm25_results = []
#     if bm25_utils.bm25_index and bm25_utils.bm25_corpus:
#         scores = bm25_utils.bm25_index.get_scores(normalize_content(query).split())

#         bm25_results = [
#             (doc_id, content, scores[i])
#             for i, (doc_id, content) in enumerate(bm25_utils.bm25_corpus)
#             if scores[i] > 0
#         ]

#     # 3. Normalize BM25 to 0–1
#     bm25_scores = [s for _, _, s in bm25_results]
#     max_bm25 = max(bm25_scores) if bm25_scores else 1.0
#     min_bm25 = min(bm25_scores) if bm25_scores else 0.0
#     bm25_range = max_bm25 - min_bm25 if max_bm25 > min_bm25 else 1.0

#     def normalize_bm25(score):
#         if bm25_range <= 0:
#             return 1.0 if score > 0 else 0.0
#         return (score - min_bm25) / bm25_range

#     # 4. Fusion: 0.6 semantic + 0.4 BM25 → final score in 0.0–1.0
#     result_map = {}  # doc_id → dict

#     semantic_weight = 0.6
#     keyword_weight = 0.4

#     # Add all semantic results
#     for doc_id, content, cosine_score, lang, created_at in sem_results:
#         final_score = semantic_weight * cosine_score
#         result_map[doc_id] = {
#             "content": content or "",
#             "score": final_score,
#             "language": lang or "unknown",
#             "created_at": created_at or "unknown",
#         }

#     # Boost with normalized BM25
#     for doc_id, content, bm25_score in bm25_results:
#         boost = keyword_weight * normalize_bm25(bm25_score)

#         if doc_id in result_map:
#             result_map[doc_id]["score"] += boost
#             # Keep best content
#             if content:
#                 result_map[doc_id]["content"] = content
#         else:
#             result_map[doc_id] = {
#                 "content": content or "",
#                 "score": boost,
#                 "language": "unknown",
#                 "created_at": "unknown",
#             }

#     # 5. Final normalization to 0–1 (safety)
#     all_scores = [info["score"] for info in result_map.values()]
#     max_score = max(all_scores) if all_scores else 1.0
#     if max_score > 1.0:
#         for info in result_map.values():
#             info["score"] = info["score"] / max_score

#     # 6. Convert to list of dicts, sort, limit
#     final_results = []
#     for doc_id, info in result_map.items():
#         final_results.append({
#             "doc_id": doc_id,
#             "content": info["content"],
#             "score": round(info["score"], 4),
#             "language": info["language"],
#             "created_at": info["created_at"],
#         })

#     final_results.sort(key=lambda x: x["score"], reverse=True)
#     final_results = final_results[:top_k]

#     # 7. Display (keep your old format if needed)
#     display_list = [
#         (d["doc_id"], d["content"], d["score"], d["language"], d["created_at"])
#         for d in final_results
#     ]
#     display_in_table(display_list, query=query, mode="hybrid")
#     display_search_stats(sem_results, bm25_results, get_elapsed, mode="hybrid")


#     return final_results, {}
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
