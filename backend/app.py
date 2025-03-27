"""
Main application entry point
"""

from app import create_app
from app.config import HOST, PORT, DEBUG

# Create Flask application
app = create_app()

if __name__ == "__main__":
    # Start the Flask development server
    app.run(host=HOST, port=PORT, debug=DEBUG)
