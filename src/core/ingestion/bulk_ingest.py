import os
import sys

# Setup Path to import 'core'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from core.db.db_connection import db_connection
from core.ingestion.insert_pdf_chunks import insert_pdf

def ingest_folder(folder_path):
    print(f"--- Bulk Ingesting from: {folder_path} ---")
    
    if not os.path.exists(folder_path):
        print(f"Error: Folder not found: {folder_path}")
        return

    conn = db_connection()
    if not conn:
        print("Error: DB Connection Failed")
        return
    cursor = conn.cursor()

    files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
    print(f"Found {len(files)} PDFs. Processing...")

    for i, filename in enumerate(files):
        full_path = os.path.join(folder_path, filename)
        print(f"\n[{i+1}/{len(files)}] Processing: {filename}")
        
        try:
            success = insert_pdf(full_path, conn, cursor)
            if success:
                print(f"✅ Success: {filename}")
            else:
                print(f"❌ Failed/Skipped: {filename}")
                
        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")

    cursor.close()
    conn.close()
    print("\n--- Bulk Ingestion Complete ---")

if __name__ == "__main__":
    # Default folder: src/core/utils/pdf_2025 (where downloader put them)
    # Adjust relative path based on where you run this script
    # This script is in src/core/ingestion/
    
    target_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../docs/data/arxiv_pdfs"))
    ingest_folder(target_dir)
