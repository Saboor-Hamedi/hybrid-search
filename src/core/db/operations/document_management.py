# Must read: This file contains the insert_document function, which is a core database operation.


import os
import sys

# Ensure the parent directory is in sys.path for relative imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


import utils.bm25_utils as bm25_utils
from utils.helper_functions import check_if_empty_input, measure_time
from utils.languages import detect_language
from utils.text_properties import normalize_content

from core.utils.ColorScheme import ColorScheme

cs = ColorScheme()


def insert_document(content, conn, cursor, model, commit= True, silent=False):
    # Check for empty input
    if check_if_empty_input(content):
        if not silent:
            print(f"{cs.RED}❌ Input cannot be empty.{cs.RESET}")
        return False

    get_elapsed = measure_time()
    nor_content = normalize_content(content)
    language = detect_language(nor_content)
    try:
        # Generate embedding
        emb = model.encode(nor_content).tolist()

        # Insert content and FTS vector (PostgreSQL)
        cursor.execute(
            "INSERT INTO document (content, languages, content_tsvector) VALUES (%s, %s, to_tsvector('simple', %s)) RETURNING id;",
            (nor_content, language, nor_content),
        )
        result = cursor.fetchone()
        if result is None:
            if not silent:
                print(f"{cs.RED}❌ INSERT failed - no ID returned{cs.RESET}")
            return False
        doc_id = result[0]

        # 3. Insert embedding (pgvector)
        cursor.execute(
            "INSERT INTO document_embedding (doc_id, embedding) VALUES (%s, %s)",
            (doc_id, emb),
        )
        # 4. Commit and notify BM25 utility
        if commit:
            conn.commit()
            bm25_utils.needs_update = True
            if not silent:
                print(
                    f"{cs.GREEN}✅ Inserted document (language: {language}). Time: {get_elapsed()}s {cs.RESET}"
                )
        else:
            if not silent:
                print(
                    f"{cs.YELLOW}📝 Queued for batch (language: {language}). Time: {get_elapsed()}s {cs.RESET}"
                )
        return True

    except Exception as e:
        print(f"{cs.RED}❌ Error after {get_elapsed()}s. Error: {e}{cs.RESET}")
        print(f"{cs.YELLOW}   Content: '{nor_content[:80]}...'{cs.RESET}")
        conn.rollback()
        return False


