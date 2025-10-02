import os
import sys
import time

# Ensure the parent directory is in sys.path for relative imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from db.db_connection import db_connection
from models.ai_model import get_embedder
from utils.text_properties import normalize_content

# from utils.bm25_utils import update_bm25_index, bm25_index, bm25_corpus
import utils.bm25_utils as bm25_utils

from core.utils.rich_console import display_results
from utils.helper_functions import check_if_empty_input
from utils.languages import detect_language
from utils.ColorScheme import ColorScheme

cs = ColorScheme()

# Connect to DB
conn = db_connection()
cursor = conn.cursor() if conn else None
model = get_embedder("paraphrase-multilingual-MiniLM-L12-v2")


# call the ColorScheme with re here
DEFAULT_TOP_K = 100
DEFAULT_THRESHOLD = 0.4
BM25_WEIGHT = 0.5


def measure_time():
    start = time.time()
    return lambda: time.time() - start


def insert_document(content, conn, cursor, model, commit=True, silent=False):
    if check_if_empty_input(content):
        if not silent:
            print(f"{cs.RED}❌ Input cannot be empty.{cs.RESET}")
        return False

    start_time = time.time()
    nor_content = normalize_content(content)
    language = detect_language(nor_content)

    try:
        emb = model.encode(nor_content).tolist()
        cursor.execute(
            "INSERT INTO document (content, languages) VALUES (%s, %s) RETURNING id;",
            (nor_content, language),
        )
        result = cursor.fetchone()
        if result is None:
            if not silent:
                print(f"{cs.RED}❌ INSERT failed - no ID returned{cs.RESET}")
            return False

        doc_id = result[0]
        cursor.execute(
            "INSERT INTO document_embedding (doc_id, embedding) VALUES (%s, %s)",
            (doc_id, emb),
        )

        # CONDITIONAL COMMIT
        if commit:
            conn.commit()
            bm25_utils.update_bm25_index(cursor, normalize_content)  # Update BM25 index
            elapsed_time = time.time() - start_time
            if not silent:
                print(
                    f"{cs.GREEN}✅ Inserted document (language: {language}). Time: {elapsed_time:.2f}s{cs.RESET}"
                )
        else:
            if not silent:
                # SILENT MODE: Don't print anything for batch operationss
                elapsed_time = time.time() - start_time
                print(
                    f"{cs.YELLOW}📝 Queued for batch (language: {language}). Time: {elapsed_time:.2f}s{cs.RESET}"
                )
        return True
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"{cs.RED}❌ Error after {elapsed_time:.2f}s: {e}{cs.RESET}")
        print(f"{cs.YELLOW}   Content: '{nor_content[:80]}...'{cs.RESET}")
        conn.rollback()
        return False


# Search function


def search(
    query, top_k=DEFAULT_TOP_K, threshold=DEFAULT_THRESHOLD, bm25_weight=BM25_WEIGHT
):
    """
    Performs a hybrid search combining Semantic (Vector) and BM25 (Keyword) search.
    """
    if check_if_empty_input(query):
        print(f"{cs.RED}Input cannot be empty.{cs.RESET}")
        return []

    get_eplased = measure_time()
    nor_query = normalize_content(query)

    try:
        # --- 1. Semantic Search (PostgreSQL) ---
        query_vec = model.encode(nor_query).tolist()
        vec_str = f"[{','.join(map(str, query_vec))}]"

        cursor.execute(
            """
            SELECT d.id, d.content, (1 - (e.embedding <=> %s::vector)) AS similarity, 
                   d.languages, d.created_at
            FROM document d
            JOIN document_embedding e ON d.id = e.doc_id
            WHERE (1 - (e.embedding <=> %s::vector)) >= %s
            ORDER BY e.embedding <=> %s::vector
            LIMIT %s
        """,
            (vec_str, vec_str, threshold, vec_str, top_k * 2),
        )
        rows = cursor.fetchall()
        semantic_results = [
            (row[0], row[1], float(row[2]), row[3], row[4]) for row in rows
        ]

        # --- 2. Hybrid Search (or fallback) ---
        bm25_utils.update_bm25_index(cursor, normalize_content)

        if bm25_utils.bm25_index is None or not bm25_utils.bm25_corpus:
            results = semantic_results
            bm25_results = []
        else:
            # Get BM25 scores
            bm25_scores = bm25_utils.bm25_index.get_scores(nor_query.split())
            bm25_results = [
                (doc_id, content, bm25_scores[i])
                for i, (doc_id, content) in enumerate(bm25_utils.bm25_corpus)
            ]
            bm25_results = [r for r in bm25_results if r[2] > 0]

            # Combine scores
            combined_results = {}
            max_semantic = (
                max([r[2] for r in semantic_results] + [0.01])
                if semantic_results
                else 0.01
            )
            max_bm25 = (
                max([r[2] for r in bm25_results] + [0.01]) if bm25_results else 0.01
            )

            # Add semantic results
            for doc_id, content, score, lang, created in semantic_results or []:
                combined_results[doc_id] = (
                    content,
                    score / max_semantic * bm25_weight,
                    lang,
                    created,
                )

            # Add BM25 results
            bm25_term_weight = 1 - bm25_weight
            for doc_id, content, score in bm25_results or []:
                normalized_bm25_score = (
                    score / max_bm25 * bm25_term_weight if max_bm25 > 0 else 0
                )

                if doc_id in combined_results:
                    current_content, current_score, current_lang, current_created = (
                        combined_results[doc_id]
                    )
                    combined_results[doc_id] = (
                        current_content,
                        current_score + normalized_bm25_score,
                        current_lang,
                        current_created,
                    )
                else:
                    combined_results[doc_id] = (
                        content,
                        normalized_bm25_score,
                        None,
                        None,
                    )

            results = [
                (doc_id, content, score, lang, created)
                for doc_id, (content, score, lang, created) in combined_results.items()
            ]
            results.sort(key=lambda x: x[2], reverse=True)

    except Exception as e:
        print(f"{cs.RED}Error during search: {e}{cs.RESET}")
        return []

    if not results:
        print(f"{cs.RED}No relevant results found.{cs.RESET}")
        return []
    # Display results
    display_results(results[:top_k], query=query)

    # Clean output
    print(f"{cs.GREEN}Semantic results: {len(semantic_results)} documents{cs.RESET}")
    if bm25_results:
        print(
            f"{cs.GREEN}BM25 results: {len(bm25_results)} documents with score > 0{cs.RESET}"
        )

    print(
        f"\n{cs.OKBLUE}Search complete. {len(results[:top_k])} results shown. Time: {get_eplased():.2f}s{cs.RESET}"
    )

    return results[:top_k]
