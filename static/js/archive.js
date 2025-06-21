document.addEventListener('DOMContentLoaded', function () {
    const applyFiltersButton = document.getElementById('applyFilters');
    const resetFiltersButton = document.getElementById('resetFilters');
    const archiveContent = document.getElementById('archiveContent');

    const fetchFilteredData = async (filters) => {
        const queryParams = new URLSearchParams(filters).toString();
        const response = await fetch(`/archive?${queryParams}`, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        const html = await response.text();

        // Replace the archive content with the filtered results
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const newContent = doc.getElementById('archiveContent');
        archiveContent.innerHTML = newContent.innerHTML;

        // Reattach event listeners for dynamically added cards
        document.getElementById('archiveContent').addEventListener('click', function (event) {
            const card = event.target.closest('.card');
            if (card) {
                const image = card.getAttribute('data-image') || 'images/default-img.jpg';
                const type = card.getAttribute('data-type') || 'N/A';
                const confidence = card.getAttribute('data-confidence') || 'N/A';
                const date = card.getAttribute('data-date') || 'N/A';
                const time = card.getAttribute('data-time') || 'N/A';
                const detectionId = card.getAttribute('data-detection-id') || 'N/A';
                openModal(image, type, confidence, date, time, detectionId);
            }
        });
    };

    applyFiltersButton.addEventListener('click', function () {
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        const detectionType = document.getElementById('detectionType').value;

        const filters = {
            startDate,
            endDate,
            detectionType
        };

        fetchFilteredData(filters);
    });

    resetFiltersButton.addEventListener('click', function () {
        document.getElementById('startDate').value = '';
        document.getElementById('endDate').value = '';
        document.getElementById('detectionType').value = 'all';

        fetchFilteredData({});
    });

    // Use event delegation to handle clicks on dynamically added cards
    document.getElementById('archiveContent').addEventListener('click', function (event) {
        const card = event.target.closest('.card'); // Check if the clicked element is inside a card
        if (card) {
            const image = card.getAttribute('data-image') || 'images/default-img.jpg';
            const type = card.getAttribute('data-type') || 'N/A';
            const confidence = card.getAttribute('data-confidence') || 'N/A';
            const date = card.getAttribute('data-date') || 'N/A';
            const time = card.getAttribute('data-time') || 'N/A';
            const detectionId = card.getAttribute('data-detection-id') || '';
            openModal(image, type, confidence, date, time, detectionId);
        }
    });

    // Add event listener for delete button
    document.getElementById('deleteDetectionBtn')?.addEventListener('click', function() {
        const detectionId = this.getAttribute('data-detection-id');
        if (detectionId) {
            deleteDetection(detectionId);
        }
    });
});

// Update the openModal function to include detection_id
function openModal(image, type, confidence, date, time, detectionId) {
    const modal = document.getElementById('detectionModal');
    const defaultImage = 'static/images/default-img.jpg';
    document.getElementById('modalImage').src = image && image !== 'images/default-img.png' ? image : defaultImage;
    document.getElementById('modalType').textContent = type || 'N/A';
    document.getElementById('modalConfidence').textContent = confidence || 'N/A';
    document.getElementById('modalDate').textContent = date || 'N/A';
    document.getElementById('modalTime').textContent = time || 'N/A';
    
    // Set the detection ID as a data attribute on the delete button
    document.getElementById('deleteDetectionBtn').setAttribute('data-detection-id', detectionId);
    
    modal.style.display = 'flex'; // Show the modal
}

// Add this function to handle deletion
function deleteDetection(detectionId) {
    console.log("Attempting to delete detection with ID:", detectionId);
    
    // Create and show confirmation dialog
    const confirmDialog = document.createElement('div');
    confirmDialog.className = 'confirm-dialog';
    confirmDialog.innerHTML = `
        <h3>Delete Detection</h3>
        <p>Are you sure you want to delete this detection and its associated report? This action cannot be undone.</p>
        <div class="confirm-actions">
            <button class="btn-cancel">Cancel</button>
            <button class="btn-confirm">Delete</button>
        </div>
    `;
    document.body.appendChild(confirmDialog);
    
    // Handle dialog buttons
    confirmDialog.querySelector('.btn-cancel').addEventListener('click', () => {
        document.body.removeChild(confirmDialog);
    });
    
    confirmDialog.querySelector('.btn-confirm').addEventListener('click', () => {
        // Remove the dialog
        document.body.removeChild(confirmDialog);
        
        // Make the DELETE request
        fetch(`/delete_detection/${detectionId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Close the modal
                closeModal();
                
                // Remove the deleted card from the grid
                const deletedCard = document.querySelector(`.card[data-detection-id="${detectionId}"]`);
                if (deletedCard) {
                    deletedCard.remove();
                }
                
                // Show a success message
                showToast('Detection and associated report deleted successfully', 'success');
            } else {
                showToast(data.message || 'Failed to delete detection', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('An error occurred while deleting the detection', 'error');
        });
    });
}

// Add a toast notification function
function showToast(message, type = 'info') {
    // Create toast element if it doesn't exist
    let toast = document.getElementById('toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'toast';
        toast.className = 'toast';
        document.body.appendChild(toast);
    }
    
    // Set toast content and type
    toast.textContent = message;
    toast.className = `toast ${type === 'success' ? 'toast-success' : type === 'error' ? 'toast-error' : 'toast-info'}`;
    toast.classList.add('show');
    
    // Hide after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

function closeModal() {
    const modal = document.getElementById('detectionModal');
    modal.style.display = 'none'; // Hide the modal
}

// Close the modal when clicking outside the content
window.addEventListener('click', function (event) {
    const modal = document.getElementById('detectionModal');
    if (event.target === modal) {
        closeModal();
    }
});

function expandToFullscreen() {
    const modalImage = document.getElementById('modalImage');
    if (modalImage.requestFullscreen) {
        modalImage.requestFullscreen();
    } else if (modalImage.webkitRequestFullscreen) { // Safari
        modalImage.webkitRequestFullscreen();
    } else if (modalImage.msRequestFullscreen) { // IE/Edge
        modalImage.msRequestFullscreen();
    }
}

// Close fullscreen when the user exits fullscreen mode
document.addEventListener('fullscreenchange', () => {
    if (!document.fullscreenElement) {
        console.log('Exited fullscreen mode');
    }
});