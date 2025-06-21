document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on a page with the video feed
    const feedContainer = document.querySelector('.feed-container');
    if (!feedContainer) return;
    
    // Store polylines data
    let polylines = [];
    
    // Function to check if we're using browser camera
    function checkIfUsingBrowserCamera() {
        fetch('/get_video_source')
            .then(response => response.json())
            .then(data => {
                if (data.success && data.video_source === 'browser_camera') {
                    // Fetch polylines data first
                    fetchPolylines().then(() => {
                        setupBrowserCamera();
                    });
                }
            })
            .catch(error => console.error('Error checking video source:', error));
    }
    
    // Fetch polylines data
    function fetchPolylines() {
        return fetch('/get_polylines')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Convert the saved format to our format
                    polylines = data.polylines.map(poly => 
                        poly.map(point => ({x: point[0][0], y: point[0][1]}))
                    );
                    console.log("Loaded polylines:", polylines);
                }
            })
            .catch(error => {
                console.error('Error loading polylines:', error);
            });
    }
    
    // Set up browser camera
    function setupBrowserCamera() {
        // Replace the server-side video feed with a local camera feed
        const feedImage = feedContainer.querySelector('.feed-image');
        if (!feedImage) return;
        
        // Create camera elements
        const videoElement = document.createElement('video');
        videoElement.id = 'browserCameraFeed';
        videoElement.autoplay = true;
        videoElement.muted = true;
        videoElement.style.width = '100%';
        videoElement.style.maxWidth = '640px';
        videoElement.style.height = 'auto';
        
        // Create canvas for drawing detections
        const canvasElement = document.createElement('canvas');
        canvasElement.id = 'detectionCanvas';
        canvasElement.style.position = 'absolute';
        canvasElement.style.top = '0';
        canvasElement.style.left = '0';
        canvasElement.style.width = '100%';
        canvasElement.style.height = '100%';
        
        // Create a wrapper to hold both video and canvas
        const wrapper = document.createElement('div');
        wrapper.style.position = 'relative';
        wrapper.appendChild(videoElement);
        wrapper.appendChild(canvasElement);
        
        // Replace the image with our video+canvas wrapper
        feedImage.style.display = 'none';
        feedContainer.insertBefore(wrapper, feedImage);
        
        // Start the browser camera
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(function(stream) {
                videoElement.srcObject = stream;
                
                // Set canvas size based on video dimensions
                videoElement.onloadedmetadata = function() {
                    canvasElement.width = videoElement.videoWidth;
                    canvasElement.height = videoElement.videoHeight;
                    
                    // Start sending frames to server for processing
                    startSendingFrames(videoElement, canvasElement);
                };
            })
            .catch(function(error) {
                console.error('Error accessing browser camera:', error);
                wrapper.innerHTML = `<div class="error-message">
                    <p>Error accessing browser camera: ${error.message}</p>
                    <p>Please check your camera permissions or choose a different video source in settings.</p>
                </div>`;
            });
    }
    
    // Function to send video frames to server for processing
    function startSendingFrames(videoElement, canvasElement) {
        const context = canvasElement.getContext('2d');
        
        // Process frame function
        function processFrame() {
            // Draw the video frame to canvas (for capture)
            const tempCanvas = document.createElement('canvas');
            const tempContext = tempCanvas.getContext('2d');
            tempCanvas.width = videoElement.videoWidth;
            tempCanvas.height = videoElement.videoHeight;
            tempContext.drawImage(videoElement, 0, 0, tempCanvas.width, tempCanvas.height);
            
            // Get the frame data as a jpeg
            const frameData = tempCanvas.toDataURL('image/jpeg', 0.8);
            
            // Send to server for processing
            fetch('/process_browser_frame', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ frame: frameData }),
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Clear the canvas
                    context.clearRect(0, 0, canvasElement.width, canvasElement.height);
                    
                    // Draw polylines first
                    drawPolylines(context, canvasElement.width, canvasElement.height);
                    
                    // Then draw detections
                    if (data.detections) {
                        drawDetections(context, data.detections, tempCanvas.width, tempCanvas.height);
                    }
                }
            })
            .catch(error => console.error('Error sending frame:', error))
            .finally(() => {
                // Process the next frame
                setTimeout(processFrame, 500); // Process a frame every 500ms
            });
        }
        
        // Start processing frames
        processFrame();
    }
    
    // Function to draw polylines on canvas
    function drawPolylines(context, canvasWidth, canvasHeight) {
        if (!polylines || polylines.length === 0) return;
        
        // Set polyline style
        context.strokeStyle = '#FF0000'; // Red color
        context.lineWidth = 2;
        
        polylines.forEach(points => {
            if (points.length < 2) return;
            
            context.beginPath();
            context.moveTo(points[0].x, points[0].y);
            
            for (let i = 1; i < points.length; i++) {
                context.lineTo(points[i].x, points[i].y);
            }
            
            // Close the polyline
            context.lineTo(points[0].x, points[0].y);
            context.stroke();
        });
    }
    
    // Function to draw detections on canvas
    function drawDetections(context, detections, sourceWidth, sourceHeight) {
        detections.forEach(detection => {
            // Scale detection coordinates to canvas size
            const scaleX = context.canvas.width / sourceWidth;
            const scaleY = context.canvas.height / sourceHeight;
            
            const x1 = detection.x1 * scaleX;
            const y1 = detection.y1 * scaleY;
            const x2 = detection.x2 * scaleX;
            const y2 = detection.y2 * scaleY;
            const width = x2 - x1;
            const height = y2 - y1;
            
            // Draw bounding box
            context.strokeStyle = '#00FF00';
            context.lineWidth = 2;
            context.strokeRect(x1, y1, width, height);
            
            // Draw label
            context.fillStyle = 'rgba(0, 0, 0, 0.7)';
            context.fillRect(x1, y1 - 20, 160, 20);
            context.fillStyle = '#00FF00';
            context.font = '14px Arial';
            context.fillText(
                `ID ${detection.id}: ${detection.label} (${detection.confidence.toFixed(2)})`,
                x1 + 5, 
                y1 - 5
            );
        });
    }
    
    // Check if we're using browser camera when the page loads
    checkIfUsingBrowserCamera();
});