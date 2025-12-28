"""
Document Manager CLI front-end
All menu actions are implemented as separate functions and called cleanly.
"""

import os
import sys
import time

# Add parent folder to path for relative imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from db.db_connection import db_connection, get_db_cursor, get_model
from ingestion.insert_pdf_chunks import insert_pdf
from utils.menu import MENU, is_back, safe_input, safe_int_input

from core.db.operations.document_management import delete_document, insert_document
from core.db.operations.search_cli.count_document import get_document_count

# Flask search imports
from core.db.operations.search_flask.hybrid_search import search_hybrid
from core.db.operations.search_flask.keyword_search import search_keyword
from core.db.operations.search_flask.semantic_search import search_semantic
from core.utils.ColorScheme import ColorScheme

cs = ColorScheme()


# MENU DISPLAY
def display_menu() -> None:
    print("\n" + "=" * 60)
    print(f"{cs.BOLD}   DOCUMENT MANAGER & THESIS ENGINE   {cs.RESET}")
    print("=" * 60)
    print(f"{cs.GREEN}Available Actions:{cs.RESET}")
    for key, (title, desc) in MENU.items():
        print(f"  {cs.BOLD}[{key.upper()}]{cs.RESET} {title:<18} : {desc}")
    print("-" * 60)
    print(f"{cs.CYAN}Hint: Type '?' for detailed help, or 'b' to go back in any menu.{cs.RESET}")
    print("=" * 60)



# IMPORTS
import logging
from rich.progress import track
from rich.console import Console
# ... other imports ...

console = Console()

# LOGGING SETUP
logging.basicConfig(
    filename='cli_activity.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ...

# ACTION FUNCTIONS (Now self-contained)

def _get_db_context():
    """Helper to get fresh connection/cursor safely."""
    conn = db_connection()
    if not conn:
        print(f"{cs.RED}Error: Database connection failed.{cs.RESET}")
        return None, None
    return conn, conn.cursor()


def _action_insert(model) -> None:
    text = safe_input("Enter document text (or 'b' to go back): ")
    if is_back(text): return
    if not text:
        print(f"{cs.RED}Input cannot be empty.{cs.RESET}")
        return

    conn, cursor = _get_db_context()
    if not conn: return
    
    try:
        insert_document(text, conn, cursor, model)
        logging.info("Inserted document manually.")
    finally:
        cursor.close()
        conn.close()


def _action_pdf() -> None:
    path = safe_input("Enter PDF file or directory path (or 'b' to go back): ")
    if is_back(path): return
    
    # Clean path (remove quotes common in Windows copy-path)
    path = path.strip('"').strip("'")
    
    conn, cursor = _get_db_context()
    if not conn: return

    try:
        if os.path.isdir(path):
            console.print(f"[cyan]Directory detected. Scanning...[/cyan]")
            files = [f for f in os.listdir(path) if f.lower().endswith('.pdf')]
            
            if not files:
                console.print(f"[yellow]No PDF files found in {path}[/yellow]")
                return
                
            console.print(f"[green]Found {len(files)} PDFs. Starting bulk ingestion...[/green]")
            logging.info(f"Starting bulk ingest of {len(files)} files from {path}")
            
            success_count = 0
            # RICH PROGRESS BAR
            for filename in track(files, description="Ingesting PDFs..."):
                full_path = os.path.join(path, filename)
                try:
                    # insert_pdf manages generic printing, we suppress or let it flow?
                    # Ideally we capture output or trust it.
                    # For progress bar cleanliness, we might want fewer prints from insert_pdf.
                    if insert_pdf(full_path, conn, cursor):
                        success_count += 1
                except Exception as e:
                    logging.error(f"Failed to process {filename}: {e}")

            console.print(f"\n[bold green]Bulk Ingestion Complete: {success_count}/{len(files)} successful.[/bold green]")
            
        elif os.path.isfile(path):
            if insert_pdf(path, conn, cursor):
                logging.info(f"Inserted PDF: {path}")
        else:
             console.print(f"[red]File or directory not found: {path}[/red]")
             
    finally:
        cursor.close()
        conn.close()


def _action_delete() -> None:
    doc_id = safe_int_input("Enter document ID to delete (or 'b' to go back): ")
    if doc_id is None: return

    conn, cursor = _get_db_context()
    if not conn: return
    try:
        delete_document(doc_id, conn, cursor)
        logging.info(f"Deleted document {doc_id}")
    finally:
        cursor.close()
        conn.close()
        
def _action_count() -> None:
    conn, cursor = _get_db_context()
    if not conn: return
    try:
        get_document_count(cursor)
    finally:
        cursor.close()
        conn.close()


# MAIN LOOP
def main_menu() -> None:
    start_time = time.time()
    print(f"{cs.GREEN}Program started at {time.ctime(start_time)}{cs.RESET}")

    # --- Model Loading (Keep Global) ---
    model_start = time.time()
    with console.status("[bold green]Loading AI Model (this takes a moment)..."):
        model = get_model()
    
    print(f"{cs.GREEN}Model loaded in {time.time() - model_start:.4f}s{cs.RESET}")
    if not model:
        print(f"{cs.RED}Failed to load model. Exiting.{cs.RESET}")
        return

    # --- Startup Summary ---
    print(f"{cs.GREEN}Setup completed in {time.time() - start_time:.4f}s{cs.RESET}")

    # --- Interactive Loop ---
    try:
        while True:
            display_menu()
            choice = safe_input(
                f"{cs.GREEN}Your choice -> {cs.BOLD}[{' / '.join(k.upper() for k in MENU)}]{cs.UNDERLINE}: {cs.RESET}"
            ).lower()

            if not choice: continue

            # === I: Insert ===
            if choice in ("i", "insert"):
                _action_insert(model)

            # === H: Hybrid ===
            elif choice == "h":
                query = safe_input("Enter hybrid search query: ")
                if not is_back(query):
                    conn, cursor = _get_db_context()
                    if conn:
                        search_hybrid(query, conn, cursor, model)
                        conn.close()

            # === S: Semantic ===
            elif choice == "s":
                query = safe_input("Enter semantic search query: ")
                if not is_back(query):
                    conn, cursor = _get_db_context()
                    if conn:
                        search_semantic(query, conn, cursor, model)
                        conn.close()

            # === K: Keyword ===
            elif choice == "k":
                query = safe_input("Enter keyword search query: ")
                if not is_back(query):
                    conn, cursor = _get_db_context()
                    if conn:
                        search_keyword(query, cursor)
                        conn.close()

            # === P: Paragraph ===
            elif choice in ("p", "para"): # Explicit P key logic if MENU has it
                query = safe_input("Enter paragraph search query: ")
                if not is_back(query):
                    conn, cursor = _get_db_context()
                    if conn:
                         from core.utils.rich_console import display_in_paragraph
                         results, _ = search_hybrid(query, conn, cursor, model)
                         display_in_paragraph(results, query=query)
                         conn.close()

            # === U: Upload PDF ===
            elif choice in ("u", "upload", "pdf"):
                _action_pdf()

            # === E: Evaluate ===
            elif choice in ("e", "eval", "evaluate"):
                # Evaluate has its own independent DB logic inside run_evaluation usually?
                # Checked auto_eval.py: YES, it calls db_connection() itself.
                # So we just call the function.
                print(f"\n{cs.BOLD}--- Thesis Evaluation Engine ---{cs.RESET}")
                print(f"Modes: 'ai' (runs LLM judge) or 'data' (fast metrics only)")
                mode = safe_input("Enter mode [data/ai] (default: data): ").lower() or "data"
                if is_back(mode): continue
                
                limit_str = safe_input("Enter query limit (default: 5): ")
                if is_back(limit_str): continue
                limit = int(limit_str) if limit_str.isdigit() else 5
                
                try:
                    from experiments.auto_eval import run_evaluation
                    run_evaluation(mode, limit)
                except Exception as e:
                    logging.error(f"Eval Loop Error: {e}")
                    print(f"{cs.RED}Evaluation Error: {e}{cs.RESET}")

            # === T: Thesis Compare ===
            elif choice in ("t", "thesis", "compare"):
                 # Comparator also handles its own DB.
                from thesis_comparator import compare_algorithms
                while True:
                    query = safe_input("\n(Comparator) Enter query (or 'b' to back): ")
                    if is_back(query): break
                    if not query: continue
                    try:
                        compare_algorithms(query)
                    except Exception as e:
                         print(f"{cs.RED}Comparison Error: {e}{cs.RESET}")


            # === D: Delete ===
            elif choice in ("d", "delete"):
                _action_delete()

            # === C: Count ===
            elif choice in ("c", "count"):
                _action_count()

            # === ?: Help ===
            elif choice in ("?", "help"):
                _action_help()

            # === Q: Quit ===
            elif choice in ("q", "quit"):
                _action_quit()
            
            else:
                 print(f"{cs.RED}Invalid option.{cs.RESET}")

    except KeyboardInterrupt:
        print(f"\n{cs.YELLOW}Interrupted. Goodbye!{cs.RESET}")
    finally:
        # DB connections are local now, nothing to close globally
        pass


# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    main_menu()
