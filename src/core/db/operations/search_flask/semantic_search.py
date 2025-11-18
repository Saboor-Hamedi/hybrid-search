from utils.ColorScheme import ColorScheme
from utils.helper_functions import measure_time

from core.db.operations.search_queries import execute_vector_query
from core.utils.console_stats import display_search_stats
from core.utils.rich_console import display_in_table

cs = ColorScheme()

TRASHOLD = 0.4
TOP_K = 50
def search_semantic(query: str, conn, cursor, model, top_k=TOP_K, threshold=TRASHOLD):
    if not query.strip():
        print(f"{cs.RED}Query cannot be empty.{cs.RESET}")
        return [], {}

    get_elapsed = measure_time()
    results = execute_vector_query(query, conn, cursor, model, top_k, threshold)

    display_in_table(results, query=query, mode="semantic")
    display_search_stats(results, [],  get_elapsed, mode="semantic")

    return results, {}
