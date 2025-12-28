from typing import Any, Dict, List, Tuple


class RRFScorer:
    """
    Implements Reciprocal Rank Fusion (RRF).
    This class combines multiple ranked lists based on the order of results
    rather than the absolute scores. It is highly robust as it is scale-agnostic.
    """

    def __init__(self, k: int = 60):
        """
        Initialize RRF Scorer.

        Args:
            k: Ranking constant (default 60). A larger k reduces the impact 
               of high-ranking items relative to lower-ranking ones.
        """
        self.k = k

    def combine(
        self,
        sem_results: List[Tuple[int, str, float, Any, Any]],
        bm25_results: List[Tuple[int, str, float, Any, Any]],
        top_k: int = 100,
    ) -> Tuple[List[Tuple], Dict[int, Dict[str, Any]]]:
        """
        Combines Semantic and BM25 results using Reciprocal Rank Fusion.

        Args:
            sem_results: List of (doc_id, content, score, language, created_at)
            bm25_results: List of (doc_id, content, score, language, created_at)
            top_k: Target number of results to return.

        Returns:
            - final_sorted: List of (doc_id, content, rrf_score, language, created_at)
            - components: Dict mapping doc_id to individual scores/ranks for transparency.
        """
        rrf_scores: Dict[int, float] = {}
        doc_data: Dict[int, Dict[str, Any]] = {}
        components: Dict[int, Dict[str, Any]] = {}

        # Helper to process a ranked list
        def process_list(results, weight=1.0):
            for rank, item in enumerate(results, start=1):
                doc_id = item[0]
                content = item[1]
                score = item[2]
                lang = item[3] if len(item) > 3 else None
                date = item[4] if len(item) > 4 else None

                # Calculate RRF contribution: weight * (1 / (k + rank))
                contribution = weight * (1.0 / (self.k + rank))

                if doc_id not in rrf_scores:
                    rrf_scores[doc_id] = 0.0
                    doc_data[doc_id] = {
                        "content": content,
                        "language": lang,
                        "created_at": date,
                    }
                    components[doc_id] = {
                        "semantic_rank": None,
                        "bm25_rank": None,
                        "semantic_rrf_score": 0.0,
                        "bm25_rrf_score": 0.0,
                    }

                rrf_scores[doc_id] += contribution
                
                # Identify which list we are processing to update components
                if weight == 1.0: # Logic for Semantic (assuming weight system or distinct calls)
                    # For simplicity in this implementation, we'll check list source outside or use specific markers
                    pass

        # Since we have two specific lists, let's process them individually for clearer component tracking
        
        # 1. Process Semantic
        for rank, item in enumerate(sem_results, start=1):
            doc_id, content, score, lang, date = item
            contribution = 1.0 / (self.k + rank)
            
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + contribution
            doc_data[doc_id] = {"content": content, "language": lang, "created_at": date}
            
            if doc_id not in components:
                components[doc_id] = {"semantic_rank": rank, "bm25_rank": None, "semantic_score": score, "bm25_score": 0.0}
            else:
                components[doc_id]["semantic_rank"] = rank
                components[doc_id]["semantic_score"] = score

        # 2. Process BM25
        for rank, item in enumerate(bm25_results, start=1):
            doc_id, content, score = item[0], item[1], item[2]
            # BM25 might have different tuple length depending on source
            lang = item[3] if len(item) > 3 else doc_data.get(doc_id, {}).get("language")
            date = item[4] if len(item) > 4 else doc_data.get(doc_id, {}).get("created_at")
            
            contribution = 1.0 / (self.k + rank)
            
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + contribution
            
            if doc_id not in doc_data:
                doc_data[doc_id] = {"content": content, "language": lang, "created_at": date}
            
            if doc_id not in components:
                components[doc_id] = {"semantic_rank": None, "bm25_rank": rank, "semantic_score": 0.0, "bm25_score": score}
            else:
                components[doc_id]["bm25_rank"] = rank
                components[doc_id]["bm25_score"] = score

        # 3. Finalize
        final_list = []
        for doc_id, score in rrf_scores.items():
            data = doc_data[doc_id]
            final_list.append((
                doc_id, 
                data["content"], 
                float(score), 
                data["language"], 
                data["created_at"]
            ))

        # Sort by RRF score descending
        final_sorted = sorted(final_list, key=lambda x: x[2], reverse=True)[:top_k]
        
        # Standardize components for frontend (similar to HybridScorer)
        final_components = {}
        for doc_id, comp in components.items():
            final_components[doc_id] = {
                "semantic_score": comp["semantic_score"],
                "bm25_score": comp["bm25_score"],
                "semantic_rank": comp["semantic_rank"],
                "bm25_rank": comp["bm25_rank"],
                "rrf_score": float(rrf_scores[doc_id])
            }

        return final_sorted, final_components