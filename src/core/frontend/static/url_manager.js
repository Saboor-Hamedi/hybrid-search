/**
 * URL Manager Utility
 * Handles Clean URL generation and state synchronization
 */

const URLManager = {
    // Defaults for comparison
    DEFAULTS: {
        mode: 'hybrid',
        fusion: 'linear',
        ltr: false,
        ai: true,
        page: 1
    },

    /**
     * Builds a clean URLSearchParams object by omitting defaults
     * @param {Object} state - { query, mode, fusion, ltr, ai, page }
     * @returns {URLSearchParams}
     */
    buildCleanParams: function(state) {
        const params = new URLSearchParams();
        
        // Always include query
        if (state.query) params.set('q', state.query);
        
        // Only include if non-default
        if (state.mode && state.mode !== this.DEFAULTS.mode) {
            params.set('mode', state.mode);
        }
        
        if (state.fusion && state.fusion !== this.DEFAULTS.fusion) {
            params.set('fusion', state.fusion);
        }
        
        if (state.ltr) {
            params.set('ltr', '1');
        }
        
        // AI is ON by default, so only set if it's OFF
        if (state.ai === false) {
            params.set('ai', '0');
        }
        
        if (state.page && state.page > this.DEFAULTS.page) {
            params.set('p', state.page);
        }
        
        return params;
    },

    /**
     * Updates the browser history with a clean URL
     */
    updateHistory: function(state) {
        const params = this.buildCleanParams(state);
        const url = params.toString() ? `/?${params.toString()}` : '/';
        window.history.pushState(state, '', url);
    }
};
