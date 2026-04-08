/**
 * Industrial API Service Layer
 * Centralizes all backend communication for the Hybrid Search Dashboard.
 */

const ApiService = {
    /**
     * Standard Fetch Wrapper with Error Handling
     */
    async _fetch(url, options = {}) {
        try {
            const response = await fetch(url, options);
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }
            return response;
        } catch (error) {
            console.error(`[ApiService Error] ${url}:`, error);
            throw error;
        }
    },

    /**
     * Executes a Search Query (AJAX)
     */
    async search(params) {
        const queryStr = params.toString();
        const url = `/?${queryStr}&ajax=1`;
        const response = await this._fetch(url, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        return await response.json();
    },

    /**
     * Deletes a Document
     */
    async deleteDocument(docId, formData) {
        // Force AJAX via URL parameter to be certain
        const url = `/document/${docId}/delete_post?ajax=1`;
        const response = await this._fetch(url, {
            method: 'POST',
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            body: formData
        });
        return await response.json();
    },

    /**
     * Assistant Streaming Interaction
     * Note: Returns the reader for streaming processing
     */
    async assistantChatStream(payload) {
        const response = await this._fetch('/api/quick-chat-stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        return response.body.getReader();
    },

    /**
     * Saves a new document to the database
     */
    async saveDocument(payload) {
        let body;
        let headers = {};

        if (payload instanceof FormData) {
            body = payload;
            // Browser sets Content-Type for FormData automatically
        } else if (typeof payload === 'object') {
            // Convert to URLSearchParams for request.form compatibility
            body = new URLSearchParams();
            for (const key in payload) {
                body.append(key, payload[key]);
            }
            body.append('ajax', '1'); // Force AJAX mode
            headers['Content-Type'] = 'application/x-www-form-urlencoded';
        } else {
            body = payload;
        }

        const response = await this._fetch('/document/new_post', {
            method: 'POST',
            headers: headers,
            body: body
        });
        return await response.json();
    }
};
