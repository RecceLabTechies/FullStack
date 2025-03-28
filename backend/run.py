#!/usr/bin/env python3
"""
Alternative entry point for running the application
"""
from app import create_app
from app.config import HOST, PORT, DEBUG

if __name__ == "__main__":
    app = create_app()
    app.run(host=HOST, port=PORT, debug=DEBUG)
