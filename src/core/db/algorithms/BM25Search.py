"""
BM25 Algorithm Implementation

This module provides a clean, optimized implementation of the BM25 (Best Matching 25)
ranking algorithm for keyword-based document retrieval.

BM25 is a probabilistic ranking function used to estimate the relevance of documents
to a given search query. It's widely used in information retrieval systems.

Formula:
    BM25(D, Q) = Σ IDF(qi) * (f(qi, D) * (k1 + 1)) / (f(qi, D) + k1 * (1 - b + b * |D| / avgdl))

Where:
    - D: Document
    - Q: Query
    - qi: Query term i
    - f(qi, D): Frequency of qi in document D
    - |D|: Length of document D
    - avgdl: Average document length in the collection
    - k1: Term frequency saturation parameter (typically 1.2-2.0)
    - b: Length normalization parameter (typically 0.75)
    - IDF(qi): Inverse document frequency of query term qi
"""

import math
import os
from typing import List, Tuple

from rank_bm25 import BM25Okapi

from core.utils.ColorScheme import ColorScheme

cs = ColorScheme()


class BM25Search:
    """
    BM25 Search Engine

    Provides efficient BM25-based keyword search with caching and optimization.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Initialize BM25 Search

        Args:
            k1: Term frequency saturation parameter (default: 1.5)
            b: Length normalization parameter (default: 0.75)
        """
        self.k1 = k1
        self.b = b
        self.bm25_index = None
        self.corpus = None
        self.doc_ids = None

    def build_index(self, cursor, normalize_fn=None):
        """
        Build BM25 index from database documents

        Args:
            cursor: Database cursor
            normalize_fn: Optional text normalization function

        Returns:
            int: Number of documents indexed
        """
        try:
            # Fetch all documents
            cursor.execute("""
                SELECT id, content, language, created_at
                FROM document
                ORDER BY id
            """)

            rows = cursor.fetchall()

            if not rows:
                print(f"{cs.YELLOW}Warning: No documents found in database{cs.RESET}")
                return 0

            # Build corpus
            self.corpus = []
            self.doc_ids = []

            for row in rows:
                doc_id = row[0]
                content = row[1] or ""
                language = row[2] or "en"
                created_at = row[3]

                # Normalize content if function provided
                if normalize_fn:
                    content = normalize_fn(content)

                # Tokenize (simple whitespace split for now)
                tokens = content.lower().split()

                self.corpus.append((doc_id, content, language, created_at))
                self.doc_ids.append(doc_id)

            # Build BM25 index
            tokenized_corpus = [doc[1].lower().split() for doc in self.corpus]
            self.bm25_index = BM25Okapi(tokenized_corpus, k1=self.k1, b=self.b)

            print(f"{cs.GREEN}✓ BM25 index built: {len(self.corpus)} documents{cs.RESET}")
            return len(self.corpus)

        except Exception as e:
            print(f"{cs.RED}Error building BM25 index: {str(e)}{cs.RESET}")
            return 0

    def search(self, query: str, top_k: int = 50, min_score: float = 0.0) -> List[Tuple]:
        """
        Search documents using BM25

        Args:
            query: Search query string
            top_k: Number of top results to return
            min_score: Minimum BM25 score threshold

        Returns:
            List of tuples: (doc_id, content, score, language, created_at)
        """
        if not self.bm25_index or not self.corpus:
            print(f"{cs.RED}Error: BM25 index not built. Call build_index() first.{cs.RESET}")
            return []

        try:
            # Tokenize query
            query_tokens = query.lower().split()

            # Get BM25 scores
            scores = self.bm25_index.get_scores(query_tokens)

            # Create results with scores
            results = []
            for idx, score in enumerate(scores):
                if score > min_score:
                    doc_id, content, language, created_at = self.corpus[idx]
                    created_at_str = created_at.strftime("%Y-%m-%d %H:%M") if created_at else "unknown"
                    results.append((doc_id, content, float(score), language, created_at_str))

            # Sort by score descending
            results.sort(key=lambda x: x[2], reverse=True)

            # Return top_k results
            return results[:top_k]

        except Exception as e:
            print(f"{cs.RED}Error in BM25 search: {str(e)}{cs.RESET}")
            import traceback
            traceback.print_exc()
            return []

    def get_top_documents(self, query: str, n: int = 10) -> List[int]:
        """
        Get top N document IDs for a query

        Args:
            query: Search query
            n: Number of documents to return

        Returns:
            List of document IDs
        """
        results = self.search(query, top_k=n)
        return [r[0] for r in results]

    def normalize_scores(self, results: List[Tuple]) -> List[Tuple]:
        """
        Normalize BM25 scores to 0-1 range using Min-Max normalization

        Args:
            results: List of (doc_id, content, score, language, created_at)

        Returns:
            List with normalized scores
        """
        if not results:
            return []

        method = os.getenv("HYBRID_BM25_NORM", "max").strip().lower()
        scores = [r[2] for r in results]
        min_score = min(scores)
        max_score = max(scores)

        normalized = []
        if method == "log":
            denom = math.log1p(max_score) if max_score > 0 else 1.0
            for doc_id, content, score, language, created_at in results:
                norm = (math.log1p(score) / denom) if max_score > 0 else 0.0
                normalized.append((doc_id, content, float(norm), language, created_at))
            return normalized

        if method == "max":
            denom = max_score if max_score > 0 else 1.0
            for doc_id, content, score, language, created_at in results:
                norm = (score / denom) if denom > 0 else 0.0
                normalized.append((doc_id, content, float(norm), language, created_at))
            return normalized

        # fallback: min-max
        score_range = max_score - min_score
        if score_range == 0:
            return [(r[0], r[1], 1.0 if r[2] > 0 else 0.0, r[3], r[4]) for r in results]

        for doc_id, content, score, language, created_at in results:
            norm_score = (score - min_score) / score_range
            normalized.append((doc_id, content, float(norm_score), language, created_at))

        return normalized


# Global BM25 instance for reuse
_bm25_engine = None


def get_bm25_engine() -> BM25Search:
    """
    Get or create global BM25 engine instance

    Returns:
        BM25Search: Global BM25 engine
    """
    global _bm25_engine
    if _bm25_engine is None:
        _bm25_engine = BM25Search(k1=1.5, b=0.75)
    return _bm25_engine


def search_bm25(query: str, cursor, top_k: int = 50, normalize_fn=None) -> List[Tuple]:
    """
    Convenience function for BM25 search

    Args:
        query: Search query
        cursor: Database cursor
        top_k: Number of results
        normalize_fn: Optional text normalization function

    Returns:
        List of search results
    """
    engine = get_bm25_engine()

    # Build index if not already built
    if engine.bm25_index is None:
        engine.build_index(cursor, normalize_fn)

    return engine.search(query, top_k=top_k)
