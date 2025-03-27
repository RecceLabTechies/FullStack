import logging
import re
from flask import Blueprint, jsonify, make_response, request
from functools import wraps
from app.utils.data_processing import (
    process_csv_data,
    find_matching_collection,
    get_db_structure,
)
from app.models.campaign import get_revenue_by_date
from app.database.connection import get_campaign_performance_collection

# Create blueprint
data_bp = Blueprint("data_routes", __name__)
logger = logging.getLogger(__name__)


# ----------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------


def handle_exceptions(f):
    """Decorator to standardize exception handling for routes"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {e}")
            return jsonify({"error": str(e)}), 500

    return decorated_function


def format_response(data, status_code=200, headers=None):
    """Standardize API response format"""
    response = jsonify(data)

    if headers:
        for key, value in headers.items():
            response.headers.add(key, value)

    return response, status_code


# ----------------------------------------------------------------
# Database structure endpoints
# ----------------------------------------------------------------


@data_bp.route("/api/v1/database-structures", methods=["GET"])
@handle_exceptions
def get_database_structures():
    """
    Retrieve the structure of all databases and their collections.
    """
    structure = get_db_structure()
    return format_response(structure)


# ----------------------------------------------------------------
# Campaign data endpoints
# ----------------------------------------------------------------


@data_bp.route("/api/v1/campaigns/filter-options", methods=["GET"])
@handle_exceptions
def get_campaign_filters():
    """
    Get unique filter values for campaign data (countries, age groups, and channels).
    """
    collection = get_campaign_performance_collection()

    # Use MongoDB's distinct() to get unique values for each field
    countries = collection.distinct("country")
    age_groups = collection.distinct("age_group")
    channels = collection.distinct("channel")

    return format_response(
        {"countries": countries, "age_groups": age_groups, "channels": channels}
    )


@data_bp.route("/api/v1/campaigns", methods=["POST"])
@handle_exceptions
def filter_campaigns():
    """
    Filter campaign data based on specified criteria including channels, countries,
    age groups, and date range.
    """
    data = request.json
    query = {}

    # Build filter query based on provided criteria
    if data.get("channels"):
        query["channel"] = {
            "$in": [
                re.compile(f"^{c.replace('-', ' ')}$", re.IGNORECASE)
                for c in data["channels"]
            ]
        }

    if data.get("countries"):
        query["country"] = {
            "$in": [
                re.compile(f"^{c.replace('-', ' ')}$", re.IGNORECASE)
                for c in data["countries"]
            ]
        }

    if data.get("ageGroups"):
        query["age_group"] = {"$in": data["ageGroups"]}

    from_date = data.get("from")
    to_date = data.get("to")
    collection = get_campaign_performance_collection()

    # Apply date range filtering if provided
    if from_date and to_date:
        try:
            # Wrap the match condition in $expr so MongoDB can evaluate dates
            results = list(
                collection.find(
                    {
                        "$and": [
                            query,
                            {
                                "$expr": {
                                    "$and": [
                                        {
                                            "$gte": [
                                                "$date",
                                                {
                                                    "$dateFromString": {
                                                        "dateString": from_date
                                                    }
                                                },
                                            ]
                                        },
                                        {
                                            "$lte": [
                                                "$date",
                                                {
                                                    "$dateFromString": {
                                                        "dateString": to_date
                                                    }
                                                },
                                            ]
                                        },
                                    ]
                                }
                            },
                        ]
                    },
                    {"_id": 0},
                )
            )
            return format_response(results)
        except Exception as e:
            logger.error(f"Error filtering data with date range: {e}")
            return format_response({"error": str(e)}, 400)

    # Execute query without date filtering
    results = list(collection.find(query, {"_id": 0}))
    return format_response(results)


@data_bp.route("/api/v1/revenues", methods=["GET"])
@handle_exceptions
def get_revenue_data():
    """Get aggregated revenue data for charting"""
    data_summary = get_revenue_by_date()
    return format_response(data_summary)


# ----------------------------------------------------------------
# CSV import endpoints
# ----------------------------------------------------------------


@data_bp.route("/api/v1/csv-imports", methods=["POST", "OPTIONS"])
def handle_csv_import():
    """
    Handle CSV file uploads and import data into MongoDB.
    """
    # Handle CORS preflight request
    if request.method == "OPTIONS":
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "*")
        response.headers.add("Access-Control-Allow-Methods", "POST")
        return response

    try:
        # Validate file presence in request
        if "file" not in request.files:
            return format_response({"error": "No file provided"}, 400)

        file = request.files["file"]
        if file.filename == "":
            return format_response({"error": "No file selected"}, 400)

        if not file.filename.endswith(".csv"):
            return format_response({"error": "File must be a CSV"}, 400)

        # Process the CSV file
        try:
            # Process CSV data
            records, is_campaign_data, default_collection_name = process_csv_data(file)

            # Find matching collection for data
            matching_collection, collection_name, found_match = (
                find_matching_collection(
                    records, is_campaign_data, default_collection_name
                )
            )

            # Check if we have any valid records to insert
            if not records:
                logger.error("No valid records found after validation")
                return format_response(
                    {"error": "No valid records found after validation"}, 400
                )

            # Insert all records into MongoDB
            result = matching_collection.insert_many(records)
            logger.info(
                f"Successfully inserted {len(result.inserted_ids)} records into {collection_name}"
            )

            # Determine operation type for response message
            operation = "appended to existing" if found_match else "uploaded to new"

            # Prepare and send response
            return format_response(
                {
                    "message": f"CSV {operation} collection successfully",
                    "count": len(result.inserted_ids),
                    "collection": collection_name,
                },
                headers={"Access-Control-Allow-Origin": "*"},
            )

        except UnicodeDecodeError:
            logger.error("Invalid CSV file encoding")
            return format_response(
                {"error": "Invalid CSV file encoding. Please use UTF-8"}, 400
            )
        except ValueError as e:
            logger.error(f"CSV validation error: {e}")
            return format_response({"error": str(e)}, 400)

    except Exception as e:
        logger.error(f"Error uploading CSV: {e}")
        return format_response({"error": str(e)}, 500)


# ----------------------------------------------------------------
# Utility endpoints
# ----------------------------------------------------------------


@data_bp.route("/api/v1/date-types", methods=["GET"])
@handle_exceptions
def inspect_date_type():
    """
    Utility endpoint to inspect the date field data type in the campaign collection.
    """
    collection = get_campaign_performance_collection()

    # Fetch one sample document
    sample = collection.find_one({}, {"date": 1, "_id": 0})

    if not sample or "date" not in sample:
        logger.warning("No date field found in sample document")
        return format_response({"message": "No date field found in sample."}, 404)

    date_value = sample["date"]
    return format_response({"value": date_value, "type": str(type(date_value))})
