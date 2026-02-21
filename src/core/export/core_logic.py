import json
import os
import time
from datetime import datetime
from core.db.db_connection import db_connection

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))

def run_export_task(task_id: str, export_tasks_dict: dict):
    """
    Background worker to fetch documents in batches and export to JSON.
    Updates the shared status dictionary 'export_tasks_dict'.
    """
    conn = db_connection()
    if not conn:
        export_tasks_dict[task_id] = {"progress": 0, "status": "failed", "error": "DB connection failed"}
        return

    try:
        cursor = conn.cursor()
        export_tasks_dict[task_id] = {"progress": 5, "status": "processing", "message": "Fetching document count..."}
        
        # 1. Get total count
        cursor.execute("SELECT COUNT(*) FROM document")
        total_count = cursor.fetchone()[0]
        
        if total_count == 0:
            export_tasks_dict[task_id] = {"progress": 100, "status": "failed", "error": "No documents found in database to export."}
            return

        # Simple cleanup logic: remove older files in temp_exports (older than 1 hour)
        temp_dir = "temp_exports"
        if os.path.exists(temp_dir):
            try:
                now = time.time()
                for filename in os.listdir(temp_dir):
                    filepath = os.path.join(temp_dir, filename)
                    if os.path.isfile(filepath) and now - os.path.getmtime(filepath) > 3600:
                        os.remove(filepath)
            except Exception as cleanup_err:
                pass

        # 2. Fetch in chunks to track progress
        batch_size = 500
        documents = []
        
        export_tasks_dict[task_id] = {"progress": 10, "status": "processing", "message": f"Exporting {total_count} documents..."}

        for i in range(0, total_count, batch_size):
            cursor.execute(
                "SELECT id, content, language, created_at FROM document ORDER BY id ASC LIMIT %s OFFSET %s",
                (batch_size, i)
            )
            rows = cursor.fetchall()
            colnames = [desc[0] for desc in cursor.description]
            
            for row in rows:
                documents.append(dict(zip(colnames, row)))
            
            # Calculate progress (from 10 to 90%)
            progress = 10 + int((len(documents) / total_count) * 80)
            export_tasks_dict[task_id]["progress"] = progress
            
            # Optional sleep to make progress visible in small DBs
            if total_count < 100:
                time.sleep(0.5)

        # 3. Write to temporary file
        temp_dir = "temp_exports"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            
        file_name = f"export_{task_id}_{int(time.time())}.json"
        file_path = os.path.join(temp_dir, file_name)
        
        export_tasks_dict[task_id]["message"] = "Saving file..."
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(documents, f, indent=4, default=json_serial, ensure_ascii=False)
        
        export_tasks_dict[task_id] = {
            "progress": 100,
            "status": "completed",
            "file_path": os.path.abspath(file_path),
            "file_name": "documents_export.json", # Suggestion for browser
            "count": total_count
        }

    except Exception as e:
        export_tasks_dict[task_id] = {"progress": 0, "status": "failed", "error": str(e)}
    finally:
        cursor.close()
        conn.close()
