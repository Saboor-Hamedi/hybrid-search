/**
 * Global Chat Widget Logic
 * Handles standalone chat interactions with the local Ollama proxy.
 */

const GC_API_ENDPOINT = '/api/quick-chat';

function toggleGlobalChat() {
    const container = document.getElementById('gc-container');
    const btn = document.getElementById('gc-toggle-btn');
    
    container.classList.toggle('visible');
    btn.classList.toggle('open');
    
    if (container.classList.contains('visible')) {
        document.getElementById('gc-input').focus();
    }
}

// Auto-resize textarea
const gcInput = document.getElementById('gc-input');
if (gcInput) {
    gcInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        if (this.value === '') this.style.height = 'auto';
    });
    
    gcInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendGlobalMessage();
        }
    });
}

async function sendGlobalMessage() {
    const input = document.getElementById('gc-input');
    const messagesDiv = document.getElementById('gc-messages');
    const sendBtn = document.getElementById('gc-send-btn');
    const typingIndicator = document.getElementById('gc-typing');
    
    const text = input.value.trim();
    if (!text) return;

    // UI Updates
    input.value = '';
    input.style.height = 'auto';
    appendMessage('user', text);
    
    // Disable interactions
    input.disabled = true;
    sendBtn.disabled = true;
    
    // Show typing
    typingIndicator.style.display = 'block';
    messagesDiv.scrollTop = messagesDiv.scrollHeight;

    try {
        const response = await fetch(GC_API_ENDPOINT, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text })
        });

        const data = await response.json();
        
        // Hide typing
        typingIndicator.style.display = 'none';

        if (data.reply) {
            appendMessage('bot', data.reply);
        } else if (data.error) {
            appendMessage('error', 'Error: ' + data.error);
        } else {
            appendMessage('bot', "I didn't get a response. Please check if Ollama is running.");
        }

    } catch (e) {
        console.error(e);
        typingIndicator.style.display = 'none';
        appendMessage('error', 'Network Error: Could not reach the server.');
    } finally {
        input.disabled = false;
        sendBtn.disabled = false;
        input.focus();
    }
}

// Helper to polish text
function polishChatText(text) {
    if (!text) return "";
    let polished = text.replace(/(^\s*\w|[.!?]\s*\w)/g, c => c.toUpperCase());
    polished = polished.replace(/\b(ai|ml|rrf|api|llm|nlp|db|sql|ui|ux|pdf)\b/gi, match => match.toUpperCase());
    return polished;
}

function appendMessage(sender, text) {
    const messagesDiv = document.getElementById('gc-messages');
    const typingIndicator = document.getElementById('gc-typing');
    
    if (sender === 'bot') {
        text = polishChatText(text);
    }
    
    const msgDiv = document.createElement('div');
    msgDiv.className = `gc-message ${sender}`;
    msgDiv.style.position = 'relative'; // For positioning copy btn if needed
    
    // Simple formatting
    let formatted = text
        .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;") 
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/`(.*?)`/g, '<code>$1</code>');

    msgDiv.innerHTML = formatted;
    
    // Add Copy Button for ALL messages (Bot & User)
    const copyBtn = document.createElement('div');
    copyBtn.className = 'gc-msg-footer mt-2 text-end';
    
    // Style: simpler is safer. Just an icon and 'Copy'.
    const btnClass = sender === 'user' ? 'text-white-50' : 'text-muted';
    
    copyBtn.innerHTML = `
        <button class="btn btn-sm btn-link p-0 text-decoration-none ${btnClass} gc-copy-btn" style="font-size: 0.75rem;">
            <i class="bi bi-clipboard"></i> Copy
        </button>
    `;
    msgDiv.appendChild(copyBtn);
    
    // Insert BEFORE the typing indicator
    messagesDiv.insertBefore(msgDiv, typingIndicator);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// Event Delegation for Copy Buttons (Robust for infinite messages)
document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('gc-messages');
    if (container) {
        container.addEventListener('click', (e) => {
            const btn = e.target.closest('.gc-copy-btn');
            if (btn) {
                // Find text
                const msgText = btn.closest('.gc-message').innerText.replace('Copy', '').trim();
                navigator.clipboard.writeText(msgText).then(() => {
                    const originalHTML = btn.innerHTML;
                    btn.innerHTML = '<i class="bi bi-check"></i>';
                    setTimeout(() => btn.innerHTML = originalHTML, 1500);
                });
            }
        });
    }
});
