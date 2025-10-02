import os
import sys

# Ensure the parent directory is in sys.path for relative imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
# from curses import raw
from db.db_connection import db_connection
from db.database_operations import insert_document, search

# from db.database_operations import insert_document
from models.ai_model import get_embedder

from utils.helper_functions import go_back

from ingestion.insert_pdf_chunks import insert_pdf

from core.utils.ColorScheme import ColorScheme

cs = ColorScheme()

# # Connect to DB
conn = db_connection()
cursor = conn.cursor() if conn else None
model = get_embedder("paraphrase-multilingual-MiniLM-L12-v2")

# main


def display_menu():
    print(f"\n" + "=" * 50)
    print(f"{cs.BOLD}DOCUMENT MANAGER MENU{cs.RESET}")
    # print(f"=" * 50)

    print(f"{cs.GREEN}Options:{cs.RESET}")
    print("  [I]nsert: Add new document text manually.")
    print("  [S]earch: Query and retrieve documents.")
    print("  [P]df:    Extract and insert from a PDF file.")
    print("  [B]ack:   Go back to previous menu.")
    print("  [Q]uit:   Exit the program.")
    print("=" * 50)


def main_menu(conn, cursor, model):
    """Main interactive loop."""

    while True:
        display_menu()
        action = (
            input(
                f"{cs.GREEN}Your choice -> {cs.BOLD}[I - S - PDF - B - Q]{cs.UNDERLINE}: {cs.RESET}"
            )
            .strip()
            .lower()
        )

        if action == "i":
            text = input("Enter document text: ").strip()
            if go_back(text):
                continue
            insert_document(text, conn, cursor, model)

        elif action == "s":
            query = input("Enter search query: ").strip()
            if go_back(query):
                continue
            search(query)

        elif action == "pdf":
            file_path = input("Enter PDF file path: ").strip()
            if go_back(file_path):
                continue
            insert_pdf(file_path, conn, cursor)
        elif action == "q":
            break


if __name__ == "__main__":
    main_menu(conn, cursor, model)
