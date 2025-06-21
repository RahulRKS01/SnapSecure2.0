import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Flask secret key
SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "default_dev_secret_key")

# MongoDB credentials
username = os.getenv("MONGO_USERNAME")
password = os.getenv("MONGO_PASSWORD")

# URL-encode the username and password if they exist
encoded_username = quote_plus(username) if username else ""
encoded_password = quote_plus(password) if password else ""

# MongoDB Atlas connection string
MONGO_URI = os.getenv(
    "MONGO_URI",
    f"mongodb+srv://{encoded_username}:{encoded_password}@fyp.ftcyv.mongodb.net/PackageDetectionSystem?retryWrites=true&w=majority"
)

# Roboflow API configuration
API_URL = os.getenv("ROBOFLOW_API_URL")
API_KEY = os.getenv("ROBOFLOW_API_KEY")
MODEL_ID = os.getenv("ROBOFLOW_MODEL_ID")

# Path to the polylines file
POLYLINES_FILE = os.getenv(
    "POLYLINES_FILE",
    os.path.join(os.path.dirname(__file__), "polylines.json")
)

# Flask-Mail configuration
MAIL_CONFIG = {
    "MAIL_SERVER": os.getenv("MAIL_SERVER"),
    "MAIL_PORT": int(os.getenv("MAIL_PORT", 587)),
    "MAIL_USE_TLS": os.getenv("MAIL_USE_TLS", "True").lower() == "true",
    "MAIL_USERNAME": os.getenv("MAIL_USERNAME"),
    "MAIL_PASSWORD": os.getenv("MAIL_PASSWORD"),
    "MAIL_DEFAULT_SENDER": os.getenv("MAIL_DEFAULT_SENDER")
}