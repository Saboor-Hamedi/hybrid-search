/**
 * InsightCard - Standalone System
 */
window.InsightCard = (function() {
    let card = null;

    const styles = `
        .sim-insight-card {
            position: fixed !important;
            z-index: 100000 !important;
            width: 320px;
            background: white !important;
            border-radius: 12px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.25) !important;
            border: 1px solid #eef2f7 !important;
            padding: 18px;
            display: none;
            pointer-events: none;
            transition: opacity 0.2s, transform 0.2s;
            transform: translateY(10px);
            opacity: 0;
            left: 0;
            top: 0;
            font-family: 'Inter', sans-serif;
        }
        .sim-insight-card.show {
            display: block !important;
            opacity: 1 !important;
            transform: translateY(0);
        }
        .insight-header { border-bottom: 1px solid #f1f5f9; margin-bottom: 12px; padding-bottom: 8px; }
        .insight-score-row { display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 11px; color: #64748b; }
        .insight-pill { padding: 2px 8px; border-radius: 6px; font-weight: 700; font-size: 10px; }
        .insight-snippet { 
            font-size: 11px; line-height: 1.5; color: #475569; font-style: italic; background: #f8fafc; 
            padding: 10px; border-radius: 8px; border-left: 3px solid #cbd5e1; max-height: 160px; overflow-y: auto;
        }
    `;

    function init() {
        if (!document.getElementById('insight-card-styles')) {
            const styleTag = document.createElement('style');
            styleTag.id = 'insight-card-styles';
            styleTag.innerHTML = styles;
            document.head.appendChild(styleTag);
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
                        <span><i class="bi bi-brain-fill text-info me-1"></i> AI Contextual Influence</span>
                        <span class="insight-pill bg-info-subtle text-info">${(data.semPct || 0).toFixed(1)}%</span>
                    </div>
                    <div class="insight-score-row">
                        <span><i class="bi bi-key-fill text-warning me-1"></i> Keyword Frequency</span>
                        <span class="insight-pill bg-warning-subtle text-warning">${(data.keyPct || 0).toFixed(1)}%</span>
                    </div>
                    <div class="progress mt-2" style="height: 5px; border-radius: 10px; background: #f1f5f9; overflow: hidden;">
                        <div class="progress-bar bg-info" style="width: ${data.semPct}%"></div>
                        <div class="progress-bar bg-warning" style="width: ${data.keyPct}%"></div>
                    </div>
                </div>
                <div class="insight-snippet">"${data.snippet}"</div>
            `;

            let x = e.clientX + 20;
            let y = e.clientY - 40;
            if (x + 320 > window.innerWidth) x = e.clientX - 340;
            if (y + 200 > window.innerHeight) y = window.innerHeight - 220;

            card.style.left = x + 'px';
            card.style.top = y + 'px';
            card.classList.add('show');
        },
        hide: function() {
            if (card) card.classList.remove('show');
        }
    };
})();
