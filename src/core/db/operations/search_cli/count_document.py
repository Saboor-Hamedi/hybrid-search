import os
import sys

# NOTE: Since _execute_count only uses cursor, we don't strictly need conn in its signature.
# We ensure the path is set correctly for imports if this is a separate file.
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import psycopg2

from core.utils.ColorScheme import ColorScheme

cs = ColorScheme()

def _execute_count(cursor):
    """
    Worker function: Fetches the total number of documents from the database
    using the provided cursor. Raises exceptions on failure.
    """
    if not cursor:
        raise ValueError("Database cursor is not active or available.")

    # Use a try block to catch potential psycopg2 or SQL execution errors
    try:
        cursor.execute("SELECT COUNT(*) FROM document")
        result = cursor.fetchone()

        # Return the count (result[0]) or 0 if the query result is unexpectedly empty
        return result[0] if result and result[0] is not None else 0

    except psycopg2.Error as e:
        # Re-raise as a RuntimeError for centralized error reporting in main.py
        raise RuntimeError(f"Database query failed: {e}") from e

def get_document_count(cursor):
    """
    Presenter function: Calls the worker, handles display, and manages exceptions.
    This is the function main.py should call.
    """
    try:
        count = _execute_count(cursor)
        print(f"{cs.GREEN}Total Documents Indexed: {cs.BOLD}{count}{cs.RESET}")

    except Exception as e:
        print(f"{cs.RED}❌ Error getting document count: {e}{cs.RESET}")
        return 0
