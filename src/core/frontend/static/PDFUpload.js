document.addEventListener('DOMContentLoaded', () => {
  const pdfDropZone = document.getElementById('pdfDropZone');
  const pdfFileInput = document.getElementById('pdfFileInput');
  const pdfUploadForm = document.getElementById('pdfUploadForm');
  const pdfFileListArea = document.getElementById('pdfFileListArea');
  const fileListItems = document.getElementById('fileListItems');
  const fileListSummary = document.getElementById('fileListSummary');
  const pdfUploadBtn = document.getElementById('pdfUploadBtn');
  const pdfBulkStatus = document.getElementById('pdfBulkStatus');
  const pdfStopBtn = document.getElementById('pdfStopBtn');
  const pdfCancelBtn = document.getElementById('pdfCancelBtn');
  const bulkUploadText = document.getElementById('bulkUploadText');

  let selectedFiles = [];
  let uploadInProgress = false;
  let shouldCancel = false;

  // Drag & Drop
  if (pdfDropZone) {
    pdfDropZone.addEventListener('click', () => pdfFileInput.click());
    pdfDropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      pdfDropZone.style.background = '#f0f7ff';
      pdfDropZone.style.borderColor = '#2563eb';
    });
    pdfDropZone.addEventListener('dragleave', () => {
      pdfDropZone.style.background = '#fafafa';
      pdfDropZone.style.borderColor = '#e5e7eb';
    });
    pdfDropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      pdfDropZone.style.background = '#fafafa';
      pdfDropZone.style.borderColor = '#e5e7eb';
      if (e.dataTransfer.files) handleFileSelection(e.dataTransfer.files);
    });
  }

  if (pdfFileInput) {
    pdfFileInput.addEventListener('change', (e) => handleFileSelection(e.target.files));
  }

  function handleFileSelection(files) {
    if (uploadInProgress) return;
    const freshFiles = Array.from(files).filter(f => f.type === 'application/pdf');
    if (freshFiles.length === 0) return;
    selectedFiles = [...selectedFiles, ...freshFiles];
    renderFileList();
  }

  window.minimizeCreateModal = function() {
    if (pdfDropZone) {
      const modal = document.getElementById('createModal');
      modal.classList.add('is-minimized');
      // If busy, make sure the text shows current progress
      if (uploadInProgress) {
        // masterToast was showing individual file, 
        // minimize can show global "Processing N/Total"
      }
    }
  };

  window.restoreCreateModal = function() {
    const modal = document.getElementById('createModal');
    modal.classList.remove('is-minimized');
  };

  // Add click listener for restore
  document.querySelector('.modal-content-main')?.addEventListener('click', (e) => {
    if (document.getElementById('createModal').classList.contains('is-minimized')) {
        window.restoreCreateModal();
    }
  });

  window.closeCreateModal = function() {
    if (uploadInProgress) {
        window.Notify.show("Upload in progress. Minimizing instead.", "info");
        window.minimizeCreateModal();
        return;
    }
    const el = document.getElementById('createModal');
    if (el) bootstrap.Modal.getOrCreateInstance(el).hide();
  };

  window.stopUploadBatch = async function() {
    if (!uploadInProgress) return;
    if (confirm("Stop current upload and all background indexing tasks?")) {
        shouldCancel = true;
        // Also signal the server to stop current worker
        try {
            await fetch('/api/stop-indexing', { method: 'POST' });
        } catch(e) { console.error("Signal stop error:", e); }
        
        if (pdfStopBtn) {
            pdfStopBtn.disabled = true;
            pdfStopBtn.textContent = 'STOPPING...';
        }
        // Notification is handled by the loop's check for shouldCancel
    }
  };

  window.clearPDFSelection = function() {
    if (uploadInProgress) {
        window.stopUploadBatch();
        return;
    }
    selectedFiles = [];
    if (pdfFileInput) pdfFileInput.value = '';
    renderFileList();
  };

  function renderFileList() {
    if (!pdfFileListArea || !fileListItems) return;
    if (selectedFiles.length === 0) {
      pdfFileListArea.style.display = 'none';
      if (pdfBulkStatus) pdfBulkStatus.style.display = 'none';
      if (pdfUploadBtn) pdfUploadBtn.disabled = true;
      return;
    }
    pdfFileListArea.style.display = 'block';
    if (pdfBulkStatus) pdfBulkStatus.style.display = 'block';
    if (pdfUploadBtn) pdfUploadBtn.disabled = uploadInProgress;
    if (fileListSummary) fileListSummary.textContent = `${selectedFiles.length} FILES SELECTED`;
    if (bulkUploadText) bulkUploadText.textContent = uploadInProgress ? "Uploading..." : `Ready to upload ${selectedFiles.length} files`;

    fileListItems.innerHTML = selectedFiles.map((file, index) => `
      <div class="file-item" id="file-row-${index}">
        <div class="file-status-icon" id="file-icon-${index}">
          <i class="bi bi-file-earmark-pdf text-primary"></i>
        </div>
        <div class="file-info">
          <span class="fw-medium">${truncateName(file.name, 40)}</span>
          <span class="text-muted small ms-2">(${(file.size / 1024 / 1024).toFixed(2)} MB)</span>
        </div>
        <div class="file-progress-mini">
          <div class="file-progress-inner" id="file-progress-${index}"></div>
        </div>
        <span class="status-badge badge-queued" id="file-badge-${index}">QUEUED</span>
      </div>
    `).join('');
  }

  function truncateName(name, len = 20) {
    if (name.length <= len) return name;
    return name.substring(0, len-3) + '...';
  }

  async function processUploadBatch() {
    if (selectedFiles.length === 0 || uploadInProgress) return;
    
    uploadInProgress = true;
    shouldCancel = false;
    
    if (pdfUploadBtn) pdfUploadBtn.style.display = 'none';
    if (pdfStopBtn) {
        pdfStopBtn.style.display = 'block';
        pdfStopBtn.disabled = false;
        pdfStopBtn.textContent = 'STOP BATCH';
    }
    if (pdfCancelBtn) pdfCancelBtn.style.display = 'none';
    if (pdfDropZone) pdfDropZone.style.opacity = '0.5';

    const total = selectedFiles.length;
    let successCount = 0;
    let failCount = 0;

    // Initialize Master Toast
    const masterToast = window.Notify.show(`Starting batch: 0/${total}`, 'info', -1, true);

    for (let i = 0; i < total; i++) {
        const badge = document.getElementById(`file-badge-${i}`);
        // SKIP if already finished (for Resume support)
        if (badge && badge.textContent === 'FINISHED') {
            successCount++; // Keep our count accurate
            continue;
        }

        if (shouldCancel) {
          masterToast.update(`Stopped at ${i}/${total}. Processed ${successCount} files.`, "warning");
          if (masterToast.setLoading) masterToast.setLoading(false); 
          setTimeout(() => masterToast.close(), 5000);
          break;
        }

        const file = selectedFiles[i];
        const row = document.getElementById(`file-row-${i}`);
        const progress = document.getElementById(`file-progress-${i}`);
        const icon = document.getElementById(`file-icon-${i}`);

        // Update Master Status & Progress
        const percent = Math.round(((i + 1) / total) * 100);
        masterToast.update(`Processing ${i + 1}/${total}: ${truncateName(file.name, 15)}`, 'info');
        masterToast.setProgress(percent);

        if (row) {
            row.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            row.style.background = '#fffbeb'; 
            row.style.borderLeft = '4px solid #f59e0b';
        }
        if (badge) { badge.className = 'status-badge badge-uploading'; badge.textContent = 'UPLOADING'; }
        if (progress) { progress.parentElement.style.display = 'block'; progress.style.width = '40%'; }
        if (icon) icon.innerHTML = '<div class="spinner-border spinner-border-sm text-warning" role="status"></div>';
        
        const formData = new FormData();
        formData.append('pdfFile', file);

        try {
            const response = await fetch('/upload-pdf', { method: 'POST', body: formData });
            if (!response.ok) throw new Error("Upload Failed");

            const data = await response.json();
            if (data.success) {
                successCount++;
                if (progress) progress.style.width = '100%';
                if (badge) { badge.className = 'status-badge badge-success'; badge.textContent = 'FINISHED'; }
                if (icon) icon.innerHTML = '<i class="bi bi-check-circle-fill text-success"></i>';
                if (row) { row.style.background = '#f0fdf4'; row.style.borderLeft = '4px solid #10b981'; }
            } else {
                throw new Error(data.error || "Server Error");
            }
        } catch (err) {
            failCount++;
            if (progress) { progress.style.width = '100%'; progress.style.background = '#ef4444'; }
            if (badge) { badge.className = 'status-badge badge-error'; badge.textContent = 'FAILED'; }
            if (icon) icon.innerHTML = '<i class="bi bi-exclamation-triangle-fill text-danger"></i>';
            if (row) { row.style.background = '#fef2f2'; row.style.borderLeft = '4px solid #ef4444'; }
            console.error(`Error uploading ${file.name}:`, err);
        }
        
        // Small delay between files to keep UI responsive
        await new Promise(r => setTimeout(r, 100));
    }

    uploadInProgress = false;
    if (pdfStopBtn) pdfStopBtn.style.display = 'none';
    if (pdfCancelBtn) pdfCancelBtn.style.display = 'block';
    if (pdfUploadBtn) pdfUploadBtn.style.display = 'block';

    if (!shouldCancel) {
        masterToast.update(`Batch Complete: ${successCount} Success, ${failCount} Failed`, successCount > 0 ? 'success' : 'danger');
        
        if (bulkUploadText) {
            bulkUploadText.innerHTML = `<span class="text-success"><i class="bi bi-check-all"></i> Batch Finished: ${successCount} documents indexed.</span>`;
        }
        
        if (pdfUploadBtn) {
            pdfUploadBtn.innerHTML = '<i class="bi bi-check-lg"></i> Finish & Reload';
            pdfUploadBtn.disabled = false;
            pdfUploadBtn.type = 'button'; 
            pdfUploadBtn.style.display = 'block';
            pdfUploadBtn.onclick = (e) => {
                e.preventDefault();
                window.location.reload();
            };
        }

        // Auto-close toast after 5s
        setTimeout(() => masterToast.close(), 5000);
    } else {
        if (bulkUploadText) {
            bulkUploadText.innerHTML = `<span class="text-warning"><i class="bi bi-slash-circle"></i> Batch Stopped: ${successCount} documents indexed.</span>`;
        }
        if (pdfUploadBtn) {
            pdfUploadBtn.innerHTML = '<i class="bi bi-play-fill"></i> Resume Upload';
            pdfUploadBtn.disabled = false;
            pdfUploadBtn.type = 'button';
            pdfUploadBtn.style.display = 'block';
            pdfUploadBtn.onclick = (e) => {
                e.preventDefault();
                processUploadBatch(); // RE-CALL to resume
            };
        }
    }
  }

  if (pdfUploadForm) {
    pdfUploadForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      await processUploadBatch();
    });
  }
});
