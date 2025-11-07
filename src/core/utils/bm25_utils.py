from rank_bm25 import BM25Okapi
from core.utils.ColorScheme import ColorScheme

cs = ColorScheme()
bm25_corpus = []
bm25_index = None
needs_update = True


def update_bm25_index(cursor, normalize_content):
    global bm25_index, bm25_corpus, needs_update

    # Optional skip rebuilding if not change has made in dat
    if not needs_update and bm25_index is not None:
        return

    cursor.execute("SELECT id, content FROM document")
    rows = cursor.fetchall()
    # 1. Create corpus of (doc_id, normalized_content)
    bm25_corpus = [(row[0], normalize_content(row[1])) for row in rows]

    # 2. Tokenize the content for the index
    tokenized_contents = [content.split() for _, content in bm25_corpus]

    # 3. Filter out items where tokenization resulted in an empty list
    valid_tokenized = [tokens for tokens in tokenized_contents if tokens]

    # Filter out empty documents

    if not valid_tokenized:
        bm25_index = None
        bm25_corpus = []  # Ensure corpus is also cleared if no valid documents
        return

    bm25_index = BM25Okapi(valid_tokenized)
    needs_update = False
    print(
        f"{cs.GREEN}✅ BM25 index updated with {len(valid_tokenized)} documents{cs.RESET}"
    )
