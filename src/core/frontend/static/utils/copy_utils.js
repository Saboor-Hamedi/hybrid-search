/**
 * Utility to handle clipboard copying across the application
 */

window.copyToClipboard = function(btn, contentOrId, type = 'text') {
    let content = '';

    if (type === 'element') {
        const el = document.getElementById(contentOrId);
        content = el ? el.innerText : '';
    } else if (type === 'selector') {
        const parent = btn.closest(contentOrId.parent);
        const el = parent ? parent.querySelector(contentOrId.child) : null;
        content = el ? el.innerText : '';
    } else {
        content = contentOrId;
    }

    if (!content) {
        console.warn('Nothing to copy');
        return;
    }

    // Modern clipboard API
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(content).then(() => {
            showCopySuccess(btn);
        }).catch(err => {
            console.error('Failed to copy using navigator.clipboard: ', err);
            fallbackCopyToClipboard(btn, content);
        });
    } else {
        fallbackCopyToClipboard(btn, content);
    }
};

/**
 * Fallback for older browsers or non-secure contexts
 */
function fallbackCopyToClipboard(btn, text) {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    
    // Ensure the textarea is off-screen
    textArea.style.position = "fixed";
    textArea.style.left = "-9999px";
    textArea.style.top = "0";
    document.body.appendChild(textArea);
    
    textArea.focus();
    textArea.select();
    
    try {
        const successful = document.execCommand('copy');
        if (successful) showCopySuccess(btn);
    } catch (err) {
        console.error('Fallback copy failed: ', err);
    }
    
    document.body.removeChild(textArea);
}

/**
 * Visual feedback for copy success
 */
window.showCopySuccess = function(btn) {
    const iconEl = btn.querySelector('i');
    if (iconEl) {
        const originalClass = iconEl.className;
        iconEl.className = 'bi bi-check2 text-success';
        btn.classList.add('copy-success');
        
        setTimeout(() => {
            iconEl.className = originalClass;
            btn.classList.remove('copy-success');
        }, 2000);
    } else {
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="bi bi-check2 text-success"></i>';
        btn.classList.add('copy-success');
        setTimeout(() => {
            btn.innerHTML = originalText;
            btn.classList.remove('copy-success');
        }, 2000);
    }
}

window.copyCode = function(btn) {
    const container = btn.closest('.code-block-container');
    const code = container.querySelector('code').innerText;
    
    if (navigator.clipboard) {
        navigator.clipboard.writeText(code).then(() => {
            const originalHtml = btn.innerHTML;
            btn.innerHTML = '<i class="bi bi-check2 text-success"></i>';
            setTimeout(() => {
                btn.innerHTML = originalHtml;
            }, 2000);
        });
    }
}
