import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from core.db.db_connection import db_connection, get_model
from core.db.operations.search_queries import execute_vector_query
from core.utils.ColorScheme import ColorScheme

cs = ColorScheme()

def test_search():
    print(f"{cs.CYAN}Initializing DB connection...{cs.RESET}")
    conn = db_connection()
    cursor = conn.cursor()
    
    print(f"{cs.CYAN}Loading model...{cs.RESET}")
    model = get_model()
    
    query = "works"
    threshold = 0.65
    top_k = 10
    
    print(f"\n{cs.CYAN}Running search for '{query}' with threshold {threshold}...{cs.RESET}")
    
    # We use execute_vector_query directly to see raw semantic scores
    results = execute_vector_query(query, conn, cursor, model, top_k, threshold)
    
    print(f"\n{cs.GREEN}Results:{cs.RESET}")
    if not results:
        print("No results found.")
    
    for r in results:
        # r = (doc_id, content, score, language, created_at)
        doc_id = r[0]
        content = r[1][:50].replace('\n', ' ')
        score = r[2]
        print(f"ID: {doc_id} | Score: {score:.4f} | Content: {content}...")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    test_search()
