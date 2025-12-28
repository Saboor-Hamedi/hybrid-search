from typing import List, Tuple, Any, Dict
from sentence_transformers import CrossEncoder

class LTRScorer:
    """
    Learning-to-Rank (LTR) Scorer using a Cross-Encoder for re-ranking.
    This acts as a 'Teacher' model to precise rank top candidates.
    """
    _instance = None
    _model = None

    def __new__(cls):
        # Singleton to load model only once
        if cls._instance is None:
            cls._instance = super(LTRScorer, cls).__new__(cls)
            # Use a lightweight but effective cross-encoder (MiniLM-L-6-v2)
            # Alternatives: 'cross-encoder/ms-marco-TinyBERT-L-2-v2' (Faster)
            print("Loading LTR Cross-Encoder (ms-marco-MiniLM-L-6-v2)...")
            cls._model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2', max_length=512)
        return cls._instance

    def rerank(
        self, 
        query: str, 
        candidates: List[Tuple[int, str, float, Any, Any]], 
        top_n: int = 10
    ) -> List[Tuple[int, str, float, Any, Any]]:
        """
        Re-ranks a list of (doc_id, content, score, ...) candidates using the Cross-Encoder.
        
        Args:
            query: The search query.
            candidates: List of tuples from search results (must include doc_id and content).
            top_n: Number of results to return after re-ranking.
            
        Returns:
            Re-sorted list of candidates with updated scores from the Cross-Encoder.
        """
        if not candidates:
            return []

        # Prepare pairs for the model: (Query, Document Content)
        # Note: We truncate content to avoid massive token usage if not handled by max_length
        pairs = [[query, doc[1][:2000]] for doc in candidates]
        
        # Predict scores (returns a numpy array or list of floats)
        scores = self._model.predict(pairs)
        
        # Combine original candidate data with new LTR score
        scored_candidates = []
        for idx, score in enumerate(scores):
            original = candidates[idx]
            # Structure: (doc_id, content, NEW_SCORE, language, created_at)
            # We cast score to float because numpy float isn't always JSON serializable later
            new_tuple = (original[0], original[1], float(score), original[3], original[4])
            scored_candidates.append(new_tuple)
            
        # Sort by new LTR score descending
        scored_candidates.sort(key=lambda x: x[2], reverse=True)
        
        return scored_candidates[:top_n]
