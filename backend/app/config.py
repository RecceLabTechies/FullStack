import os

# Flask Configuration
DEBUG = os.getenv("FLASK_DEBUG", "True") == "True"
PORT = int(os.getenv("PORT", 5000))
HOST = "0.0.0.0"
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

# PostgreSQL Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:example@postgres:5432/app"
)

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# CORS Configuration
CORS_CONFIG = {
    "origins": "*",
    "methods": ["GET", "POST", "PATCH", "OPTIONS", "PUT"],
    "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
}
