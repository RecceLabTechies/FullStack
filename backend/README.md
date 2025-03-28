# Backend API Service

This directory contains the Flask-based REST API backend service for the FullStack application.

## Overview

The backend provides a RESTful API for the frontend to interact with the database and other services. It's built with:

- **Flask**: Python web framework for building the API
- **MongoDB**: Database connector for data storage
- **RESTful Design**: Organized routes for resource management

## Project Structure

```
backend/
├── app/                  # Main application package
│   ├── __init__.py       # Application factory
│   ├── config.py         # Configuration settings
│   ├── routes/           # API endpoints
│   ├── models/           # Data models
│   ├── database/         # Database connections
│   └── utils/            # Utility functions
├── data_storage/         # Data storage modules
├── tests/                # Test suite
├── Dockerfile            # Container configuration
├── requirements.txt      # Python dependencies
├── pyproject.toml        # Project metadata and tools configuration
├── run.py                # Application entry point
└── README.md             # This documentation
```

## Getting Started

### Prerequisites

- Python 3.8+
- MongoDB (accessible via configuration)

### Local Development

1. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the development server:
   ```bash
   python run.py
   ```

### Docker Deployment

Build and run the Docker container:

```bash
docker build -t fullstack-backend .
docker run -p 5001:5001 fullstack-backend
```

## API Documentation

The API provides endpoints for:

- User management
- Authentication
- Data operations
- Integration with other services

## Environment Configuration

Environment variables or a `.env` file can be used to configure:

- Database connection
- API keys
- Environment-specific settings
- Debug options

## Testing

Run the test suite:

```bash
pytest
```

## License

This project is licensed under the terms of the included LICENSE file.
