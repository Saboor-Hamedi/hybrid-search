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

    try {
        const aiProvider = localStorage.getItem('ai_provider') || 'ollama';
        const aiModel = localStorage.getItem('ai_model') || 'qwen2.5:0.5b';
        const aiApiKey = localStorage.getItem('ai_api_key') || '';
        const ollamaBaseUrl = localStorage.getItem('ollama_base_url') || 'http://localhost:11434';

        const response = await fetch('/api/quick-chat', {
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

        const data = await response.json();
        
        // Replace typing skeleton with actual response
        const resultsArea = document.getElementById(typingId);
        if (resultsArea && data.reply) {
            const polished = polishChatText(data.reply);
            resultsArea.innerHTML = `
                <div class="message message-ai-turn d-flex gap-3">
                    <div class="chat-avatar ai-avatar">
                        <i class="bi bi-robot"></i>
                    </div>
                    <div class="message-response flex-grow-1 chat-bubble-ai">
                        ${formatBotResponse(polished)}
                    </div>
                </div>`;
        } else if (resultsArea) {
            resultsArea.innerHTML = `<div class="alert alert-danger mx-5 small">${data.error || "No response."}</div>`;
        }
        
        scrollToBottom();
    } catch (err) {
        console.error("Assistant chat failed", err);
        const resultsArea = document.getElementById(typingId);
        if (resultsArea) resultsArea.innerHTML = `<div class="alert alert-danger mx-5 small">Error: ${err.message}</div>`;
    }
}

function formatBotResponse(text) {
    return text
        .replace(/\r\n/g, '\n')
        .replace(/\n/g, '<br>')
        .replace(/```(\w*)\n?([\s\S]*?)```/g, (match, lang, code) => {
            return `
            <div class="code-block-container my-2">
                <div class="code-block-header">
                    <span>${lang || 'code'}</span>
                    <button class="copy-code-btn" onclick="copyCode(this)">
                        <i class="bi bi-clipboard"></i> Copy
                    </button>
                </div>
                <pre><code>${code.trim()}</code></pre>
            </div>`;
        })
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/`(.*?)`/g, '<code>$1</code>');
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
    let formatted = polishedText
        .replace(/\r\n/g, '\n')
        .replace(/\n/g, '<br>')
        .replace(/```(\w*)\n?([\s\S]*?)```/g, (match, lang, code) => {
            return `
            <div class="code-block-container">
                <div class="code-block-header">
                    <span>${lang || 'code'}</span>
                    <button class="copy-code-btn" onclick="copyCode(this)">
                        <i class="bi bi-clipboard"></i> Copy
                    </button>
                </div>
                <pre><code>${code.trim()}</code></pre>
            </div>`;
        })
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/`(.*?)`/g, '<code>$1</code>')
        .replace(/\[Doc\s*(\d+)\]/g, '<strong class="text-primary small mx-1">#$1</strong>');
        
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
            <button class="action-btn" onclick="copyToClipboard(this, {parent: '.assistant-chat-bot', child: '.assistant-content'}, 'selector')" title="Copy Response">
                <i class="bi bi-copy"></i> Copy
            </button>
            <button class="action-btn" onclick="handleFeedback(this, 'like')" title="Helpful">
                <i class="bi bi-hand-thumbs-up"></i>
            </button>
            <button class="action-btn" onclick="handleFeedback(this, 'dislike')" title="Not Helpful">
                <i class="bi bi-hand-thumbs-down"></i>
            </button>
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
