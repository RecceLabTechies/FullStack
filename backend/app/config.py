import os

# Flask Configuration
DEBUG = os.getenv("FLASK_DEBUG", "True") == "True"
PORT = int(os.getenv("PORT", 5000))
HOST = "0.0.0.0"
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://root:example@mongodb:27017/")
DB_NAME = os.getenv("MONGO_DB_NAME", "test_database")

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# CORS Configuration
CORS_CONFIG = {
    "origins": "*",
    "methods": ["GET", "POST", "PATCH", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
}
