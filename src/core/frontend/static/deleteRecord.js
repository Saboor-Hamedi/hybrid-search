/**
 * High-Fidelity Document Deletion Handler
 * Utilizes ApiService for data and ModalManager for UI.
 */

function deleteRecord(docId) {
    if (event) event.preventDefault();

    ModalManager.showDelete({
        title: 'Delete Document?',
        message: `Are you sure you want to delete <strong>#${docId}</strong>? This action cannot be undone.`,
        confirmText: 'Delete Permanent',
        loadingText: 'Deleting...',
        icon: 'bi-exclamation-triangle',
        danger: true,
        onConfirm: async (resetModal) => {
            const form = document.getElementById("quickDeleteForm");
            
            try {
                // 1. Execute deletion via Industrial ApiService
                const result = await ApiService.deleteDocument(docId, new FormData(form));
                
                if (result.success) {
                    // 2. Clear UI state
                    ModalManager.hide('quickDeleteModal');

                    // 3. Document Page Redirection Logic
                    if (window.location.pathname.includes('document')) {
                        const backUrl = `/?q=${encodeURIComponent(form.q?.value || '')}&mode=${form.mode?.value || 'hybrid'}`;
                        window.location.href = backUrl;
                        return;
                    }

                    // 4. Animate removal from Search Results
                    const items = document.querySelectorAll(".result-item");
                    items.forEach((item) => {
                        // Check for both the ID string and the specific visual #ID
                        if (item.innerHTML.includes("#" + docId) || item.dataset.docId === docId) {
                            item.style.opacity = "0";
                            item.style.transform = "translateX(50px)";
                            item.style.transition = "all 0.4s ease";
                            setTimeout(() => {
                                item.remove();
                                // Trigger empty state check if needed
                                if (document.querySelectorAll(".result-item").length === 0) {
                                    location.reload(); 
                                }
                            }, 400);
                        }
                    });
                } else {
                    throw new Error(result.error || "Unknown server error");
                }
            } catch (err) {
                console.error("Delete failed:", err);
                alert("Delete failed: " + err.message);
                resetModal();
            }
        }
    });
}
