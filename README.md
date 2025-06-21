# SnapSecure - AI-Powered Package Theft Detection System

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

SnapSecure is a comprehensive AI-powered security system designed to detect and monitor package deliveries and potential theft incidents. The system uses computer vision, and real-time monitoring to provide homeowners with an advanced solution to protect their delivered packages.

## Features

### Core Functionality
- **AI-Powered Detection**: Utilizes Roboflow's machine learning models to identify packages and potential theft events
- **Real-time Monitoring**: Continuously analyzes video feeds for suspicious activity
- **Region of Interest (ROI)**: Define specific areas to monitor through an intuitive drawing interface
- **Multi-source Video Support**: Connect to webcams, IP cameras, or upload video files

### User Experience
- **User Authentication**: Secure login and registration system
- **Intuitive Dashboard**: Real-time alerts and system status at a glance
- **Email Notifications**: Receive alerts when potential theft is detected
- **Mobile-responsive Design**: Access the system from any device

### Data Management
- **Archived Detections**: View and filter historical detection events
- **Detailed Reports**: Analyze detection patterns with visual charts and statistics
- **Event Verification**: Mark detections as verified safe or verified theft
- **User Profiles**: Manage personal information and system preferences

## System Architecture

SnapSecure is built using modern web technologies and follows a client-server architecture:

- **Frontend**: HTML5, CSS3, JavaScript, Chart.js
- **Backend**: Python Flask web framework
- **Database**: MongoDB for data storage
- **AI Integration**: Roboflow API for object detection
- **Video Processing**: OpenCV and SORT tracking algorithm
- **Notifications**: Flask-Mail for email alerts

## Getting Started

### Prerequisites

- Python 3.10+
- MongoDB
- Docker and Docker Compose (for containerized deployment)
- Roboflow API key

### Installation

#### Option 1: Local Setup

1. Clone the repository:
```bash
git clone https://github.com/RahulRKS01/SnapSecure2.0.git
cd snapsecure
```

2. Create Virtual Environment:
```bash
python -m venv venv
```

3. Install dependencies:
```bash

pip install -r requirements.txt
```

4. Set up environment variables:
```bash
# Create a .env file with the following variables
# Flask secret key
FLASK_SECRET_KEY=your_secret_key_here

# MongoDB credentials
MONGO_USERNAME=your_mongodb_username
MONGO_PASSWORD=your_mongodb_password
MONGO_URI=your_mongodb_uri

# Roboflow API configuration
ROBOFLOW_API_URL=https://serverless.roboflow.com
ROBOFLOW_API_KEY=your_roboflow_api_key
ROBOFLOW_MODEL_ID=your_model_id

# Flask-Mail configuration
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@example.com
MAIL_PASSWORD=your_email_password
MAIL_DEFAULT_SENDER=your_email@example.com
```

5. Run the application:
```bash
flask run
```

#### Option 2: Docker Deployment (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/RahulRKS01/SnapSecure2.0.git
cd snapsecure
```

2. Create a `.env` file with your environment variables (see above)

3. Build and run with Docker Compose:
```bash
docker-compose build

docker-compose up -d
```

The application will be available at http://localhost:5000

## Detailed Usage Guide

### Creating and Setting Up Your Account

#### Registration:
- Navigate to the registration page from the home screen
- Enter your email address, create a strong password, and confirm your password
- Submit the form to create your account
  
#### Login:
- Enter your registered email and password

#### Profile Management:
- Access your profile from the user menu in the top-right corner
- Update personal information (name, contact details)
- Set notification preferences

### Dashboard Navigation

The dashboard is your central control center, featuring:

#### Main Panel:
- Live video feed with AI detection overlays
- Current system status indicators
- Quick access to recent alerts
- System performance metrics

#### Navigation Sidebar:
- Dashboard (home)
- Archive (detection history)
- Reports (analytics)
- Settings

### Configuring Video Sources

#### Navigate to Settings > Video Source:
- Click on the settings icon or use the sidebar navigation

#### Select Video Source Type:

##### Camera: Use built-in webcam or connected cameras
- Select from the dropdown list of available devices
- Save the camera source before switching back to dashboard

##### IP Camera:
- Enter the RTSP/HTTP URL (e.g., `rtsp://username:password@camera_ip:port/stream`)
- Specify authentication details if required
- Test the connection before saving
- Common formats:
  - Hikvision: `rtsp://username:password@camera_ip:554/Streaming/Channels/101`
  - Dahua: `rtsp://username:password@camera_ip:554/cam/realmonitor?channel=1&subtype=0`
  - Generic ONVIF: `rtsp://camera_ip:554/onvif1`

##### Upload Video:
- Click "Choose File" to select a video from your device
- Supported formats: MP4, AVI, MOV (max size: 500MB)
- Click "Upload" and wait for processing confirmation
- The system will analyze the uploaded video as if it were a live stream

### Setting Up Regions of Interest (ROI)

#### Access ROI Editor:
- Go to Settings > Region of Interest
- Click on the "Edit ROI" button

#### Drawing ROI Areas:
- The video feed will freeze to allow you to draw
- Click on the video to place points forming a polygon
- Continue clicking to add more points
- Double click upon placing the last point to complete the polygon
- Multiple ROIs can be created for different areas

#### Editing ROI Areas:
- Click on an existing ROI to select it
- Select the "Delete ROI" option to delete the selected Polygon
  
#### Saving ROI Configuration:
- Click "Save ROIs" to confirm your changes
- The system will immediately begin using the new ROI settings

### Monitoring and Alert System

#### Real-time Monitoring:
- The dashboard displays active monitoring status
- Detection boxes appear around identified objects
- Object labels and confidence scores are displayed

#### Alert Notifications:

##### Email Notifications:
- Instant emails for critical alerts include:
  - Detection timestamp
  - Detection type (package, person, potential theft)
  - Confidence level
  - Screenshot of the event

#### Alert Response:
- Click on an alert to view details
- Mark alerts as "Safe" or "Package Theft"

### Managing Detection Archive

#### Accessing the Archive:
- Navigate to the Archive section from the sidebar
- View a chronological list of all detection events

#### Filtering and Sorting:
- Filter by date range using the calendar picker
- Sort by time or time

#### Detection Details:
- Click on any detection to view detailed information
- See metadata including:
  - Timestamp
  - Object type
  - Confidence score
  - ROI zone where detected

#### Verification Actions:
- Mark detections as:
  - Verified Safe (legitimate delivery or household member)
  - Verified Theft (confirmed package theft)

#### Export Options:
- Generate printable reports for law enforcement

### Analytics and Reporting

#### Accessing Reports:
- Navigate to the Reports section from the sidebar

#### Reports Analytics:
- View detection statistics for selected time periods
- Interactive charts showing:
  - Detection frequency by day/week/month
  - Distribution of detection types
  - Confidence level distributions
  - Peak detection times

#### Custom Reports:
- Create reports for specific date ranges

#### Exporting Reports:
- Download reports as PDF

### Troubleshooting Guide

#### Video Feed Issues

##### No Video Feed:
- Check that your camera is properly connected
- Verify camera permissions in your browser
- Ensure the correct video source is selected
- Restart the application if the feed freezes

##### Poor Video Quality:
- Check your internet connection if using an IP camera
- Lower the resolution in settings
- Ensure adequate lighting in the monitored area
- Clean the camera lens if applicable

##### IP Camera Connection Failures:
- Verify the camera is powered on and connected to your network
- Double-check the RTSP/HTTP URL format
- Ensure username and password are correct
- Check that your firewall allows the connection

#### Detection Issues

##### False Positives:
- Increase the confidence threshold in settings
- Refine your ROI to exclude areas with movement
- Adjust lighting to reduce shadows and reflections
- Update to the latest AI model if available

##### Missed Detections:
- Lower the confidence threshold
- Ensure packages are visible and not obscured
- Adjust camera positioning for better coverage
- Expand ROI to include all relevant areas

##### Tracking Issues:
- Increase processing resolution
- Reduce camera movement (wind, vibrations)
- Ensure consistent lighting (avoid extreme light changes)
- Check for objects that might block the view

#### Notification Issues

##### No Email Alerts:
- Check your spam/junk folder
- Verify your email address is correct in profile settings
- Ensure email notification are enabled in settings
- Check SMTP server configuration in .env file

##### Delayed Notifications:
- Check your internet connection
- Verify server resources are adequate
- Consider upgrading your hosting plan if using cloud deployment

#### Database and Storage Issues

##### "Database Connection Failed" Error:
- Check MongoDB is running
- Verify connection details in .env file
- Ensure database user has correct permissions
- Check disk space for database storage

##### Storage Full Warning:
- Delete unnecessary detection videos
- Adjust video retention settings
- Archive old data or expand storage capacity
- Lower video quality settings to reduce file sizes

## Docker Deployment Details

SnapSecure is containerized using Docker for easy deployment and scaling:

### Docker Components

- **Application Container**: Python environment with all dependencies
- **MongoDB Container**: Database for storing detection events and user data
- **Networking**: Containers communicate on an internal network
- **Volumes**: Persistent storage for database and uploaded videos

### Docker Setup

The `Dockerfile` includes:
- Base Python image with necessary system dependencies
- OpenCV and video processing libraries
- Flask application setup
- Xvfb configuration for headless video processing

The `docker-compose.yml` configures:
- Service dependencies
- Environment variables
- Network settings
- Volume mappings
- Port forwarding

### Running with Docker

```bash
# Build and start the containers
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down

# Update containers (after code changes)
docker-compose build
docker-compose up -d
```

### Docker Troubleshooting

#### Container Fails to Start:
- Check logs: `docker-compose logs app`
- Verify environment variables in .env file
- Ensure ports are not already in use

#### Camera Access in Docker:
- Add `--device=/dev/video0:/dev/video0` to docker run command
- Ensure the host system has proper camera permissions

#### Performance Issues:
- Allocate more resources to Docker (CPU, RAM)
- Use volume mounts instead of copying files when possible
- Consider enabling GPU support for faster AI processing

## Technical Details

### Video Processing Pipeline

1. Video frames are captured from the selected source
2. Each frame is processed through the Roboflow AI model
3. The SORT algorithm tracks objects across frames
4. Detected objects are filtered based on ROI settings
5. Detection events are stored in MongoDB
6. The system monitors for package disappearance events

### Database Schema

- **User Collection**: User authentication and preferences
- **Detection Collection**: Package detection events with metadata
- **Report Collection**: Verified events with user feedback

### Security Features

- Password hashing with bcrypt
- Session management
- Input validation
- Environment variable separation

## Troubleshooting

### Common Issues

1. **Video feed not loading**
   - Check camera permissions
   - Verify IP camera URL format
   - Ensure Docker has access to camera devices

2. **AI detection not working**
   - Verify your Roboflow API key is correct
   - Check internet connectivity
   - Adjust ROI settings if needed

3. **Email notifications not received**
   - Check spam/junk folder
   - Verify email configuration settings
   - Ensure email service provider allows automated emails

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Roboflow for providing the object detection models
- SORT algorithm for object tracking
- OpenCV for video processing capabilities
- Flask framework for web application development

---

**Note**: SnapSecure is designed for personal use and should be deployed responsibly, respecting privacy laws and regulations in your jurisdiction.
**Contact**: Please do contact me at 82102@siswa.unimas.my or jaszrks@gmail.com to obtain more details on how to run the system.
