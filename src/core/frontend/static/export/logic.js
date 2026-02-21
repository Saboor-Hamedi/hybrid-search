/**
 * Logic for Document Export Feature
 * Uses the existing notification system from PDFUpload.js
 */

async function startExport() {
    
    // Create a temporary ID for immediate feedback
    const tempId = 'export-init-' + Math.random().toString(36).substr(2, 5);
    showExportNotification(tempId, 'Initiating export...', 'info', true);

    // 1. Initiate Export
    try {
        const response = await fetch('http://localhost:8000/export/start', {
            method: 'POST'
        });
        
        if (!response.ok) throw new Error('Failed to start export');
        
        const { task_id } = await response.json();
        
        // 2. Update Notification with Task ID
        const toastId = 'export-' + task_id.substr(0, 8);
        const tempToast = document.getElementById(tempId);
        if (tempToast) tempToast.id = toastId; // Reuse the existing toast element

        showExportNotification(toastId, 'Preparing database export...', 'info', true);
        
        // 3. Start Polling
        pollExportStatus(task_id, toastId);
        
    } catch (error) {
        console.error('Export error:', error);
        showExportNotification(tempId, 'Could not start export: ' + error.message, 'danger', false);
    }
}

async function pollExportStatus(task_id, toastId) {
    const checkStatus = async () => {
        try {
            const response = await fetch(`http://localhost:8000/export/status/${task_id}`);
            if (!response.ok) throw new Error('Failed to fetch status');
            
            const task = await response.json();
            
            if (task.status === 'processing') {
                const msg = task.message || `Exporting... ${task.progress}%`;
                showExportNotification(toastId, msg, 'info', true);
            } else if (task.status === 'completed') {
                clearInterval(pollInterval);
                showExportNotification(toastId, `Export complete! ${task.count} documents.`, 'success', false);
                
                // Trigger Download
                triggerDownload(task_id);
                
                // Remove notification after 5 seconds
                setTimeout(() => {
                    const toast = document.getElementById(toastId);
                    if (toast) toast.remove();
                }, 5000);
            } else if (task.status === 'failed') {
                clearInterval(pollInterval);
                const errorMsg = task.error || 'Export failed';
                showExportNotification(toastId, errorMsg, 'danger', false);
            }
            
        } catch (error) {
            console.error('Polling error:', error);
            if (typeof pollInterval !== 'undefined') clearInterval(pollInterval);
            showExportNotification(toastId, 'Error checking export status', 'danger', false);
        }
    };

    // Run once immediately
    checkStatus();
    
    // Then set interval
    const pollInterval = setInterval(checkStatus, 1500);
}

function triggerDownload(task_id) {
    const downloadUrl = `http://localhost:8000/export/download/${task_id}`;
    // Create a temporary link and click it
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = 'documents_export.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

/**
 * Reuses the notification UI pattern from PDFUpload.js
 * If updateToast exists in global scope (from PDFUpload.js), we use it.
 * Otherwise we define a minimal version.
 */
function showExportNotification(id, msg, type, isLoading) {
    // Try to find the container
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = 'position: fixed; top: 80px; right: 20px; z-index: 10000; display: flex; flex-direction: column; gap: 12px;';
        document.body.appendChild(container);
    }

    let toast = document.getElementById(id);
    
    // Icon Logic
    let iconContent = '<i class="bi bi-info-circle"></i>';
    if (isLoading) {
        iconContent = '<div class="spinner-border" style="width: 14px; height: 14px; border-width: 2px;" role="status"></div>';
    } else if (type === 'success') {
        iconContent = '<i class="bi bi-check-circle-fill text-success"></i>';
    } else if (type === 'danger') {
        iconContent = '<i class="bi bi-x-circle-fill text-danger"></i>';
    }

    const iconHtml = `<div class="d-flex align-items-center justify-content-center" style="width: 28px; height: 28px; background: #f8fafc; border-radius: 50%; color: #64748b; font-size: 1.1rem; flex-shrink: 0;">${iconContent}</div>`;

    const contentHtml = `
      <div class="d-flex align-items-center">
          ${iconHtml}
          <div class="ms-3 flex-grow-1">
              <div class="fw-semibold text-dark" style="font-size: 0.85rem; line-height: 1.2;">Export Service</div>
              <div class="text-muted" style="font-size: 0.75rem; line-height: 1.2;">${msg}</div>
          </div>
          <button type="button" class="btn-close ms-2" style="font-size: 0.6rem;" onclick="document.getElementById('${id}').remove()"></button>
      </div>
    `;

    if (!toast) {
        toast = document.createElement('div');
        toast.id = id;
        toast.className = `alert-custom shadow-lg border-0 mb-0 p-3`;
        toast.style.cssText = 'min-width: 240px; max-width: 320px; animation: toastSlideIn 0.4s cubic-bezier(0.16, 1, 0.3, 1); background: white; border-left: 4px solid #2563eb; border-radius: 12px;';
        if (type === 'success') toast.style.borderLeftColor = '#10b981';
        if (type === 'danger') toast.style.borderLeftColor = '#ef4444';
        toast.innerHTML = contentHtml;
        container.appendChild(toast);
    } else {
        toast.innerHTML = contentHtml;
        if (type === 'success') toast.style.borderLeftColor = '#10b981';
        if (type === 'danger') toast.style.borderLeftColor = '#ef4444';
    }
}
