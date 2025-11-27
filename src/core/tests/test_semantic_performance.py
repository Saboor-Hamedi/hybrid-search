"""
Test script to compare semantic search performance with different configurations
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from core.db.db_connection import db_connection, get_model
from core.db.operations.search_flask.semantic_search import search_semantic
from core.utils.ColorScheme import ColorScheme
import time

cs = ColorScheme()

def test_semantic_search():
    """Test semantic search with various queries"""
    
    # Test queries covering different scenarios
    test_queries = [
        "python programming",
        "database connection error",
        "machine learning algorithms",
        "web development tutorial",
        "data science",
    ]
    
    print(f"\n{cs.CYAN}{'='*70}{cs.RESET}")
    print(f"{cs.CYAN}  SEMANTIC SEARCH PERFORMANCE TEST{cs.RESET}")
    print(f"{cs.CYAN}{'='*70}{cs.RESET}\n")
    
    # Connect to database
    conn = db_connection()
    if not conn:
        print(f"{cs.RED}Failed to connect to database{cs.RESET}")
        return
    
    cursor = conn.cursor()
    model = get_model()
    
    if not model:
        print(f"{cs.RED}Failed to load model{cs.RESET}")
        return
    
    print(f"{cs.GREEN}✓ Database connected{cs.RESET}")
    print(f"{cs.GREEN}✓ Model loaded{cs.RESET}\n")
    
    # Test different thresholds
    thresholds = [0.25, 0.4, 0.6]
    
    for threshold in thresholds:
        print(f"\n{cs.YELLOW}{'─'*70}{cs.RESET}")
        print(f"{cs.YELLOW}Testing with THRESHOLD = {threshold}{cs.RESET}")
        print(f"{cs.YELLOW}{'─'*70}{cs.RESET}\n")
        
        total_results = 0
        total_time = 0
        
        for query in test_queries:
            start = time.time()
            
            # Run search
            results, _ = search_semantic(
                query, 
                conn, 
                cursor, 
                model, 
                top_k=100, 
                threshold=threshold
            )
            
            elapsed = (time.time() - start) * 1000
            total_time += elapsed
            total_results += len(results)
            
            # Display results
            print(f"\n{cs.CYAN}Query:{cs.RESET} '{query}'")
            print(f"{cs.GREEN}Results:{cs.RESET} {len(results)} | {cs.GREEN}Time:{cs.RESET} {elapsed:.2f}ms")
            
            if results:
                top_score = results[0][2]
                avg_score = sum(r[2] for r in results) / len(results)
                print(f"{cs.GREEN}Top Score:{cs.RESET} {top_score:.4f} | {cs.GREEN}Avg Score:{cs.RESET} {avg_score:.4f}")
                
                # Show top 3 results
                print(f"\n{cs.MAGENTA}Top 3 Results:{cs.RESET}")
                for i, (doc_id, content, score, lang, date) in enumerate(results[:3], 1):
                    preview = content[:80].replace('\n', ' ')
                    print(f"  {i}. [{score:.4f}] {preview}...")
            else:
                print(f"{cs.RED}No results found{cs.RESET}")
        
        # Summary for this threshold
        avg_results = total_results / len(test_queries)
        avg_time = total_time / len(test_queries)
        
        print(f"\n{cs.YELLOW}Summary for threshold {threshold}:{cs.RESET}")
        print(f"  Avg Results per Query: {avg_results:.1f}")
        print(f"  Avg Query Time: {avg_time:.2f}ms")
        print(f"  Total Results: {total_results}")
    
    cursor.close()
    conn.close()
    
    print(f"\n{cs.CYAN}{'='*70}{cs.RESET}")
    print(f"{cs.GREEN}✓ Test completed{cs.RESET}\n")


if __name__ == "__main__":
    test_semantic_search()
