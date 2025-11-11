import os
import sys

# Ensure path is set correctly
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from core.utils.ColorScheme import ColorScheme
from utils.helper_functions import measure_time

cs = ColorScheme()

def display_search_stats(semantic_results, bm25_results, get_elapsed_func):
    """
    Prints CLI statistics regarding search results and elapsed time.

    Args:
        semantic_results (list): Results from the vector search.
        bm25_results (list): Results from the BM25 search.
        get_elapsed_func (callable): The measure_time return function to get elapsed time.
    """
    print(f"{cs.GREEN}Semantic results: {len(semantic_results)} documents{cs.RESET}")

    if bm25_results:
        print(f"{cs.GREEN}BM25 results: {len(bm25_results)} documents with score > 0{cs.RESET}")
    print(f"{cs.OKBLUE}Search complete. Time: {get_elapsed_func()} {cs.RESET}")
