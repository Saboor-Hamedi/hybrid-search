from utils.ColorScheme import ColorScheme

cs = ColorScheme()
MENU = {
    "i": ("Insert", "Add new document text manually."),
    "h": ("Hybrid Search", "Search using both semantic + keyword (BM25)."),
    "s": ("Semantic Search", "Search using AI embeddings (vector similarity)."),
    "k": ("Keyword Search", "Traditional full-text search (Postgres FTS)."),
    "p": ("Paragraph Search", "Show results in readable paragraphs."),
    "d": ("Delete", "Delete a document by ID."),
    "c": ("Count", "Show total number of documents."),
    "q": ("Quit", "Exit the program."),
}

def safe_input(promt)-> str:
    try:
        return input(promt).strip()
    except (EOFError, KeyboardInterrupt):
        print(f"\n{cs.YELLOW}Operation cancelled.{cs.RESET}")
        return ""

def safe_int_input(prompt: str) -> int | None:
    """Return int or None on error / cancel."""
    raw = safe_input(prompt)
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        print(f"{cs.RED}Please enter a valid integer.{cs.RESET}")
        return None

def is_back(text: str) -> bool:
    from utils.helper_functions import go_back
    return go_back(text)


