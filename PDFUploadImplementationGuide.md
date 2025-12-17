# PDF Upload Feature Implementation Guide

## ✅ What's Been Done:

### 1. Frontend (Complete ✓)

- ✅ Enhanced "Create Modal" with tabs for Text and PDF upload
- ✅ Drag-and-drop support for PDF files
- ✅ File validation (PDF only)
- ✅ Progress indicator during upload
- ✅ Success/Error messaging
- ✅ JavaScript handlers (PDFUpload.js)
- ✅ Added to chat_base.html template

### 2. Backend (Needs Manual Addition ⚠️)

The PDF upload route has been created in `PDFUploadRoute.py` but needs to be manually added to `flask_app.py`

## 📋 TO-DO: Add to flask_app.py

**Location**: Add this code to `src/core/flask_app.py` BEFORE the line:

```python
#  Run
if __name__ == "__main__":
```

**Code to Add**:

```python
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
```

## 🧪 How It Works:

1. **User clicks "New Doc"** → Modal opens with 2 tabs
2. **Switches to "PDF Upload" tab**
3. **Drag & drop or click to browse** → Select PDF file
4. **Clicks "Upload PDF"** → File is sent to Flask
5. **Flask `/upload-pdf` route**:
   - Saves file temporarily
   - Calls `insert_pdf()` from your existing script
   - Processes PDF into chunks
   - Stores in database with embeddings
   - Deletes temp file
   - Returns success/error
6. **Frontend shows success** → Page reloads to show new documents

## 📁 Files Created/Modified:

### Created:

- ✅ `src/core/frontend/static/PDFUpload.js` - PDF upload JavaScript
- ✅ `src/core/PDFUploadRoute.py` - Reference for the Flask route

### Modified:

- ✅ `src/core/frontend/templates/portion/chat_base.html` - Enhanced modal with PDF upload tab

### Needs Manual Edit:

- ⚠️ `src/core/flask_app.py` - Add the upload route (copy from PDFUploadRoute.py)

## 🎯 Features:

- ✅ Drag and drop PDF files
- ✅ Click to browse for files
- ✅ File validation (PDF only)
- ✅ Visual feedback (hover states, file name display)
- ✅ Progress indicator during processing
- ✅ Success/Error messages
- ✅ Automatic page reload after success
- ✅ Uses your existing PDF processing logic
- ✅ Proper temp file cleanup
- ✅ Error handling

## 🚀 Testing:

1. Add the route to `flask_app.py` as shown above
2. Restart Flask: `python flask_app.py`
3. Open your app: `http://localhost:5000`
4. Click "+ New Doc" button
5. Switch to "PDF Upload" tab
6. Drag & drop a PDF or click to browse
7. Click "Upload PDF"
8. Watch the progress indicator
9. See success message
10. Page reloads with new documents!

## 💡 Notes:

- The PDF will be chunked automatically using your existing settings (500 char chunks, 50 overlap)
- Language detection is automatic
- Embeddings are generated for each chunk
- Everything uses your existing `insert_pdf_chunks.py` logic
- Zero changes to your backend processing code
- Frontend-only implementation except for the single Flask route
