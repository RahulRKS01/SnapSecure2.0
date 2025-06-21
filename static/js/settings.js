document.addEventListener('DOMContentLoaded', function () {
    const collapsibleTriggers = document.querySelectorAll('.collapsible-trigger');
    const videoSource = document.getElementById('videoSource');
    const uploadVideoSection = document.getElementById('uploadVideoSection');
    const videoFileInput = document.getElementById('videoFile');
    const saveSettingsButton = document.getElementById('saveSettings');
    const editROIButton = document.getElementById('editROI');
    const uploadButton = document.getElementById('uploadButton');
    const ipCameraSection = document.getElementById('ipCameraSection');
    const ipCameraAddress = document.getElementById('ipCameraAddress');
    const submitIpCamera = document.getElementById('submitIpCamera');
    const cameraSelectionSection = document.getElementById('cameraSelectionSection');
    const cameraIndexDropdown = document.getElementById('cameraIndex');
    const submitCameraIndexButton = document.getElementById('submitCameraIndex');

    // Handle collapsible behavior for all collapsible triggers
    collapsibleTriggers.forEach(trigger => {
        trigger.addEventListener('click', function () {
            const content = this.nextElementSibling;
            const toggleIcon = this.querySelector('.toggle-icon');

            // Toggle active class for content and icon
            content.classList.toggle('active');
            toggleIcon.classList.toggle('active');

            // Don't set height explicitly, let CSS handle it
            // This avoids conflicts between inline styles and CSS
        });
    });

    // Show or hide the upload video section based on the selected video source
    videoSource.addEventListener('change', function () {
        if (videoSource.value === 'upload') {
            uploadVideoSection.style.display = 'block';
        } else {
            uploadVideoSection.style.display = 'none';
        }

        if (videoSource.value === 'stream') {
            ipCameraSection.style.display = 'block';
        } else {
            ipCameraSection.style.display = 'none';
        }

        if (videoSource.value === 'camera') {
            cameraSelectionSection.style.display = 'block';

            // Fetch available cameras
            fetch('/get_available_cameras')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Populate the dropdown with available cameras
                        cameraIndexDropdown.innerHTML = '<option value="" disabled selected>Select a camera</option>';
                        data.cameras.forEach((camera, index) => {
                            const option = document.createElement('option');
                            option.value = index;
                            option.textContent = camera;
                            cameraIndexDropdown.appendChild(option);
                        });
                    } else {
                        alert('Failed to fetch available cameras: ' + data.message);
                    }
                })
                .catch(error => {
                    console.error('Error fetching cameras:', error);
                    alert('An error occurred while fetching available cameras.');
                });
        } else {
            cameraSelectionSection.style.display = 'none';
        }
    });

    // Ensure the upload section is displayed if "Upload" is preselected
    if (videoSource.value === 'upload') {
        uploadVideoSection.style.display = 'block';
    }

    // Ensure the IP camera section is displayed if "stream" is preselected
    if (videoSource.value === 'stream') {
        ipCameraSection.style.display = 'block';
    }

    // Handle Save Settings
    saveSettingsButton.addEventListener('click', function () {
        const settings = {
            videoSource: videoSource.value, // Include the selected video source
        };

        console.log('Saving settings:', settings); // Debug log

        fetch('/update_video_source', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(settings),
        })
            .then(response => response.json())
            .then(data => {
                console.log('Response from server:', data); // Debug log
                if (data.success) {
                    showToast('Settings saved successfully', 'success');
                } else {
                    showToast('Failed to save settings', 'error');
                }
            })
            .catch(error => {
                console.error('Error saving settings:', error);
                showToast('An error occurred while saving settings', 'error');
            });
    });

    // Replace the ROI Editor launch handler
    editROIButton.addEventListener('click', function (e) {
        e.preventDefault();
        
        window.location.href = '/web_roi_editor'
    });

    // Handle the "Upload" button click
    uploadButton.addEventListener('click', function () {
        const file = videoFileInput.files[0];
        if (!file) {
            alert('Please select a video file to upload.');
            return;
        }

        const formData = new FormData();
        formData.append('videoFile', file);

        fetch('/upload_video', {
            method: 'POST',
            body: formData,
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Video uploaded successfully.');
                } else {
                    alert('Failed to upload video.');
                }
            })
            .catch(error => {
                console.error('Error uploading video:', error);
                alert('An error occurred while uploading the video.');
            });
    });

    // Handle the "Submit" button click for IP camera address
    submitIpCamera.addEventListener('click', function (e) {
        e.preventDefault();

        const ipAddress = ipCameraAddress.value.trim();
        if (!ipAddress) {
            alert('Please enter a valid IP camera address.');
            return;
        }

        fetch('/update_ip_camera', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ ipCameraAddress: ipAddress }),
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('IP camera address updated successfully.');
                } else {
                    alert('Failed to update IP camera address: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while updating the IP camera address.');
            });
    });

    // Handle the "Submit" button click for camera index
    submitCameraIndexButton.addEventListener('click', function (e) {
        e.preventDefault();

        const cameraIndex = cameraIndexDropdown.value;
        if (!cameraIndex) {
            alert('Please select a camera.');
            return;
        }

        fetch('/update_camera_index', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ cameraIndex: parseInt(cameraIndex) }),
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Camera index updated successfully.');
                } else {
                    alert('Failed to update camera index: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while updating the camera index.');
            });
    });

    // Simple toast notification
    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.classList.add('show');
        }, 100);

        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 300);
        }, 3000);
    }
});