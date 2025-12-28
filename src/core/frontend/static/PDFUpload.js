// === PDF UPLOAD FUNCTIONALITY ===

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', function() {
  
  console.log('PDF Upload script loaded');
  
  const pdfDropZone = document.getElementById('pdfDropZone');
  const pdfFileInput = document.getElementById('pdfFileInput');
  const pdfUploadForm = document.getElementById('pdfUploadForm');
  const pdfUploadBtn = document.getElementById('pdfUploadBtn');
  const pdfFileName = document.getElementById('pdfFileName');
  const selectedFileName = document.getElementById('selectedFileName');
  const pdfUploadProgress = document.getElementById('pdfUploadProgress');
  const pdfUploadResult = document.getElementById('pdfUploadResult');
  
  // Quick upload from main input area
  const quickPdfInput = document.getElementById('quickPdfInput');
  console.log('Quick PDF Input found:', quickPdfInput);
  
  if (quickPdfInput) {
    quickPdfInput.addEventListener('change', (e) => {
      console.log('File selected!', e.target.files);
      const file = e.target.files[0];
      if (file) {
        console.log('Processing file:', file.name);
        uploadPDFDirectly(file);
      }
    });
    console.log('Quick PDF upload listener attached');
  } else {
    console.warn('quickPdfInput element not found!');
  }
  
  // Close create modal helper
  window.closeCreateModal = function() {
    document.getElementById('createModal').style.display = 'none';
    clearPDFSelection();
  }
  
  // Clear PDF selection
  window.clearPDFSelection = function() {
    if (pdfFileInput) pdfFileInput.value = '';
    if (pdfFileName) pdfFileName.style.display = 'none';
    if (pdfUploadBtn) pdfUploadBtn.disabled = true;
    if (pdfUploadResult) pdfUploadResult.style.display = 'none';
    if (pdfUploadProgress) pdfUploadProgress.style.display = 'none';
  }
  
  // Click on drop zone opens file selector
  if (pdfDropZone) {
    pdfDropZone.addEventListener('click', () => {
      pdfFileInput.click();
    });
    
    // Handle file selection
    pdfFileInput.addEventListener('change', (e) => {
      const files = e.target.files;
      if (files.length > 0) {
        handlePDFFiles(files);
      }
    });
    
    // Drag and drop handlers
    pdfDropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      e.stopPropagation();
      pdfDropZone.style.borderColor = '#2563eb';
      pdfDropZone.style.background = '#eff6ff';
    });
    
    pdfDropZone.addEventListener('dragleave', (e) => {
      e.preventDefault();
      e.stopPropagation();
      pdfDropZone.style.borderColor = '#d1d5db';
      pdfDropZone.style.background = 'transparent';
    });
    
    pdfDropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      e.stopPropagation();
      pdfDropZone.style.borderColor = '#d1d5db';
      pdfDropZone.style.background = 'transparent';
      
      const files = e.dataTransfer.files;
      if (files.length > 0) {
          // Filter for PDFs
          const validFiles = Array.from(files).filter(f => f.type === 'application/pdf' || f.name.toLowerCase().endsWith('.pdf'));
          
          if (validFiles.length > 0) {
              const dataTransfer = new DataTransfer();
              validFiles.forEach(f => dataTransfer.items.add(f));
              pdfFileInput.files = dataTransfer.files;
              
              handlePDFFiles(validFiles);
          } else {
              alert('Please select PDF files');
          }
      }
    });
  }
  
  // Handle PDF files
  function handlePDFFiles(files) {
    if (files.length === 1) {
        if (selectedFileName) selectedFileName.textContent = files[0].name;
    } else {
        if (selectedFileName) selectedFileName.textContent = `${files.length} files selected`;
    }
    
    if (pdfFileName) pdfFileName.style.display = 'block';
    if (pdfUploadBtn) pdfUploadBtn.disabled = false;
    if (pdfUploadResult) pdfUploadResult.style.display = 'none';
  }
  
  // Upload PDF directly (from quick button)
  function uploadPDFDirectly(file) {
    console.log('uploadPDFDirectly called with:', file.name);
    
    // Use Custom Modal
    const modalEl = document.getElementById('confirmModal');
    const titleEl = document.getElementById('confirmModalTitle');
    const msgEl = document.getElementById('confirmModalMessage');
    const btnEl = document.getElementById('confirmModalBtn');
    
    if (modalEl && typeof bootstrap !== 'undefined') {
        titleEl.textContent = 'Upload PDF?';
        msgEl.textContent = `Process "${file.name}" in the background?`;
        
        // Clone button to remove old listeners
        const newBtn = btnEl.cloneNode(true);
        btnEl.parentNode.replaceChild(newBtn, btnEl);
        
        const bsModal = new bootstrap.Modal(modalEl);
        
        newBtn.onclick = async () => {
            bsModal.hide();
            // Start background upload
            await processUpload([file], true);
        };
        
        bsModal.show();
    } else {
        // Fallback
        if (confirm(`Process "${file.name}" in background?`)) {
             processUpload([file], true);
        }
    }
  }

  // Common upload processor
  // files: FileList or Array of File objects
  // isDirect: boolean (true for quick upload, false for modal)
  async function processUpload(files, isDirect) {
      const filesArray = Array.from(files);
      if (filesArray.length === 0) return;

      // Truncate filename helper
      function truncateName(name, maxLength=20) {
          if (name.length <= maxLength) return name;
          return name.substring(0, maxLength) + '...';
      }

      // Persistent Toast Logic
      function updateToast(id, msg, type='info', isLoading=false) {
          let container = document.getElementById('toast-container');
          if (!container) {
              container = document.createElement('div');
              container.id = 'toast-container';
              container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 10000; display: flex; flex-direction: column; gap: 10px;';
              document.body.appendChild(container); // Moved to TOP right as requested by "under the header" hint
          }
          
          let toast = document.getElementById(id);
          
          // Icon Selection
          let icon = '<i class="bi bi-info-circle me-2"></i>';
          if (isLoading) icon = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>';
          if (type === 'success') icon = '<i class="bi bi-check-circle-fill text-success me-2"></i>';
          if (type === 'danger') icon = '<i class="bi bi-x-circle-fill text-danger me-2"></i>';

          const contentHtml = `
            <div class="d-flex align-items-center justify-content-between">
                <div class="d-flex align-items-center">
                    ${icon}
                    <span class="fw-medium">${msg}</span>
                </div>
                <button type="button" class="btn-close btn-close-sm ms-3" onclick="document.getElementById('${id}').remove()" aria-label="Close"></button>
            </div>
          `;

          if (!toast) {
              // Create New
              toast = document.createElement('div');
              toast.id = id;
              toast.className = `alert alert-light shadow-sm border border-${type} mb-0 p-2`;
              toast.style.cssText = 'min-width: 200px; max-width: 300px; animation: slideInRight 0.3s ease-out; background: white; font-size: 0.9rem;';
              toast.innerHTML = contentHtml;
              container.appendChild(toast);
          } else {
              // Update Existing
              toast.className = `alert alert-light shadow-sm border border-${type} mb-0 p-2`;
              toast.innerHTML = contentHtml;
          }
      }
      
      // Inject CSS
      if (!document.getElementById('toast-styles')) {
           const style = document.createElement('style');
           style.id = 'toast-styles';
           style.innerHTML = `@keyframes slideInRight { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }`;
           document.head.appendChild(style);
      }

      for (let i = 0; i < filesArray.length; i++) {
          const file = filesArray[i];
          const formData = new FormData();
          formData.append('pdfFile', file); 
          
          const toastId = 'toast-' + Math.random().toString(36).substr(2, 9);
          const shortName = truncateName(file.name, 25);

          if (isDirect) {
              updateToast(toastId, `Processing ${shortName}...`, 'primary', true);
          }

          try {
              // Since backend is threaded (202 Accepted), this returns practically instantly
              const response = await fetch('/upload-pdf', {
                  method: 'POST',
                  body: formData
              });
              
              const data = await response.json();

              if (data.success) {
                  // The "heavy" part is now in background. 
                  // HOWEVER, since we can't poll via websocket/DB, 
                  // we have to fake a bit of "wait" or just tell user it's started.
                  // User wanted "Processing -> Success". 
                  // Since the Server returns IMMEDIATELY now (202), we can't know when it's *actually* done without polling.
                  // For the sake of UX asked ("Loader -> Success"):
                  // We will transition to "Processing in Background..." 
                  
                  // Wait a realistic amount of time? No, that's fake.
                  // Correct UX for 202: "Upload Queued" -> "Processing..."
                  
                  // Given the constraints (no DB status polling), checking 'success' logic:
                  // The previous code waited for the Whole Process.
                  // Now logic is: Python returns 202 instantly.
                  // So the JS receives 'success' instantly. 
                  // This creates a UX problem: It will say "Success" before it's actually searchable.
                  
                  // Update toast to say "Backgrounding"
                  updateToast(toastId, `Processing ${shortName} in background...`, 'info', true);
                  
                  // We simulate a completion after some time or just leave it as "Processing..." 
                  // But the user wants "Success" notification.
                  // Without a polling endpoint, we can't know.
                  
                  // PROPOSAL: I will auto-mark it as "Queued" (Success) but keep the spinner for a few seconds.
                  setTimeout(() => {
                       updateToast(toastId, `PDF ${shortName} queued successfully.`, 'success', false);
                  }, 2000);
                  
              } else {
                  updateToast(toastId, `Failed: ${shortName}`, 'danger', false);
              }

          } catch (error) {
              console.error(error);
              updateToast(toastId, `Error: ${shortName}`, 'danger', false);
          }
      }
  }

  
  // Handle form submission (from modal)
  if (pdfUploadForm) {
    pdfUploadForm.addEventListener('submit', async (e) => {
      e.preventDefault();
       
      const files = pdfFileInput.files;
      if (!files || files.length === 0) {
        alert('Please select PDF file(s)');
        return;
      }
      
      await processUpload(files, false);
    });
  }
});
