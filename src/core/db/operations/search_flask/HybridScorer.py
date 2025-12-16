import math
import os
from typing import Any, Dict, List, Tuple


class HybridScorer:
    """Encapsulates hybrid scoring logic: normalize BM25, combine with semantic.

    Usage:
        scorer = HybridScorer(alpha=0.5)
        final, components = scorer.combine(sem_results, bm25_results)

    - sem_results: list of (doc_id, content, semantic_score, language, created_at)
    - bm25_results: list of (doc_id, content, raw_bm25_score)

    Returns:
    - final: list of (doc_id, content, final_score, language, created_at)
    - components: dict[doc_id] -> {semantic_score, bm25_score, semantic_weight, bm25_weight}
    """

    def __init__(self, alpha: float = 0.5):
        # alpha = weight for BM25, (1-alpha) for semantic
        if not 0.0 <= alpha <= 1.0:
            raise ValueError("alpha must be between 0 and 1")
        self.alpha = float(alpha)

    def normalize_bm25(self, bm25_results: List[Tuple[int, str, float]]) -> Dict[int, float]:
        if not bm25_results:
            return {}
        # Select normalization method via env var: 'max' (default), 'log', or 'minmax'
        method = os.getenv("HYBRID_BM25_NORM", "max").strip().lower()
        scores = [s for _, _, s in bm25_results]
        min_s, max_s = min(scores), max(scores)
        out: Dict[int, float] = {}

        if method == "log":
            # log1p-scaling: log1p(raw) / log1p(max)
            denom = math.log1p(max_s) if max_s > 0 else 1.0
            for doc_id, _, raw in bm25_results:
                norm = (math.log1p(raw) / denom) if max_s > 0 else 0.0
                out[doc_id] = float(norm)
            return out

        if method == "max":
            # simple max-scaling: raw / max
            denom = max_s if max_s > 0 else 1.0
            for doc_id, _, raw in bm25_results:
                norm = (raw / denom) if denom > 0 else 0.0
                out[doc_id] = float(norm)
            return out

        # fallback: original min-max normalization
        denom = max_s - min_s if max_s != min_s else 1.0
        for doc_id, _, raw in bm25_results:
            norm = (raw - min_s) / denom if max_s != min_s else (1.0 if raw > 0 else 0.0)
            out[doc_id] = float(norm)
        return out

    def combine(
        self,
        sem_results: List[Tuple[int, str, float, Any, Any]],
        bm25_results: List[Tuple[int, str, float]],
        top_k: int = 100,
    ):
        bm25_norm = self.normalize_bm25(bm25_results)

        result_map: Dict[int, Dict[str, Any]] = {}

        for doc_id, content, sem_score, language, created_at in sem_results:
            result_map[doc_id] = {
                "content": content,
                "language": language,
                "created_at": created_at,
                "semantic_score": float(sem_score),
                "bm25_score": 0.0,
                "final_score": float(sem_score) * (1 - self.alpha),
            }

        for doc_id, content, raw_bm in bm25_results:
            bm = float(bm25_norm.get(doc_id, 0.0))
            if doc_id in result_map:
                result_map[doc_id]["bm25_score"] = bm
                result_map[doc_id]["final_score"] += bm * self.alpha
            else:
                # No semantic hit; include BM25-only
                result_map[doc_id] = {
                    "content": content,
                    "language": None,
                    "created_at": None,
                    "semantic_score": 0.0,
                    "bm25_score": bm,
                    "final_score": bm * self.alpha,
                }

        # Build final list preserving tuple shape (doc_id, content, final_score, language, created_at)
        final_list = []
        components = {}
        for doc_id, v in result_map.items():
            final_list.append((doc_id, v["content"], float(v["final_score"]), v["language"], v["created_at"]))
            components[doc_id] = {
                "semantic_score": float(v.get("semantic_score", 0.0)),
                "bm25_score": float(v.get("bm25_score", 0.0)),
                "semantic_weight": float(1 - self.alpha),
                "bm25_weight": float(self.alpha),
            }

        final_sorted = sorted(final_list, key=lambda x: x[2], reverse=True)[:top_k]
        return final_sorted, components
