"""
PDF Upload Route for Flask App
Add this to flask_app.py before the if __name__ == "__main__" block
"""

# Add this route to flask_app.py:

@app.route("/upload-pdf", methods=["POST"])
def UploadPDF():
    """Handle PDF file upload and process it into chunks"""
    import tempfile
    from werkzeug.utils import secure_filename
    from ingestion.insert_pdf_chunks import insert_pdf
    
    if 'pdfFile' not in request.files:
        return {"success": False, "error": "No file provided"}, 400
    
    file = request.files['pdfFile']
    
    if file.filename == '':
        return {"success": False, "error": "No file selected"}, 400
    
    if not file.filename.lower().endswith('.pdf'):
        return {"success": False, "error": "Only PDF files are allowed"}, 400
    
    try:
        # Create a temporary file to save the PDF
        secure_name = secure_filename(file.filename)
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"upload_{secure_name}")
        
        # Save the uploaded file
        file.save(temp_path)
        
        # Get database connection
        conn, cursor = _db()
        
        # Process the PDF using existing logic
        success = insert_pdf(temp_path, conn, cursor)
        
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        # Close database connection
        cursor.close()
        conn.close()
        
        if success:
            return {"success": True, "message": f"PDF '{secure_name}' processed successfully"}, 200
        else:
            return {"success": False, "error": "Failed to process PDF"}, 500
            
    except Exception as e:
        # Clean up temp file in case of error
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)
        print(f"PDF upload error: {e}")
        return {"success": False, "error": str(e)}, 500
