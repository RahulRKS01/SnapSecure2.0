import cv2
import numpy as np
import json
import os
import argparse
import sys
from pymongo import MongoClient
from bson.objectid import ObjectId

# Import configurations
from config import MONGO_URI, POLYLINES_FILE

# Global variables
current_polyline = []
polylines = []
resized_width = 640  # Resized video width (same as in app.py)
resized_height = 480  # Resized video height (same as in app.py)

# Function to save polylines to a JSON file
def save_polylines(filename):
    # Save polylines directly in the resized resolution
    scaled_polylines = [pts.tolist() for pts in polylines]
    with open(filename, 'w') as f:
        json.dump(scaled_polylines, f)

# Function to load polylines from a JSON file
def load_polylines(filename):
    global polylines
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
            # Load polylines directly in the resized resolution
            polylines = [np.array(pts, np.int32) for pts in data]
    except FileNotFoundError:
        print(f"File {filename} not found. Starting with an empty set of polylines.")
        polylines = []

# Function to get user's video source from MongoDB
def get_video_source(user_id):
    try:
        # Connect to MongoDB using the URI from config
        client = MongoClient(MONGO_URI)
        db = client["PackageDetectionSystem"]
        
        # Find the user document
        user = db["User"].find_one({"_id": ObjectId(user_id)})
        
        if not user:
            print(f"User with ID {user_id} not found")
            return None
            
        # Get the video source configuration
        video_source = user.get("video_source", "camera")
        
        if video_source == "camera":
            camera_index = user.get("camera_index", 0)
            return camera_index
        elif video_source == "stream":
            ip_address = user.get("ip_camera_address", "")
            if ip_address:
                return ip_address
        elif video_source == "upload":
            video_path = user.get("uploaded_video_path", "")
            if os.path.exists(video_path):
                return video_path
            
        # If we couldn't determine a valid source, return None
        return None
    except Exception as e:
        print(f"Error getting video source: {e}")
        return None

# Mouse callback function to draw points and handle deletion
def draw_polyline(event, x, y, flags, param):
    global current_polyline, polylines

    if event == cv2.EVENT_LBUTTONDOWN:  # Left mouse button click
        current_polyline.append([x, y])
    
    elif event == cv2.EVENT_RBUTTONDOWN:  # Right mouse button click
        if current_polyline:  # Complete the current polyline on right click
            polylines.append(np.array(current_polyline, np.int32).reshape((-1, 1, 2)))
            current_polyline = []  # Reset current polyline
    
    elif event == cv2.EVENT_MBUTTONDOWN:  # Middle mouse button click (delete mode)
        # Check if any polyline is close to the clicked point (within 10 pixels)
        for i in range(len(polylines)):
            dist = np.sqrt((polylines[i][:, 0, 0] - x) ** 2 + (polylines[i][:, 0, 1] - y) ** 2)
            if np.any(dist < 10):
                polylines.pop(i)
                break

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Draw ROI polylines on video frame")
    parser.add_argument("--user_id", help="User ID to get video source from database")
    args = parser.parse_args()
    
    # Load polylines from file (if exists)
    load_polylines(POLYLINES_FILE)
    
    # Default frame path for fallback
    live_frame_path = os.path.join(os.getcwd(), "static", "images", "live_frame.jpg")
    frame = None
    
    # If user_id is provided, try to get video source from MongoDB
    if args.user_id:
        video_source = get_video_source(args.user_id)
        if video_source is not None:
            try:
                # Try to get a frame from the video source
                cap = cv2.VideoCapture(video_source)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret:
                        print(f"Successfully captured frame from user's video source")
                    else:
                        print(f"Failed to read frame from video source {video_source}")
                else:
                    print(f"Failed to open video source {video_source}")
                
                # Release the capture
                cap.release()
            except Exception as e:
                print(f"Error capturing frame: {e}")
    
    # If we couldn't get a frame from the video source, fall back to the static image
    if frame is None:
        print(f"Using static image from {live_frame_path}")
        frame = cv2.imread(live_frame_path)
        if frame is None:
            print(f"Error: Could not load the live frame from {live_frame_path}.")
            sys.exit(1)
    
    # Resize the frame to the desired resolution
    frame = cv2.resize(frame, (resized_width, resized_height))
    
    # Create a named window and set mouse callback
    cv2.namedWindow('ROI_Editor', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('ROI_Editor', 800, 600)
    cv2.setMouseCallback('ROI_Editor', draw_polyline)
    
    while True:
        # Make a copy of the frame to draw polylines on
        frame_copy = frame.copy()
        
        # Draw existing polylines
        for pts in polylines:
            cv2.polylines(frame_copy, [pts], isClosed=True, color=(0, 255, 0), thickness=2)
        
        # Draw current polyline (incomplete)
        if current_polyline:
            for i in range(len(current_polyline) - 1):
                cv2.line(frame_copy, tuple(current_polyline[i]), tuple(current_polyline[i+1]), (0, 0, 255), 2)
        
        # Create a dark background for text
        cv2.rectangle(frame_copy, (5, 5), (635, 60), (0, 0, 0), -1)
        cv2.rectangle(frame_copy, (5, 5), (635, 60), (255, 255, 255), 1)

        # Add detailed instructions on multiple lines
        cv2.putText(frame_copy, "ROI Editor Controls:", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frame_copy, "- Left-click: Add points | Right-click: Complete polyline", (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frame_copy, "- Middle-click: Delete polyline | 's': Save | 'q': Quit", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        
        # Show the frame with polylines
        cv2.imshow('ROI_Editor', frame_copy)
        
        # Handle key press events
        key = cv2.waitKey(100)
        if key & 0xFF == ord('q'):  # Quit
            break
        elif key & 0xFF == ord('s'):  # Save polylines to JSON file
            save_polylines(POLYLINES_FILE)
            print(f"Polylines saved to {POLYLINES_FILE}")
    
    # Close all OpenCV windows
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
