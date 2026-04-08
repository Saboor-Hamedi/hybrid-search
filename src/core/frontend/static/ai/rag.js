/**
 * Simple Regex-based Markdown Parser
 */
/**
 * Advanced Markdown Parser powered by Marked.js
 */
function parseMarkdown(text) {
    if (!text) return "";
    const cleanSource = text.trim(); // TRIMMING prevents indented code blocks
    
    // Configure marked if available
    if (window.marked) {
        // Custom renderer for code blocks (consistent with assistant.js)
        const renderer = new marked.Renderer();
        renderer.code = function(arg1, arg2) {
            // Handle newer marked versions where the first arg is an object {text, lang, ...}
            const text = (typeof arg1 === 'object') ? arg1.text : arg1;
            const lang = (typeof arg1 === 'object') ? (arg1.lang || 'code') : (arg2 || 'code');
            
            return `
            <div class="code-block-container my-3">
                <div class="code-block-header">
                    <span>${lang}</span>
                    <button class="copy-code-btn" onclick="copyCode(this)">
                        <i class="bi bi-clipboard"></i> Copy
                    </button>
                </div>
                <pre><code class="language-${lang}">${text}</code></pre>
            </div>`;
        };
        
        return marked.parse(cleanSource, {
            renderer: renderer,
            breaks: true,
            gfm: false // Disable indented code blocks by focusing only on GFM
        });
    }

    // Fallback to basic regex if marked is missing
    let clean = cleanSource.replace(/```(\w*)\n?([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
    clean = clean.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    clean = clean.replace(/\n/g, '<br>');
    return clean;
}

async function triggerAIAnswer(turnId = null) {
    const scope = turnId ? document.getElementById(turnId) : document;
    if (!scope) return;

    const container = scope.querySelector('.ai-research-box');
    const spinner = scope.querySelector('.spinner-ai');
    const textBox = scope.querySelector('.ai-answer-text');
    const footerEl = scope.querySelector('.ai-research-footer');
    
    const query = document.querySelector('textarea[name="query"]').value || 
                 scope.querySelector('.message-query')?.textContent.trim();
    
    if (!container || !query) return;

    // Show Container & Spinner
    container.classList.remove('d-none');
    if (spinner) spinner.classList.remove('d-none');
    textBox.innerHTML = '<i class="text-muted">Consulting local research documents...</i>';

    // Collect Top 5 Contexts from the CURRENT turn or whole page
    const contexts = [];
    const items = scope.querySelectorAll('.result-item');
    for (let i = 0; i < Math.min(items.length, 5); i++) {
        const item = items[i];
        let docId = "Unknown";
        const idEl = item.querySelector('.result-doc-id');
        if (idEl) {
             docId = idEl.textContent.trim().replace('#', '');
        }

        const btn = item.querySelector('button[onclick="showAnalysis(this)"]');
        if (btn && btn.dataset.content) {
            contexts.push({
                doc_id: docId,
                content: btn.dataset.content
            });
        }
    }

    if (contexts.length === 0) {
         textBox.textContent = "Could not extract context for AI generation.";
         if (spinner) spinner.classList.add('d-none');
         return;
    }

    try {
        const aiProvider = localStorage.getItem('ai_provider') || 'ollama';
        const aiModel = localStorage.getItem('ai_model') || 'qwen2.5:0.5b';
        const aiApiKey = localStorage.getItem('ai_api_key') || '';
        const ollamaBaseUrl = localStorage.getItem('ollama_base_url') || 'http://localhost:11434';

        // Use the new STREAMING endpoint
        const response = await fetch('/generate-stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                query: query.trim(), 
                contexts: contexts,
                provider: aiProvider,
                model: aiModel,
                api_key: aiApiKey,
                base_url: ollamaBaseUrl
            })
        });

        if (spinner) spinner.classList.add('d-none');
        
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        // --- STREAMING PROCESSING ---
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullAnswer = "";
        textBox.innerHTML = ""; // Clear the loading text

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value, { stream: true });
            fullAnswer += chunk;
            
            // Progressive Rendering
            // We strip the metadata tag if it starts to appear, 
            // but we'll do the final cleanup after the stream
            let displayAnswer = fullAnswer;
            
            // Apply Markdown Parsing live
            textBox.innerHTML = parseMarkdown(displayAnswer).replace(/\[Doc\s*(\d+)\]/g, '<strong class="text-primary small mx-1">#$1</strong>');
            
            // Auto-scroll to bottom of this turn if needed
            if (scope && typeof scope.scrollIntoView === 'function') {
                // scope.scrollIntoView({ behavior: 'smooth', block: 'end' });
            }
        }

        // --- FINAL PROCESSING (After stream ends) ---
        if (fullAnswer) {
            let finalMarkdown = fullAnswer;
            let bestSourceId = null;

            // Extract BEST_SOURCE_ID
            const sourceMatch = finalMarkdown.match(/(?:\*\*|)?(?:BEST[-_ ]?SOURCE[-_ ]?ID|Best[-_ ]?Source[-_ ]?ID|Source[-_ ]?ID|Source|Best[-_ ]?Source)(?:\*\*|)?:\s*(\d+)/i);
            if (sourceMatch) {
                bestSourceId = sourceMatch[1];
                finalMarkdown = finalMarkdown.replace(sourceMatch[0], '').trim();
            }

            // Cleanup text (Casing fix for headers/AI terms)
            // Note: Casing fix can be aggressive on code, so we apply carefully
            // finalMarkdown = finalMarkdown.replace(/(^\s*\w|[.!?]\s*\w)/g, c => c.toUpperCase());
            finalMarkdown = finalMarkdown.replace(/\b(ai|ml|rrf|api|llm|nlp|db|sql|ui|ux|pdf)\b/gi, m => m.toUpperCase());

            // Re-render final cleaned version
            const formatted = parseMarkdown(finalMarkdown).replace(/\[Doc\s*(\d+)\]/g, '<strong class="text-primary small mx-1">#$1</strong>');
            textBox.innerHTML = formatted;

            if (footerEl) {
                footerEl.classList.remove('d-none');
                const copyBtnId = `copy-btn-${Date.now()}`;
                footerEl.innerHTML = `
                <div class="d-flex align-items-center justify-content-between pt-3 mt-3 border-top" style="font-size: 0.8rem;">
                    <div>
                        ${bestSourceId ? `
                        <span class="d-flex align-items-center text-muted">
                            <i class="bi bi-star-fill text-warning me-1"></i>
                            <span class="fw-semibold text-secondary">Source:</span>
                            <span class="ms-1 text-primary fw-bold">#${bestSourceId}</span>
                        </span>
                        ` : '<span class="text-muted fst-italic small">Generated from context</span>'}
                    </div>

                    <button id="${copyBtnId}" class="btn btn-sm text-secondary border-0 d-flex align-items-center bg-transparent p-0" 
                            style="min-width: 65px; justify-content: end;" title="Copy to clipboard"
                            data-content="${finalMarkdown.replace(/"/g, '&quot;')}"
                            onclick="copyToClipboard(this, this.dataset.content)">
                        <i class="bi bi-copy me-1"></i> Copy
                    </button>
                </div>
                `;
            }
        }

    } catch (e) {
        console.error("AI Generation failed", e);
        if (spinner) spinner.classList.add('d-none');
        textBox.textContent = "Error: Could not contact local AI service.";
    }
}
