"""
Application Configuration Module

This module centralizes all configuration settings for the LLM backend application.
It handles environment variable loading and provides default values for various
configuration parameters.

Configuration categories include:
- Flask server settings (debug mode, port, host)
- PostgreSQL connection parameters
- Logging configuration
- CORS (Cross-Origin Resource Sharing) settings
"""

import os

# Flask Configuration
# Controls the application server behavior
DEBUG = os.getenv("FLASK_DEBUG", "True") == "True"  # Enable/disable debug mode
PORT = int(os.getenv("PORT", 5000))  # HTTP port to listen on
HOST = "0.0.0.0"  # Listen on all network interfaces
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max request size

# PostgreSQL Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:example@postgres:5432/app"
)
# When running in Docker, the host should be 'postgres' (service name)
# When running locally, the host should be 'localhost'
# DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:example@localhost:5432/app")

# Logging Configuration
# Controls log verbosity and format
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")  # Default to INFO level if not specified
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# CORS Configuration
# Allows the API to be accessed from different origins (e.g., frontend applications)
CORS_CONFIG = {
    "origins": "*",  # Allow all origins (can be restricted in production)
    "methods": ["GET", "POST", "PATCH", "OPTIONS"],  # Allowed HTTP methods
    "allow_headers": [
        "Content-Type",
        "Authorization",
        "X-Requested-With",
    ],  # Allowed headers
}
