/**
 * Command Palette (Ctrl+K) Functionality
 * 
 * Provides quick search access via keyboard shortcut
 */

(function () {
    'use strict';

    // Get modal element
    const commandModal = document.getElementById('commandPaletteModal');
    const commandInput = document.getElementById('commandPaletteInput');
    const commandResults = document.getElementById('commandResults');
    const commandResultsList = document.getElementById('commandResultsList');

    if (!commandModal || !commandInput) {
        console.warn('Command palette elements not found');
        return;
    }

    // Initialize Bootstrap modal
    const bsModal = new bootstrap.Modal(commandModal, {
        keyboard: true,
        backdrop: true
    });

    /**
     * Open command palette
     */
    function openCommandPalette() {
        bsModal.show();

        // Focus input after modal is shown
        commandModal.addEventListener('shown.bs.modal', function () {
            commandInput.focus();
            commandInput.select();
        }, { once: true });
    }

    /**
     * Close command palette
     */
    function closeCommandPalette() {
        bsModal.hide();
    }

    /**
     * Get selected search mode
     */
    function getSelectedMode() {
        const checkedMode = document.querySelector('input[name="commandMode"]:checked');
        return checkedMode ? checkedMode.value : 'hybrid';
    }

    /**
     * Execute search
     */
    function executeSearch() {
        const query = commandInput.value.trim();

        if (!query) {
            return;
        }

        const mode = getSelectedMode();
        const pageSize = 50; // Default page size

        const fusionStrategy = document.getElementById('fusionStrategy').value;
        const useLtr = document.getElementById('ltrToggle').checked;
        
        // Capture AI Toggle state from main UI to persist it
        const aiToggle = document.getElementById('aiToggle');
        const useAi = aiToggle ? aiToggle.checked : false;

        // Build search URL
        const params = new URLSearchParams({
            query: query,
            mode: mode,
            page_size: pageSize,
            page: 1,
            fusion_strategy: fusionStrategy,
            use_ltr: useLtr ? 'on' : 'off',
            use_ai: useAi ? 'on' : 'off'
        });

        // Navigate to search results
        window.location.href = `/?${params.toString()}`;
    }

    /**
     * Handle keyboard shortcuts
     */
    document.addEventListener('keydown', function (e) {
        // Ctrl+K or Cmd+K to open
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            openCommandPalette();
        }

        // Escape to close (when modal is open)
        if (e.key === 'Escape' && commandModal.classList.contains('show')) {
            closeCommandPalette();
        }
    });

    /**
     * Handle Enter key in command input
     */
    commandInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            executeSearch();
            closeCommandPalette();
        }
    });

    /**
     * Sync command palette mode with main form mode
     */
    function syncModeFromMainForm() {
        const mainModeInput = document.querySelector('input[name="mode"]:checked');
        if (mainModeInput) {
            const currentMode = mainModeInput.value;
            const commandModeRadio = document.querySelector(`input[name="commandMode"][value="${currentMode}"]`);
            if (commandModeRadio) {
                commandModeRadio.checked = true;
            }
        }
    }

    /**
     * Update main form mode when command palette mode changes
     */
    document.querySelectorAll('input[name="commandMode"]').forEach(radio => {
        radio.addEventListener('change', function () {
            const mainModeRadio = document.querySelector(`input[name="mode"][value="${this.value}"]`);
            if (mainModeRadio) {
                mainModeRadio.click(); // Click to trigger any attached listeners
            }
        });
    });

    /**
     * Optional: Live search preview (debounced)
     */
    let searchTimeout;
    commandInput.addEventListener('input', function () {
        clearTimeout(searchTimeout);

        const query = this.value.trim();

        if (query.length < 3) {
            commandResults.classList.add('d-none');
            return;
        }

        // Debounce search
        searchTimeout = setTimeout(function () {
            // You can implement live preview here
            // For now, we'll just show a hint
            commandResults.classList.remove('d-none');
            commandResultsList.innerHTML = `
                <div class="text-center py-3 text-muted">
                    <i class="bi bi-info-circle me-2"></i>
                    Press <kbd>Enter</kbd> to search for "${query}"
                </div>
            `;
        }, 300);
    });

    /**
     * Clear results when modal is hidden
     */
    commandModal.addEventListener('hidden.bs.modal', function () {
        commandInput.value = '';
        commandResults.classList.add('d-none');
        commandResultsList.innerHTML = '';
    });

    /**
     * Initialize: Sync mode on page load
     */
    syncModeFromMainForm();

    /**
     * Add visual indicator for Ctrl+K shortcut
     */
    function addKeyboardHint() {
        const searchInput = document.querySelector('input[name="query"]');
        if (searchInput && !searchInput.dataset.hintAdded) {
            searchInput.placeholder = 'Enter your search query... (or press Ctrl+K)';
            searchInput.dataset.hintAdded = 'true';
        }
    }

    // Add hint on page load
    addKeyboardHint();

    // Export functions for external use
    window.commandPalette = {
        open: openCommandPalette,
        close: closeCommandPalette,
        getMode: getSelectedMode
    };

    console.log('✓ Command Palette initialized (Ctrl+K to open)');
})();
