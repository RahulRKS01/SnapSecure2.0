# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for OpenCV and other libraries
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libfontconfig1 \
    libxrender1 \
    libdbus-1-3 \
    libxkbcommon-x11-0 \
    libxi6 \
    fonts-liberation \
    libfreetype6 \
    libharfbuzz0b \
    && rm -rf /var/lib/apt/lists/*

# Add additional fonts
RUN apt-get update && apt-get install -y \
    fonts-dejavu \
    fonts-liberation

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    # First install small dependencies
    pip install --no-cache-dir --timeout 180 --retries 5 python-dotenv Flask Flask-Bcrypt Flask-Mail pymongo requests && \
    # Then the scientific libraries that might timeout
    pip install --no-cache-dir --timeout 180 --retries 5 numpy scipy matplotlib && \
    # Then OpenCV which is often problematic on ARM
    pip install --no-cache-dir --timeout 180 --retries 5 "opencv-python<=4.10.0.84,>=4.8.1.78" && \
    # Finally install remaining packages
    pip install --no-cache-dir --timeout 180 --retries 5 -r requirements.txt

# Install ffmpeg for video processing
RUN apt-get update && apt-get install -y ffmpeg

# Install wkhtmltopdf and dependencies
RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    xvfb \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Add ARM-specific dependencies
RUN apt-get update && apt-get install -y \
    libatlas-base-dev \
    libhdf5-dev \
    libhdf5-serial-dev \
    libopenjp2-7 \
    && rm -rf /var/lib/apt/lists/*

# Copy the rest of the application code
COPY . .

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV FLASK_RUN_HOST=0.0.0.0

# Set the DISPLAY environment variable
ENV DISPLAY=:99

# Default MongoDB URI - will be overridden by env var if provided
ENV MONGO_URI=mongodb://localhost:27017/PackageDetectionSystem

# Create upload directory
RUN mkdir -p uploaded_videos && chmod 777 uploaded_videos


# Run the Flask application
CMD ["flask", "run"]