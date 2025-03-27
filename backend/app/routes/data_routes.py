import logging
from flask import Blueprint, jsonify, make_response, request
from app.utils.data_processing import (
    process_csv_data,
    find_matching_collection,
    get_db_structure,
)
from app.models.campaign import get_revenue_by_date

# Create blueprint
data_bp = Blueprint("data_routes", __name__)
logger = logging.getLogger(__name__)


@data_bp.route("/api/db-structure", methods=["GET"])
def db_structure():
    """
    Retrieve the structure of all databases and their collections.
    """
    try:
        structure = get_db_structure()
        return jsonify(structure)
    except Exception as e:
        logger.error(f"Error getting database structure: {e}")
        return jsonify({"error": str(e)}), 500


@data_bp.route("/api/upload-csv", methods=["POST", "OPTIONS"])
def upload_csv():
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
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        if not file.filename.endswith(".csv"):
            return jsonify({"error": "File must be a CSV"}), 400

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
                return (
                    jsonify({"error": "No valid records found after validation"}),
                    400,
                )

            # Insert all records into MongoDB
            result = matching_collection.insert_many(records)
            logger.info(
                f"Successfully inserted {len(result.inserted_ids)} records into {collection_name}"
            )

            # Determine operation type for response message
            operation = "appended to existing" if found_match else "uploaded to new"

            # Prepare and send response
            response = jsonify(
                {
                    "message": f"CSV {operation} collection successfully",
                    "count": len(result.inserted_ids),
                    "collection": collection_name,
                }
            )
            response.headers.add("Access-Control-Allow-Origin", "*")
            return response

        except UnicodeDecodeError:
            logger.error("Invalid CSV file encoding")
            return (
                jsonify({"error": "Invalid CSV file encoding. Please use UTF-8"}),
                400,
            )
        except ValueError as e:
            logger.error(f"CSV validation error: {e}")
            return jsonify({"error": str(e)}), 400

    except Exception as e:
        logger.error(f"Error uploading CSV: {e}")
        return jsonify({"error": str(e)}), 500


@data_bp.route("/api/revenue_data", methods=["GET"])
def revenue_data():
    """Get aggregated revenue data for charting"""
    try:
        data_summary = get_revenue_by_date()
        return jsonify(data_summary)
    except Exception as e:
        logger.error(f"Error retrieving revenue data: {e}")
        return jsonify({"error": str(e)}), 500
