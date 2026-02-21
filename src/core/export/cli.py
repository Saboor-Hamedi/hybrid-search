import json
import os
import sys
from datetime import datetime

# Ensure the script can find the local modules
# Current file: src/core/export/cli.py -> target: src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from core.db.db_connection import db_connection

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))

def export_documents_to_json(output_file="documents_export.json"):
    print(f"⏳ Connecting to database...")
    conn = db_connection()
    if not conn:
        print("❌ Failed to connect to database.")
        return

    try:
        cursor = conn.cursor()
        print(f"⏳ Fetching all documents from 'document' table...")
        
        # We only export the core logical columns
        cursor.execute("SELECT id, content, language, created_at FROM document ORDER BY id ASC")
        rows = cursor.fetchall()
        
        # Get column names
        colnames = [desc[0] for desc in cursor.description]
        
        # Convert to list of dicts
        documents = []
        for row in rows:
            documents.append(dict(zip(colnames, row)))
        
        print(f"✅ Successfully fetched {len(documents)} documents.")
        
        # Write to JSON
        print(f"⏳ Writing to {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(documents, f, indent=4, default=json_serial, ensure_ascii=False)
            
        print(f"✨ Export complete! File saved to: {os.path.abspath(output_file)}")

    except Exception as e:
        print(f"❌ An error occurred during export: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    # Get the project root (one level up from src)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    default_path = os.path.join(project_root, "documents_export.json")
    
    filename = sys.argv[1] if len(sys.argv) > 1 else default_path
    export_documents_to_json(filename)
