/**
 * Sidebar Toggle and State Persistence Logic
 */
document.addEventListener('DOMContentLoaded', () => {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const appLayout = document.getElementById('appLayout');
    
    if (sidebarToggle && appLayout) {
        // Toggle Click Listener
        sidebarToggle.addEventListener('click', () => {
            const newState = appLayout.classList.toggle('sidebar-collapsed');
            localStorage.setItem('sidebar-collapsed', newState);
        });
    }
});
