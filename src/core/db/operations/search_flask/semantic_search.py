from utils.ColorScheme import ColorScheme
from utils.helper_functions import measure_time
import re

from core.db.operations.search_queries import execute_vector_query
from core.utils.console_stats import display_search_stats
from core.utils.rich_console import display_in_table

cs = ColorScheme()

BASE_THRESHOLD = 0.35
TOP_K = 200

def _dynamic_threshold(q: str) -> float:
    tokens = [t for t in q.strip().split() if t]
    n = len(tokens)
    if n <= 1:
        return 0.20
    if n <= 3:
        return 0.28
    return BASE_THRESHOLD

def search_semantic(query: str, conn, cursor, model, top_k=TOP_K, threshold: float = None):
    if not query.strip():
        print(f"{cs.RED}Query cannot be empty.{cs.RESET}")
        return [], {}

    get_elapsed = measure_time()
    thr = threshold if threshold is not None else _dynamic_threshold(query)
    results = execute_vector_query(query, conn, cursor, model, top_k, thr)
    if not results:
        thr_fallback = max(thr - 0.1, 0.1)
        results = execute_vector_query(query, conn, cursor, model, top_k * 2, thr_fallback)

    filtered = []
    q_tokens = re.findall(r"\w+", query.lower())
    prefer_en = all(ord(c) < 128 for c in query)
    phrase = " ".join(q_tokens).strip()
    for doc_id, content, score, language, created_at in results:
        text = (content or "").strip()
        if len(text) < 20:
            continue
        boost = 0.0
        if q_tokens and any(t in text.lower() for t in q_tokens):
            boost += 0.05
        # Exact phrase boost
        if phrase and phrase in text.lower():
            boost += 0.06
        # Position boost: earlier matches get a small extra boost
        pos_boost = 0.0
        try:
            positions = []
            for t in q_tokens:
                p = text.lower().find(t)
                if p != -1:
                    positions.append(p)
            if positions:
                first_pos = min(positions)
                # Map position to [0, 0.05] boost based on proximity to start
                ratio = max(0.0, 1.0 - (first_pos / max(1, len(text))))
                pos_boost = 0.05 * ratio
        except Exception:
            pos_boost = 0.0
        boost += pos_boost
        if prefer_en and (language or "").lower() == "en":
            boost += 0.02
        filtered.append((doc_id, content, float(score) + boost, language, created_at))

    filtered.sort(key=lambda x: x[2], reverse=True)
    results = filtered

    display_in_table(results, query=query, mode="semantic")
    display_search_stats(results, [],  get_elapsed, mode="semantic")

    return results, {}
