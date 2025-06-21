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

## Usage Guide

### Setting Up Your Account

1. Register with your email and create a password
2. Log in to access the dashboard

### Configuring Video Source

1. Navigate to Settings
2. Choose your preferred video source:
   - Webcam (select from available cameras)
   - IP Camera (enter the camera's URL)
   - Upload a video file (for testing or offline analysis)

### Setting Up Regions of Interest (ROI)

1. Go to Settings > Region of Interest
2. Use the ROI Editor to draw polygons around areas you want to monitor
3. Save your settings

### Monitoring and Alerts

1. The Dashboard shows the live video feed with AI detection overlays
2. When a package is detected and then disappears, the system will:
   - Generate an alert in the dashboard
   - Send an email notification (if configured)
   - Create an entry in the detection archive

### Reviewing Detections

1. Use the Archive section to view all past detections
2. Filter by date, detection type, and confidence level
3. Mark detections as "Verified Safe" or "Verified Theft"

### Analyzing Reports

1. Visit the Reports section to view detection statistics
2. Analyze trends in package deliveries and potential theft incidents
3. View confidence levels and verification status of detections

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
```

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
