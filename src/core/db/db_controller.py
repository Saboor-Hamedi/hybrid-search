# db_controller.py
from typing import List, Optional

import psycopg2


def update_record(conn, cursor, doc_id: int, content: str, language: str = "en", embedding: Optional[List[float]] = None) -> bool:
    """Update a document record in the database."""
    try:
        # Check if document exists first
        cursor.execute("SELECT id FROM document WHERE id = %s", (doc_id,))
        if not cursor.fetchone():
            return False

        # Update document table
        cursor.execute("""
            UPDATE document
            SET content = %s,
                languages = %s
            WHERE id = %s
        """, (content, language, doc_id))

        # Update embedding if provided
        # Check if embedding record exists
        cursor.execute("SELECT id FROM document_embedding WHERE doc_id = %s", (doc_id,))
        if cursor.fetchone():
            # Update existing embedding
            cursor.execute("""
                UPDATE document_embedding
                SET embedding = %s
                WHERE doc_id = %s
            """, (embedding, doc_id))
        else:
            # Insert new embedding
            cursor.execute("""
                INSERT INTO document_embedding (doc_id, embedding)
                VALUES (%s, %s)
            """, (doc_id, embedding))

        return cursor.rowcount > 0

    except psycopg2.Error as e:
        conn.rollback()
        raise e
    except Exception as e:
        conn.rollback()
        raise e
