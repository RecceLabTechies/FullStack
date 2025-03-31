# RecceLabTechies Backend Service

This repository contains the Flask-based REST API backend service for the RecceLabTechies campaign analytics application.

## Overview

The backend provides a comprehensive API for campaign performance analytics, user management, and data visualization. Built with:

- **Flask**: Web framework for RESTful API endpoints
- **MongoDB**: NoSQL database for storing campaign performance data
- **Marshmallow**: Schema validation and serialization
- **Pandas**: Data processing and analysis

## Project Structure

```
backend/
├── app/                  # Main application package
│   ├── __init__.py       # Application factory
│   ├── database/         # Database connection modules
│   ├── models/           # Data models
│   ├── routes/           # API endpoint definitions
│   │   ├── data_routes.py    # Campaign data endpoints
│   │   └── user_routes.py    # User management endpoints
│   ├── services/         # Business logic
│   │   └── campaign_service.py  # Campaign analytics logic
│   └── utils/            # Utility functions for data processing
├── data/                 # Sample/training data files
├── notebooks/            # Jupyter notebooks for analysis
│   └── prophet/          # Time series forecasting models
├── tests/                # Test suite
│   ├── test_data_routes.py
│   └── test_user_routes.py
├── .env                  # Environment variables (git-ignored)
├── environment.yml       # Conda environment definition
├── pyproject.toml        # Project metadata and config
├── requirements.txt      # Pip dependencies
└── README.md             # This documentation
```

## Getting Started

### Prerequisites

- Python 3.12+
- Anaconda or Miniconda
- MongoDB

### Environment Setup

#### Using Conda (Recommended)

1. Create and activate the conda environment:

   ```bash
   conda env create -f environment.yml
   conda activate reccelabs
   ```

#### Using Pip

1. Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

### Configuration

Create a `.env` file in the project root with the following variables:

```
MONGO_URI=mongodb://localhost:27017/
MONGO_DB_NAME=campaign_data
FLASK_APP=app
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=your_secret_key_here
```

### Running the Application

```bash
python run.py
```

The application will be available at http://localhost:5000.

## API Endpoints

### User Management

- `GET /api/v1/users`: Get all users
- `POST /api/v1/users`: Create a new user
- `GET /api/v1/users/{username}`: Get user details
- `PUT /api/v1/users/{username}`: Update user
- `PATCH /api/v1/users/{username}`: Partially update user
- `DELETE /api/v1/users/{username}`: Delete user

### Campaign Data

- `GET /api/v1/campaigns/filter-options`: Get all filter options
- `GET /api/v1/campaigns`: Get filtered campaign data
- `POST /api/v1/campaigns`: Filter campaigns with complex criteria
- `GET /api/v1/campaigns/revenues`: Get revenue data by date
- `GET /api/v1/campaigns/monthly-performance`: Get monthly performance metrics
- `POST /api/v1/campaigns/monthly-data`: Update monthly revenue/ad spend data
- `GET /api/v1/campaigns/channels/roi`: Get ROI per marketing channel
- `GET /api/v1/campaigns/age-groups/roi`: Get ROI per age group
- `GET /api/v1/campaigns/cost-heatmap`: Get cost metrics heatmap

### Data Import

- `POST /api/v1/imports/csv`: Import campaign data from CSV

## Testing

Run the test suite:

```bash
pytest
```

For test coverage report:

```bash
pytest --cov=app
```

## Development

Install development dependencies:

```bash
pip install -e ".[dev]"
```

Format code with Black:

```bash
black app/ tests/
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
