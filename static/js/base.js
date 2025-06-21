document.addEventListener('DOMContentLoaded', function () {
    const logoutLink = document.querySelector('.sidebar-link[href="/logout"]'); // Adjust selector if needed
    const logoutModal = document.getElementById('logoutModal');
    const confirmLogout = document.getElementById('confirmLogout');
    const cancelLogout = document.getElementById('cancelLogout');

    if (logoutLink) {
        logoutLink.addEventListener('click', function (e) {
            e.preventDefault(); // Prevent default logout action
            logoutModal.style.display = 'flex'; // Show the modal
        });
    }

    if (cancelLogout) {
        cancelLogout.addEventListener('click', function () {
            logoutModal.style.display = 'none'; // Hide the modal
        });
    }

    if (confirmLogout) {
        confirmLogout.addEventListener('click', function () {
            window.location.href = '/logout'; // Redirect to the logout route
        });
    }

    // Close the modal when clicking outside the content
    window.addEventListener('click', function (e) {
        if (e.target === logoutModal) {
            logoutModal.style.display = 'none';
        }
    });
});

// Add this function at the end of the file
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerText = message;
    document.body.appendChild(toast);
    
    // Show the toast
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);
    
    // Hide the toast after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 3000);
}