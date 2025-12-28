import contextlib
import os
import sys
from typing import Dict, List, Set, Tuple

# Setup path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from core.db.db_connection import db_connection, get_model
from core.db.operations.search_flask.semantic_search import search_semantic
from core.db.operations.search_flask.keyword_search import search_keyword
from core.db.operations.search_flask.hybrid_search import search_hybrid
from core.db.operations.search_flask.rrf_search import search_rrf
from core.db.operations.search_flask.ltr_search import search_ltr
from core.utils.ColorScheme import ColorScheme

console = Console()
cs = ColorScheme()

@contextlib.contextmanager
def suppress_stdout():
    """Helper to suppress internal prints from search functions."""
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout

def compare_algorithms(query: str, top_n: int = 5):
    """
    Runs the same query through all algorithms (inc. 3 fusion strategies + LTR) and displays a comparison table.
    """
    console.print(Panel(f"[bold cyan]Thesis Evaluation Bench[/]\n[white]Query: '{query}'[/]", expand=False))

    conn = db_connection()
    cursor = conn.cursor()
    model = get_model()

    # 1. Run all searches and track latency
    latencies = {}
    
    import time
    
    # Semantic
    start = time.time()
    sem_results, _ = search_semantic(query, conn, cursor, model, top_k=20)
    latencies["semantic"] = (time.time() - start) * 1000

    # Keyword
    start = time.time()
    key_results, _ = search_keyword(query, cursor, top_k=20)
    latencies["keyword"] = (time.time() - start) * 1000

    # Hybrid - Linear (Weighted)
    start = time.time()
    hyb_results, _ = search_hybrid(query, conn, cursor, model, top_k=20, fusion_strategy="linear")
    latencies["linear"] = (time.time() - start) * 1000

    # Hybrid - CombSUM
    start = time.time()
    sum_results, _ = search_hybrid(query, conn, cursor, model, top_k=20, fusion_strategy="combsum")
    latencies["combsum"] = (time.time() - start) * 1000

    # Hybrid - CombMNZ
    start = time.time()
    mnz_results, _ = search_hybrid(query, conn, cursor, model, top_k=20, fusion_strategy="combmnz")
    latencies["combmnz"] = (time.time() - start) * 1000

    # RRF
    start = time.time()
    rrf_results, _ = search_rrf(query, conn, cursor, model, top_k=20)
    latencies["rrf"] = (time.time() - start) * 1000

    # LTR (Learning to Rank)
    start = time.time()
    # Note: LTR re-ranks candidates, so we fetch top 20 final results from 50 candidates
    ltr_results, _ = search_ltr(query, conn, cursor, model, top_k=20, candidate_k=50)
    latencies["ltr"] = (time.time() - start) * 1000

    # 2. Extract Doc IDs and Ranks
    def get_rank_map(results):
        return {r[0]: idx + 1 for idx, r in enumerate(results)}

    sem_ranks = get_rank_map(sem_results)
    key_ranks = get_rank_map(key_results)
    hyb_ranks = get_rank_map(hyb_results)
    sum_ranks = get_rank_map(sum_results)
    mnz_ranks = get_rank_map(mnz_results)
    rrf_ranks = get_rank_map(rrf_results)
    ltr_ranks = get_rank_map(ltr_results)

    # 3. Create a unified set of all top Doc IDs across all methods
    all_top_ids: List[int] = []
    # Include LTR results in the candidate pool for the table
    for r_list in [sem_results, key_results, hyb_results, sum_results, mnz_results, rrf_results, ltr_results]:
        all_top_ids.extend([r[0] for r in r_list[:top_n]])
    
    unique_ids = list(dict.fromkeys(all_top_ids)) # Preserve order of first appearance

    # 4. Build the Comparison Table
    table = Table(
        title=f"\n[bold white]Algorithm Benchmarking & Side-by-Side Comparison (Top {top_n})[/]", 
        header_style="bold magenta", 
        border_style="cyan",
        box=box.DOUBLE_EDGE,
        show_lines=True
    )
    table.add_column("Doc", justify="center", style="dim", width=4)
    table.add_column("Sem.", justify="center", width=4)
    table.add_column("Key.", justify="center", width=4)
    table.add_column("Linear", justify="center", width=6)
    table.add_column("Comb\nSUM", justify="center", width=6)
    table.add_column("Comb\nMNZ", justify="center", width=6)
    table.add_column("RRF", justify="center", width=4)
    table.add_column("LTR\n(AI)", justify="center", width=4, style="bold yellow")
    table.add_column("Summary Content", width=50, style="dim italic")

    # Sort primarily by LTR rank (if present) or RRF logic
    # Giving LTR visual priority
    sorted_ids = sorted(unique_ids, key=lambda x: ltr_ranks.get(x, 999))

    for doc_id in sorted_ids:
        s_rank = sem_ranks.get(doc_id, "-")
        k_rank = key_ranks.get(doc_id, "-")
        h_rank = hyb_ranks.get(doc_id, "-")
        sum_rank = sum_ranks.get(doc_id, "-")
        mnz_rank = mnz_ranks.get(doc_id, "-")
        r_rank = rrf_ranks.get(doc_id, "-")
        l_rank = ltr_ranks.get(doc_id, "-")

        # Get content
        content = "Unknown Document"
        for r_list in [sem_results, key_results, hyb_results, rrf_results]:
            found = [r[1] for r in r_list if r[0] == doc_id]
            if found:
                content = found[0][:100].replace("\n", " ").strip() + "..."
                break

        # Coloring logic
        def fmt_rank(r):
            if r == "-": return "[dim]-[/]"
            if int(r) <= 3: return f"[bold green]{r}[/]"
            return str(r)

        table.add_row(
            str(doc_id),
            fmt_rank(s_rank),
            fmt_rank(k_rank),
            fmt_rank(h_rank),
            fmt_rank(sum_rank),
            fmt_rank(mnz_rank),
            fmt_rank(r_rank),
            fmt_rank(l_rank),
            content
        )

    console.print("\n")
    console.print(table)
    
    # 5. Summary Insights & Performance
    perf_table = Table(title="Performance Measurement", box=box.SIMPLE)
    perf_table.add_column("Algorithm", style="cyan")
    perf_table.add_column("Latency (ms)", justify="right", style="green")
    
    for m in ["semantic", "keyword", "linear", "combsum", "combmnz", "rrf", "ltr"]:
        perf_table.add_row(m.capitalize(), f"{latencies[m]:.1f}ms")
        
    console.print(perf_table)

    console.print("\n[bold cyan]Analysis Summary:[/]")
    
    s_top = set(list(sem_ranks.keys())[:5])
    r_top = set(list(rrf_ranks.keys())[:5])
    l_top = set(list(ltr_ranks.keys())[:5])
    
    overlap_sr = len(s_top.intersection(r_top))
    overlap_sl = len(s_top.intersection(l_top))
    
    console.print(f" • [white]RRF Alignment:[/] Overlaps with [green]{overlap_sr}/5[/] Semantic top hits.")
    console.print(f" • [white]LTR Alignment:[/] Overlaps with [green]{overlap_sl}/5[/] Semantic top hits.")
    
    if ltr_results and sem_results:
        ltr_top = ltr_results[0][0]
        sem_top = sem_results[0][0]
        if ltr_top != sem_top:
             console.print(f" • [yellow]AI Re-Rank Change:[/] LTR chose Doc [bold white]#{ltr_top}[/] over Semantic's [bold white]#{sem_top}[/].")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    console.clear()
    console.print(Panel.fit("[bold green]Thesis Algorithm Bench Loaded[/]\n[dim]Type 'exit' or 'q' to stop.[/]", border_style="green"))
    
    while True:
        query = console.input("\n[bold yellow]Enter query to compare:[/] ").strip()
        
        if query.lower() in ["exit", "q", "quit"]:
            console.print("[bold red]Evaluation Bench Closed.[/]")
            break
            
        if not query:
            query = "artificial intelligence"
            console.print(f"[dim]Empty input. Using default: '{query}'[/]")
        
        try:
            compare_algorithms(query)
            console.print("\n" + "─" * 80 + "\n")
        except KeyboardInterrupt:
            break
        except Exception as e:
            console.print(f"[bold red]System Error:[/] {str(e)}")
