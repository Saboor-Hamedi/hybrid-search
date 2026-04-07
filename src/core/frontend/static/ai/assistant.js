/**
 * AI Assistant Mode Logic
 * Handles interactive chat with Ollama proxy
 */

/**
 * Handle direct AI chat logic (No RAG, just conversation)
 */
async function handleAssistantChat(message) {
  const historyArea = document.getElementById('historyArea');
  const chatContainer = document.querySelector('.chat-container');
  const textarea = document.querySelector('.search-input');
  
  // 1. Ensure UI is ready 
  if (chatContainer && chatContainer.classList.contains('is-empty-chat')) {
    chatContainer.classList.remove('is-empty-chat');
    document.body.classList.add('is-query-active');
  }

  // 2. Clear input
  if (textarea) {
    textarea.value = '';
    textarea.style.height = 'auto';
  }

  // 3. Create a Turn Container (Unified with Search Engine)
  const turnId = 'assistant-turn-' + Date.now();
  const turnDiv = document.createElement('div');
  turnDiv.id = turnId;
  turnDiv.className = 'search-turn-container mb-4 assistant-mode-turn';
  if (historyArea) historyArea.appendChild(turnDiv);

  // 4. Render User Message & Bot Skeleton
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
  
  // Save User Message to History
  saveToLocalHistory('user', message);

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
        
        // Results area setup
        const resultsArea = document.getElementById(typingId);
        if (resultsArea) {
            resultsArea.innerHTML = `
                <div class="message message-ai-turn d-flex gap-3">
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
            
            // Progressive rendering with simple formatting
            contentArea.innerHTML = formatBotResponse(fullReply);
            scrollToBottom();
        }

        // Final Polish
        const finalPolished = polishChatText(fullReply);
        contentArea.innerHTML = formatBotResponse(finalPolished);
        
        // Add actions after stream is done
        const responseWrapper = resultsArea.querySelector('.message-response');
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'assistant-actions mt-3 d-flex gap-2';
        actionsDiv.innerHTML = getAssistantActionsHtml();
        responseWrapper.appendChild(actionsDiv);
        
        scrollToBottom();

        // Save AI Response to History
        saveToLocalHistory('bot', fullReply);
    } catch (err) {
        console.error("Assistant chat failed", err);
        const resultsArea = document.getElementById(typingId);
        if (resultsArea) resultsArea.innerHTML = `<div class="alert alert-danger mx-5 small">Error: ${err.message}</div>`;
    }
}

function formatBotResponse(text) {
    if (!text) return "";

    // 1. Pre-process: Help marked with some specific formatting
    let cleanText = text.replace(/\r\n/g, '\n');

    // 2. Configure marked for great rendering
    if (window.marked) {
        // Use marked for the heavy lifting
        return marked.parse(cleanText, {
            breaks: true, // Support single line breaks as <br>
            gfm: true     // GitHub Flavored Markdown
        });
    }

    // Fallback if marked is missing (unlikely)
    return cleanText.replace(/\n/g, '<br>');
}

/**
 * Configure marked renderer for custom code blocks
 */
if (window.marked) {
    const renderer = new marked.Renderer();
    
    renderer.code = function(code, language) {
        const lang = language || 'code';
        return `
        <div class="code-block-container my-3">
            <div class="code-block-header">
                <span>${lang}</span>
                <button class="copy-code-btn" onclick="copyCode(this)">
                    <i class="bi bi-clipboard"></i> Copy
                </button>
            </div>
            <pre><code class="language-${lang}">${code}</code></pre>
        </div>`;
    };

    marked.setOptions({ renderer: renderer });
}


/**
 * Handle Like/Dislike feedback
 */
function handleFeedback(btn, type) {
  const actions = btn.closest('.assistant-actions');
  const allBtns = actions.querySelectorAll('.action-btn');
  
  // Reset previous selection
  allBtns.forEach(b => b.classList.remove('active'));
  
  // Highlight current selection
  btn.classList.add('active');
  
  // Optional: Send to backend
  console.log(`Feedback received: ${type}`);
}

/**
 * Utility to append a message bubble to the messages area
 */
function appendChatMessage(sender, text, id = null, isTyping = false) {
  let wrapper = document.getElementById('historyArea');
  if (!wrapper) wrapper = document.querySelector('.messages-wrapper');
  if (!wrapper) return;

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
        <div class="assistant-content">
          ${isTyping ? '<div class="typing-indicator"><span></span><span></span><span></span></div>' : formatted}
        </div>
        ${!isTyping ? `
        <div class="assistant-actions mt-3 d-flex gap-2">
            ${getAssistantActionsHtml()}
        </div>
        ` : ''}
      </div>
    `;
  } else {
    contentHtml = `<div class="alert alert-danger py-2 small flex-grow-1">${text}</div>`;
  }

  msgDiv.innerHTML = contentHtml;
  wrapper.appendChild(msgDiv);
}

/**
 * Reuse polishing from global chat
 */
function polishChatText(text) {
  if (!text) return "";
  // Simple cleaning: ensure first letter is capitalized, trim whitespace
  let clean = text.trim();
  return clean.charAt(0).toUpperCase() + clean.slice(1);
}

/**
 * Returns the HTML for assistant action buttons to avoid duplication
 */
function getAssistantActionsHtml() {
    return `
        <button class="action-btn" onclick="copyToClipboard(this, {parent: '.assistant-chat-bot', child: '.assistant-content'}, 'selector')" title="Copy Response">
            <i class="bi bi-copy"></i> Copy
        </button>
        <button class="action-btn" onclick="saveToDatabase(this)" title="Save to Knowledge Base">
            <i class="bi bi-plus-circle"></i> Save
        </button>
        <button class="action-btn" onclick="handleFeedback(this, 'like')" title="Helpful">
            <i class="bi bi-hand-thumbs-up"></i>
        </button>
        <button class="action-btn" onclick="handleFeedback(this, 'dislike')" title="Not Helpful">
            <i class="bi bi-hand-thumbs-down"></i>
        </button>`;
}

/**
 * Handle insertion of AI response into the database (Knowledge Base)
 */
async function saveToDatabase(btn) {
    const parent = btn.closest('.message-ai-turn');
    const contentArea = parent.querySelector('.assistant-content');
    if (!contentArea) return;

    // Get cleaned content (strip HTML tags since it's formatted for UI)
    const rawContent = contentArea.innerText;
    
    // UI Loading state
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
                'language': 'en', // Backend detects language anyway
                'ajax': '1'
            })
        });

        const result = await response.json();
        if (result.success) {
            btn.innerHTML = `<i class="bi bi-check-circle-fill"></i> Saved`;
            btn.classList.add('text-success');
            
            // Trigger toast if global showToast exists
            if (window.showToast) {
                showToast("Response indexed into Knowledge Base successfully!", "success");
            }
        } else {
            throw new Error(result.error || "Failed to save document.");
        }
    } catch (err) {
        console.error("Save failed:", err);
        btn.innerHTML = `<i class="bi bi-exclamation-triangle"></i> Error`;
        btn.classList.add('text-danger');
        if (window.showToast) {
            showToast("Failed to index content: " + err.message, "error");
        }
    } finally {
        setTimeout(() => {
            if (!btn.classList.contains('text-success')) {
                btn.innerHTML = originalHtml;
                btn.disabled = false;
                btn.classList.remove('text-danger');
            }
        }, 3000);
    }
}

/**
 * --- PERSISTENCE LOGIC ---
 */

const HISTORY_KEY = 'assistant_chat_history_v1';

function saveToLocalHistory(sender, text) {
    try {
        const history = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
        history.push({ 
            sender, 
            text, 
            timestamp: new Date().toISOString() 
        });
        // Limit history to last 50 messages to keep performance
        if (history.length > 50) history.shift();
        localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
    } catch (e) {
        console.error("Failed to save to local history", e);
    }
}

function loadLocalHistory() {
    try {
        const history = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
        if (history.length === 0) return;

        // If history exists, ensure UI is prepped
        const chatContainer = document.querySelector('.chat-container');
        if (chatContainer) {
            chatContainer.classList.remove('is-empty-chat');
            document.body.classList.add('is-query-active');
        }

        history.forEach(msg => {
            appendChatMessage(msg.sender, msg.text);
        });
        
        // Add a "Clear History" divider/button if messages exist
        addClearHistoryUI();
        scrollToBottom();
    } catch (e) {
        console.error("Failed to load local history", e);
    }
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
    if (confirm("Are you sure you want to clear your local assistant chat history?")) {
        localStorage.removeItem(HISTORY_KEY);
        // If we are currently in assistant mode without a research query, reload to reset UI
        const activeType = document.querySelector('.type-pill.active')?.dataset.type;
        if (activeType === 'assistant') {
            window.location.reload();
        } else {
            // Just remove the visual turns
            document.querySelectorAll('.assistant-mode-turn, .message-ai-turn, .message-user-turn').forEach(el => {
                if (el.closest('.assistant-mode-turn') || !el.querySelector('.rank-badges')) { // Only remove assistant messages
                    el.remove();
                }
            });
            document.getElementById('clearHistoryBtn')?.parentElement?.remove();
        }
    }
}

// Global initialization
document.addEventListener('DOMContentLoaded', () => {
    // Small delay to ensure other UI components are ready
    setTimeout(loadLocalHistory, 100);
});
