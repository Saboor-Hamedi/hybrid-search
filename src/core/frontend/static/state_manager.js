/**
 * Industrial UI/UX State Manager
 * Synchronizes DOM Controls, LocalStorage, and URL State.
 */

const StateManager = {
    // Keys used in localStorage
    KEYS: {
        AI_ENABLED: 'ai-summarization-enabled',
        SEARCH_MODE: 'active_mode',
        FUSION_STRATEGY: 'fusion_strategy',
        USE_LTR: 'use_ltr'
    },

    isInitializing: false,

    /**
     * Scrapes the UI to get the current application state
     */
    getUIState: function() {
        return {
            query: document.querySelector('.search-input')?.value || '',
            mode: document.getElementById('activeModeInput')?.value || 'hybrid',
            fusion: document.querySelector('input[name="fusion_strategy"]')?.value || 'linear',
            ltr: document.querySelector('input[name="use_ltr"]')?.checked || false,
            ai: document.getElementById('aiToggle')?.checked || false,
            page: 1 
        };
    },

    /**
     * Persists the current UI state to local memory
     */
    saveToStorage: function(state = null) {
        if (this.isInitializing) return; // Prevent overwriting during load
        const s = state || this.getUIState();
        localStorage.setItem(this.KEYS.AI_ENABLED, s.ai);
        localStorage.setItem(this.KEYS.SEARCH_MODE, s.mode);
        localStorage.setItem(this.KEYS.FUSION_STRATEGY, s.fusion);
        localStorage.setItem(this.KEYS.USE_LTR, s.ltr);
    },

    /**
     * Restores UI controls from local memory
     */
    restoreFromStorage: function() {
        this.isInitializing = true;
        try {
            const ai = localStorage.getItem(this.KEYS.AI_ENABLED);
            const mode = localStorage.getItem(this.KEYS.SEARCH_MODE);
            const ltr = localStorage.getItem(this.KEYS.USE_LTR);
            
            if (ai !== null) {
                const isEnabled = ai === 'true';
                window.ENABLE_AI = isEnabled;
                this._setToggle('aiToggle', isEnabled);
                this._setToggle('modalAiToggle', isEnabled);
            }
            
            if (mode) {
                const modeInput = document.getElementById('activeModeInput');
                if (modeInput) modeInput.value = mode;
                this._updateModeUISilent(mode);
            }

            if (ltr !== null) {
                this._setToggle('ltrToggle', ltr === 'true');
            }
        } finally {
            // Re-enable syncing after a small delay to ensure DOM is ready
            setTimeout(() => { this.isInitializing = false; }, 100);
        }
    },

    /**
     * Synchronizes everything: Storage, URL, and DOM
     */
    syncAll: function(state = null) {
        const s = state || this.getUIState();
        
        // CROSS-UI SYNC: Ensure both toggles match the "truth"
        this._setToggle('aiToggle', s.ai);
        this._setToggle('modalAiToggle', s.ai);
        
        this.saveToStorage(s);
        
        if (typeof URLManager !== 'undefined') {
            URLManager.updateHistory(s);
        }
    },

    // --- Private Helpers ---

    _setToggle: function(id, checked) {
        const el = document.getElementById(id);
        if (el) el.checked = checked;
    },

    _updateModeUISilent: function(mode) {
        // 1. Update Custom Dropdown UI
        const items = document.querySelectorAll('.dropdown-item-custom');
        items.forEach(item => {
            if (item.dataset.value === mode) {
                const iconClass = item.dataset.icon;
                const labelText = item.querySelector('.item-header span')?.textContent;
                
                const currentModeLabel = document.getElementById('currentModeLabel');
                const currentModeIcon = document.getElementById('currentModeIcon');
                
                if (currentModeLabel && labelText) currentModeLabel.textContent = labelText;
                if (currentModeIcon && iconClass) currentModeIcon.innerHTML = `<i class="bi ${iconClass}"></i>`;
                
                items.forEach(i => i.classList.remove('active'));
                item.classList.add('active');
            }
        });

        // 2. Update Settings Modal (Silent)
        const modeOptions = document.querySelectorAll('.mode-option');
        modeOptions.forEach(opt => {
            if (opt.dataset.mode === mode) {
                modeOptions.forEach(o => o.classList.remove('active'));
                opt.classList.add('active');
            }
        });

        // 3. Update Sync Radios (Backwards Compatibility)
        const allRadios = document.querySelectorAll('input[name="searchMode"], input[name="commandMode"]');
        allRadios.forEach(radio => {
            if (radio.value === mode) radio.checked = true;
        });
    }
};

// Initial restoration on script load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => StateManager.restoreFromStorage());
} else {
    StateManager.restoreFromStorage();
}
