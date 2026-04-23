/**
 * Unified Notification System (Singleton)
 * Provides a clean, reusable toast interface across all components.
 */
window.Notify = (function() {
    let container = null;

    function init() {
        if (container) return;
        container = document.createElement('div');
        container.id = 'unified-toast-container';
        container.style.cssText = `
            position: fixed;
            top: 60px;
            right: 20px;
            z-index: 11000;
            display: flex;
            flex-direction: column;
            gap: 12px;
            pointer-events: none;
        `;
        document.body.appendChild(container);

        // Global Styles
        const style = document.createElement('style');
        style.id = 'unified-toast-styles';
        style.innerHTML = `
            @keyframes toastSlideIn { 
                from { transform: translateX(100%); opacity: 0; } 
                to { transform: translateX(0); opacity: 1; } 
            }
            @keyframes toastSlideOut { 
                from { transform: translateX(0); opacity: 1; } 
                to { transform: translateX(100%); opacity: 0; } 
            }
            .notify-toast {
                min-width: 280px;
                max-width: 380px;
                background: #ffffff;
                border-radius: 16px;
                padding: 12px 16px;
                box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1), 0 5px 10px -5px rgba(0,0,0,0.04);
                border: 1px solid #f3f4f6;
                display: flex;
                align-items: center;
                gap: 12px;
                pointer-events: auto;
                animation: toastSlideIn 0.4s cubic-bezier(0.16, 1, 0.3, 1);
                transition: opacity 0.3s, transform 0.3s;
            }
            .notify-toast.hiding { animation: toastSlideOut 0.4s forwards; }
            .notify-content { flex-grow: 1; min-width: 0; }
            .notify-title { font-size: 0.85rem; font-weight: 700; color: #111827; line-height: 1.3; }
            .notify-desc { font-size: 0.75rem; color: #6b7280; line-height: 1.2; word-wrap: break-word; margin-top: 2px; }
            .notify-icon { font-size: 1.25rem; flex-shrink: 0; display: flex; align-items: center; justify-content: center; width: 32px; height: 32px; border-radius: 8px; background: #f9fafb; transition: all 0.3s; }
            .notify-progress { height: 4px; background: #e5e7eb; border-radius: 2px; margin-top: 8px; overflow: hidden; display: none; }
            .notify-progress-bar { height: 100%; background: #2563eb; width: 0%; transition: width 0.3s ease; }
            .notify-toast.success .notify-progress-bar { background: #10b981; }

            /* Simulator Insight Card */
            .sim-insight-card {
                position: fixed;
                z-index: 12000;
                width: 320px;
                background: white;
                border-radius: 12px;
                box-shadow: 0 15px 35px -5px rgba(0,0,0,0.2);
                border: 1px solid #e5e7eb;
                padding: 16px;
                display: none;
                pointer-events: none;
                transition: opacity 0.2s, transform 0.2s;
                transform: translateY(10px);
                opacity: 0;
            }
            .sim-insight-card.show {
                display: block !important;
                opacity: 1;
                transform: translateY(0);
            }
            .insight-header { border-bottom: 1px solid #f3f4f6; margin-bottom: 10px; padding-bottom: 8px; }
            .insight-score-row { display: flex; justify-content: space-between; margin-bottom: 4px; font-size: 10px; }
            .insight-pill { padding: 2px 6px; border-radius: 4px; font-weight: bold; }
        `;
        document.head.appendChild(style);
    }

    /**
     * Shows a notification toast
     * @param {string} title Text content
     * @param {string} type 'success', 'danger', 'info', 'warning'
     * @param {number} duration ms to show (-1 for persistent)
     * @param {boolean} showLoader 
     */
    function show(title, type = 'info', duration = 4000, showLoader = false) {
        init();
        
        const toast = document.createElement('div');
        toast.className = `notify-toast ${type}`;
        
        let iconHtml = '<i class="bi bi-info-circle text-primary"></i>';
        if (showLoader) iconHtml = '<div class="spinner-border spinner-border-sm text-primary" role="status"></div>';
        else if (type === 'success') iconHtml = '<i class="bi bi-check-circle-fill text-success"></i>';
        else if (type === 'danger') iconHtml = '<i class="bi bi-exclamation-octagon-fill text-danger"></i>';
        else if (type === 'warning') iconHtml = '<i class="bi bi-exclamation-triangle-fill text-warning"></i>';

        toast.innerHTML = `
            <div class="notify-icon">${iconHtml}</div>
            <div class="notify-content">
                <div class="notify-title">${title}</div>
                <div class="notify-progress"><div class="notify-progress-bar"></div></div>
            </div>
            <button type="button" class="btn-close" style="font-size: 0.65rem;" onclick="this.parentElement.remove()"></button>
        `;

        container.appendChild(toast);

        if (duration > 0) {
            setTimeout(() => {
                toast.classList.add('hiding');
                setTimeout(() => toast.remove(), 400);
            }, duration);
        }
        
        return {
            update: (newTitle, newType = type) => {
                toast.querySelector('.notify-title').innerText = newTitle;
                if (newType !== type) {
                    const iconArea = toast.querySelector('.notify-icon');
                    toast.classList.remove('success', 'danger', 'info', 'warning');
                    toast.classList.add(newType);
                    
                    if (newType === 'success') iconArea.innerHTML = '<i class="bi bi-check-circle-fill text-success"></i>';
                    else if (newType === 'danger') iconArea.innerHTML = '<i class="bi bi-exclamation-octagon-fill text-danger"></i>';
                }
            },
            setProgress: (percent) => {
                const prog = toast.querySelector('.notify-progress');
                const bar = toast.querySelector('.notify-progress-bar');
                if (prog) prog.style.display = 'block';
                if (bar) bar.style.width = `${percent}%`;
            },
            close: () => {
                toast.classList.add('hiding');
                setTimeout(() => toast.remove(), 400);
            }
        };
    }

    return { show };
})();
