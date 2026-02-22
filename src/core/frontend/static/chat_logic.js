// === UX ENHANCEMENTS ===

// Auto-resize textarea
const textarea = document.querySelector('.search-input');
textarea?.addEventListener('input', function() {
  this.style.height = 'auto';
  // Use scrollHeight but ensure it feels aligned with the 32px-52px range
  this.style.height = (this.scrollHeight) + 'px';
});

// Handle Enter key to submit
textarea?.addEventListener('keydown', function(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    const form = this.closest('form');
    if (form) {
      // Create and dispatch a submit event or call the submit method
      // Note: form.submit() doesn't fire the 'submit' event listener, 
      // so we use requestSubmit() or click the button.
      form.requestSubmit ? form.requestSubmit() : form.querySelector('button[type="submit"]')?.click();
    }
  }
});

// Search Mode Dropdown Logic (Legacy - Only if elements exist)
const modeTrigger = document.getElementById('modeTrigger');
const modeMenu = document.getElementById('modeMenu');
const modeItems = document.querySelectorAll('.dropdown-item-custom');
const activeModeInput = document.getElementById('activeModeInput');
const currentModeLabel = document.getElementById('currentModeLabel');
const currentModeIcon = document.getElementById('currentModeIcon');

if (modeTrigger && modeMenu) {
  modeTrigger.addEventListener('click', (e) => {
    e.stopPropagation();
    modeMenu.classList.toggle('show');
  });

  modeItems.forEach(item => {
    item.addEventListener('click', function() {
      const val = this.dataset.value;
      const iconClass = this.dataset.icon;
      const labelText = this.querySelector('.item-header span').textContent;

      modeItems.forEach(i => i.classList.remove('active'));
      this.classList.add('active');
      
      if (currentModeLabel) currentModeLabel.textContent = labelText;
      if (currentModeIcon) currentModeIcon.innerHTML = `<i class="bi ${iconClass}"></i>`;
      if (activeModeInput) activeModeInput.value = val;
      modeMenu.classList.remove('show');
    });
  });

  document.addEventListener('click', () => {
    modeMenu.classList.remove('show');
  });
}

// Loading state on form submit
const searchForm = document.querySelector('.search-form');
const searchBtn = document.querySelector('.search-btn');

if (searchForm && searchBtn) {
  // Mode Toggle Logic
  const typePills = document.querySelectorAll('.type-pill');
  const activeSearchType = document.getElementById('activeSearchType');
  const searchInput = document.querySelector('.search-input');

  typePills.forEach(pill => {
    pill.addEventListener('click', () => {
      typePills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      const type = pill.dataset.type;
      activeSearchType.value = type;
      
      // Visual feedback
      if (type === 'assistant') {
        searchInput.placeholder = "Chat with AI Assistant...";
        document.body.classList.add('assistant-mode-active');
      } else {
        searchInput.placeholder = "Ask me anything...";
        document.body.classList.remove('assistant-mode-active');
      }
    });
  });

    searchForm.addEventListener('submit', async function(e) {
    const query = textarea.value.trim();
    if (!query) {
      e.preventDefault();
      textarea.focus();
      return;
    }

    // 1. Intercept for SPA behavior
    e.preventDefault();

    // Check if we need to transition from welcome state
    const chatContainer = document.querySelector('.chat-container');
    if (chatContainer && chatContainer.classList.contains('is-empty-chat')) {
        chatContainer.classList.remove('is-empty-chat');
        document.body.classList.add('is-query-active');
    }

    // 2. Handle Assistant mode (Existing)
    if (activeSearchType.value === 'assistant') {
      await handleAssistantChat(query);
    } 
    // 3. Handle Normal/Hybrid Search dynamically
    else if (typeof handleDynamicSearch === 'function') {
      const modeInput = document.getElementById('activeModeInput');
      await handleDynamicSearch(query, modeInput?.value || 'hybrid');
    } else {
      // Fallback if script not loaded (should not happen)
      searchForm.submit();
      return; 
    }
  });
}

// Keyboard Shortcuts
let keyboardHint = null;

// Create keyboard hint element
function createKeyboardHint() {
  if (!keyboardHint) {
    keyboardHint = document.createElement('div');
    keyboardHint.className = 'keyboard-hint';
    keyboardHint.innerHTML = 'Press <kbd>/</kbd> to search • <kbd>Ctrl+K</kbd> for modal • <kbd>Esc</kbd> to clear';
    document.body.appendChild(keyboardHint);
  }
}

// Show keyboard hint temporarily
function showKeyboardHint() {
  createKeyboardHint();
  keyboardHint.classList.add('show');
  setTimeout(() => {
    keyboardHint.classList.remove('show');
  }, 2000);
}

// Global keyboard shortcuts
document.addEventListener('keydown', function(e) {
  // "/" to focus search (like Discord/Slack)
  if (e.key === '/' && !['INPUT', 'TEXTAREA'].includes(e.target.tagName)) {
    e.preventDefault();
    textarea?.focus();
    showKeyboardHint();
  }
  
  // Escape to clear search when focused on input
  if (e.key === 'Escape' && e.target === textarea) {
    textarea.value = '';
    textarea.blur();
  }
});

// Show hint on first visit
setTimeout(() => {
  if (!sessionStorage.getItem('keyboardHintShown')) {
    showKeyboardHint();
    sessionStorage.setItem('keyboardHintShown', 'true');
  }
}, 1000);

// Example searches functionality
const exampleSearches = document.querySelectorAll('.example-search');
exampleSearches.forEach(example => {
  example.addEventListener('click', function() {
    const searchText = this.textContent.trim();
    if (textarea) {
      textarea.value = searchText;
      textarea.focus();
      // Trigger resize
      textarea.dispatchEvent(new Event('input'));
    }
  });
});

// Auto-focus management after search
window.addEventListener('load', () => {
  // If there's a query but textarea is empty, keep it ready for next search
  const hasResults = document.querySelectorAll('.result-item').length > 0;
  if (hasResults && textarea) {
    // Don't auto-focus on mobile
    if (window.innerWidth > 768) {
      setTimeout(() => textarea.focus(), 100);
    }
  }
});

// Scroll to bottom on page load if there are results
function scrollToBottom() {
  setTimeout(() => {
    const messagesArea = document.getElementById('messagesArea');
    messagesArea?.scrollTo(0, messagesArea.scrollHeight);
  }, 100);
}

// Result quick actions (copy on double-click)
document.querySelectorAll('.result-content').forEach(result => {
  let clickCount = 0;
  let clickTimer = null;
  
  result.addEventListener('click', function(e) {
    // Don't interfere with link clicks
    if (e.target.tagName === 'A') return;
    
    clickCount++;
    
    if (clickCount === 1) {
      clickTimer = setTimeout(() => {
        clickCount = 0;
      }, 300);
    } else if (clickCount === 2) {
      clearTimeout(clickTimer);
      // Copy content on double-click
      const text = this.textContent.trim();
      navigator.clipboard.writeText(text).then(() => {
        // Show brief feedback
        const original = this.style.background;
        this.style.background = '#dbeafe';
        setTimeout(() => {
          this.style.background = original;
        }, 200);
      });
      clickCount = 0;
    }
  });
});

// Smooth scroll enhancement for pagination
document.querySelectorAll('.pagination-btns form').forEach(form => {
  form.addEventListener('submit', function() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
});

// Close modal on outside click
document.getElementById('createModal')?.addEventListener('click', function(e) {
  if (e.target === this) {
    this.style.display = 'none';
  }
});

// Prevent form resubmission on refresh
if (window.history.replaceState) {
  window.history.replaceState(null, null, window.location.href);
}

// Close Create Modal Helper
function closeCreateModal() {
  document.getElementById('createModal').style.display = 'none';
}

// === Analysis Modal Logic ===
let analysisChart = null;

// Helper to switch tabs
function showAnalysisTab(tabId) {
    const triggerEl = document.querySelector(`#analysisTabs button[data-bs-target="${tabId}"]`);
    if (triggerEl) {
        bootstrap.Tab.getOrCreateInstance(triggerEl).show();
    }
}

function showAnalysis(btn) {
    showAnalysisTab('#basicTab'); // Default to first tab
    
    const d = btn.dataset;
    // Try to get prompt from button, or fall back to the search input value
    const currentQuery = d.prompt || document.querySelector('input[name="query"]')?.value || document.querySelector('textarea[name="query"]')?.value || "-";
    document.getElementById('modalPrompt').textContent = currentQuery;
    document.getElementById('metricDocId').textContent = "Doc #" + d.docId; // Set Focus

    // Initialize Latency directly from button if available
    if (d.latency) {
         const lat = parseFloat(d.latency);
         document.getElementById('metricLatency').textContent = lat + ' ms';
         window.currentLatency = lat;
         
         // Try to calculate QpMS immediately if Session NDCG exists
         const sessionBtn = document.querySelector('button[onclick="showSessionAnalysis(this)"]');
         if (sessionBtn && sessionBtn.dataset.ndcg && sessionBtn.dataset.ndcg !== 'N/A') {
             const ndcg = parseFloat(sessionBtn.dataset.ndcg);
             const qpms = (ndcg / lat) * 1000;
             document.getElementById('metricQpMS').textContent = qpms.toFixed(4);
         } else {
             document.getElementById('metricQpMS').textContent = '-';
         }
    }
    
    // Populate Table
    document.getElementById('modalTableDocId').textContent = '#' + d.docId;
    document.getElementById('modalTableFinal').textContent = parseFloat(d.score).toFixed(4);
    document.getElementById('modalTableStrategy').textContent = d.strategy.toUpperCase();
    document.getElementById('modalTableMode').textContent = d.mode.toUpperCase();
    
    document.getElementById('modalTableSem').textContent = d.sem !== 'N/A' ? parseFloat(d.sem).toFixed(4) : 'N/A';
    document.getElementById('modalTableKey').textContent = d.key !== 'N/A' ? parseFloat(d.key).toFixed(4) : 'N/A';
    
    document.getElementById('modalTableSemW').textContent = d.semW !== 'N/A' ? parseFloat(d.semW).toFixed(2) : '-';
    document.getElementById('modalTableKeyW').textContent = d.keyW !== 'N/A' ? parseFloat(d.keyW).toFixed(2) : '-';
    
    document.getElementById('modalContentPreview').innerHTML = d.content; // using innerHTML to render highlights if present
    
    // Chart Data Prep
    updateRadar(d);
    
    // Attempt to pre-load the Strategy Chart (Session context) even in Doc view
    preloadStrategyChart();

    new bootstrap.Modal(document.getElementById('analysisModal')).show();
}

function showSessionAnalysis(btn) {
    showAnalysisTab('#metricsTab');
    
    const d = btn.dataset;
    document.getElementById('modalPrompt').textContent = d.prompt || "No query recorded"; // Set Prompt
    document.getElementById('metricDocId').textContent = "Session Overview"; // Reset Focus
    
    // 1. Effectiveness
    document.getElementById('metricP').textContent = d.p !== 'N/A' ? parseFloat(d.p).toFixed(4) : 'N/A';
    document.getElementById('metricR').textContent = d.r !== 'N/A' ? parseFloat(d.r).toFixed(4) : 'N/A';
    document.getElementById('metricMAP').textContent = d.map !== 'N/A' ? parseFloat(d.map).toFixed(4) : 'N/A';
    document.getElementById('metricNDCG').textContent = d.ndcg !== 'N/A' ? parseFloat(d.ndcg).toFixed(4) : 'N/A';
    
    // 2. Efficiency
    document.getElementById('metricLatency').textContent = d.latency + ' ms';
    document.getElementById('metricQpMS').textContent = d.qpms !== 'N/A' ? parseFloat(d.qpms).toFixed(4) : 'N/A';
    
    // 3. Router
    document.getElementById('metricRouter').textContent = d.router !== 'N/A' ? (parseFloat(d.router)*100).toFixed(0) + '%' : 'N/A';
    
    const routerBadge = document.getElementById('metricRouterBadge');
    if (d.choice === 'Hybrid') {
        routerBadge.className = 'badge bg-primary';
        routerBadge.textContent = 'Correct'; // Mock logic for now
    } else {
        routerBadge.className = 'badge bg-secondary';
        routerBadge.textContent = d.choice;
    }
    
    // Load Chart
    preloadStrategyChart();
    
    new bootstrap.Modal(document.getElementById('analysisModal')).show();
}

// Helper: Loads the chart data from the Session Button without needing a toggle event
function preloadStrategyChart() {
    const sessionBtn = document.querySelector('button[onclick="showSessionAnalysis(this)"]');
    if (sessionBtn && sessionBtn.dataset.rankDebug && window.updateComparisonChart) {
        try {
            const rankDebug = JSON.parse(sessionBtn.dataset.rankDebug);
            // Calculate using current ground truth (judgedDocs)
            // If judgedDocs is empty, scores will be 0 (correct)
            const sem = calculateSingleStrategyNDCG(rankDebug.semantic, judgedDocs, sessionK);
            const key = calculateSingleStrategyNDCG(rankDebug.keyword, judgedDocs, sessionK);
            
            // Get current hybrid ndcg from button or calc
            const hybrid = sessionBtn.dataset.ndcg !== 'N/A' ? parseFloat(sessionBtn.dataset.ndcg) : 0;
            
            window.updateComparisonChart(sem, key, hybrid);
        } catch(e) { console.error("Chart preload error", e); }
    }
}


function copyAnalysisData() {
    let textSummary = "";
    
    // Determine mode based on Focus
    // It seems 'metricDocId' is used for Thesis tab focus, 
    // but we can also check the Active Tab if needed.
    // However, the user flow implies we care about what is SHOWN.
    
    const metricFocus = document.getElementById('metricDocId').textContent;
    const isSessionMode = metricFocus === "Session Overview";
    
    // Gather Basic Data (might be empty/dashes if in Session Mode, but we grab dom elements safely)
    const contextData = {
        doc_id: document.getElementById('modalTableDocId').textContent,
        final_score: document.getElementById('modalTableFinal').textContent,
        strategy: document.getElementById('modalTableStrategy').textContent,
        mode: document.getElementById('modalTableMode').textContent,
        semantic: {
            score: document.getElementById('modalTableSem').textContent,
            weight: document.getElementById('modalTableSemW').textContent
        },
        keyword: {
            score: document.getElementById('modalTableKey').textContent,
            weight: document.getElementById('modalTableKeyW').textContent
        },
        prompt: document.getElementById('modalPrompt').textContent,
        result_content: document.getElementById('modalContentPreview').innerText.replace(/\n+/g, ' ').trim()
    };

    if (isSessionMode) {
        textSummary += `=== Session Analysis ===\n`;
        textSummary += `Prompt: "${contextData.prompt}"\n`;
        
        // List Judged Docs
        if (typeof judgedDocs !== 'undefined' && judgedDocs.size > 0) {
            textSummary += `Relevant Docs: ${Array.from(judgedDocs).map(id => '#'+id).join(', ')}\n`;
        } else {
            textSummary += `Relevant Docs: None marked.\n`;
        }
    } else {
        // Single Document Mode
        textSummary += `Doc: ${contextData.doc_id}\n`;
        textSummary += `Final Score: ${contextData.final_score}\n`;
        textSummary += `Strategy: ${contextData.strategy}\n`;
        textSummary += `Mode: ${contextData.mode}\n`;
        textSummary += `Semantic: ${contextData.semantic.score} (w=${contextData.semantic.weight})\n`;
        textSummary += `Keyword: ${contextData.keyword.score} (w=${contextData.keyword.weight})\n`;
        textSummary += `Prompt: "${contextData.prompt}"\n\n`;
        textSummary += `Result: "${contextData.result_content}"\n`;
    }

    textSummary += `\n__\nThesis Metrics (Session)\n`;
    textSummary += `---------------------\n`;

    // 2. Collect Thesis Metrics Data
    const metricsData = {
        focus: metricFocus,
        effectiveness: {
            precision: document.getElementById('metricP').textContent,
            recall: document.getElementById('metricR').textContent,
            map: document.getElementById('metricMAP').textContent,
            mrr: document.getElementById('metricMRR').textContent, // New
            ndcg: document.getElementById('metricNDCG').textContent
        },
        efficiency: {
            latency: document.getElementById('metricLatency').textContent,
            qpms: document.getElementById('metricQpMS').textContent
        },
        router: {
            accuracy: document.getElementById('metricRouter').textContent
        }
    };
    
    textSummary += `PRECISION@K: ${metricsData.effectiveness.precision}\n`;
    textSummary += `RECALL@K:   ${metricsData.effectiveness.recall}\n`;
    textSummary += `MAP:        ${metricsData.effectiveness.map}\n`;
    textSummary += `MRR:        ${metricsData.effectiveness.mrr}\n`; // New
    textSummary += `NDCG@10:    ${metricsData.effectiveness.ndcg}\n\n`;
    textSummary += `LATENCY:    ${metricsData.efficiency.latency}\n`;
    textSummary += `QpMS:       ${metricsData.efficiency.qpms}\n\n`;
    textSummary += `ROUTER ACC: ${metricsData.router.accuracy}`;

    navigator.clipboard.writeText(textSummary).then(() => {
        // Visual Feedback
        const btn = document.querySelector('button[onclick="copyAnalysisData()"] i');
        if(btn) {
            const originalClass = btn.className;
            btn.className = 'bi bi-check2 text-success';
            setTimeout(() => {
                btn.className = originalClass;
            }, 1500);
        }
    });
}

// === Manual Evaluation (Thesis Metrics) ===
let judgedDocs = new Set(); // Stores doc_ids marked as relevant
const sessionK = 10; // We evaluate Top 10 usually

function toggleRelevance(checkbox) {
    const docId = checkbox.dataset.docId;
    if (checkbox.checked) {
        judgedDocs.add(docId);
    } else {
        judgedDocs.delete(docId);
    }
    calculateAndSyncMetrics();
}

function calculateAndSyncMetrics() {
    // 1. gather current ranked list
    // We assume the DOM order is the ranked order (1 to N)
    const results = document.querySelectorAll('.result-item');
    let hits = 0;
    let rank = 1;
    let sumPrec = 0;
    let dcg = 0;
    let idcg = 0;
    
    // Total RELEVANT docs (Recall denominator). 
    // In a live user session, we assume 'Total Relevant' is just 'Total Marked So Far' 
    // unless we know there are hidden relevant docs. For this "Interactive" mode, 
    // we recall relative to what the user has found. 
    const totalRel = judgedDocs.size; 

    results.forEach((el, index) => {
        if (index >= sessionK) return; // effectively @10

        const box = el.querySelector('.relevance-toggle input');
        const rId = box.dataset.docId;
        const isRel = judgedDocs.has(rId);

        if (isRel) {
            hits++;
            sumPrec += hits / rank;
            dcg += 1 / Math.log2(rank + 1);
        }
        
        // Ideal DCG (Optimistic: if we had 'totalRel' hits at the top)
        if (rank <= totalRel) {
             idcg += 1 / Math.log2(rank + 1);
        }

        rank++;
    });

    // P@K (Precision at 10)
    const p_k = hits / Math.min(results.length, sessionK); 
    
    // Recall@K (Hits / Total Relevant)
    const r_k = totalRel > 0 ? hits / totalRel : 0; 

    // MAP (Mean Average Precision)
    const map = totalRel > 0 ? sumPrec / totalRel : 0;

    // NDCG
    const ndcg = idcg > 0 ? dcg / idcg : 0;
    
    // MRR (Mean Reciprocal Rank) = 1 / Rank of First Relevant Document
    // Loop again to find first relevant
    let mrr = 0;
    let rank2 = 1;
    for (const el of results) {
        if (rank2 > sessionK) break;
        const box = el.querySelector('.relevance-toggle input');
        if (judgedDocs.has(box.dataset.docId)) {
            mrr = 1.0 / rank2;
            break; // Found the first one
        }
        rank2++;
    }

    // --- Strategy Comparison Logic ---
    const btn = document.querySelector('button[onclick="showSessionAnalysis(this)"]');
    let compNDCG = { semantic: 0, keyword: 0 };
    
    if (btn && btn.dataset.rankDebug) {
        try {
            const rankDebug = JSON.parse(btn.dataset.rankDebug);
            compNDCG.semantic = calculateSingleStrategyNDCG(rankDebug.semantic, judgedDocs, sessionK);
            compNDCG.keyword = calculateSingleStrategyNDCG(rankDebug.keyword, judgedDocs, sessionK);
        } catch (e) {
            console.error("Error parsing rank debug data", e);
        }
    }

    // QpMS & Latency Chart
    let latency = 0;
    let latStats = { semantic: 0, keyword: 0, fusion: 0 };
    
    if (window.currentLatency) {
        latency = window.currentLatency;
    } else if (btn && btn.dataset.latency) {
        latency = parseFloat(btn.dataset.latency);
    }
    
    // Get Stacked Latency Data from Button
    if (btn && btn.dataset.latencyStats) {
        try {
            latStats = JSON.parse(btn.dataset.latencyStats);
        } catch(e) {}
    }

    const qpms = (latency > 0) ? (ndcg / latency) * 1000 : 0;

    updateSessionStats(p_k, r_k, map, ndcg, mrr, qpms, compNDCG, latStats);
}

function calculateSingleStrategyNDCG(idList, trueIds, k) {
    if (!idList || idList.length === 0) return 0.0;
    let dcg = 0;
    let idcg = 0;
    let rank = 1;
    let totalRel = trueIds.size;
    
    // Iterate top K of the STRATEGY list
    for (let i = 0; i < Math.min(idList.length, k); i++) {
        const id = String(idList[i]); // Ensure string comparison
        if (trueIds.has(id)) {
            dcg += 1 / Math.log2(rank + 1);
        }
        if (rank <= totalRel) {
            idcg += 1 / Math.log2(rank + 1);
        }
        rank++;
    }
    return idcg > 0 ? dcg / idcg : 0;
}

function updateSessionStats(p, r, map, ndcg, mrr, qpms, compStats, latStats) {
    const btn = document.querySelector('button[onclick="showSessionAnalysis(this)"]');
    if (!btn) return;

    // Update Data Attributes
    btn.dataset.p = p.toFixed(4);
    btn.dataset.r = r.toFixed(4);
    btn.dataset.map = map.toFixed(4);
    btn.dataset.ndcg = ndcg.toFixed(4);
    btn.dataset.mrr = mrr.toFixed(4); // New
    btn.dataset.qpms = qpms.toFixed(4);
    
    if (compStats) {
        btn.dataset.ndcgSem = compStats.semantic.toFixed(4);
        btn.dataset.ndcgKey = compStats.keyword.toFixed(4);
    }

    // If modal is open, update it live
    if (document.getElementById('metricP')) {
        document.getElementById('metricP').textContent = p.toFixed(4);
        document.getElementById('metricR').textContent = r.toFixed(4);
        document.getElementById('metricMAP').textContent = map.toFixed(4);
        document.getElementById('metricMRR').textContent = mrr.toFixed(4); // New
        document.getElementById('metricNDCG').textContent = ndcg.toFixed(4);
        document.getElementById('metricQpMS').textContent = qpms.toFixed(4);
        
        // Update Comparison Chart
        if (window.updateComparisonChart && compStats) {
            window.updateComparisonChart(compStats.semantic, compStats.keyword, ndcg);
        }
        
        // Update Latency Stack Chart
        if (window.updateLatencyChart && latStats) {
            window.updateLatencyChart(latStats.semantic || 0, latStats.keyword || 0, latStats.fusion || 0);
        }
    }
}


// --- Chart.js Initialization ---
document.addEventListener('DOMContentLoaded', function() {
    // Initial render
    // renderResults(fakeResults);
    
    // Init Charts
    initRadarChart();
    initComparisonChart();
    initLatencyChart();

    // Trigger AI Answer if results exist AND AI is enabled
    const items = document.querySelectorAll('.result-item');
    if (items.length > 0 && window.ENABLE_AI) {
        triggerAIAnswer();
    }
});


// --- Chart.js Globals ---

// --- Chart.js Globals ---
let radarChart = null;
let comparisonChart = null;
let latencyChart = null;

function initRadarChart() {
    const ctx = document.getElementById('scoreRadarChart');
    if (!ctx) return;
    
    radarChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['Semantic', 'Keyword', 'Date Relevance', 'Language Match', 'Popularity'],
            datasets: [{
                label: 'Score Profile',
                data: [0, 0, 0, 0, 0],
                fill: true,
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                borderColor: 'rgb(54, 162, 235)',
                pointBackgroundColor: 'rgb(54, 162, 235)',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: 'rgb(54, 162, 235)'
            }]
        },
        options: {
            elements: { line: { tension: 0.3 } },
            scales: { r: { beginAtZero: true, max: 1.0, ticks: { display: false } } },
            plugins: { legend: { display: false } }
        }
    });
}

function initComparisonChart() {
    const ctx = document.getElementById('strategyComparisonChart');
    if (!ctx) return;
    
    comparisonChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Semantic', 'Keyword', 'Hybrid (You)'],
            datasets: [{
                label: 'NDCG@10',
                data: [0, 0, 0], // placeholders
                backgroundColor: [
                    'rgba(54, 162, 235, 0.6)', // Semantic (Blue)
                    'rgba(255, 193, 7, 0.6)',  // Keyword (Yellow)
                    'rgba(25, 135, 84, 0.8)'   // Hybrid (Green)
                ],
                borderColor: [
                    'rgb(54, 162, 235)',
                    'rgb(255, 193, 7)',
                    'rgb(25, 135, 84)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y', // Horizontal bars
            scales: {
                x: { beginAtZero: true, max: 1.0, title: { display: true, text: 'NDCG@10 Score' } }
            },
            plugins: {
                legend: { display: false },
                tooltip: { 
                    callbacks: {
                        label: function(context) {
                            return context.parsed.x.toFixed(4);
                        }
                    }
                }
            },
            responsive: true,
            maintainAspectRatio: false
        }
    });
}

function initLatencyChart() {
    const ctx = document.getElementById('latencyStackChart');
    if (!ctx) return;

    latencyChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Latency'],
            datasets: [
                {
                    label: 'Semantic',
                    data: [0],
                    backgroundColor: 'rgba(54, 162, 235, 0.8)', // Primary
                    barThickness: 10
                },
                {
                    label: 'Keyword',
                    data: [0],
                    backgroundColor: 'rgba(255, 193, 7, 0.8)', // Warning
                    barThickness: 10
                },
                {
                    label: 'Fusion',
                    data: [0],
                    backgroundColor: 'rgba(108, 117, 125, 0.8)', // Secondary
                    barThickness: 10
                }
            ]
        },
        options: {
            indexAxis: 'y',
            scales: {
                x: { stacked: true, display: false },
                y: { stacked: true, display: false }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + context.parsed.x.toFixed(2) + ' ms';
                        }
                    }
                }
            },
            responsive: true,
            maintainAspectRatio: false,
            layout: { padding: 0 }
        }
    });
}

window.updateComparisonChart = function(sem, key, hybrid) {
    if (comparisonChart) {
        comparisonChart.data.datasets[0].data = [sem, key, hybrid];
        comparisonChart.update();
    }
};

window.updateLatencyChart = function(semMs, keyMs, fuseMs) {
    if (latencyChart) {
        latencyChart.data.datasets[0].data = [semMs];
        latencyChart.data.datasets[1].data = [keyMs];
        latencyChart.data.datasets[2].data = [fuseMs];
        latencyChart.update();
    }
};

function updateRadar(d) {
    if (!radarChart) return;
    
    // Parse values safely
    const semVal = d.sem !== 'N/A' ? parseFloat(d.sem) : 0;
    const keyVal = d.key !== 'N/A' ? parseFloat(d.key) : 0;
    const keyNorm = Math.min(1.0, keyVal / 3.0); 

    radarChart.data.datasets[0].data = [
        semVal,
        keyNorm,
        0.5, // Mock Date
        0.8, // Mock Lang
        0.3  // Mock Pop
    ];
    radarChart.update();
}
