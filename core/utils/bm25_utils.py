from rank_bm25 import BM25Okapi
from core.utils.ColorScheme import ColorScheme

cs = ColorScheme()
bm25_corpus = []
bm25_index = None


def update_bm25_index(cursor, normalize_content):
    global bm25_index, bm25_corpus

    cursor.execute("SELECT id, content FROM document")
    rows = cursor.fetchall()

    # 1. Create corpus of (doc_id, normalized_content)
    bm25_corpus = [(row[0], normalize_content(row[1])) for row in rows]

    # 2. Tokenize the content for the index
    tokenized_contents = [content.split() for _, content in bm25_corpus]

    # 3. Filter out items where tokenization resulted in an empty list
    valid_tokenized = [tokens for tokens in tokenized_contents if tokens]
    # print(
    #     f"{cs.CYAN}📊 DEBUG: After filtering, {len(valid_tokenized)} valid documents{cs.RESET}"
    # )

    # Filter out empty documents

    if not valid_tokenized:
        bm25_index = None
        bm25_corpus = []  # Ensure corpus is also cleared if no valid documents
        return

    # Re-align corpus to only contain documents that were actually indexed (optional but safer)
    # The current approach is fine if you know all rows have content.

    bm25_index = BM25Okapi(valid_tokenized)
    print(
        f"{cs.GREEN}✅ BM25 index updated with {len(valid_tokenized)} documents{cs.RESET}"
    )
