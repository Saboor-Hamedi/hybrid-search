# main.py
import os
import sys
import time

# Ensure the parent directory is in sys.path for relative imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from db.count_document import get_document_count
from db.database_operations import insert_document, paragraph_search, search
from db.db_connection import db_connection, get_db_cursor, get_model
from ingestion.insert_pdf_chunks import insert_pdf
from utils.helper_functions import go_back

from core.utils.ColorScheme import ColorScheme

cs = ColorScheme()
# print("Hello wordl, from main.py!")
count_options = ["count", "c"]


def display_menu():
    print("\n" + "=" * 50)
    print(f"{cs.BOLD}DOCUMENT MANAGER MENU{cs.RESET}")
    print(f"{cs.GREEN}Options:{cs.RESET}")
    print("  [I]nsert: Add new document text manually.")
    print("  [S]earch: Query and retrieve documents.")
    print("  [C]ount:  Query and count documents.")
    print("  [P]df:    Extract and insert from a PDF file.")
    print("  [B]ack:   Go back to previous menu.")
    print("  [Q]uit:   Exit the program.")
    print("=" * 50)


def main_menu():
    """Main interactive loop."""

    # --- Initial Timer Start ---
    start_time = time.time()
    print(f"{cs.GREEN}⏳ Program started at {time.ctime(start_time)}{cs.RESET}")

    # --- 1. Database Connection ---
    db_start_time = time.time() # Start timer for DB
    conn = db_connection()
    if not conn:
        print(f"{cs.RED}❌ Failed to connect to database. Exiting.{cs.RESET}")
        return

    cursor = get_db_cursor(conn)
    db_elapsed = time.time() - db_start_time
    print(f"{cs.GREEN}✅ Database connected in {db_elapsed:.4f} seconds.{cs.RESET}") # Report individual time

    # --- 2. Model Loading ---
    model_start_time = time.time() # Start timer for Model
    model = get_model()

    model_elapsed = time.time() - model_start_time
    # NOTE: The output from get_model() already reports its time,
    # but this confirms the total time taken for the call.
    print(f"{cs.GREEN}✅ Model loading call returned in {model_elapsed:.4f} seconds.{cs.RESET}")

    if not model:
        print(f"{cs.RED}❌ Failed to load model. Exiting.{cs.RESET}")
        if cursor: cursor.close()
        if conn: conn.close()
        return

    # --- 3. Total Startup Time ---
    total_start_uptime = time.time() - start_time
    print(f"{cs.GREEN}✅ Setup completed in {total_start_uptime:.4f} seconds.{cs.RESET}")
    try:
        while True:
            display_menu()
            try:
                action = (
                    input(
                        f"{cs.GREEN}Your choice -> {cs.BOLD}[I - S - Count(c) - PDF - Q]{cs.UNDERLINE}: {cs.RESET}"
                    )
                    .strip()
                    .lower()
                )
            except (EOFError, KeyboardInterrupt):
                print(f"\n{cs.YELLOW}Exiting program.{cs.RESET}")
                break

            if action == "i":
                try:
                    text = input("Enter document text: ").strip()
                    if go_back(text):
                        continue
                    insert_document(text, conn, cursor, model)
                except (EOFError, KeyboardInterrupt):
                    print(f"\n{cs.YELLOW}Cancelled insert operation.{cs.RESET}")
                    continue

            elif action == "s":
                try:
                    query = input(
                        "Enter search query (or 'p [query]' for paragraph mode): "
                    ).strip()
                    if go_back(query):
                        continue

                    # Check for paragraph mode using 'p ' prefix
                    if query.startswith("p ") and len(query) > 2:
                        actual_query = query[2:].strip()
                        paragraph_search(actual_query, conn, cursor, model)
                    elif query == "p":
                        # If only 'p' was entered, ask for the query
                        actual_query = input(
                            "Enter search query for paragraph mode: "
                        ).strip()
                        if go_back(actual_query):
                            continue
                        paragraph_search(actual_query, conn, cursor, model)
                    else:
                        # Regular search
                        search(query, conn, cursor, model)
                except (EOFError, KeyboardInterrupt):
                    print(f"\n{cs.YELLOW}Cancelled search operation.{cs.RESET}")
                    continue
            elif action == "paragraphs":
                try:
                    query = input("Enter search query: ").strip()
                    if go_back(query):
                        continue

                    paragraph_search(query, conn, cursor, model)
                except (EOFError, KeyboardInterrupt):
                    print(f"\n{cs.YELLOW}Cancelled search operation.{cs.RESET}")
                    continue
                # Added option to count documents

            elif action in count_options:
                try:
                    count = get_document_count(conn, cursor)
                    print(f"{cs.GREEN}Number of documents: {count}{cs.RESET}")
                except (EOFError, KeyboardInterrupt):
                    print(f"\n{cs.YELLOW}Cancelled search operation.{cs.RESET}")
                    continue

            elif action == "pdf":
                try:
                    file_path = input("Enter PDF file path: ").strip()
                    if go_back(file_path):
                        continue
                    insert_pdf(file_path, conn, cursor)
                except (EOFError, KeyboardInterrupt):
                    print(f"\n{cs.YELLOW}Cancelled PDF operation.{cs.RESET}")
                    continue

            elif action == "q":
                break
            else:
                print(
                    f"{cs.RED}Invalid option. Please choose I, S, PDF, or Q.{cs.RESET}"
                )

    finally:
        # Clean up resources
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            print(f"{cs.GREEN}✅ Database connection closed.{cs.RESET}")


if __name__ == "__main__":
    main_menu()
