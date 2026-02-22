/**
 * Search Dynamic Logic
 * Handles dynamic search submission and result rendering without full page reloads
 */

async function handleDynamicSearch(query, searchMode, page = 1) {
    const historyArea = document.getElementById('historyArea');
    const searchBtn = document.querySelector('.search-btn');
    const textarea = document.querySelector('.search-input');
    
    // 1. Loading State & turn setup
    searchBtn.classList.add('loading');
    searchBtn.disabled = true;

    // Generate unique ID for this search "turn"
    const turnId = 'turn-' + Date.now();
    const turnDiv = document.createElement('div');
    turnDiv.id = turnId;
    turnDiv.className = 'search-turn-container mb-4';
    if (historyArea) historyArea.appendChild(turnDiv);

    // Clear input immediately for better UX
    if (textarea && page === 1) {
        textarea.value = '';
        textarea.style.height = 'auto';
    }

    // Show user query + shimmer in this specific turn
    turnDiv.innerHTML = `
        <div class="message message-user-turn d-flex gap-3 mb-3">
            <div class="chat-avatar user-avatar">
                <i class="bi bi-person-fill"></i>
            </div>
            <div class="query-container">
                <div class="message-query">
                    ${query}
                </div>
                <div class="user-actions">
                    <button class="user-action-btn" 
                            onclick="copyToClipboard(this, this.dataset.query)" 
                            data-query="${query.replace(/"/g, '&quot;')}"
                            title="Copy Prompt">
                        <i class="bi bi-copy"></i>
                    </button>
                </div>
            </div>
        </div>
        <div class="turn-results">
            <div class="message message-ai-turn d-flex gap-3">
                <div class="chat-avatar ai-avatar">
                    <i class="bi bi-robot"></i>
                </div>
                <div class="message-response flex-grow-1">
                    <div class="shimmer-preview px-2">
                        <div class="shimmer-line mb-3"></div>
                        <div class="shimmer-line mb-3 w-75"></div>
                    </div>
                </div>
            </div>
        </div>`;

    try {
        const fusionStrategy = document.querySelector('input[name="fusion_strategy"]')?.value || 'linear';
        const useLtr = document.querySelector('input[name="use_ltr"]')?.checked || false;
        const useAi = document.querySelector('input[name="use_ai"]')?.checked || false;

        const params = new URLSearchParams({
            query: query,
            mode: searchMode,
            fusion_strategy: fusionStrategy,
            use_ltr: useLtr ? 'on' : 'off',
            use_ai: useAi ? 'on' : 'off',
            page: page
        });

        const fetchParams = new URLSearchParams(params);
        fetchParams.append('ajax', '1');

        // Update URL only for main searches (page 1)
        if (page === 1) {
            window.history.pushState({}, '', `/?${params.toString()}`);
        }

        // 2. Fetch Results
        const response = await fetch(`/?${fetchParams.toString()}`, {
            headers: { 
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`Server returned status ${response.status}`);
        }

        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            throw new Error('Server did not return JSON. Please check if you are logged out or if there is a server error.');
        }

        const data = await response.json();

        // 3. Render Results into THIS turn
        renderSearchResults(data, turnId);

        // 4. Trigger AI Answer if enabled & page 1
        if (useAi && page === 1 && typeof triggerAIAnswer === 'function') {
            triggerAIAnswer(turnId);
        }

    } catch (err) {
        console.error("Dynamic search failed", err);
        const resultsArea = turnDiv.querySelector('.turn-results');
        if (resultsArea) {
            resultsArea.innerHTML = `<div class="alert alert-danger">Search failed: ${err.message}</div>`;
        }
    } finally {
        searchBtn.classList.remove('loading');
        searchBtn.disabled = false;
        
        // Scroll to the top of the NEW turn
        if (turnDiv) {
            turnDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }
}

function renderSearchResults(data, turnId) {
    const turnDiv = document.getElementById(turnId);
    if (!turnDiv) return;
    
    const resultsArea = turnDiv.querySelector('.turn-results');
    if (!resultsArea) return;

    if (!data.results || data.results.length === 0) {
        resultsArea.innerHTML = `
            <div class="message message-ai-turn d-flex gap-3">
                <div class="chat-avatar ai-avatar">
                    <i class="bi bi-robot"></i>
                </div>
                <div class="message-response flex-grow-1">
                    <div class="result-item py-2 border-bottom-0">
                        <div class="d-flex align-items-baseline gap-2 mb-2 text-muted small">
                             <strong>Search Assistant</strong>
                        </div>
                        <div class="result-content mb-0" style="font-size: 0.9rem; color: #6b7280; text-align: left;">
                            No results found for "${data.query}". Try adjusting your keywords or switching to <strong>Semantic</strong> mode.
                        </div>
                    </div>
                </div>
            </div>`;
        return;
    }

    const { results, stats, mode, query } = data;
    
    let resultsHtml = `
        <div class="message message-ai-turn d-flex gap-3">
            <div class="chat-avatar ai-avatar">
                <i class="bi bi-robot"></i>
            </div>
            <div class="message-response flex-grow-1">
                <div class="response-header d-flex justify-content-between align-items-center mb-3">
                    <span class="text-muted small">${stats.returned} results found in ${stats.query_time_ms}ms</span>
                    <button class="btn btn-sm btn-outline-primary" style="border-radius: 5px; font-size: 0.8rem;"
                        onclick="showSessionAnalysis(this)"
                        data-p="${stats.precision_at_k}"
                        data-r="${stats.recall_at_k}"
                        data-map="${stats.map_score}"
                        data-ndcg="${stats.ndcg_score}"
                        data-qpms="${stats.qpms}"
                        data-latency="${stats.query_time_ms}"
                        data-router="${stats.router_accuracy}"
                        data-choice="${stats.router_choice}"
                        data-prompt="${query}"
                        data-rank-debug='${JSON.stringify(stats.rank_debug || {})}'
                        data-latency-stats='${JSON.stringify(stats.latency_stats || {})}'>
                        <i class="bi bi-bar-chart-fill"></i> Query Analysis
                    </button>
                </div>`;

    results.forEach(r => {
        const scoreClass = r.score >= 0.7 ? 'score-high' : (r.score >= 0.4 ? 'score-medium' : 'score-low');
        const formattedScore = r.score.toFixed(3);
        
        resultsHtml += `
            <div class="result-item">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <span class="result-doc-id fw-bold text-primary">#${r.doc_id}</span>
                    <span class="score-badge ${scoreClass}">
                        ${formattedScore}
                    </span>
                </div>
                
                <div class="result-content mb-2" title="Double click to copy">
                    ${r.content_highlighted || r.content}
                </div>
                
                <div class="result-meta d-flex justify-content-between align-items-center">
                    <span class="d-flex align-items-center">
                        Score: ${formattedScore} • ${r.language.toUpperCase()} • ${r.created_at}
                        <label class="relevance-toggle" title="Mark as Relevant (Ground Truth)">
                            <input type="checkbox" onchange="toggleRelevance(this)" data-doc-id="${r.doc_id}">
                            Relevant?
                        </label>
                    </span>
                    <div class="result-actions d-flex justify-content-end align-items-center gap-2 mt-2">
                        <button class="btn btn-sm btn-outline-info d-flex align-items-center px-2" 
                            style="font-size: 0.75rem; height: 24px; border-radius: 4px;"
                            onclick="showAnalysis(this)"
                            data-doc-id="${r.doc_id}"
                            data-score="${r.score}"
                            data-sem="${r.semantic_score || 'N/A'}"
                            data-key="${r.bm25_score || 'N/A'}"
                            data-sem-w="${r.semantic_weight || 'N/A'}"
                            data-key-w="${r.bm25_weight || 'N/A'}"
                            data-strategy="${r.strategy || 'Linear'}"
                            data-mode="${r.origin_mode || mode}"
                            data-prompt="${query.replace(/'/g, "&apos;")}"
                            data-content="${r.content.substring(0, 4000).replace(/'/g, "&apos;")}"
                            data-latency="${stats.query_time_ms}">
                            <i class="bi bi-graph-up me-1"></i> Analysis
                        </button>
                        <button class="btn btn-sm btn-outline-secondary d-flex align-items-center justify-content-center" 
                            style="width: 28px; height: 24px; border-radius: 4px; padding: 0;"
                            onclick="copyToClipboard(this, this.dataset.content)"
                            data-content="${escapeHTML(r.content.substring(0, 4000))}"
                            title="Copy Content">
                            <i class="bi bi-copy"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-primary d-flex align-items-center justify-content-center"
                            style="width: 28px; height: 24px; border-radius: 4px; padding: 0;"
                            onclick="openEditModal('${r.doc_id}', this.dataset.content, '${query.replace(/'/g, "\\'")}', '${mode}', '${r.language}')"
                            data-content="${escapeHTML(r.content)}"
                            title="Edit Result">
                            <i class="bi bi-pencil" style="font-size: 0.75rem;"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger d-flex align-items-center justify-content-center"
                            style="width: 28px; height: 24px; border-radius: 4px; padding: 0;"
                            onclick="deleteRecord('${r.doc_id}')" 
                            title="Delete Result">
                            <i class="bi bi-trash" style="font-size: 0.75rem;"></i>
                        </button>
                    </div>
                </div>
            </div>`;
    });

    // Add unique AI Insight area for the whole turn after results loop
    resultsHtml += `
            <!-- AI Insight area for dynamic turn -->
            <div class="ai-research-box d-none mt-4">
                <div class="ai-research-header">
                    <span class="d-flex align-items-center gap-2">
                        <i class="bi bi-robot"></i> <strong>AI Insight</strong>
                    </span>
                    <div class="loading-shimmer d-none spinner-ai"></div>
                </div>
                <div class="ai-research-body">
                    <div class="ai-answer-text">
                        <!-- Content will be streamed here -->
                    </div>
                </div>
                <div class="ai-research-footer d-none pt-3 mt-3 border-top">
                    <!-- Footer content -->
                </div>
            </div>
        </div>
    </div>`;

    resultsArea.innerHTML = resultsHtml;
}

function escapeHTML(str) {
    if (!str) return '';
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&apos;');
}

