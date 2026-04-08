/**
 * AI Assistant Mode Logic
 * Handles interactive chat with Ollama proxy
 */

/**
 * --- UI GENERATION HELPERS ---
 */

function polishChatText(text) {
  if (!text) return "";
  // Simple cleaning: ensure first letter is capitalized, trim whitespace
  let clean = text.trim();
  return clean.charAt(0).toUpperCase() + clean.slice(1);
}

function formatBotResponse(text) {
    if (!text) return "";
    const cleanSource = text.trim(); // TRIMMING is mandatory to prevent code block conversion
    
    if (window.marked) {
        return marked.parse(cleanSource, {
            breaks: true,
            gfm: true
        });
    }
    return cleanSource.replace(/\n/g, '<br>');
}

/**
 * Configure marked renderer for custom code blocks
 */
if (window.marked) {
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

    marked.setOptions({ 
        renderer: renderer,
        breaks: true,
        gfm: true
    });
}

/**
 * Returns the HTML for assistant action buttons to avoid duplication
 */
function getAssistantActionsHtml(isSaved = false, msgId = null) {
    const saveClass = isSaved ? 'action-btn text-success disabled' : 'action-btn';
    const saveIcon = isSaved ? 'bi-check-circle-fill' : 'bi-plus-circle';
    const saveText = isSaved ? 'Saved' : 'Save';
    const saveAttr = msgId ? `data-msg-id="${msgId}"` : '';

    return `
        <button class="action-btn" onclick="copyToClipboard(this, {parent: '.assistant-chat-bot', child: '.assistant-content'}, 'selector')" title="Copy Response">
            <i class="bi bi-copy"></i> Copy
        </button>
        <button class="${saveClass}" onclick="saveToDatabase(this)" ${saveAttr} title="Save to Knowledge Base">
            <i class="bi ${saveIcon}"></i> ${saveText}
        </button>
        <button class="action-btn" onclick="handleFeedback(this, 'like')" title="Helpful">
            <i class="bi bi-hand-thumbs-up"></i>
        </button>
        <button class="action-btn" onclick="handleFeedback(this, 'dislike')" title="Not Helpful">
            <i class="bi bi-hand-thumbs-down"></i>
        </button>`;
}

function createChatMessageDiv(sender, text, id = null, isSaved = false, isTyping = false) {
  const msgDiv = document.createElement('div');
  msgDiv.className = 'message d-flex gap-3 ' + (sender === 'user' ? 'message-user-turn' : 'message-ai-turn');
  if (id) msgDiv.id = id;
  
  let contentHtml = '';
  const polishedText = sender === 'bot' ? polishChatText(text) : text;
  
  if (sender === 'user') {
    contentHtml = `
      <div class="chat-avatar user-avatar">
        <i class="bi bi-person-fill"></i>
      </div>
      <div class="query-container">
        <div class="message-query">
          ${polishedText}
        </div>
        <div class="user-actions">
            <button class="user-action-btn" 
                    onclick="copyToClipboard(this, this.dataset.query)" 
                    data-query="${polishedText.replace(/"/g, '&quot;')}"
                    title="Copy Prompt">
                <i class="bi bi-copy"></i>
            </button>
        </div>
      </div>
    `;
    } else if (sender === 'bot') {
    let formatted = formatBotResponse(polishedText);
    // Handle citations if any (from RAG)
    formatted = formatted.replace(/\[Doc\s*(\d+)\]/g, '<strong class="text-primary small mx-1">#$1</strong>');
        
    contentHtml = `
      <div class="chat-avatar ai-avatar">
        <i class="bi bi-robot"></i>
      </div>
      <div class="message-response assistant-chat-bot flex-grow-1">
        <div class="d-flex align-items-center gap-2 mb-2 text-primary small fw-bold">
           AI Assistant
        </div>
        <div class="assistant-content" data-raw-content="${polishedText.replace(/"/g, '&quot;')}">
          ${isTyping ? '<div class="typing-indicator"><span></span><span></span><span></span></div>' : formatted}
        </div>
        ${!isTyping ? `
        <div class="assistant-actions mt-3 d-flex gap-2">
            ${getAssistantActionsHtml(isSaved, id)}
        </div>
        ` : ''}
      </div>
    `;
  } else {
    contentHtml = `<div class="alert alert-danger py-2 small flex-grow-1">${text}</div>`;
  }

  msgDiv.innerHTML = contentHtml;
  return msgDiv;
}

function appendChatMessage(sender, text, id = null, isSaved = false, isTyping = false) {
  let wrapper = document.getElementById('historyArea');
  if (!wrapper) wrapper = document.querySelector('.messages-wrapper');
  if (!wrapper) return;

  const msgDiv = createChatMessageDiv(sender, text, id, isSaved, isTyping);
  wrapper.appendChild(msgDiv);
}

/**
 * --- MAIN CHAT LOGIC ---
 */

async function handleAssistantChat(message) {
  const historyArea = document.getElementById('historyArea');
  const chatContainer = document.querySelector('.chat-container');
  const textarea = document.querySelector('.search-input');
  
  if (chatContainer && chatContainer.classList.contains('is-empty-chat')) {
    chatContainer.classList.remove('is-empty-chat');
    document.body.classList.add('is-query-active');
  }

  if (textarea) {
    textarea.value = '';
    textarea.style.height = 'auto';
  }

  const turnId = 'assistant-turn-' + Date.now();
  const turnDiv = document.createElement('div');
  turnDiv.id = turnId;
  turnDiv.className = 'search-turn-container mb-4 assistant-mode-turn';
  if (historyArea) historyArea.appendChild(turnDiv);

  const typingId = 'typing-' + Date.now();
  turnDiv.innerHTML = `
    <div class="message message-user-turn d-flex gap-3 mb-3">
        <div class="chat-avatar user-avatar">
            <i class="bi bi-person-fill"></i>
        </div>
        <div class="query-container">
            <div class="message-query">${message}</div>
        </div>
    </div>
    <div class="turn-results" id="${typingId}">
        <div class="message message-ai-turn d-flex gap-3">
            <div class="chat-avatar ai-avatar">
                <i class="bi bi-robot"></i>
            </div>
            <div class="message-response flex-grow-1">
                <div class="shimmer-preview px-2">
                    <div class="shimmer-line mb-2"></div>
                    <div class="shimmer-line mb-2 w-75"></div>
                </div>
            </div>
        </div>
    </div>`;

  scrollToBottom();
  
  const userMsgId = 'msg-' + Date.now();
  saveToLocalHistory('user', message, false, userMsgId);

  try {
    const aiProvider = localStorage.getItem('ai_provider') || 'ollama';
    const aiModel = localStorage.getItem('ai_model') || 'qwen2.5:0.5b';
    const aiApiKey = localStorage.getItem('ai_api_key') || '';
    const ollamaBaseUrl = localStorage.getItem('ollama_base_url') || 'http://localhost:11434';

    const response = await fetch('/api/quick-chat-stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            message: message,
            provider: aiProvider,
            model: aiModel,
            api_key: aiApiKey,
            base_url: ollamaBaseUrl
        })
    });

    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    
    const resultsArea = document.getElementById(typingId);
    const botMsgId = 'msg-' + (Date.now() + 1);

    if (resultsArea) {
        resultsArea.innerHTML = `
            <div class="message message-ai-turn d-flex gap-3" id="${botMsgId}">
                <div class="chat-avatar ai-avatar">
                    <i class="bi bi-robot"></i>
                </div>
                <div class="message-response flex-grow-1 chat-bubble-ai assistant-chat-bot">
                    <div class="assistant-content"></div>
                </div>
            </div>`;
    }
    
    const contentArea = resultsArea.querySelector('.assistant-content');
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let fullReply = "";

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        fullReply += chunk;
        contentArea.innerHTML = formatBotResponse(fullReply);
        scrollToBottom();
    }

    const finalPolished = polishChatText(fullReply);
    contentArea.innerHTML = formatBotResponse(finalPolished);
    contentArea.dataset.rawContent = fullReply;
    
    const responseWrapper = resultsArea.querySelector('.message-response');
    const actionsDiv = document.createElement('div');
    actionsDiv.className = 'assistant-actions mt-3 d-flex gap-2';
    actionsDiv.innerHTML = getAssistantActionsHtml(false, botMsgId);
    responseWrapper.appendChild(actionsDiv);
    
    scrollToBottom();
    saveToLocalHistory('bot', fullReply, false, botMsgId);
  } catch (err) {
    console.error("Assistant chat failed", err);
    const resultsArea = document.getElementById(typingId);
    if (resultsArea) resultsArea.innerHTML = `<div class="alert alert-danger mx-5 small">Error: ${err.message}</div>`;
  }
}

/**
 * --- FEEDBACK & SAVE ---
 */

function handleFeedback(btn, type) {
  const actions = btn.closest('.assistant-actions');
  const allBtns = actions.querySelectorAll('.action-btn');
  allBtns.forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  console.log(`Feedback received: ${type}`);
}

async function saveToDatabase(btn) {
    const parent = btn.closest('.message-ai-turn');
    const contentArea = parent?.querySelector('.assistant-content');
    if (!contentArea) return;

    const msgId = btn.dataset.msgId || parent.getAttribute('id');
    const rawContent = contentArea.dataset.rawContent || contentArea.innerText;
    
    const originalHtml = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...`;

    try {
        const response = await fetch('/document/new_post', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: new URLSearchParams({
                'content': rawContent,
                'language': 'en',
                'ajax': '1'
            })
        });

        const result = await response.json();
        if (result.success) {
            btn.innerHTML = `<i class="bi bi-check-circle-fill"></i> Saved`;
            btn.classList.add('text-success');
            btn.classList.add('disabled');
            if (msgId) updateMessageSaveState(msgId, true);
            if (window.showToast) showToast("Response indexed successfully!", "success");
        } else {
            throw new Error(result.error || "Failed to save document.");
        }
    } catch (err) {
        console.error("Save failed:", err);
        btn.innerHTML = `<i class="bi bi-exclamation-triangle"></i> Error`;
        btn.classList.add('text-danger');
        btn.disabled = false;
        if (window.showToast) showToast("Failed to index content: " + err.message, "error");
    } finally {
        setTimeout(() => {
            if (!btn.classList.contains('text-success')) {
                btn.innerHTML = originalHtml;
                btn.classList.remove('text-danger');
            }
        }, 3000);
    }
}

/**
 * --- PERSISTENCE ---
 */

const HISTORY_KEY = 'assistant_chat_history_v1';

function saveToLocalHistory(sender, text, isSaved = false, id = null) {
    try {
        const history = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
        history.push({ 
            id: id || ('msg-' + Date.now()),
            sender, text, isSaved,
            timestamp: new Date().toISOString() 
        });
        if (history.length > 50) history.shift();
        localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
    } catch (e) { console.error("History save error", e); }
}

function updateMessageSaveState(id, isSaved) {
    try {
        let history = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
        history = history.map(msg => (msg.id === id ? { ...msg, isSaved } : msg));
        localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
    } catch (e) { console.error("History update error", e); }
}

function loadLocalHistory() {
    try {
        const history = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
        if (history.length === 0) return;

        const chatContainer = document.querySelector('.chat-container');
        if (chatContainer) {
            chatContainer.classList.remove('is-empty-chat');
            document.body.classList.add('is-query-active');
        }

        const fragment = document.createDocumentFragment();
        history.forEach(msg => {
            const msgDiv = createChatMessageDiv(msg.sender, msg.text, msg.id, msg.isSaved);
            if (msgDiv) fragment.appendChild(msgDiv);
        });
        
        const historyArea = document.getElementById('historyArea') || document.querySelector('.messages-wrapper');
        if (historyArea) historyArea.prepend(fragment);
        addClearHistoryUI();
    } catch (e) { console.error("History load error", e); }
}

function addClearHistoryUI() {
    const historyArea = document.getElementById('historyArea');
    if (!historyArea || document.getElementById('clearHistoryBtn')) return;

    const div = document.createElement('div');
    div.className = 'text-center my-4 opacity-50';
    div.innerHTML = `
        <button id="clearHistoryBtn" class="btn btn-sm btn-link text-muted" style="font-size: 0.7rem; text-decoration: none;" onclick="clearAssistantHistory()">
            <i class="bi bi-trash3"></i> Clear Assistant History
        </button>
    `;
    historyArea.prepend(div);
}

function clearAssistantHistory() {
    if (confirm("Clear local history?")) {
        localStorage.removeItem(HISTORY_KEY);
        const activeType = document.querySelector('.type-pill.active')?.dataset.type;
        if (activeType === 'assistant') window.location.reload();
        else {
            document.querySelectorAll('.assistant-mode-turn, .message-ai-turn, .message-user-turn').forEach(el => el.remove());
            document.getElementById('clearHistoryBtn')?.parentElement?.remove();
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    setTimeout(loadLocalHistory, 100);
});

/**
 * --- CONTENT GENERATOR ---
 */
window.aiGenerator = {
    isGenerating: false,
    controller: null,
    handleAction(textareaId, btnId, groupId, inputId) {
        const group = document.getElementById(groupId);
        const input = document.getElementById(inputId);
        const btn = document.getElementById(btnId);
        if (this.isGenerating) { this.stop(); return; }
        if (!group.classList.contains('d-none') && !input.value.trim()) { this.hide(btnId, groupId); return; }
        if (group.classList.contains('d-none')) {
            group.classList.remove('d-none');
            input.focus();
            btn.innerHTML = `<i class="bi bi-magic"></i> Write`;
            input.onkeydown = (e) => { if (e.key === 'Enter') { e.preventDefault(); this.generate(textareaId, btnId, groupId, inputId); } };
            return;
        }
        this.generate(textareaId, btnId, groupId, inputId);
    },
    hide(btnId, groupId) {
        document.getElementById(groupId)?.classList.add('d-none');
        const btn = document.getElementById(btnId);
        if (btn) btn.innerHTML = `<i class="bi bi-robot"></i> AI Generate`;
    },
    async generate(textareaId, btnId, groupId, inputId) {
        if (this.isGenerating) return;
        const textarea = document.getElementById(textareaId);
        const btn = document.getElementById(btnId);
        const group = document.getElementById(groupId);
        const input = document.getElementById(inputId);
        if (!textarea || !btn || !input) return;
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const selectedText = textarea.value.substring(start, end);
        const currentText = (selectedText || textarea.value).trim();
        const customInstruction = input.value.trim();
        try {
            this.isGenerating = true;
            this.controller = new AbortController();
            btn.innerHTML = `<i class="bi bi-stop-fill"></i> Stop`;
            btn.classList.add('btn-gen-stop');
            textarea.classList.add('textarea-generating');
            let prompt = "";
            const systemContext = "Generate ONLY raw content. NO conversational filler. NO HTML.";
            if (customInstruction) prompt = `${systemContext}\n\nInstruction: ${customInstruction}\n\nContext:\n${currentText}\n\nResponse:`;
            else if (!currentText) prompt = `${systemContext}\n\nTechnical concept KB entry.`;
            else prompt = `${systemContext}\n\nExpand professionally:\n\n${currentText}\n\nContinued:`;

            const response = await fetch('/api/quick-chat-stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                signal: this.controller.signal,
                body: JSON.stringify({ 
                    message: prompt,
                    provider: localStorage.getItem('ai_provider') || 'ollama',
                    model: localStorage.getItem('ai_model') || 'qwen2.5:0.5b',
                    api_key: localStorage.getItem('ai_api_key') || '',
                    base_url: localStorage.getItem('ollama_base_url') || 'http://localhost:11434'
                })
            });
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            if (selectedText) {
                textarea.value = textarea.value.substring(0, start);
                var currentPos = start;
                this.afterBuffer = textarea.value.substring(end);
            } else if (currentText) textarea.value += "\n\n";

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                let chunk = decoder.decode(value, { stream: true });
                chunk = chunk.replace(/&quot;/g, '"').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
                if (selectedText) {
                    const val = textarea.value;
                    textarea.value = val.substring(0, currentPos) + chunk + val.substring(currentPos);
                    currentPos += chunk.length;
                } else textarea.value += chunk;
                textarea.scrollTop = textarea.scrollHeight;
            }
            group.classList.add('d-none');
            input.value = '';
        } catch (err) { console.error("Gen error", err); }
        finally {
            this.isGenerating = false;
            btn.innerHTML = `<i class="bi bi-robot"></i> AI Generate`;
            btn.classList.remove('btn-gen-stop');
            textarea.classList.remove('textarea-generating');
        }
    },
    stop() { this.controller?.abort(); }
};
