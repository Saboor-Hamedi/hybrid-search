/**
 * AI Assistant Mode Logic
 * Handles interactive chat with Ollama proxy
 */

/**
 * Handle direct AI chat logic (No RAG, just conversation)
 */
async function handleAssistantChat(message) {
  const messagesArea = document.getElementById('messagesArea');
  const chatContainer = document.querySelector('.chat-container');
  const textarea = document.querySelector('.search-input');
  
  // 1. Ensure UI is ready for messages
  if (chatContainer.classList.contains('is-empty-chat')) {
    chatContainer.classList.remove('is-empty-chat');
    document.body.classList.add('is-query-active'); // Triggers hiding chat-hero and empty-state
  }
  
  // 2. Clear input
  textarea.value = '';
  textarea.style.height = 'auto';
  
  // 3. Append User Message
  appendChatMessage('user', message);
  
  // 4. Typing Indicator
  const typingId = 'typing-' + Date.now();
  appendChatMessage('bot', '...', typingId, true);
  scrollToBottom();

  try {
    const response = await fetch('/api/quick-chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: message })
    });

    const data = await response.json();
    
    // Remove typing
    document.getElementById(typingId)?.remove();

    if (data.reply) {
      appendChatMessage('bot', data.reply);
    } else {
      appendChatMessage('error', data.error || "No response. Is Ollama running?");
    }
  } catch (err) {
    document.getElementById(typingId)?.remove();
    appendChatMessage('error', "Connection error: Could not reach the AI service.");
  }
  
  scrollToBottom();
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
  const wrapper = document.querySelector('.messages-wrapper');
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
    const formatted = polishedText
        .replace(/\n/g, '<br>')
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
