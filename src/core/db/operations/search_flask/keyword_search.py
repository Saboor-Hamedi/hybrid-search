from utils.ColorScheme import ColorScheme
from utils.helper_functions import measure_time

from core.db.operations.keyword_queries import execute_keyword_query
from core.utils.console_stats import display_search_stats
from core.utils.rich_console import display_in_table

cs = ColorScheme()
def search_keyword(query: str, cursor, top_k: int=1000):
    if not query.strip():
        print(f"{cs.RED}Query cannot be empty.{cs.RESET}")
        return [], {}

    get_elapsed = measure_time()
    results, stats = execute_keyword_query(query, cursor, top_k)

    display_in_table(results, query=query, mode="keyword")
    display_search_stats([], results, get_elapsed, mode="keyword")
    return results, {}
