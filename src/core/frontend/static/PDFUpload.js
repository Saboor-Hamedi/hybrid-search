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
      const file = e.target.files[0];
      if (file) {
        handlePDFFile(file);
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
      
      const file = e.dataTransfer.files[0];
      if (file) {
        if (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')) {
          // Create a new DataTransfer object and add the file
          const dataTransfer = new DataTransfer();
          dataTransfer.items.add(file);
          
          // Set the files to the input element
          pdfFileInput.files = dataTransfer.files;
          
          // Now handle the file
          handlePDFFile(file);
        } else {
          alert('Please select a PDF file');
        }
      }
    });
  }
  
  // Handle PDF file
  function handlePDFFile(file) {
    if (selectedFileName) selectedFileName.textContent = file.name;
    if (pdfFileName) pdfFileName.style.display = 'block';
    if (pdfUploadBtn) pdfUploadBtn.disabled = false;
    if (pdfUploadResult) pdfUploadResult.style.display = 'none';
  }
  
  // Upload PDF directly (from quick button)
  async function uploadPDFDirectly(file) {
    console.log('uploadPDFDirectly called with:', file.name);
    
    if (!confirm(`Upload and process "${file.name}"? This may take a few minutes.`)) {
      console.log('User cancelled upload');
      return;
    }
    
    console.log('Starting upload...');
    
    const formData = new FormData();
    formData.append('pdfFile', file);
    
    try {
      // Show loading indicator in input area
      const searchBtn = document.querySelector('.search-btn');
      const originalBtnText = searchBtn.innerHTML;
      searchBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing PDF...';
      searchBtn.disabled = true;
      
      console.log('Sending request to /upload-pdf');
      
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 min timeout
      
      const response = await fetch('/upload-pdf', {
        method: 'POST',
        body: formData,
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      console.log('Response received:', response.status);
      
      const data = await response.json();
      console.log('Response data:', data);
      
      searchBtn.innerHTML = originalBtnText;
      searchBtn.disabled = false;
      
      if (data.success) {
        alert(`Success! ${data.message}`);
        window.location.reload();
      } else {
        alert(`Error: ${data.error}`);
      }
    } catch (error) {
      console.error('Upload error:', error);
      alert(`Upload failed: ${error.message}`);
      const searchBtn = document.querySelector('.search-btn');
      searchBtn.innerHTML = '<i class="bi bi-search"></i> Search';
      searchBtn.disabled = false;
    }
  }
  
  // Handle form submission (from modal)
  if (pdfUploadForm) {
    pdfUploadForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const file = pdfFileInput.files[0];
      if (!file) {
        alert('Please select a PDF file');
        return;
      }
      
      // Show progress
      pdfUploadProgress.style.display = 'block';
      pdfUploadBtn.disabled = true;
      pdfUploadResult.style.display = 'none';
      
      const formData = new FormData();
      formData.append('pdfFile', file);
      
      try {
        // Add timeout (5 minutes)
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 300000);
        
        const response = await fetch('/upload-pdf', {
          method: 'POST',
          body: formData,
          signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        const data = await response.json();
        
        // Hide progress
        pdfUploadProgress.style.display = 'none';
        
        if (data.success) {
          pdfUploadResult.innerHTML = `
            <div class="alert alert-success">
              <i class="bi bi-check-circle me-2"></i>
              ${data.message}
            </div>
          `;
          pdfUploadResult.style.display = 'block';
          
          // Reset form after 2 seconds and close modal
          setTimeout(() => {
            closeCreateModal();
            window.location.reload();
          }, 2000);
        } else {
          pdfUploadResult.innerHTML = `
            <div class="alert alert-danger">
              <i class="bi bi-exclamation-triangle me-2"></i>
              Error: ${data.error}
            </div>
          `;
          pdfUploadResult.style.display = 'block';
          pdfUploadBtn.disabled = false;
        }
      } catch (error) {
        pdfUploadProgress.style.display = 'none';
        const errorMsg = error.name === 'AbortError' ? 'Upload timed out (5 min limit)' : error.message;
        pdfUploadResult.innerHTML = `
          <div class="alert alert-danger">
            <i class="bi bi-exclamation-triangle me-2"></i>
            Upload failed: ${errorMsg}
          </div>
        `;
        pdfUploadResult.style.display = 'block';
        pdfUploadBtn.disabled = false;
      }
    });
  }
});
