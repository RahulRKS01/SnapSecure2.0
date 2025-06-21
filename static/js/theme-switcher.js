function getCurrentTheme() {
    return document.documentElement.getAttribute('data-theme') || 'dark';
}

document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.getElementById('themeToggle');
    
    // Only proceed if the theme toggle exists on the page
    if (!themeToggle) {
        console.log("Theme toggle not found on this page");
        return;
    }
    
    console.log("Theme toggle found, initializing...");
    
    // Check for saved theme preference
    const savedTheme = localStorage.getItem('theme') || 'dark';
    
    // Apply theme to HTML element
    document.documentElement.setAttribute('data-theme', savedTheme);
    themeToggle.checked = savedTheme === 'light';
    
    console.log("Initial theme set to:", savedTheme);
    
    // Listen for toggle changes
    themeToggle.addEventListener('click', function() {
        // Use setTimeout to ensure the checked state is updated first
        setTimeout(() => {
            const newTheme = themeToggle.checked ? 'light' : 'dark';
            console.log("Toggle changed, setting theme to:", newTheme);
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            
            // Create simple toast notification
            const toast = document.createElement('div');
            toast.className = 'toast toast-info';
            toast.textContent = `Theme switched to ${newTheme} mode`;
            document.body.appendChild(toast);
            
            // Show toast
            setTimeout(() => toast.classList.add('show'), 10);
            
            // Hide toast after 3 seconds
            setTimeout(() => {
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), 300);
            }, 3000);
        }, 0);
    });
});