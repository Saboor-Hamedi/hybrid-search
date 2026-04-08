/**
 * Industrial Modal Manager
 * Standardizes modal interactions and aesthetic customization.
 */

const ModalManager = {
    /**
     * Triggers the High-Fidelity Delete Modal
     * @param {Object} options - { title, message, confirmText, icon, onConfirm }
     */
    showDelete: function(options) {
        const modal = document.getElementById('quickDeleteModal');
        if (!modal) return;
        
        // Dynamic Customization
        const titleEl = document.getElementById('quickDeleteTitle');
        const msgEl = document.getElementById('quickDeleteMessage');
        const confirmBtn = document.getElementById('quickDeleteConfirmBtn');
        const iconEl = document.getElementById('quickDeleteIcon');
        const form = document.getElementById('quickDeleteForm');
        
        if (titleEl) titleEl.textContent = options.title || 'Delete Document?';
        if (msgEl) msgEl.innerHTML = options.message || 'Are you sure?';
        if (confirmBtn) {
            confirmBtn.textContent = options.confirmText || 'Delete Permanent';
            confirmBtn.className = `btn btn-sm ${options.danger ? 'btn-danger' : 'btn-primary'}`;
        }
        
        if (iconEl && options.icon) {
            iconEl.className = `bi ${options.icon}`;
        }

        // Action Handling
        if (form) {
            // Reset state
            confirmBtn.disabled = false;
            
            form.onsubmit = (e) => {
                e.preventDefault();
                
                // Visual Feedback
                confirmBtn.disabled = true;
                const originalText = confirmBtn.textContent;
                confirmBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span> ${options.loadingText || 'Processing...'}`;
                
                if (options.onConfirm) {
                    options.onConfirm(() => {
                        // Reset Callback (if needed)
                        confirmBtn.disabled = false;
                        confirmBtn.textContent = originalText;
                        this.hide('quickDeleteModal');
                    });
                }
            };
        }
        
        modal.style.display = 'flex';
    },

    /**
     * Standard Bootstrap Confirmation Modal
     */
    confirm: function(options) {
        const modalEl = document.getElementById('confirmModal');
        if (!modalEl) return;
        
        document.getElementById('confirmModalTitle').textContent = options.title || 'Security Lock';
        document.getElementById('confirmModalMessage').textContent = options.message || 'Are you sure?';
        
        const confirmBtn = document.getElementById('confirmModalBtn');
        
        // Re-bind click listener
        const newConfirmBtn = confirmBtn.cloneNode(true);
        confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
        
        newConfirmBtn.onclick = () => {
            if (options.onConfirm) options.onConfirm();
            this.hideBootstrap('confirmModal');
        };
        
        this.showBootstrap('confirmModal');
    },

    // --- Helpers ---
    hide: function(id) {
        const el = document.getElementById(id);
        if (el) el.style.display = 'none';
    },

    showBootstrap: function(id) {
        const el = document.getElementById(id);
        if (el) bootstrap.Modal.getOrCreateInstance(el).show();
    },

    hideBootstrap: function(id) {
        const el = document.getElementById(id);
        if (el) bootstrap.Modal.getOrCreateInstance(el).hide();
    }
};
