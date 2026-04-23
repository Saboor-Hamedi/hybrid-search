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
    // Don't interfere with link, button, or icon clicks (actions)
    if (['A', 'BUTTON', 'I'].includes(e.target.tagName)) return;
    if (e.target.closest('button') || e.target.closest('a')) return;
    
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
        // Subtle visual feedback
        this.classList.add('copy-success-highlight');
        setTimeout(() => {
          this.classList.remove('copy-success-highlight');
        }, 400);
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
    
    // Populate Preview (Markdown-aware)
    if (typeof parseMarkdown === 'function') {
        document.getElementById('modalContentPreview').innerHTML = parseMarkdown(d.content);
    } else {
        document.getElementById('modalContentPreview').innerHTML = d.content;
    }
    
    // Chart Data Prep
    updateRadar(d);
    
    // Attempt to pre-load the Strategy Chart (Session context) even in Doc view
    preloadStrategyChart();

    bootstrap.Modal.getOrCreateInstance(document.getElementById('analysisModal')).show();
}

function showSessionAnalysis(btn) {
    showAnalysisTab('#metricsTab');
    
    const d = btn.dataset;
    const setVal = (id, val) => { 
        const el = document.getElementById(id); 
        if (el) el.textContent = val; 
    };

    setVal('modalPrompt', d.prompt || "No query recorded");
    setVal('metricDocId', "Session Overview");
    
    // 1. Effectiveness
    setVal('metricP', d.p !== 'N/A' ? parseFloat(d.p).toFixed(4) : 'N/A');
    setVal('metricR', d.r !== 'N/A' ? parseFloat(d.r).toFixed(4) : 'N/A');
    setVal('metricF1', d.f1 !== 'N/A' ? parseFloat(d.f1).toFixed(4) : 'N/A');
    setVal('metricMAP', d.map !== 'N/A' ? parseFloat(d.map).toFixed(4) : 'N/A');
    setVal('metricNDCG', d.ndcg !== 'N/A' ? parseFloat(d.ndcg).toFixed(4) : 'N/A');
    setVal('metricMRR', d.mrr !== 'N/A' ? parseFloat(d.mrr).toFixed(4) : 'N/A');
    
    // 2. Efficiency
    setVal('metricLatency', d.latency + ' ms');
    setVal('metricQpMS', d.qpms !== 'N/A' ? parseFloat(d.qpms).toFixed(4) : 'N/A');
    
    // 3. Router
    setVal('metricRouter', d.router !== 'N/A' ? (parseFloat(d.router)*100).toFixed(0) + '%' : 'N/A');
    
    const routerBadge = document.getElementById('metricRouterBadge');
    if (routerBadge) {
        if (d.router && d.router !== 'N/A') {
            const rAcc = parseFloat(d.router);
            if (rAcc >= 1.0) {
                routerBadge.className = 'badge bg-success';
                routerBadge.textContent = 'Optimal';
            } else if (rAcc > 0.7) {
                routerBadge.className = 'badge bg-primary';
                routerBadge.textContent = 'Effective';
            } else {
                routerBadge.className = 'badge bg-warning text-dark';
                routerBadge.textContent = 'Sub-optimal';
            }
        } else {
            routerBadge.className = 'badge bg-light text-dark border';
            routerBadge.textContent = 'Untested';
        }
    }
    
    // Load Chart
    preloadStrategyChart();
    
    // Trigger Alpha Simulation to populate the preview list
    setTimeout(() => {
        const range = document.getElementById('alphaSimulationRange');
        if (range) range.dispatchEvent(new Event('input'));
    }, 200);
    
    bootstrap.Modal.getOrCreateInstance(document.getElementById('analysisModal')).show();
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


function copyAnalysisData(btn) {
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
            precision: document.getElementById('metricP')?.textContent || 'N/A',
            recall: document.getElementById('metricR')?.textContent || 'N/A',
            f1: document.getElementById('metricF1')?.textContent || 'N/A',
            map: document.getElementById('metricMAP')?.textContent || 'N/A',
            mrr: document.getElementById('metricMRR')?.textContent || 'N/A',
            ndcg: document.getElementById('metricNDCG')?.textContent || 'N/A',
            avgRank: document.getElementById('metricAvgRank')?.textContent || 'N/A'
        },
        hits: {
            h1: document.getElementById('metricH1')?.textContent || 'N/A',
            h3: document.getElementById('metricH3')?.textContent || 'N/A',
            h5: document.getElementById('metricH5')?.textContent || 'N/A',
            h10: document.getElementById('metricH10')?.textContent || 'N/A'
        },
        deep: {
            jaccard: document.getElementById('metricJaccard')?.textContent || 'N/A',
            faithfulness: document.getElementById('metricFaithfulness')?.textContent || 'N/A'
        },
        efficiency: {
            latency: document.getElementById('metricLatency')?.textContent || 'N/A',
            qpms: document.getElementById('metricQpMS')?.textContent || 'N/A'
        },
        router: {
            accuracy: document.getElementById('metricRouter')?.textContent || 'N/A'
        }
    };
    
    textSummary += `PRECISION@K: ${metricsData.effectiveness.precision}\n`;
    textSummary += `RECALL@K:    ${metricsData.effectiveness.recall}\n`;
    textSummary += `F1-SCORE:    ${metricsData.effectiveness.f1}\n`;
    textSummary += `MAP:         ${metricsData.effectiveness.map}\n`;
    textSummary += `MRR:         ${metricsData.effectiveness.mrr}\n`;
    textSummary += `NDCG@10:     ${metricsData.effectiveness.ndcg}\n`;
    textSummary += `AVG RANK:    ${metricsData.effectiveness.avgRank}\n\n`;
    
    textSummary += `Strategy Overlap (Jaccard): ${metricsData.deep.jaccard}\n`;
    textSummary += `HITS ASSESSMENT: H@1:${metricsData.hits.h1}, H@3:${metricsData.hits.h3}, H@5:${metricsData.hits.h5}, H@10:${metricsData.hits.h10}\n`;
    textSummary += `AI FAITHFULNESS: ${metricsData.deep.faithfulness}\n\n`;

    textSummary += `LATENCY (Raw): ${metricsData.efficiency.latency}\n`;
    textSummary += `QpMS (Thesis): ${metricsData.efficiency.qpms}\n\n`;
    
    textSummary += `ROUTER ACC: ${metricsData.router.accuracy}`;

    navigator.clipboard.writeText(textSummary).then(() => {
        // Use Global Style Feedback
        if (btn) {
            btn.classList.add('btn-success');
            btn.classList.remove('btn-primary');
            if (typeof window.showCopySuccess === 'function') {
                window.showCopySuccess(btn);
            }
            
            setTimeout(() => {
                btn.classList.remove('btn-success');
                btn.classList.add('btn-primary');
            }, 2000);
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
    // Pass the checkbox to identify which search turn we are in
    calculateAndSyncMetrics(checkbox);
}

function calculateAndSyncMetrics(contextEl) {
    // 1. Identify which turn we are in
    let container = document;
    if (contextEl) {
        container = contextEl.closest('.message-response') || contextEl.closest('.turn-results') || document;
    }

    // 2. Gather results for THIS TURN ONLY
    const results = container.querySelectorAll('.result-item');
    if (results.length === 0) return; // Nothing to calculate

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

    // --- NEW ADVANCED METRICS ---
    
    // 1. F1 Score (Harmonic mean of P and R)
    const f1 = (p_k + r_k) > 0 ? (2 * p_k * r_k) / (p_k + r_k) : 0;

    // 2. Average Rank of Relevant Documents
    let totalRankSum = 0;
    let relCount = 0;
    results.forEach((el, index) => {
        const box = el.querySelector('.relevance-toggle input');
        if (judgedDocs.has(box.dataset.docId)) {
            totalRankSum += (index + 1);
            relCount++;
        }
    });
    const avgRank = relCount > 0 ? (totalRankSum / relCount) : 0;

    // 3. HITS @ 1, 3, 5, 10
    let hitsAt = { h1: 0, h3: 0, h5: 0, h10: 0 };
    results.forEach((el, index) => {
        const box = el.querySelector('.relevance-toggle input');
        if (judgedDocs.has(box.dataset.docId)) {
            const rank = index + 1;
            if (rank <= 1) hitsAt.h1 = 1;
            if (rank <= 3) hitsAt.h3 = 1;
            if (rank <= 5) hitsAt.h5 = 1;
            if (rank <= 10) hitsAt.h10 = 1;
        }
    });

    // 4. Strategy Overlap (Jaccard Index)
    const btn = container.querySelector('button[onclick="showSessionAnalysis(this)"]') || 
                document.querySelector('button[onclick="showSessionAnalysis(this)"]');
    
    let jaccard = 0;
    let compNDCG = { semantic: 0, keyword: 0 };
    
    if (btn && btn.dataset.rankDebug) {
        try {
            const rankDebug = JSON.parse(btn.dataset.rankDebug);
            const semSet = new Set(rankDebug.semantic.map(String));
            const keySet = new Set(rankDebug.keyword.map(String));
            
            const intersection = new Set([...semSet].filter(x => keySet.has(x)));
            const union = new Set([...semSet, ...keySet]);
            jaccard = union.size > 0 ? intersection.size / union.size : 0;

            compNDCG.semantic = calculateSingleStrategyNDCG(rankDebug.semantic, judgedDocs, sessionK);
            compNDCG.keyword = calculateSingleStrategyNDCG(rankDebug.keyword, judgedDocs, sessionK);
        } catch (e) {
            console.error("Error parsing rank debug data", e);
        }
    }

    // 5. AI Faithfulness (Grounding) Mock/Regex
    let faithfulness = 1.0; 
    const aiText = container.querySelector('.ai-answer-text')?.innerText || "";
    const citations = aiText.match(/\[Doc\s*(\d+)\]/g);
    if (citations && citations.length > 0) {
        const allDocIds = new Set(Array.from(results).map(el => el.querySelector('.relevance-toggle input').dataset.docId));
        let validCitations = 0;
        citations.forEach(cit => {
            const id = cit.match(/\d+/)[0];
            if (allDocIds.has(id)) validCitations++;
        });
        faithfulness = validCitations / citations.length;
    }

    // QpMS & Latency Logic
    let latency = 0;
    let latStats = { semantic: 0, keyword: 0, fusion: 0 };
    if (window.currentLatency) {
        latency = window.currentLatency;
    } else if (btn && btn.dataset.latency) {
        latency = parseFloat(btn.dataset.latency);
    }
    if (btn && btn.dataset.latencyStats) {
        try { latStats = JSON.parse(btn.dataset.latencyStats); } catch(e) {}
    }
    const qpms = (latency > 0) ? (ndcg / latency) * 1000 : 0;

    // Router Accuracy
    let routerAcc = 1.0; 
    if (compNDCG.semantic > 0 || compNDCG.keyword > 0) {
        const bestBaseline = Math.max(compNDCG.semantic, compNDCG.keyword);
        routerAcc = (ndcg < bestBaseline) ? ndcg / bestBaseline : 1.0;
    } else if (ndcg === 0 && totalRel > 0) {
        routerAcc = 0;
    }

    updateSessionStats({
        p: p_k, r: r_k, f1: f1, map: map, ndcg: ndcg, mrr: mrr, 
        avgRank: avgRank, hits: hitsAt, jaccard: jaccard, 
        faithfulness: faithfulness, qpms: qpms, 
        compNDCG: compNDCG, latStats: latStats, 
        btn: btn, routerAcc: routerAcc, results: results
    });
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

function updateSessionStats(meta) {
    const { p, r, f1, map, ndcg, mrr, avgRank, hits, jaccard, faithfulness, qpms, compNDCG, latStats, btn, routerAcc, results } = meta;
    if (!btn) return;

    // Update Data Attributes for persistence
    btn.dataset.p = p.toFixed(4);
    btn.dataset.r = r.toFixed(4);
    btn.dataset.f1 = f1.toFixed(4);
    btn.dataset.map = map.toFixed(4);
    btn.dataset.ndcg = ndcg.toFixed(4);
    btn.dataset.mrr = mrr.toFixed(4);
    btn.dataset.avgRank = avgRank.toFixed(2);
    btn.dataset.hits = JSON.stringify(hits);
    btn.dataset.jaccard = jaccard.toFixed(4);
    btn.dataset.faithfulness = faithfulness.toFixed(4);
    btn.dataset.qpms = qpms.toFixed(4);
    btn.dataset.router = routerAcc.toFixed(4);

    // Update Modal DOM live
    const setT = (id, val) => { const el = document.getElementById(id); if(el) el.textContent = val; };
    
    setT('metricP', p.toFixed(4));
    setT('metricR', r.toFixed(4));
    setT('metricF1', f1.toFixed(4));
    setT('metricMAP', map.toFixed(4));
    setT('metricNDCG', ndcg.toFixed(4));
    setT('metricMRR', mrr.toFixed(4));
    setT('metricAvgRank', avgRank > 0 ? avgRank.toFixed(1) : '-');
    
    setT('metricH1', hits.h1 ? 'YES' : 'NO');
    setT('metricH3', hits.h3 ? 'YES' : 'NO');
    setT('metricH5', hits.h5 ? 'YES' : 'NO');
    setT('metricH10', hits.h10 ? 'YES' : 'NO');

    setT('metricJaccard', (jaccard * 100).toFixed(1) + '%');
    const jBar = document.getElementById('jaccardProgress');
    if(jBar) jBar.style.width = (jaccard * 100) + '%';

    setT('metricFaithfulness', (faithfulness * 100).toFixed(0) + '%');
    const fBar = document.getElementById('faithfulnessProgress');
    if(fBar) {
        fBar.style.width = (faithfulness * 100) + '%';
        fBar.className = faithfulness > 0.8 ? 'progress-bar bg-success' : (faithfulness > 0.5 ? 'progress-bar bg-warning' : 'progress-bar bg-danger');
    }

    setT('metricQpMS', qpms.toFixed(4));
    setT('metricRouter', (routerAcc * 100).toFixed(0) + '%');
    
    // Router Badge
    const routerBadge = document.getElementById('metricRouterBadge');
    if (routerBadge) {
        if (routerAcc >= 1.0) { routerBadge.className = 'badge bg-success'; routerBadge.textContent = 'Optimal'; }
        else if (routerAcc > 0.7) { routerBadge.className = 'badge bg-primary'; routerBadge.textContent = 'Effective'; }
        else { routerBadge.className = 'badge bg-warning text-dark'; routerBadge.textContent = 'Sub-optimal'; }
    }

    // Update Charts
    if (window.updateComparisonChart && compNDCG) {
        window.updateComparisonChart(compNDCG.semantic, compNDCG.keyword, ndcg);
    }
    
    // Update PR Curve and GPA (NEW)
    updatePRCurve(results, judgedDocs);
    updateGPA(ndcg, mrr, qpms);
}


// === THESIS HUB: PR CURVE & GPA (NEW) ===
let globalSessionLogs = { ndcgSum: 0, mrrSum: 0, qpmsSum: 0, count: 0 };

function updateGPA(ndcg, mrr, qpms) {
    globalSessionLogs.ndcgSum += ndcg;
    globalSessionLogs.mrrSum += mrr;
    globalSessionLogs.qpmsSum += qpms;
    globalSessionLogs.count++;

    const avgNDCG = globalSessionLogs.ndcgSum / globalSessionLogs.count;
    const avgMRR = globalSessionLogs.mrrSum / globalSessionLogs.count;
    const avgQpMS = globalSessionLogs.qpmsSum / globalSessionLogs.count;

    const setT = (id, val) => { const el = document.getElementById(id); if(el) el.textContent = val; };
    setT('sessionNDCG', avgNDCG.toFixed(4));
    setT('sessionMRR', avgMRR.toFixed(4));
    setT('sessionQpMS', avgQpMS.toFixed(4));

    // Dynamic Letter Grade
    const gpaEl = document.getElementById('sessionGPA');
    if (gpaEl) {
        if (avgNDCG > 0.8) gpaEl.textContent = 'A+';
        else if (avgNDCG > 0.6) gpaEl.textContent = 'A';
        else if (avgNDCG > 0.4) gpaEl.textContent = 'B';
        else if (avgNDCG > 0.2) gpaEl.textContent = 'C';
        else gpaEl.textContent = 'D';
    }
}

function updatePRCurve(results, judgedIds) {
    if (!prCurveChart) return;
    
    let points = [];
    let hits = 0;
    const totalRel = judgedIds.size;
    
    if (totalRel === 0) {
        prCurveChart.data.datasets[0].data = [{x:0, y:1}, {x:1, y:0}];
        prCurveChart.update();
        return;
    }

    results.forEach((el, index) => {
        const box = el.querySelector('.relevance-toggle input');
        if (!box) return;
        const docId = box.dataset.docId;
        const rank = index + 1;
        if (judgedIds.has(docId)) {
            hits++;
            const precision = hits / rank;
            const recall = hits / totalRel;
            points.push({ x: recall, y: precision });
        }
    });

    points.sort((a,b) => a.x - b.x);
    if (points.length > 0) points.unshift({ x: 0, y: points[0].y });

    prCurveChart.data.datasets[0].data = points;
    prCurveChart.update();
}

// === THESIS HUB: DYNAMIC RE-RANKING (NEW) ===
function handleAlphaSimulation() {
    const range = document.getElementById('alphaSimulationRange');
    const alphaDisp = document.getElementById('alphaValueDisplay');
    if (!range || !alphaDisp) return;

    range.addEventListener('input', (e) => {
        const alpha = parseFloat(e.target.value);
        alphaDisp.textContent = `α = ${alpha.toFixed(2)}`;
        
        const currentModalBtn = document.querySelector('button[onclick="showSessionAnalysis(this)"]');
        if (!currentModalBtn) return;
        
        const resultItems = Array.from(document.querySelectorAll('.result-item'));
        if (resultItems.length === 0) return;

        // 1. Dynamic Normalization: Find the max scores in the current set to balance the slider
        let maxSem = 0.1;
        let maxKey = 0.1;
        resultItems.forEach(item => {
            const d = item.querySelector('.analysis-btn')?.dataset;
            if (d) {
                const s = d.sem !== 'N/A' ? parseFloat(d.sem) : 0;
                const k = d.key !== 'N/A' ? parseFloat(d.key) : 0;
                if (s > maxSem) maxSem = s;
                if (k > maxKey) maxKey = k;
            }
        });

        // 2. Calculate Simulated Scores
        const simulated = resultItems.map((item, originalIndex) => {
            const btn = item.querySelector('.analysis-btn') || item.querySelector('button[onclick^="showAnalysis"]');
            if(!btn) return null;
            const d = btn.dataset;
            
            const sem = d.sem !== 'N/A' ? parseFloat(d.sem) : 0;
            const key = d.key !== 'N/A' ? parseFloat(d.key) : 0;
            
            // Normalize relative to the best in this specific search
            const semNorm = sem / (maxSem || 1);
            const keyNorm = key / (maxKey || 1);
            
            // HARD ZEROING: Force absolute 0 if alpha is at edges
            const semContrib = alpha === 0 ? 0 : (alpha * semNorm);
            const keyContrib = alpha === 1 ? 0 : ((1 - alpha) * keyNorm);
            const simScore = semContrib + keyContrib;
            
            return {
                id: d.docId,
                title: item.querySelector('.result-title span')?.textContent || "Doc #" + d.docId,
                score: simScore,
                semContrib: semContrib,
                keyContrib: keyContrib,
                originalRank: originalIndex + 1,
                isRel: judgedDocs.has(d.docId),
                snippet: d.content ? d.content.substring(0, 180).replace(/"/g, '&quot;') + "..." : "No preview available"
            };
        }).filter(x => x !== null);

        // 2. Sort by Simulated Score
        simulated.sort((a,b) => b.score - a.score);
        
        // 3. Render with Rank Shift indicators & Contribution Bars
        renderRerankPreview(simulated);
    });
}

// === DYNAMIC INSIGHT CARD SYSTEM (INTEGRATED) ===
const InsightCard = (function() {
    let card = null;
    const styles = `
        .sim-insight-card {
            position: fixed !important;
            z-index: 200000 !important;
            width: 320px;
            background: white !important;
            border-radius: 12px;
            box-shadow: 0 20px 50px rgba(0,0,0,0.3) !important;
            border: 1px solid #e2e8f0 !important;
            padding: 16px;
            display: none;
            pointer-events: none;
            left: 0; top: 0;
            font-family: sans-serif;
        }
        .sim-insight-card.show { display: block !important; opacity: 1 !important; }
        .insight-header { border-bottom: 1px solid #f1f5f9; margin-bottom: 10px; padding-bottom: 8px; }
        .insight-score-row { display: flex; justify-content: space-between; margin-bottom: 4px; font-size: 11px; color: #64748b; }
        .insight-pill { padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 10px; }
        .insight-snippet { font-size: 11px; line-height: 1.4; color: #475569; font-style: italic; background: #f8fafc; padding: 8px; border-radius: 6px; border-left: 3px solid #cbd5e1; }
    `;

    function init() {
        if (!document.getElementById('insight-styles')) {
            const s = document.createElement('style');
            s.id = 'insight-styles'; s.innerHTML = styles;
            document.head.appendChild(s);
        }
        if (!card) {
            card = document.createElement('div');
            card.className = 'sim-insight-card';
            document.body.appendChild(card);
        }
    }

    return {
        show: function(e, data) {
            init();
            if (!data) return;
            card.innerHTML = `
                <div class="insight-header d-flex justify-content-between align-items-center">
                    <span class="badge bg-dark" style="font-size: 9px;">DOC #${data.id}</span>
                    <span class="text-primary fw-bold" style="font-size: 11px;">MATCH SCORE: ${data.score.toFixed(4)}</span>
                </div>
                <div class="mb-3">
                    <div class="insight-score-row">
                        <span><i class="bi bi-brain-fill text-info me-2"></i>AI Context Influence</span>
                        <span class="insight-pill bg-info-subtle text-info">${(data.semPct || 0).toFixed(1)}%</span>
                    </div>
                    <div class="insight-score-row">
                        <span><i class="bi bi-key-fill text-warning me-2"></i>Keyword Frequency</span>
                        <span class="insight-pill bg-warning-subtle text-warning">${(data.keyPct || 0).toFixed(1)}%</span>
                    </div>
                    <div class="progress mt-2" style="height: 6px; border-radius: 10px; background: #f1f5f9; overflow: hidden;">
                        <div class="progress-bar bg-info" style="width: ${data.semPct}%"></div>
                        <div class="progress-bar bg-warning" style="width: ${data.keyPct}%"></div>
                    </div>
                </div>
                <div class="insight-snippet">"${data.snippet}"</div>
                <div class="mt-2 pt-2 border-top x-small text-muted d-flex gap-3 justify-content-center">
                    <span><span class="badge bg-info p-1 me-1" style="width:10px;height:10px;display:inline-block"></span> AI</span>
                    <span><span class="badge bg-warning p-1 me-1" style="width:10px;height:10px;display:inline-block"></span> Keywords</span>
                </div>
            `;
            let x = e.clientX + 20; let y = e.clientY - 40;
            if (x + 320 > window.innerWidth) x = e.clientX - 340;
            if (y + 180 > window.innerHeight) y = window.innerHeight - 190;
            card.style.left = x + 'px'; card.style.top = y + 'px';
            card.classList.add('show');
        },
        hide: function() { if (card) card.classList.remove('show'); }
    };
})();

// Global simulation store
window.simDataStore = {};

function renderRerankPreview(list) {
    const previewList = document.getElementById('rerankPreviewList');
    if (!previewList) return;
    window.simDataStore = {};

    previewList.innerHTML = list.map((item, idx) => {
        const newRank = idx + 1;
        const shift = item.originalRank - newRank;
        let shiftHtml = (shift > 0) ? `<span class="text-success">↑${shift}</span>` : (shift < 0 ? `<span class="text-danger">↓${Math.abs(shift)}</span>` : `<span class="text-muted">•</span>`);

        const total = item.semContrib + item.keyContrib;
        const semPct = total > 0 ? (item.semContrib / total) * 100 : 0;
        const keyPct = total > 0 ? (item.keyContrib / total) * 100 : 0;

        const itemId = `sim_${item.id}_${idx}`;
        window.simDataStore[itemId] = { id: item.id, score: item.score, semPct: semPct, keyPct: keyPct, snippet: item.snippet };

        return `
        <div class="d-flex align-items-center justify-content-between p-2 x-small border-bottom ${item.isRel ? 'bg-success-subtle border-success' : ''}" 
             onmouseenter="InsightCard.show(event, window.simDataStore['${itemId}'])" 
             onmouseleave="InsightCard.hide()" style="cursor: help;">
            <div class="d-flex align-items-center gap-2 overflow-hidden">
                <div class="d-flex flex-column align-items-center" style="min-width: 24px;">
                    <span class="badge bg-secondary" style="font-size: 8px;">#${newRank}</span>
                    <div style="font-size: 7px;">${shiftHtml}</div>
                </div>
                <div class="overflow-hidden">
                    <div class="text-truncate" style="max-width: 130px; font-weight: 500;">${item.title}</div>
                    <div class="d-flex mt-1" style="height: 3px; width: 80px; background: #eee; border-radius: 1px; overflow: hidden;">
                        <div style="width: ${semPct}%; min-width: ${semPct > 0 ? '2px' : '0'}; background: #0dcaf0;"></div>
                        <div style="width: ${keyPct}%; min-width: ${keyPct > 0 ? '2px' : '0'}; background: #ffc107;"></div>
                    </div>
                </div>
            </div>
            <div class="text-end">
                <div class="fw-bold text-primary" style="font-size: 9px;">${item.score.toFixed(3)}</div>
                <div class="text-muted" style="font-size: 7px;">Was #${item.originalRank}</div>
            </div>
        </div>
        `;
    }).join('');
}

function initPRCurveChart() {
    const ctx = document.getElementById('prCurveChart');
    if (!ctx) return;
    prCurveChart = new Chart(ctx, {
        type: 'line',
        data: {
            datasets: [{
                label: 'Precision-Recall',
                data: [],
                borderColor: 'rgb(13, 202, 240)',
                backgroundColor: 'rgba(13, 202, 240, 0.1)',
                fill: true,
                tension: 0.4,
                pointRadius: 4
            }]
        },
        options: {
            scales: {
                x: { type: 'linear', min: 0, max: 1.0, title: { display: true, text: 'Recall', font: { size: 9 } } },
                y: { min: 0, max: 1.0, title: { display: true, text: 'Precision', font: { size: 9 } } }
            },
            plugins: { legend: { display: false } },
            responsive: true,
            maintainAspectRatio: false
        }
    });
}

// --- Chart.js Initialization ---
document.addEventListener('DOMContentLoaded', function() {
    // 1. Initialize Charts
    initRadarChart();
    initComparisonChart();
    initPRCurveChart();
    handleAlphaSimulation();

    // 2. Render Markdown in Search Results (if present)
    if (typeof parseMarkdown === 'function') {
        document.querySelectorAll('.result-content').forEach(el => {
            // Only parse if not already a complex HTML block (e.g. from Assistant)
            if (!el.closest('.assistant-chat-bot')) {
                const raw = el.innerHTML.trim(); // Trim to prevent indented code blocks
                if (raw) el.innerHTML = parseMarkdown(raw);
            }
        });
    }

    // 3. Trigger AI Answer if results exist AND AI is enabled
    const items = document.querySelectorAll('.result-item');
    if (items.length > 0 && window.ENABLE_AI) {
        triggerAIAnswer();
    }
});


let radarChart = null;
let comparisonChart = null;
let prCurveChart = null;

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
            plugins: { legend: { display: false } },
            maintainAspectRatio: false
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
                data: [0, 0, 0],
                backgroundColor: [
                    'rgba(54, 162, 235, 0.6)',
                    'rgba(255, 193, 7, 0.6)',
                    'rgba(25, 135, 84, 0.8)'
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
            indexAxis: 'y',
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

window.updateComparisonChart = function(sem, key, hybrid) {
    if (comparisonChart) {
        comparisonChart.data.datasets[0].data = [sem, key, hybrid];
        comparisonChart.update();
    }
};

function updateRadar(d) {
    if (!radarChart) return;
    const semVal = d.sem !== 'N/A' ? parseFloat(d.sem) : 0;
    const keyVal = d.key !== 'N/A' ? parseFloat(d.key) : 0;
    const keyNorm = Math.min(1.0, keyVal / 3.0); 

    radarChart.data.datasets[0].data = [semVal, keyNorm, 0.5, 0.8, 0.3];
    radarChart.update();
}
