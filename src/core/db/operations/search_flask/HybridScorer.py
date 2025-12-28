import math
import os
from typing import Any, Dict, List, Tuple


class HybridScorer:
    """Encapsulates hybrid scoring logic: normalize scores, combine with different strategies.

    Usage:
        scorer = HybridScorer(alpha=0.5)
        # Linear (Default)
        final, components = scorer.combine(sem_results, bm25_results, strategy="linear")
        # CombSUM
        final, components = scorer.combine(sem_results, bm25_results, strategy="combsum")

    Strategies:
    - 'linear': alpha * BM25 + (1-alpha) * Semantic
    - 'combsum': Sum of normalized scores
    - 'combmnz': CombSUM * (number of non-zero sources)
    """

    def __init__(self, alpha: float = 0.5):
        # alpha = weight for BM25, (1-alpha) for semantic (Used only in 'linear' mode)
        if not 0.0 <= alpha <= 1.0:
            raise ValueError("alpha must be between 0 and 1")
        self.alpha = float(alpha)

    def _normalize_values(self, scores: List[float], method: str = "max") -> List[float]:
        """Helper to normalize a list of floats based on method."""
        if not scores:
            return []
        
        min_s, max_s = min(scores), max(scores)
        
        if method == "log":
            # log1p-scaling: log1p(raw) / log1p(max)
            denom = math.log1p(max_s) if max_s > 0 else 1.0
            return [(math.log1p(s) / denom) if max_s > 0 else 0.0 for s in scores]

        if method == "minmax":
            # (val - min) / (max - min)
            denom = max_s - min_s if max_s != min_s else 1.0
            return [(s - min_s) / denom if max_s != min_s else (1.0 if s > 0 else 0.0) for s in scores]

        # Default: "max" -> val / max
        denom = max_s if max_s > 0 else 1.0
        return [(s / denom) if denom > 0 else 0.0 for s in scores]

    def combine(
        self,
        sem_results: List[Tuple[int, str, float, Any, Any]],
        bm25_results: List[Tuple[int, str, float]],
        top_k: int = 100,
        strategy: str = "linear"
    ):
        """
        Combines Semantic and BM25 results using the specified strategy.
        
        sem_results: List of (doc_id, content, score, language, created_at)
        bm25_results: List of (doc_id, content, score)
        strategy: 'linear', 'combsum', or 'combmnz'
        """
        
        # 1. Normalize BM25 Scores
        bm25_method = os.getenv("HYBRID_BM25_NORM", "max").strip().lower()
        # For CombSUM/MNZ, we prefer 'max' scaling (score / max_score) to preserve
        # relative strength without zeroing out the bottom element (which minmax does).
        if strategy in ["combsum", "combmnz"]:
            bm25_method = "max"
            
        bm25_scores_raw = [r[2] for r in bm25_results]
        bm25_scores_norm = self._normalize_values(bm25_scores_raw, bm25_method)
        bm25_map = {r[0]: s for r, s in zip(bm25_results, bm25_scores_norm)}

        # 2. Normalize Semantic Scores
        sem_scores_raw = [r[2] for r in sem_results]
        # Semantic scores (cosine) are typically 0.0 to 1.0. 
        # Using 'max' normalization preserves their distribution better than minmax.
        sem_scores_norm = self._normalize_values(sem_scores_raw, "max")
        sem_map = {r[0]: s for r, s in zip(sem_results, sem_scores_norm)}

        # 3. Merge candidates
        all_ids = set(bm25_map.keys()) | set(sem_map.keys())
        
        # Helper to get content info from either source
        content_lookup = {}
        for r in sem_results: content_lookup[r[0]] = (r[1], r[3], r[4]) # content, lang, date
        for r in bm25_results: 
            if r[0] not in content_lookup:
                content_lookup[r[0]] = (r[1], None, None)

        result_map = {}

        for doc_id in all_ids:
            s_norm = sem_map.get(doc_id, 0.0)
            b_norm = bm25_map.get(doc_id, 0.0)
            
            score = 0.0
            
            # --- FUSION LOGIC ---
            if strategy == "combsum":
                # CombSUM: Sum of normalized scores
                score = s_norm + b_norm
                
            elif strategy == "combmnz":
                # CombMNZ: CombSUM * count of non-zero systems
                # We check > 0.001 to avoid floating point artifacts
                count = (1 if s_norm > 1e-6 else 0) + (1 if b_norm > 1e-6 else 0)
                score = (s_norm + b_norm) * count
                
            else:
                # Default: Linear (Weighted)
                score = (b_norm * self.alpha) + (s_norm * (1 - self.alpha))

            content, lang, created = content_lookup.get(doc_id, (None, None, None))
            
            result_map[doc_id] = {
                "content": content,
                "language": lang,
                "created_at": created,
                "semantic_score": s_norm,
                "bm25_score": b_norm,
                "final_score": score
            }

        # 4. Format Output
        final_list = []
        components = {}
        
        for doc_id, v in result_map.items():
            final_list.append((doc_id, v["content"], float(v["final_score"]), v["language"], v["created_at"]))
            components[doc_id] = {
                "semantic_score": v["semantic_score"],
                "bm25_score": v["bm25_score"],
                "semantic_weight": 1 - self.alpha if strategy == "linear" else 1.0,
                "bm25_weight": self.alpha if strategy == "linear" else 1.0,
                "strategy": strategy
            }

        final_sorted = sorted(final_list, key=lambda x: x[2], reverse=True)[:top_k]
        return final_sorted, components
