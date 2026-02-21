/**
 * Sidebar Toggle and State Persistence Logic
 */
document.addEventListener('DOMContentLoaded', () => {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const appLayout = document.getElementById('appLayout');
    
    if (sidebarToggle && appLayout) {
        // Initial Check for 800 width
        const checkWidth = () => {
            if (window.innerWidth <= 800) {
                appLayout.classList.add('sidebar-collapsed');
            }
        };

        // Run once on load
        checkWidth();

        // Toggle Click Listener
        sidebarToggle.addEventListener('click', () => {
            const newState = appLayout.classList.toggle('sidebar-collapsed');
            localStorage.setItem('sidebar-collapsed', newState);
        });

        // Optional: Close on resize if crossing the threshold
        window.addEventListener('resize', () => {
            if (window.innerWidth <= 800 && !appLayout.classList.contains('sidebar-collapsed')) {
                appLayout.classList.add('sidebar-collapsed');
            }
        });
    }
});
