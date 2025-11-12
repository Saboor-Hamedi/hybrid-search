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

from core.db.operations.count_document import get_document_count
from core.db.operations.database_operations import paragraph_search, search
from core.db.operations.document_management import delete_document, insert_document
from core.db.operations.hybrid_search import search_hybrid
from core.db.operations.keyword_search import search_keyword
from core.db.operations.semantic_search import search_semantic

# from core.db.operations.hybrid_search import paragraph_search, search
from core.utils.ColorScheme import ColorScheme

cs = ColorScheme()


# --------------------------------------------------------------------------- #
# MENU DISPLAY
# --------------------------------------------------------------------------- #
def display_menu() -> None:
    print("\n" + "=" * 50)
    print(f"{cs.BOLD}DOCUMENT MANAGER MENU{cs.RESET}")
    print(f"{cs.GREEN}Options:{cs.RESET}")
    for key, (title, desc) in MENU.items():
        print(f"  {cs.BOLD}{key.upper()}{cs.RESET}: {title} — {desc}")
    print("=" * 50)


# --------------------------------------------------------------------------- #
# ACTION FUNCTIONS (all called from the menu)
# --------------------------------------------------------------------------- #
def _action_insert(conn, cursor, model) -> None:
    text = safe_input("Enter document text (or 'b' to go back): ")
    if is_back(text):
        return
    if not text:
        print(f"{cs.RED}Input cannot be empty.{cs.RESET}")
        return
    insert_document(text, conn, cursor, model)


# def _action_search(conn, cursor, model) -> None:
#     query = safe_input("Enter search query (prefix 'p ' for paragraph mode, or 'b' to go back): ")
#     if is_back(query):
#         return

#     if query.lower().startswith("p ") and len(query) > 2:

#         paragraph_search(query[2:].strip(), conn, cursor, model)
#     elif query.lower() == "p":
#         q = safe_input("Enter paragraph-mode query: ")
#         if not is_back(q):
#             paragraph_search(q, conn, cursor, model)
#     else:
#         search(query, conn, cursor, model)


def _action_pdf(conn, cursor) -> None:
    path = safe_input("Enter PDF file path (or 'b' to go back): ")
    if is_back(path):
        return
    if not os.path.isfile(path):
        print(f"{cs.RED}File not found: {path}{cs.RESET}")
        return
    insert_pdf(path, conn, cursor)


def _action_delete(conn, cursor) -> None:
    doc_id = safe_int_input("Enter document ID to delete (or 'b' to go back): ")
    if doc_id is None:
        return
    delete_document(doc_id, conn, cursor)


def _action_count(cursor) -> None:
    get_document_count(cursor)


def _action_quit() -> None:
    print(f"{cs.GREEN}Exiting program. Goodbye!{cs.RESET}")
    sys.exit(0)


# --------------------------------------------------------------------------- #
# MAIN LOOP – Calls the functions above
# --------------------------------------------------------------------------- #
def main_menu() -> None:
    start_time = time.time()
    print(f"{cs.GREEN}Program started at {time.ctime(start_time)}{cs.RESET}")

    # --- Database Connection ---
    db_start = time.time()
    conn = db_connection()
    if not conn:
        print(f"{cs.RED}Failed to connect to database. Exiting.{cs.RESET}")
        return
    cursor = get_db_cursor(conn)
    print(f"{cs.GREEN}Database connected in {time.time() - db_start:.4f}s{cs.RESET}")

    # --- Model Loading ---
    model_start = time.time()
    model = get_model()
    print(f"{cs.GREEN}Model loading call returned in {time.time() - model_start:.4f}s{cs.RESET}")
    if not model:
        print(f"{cs.RED}Failed to load model. Exiting.{cs.RESET}")
        if cursor is not None:
            cursor.close()
        conn.close()
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

            if not choice:
                continue

            # === I: Insert ===
            if choice in ("i", "insert"):
                _action_insert(conn, cursor, model)

            # === S: Search ===
            elif choice == "h":
                query = safe_input("Enter hybrid search query (or 'b' to go back): ")
                if is_back(query): continue
                search_hybrid(query, conn, cursor, model)

            elif choice == "s":
                query = safe_input("Enter semantic search query (or 'b' to go back): ")
                if is_back(query): continue
                search_semantic(query, conn, cursor, model)

            elif choice == "k":
                query = safe_input("Enter keyword search query (or 'b' to go back): ")
                if is_back(query): continue
                search_keyword(query, cursor)

            elif choice == "p":
                query = safe_input("Enter paragraph search query (or 'b' to go back): ")
                if is_back(query): continue
                # Reuse hybrid but show in paragraph
                from core.utils.rich_console import display_in_paragraph
                results, _ = search_hybrid(query, conn, cursor, model)
                display_in_paragraph(results, query=query)

            # === D: Delete ===
            elif choice in ("d", "delete"):
                _action_delete(conn, cursor)

            # === C: Count ===
            elif choice in ("c", "count"):
                _action_count(cursor)

            # === P: PDF ===
            elif choice in ("p", "pdf"):
                _action_pdf(conn, cursor)

            # === Q: Quit ===
            elif choice in ("q", "quit"):
                _action_quit()

            # === Invalid ===
            else:
                print(f"{cs.RED}Invalid option. Please try again.{cs.RESET}")

    except KeyboardInterrupt:
        print(f"\n{cs.YELLOW}Interrupted. Goodbye!{cs.RESET}")
    finally:
        # --- Cleanup ---
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            print(f"{cs.GREEN}Database connection closed.{cs.RESET}")


# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    main_menu()
