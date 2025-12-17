"""
Enhanced PDF Upload with Live Progress Streaming

This creates a WebSocket-like streaming progress for PDF uploads.
Since we can't easily add WebSockets, we'll use a simpler approach:

1. Show a progress modal with animated dots
2. Log progress to console
3. Poll for completion

For TRUE live streaming, you'd need to add Server-Sent Events (SSE) or WebSockets.
"""

# SIMPLE VERSION: Just show better feedback

# In chat_base.html, add this CSS for a progress modal:

"""

<style>
.pdf-progress-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0,0,0,0.7);
  z-index: 10000;
  display: none;
  align-items: center;
  justify-content: center;
}

.pdf-progress-box {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  text-align: center;
  max-width: 500px;
  width: 90%;
}

.pdf-progress-spinner {
  width: 60px;
  height: 60px;
  border: 4px solid #e5e7eb;
  border-top-color: #2563eb;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

.pdf-progress-text {
  font-size: 1rem;
  color: #374151;
  margin-bottom: 0.5rem;
}

.pdf-progress-detail {
  font-size: 0.875rem;
  color: #6b7280;
}

.pdf-progress-tip {
  font-size: 0.75rem;
  color: #9ca3af;
  margin-top: 1rem;
  font-style: italic;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>

<!-- Add this modal HTML -->
<div id="pdfProgressModal" class="pdf-progress-modal">
  <div class="pdf-progress-box">
    <div class="pdf-progress-spinner"></div>
    <div class="pdf-progress-text">Processing PDF...</div>
    <div class="pdf-progress-detail">
      Extracting content, chunking, and generating embeddings
    </div>
    <div class="pdf-progress-tip">
      Large PDFs may take 2-5 minutes. Check your terminal for detailed progress.
    </div>
  </div>
</div>
"""

# Update PDFUpload.js uploadPDFDirectly function:

"""
async function uploadPDFDirectly(file) {
if (!confirm(`Upload and process "${file.name}"? This may take a few minutes.`)) {
return;
}

const formData = new FormData();
formData.append('pdfFile', file);

// Show progress modal
const progressModal = document.getElementById('pdfProgressModal');
if (progressModal) {
progressModal.style.display = 'flex';
}

try {
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 min timeout

    const response = await fetch('/upload-pdf', {
      method: 'POST',
      body: formData,
      signal: controller.signal
    });

    clearTimeout(timeoutId);
    const data = await response.json();

    // Hide progress modal
    if (progressModal) {
      progressModal.style.display = 'none';
    }

    if (data.success) {
      alert(`Success! ${data.message}`);
      window.location.reload();
    } else {
      alert(`Error: ${data.error}`);
    }

} catch (error) {
// Hide progress modal
if (progressModal) {
progressModal.style.display = 'none';
}
alert(`Upload failed: ${error.message}`);
}
}
"""
