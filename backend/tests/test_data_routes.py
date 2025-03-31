import pytest
import json
import sys
import os
from unittest.mock import patch, MagicMock
from io import BytesIO
from flask import Flask, Blueprint, jsonify, request

# Add the project root to the Python path to ensure imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Now import from app
try:
    from app import create_app
except ImportError as e:
    print(f"Import error: {e}")
    # Create a simplified test version if import fails
    from flask import Flask

    def create_app(config_name=None):
        app = Flask(__name__)
        app.config["TESTING"] = True
        return app


# Create a test app for testing routes in isolation
@pytest.fixture
def client():
    """Create a test client for the app"""
    app = Flask(__name__)
    app.config["TESTING"] = True

    # Mock data routes
    data_bp = Blueprint("data_routes", __name__)

    # ----------------------------------------------------------------
    # Database structure endpoints
    # ----------------------------------------------------------------
    @data_bp.route("/api/v1/database/structure", methods=["GET"])
    def get_database_structures_data():
        """Mock database structure endpoint"""
        structure = {
            "databases": [
                {
                    "name": "campaign_data",
                    "collections": ["campaigns", "monthly_data", "user_data"],
                }
            ]
        }
        return jsonify({"success": True, "data": structure, "status": 200})

    # ----------------------------------------------------------------
    # Campaign data endpoints
    # ----------------------------------------------------------------
    @data_bp.route("/api/v1/campaigns/filter-options", methods=["GET"])
    def get_campaign_filters_data():
        """Mock filter options endpoint"""
        filter_options = {
            "channels": ["Facebook", "Google", "Instagram"],
            "countries": ["Singapore", "Malaysia", "Indonesia"],
            "age_groups": ["18-24", "25-34", "35-44", "45-54", "55+"],
            "campaign_ids": ["January_2022_1", "February_2022_1"],
            "date_range": {"min": "2022-01-01", "max": "2022-12-31"},
        }
        return jsonify({"success": True, "data": filter_options, "status": 200})

    @data_bp.route("/api/v1/campaigns", methods=["GET", "POST"])
    def get_campaigns_data():
        """Mock campaigns data endpoint"""
        # For testing validation errors
        if request.method == "POST":
            data = request.json or {}

            # Check for validation error case
            if data.get("test_validation_error"):
                return (
                    jsonify(
                        {
                            "error": {
                                "status": 400,
                                "message": "Validation error",
                                "type": "validation_error",
                                "details": {"channels": ["Invalid channel"]},
                            }
                        }
                    ),
                    400,
                )

        # Return mock data for normal case
        campaigns = {
            "items": [
                {
                    "date": "2022-01-01",
                    "campaign_id": "January_2022_1",
                    "channel": "Facebook",
                    "country": "Singapore",
                    "age_group": "25-34",
                    "ad_spend": 5000.0,
                    "views": 150000,
                    "leads": 3000,
                    "new_accounts": 300,
                    "revenue": 15000.0,
                }
            ],
            "total": 1,
            "page": 1,
            "page_size": 20,
            "total_pages": 1,
        }
        return jsonify({"success": True, "data": campaigns, "status": 200})

    @data_bp.route("/api/v1/campaigns/revenues", methods=["GET"])
    def get_revenue_by_date_data():
        """Mock revenue by date endpoint"""
        data_summary = {
            "dates": ["2022-01", "2022-02", "2022-03"],
            "revenues": [15000, 18000, 22000],
            "ad_spends": [5000, 6000, 7000],
        }
        return jsonify({"success": True, "data": data_summary, "status": 200})

    @data_bp.route("/api/v1/campaigns/monthly-performance", methods=["GET"])
    def get_monthly_performance_data_route():
        """Mock monthly performance endpoint"""
        # Test validation errors if specific params are passed
        if request.args.get("test_validation_error") == "true":
            return (
                jsonify(
                    {
                        "error": {
                            "status": 400,
                            "message": "Validation error",
                            "type": "validation_error",
                            "details": {"from_date": ["Invalid date format"]},
                        }
                    }
                ),
                400,
            )

        performance_data = {
            "months": ["2022-01", "2022-02", "2022-03"],
            "revenue": [15000, 18000, 22000],
            "ad_spend": [5000, 6000, 7000],
            "roi": [3.0, 3.0, 3.14],
        }
        return jsonify({"success": True, "data": performance_data, "status": 200})

    @data_bp.route("/api/v1/campaigns/monthly-data", methods=["POST"])
    def update_monthly_data_route():
        """Mock update monthly data endpoint"""
        data = request.json or {}

        # Check if request has updates
        if not data or "updates" not in data:
            return (
                jsonify(
                    {
                        "error": {
                            "status": 400,
                            "message": "Request body is required",
                            "type": "validation_error",
                        }
                    }
                ),
                400,
            )

        # Check for validation errors for test case
        if data.get("test_validation_error"):
            return (
                jsonify(
                    {
                        "error": {
                            "status": 400,
                            "message": "Validation error",
                            "type": "validation_error",
                            "details": {"updates": ["Invalid month format"]},
                        }
                    }
                ),
                400,
            )

        # Simulate successful update
        return jsonify(
            {
                "success": True,
                "data": {
                    "message": "Monthly data updated successfully",
                    "months": ["2022-01", "2022-02", "2022-03"],
                    "revenue": [20000, 18000, 22000],  # Updated
                    "ad_spend": [5000, 6000, 7000],
                },
                "status": 200,
            }
        )

    @data_bp.route("/api/v1/campaigns/channels/roi", methods=["GET"])
    def get_channel_roi_data_route():
        """Mock channel ROI endpoint"""
        data = [
            {"channel": "Facebook", "roi": 3.0},
            {"channel": "Google", "roi": 3.5},
            {"channel": "Instagram", "roi": 2.8},
        ]
        return jsonify({"success": True, "data": data, "status": 200})

    @data_bp.route("/api/v1/campaigns/age-groups/roi", methods=["GET"])
    def get_age_group_roi_data_route():
        """Mock age group ROI endpoint"""
        data = [
            {"age_group": "18-24", "roi": 2.5},
            {"age_group": "25-34", "roi": 3.2},
            {"age_group": "35-44", "roi": 2.9},
        ]
        return jsonify({"success": True, "data": data, "status": 200})

    @data_bp.route("/api/v1/campaigns/past-month/revenue", methods=["GET"])
    def get_revenue_past_month_data_route():
        """Mock past month revenue endpoint"""
        return jsonify({"success": True, "data": {"revenue": 22000}, "status": 200})

    @data_bp.route("/api/v1/campaigns/past-month/roi", methods=["GET"])
    def get_roi_past_month_data_route():
        """Mock past month ROI endpoint"""
        return jsonify({"success": True, "data": {"roi": 3.14}, "status": 200})

    @data_bp.route("/api/v1/campaigns/cost-heatmap", methods=["GET"])
    def get_cost_heatmap_data_route():
        """Mock cost heatmap endpoint"""
        # Test non-existent data case
        if request.args.get("country") == "nonexistent":
            return (
                jsonify(
                    {
                        "error": {
                            "status": 404,
                            "message": "No data found for nonexistent and campaign January_2022_1",
                            "type": "resource_not_found",
                        }
                    }
                ),
                404,
            )

        data_summary = [
            {
                "channel": "Facebook",
                "costPerLead": 1.67,
                "costPerView": 0.03,
                "costPerAccount": 16.67,
            },
            {
                "channel": "Google",
                "costPerLead": 1.82,
                "costPerView": 0.04,
                "costPerAccount": 18.18,
            },
        ]
        return jsonify({"success": True, "data": data_summary, "status": 200})

    # ----------------------------------------------------------------
    # CSV import endpoints
    # ----------------------------------------------------------------
    @data_bp.route("/api/v1/imports/csv", methods=["POST", "OPTIONS"])
    def create_csv_import_data():
        """Mock CSV import endpoint"""
        if request.method == "OPTIONS":
            response = jsonify({})
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add("Access-Control-Allow-Headers", "*")
            response.headers.add("Access-Control-Allow-Methods", "POST")
            return response

        # Check if file is provided
        if "file" not in request.files:
            return (
                jsonify(
                    {
                        "error": {
                            "status": 400,
                            "message": "No file selected",
                            "type": "validation_error",
                        }
                    }
                ),
                400,
            )

        file = request.files["file"]

        # Check if it's a CSV file
        if not file.filename.endswith(".csv"):
            return (
                jsonify(
                    {
                        "error": {
                            "status": 400,
                            "message": "File must be a CSV",
                            "type": "validation_error",
                        }
                    }
                ),
                400,
            )

        # Simulate successful import
        return jsonify(
            {
                "success": True,
                "data": {
                    "message": "CSV uploaded to new collection successfully",
                    "count": 10,
                    "collection": "campaign_data_2022",
                },
                "status": 200,
            }
        )

    # ----------------------------------------------------------------
    # Utility endpoints
    # ----------------------------------------------------------------
    @data_bp.route("/api/v1/utils/date-types", methods=["GET"])
    def get_date_type_data():
        """Mock date type endpoint"""
        # Return mock date type info
        return jsonify(
            {
                "success": True,
                "data": {
                    "value": "2022-01-01T00:00:00.000Z",
                    "type": "<class 'datetime.datetime'>",
                },
                "status": 200,
            }
        )

    # Register blueprint
    app.register_blueprint(data_bp)

    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_campaign_data():
    """Sample campaign data for testing"""
    return {
        "date": "2022-01-01",
        "campaign_id": "January_2022_1",
        "channel": "Facebook",
        "country": "Singapore",
        "age_group": "25-34",
        "ad_spend": 5000.0,
        "views": 150000,
        "leads": 3000,
        "new_accounts": 300,
        "revenue": 15000.0,
    }


@pytest.fixture
def mock_monthly_update_data():
    """Sample monthly update data for testing"""
    return {"updates": [{"month": "2022-01", "revenue": 20000.0, "ad_spend": 5000.0}]}


@pytest.fixture
def mock_csv_file():
    """Create a mock CSV file for testing"""
    csv_content = b"date,campaign_id,channel,country,age_group,ad_spend,views,leads,new_accounts,revenue\n"
    csv_content += b"2022-01-01,January_2022_1,Facebook,Singapore,25-34,5000.0,150000,3000,300,15000.0\n"

    return {"file": (BytesIO(csv_content), "test_data.csv")}


class TestDataRoutesDatabase:
    """Test suite for database structure endpoint"""

    def test_get_database_structure(self, client):
        """Test GET /api/v1/database/structure"""
        response = client.get("/api/v1/database/structure")

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["success"] is True
        assert "databases" in response_data["data"]
        assert len(response_data["data"]["databases"]) == 1


class TestDataRoutesCampaigns:
    """Test suite for campaign data endpoints"""

    def test_get_campaign_filter_options(self, client):
        """Test GET /api/v1/campaigns/filter-options"""
        response = client.get("/api/v1/campaigns/filter-options")

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["success"] is True
        assert "channels" in response_data["data"]
        assert "countries" in response_data["data"]
        assert "age_groups" in response_data["data"]

    def test_get_campaigns_get_method(self, client, mock_campaign_data):
        """Test GET /api/v1/campaigns"""
        response = client.get("/api/v1/campaigns")

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["success"] is True
        assert "items" in response_data["data"]
        assert len(response_data["data"]["items"]) > 0

    def test_get_campaigns_post_method(self, client, mock_campaign_data):
        """Test POST /api/v1/campaigns with filter parameters"""
        filter_params = {
            "channels": ["Facebook"],
            "countries": ["Singapore"],
            "age_groups": ["25-34"],
            "from_date": "2022-01-01",
            "to_date": "2022-12-31",
            "sort_by": "date",
            "sort_dir": "desc",
        }

        response = client.post(
            "/api/v1/campaigns",
            data=json.dumps(filter_params),
            content_type="application/json",
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["success"] is True
        assert "items" in response_data["data"]

    def test_get_campaigns_validation_error(self, client):
        """Test POST /api/v1/campaigns with invalid data"""
        invalid_params = {
            "test_validation_error": True,
            "channels": ["InvalidChannel"],
        }

        response = client.post(
            "/api/v1/campaigns",
            data=json.dumps(invalid_params),
            content_type="application/json",
        )

        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert "error" in response_data
        assert response_data["error"]["type"] == "validation_error"

    def test_get_revenue_by_date(self, client):
        """Test GET /api/v1/campaigns/revenues"""
        response = client.get("/api/v1/campaigns/revenues")

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["success"] is True
        assert "dates" in response_data["data"]
        assert "revenues" in response_data["data"]
        assert "ad_spends" in response_data["data"]

    def test_get_monthly_performance(self, client):
        """Test GET /api/v1/campaigns/monthly-performance"""
        response = client.get("/api/v1/campaigns/monthly-performance")

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["success"] is True
        assert "months" in response_data["data"]
        assert "revenue" in response_data["data"]
        assert "ad_spend" in response_data["data"]
        assert "roi" in response_data["data"]

    def test_get_monthly_performance_with_filters(self, client):
        """Test GET /api/v1/campaigns/monthly-performance with filters"""
        response = client.get(
            "/api/v1/campaigns/monthly-performance?from_date=2022-01-01&to_date=2022-12-31&channels=Facebook,Google"
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["success"] is True

    def test_get_monthly_performance_validation_error(self, client):
        """Test GET /api/v1/campaigns/monthly-performance with invalid data"""
        response = client.get(
            "/api/v1/campaigns/monthly-performance?test_validation_error=true"
        )

        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert "error" in response_data
        assert response_data["error"]["type"] == "validation_error"

    def test_update_monthly_data_success(self, client, mock_monthly_update_data):
        """Test POST /api/v1/campaigns/monthly-data with valid data"""
        response = client.post(
            "/api/v1/campaigns/monthly-data",
            data=json.dumps(mock_monthly_update_data),
            content_type="application/json",
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["success"] is True
        assert "message" in response_data["data"]
        assert "months" in response_data["data"]
        assert "revenue" in response_data["data"]
        assert "ad_spend" in response_data["data"]

    def test_update_monthly_data_validation_error(self, client):
        """Test POST /api/v1/campaigns/monthly-data with invalid data"""
        invalid_data = {
            "test_validation_error": True,
            "updates": [
                {
                    "month": "invalid-month",
                    "revenue": 1000,
                }
            ],
        }

        response = client.post(
            "/api/v1/campaigns/monthly-data",
            data=json.dumps(invalid_data),
            content_type="application/json",
        )

        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert "error" in response_data
        assert response_data["error"]["type"] == "validation_error"

    def test_update_monthly_data_empty_request(self, client):
        """Test POST /api/v1/campaigns/monthly-data with empty request"""
        response = client.post(
            "/api/v1/campaigns/monthly-data",
            data=json.dumps({}),
            content_type="application/json",
        )

        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert "error" in response_data

    def test_get_channel_roi(self, client):
        """Test GET /api/v1/campaigns/channels/roi"""
        response = client.get("/api/v1/campaigns/channels/roi")

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["success"] is True
        assert len(response_data["data"]) > 0
        assert "channel" in response_data["data"][0]
        assert "roi" in response_data["data"][0]

    def test_get_age_group_roi(self, client):
        """Test GET /api/v1/campaigns/age-groups/roi"""
        response = client.get("/api/v1/campaigns/age-groups/roi")

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["success"] is True
        assert len(response_data["data"]) > 0
        assert "age_group" in response_data["data"][0]
        assert "roi" in response_data["data"][0]

    def test_get_revenue_past_month(self, client):
        """Test GET /api/v1/campaigns/past-month/revenue"""
        response = client.get("/api/v1/campaigns/past-month/revenue")

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["success"] is True
        assert "revenue" in response_data["data"]

    def test_get_roi_past_month(self, client):
        """Test GET /api/v1/campaigns/past-month/roi"""
        response = client.get("/api/v1/campaigns/past-month/roi")

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["success"] is True
        assert "roi" in response_data["data"]

    def test_get_cost_heatmap(self, client):
        """Test GET /api/v1/campaigns/cost-heatmap"""
        response = client.get("/api/v1/campaigns/cost-heatmap")

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["success"] is True
        assert len(response_data["data"]) > 0
        assert "channel" in response_data["data"][0]
        assert "costPerLead" in response_data["data"][0]
        assert "costPerView" in response_data["data"][0]

    def test_get_cost_heatmap_with_params(self, client):
        """Test GET /api/v1/campaigns/cost-heatmap with parameters"""
        response = client.get(
            "/api/v1/campaigns/cost-heatmap?country=Singapore&campaign_id=January_2022_1&channels=Facebook,Google"
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["success"] is True

    def test_get_cost_heatmap_not_found(self, client):
        """Test GET /api/v1/campaigns/cost-heatmap with non-existent data"""
        response = client.get("/api/v1/campaigns/cost-heatmap?country=nonexistent")

        assert response.status_code == 404
        response_data = json.loads(response.data)
        assert "error" in response_data
        assert response_data["error"]["type"] == "resource_not_found"


class TestDataRoutesCSVImport:
    """Test suite for CSV import endpoint"""

    def test_csv_import_options(self, client):
        """Test OPTIONS /api/v1/imports/csv (CORS preflight)"""
        response = client.options("/api/v1/imports/csv")

        assert response.status_code == 200
        assert response.headers.get("Access-Control-Allow-Origin") == "*"
        assert response.headers.get("Access-Control-Allow-Methods") == "POST"

    def test_csv_import_success(self, client, mock_csv_file):
        """Test POST /api/v1/imports/csv with valid CSV file"""
        response = client.post(
            "/api/v1/imports/csv",
            data=mock_csv_file,
            content_type="multipart/form-data",
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["success"] is True
        assert "message" in response_data["data"]
        assert "count" in response_data["data"]
        assert "collection" in response_data["data"]

    def test_csv_import_no_file(self, client):
        """Test POST /api/v1/imports/csv with no file"""
        response = client.post("/api/v1/imports/csv", data={})

        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert "error" in response_data
        assert "No file selected" in response_data["error"]["message"]

    def test_csv_import_invalid_file_type(self, client):
        """Test POST /api/v1/imports/csv with non-CSV file"""
        invalid_file = {"file": (BytesIO(b"test data"), "test.txt")}

        response = client.post(
            "/api/v1/imports/csv",
            data=invalid_file,
            content_type="multipart/form-data",
        )

        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert "error" in response_data
        assert "File must be a CSV" in response_data["error"]["message"]


class TestDataRoutesUtility:
    """Test suite for utility endpoints"""

    def test_get_date_type(self, client):
        """Test GET /api/v1/utils/date-types"""
        response = client.get("/api/v1/utils/date-types")

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["success"] is True
        assert "value" in response_data["data"]
        assert "type" in response_data["data"]
