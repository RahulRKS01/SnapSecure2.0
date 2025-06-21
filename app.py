from flask import Flask, render_template, Response, jsonify, session, flash, redirect, url_for, request, make_response
import cv2
import numpy as np
import os
# Set the non-interactive backend before importing pyplot
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
# print(f"Using matplotlib backend: {matplotlib.get_backend()}", flush=True)  # Add this for debugging
from datetime import datetime, timedelta
from pymongo import MongoClient
from urllib.parse import quote_plus
from sort import Sort  # Import the SORT tracker
from inference_sdk import InferenceHTTPClient
import json
from flask_bcrypt import Bcrypt
from config import POLYLINES_FILE
import tempfile
import time
import base64  # Add this import for encoding images
from email_utils import init_mail, send_email_alert  # Import email utilities
from config import MAIL_CONFIG  # Import mail configuration
from bson.objectid import ObjectId  # Import ObjectId for MongoDB queries
import threading  # Import threading for monitoring database inactivity
from email_utils import send_email_and_update_report
from profile_logic import get_user_data, update_user_data
import subprocess
from werkzeug.utils import secure_filename
from io import BytesIO
import requests
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO
from datetime import datetime
import json
import matplotlib.pyplot as plt
from reportlab.lib.utils import ImageReader
import traceback
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

UPLOAD_FOLDER = 'uploaded_videos'
# Define allowed video extensions
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize Flask app
app = Flask(__name__)
bcrypt = Bcrypt(app)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Use environment variables for sensitive data
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/PackageDetectionSystem")
SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")
API_URL = os.getenv("API_URL", "https://serverless.roboflow.com")
API_KEY = os.getenv("API_KEY", "default_api_key")
MODEL_ID = os.getenv("MODEL_ID", "default_model_id")

# Initialize MongoDB client
client = MongoClient(MONGO_URI)
db = client["PackageDetectionSystem"]

# Set Flask secret key
app.secret_key = SECRET_KEY

# Set session lifetime
app.permanent_session_lifetime = timedelta(minutes=30)

cv2.setLogLevel(0)

# Initialize the InferenceHTTPClient with your API URL and API key
CLIENT = InferenceHTTPClient(
    api_url=API_URL,
    api_key=API_KEY
)

MODEL_ID = MODEL_ID
POLYLINES_FILE = POLYLINES_FILE

# Initialize SORT tracker
tracker = Sort(max_age=30, min_hits=3, iou_threshold=0.3)

# Connect to MongoDB Atlas
client = MongoClient(MONGO_URI)
db = client["PackageDetectionSystem"]
collection = db["Detection"]

# Global variables for video capture
video_stream = None  # Initialize as None
video_source = "camera"  # Default video source

class ThreadedVideoStream:
    def __init__(self, src=1, width=640, height=480):
        # Use a safer approach to initialize the camera
        self.src = src
        self.width = width
        self.height = height
        self.stream = None
        self.frame = None
        self.grabbed = False
        self.stopped = False
        
    def start(self):
        # Initialize the camera here instead of in __init__
        try:
            self.stream = cv2.VideoCapture(self.src)
            if self.stream.isOpened():
                self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                (self.grabbed, self.frame) = self.stream.read()
                if self.grabbed:
                    # Only start the thread if we successfully grabbed a frame
                    threading.Thread(target=self.update, daemon=True).start()
                    return self
            return None
        except Exception as e:
            print(f"Error starting threaded video stream: {e}")
            return None
        
    def update(self):
        while not self.stopped:
            try:
                (self.grabbed, new_frame) = self.stream.read()
                if self.grabbed and new_frame is not None:
                    self.frame = new_frame
                else:
                    # If we can't grab a frame, sleep a bit to avoid high CPU usage
                    time.sleep(0.01)
            except Exception as e:
                print(f"Error reading frame: {e}")
                time.sleep(0.1)  # Sleep longer on error
            
    def read(self):
        # Return the most recently read frame
        return self.frame if self.frame is not None else None
    
    def isOpened(self):
        # Check if the camera is open
        return self.stream is not None and self.stream.isOpened() and self.grabbed
        
    def set(self, prop, value):
        # Set a property if the stream exists
        if self.stream is not None:
            return self.stream.set(prop, value)
        return False

    def get(self, prop):
        """Get a property from the underlying VideoCapture"""
        if self.stream is not None:
            return self.stream.get(prop)
        return 0  # Return 0 as default if stream is None
        
    def release(self):
        # Stop the thread and release the camera
        self.stopped = True
        if self.stream is not None:
            self.stream.release()

class MjpegStreamReader:
    def __init__(self, url):
        self.url = url
        self.stream = None
        self.bytes_buffer = BytesIO()
        self.frame = None
        self.stopped = False
        self.thread = None
        self.is_valid_stream = False
        self.frame_width = 640  # Default width
        self.frame_height = 480  # Default height
        self.fps = 30  # Default FPS for MJPEG streams
    
    def start(self):
        """Start the MJPEG stream connection"""
        try:
            self.stream = requests.get(self.url, stream=True, timeout=5)
            if self.stream.status_code == 200:
                content_type = self.stream.headers.get('content-type', '')
                
                # Only proceed if this is actually an MJPEG stream
                if 'multipart/x-mixed-replace' in content_type:
                    print(f"Valid MJPEG stream found with content-type: {content_type}")
                    self.is_valid_stream = True
                    # Start the frame reading thread
                    self.stopped = False
                    self.thread = threading.Thread(target=self._update, daemon=True)
                    self.thread.start()
                    return True
                else:
                    print(f"Not a valid MJPEG stream. Content type: {content_type}")
                    return False
            return False
        except Exception as e:
            print(f"MJPEG Connection error: {str(e)}")
            return False
    
    def _update(self):
        """Background thread to continuously read frames"""
        content_type = self.stream.headers.get('content-type', '')
        
        # We already checked this in start(), but double-check here
        if 'multipart/x-mixed-replace' in content_type:
            try:
                boundary = content_type.split('boundary=')[1]
                
                # Process the stream
                self.bytes_buffer = BytesIO()
                capture_image = False
                
                for chunk in self.stream.iter_content(chunk_size=1024):
                    if self.stopped:
                        break
                    
                    if chunk:
                        # Check if this is the start of a new frame
                        if boundary.encode() in chunk:
                            if self.bytes_buffer.tell() > 0:
                                # We've captured a complete frame
                                self.bytes_buffer.seek(0)
                                try:
                                    image_data = np.asarray(bytearray(self.bytes_buffer.read()), dtype=np.uint8)
                                    frame = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
                                    if frame is not None:
                                        self.frame = frame
                                        # Update frame dimensions based on the actual frame
                                        self.frame_width = frame.shape[1]
                                        self.frame_height = frame.shape[0]
                                except Exception as e:
                                    print(f"Error decoding frame: {e}")
                            
                            # Start capturing the new frame
                            self.bytes_buffer = BytesIO()
                            capture_image = True
                        elif capture_image:
                            self.bytes_buffer.write(chunk)
            except Exception as e:
                print(f"Error in MJPEG stream processing: {e}")
    
    def read(self):
        """Read a frame from the MJPEG stream"""
        return self.frame
    
    def isOpened(self):
        """Check if the stream is open and working"""
        return self.stream is not None and self.is_valid_stream and not self.stopped
    
    def release(self):
        """Stop the stream"""
        self.stopped = True
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        self.stream = None
        self.frame = None

    def get(self, prop_id):
        """
        Mimics cv2.VideoCapture's get() method to return stream properties
        """
        if prop_id == cv2.CAP_PROP_FPS:
            return self.fps
        elif prop_id == cv2.CAP_PROP_FRAME_WIDTH:
            # If we have a frame, return its actual width, otherwise return default
            if self.frame is not None:
                return self.frame.shape[1]
            return self.frame_width
        elif prop_id == cv2.CAP_PROP_FRAME_HEIGHT:
            # If we have a frame, return its actual height, otherwise return default
            if self.frame is not None:
                return self.frame.shape[0]
            return self.frame_height
        elif prop_id == cv2.CAP_PROP_POS_FRAMES:
            return 0  # MJPEG streams don't have frame position
        elif prop_id == cv2.CAP_PROP_FRAME_COUNT:
            return -1  # MJPEG streams don't have a frame count (infinite)
        else:
            return 0  # Default return for unsupported properties

# Initialize the video stream during application startup
def initialize_video_stream(user_id=None):
    global video_stream, video_source

    try:
        # If user_id is not provided, check if we're in a request context first
        if user_id is None:
            # Check if we're in a Flask request context before trying to access session
            if not hasattr(request, 'environ'):
                print("Not in a request context - initializing with defaults")
                return
                
            user_id = session.get('user_id')
            if not user_id:
                print("Error: User ID is required to initialize the video stream.")
                return

        print(f"Initializing video stream for user_id: {user_id}")

        # Release the existing video stream if it exists
        if video_stream is not None:
            video_stream.release()
            print("Released existing video stream")
        video_stream = None

        # Fetch the video source and IP camera address from the database
        user = db["User"].find_one({"_id": ObjectId(user_id)})
        if user:
            video_source = user.get("video_source", "camera")
            ip_camera_address = user.get("ip_camera_address", "").strip()
            print(f"Fetched video_source: {video_source}, ip_camera_address: {ip_camera_address}")
        else:
            print("Error: User not found in the database.")
            return

        # Initialize the video stream based on the video source
        if video_source == "stream":
            if not ip_camera_address:
                print("Error: No IP camera address found in the database.")
                return

            print(f"Connecting to IP camera at {ip_camera_address}")
            
            # For RTSP streams, use the optimized connection method
            if ip_camera_address.lower().startswith("rtsp://"):
                video_stream = optimize_rtsp_connection(ip_camera_address)
            else:
                # For other stream types (HTTP, etc.)
                try:
                    # Try the custom MJPEG reader first (for HTTP streams)
                    mjpeg_reader = MjpegStreamReader(ip_camera_address)
                    if (mjpeg_reader.start()):
                        print("Successfully connected using custom MJPEG reader")
                        video_stream = mjpeg_reader
                    else:
                        # If custom reader fails, fall back to OpenCV
                        print("Custom MJPEG reader failed, falling back to OpenCV")
                        video_stream = cv2.VideoCapture(ip_camera_address, cv2.CAP_FFMPEG)
                except Exception as e:
                    print(f"Error with custom MJPEG reader: {e}")
                    # Fall back to OpenCV
                    video_stream = cv2.VideoCapture(ip_camera_address, cv2.CAP_FFMPEG)
            
            # Check if the video stream is opened successfully
            if (hasattr(video_stream, 'isOpened') and not video_stream.isOpened()):
                print("Error: Failed to connect to the IP camera.")
                video_stream = None
        elif video_source == "camera":
            # Keep existing webcam handling code
            camera_index = user.get("camera_index", 0)  # Default to 0 if not set
            print(f"Connecting to camera index {camera_index}")
            video_stream = cv2.VideoCapture(camera_index)
        elif video_source == "upload":
            # Keep existing uploaded video handling code
            uploaded_video_path = user.get("uploaded_video_path", "")
            if os.path.exists(uploaded_video_path):
                print(f"Using uploaded video: {uploaded_video_path}")
                video_stream = cv2.VideoCapture(uploaded_video_path)
            else:
                print("Error: Uploaded video file not found.")
                video_stream = None
        else:
            print(f"Error: Unknown video source '{video_source}'")
            video_stream = None

        # Verify the video stream
        if video_stream is not None and (not hasattr(video_stream, 'isOpened') or video_stream.isOpened()):
            print("Video stream initialized successfully.")
        else:
            print("Error: Video stream is not initialized or cannot be opened.")

    except Exception as e:
        print(f"Error initializing video stream: {e}")
        video_stream = None

# Call the initialization function during application startup
# initialize_video_stream()

# Initialize Flask-Mail
mail = init_mail(app, MAIL_CONFIG)

# Global variable to track the last detection state
last_detection = {"detected": False, "details": None}

# Global variable to track the last insertion time
last_insertion_time = None

# Global variable to track email notification state
email_sent = False


def store_detection_in_db(track_id, label, confidence, timestamp, user_id, image):
    global last_insertion_time

    if not user_id:
        print("User ID not provided. Cannot store detection.")
        return

    # Encode the entire image as a base64 string
    _, buffer = cv2.imencode('.jpg', image)
    encoded_image = base64.b64encode(buffer).decode('utf-8')

    # Prepare the detection data
    detection_data = {
        "detection_id": track_id,
        "type_of_detection": label,
        "confidence": confidence,
        "timestamp": timestamp,
        "user_id": user_id,  # Foreign key to the User collection
        "image": encoded_image,  # Add the image field
        "status": True  # Initially set the status to True (present)
    }

    # Insert or update the detection in MongoDB
    collection.update_one(
        {"detection_id": track_id, "user_id": user_id},  # Match by detection_id and user_id
        {"$set": detection_data},
        upsert=True
    )

    # Update the last insertion time
    last_insertion_time = datetime.now()


def monitor_database_inactivity(user_id):
    """Monitor the database for inactivity and update the status field if no updates occur."""
    global last_insertion_time, email_sent

    # Define the inactivity threshold (e.g., 10 seconds)
    inactivity_threshold = timedelta(seconds=10)

    while True:
        # Check if there has been no insertion for the threshold period
        if last_insertion_time and datetime.now() - last_insertion_time > inactivity_threshold:
            if not email_sent:  # Only send an email if one hasn't been sent already
                # Fetch the latest detection for the user
                latest_detection = collection.find_one(
                    {"user_id": user_id, "status": True},  # Only check detections with status=True
                    sort=[("timestamp", -1)]  # Sort by timestamp in descending order
                )

                if latest_detection:
                    # Update the status to False (taken)
                    collection.update_one(
                        {"_id": latest_detection["_id"]},
                        {"$set": {"status": False}}
                    )

                    # Check if a report already exists for this detection
                    report = db["Report"].find_one({"detection_id": latest_detection["detection_id"]})

                    if not report:
                        # Create a new report if it doesn't exist
                        report_data = {
                            "detection_id": latest_detection["detection_id"],
                            "report_id": f"RPT-{latest_detection['detection_id']}",  # Generate a custom report ID
                            "verification": None,  # Initially set verification to None
                            "timestamp": datetime.now().isoformat()
                        }
                        db["Report"].insert_one(report_data)

                    # Prepare the detection details
                    detection_details = {
                        "type_of_detection": latest_detection.get("type_of_detection", "Unknown"),
                        "confidence": latest_detection.get("confidence", 0.0),
                        "date": latest_detection["timestamp"].split("T")[0],
                        "time": latest_detection["timestamp"].split("T")[1][:5],
                        "image": latest_detection.get("image", None)
                    }

                    # Fetch the user's email
                    user_email = db["User"].find_one({"_id": ObjectId(user_id)}).get("email")
                    if user_email:
                        # Use app.app_context() to send the email
                        with app.app_context():
                            send_email_alert(mail, detection_details, user_email)
                            print("Email sent to:", user_email)

                    # Mark the email as sent
                    email_sent = True
        else:
            # Reset the email_sent flag when new detections occur
            email_sent = False

        # Sleep for a short period before checking again
        time.sleep(1)


def monitor_detections(detection, user_id):
    """Monitor the detection state and trigger an alert if a package is removed."""
    global last_detection

    if detection["type_of_detection"] == "package":
        # If a package is detected, update the state
        last_detection["detected"] = True
        last_detection["details"] = detection
    elif last_detection["detected"]:
        # If the package was detected previously but is now undetected
        last_detection["detected"] = False
        user_email = db["User"].find_one({"_id": ObjectId(user_id)}).get("email")
        if user_email:
            send_email_alert(mail, last_detection["details"], user_email)


def detect_objects(frame):
    _, encoded_image = cv2.imencode('.jpg', frame)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
        temp_file.write(encoded_image)
        temp_image_path = temp_file.name

    try:
        # Perform inference
        result = CLIENT.infer(temp_image_path, model_id=MODEL_ID)
    finally:
        # Ensure the temporary file is deleted
        if (os.path.exists(temp_image_path)):
            os.remove(temp_image_path)

    return result


def load_polylines(filename):
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
            # Flatten the extra level of nesting
            return [np.array([point[0] for point in polyline], np.int32).reshape((-1, 1, 2)) for polyline in data]
    except FileNotFoundError:
        print(f"File {filename} not found. No polylines will be used.")
        return []


def is_point_in_polylines(point, polylines):
    for polyline in polylines:
        if cv2.pointPolygonTest(polyline, point, False) >= 0:
            return True
    return False

# Create a global lock for thread-safe video stream access
video_stream_lock = threading.Lock()

def generate_frames(user_id):
    global last_insertion_time, video_stream, video_stream_lock

    # Add these lines at the beginning to track actual FPS
    fps_counter = 0
    fps_timer = time.time()
    actual_fps = 0  # Initialize with a default value

    # Start the database monitoring thread
    threading.Thread(target=monitor_database_inactivity, args=(user_id,), daemon=True).start()

    # Load polylines from the file
    polylines = load_polylines(POLYLINES_FILE)
    print(f"Loaded polylines: {polylines}")

    frame_count = 0
    start_time = time.time()
    last_saved_time = time.time()  # Track the last time a frame was saved

    # Set a default frame_delay value (30 FPS)
    frame_delay = 1 / 30  # Default to 30 FPS
    
    # Try to get the frame rate from the video stream if available
    if video_stream is not None and video_stream.isOpened():
        video_fps = video_stream.get(cv2.CAP_PROP_FPS)
        if video_fps > 0:
            frame_delay = 1 / video_fps

    # Add a counter to track consecutive failures
    consecutive_failures = 0
    max_failures = 5  # After this many failures, switch to a blank frame mode

    # Set the current thread to a higher priority if possible
    set_thread_priority()

    # Ensure the video stream is initialized
    if video_stream is None or not video_stream.isOpened():
        print("Video stream is not initialized or cannot be opened. Attempting to reinitialize...")
        initialize_video_stream(user_id)
        time.sleep(1)
        
        # Update frame_delay if video stream is now available
        if video_stream is not None and video_stream.isOpened():
            video_fps = video_stream.get(cv2.CAP_PROP_FPS)
            if video_fps > 0:
                frame_delay = 1 / video_fps

    # Add the while loop here to fix the 'continue' error
    while True:
        # If still not available, yield a blank frame and continue
        if video_stream is None or not video_stream.isOpened():
            # Create a blank frame with a message
            blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(blank_frame, "Camera not available", (150, 240), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # Encode and yield the blank frame
            _, buffer = cv2.imencode('.jpg', blank_frame)
            frame = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.5)  # Wait before trying again
            continue  # Now this is properly in a loop

        try:
            # Use the lock for thread safety when accessing the video stream
            with video_stream_lock:
                # Check what type of video stream we're using
                if isinstance(video_stream, MjpegStreamReader):
                    # MjpegStreamReader.read() returns just the frame
                    frame = video_stream.read()
                    ret = frame is not None
                elif isinstance(video_stream, ThreadedVideoStream):
                    # ThreadedVideoStream.read() returns just the frame
                    frame = video_stream.read()
                    ret = frame is not None
                else:
                    # For RTSP/regular VideoCapture, use grab/retrieve pattern
                    # which is more stable for RTSP streams
                    ret = video_stream.grab()
                    if ret:
                        ret, frame = video_stream.retrieve()
                    else:
                        frame = None

            # Process frames outside the lock to avoid holding the lock too long
            if not ret or frame is None:
                consecutive_failures += 1
                print(f"Failed to read frame ({consecutive_failures}/{max_failures})")
                
                if consecutive_failures >= max_failures:
                    # After multiple failures, just display a blank frame with a message
                    blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    cv2.putText(blank_frame, "Camera not available", (150, 240), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                    
                    _, buffer = cv2.imencode('.jpg', blank_frame)
                    frame = buffer.tobytes()
                    
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                    time.sleep(1)  # Wait longer before trying again
                    continue
                
                # Try to reinitialize the video stream
                with video_stream_lock:  # Lock when reinitializing
                    if video_stream is not None:
                        video_stream.release()
                    video_stream = None
                
                initialize_video_stream(user_id)  # Pass the user_id
                time.sleep(0.5)
                continue
            
            # Reset the failure counter on success
            consecutive_failures = 0
            
        except Exception as e:
            print(f"Error reading from video stream: {e}")
            # Create and yield a blank frame when an error occurs
            blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(blank_frame, "Error: " + str(e), (50, 240), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            _, buffer = cv2.imencode('.jpg', blank_frame)
            frame = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.5)  # Wait before trying again
            continue

        frame_count += 1
        skip_factor = max(1, int(5 / max(1, actual_fps)))  # Dynamic skip based on FPS
        if frame_count % skip_factor != 0:
            continue

        # Resize the frame to match the expected dimensions
        frame = cv2.resize(frame, (640, 480))

        # Save a frame every 10 minutes
        current_time = time.time()
        if current_time - last_saved_time >= 600:  # 600 seconds = 10 minutes
            save_frame_locally(frame)
            last_saved_time = current_time

        # Make a copy of the frame for saving to the database
        frame_for_db = frame.copy()

        # Perform object detection
        detections = detect_objects(frame)

        # Prepare detections for SORT
        sort_detections = []
        labels = {}
        for i, detection in enumerate(detections.get("predictions", [])):
            x, y, w, h = detection["x"], detection["y"], detection["width"], detection["height"]
            confidence = detection["confidence"]
            label = detection["class"]

            x1 = x - w / 2
            y1 = y - h / 2
            x2 = x + w / 2
            y2 = y + h / 2

            # Check if the center of the bounding box is inside any polyline
            center_point = (int(x), int(y))
            if not is_point_in_polylines(center_point, polylines):
                continue  # Skip detections outside the polylines

            sort_detections.append([x1, y1, x2, y2, confidence])
            labels[i] = {"label": label, "confidence": confidence}

        if len(sort_detections) > 0:
            tracked_objects = tracker.update(np.array(sort_detections))
        else:
            tracked_objects = []

        # Draw detections on the frame (for display and saving to the database)
        for i, track in enumerate(tracked_objects):
            track_id = int(track[4])
            x1, y1, x2, y2 = map(int, track[:4])
            label = labels.get(i, {}).get("label", "Unknown")
            confidence = labels.get(i, {}).get("confidence", 0.0)

            # Draw bounding box and label on the frame
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"ID {track_id}: {label} ({confidence:.2f})", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Also draw on the frame_for_db to save inference in the database
            cv2.rectangle(frame_for_db, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame_for_db, f"ID {track_id}: {label} ({confidence:.2f})", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            timestamp = datetime.now().isoformat()
            detection_details = {
                "detection_id": track_id,
                "type_of_detection": label,
                "confidence": confidence,
                "timestamp": timestamp,
                "date": timestamp.split("T")[0],
                "time": timestamp.split("T")[1][:5],
                "image": base64.b64encode(cv2.imencode('.jpg', frame_for_db)[1]).decode('utf-8')  # Save frame with inference
            }
            store_detection_in_db(track_id, label, confidence, timestamp, user_id, frame_for_db)

            # Update the last insertion time
            last_insertion_time = datetime.now()

        # Draw the polylines on the frame (for display only)
        for polyline in polylines:
            #print(f"Drawing polyline: {polyline}")
            cv2.polylines(frame, [polyline], isClosed=True, color=(255, 0, 0), thickness=2)

        # Encode the frame as JPEG (with ROI and detections drawn) for display
        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


def save_frame_locally(frame):
    """Save the frame locally as an image file in the images directory."""
    try:
        # Define the file path in the images directory
        file_path = "images/live_frame.jpg"  # Ensure the 'images' directory exists
        cv2.imwrite(file_path, frame)
        print(f"Saved live frame to {file_path} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        print(f"Error saving live frame: {e}")


detection_thread = None
detection_running = False  # Flag to control the detection process

def start_detection(user_id):
    global detection_thread, detection_running

    if detection_running:
        print("Detection is already running.")
        return

    detection_running = True

    def detection_task():
        global detection_running  # Explicitly declare detection_running as global
        try:
            for _ in generate_frames(user_id):
                if not detection_running:
                    break
        except Exception as e:
            print(f"Error in detection thread: {e}")
        finally:
            detection_running = False

    detection_thread = threading.Thread(target=detection_task, daemon=True)
    detection_thread.start()
    print("Detection thread started.")

def stop_detection():
    global detection_running
    detection_running = False
    print("Detection thread stopped.")

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Find user in MongoDB
        user = db["User"].find_one({"email": email})
        if user:
            if bcrypt.check_password_hash(user['password'], password):
                # Combine first_name and last_name for display purposes
                session['user_id'] = str(user['_id'])
                session['user_name'] = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
                session.permanent = True  # Mark session as permanent
                flash("Login successful!", "success")

                # Start the database inactivity monitor thread
                threading.Thread(target=monitor_database_inactivity, args=(session['user_id'],), daemon=True).start()
                
                if 'user_id' in session:
                    start_detection(session['user_id'])

                return redirect(url_for('dashboard'))
            else:
                flash("Incorrect password. Please try again.", "error")
        else:
            flash("User not found. Please sign up.", "error")

        return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Check if passwords match
        if password != confirm_password:
            flash("Passwords do not match. Please try again.", "error")
            return redirect(url_for('signup'))

        # Check if the email or username already exists
        existing_user = db["User"].find_one({"$or": [{"email": email}, {"username": username}]})
        if existing_user:
            if existing_user.get("email") == email:
                flash("Email already registered. Please log in.", "error")
            elif existing_user.get("username") == username:
                flash("Username already taken. Please choose another.", "error")
            return redirect(url_for('signup'))

        # Hash the password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Insert user into MongoDB
        user_data = {
            "first_name": first_name,
            "last_name": last_name,
            "username": username,
            "email": email,
            "password": hashed_password,
            "created_at": datetime.now()
        }
        db["User"].insert_one(user_data)

        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("Please log in to access the dashboard.", "error")
        return redirect(url_for('login'))

    try:
        # Fetch all detections with status = False and unverified reports
        alert_detections = list(db["Detection"].find(
            {"user_id": session['user_id'], "status": False}
        ).sort("timestamp", -1))

        # Add report details for each detection
        for detection in alert_detections:
            report = db["Report"].find_one(
                {"detection_id": detection["detection_id"], "verification": None}
            )
            if report:
                detection["report_id"] = report["report_id"]
                detection["date"] = detection["timestamp"].split("T")[0]
                detection["time"] = detection["timestamp"].split("T")[1][:5]

        # Filter out detections without unverified reports
        alert_detections = [d for d in alert_detections if "report_id" in d]

        # Fetch detection history (latest 5 detections)
        history = db["Detection"].find({"user_id": session['user_id']}).sort("timestamp", -1).limit(5)
        history_list = [
            {
                "detection_id": entry["detection_id"],
                "date": entry["timestamp"].split("T")[0],
                "time": entry["timestamp"].split("T")[1][:5],
                "type_of_detection": entry["type_of_detection"],
                "confidence": entry["confidence"]
            }
            for entry in history
        ]


    except Exception as e:
        print(f"Error fetching data: {e}")
        alert_detections = []
        history_list = []

    return render_template(
        'dashboard.html',
        detections=alert_detections,  # Pass all detections to the template
        history=history_list,       # For the history section
        now=datetime.now() # Pass the current time to the template
    )


@app.route('/video_feed')
def video_feed():
    if 'user_id' not in session:
        flash("Please log in to access the video feed.", "error")
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    if not user_id:
        flash("Invalid session. Please log in again.", "error")
        return redirect(url_for('login'))

    # Initialize the video stream for the current user
    initialize_video_stream(user_id)

    return Response(generate_frames(user_id), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/history')
def history():
    if 'user_id' not in session:
        flash("Please log in to access the history.", "error")
        return redirect(url_for('login'))

    # Fetch detection history for the logged-in user
    detections = collection.find(
        {"user_id": session['user_id']},  # Filter by user_id
        {"timestamp": 1, "_id": 0}
    ).sort("timestamp", -1).limit(10)
    timestamps = [detection["timestamp"] for detection in detections]
    return jsonify(timestamps)


@app.route('/archive')
def archive():
    if 'user_id' not in session:
        flash("Please log in to access the archive.", "error")
        return redirect(url_for('login'))

    user_id = session['user_id']
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')
    detection_type = request.args.get('detectionType')

    # Build the query
    query = {"user_id": user_id}
    if start_date:
        query["timestamp"] = {"$gte": start_date}
    if end_date:
        end_date_with_time = (datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        if "timestamp" in query:
            query["timestamp"]["$lt"] = end_date_with_time
        else:
            query["timestamp"] = {"$lt": end_date_with_time}
    if detection_type and detection_type != "all":
        query["type_of_detection"] = detection_type

    # Fetch filtered data from MongoDB
    detections = collection.find(query)
    detection_list = []

    for detection in detections:
        image_url = f"data:image/jpeg;base64,{detection['image']}" if detection.get("image") else "static/images/default-img.jpg"
        detection_list.append({
            "detection_id": detection.get("detection_id", "Unknown"),
            "confidence": detection.get("confidence", "N/A"),
            "date": detection.get("timestamp").split("T")[0] if detection.get("timestamp") else "Unknown",
            "time": detection.get("timestamp").split("T")[1][:5] if detection.get("timestamp") else "Unknown",
            "type_of_detection": detection.get("type_of_detection", "Unknown"),
            "image": image_url
        })

    # Render the filtered results
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  # Check if it's an AJAX request
        return render_template('partials/archive_content.html', detections=detection_list)
    else:
        return render_template('archive.html', detections=detection_list)


@app.route('/reports')
def reports():
    if 'user_id' not in session:
        flash("Please log in to access the reports.", "error")
        return redirect(url_for('login'))

    try:
        # Fetch detection data for the logged-in user
        detections = db["Detection"].find({"user_id": session['user_id']})
        detection_list = []
        total_detections = 0
        total_thefts = 0
        total_safe = 0
        high_confidence = 0
        medium_confidence = 0
        low_confidence = 0
        graph_data = {
            "labels": [],
            "datasets": {
                "deliveries": [],
                "thefts": [],
                "highConfidence": [],
                "mediumConfidence": [],
                "lowConfidence": [],
                "noTheftRecords": []
            }
        }

        for detection in detections:
            # Fetch the corresponding report for verification status
            report = db["Report"].find_one({"detection_id": detection["detection_id"]})
            verification = report.get("verification") if report else None


            confidence = detection.get("confidence", 0)
            if confidence >= 0.75:
                confidence_level = "High"
                high_confidence += 1
            elif confidence >= 0.5:
                confidence_level = "Medium"
                medium_confidence += 1
            else:
                confidence_level = "Low"
                low_confidence += 1

            # Prepare detection data
            detection_list.append({
                "detection_id": detection["detection_id"],
                "date": detection["timestamp"].split("T")[0],
                "time": detection["timestamp"].split("T")[1][:5],
                "confidence": confidence,
                "confidence_level": confidence_level,
                "type_of_detection": detection["type_of_detection"],
                "status": detection.get("status"),  # Keep it as a boolean
                "verification": verification  # Add verification status
            })

            # Update statistics
            total_detections += 1
            if verification is False:  # Correct comparison for boolean
                total_thefts += 1
            else: # Increment total_safe if verification is True or None
                total_safe += 1

            # Update graph data
            date = detection["timestamp"].split("T")[0]
            if date not in graph_data["labels"]:
                graph_data["labels"].append(date)
                graph_data["datasets"]["deliveries"].append(0)
                graph_data["datasets"]["thefts"].append(0)
                graph_data["datasets"]["highConfidence"].append(0)
                graph_data["datasets"]["mediumConfidence"].append(0)
                graph_data["datasets"]["lowConfidence"].append(0)
                graph_data["datasets"]["noTheftRecords"].append(0)

            index = graph_data["labels"].index(date)
            graph_data["datasets"]["deliveries"][index] += 1
            if verification is False:
                graph_data["datasets"]["thefts"][index] += 1
            else:  # Increment no-theft records if verification is True or None
                graph_data["datasets"]["noTheftRecords"][index] += 1

            if confidence >= 0.75:
                graph_data["datasets"]["highConfidence"][index] += 1
            elif confidence >= 0.5:
                graph_data["datasets"]["mediumConfidence"][index] += 1
            else:
                graph_data["datasets"]["lowConfidence"][index] += 1

    except Exception as e:
        print(f"Error fetching reports: {e}")
        detection_list = []
        total_detections = 0
        total_thefts = 0
        total_safe = 0
        high_confidence = 0
        medium_confidence = 0
        low_confidence = 0
        graph_data = {"labels": [], "datasets": {}}

    return render_template(
        'reports.html',
        detection_data=detection_list,
        graph_data=graph_data,
        total_detections=total_detections,
        total_thefts=total_thefts,
        total_safe=total_safe,
        high_confidence=high_confidence,
        medium_confidence=medium_confidence,
        low_confidence=low_confidence
    )


@app.route('/profile', methods=['GET'])
def profile():
    user = get_user_data(db)
    if isinstance(user, dict):  # If user data is returned
        return render_template('profile.html', user=user)
    return user  # Redirect if session is invalid

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if request.method == 'POST':
        return update_user_data(db, request.form)
    user = get_user_data(db)
    if isinstance(user, dict):  # If user data is returned
        return render_template('edit_profile.html', user=user)
    return user  # Redirect if session is invalid



@app.route('/logout')
def logout():
    # Clear the session and redirect to the login page
    stop_detection()  # Stop the detection thread if running
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))


@app.route('/test_email')
def test_email():
    try:
        test_details = {
            "type_of_detection": "package",
            "confidence": 0.95,
            "date": "2025-04-09",
            "time": "14:30",
            "image": None  # Replace with a base64-encoded image if needed
        }
        recipient_email = "82102@siswa.unimas.my"  # Replace with a valid email
        send_email_alert(mail, test_details, recipient_email)
        return "Test email sent successfully!"
    except Exception as e:
        return f"Failed to send test email: {e}"



@app.route('/trigger_email', methods=['POST'])
def trigger_email():
    detection_id = request.json.get('detection_id')
    user_email = request.json.get('user_email')
    detection_details = request.json.get('detection_details')

    send_email_and_update_report(mail, db, detection_id, user_email, detection_details)
    return jsonify({"success": True, "message": "Email sent and report updated."})


@app.route('/update_verification', methods=['POST'])
def update_verification():
    data = request.get_json()
    report_id = data.get('report_id')
    verification = data.get('verification')  # Expecting a boolean: True (safe) or False (theft)

    print(f"Received data: report_id={report_id}, verification={verification}")

    try:
        # Ensure verification is a boolean
        if not isinstance(verification, bool):
            return jsonify({"success": False, "message": "Invalid verification value. Must be a boolean (True or False)."}), 400

        # Update the verification field in the Report collection
        result = db["Report"].update_one(
            {"report_id": report_id},  # Query the Report collection
            {"$set": {"verification": verification, "verified_at": datetime.now().isoformat()}}
        )

        if result.matched_count == 0:
            return jsonify({"success": False, "message": "Report not found."}), 404

        return jsonify({"success": True, "message": "Verification updated successfully."}), 200
    except Exception as e:
        print(f"Error updating verification: {e}")
        return jsonify({"success": False, "message": "Failed to update verification."}), 500


@app.route('/settings')
def settings():
    if 'user_id' not in session:
        flash("Please log in to access the settings.", "error")
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    video_source = "camera"  # Default to "camera" if not set
    ip_camera_address = ""  # Default to empty if not set

    if user_id:
        user = db["User"].find_one({"_id": ObjectId(user_id)})
        if user:
            video_source = user.get("video_source", "camera")
            ip_camera_address = user.get("ip_camera_address", "")

    return render_template('settings.html', video_source=video_source, ip_camera_address=ip_camera_address)


@app.route('/update_video_source', methods=['POST'])
def update_video_source():
    global video_stream, video_source

    try:
        # Get the new video source from the request
        data = request.get_json()
        new_source = data.get('videoSource')

        print(f"Received video source: {new_source}")  # Debug log

        if new_source not in ["camera", "upload", "stream"]:
            return jsonify({"success": False, "message": "Invalid video source"}), 400

        # Release the current video stream if it exists
        if video_stream is not None:
            video_stream.release()
            video_stream = None
            print("Releasing existing video stream")

        # Update the global video source
        video_source = new_source
        print(f"Updated global video_source to: {video_source}")

        # Get the user ID from the session
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"success": False, "message": "User not logged in"}), 401

        print(f"Updating video source for user_id: {user_id}")

        # Update the video source in the database
        result = db["User"].update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"video_source": video_source}}
        )
        print(f"Database update result: {result.modified_count}")

        # Reinitialize the video stream for the new source
        initialize_video_stream(user_id)

        if video_stream is not None and video_stream.isOpened():
            return jsonify({"success": True, "message": "Video source updated successfully"}), 200
        else:
            return jsonify({"success": False, "message": "Failed to initialize video stream"}), 500

    except Exception as e:
        print(f"Error updating video source: {e}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@app.route('/upload_video', methods=['POST'])
def upload_video():
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Please log in to upload a video."}), 401

    if 'videoFile' not in request.files:
        return jsonify({"success": False, "message": "No video file selected."}), 400

    file = request.files['videoFile']
    if file.filename == '':
        return jsonify({"success": False, "message": "No video file selected."}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Save the file path in the database for the logged-in user
        user_id = session.get('user_id')
        db["User"].update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"video_source": "upload", "uploaded_video_path": file_path}}
        )

        return jsonify({"success": True, "message": "Video uploaded successfully."}), 200

    return jsonify({"success": False, "message": "Invalid file type. Please upload a valid video file."}), 400


# @app.route('/launch_roi_tool', methods=['POST'])
# def launch_roi_tool():
#     try:
#         # Use sys.executable to get the current Python interpreter path
#         import sys
#         python_executable = sys.executable
        
#         # Launch DrawingPolylines.py with the same Python interpreter
#         # Launch DrawingPolylines.py with Xvfb
#         # subprocess.Popen(
#         #     ["xvfb-run", "-a", python_executable, "DrawingPolylines.py"],
#         #     cwd=os.path.dirname(__file__)
#         # )
#         # Launch DrawingPolylines.py with the same Python interpreter
#         subprocess.Popen([python_executable, 'DrawingPolylines.py'], 
#                          cwd=os.path.dirname(__file__))
        
        
#         return jsonify({"success": True, "message": "ROI tool launched successfully"}), 200
#     except Exception as e:
#         print(f"Error launching ROI tool: {e}")
#         return jsonify({"success": False, "message": "Failed to launch ROI tool"}), 500

@app.route('/launch_roi_tool', methods=['POST'])
def launch_roi_tool():
    try:
        # Get the current user ID from the session
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({"success": False, "message": "User not logged in"}), 401
        
        # Use subprocess to launch the DrawingPolylines.py script
        import subprocess
        import sys
        
        # Get the current Python executable path
        python_path = sys.executable
        
        # Launch the script with the user_id parameter
        subprocess.Popen([python_path, 'DrawingPolylines.py', '--user_id', str(user_id)])
        
        return jsonify({"success": True, "message": "ROI Editor launched successfully"}), 200
    except Exception as e:
        print(f"Error launching ROI Editor: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/update_ip_camera', methods=['POST'])
def update_ip_camera():
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "User not logged in."}), 401

    user_id = session.get('user_id')
    data = request.get_json()
    ip_camera_address = data.get('ipCameraAddress', '').strip()

    if not ip_camera_address:
        return jsonify({"success": False, "message": "IP camera address is required."}), 400

    try:
        # Update the user's IP camera address in the database
        db["User"].update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"ip_camera_address": ip_camera_address}}
        )
        return jsonify({"success": True, "message": "IP camera address updated successfully."}), 200
    except Exception as e:
        print(f"Error updating IP camera address: {e}")
        return jsonify({"success": False, "message": "Failed to update IP camera address."}), 500


@app.route('/get_available_cameras', methods=['GET'])
def get_available_cameras():
    try:
        available_cameras = []
        for i in range(10):  # Check the first 10 camera indices
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available_cameras.append(f"Camera {i}")
                cap.release()
        return jsonify({"success": True, "cameras": available_cameras}), 200
    except Exception as e:
        print(f"Error detecting cameras: {e}")
        return jsonify({"success": False, "message": "Failed to detect cameras."}), 500


@app.route('/update_camera_index', methods=['POST'])
def update_camera_index():
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "User not logged in."}), 401

    user_id = session.get('user_id')
    data = request.get_json()
    camera_index = data.get('cameraIndex')

    if camera_index is None:
        return jsonify({"success": False, "message": "Camera index is required."}), 400

    try:
        # Update the user's selected camera index in the database
        db["User"].update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"camera_index": camera_index}}
        )
        return jsonify({"success": True, "message": "Camera index updated successfully."}), 200
    except Exception as e:
        print(f"Error updating camera index: {e}")
        return jsonify({"success": False, "message": "Failed to update camera index."}), 500


def optimize_rtsp_connection(url):
    """Configure and optimize RTSP stream connection"""
    # Disable multi-threading in FFmpeg to avoid the assertion error
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "threads;1|rtsp_transport;tcp|max_delay;500000|fflags;discardcorrupt|flags;low_delay"
    
    # Set shorter timeouts
    os.environ["OPENCV_FFMPEG_READ_TIMEOUT"] = "5"
    
    # Create a list of URLs to try (original + alternatives)
    urls_to_try = [url]
    
    # Add TCP transport if not already specified
    if "rtsp://" in url and "?transport=" not in url:
        urls_to_try.append(f"{url}?transport=tcp")
    
    # Add UDP transport as a fallback
    if "rtsp://" in url:
        base_url = url.split("?")[0]
        urls_to_try.append(f"{base_url}?transport=udp")
    
    # Try each URL
    for test_url in urls_to_try:
        try:
            print(f"Trying RTSP connection with: {test_url}")
            cap = cv2.VideoCapture(test_url, cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)  # Reduce buffer size
            
            # Test if we can actually read a frame
            success = cap.grab()
            if success:
                print(f"Successfully connected to: {test_url}")
                return cap
            else:
                print(f"Could grab from {test_url} but no frames available")
                cap.release()
        except Exception as e:
            print(f"Error testing {test_url}: {e}")
    
    # If all attempts failed, try one more time with the original URL
    try:
        print("Final attempt with original URL and minimal settings")
        return cv2.VideoCapture(url, cv2.CAP_FFMPEG)
    except:
        print("All connection attempts failed")
        return None

def set_thread_priority():
    """Set thread priority in a platform-independent way"""
    try:
        import os
        if hasattr(os, "sched_setaffinity") and os.name == 'posix':
            # On Linux systems
            os.sched_setaffinity(0, {0, 1})  # Use CPU cores 0 and 1
        elif os.name == 'nt':  # Windows
            try:
                # Try to import Windows-specific modules
                import win32api, win32process, win32con
                pid = win32api.GetCurrentProcessId()
                handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, True, pid)
                win32process.SetPriorityClass(handle, win32process.HIGH_PRIORITY_CLASS)
            except ImportError:
                print("win32api not available, skipping priority adjustment on Windows")
        else:
            # Other platforms
            print(f"Thread priority adjustment not implemented for {os.name}")
    except Exception as e:
        print(f"Could not adjust thread priority: {e}")

#just added 7.5.2025
@app.route('/delete_detection/<detection_id>', methods=['DELETE'])
def delete_detection(detection_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please log in to delete detections'}), 401
    
    user_id = session['user_id']
    print(f"Attempting to delete: detection_id={detection_id}, user_id={user_id}")
    
    try:
        # Try to convert detection_id to different types for matching
        detection_id_values = [detection_id]  # Original string format
        try:
            # Add integer format
            detection_id_values.append(int(detection_id))
        except ValueError:
            pass

        # First, find the detection document to verify ownership
        detection = None
        for id_value in detection_id_values:
            detection = db["Detection"].find_one({"detection_id": id_value, "user_id": user_id})
            if detection:
                break
        
        if not detection:
            return jsonify({'success': False, 'message': 'Detection not found or you do not have permission to delete it'}), 404
        
        # Now that we found the detection, get the actual detection_id value from the database
        actual_detection_id = detection["detection_id"]
        
        # Delete the detection document
        result = db["Detection"].delete_one({"detection_id": actual_detection_id})
        
        # Also delete any related Report documents
        report_result = db["Report"].delete_one({"detection_id": actual_detection_id})
        
        print(f"Deleted detection: {result.deleted_count}, Deleted report: {report_result.deleted_count}")
        
        return jsonify({
            'success': True, 
            'message': 'Detection and related report deleted successfully'
        })
        
    except Exception as e:
        print(f"Error deleting detection: {e}")
        return jsonify({'success': False, 'message': 'An error occurred while deleting the detection'}), 500

# just added 13/5/2025
@app.route('/web_roi_editor')
def web_roi_editor():
    if 'user_id' not in session:
        flash("Please log in to access the ROI editor.", "error")
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    
    # Get a frame from the user's video source
    frame_base64 = capture_frame_for_roi_editor(user_id)
    
    return render_template('web_roi_editor.html', 
                          frame_image=frame_base64,
                          polylines_file=POLYLINES_FILE)

def capture_frame_for_roi_editor(user_id):
    """Capture a frame from the user's video source for the ROI editor"""
    try:
        # Initialize video source
        initialize_video_stream(user_id)
        
        if video_stream and video_stream.isOpened():
            # Get a frame
            if isinstance(video_stream, MjpegStreamReader) or isinstance(video_stream, ThreadedVideoStream):
                frame = video_stream.read()
            else:
                ret, frame = video_stream.read()
                if not ret:
                    return None
            
            # Resize and encode to base64
            frame = cv2.resize(frame, (640, 480))
            _, buffer = cv2.imencode('.jpg', frame)
            return base64.b64encode(buffer).decode('utf-8')
    except Exception as e:
        print(f"Error capturing frame for ROI editor: {e}")
    
    return None

@app.route('/save_roi_polylines', methods=['POST'])
def save_roi_polylines():
    """Save ROI polylines sent from web interface"""
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
        
    try:
        polylines_data = request.json.get('polylines', [])
        
        with open(POLYLINES_FILE, 'w') as f:
            json.dump(polylines_data, f)
            
        return jsonify({"success": True, "message": "ROI polylines saved successfully"})
    except Exception as e:
        print(f"Error saving ROI polylines: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/get_polylines')
def get_polylines():
    """Get existing ROI polylines"""
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    try:
        if os.path.exists(POLYLINES_FILE):
            with open(POLYLINES_FILE, 'r') as f:
                data = json.load(f)
                return jsonify({"success": True, "polylines": data})
        else:
            # Return empty array if file doesn't exist
            return jsonify({"success": True, "polylines": []})
    except Exception as e:
        print(f"Error loading polylines: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/generate_pdf_report')
def generate_pdf_report():
    if 'user_id' not in session:
        flash("Please log in to generate reports.", "error")
        return redirect(url_for('login'))

    try:
        # Get date range parameters
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        
        # Title suffix based on date range
        date_range_title = ""

        # Create a file-like buffer to receive PDF data
        buffer = BytesIO()
        
        # Create the PDF document using ReportLab
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        subtitle_style = styles['Heading2']
        normal_style = styles['Normal']
        
        # Add custom style for centered text
        centered_style = ParagraphStyle(name='Centered', parent=styles['Heading1'], alignment=1)
        
        # Build MongoDB query for date filtering
        query = {"user_id": session['user_id']}
        
        if start_date and end_date:
            # Format dates for MongoDB query (ISO format)
            start_date_iso = f"{start_date}T00:00:00"
            end_date_iso = f"{end_date}T23:59:59"
            
            query["timestamp"] = {
                "$gte": start_date_iso,
                "$lte": end_date_iso
            }
            
            date_range_title = f" ({start_date} to {end_date})"

        # Add the title
        elements.append(Paragraph("SnapSecure Detection Report", centered_style))
        elements.append(Spacer(1, 0.25*inch))
        
        # Add date
        date_text = f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        elements.append(Paragraph(date_text, styles["Normal"]))
        elements.append(Spacer(1, 0.25*inch))
        
        # Get statistics data from MongoDB
        # Fetch detection data for the logged-in user
        detections = list(db["Detection"].find(query))  # Use the query variable that includes date filters
        
        # Calculate statistics similar to the reports route
        total_detections = 0
        total_thefts = 0
        total_safe = 0
        high_confidence = 0
        medium_confidence = 0
        low_confidence = 0
        detection_list = []
        
        for detection in detections:
            # Fetch the corresponding report for verification status
            report = db["Report"].find_one({"detection_id": detection["detection_id"]})
            verification = report.get("verification") if report else None
            
            # Calculate confidence level
            confidence = detection.get("confidence", 0)
            if confidence >= 0.75:
                confidence_level = "High"
                high_confidence += 1
            elif confidence >= 0.5:
                confidence_level = "Medium"
                medium_confidence += 1
            else:
                confidence_level = "Low"
                low_confidence += 1
            
            # Prepare detection data
            detection_list.append({
                "detection_id": detection["detection_id"],
                "date": detection["timestamp"].split("T")[0],
                "time": detection["timestamp"].split("T")[1][:5],
                "confidence": confidence,
                "confidence_level": confidence_level,
                "type_of_detection": detection["type_of_detection"],
                "status": detection.get("status"),
                "verification": verification
            })
            
            # Update statistics
            total_detections += 1
            if verification is False:
                total_thefts += 1
            else:
                total_safe += 1
                
         # Update filename to include date range if specified
        filename_suffix = ""
        if start_date and end_date:
            filename_suffix = f"_{start_date}_to_{end_date}"
        
        # Add statistics section
        elements.append(Paragraph("Detection Statistics", subtitle_style))
        elements.append(Spacer(1, 0.1*inch))
        
        # Create statistics table
        stats_data = [
            ["Statistic", "Value"],
            ["Total Records", str(total_detections)],
            ["Records with Package Theft", str(total_thefts)],
            ["Records with No Package Theft", str(total_safe)],
            ["High Confidence Records", str(high_confidence)],
            ["Medium Confidence Records", str(medium_confidence)],
            ["Low Confidence Records", str(low_confidence)]
        ]
        
        stats_table = Table(stats_data, colWidths=[3*inch, 1.5*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (1, 0), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 1), (0, -1), colors.lightgrey),
        ]))
        
        elements.append(stats_table)
        elements.append(Spacer(1, 0.25*inch))
        
        # Add detection records section
        elements.append(Paragraph("Detection Records", subtitle_style))
        elements.append(Spacer(1, 0.1*inch))
        
        # Create detection records table (limit to 20 most recent records for space)
        detection_list = sorted(detection_list, key=lambda x: f"{x['date']} {x['time']}", reverse=True)[:20]
        
        table_data = [["ID", "Date", "Time", "Type", "Confidence", "Verification"]]
        for detection in detection_list:
            # Format verification status for display
            if detection["verification"] is None:
                verification_status = "Unverified"
            elif detection["verification"] is False:
                verification_status = "Theft"
            else:
                verification_status = "Safe"
                
            table_data.append([
                detection["detection_id"],
                detection["date"],
                detection["time"],
                detection["type_of_detection"],
                detection["confidence_level"],
                verification_status
            ])
        
        detection_table = Table(table_data, colWidths=[0.8*inch, 0.8*inch, 0.7*inch, 1.0*inch, 0.9*inch, 0.9*inch])
        detection_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(detection_table)
        
        # Add a note about confidence levels
        elements.append(Spacer(1, 0.25*inch))
        elements.append(Paragraph("*Confidence Level Legend:", styles["Italic"]))
        elements.append(Paragraph("High: Over 75% confidence", styles["Italic"]))
        elements.append(Paragraph("Medium: 50-75% confidence", styles["Italic"]))
        elements.append(Paragraph("Low: Below 50% confidence", styles["Italic"]))
        
        # Generate a chart for the PDF
        # plt.figure(figsize=(7, 3))
        # confidence_levels = ['High', 'Medium', 'Low']
        # values = [high_confidence, medium_confidence, low_confidence]
        # chart_colors = ['#4ADE80', '#FACC15', '#F87171']  # Green, Yellow, Red - RENAMED from 'colors' to 'chart_colors'

        # plt.bar(confidence_levels, values, color=chart_colors)
        # plt.title('Detection Confidence Levels')
        # plt.ylabel('Number of Detections')
        # plt.tight_layout()

        # # Save the chart to a BytesIO object
        # chart_buffer = BytesIO()
        # plt.savefig(chart_buffer, format='png')
        # chart_buffer.seek(0)
        # plt.close()
        
        # Generate chart using the thread-safe function
        chart_buffer = create_chart_image(high_confidence, medium_confidence, low_confidence)
        
        if chart_buffer:
            # Add the chart to the PDF
            elements.append(Paragraph("Detection Confidence Chart", subtitle_style))
            elements.append(Spacer(1, 0.1*inch))
            img = Image(chart_buffer, width=6*inch, height=3*inch)
            elements.append(img)
            elements.append(Spacer(1, 0.25*inch))
        
        # Add footer
        elements.append(Spacer(1, 0.5*inch))
        elements.append(Paragraph("© 2024 SnapSecure.inc - Generated from your SnapSecure account", styles["Italic"]))
        
        # Build the PDF document
        doc.build(elements)
        
        # FileResponse sets the Content-Disposition header
        buffer.seek(0)
        
        response = make_response(buffer.getvalue())
        response.mimetype = 'application/pdf'
        # Only change the filename to include date range:
        response.headers['Content-Disposition'] = 'attachment; filename=SnapSecure_Report' + filename_suffix + '_' + datetime.now().strftime('%Y%m%d_%H%M') + '.pdf'
        
        return response
        
    # Change this in your generate_pdf_report function:
    except Exception as e:
        print(f"Error generating PDF: {e}", flush=True)
        traceback.print_exc()  # Add this import at the top: import traceback
        flash(f"Error generating PDF: {str(e)}", "error")
        return redirect(url_for('reports'))

def create_chart_image(high_confidence, medium_confidence, low_confidence):
    """
    Create a chart image in a thread-safe way and return the image data
    """
    try:
        # Create a figure with the Agg backend
        import matplotlib
        matplotlib.use('Agg')  # Set backend again to be safe
        import matplotlib.pyplot as plt
        
        # Create a new figure with explicit non-interactive backend
        plt.ioff()  # Turn off interactive mode
        fig = plt.figure(figsize=(7, 3))
        
        # Generate chart
        confidence_levels = ['High', 'Medium', 'Low']
        values = [high_confidence, medium_confidence, low_confidence]
        chart_colors = ['#4ADE80', '#FACC15', '#F87171']  # Green, Yellow, Red
        
        plt.bar(confidence_levels, values, color=chart_colors)
        plt.title('Detection Confidence Levels')
        plt.ylabel('Number of Detections')
        plt.tight_layout()
        
        # Save to BytesIO
        from io import BytesIO
        chart_buffer = BytesIO()
        fig.savefig(chart_buffer, format='png')
        chart_buffer.seek(0)
        
        # Explicitly close the figure to free up resources
        plt.close(fig)
        plt.close('all')  # Close any other figures that might be open
        
        return chart_buffer
    except Exception as e:
        print(f"Error creating chart: {e}")
        return None

if __name__ == "__main__":
    app.run(debug=True)
    # app.run(host='0.0.0.0', port=5000)