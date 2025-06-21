document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.querySelector('.dashboard-sidebar');
    const toast = document.getElementById('toast');

    // Function to show toast notification
    function showToast(message, type = 'info') {
        toast.textContent = message;
        toast.className = `toast toast-${type} show`;

        // Hide the toast after 3 seconds
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }

    // Mark as safe
    document.getElementById('markSafe')?.addEventListener('click', () => {
        fetch('/update_status', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ detection_id: '{{ detection.detection_id }}', status: 'safe' })
        }).then(response => {
            if (response.ok) {
                // Trigger flip animation
                sidebar.classList.add('flip-close');

                // Show toast notification
                showToast('Detection marked as safe. You can review it in the archive.', 'success');

                // Reload the page after the animation
                setTimeout(() => location.reload(), 600);
            } else {
                showToast('Failed to mark detection as safe.', 'error');
            }
        });
    });

    // Mark as theft
    document.getElementById('markTheft')?.addEventListener('click', () => {
        fetch('/update_status', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ detection_id: '{{ detection.detection_id }}', status: 'theft' })
        }).then(response => {
            if (response.ok) {
                // Trigger flip animation
                sidebar.classList.add('flip-close');

                // Show toast notification
                showToast('Detection marked as theft. You can review it in the archive.', 'success');

                // Reload the page after the animation
                setTimeout(() => location.reload(), 600);
            } else {
                showToast('Failed to mark detection as theft.', 'error');
            }
        });
    });

    // Mark as Verified Safe
    document.querySelectorAll('#verifySafe').forEach(button => {
        button.addEventListener('click', (event) => {
            const reportId = event.target.getAttribute('data-report-id');
            fetch('/update_verification', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ report_id: reportId, verification: true })
            }).then(response => {
                if (response.ok) {
                    alert('Report marked as Verified Safe.');
                    location.reload();
                } else {
                    alert('Failed to mark report as Verified Safe.');
                }
            });
        });
    });

    // Mark as Verified Theft
    document.querySelectorAll('#verifyTheft').forEach(button => {
        button.addEventListener('click', (event) => {
            const reportId = event.target.getAttribute('data-report-id');
            fetch('/update_verification', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ report_id: reportId, verification: false })
            }).then(response => {
                if (response.ok) {
                    alert('Report marked as Verified Theft.');
                    location.reload();
                } else {
                    alert('Failed to mark report as Verified Theft.');
                }
            });
        });
    });
});