import csv
import json
import logging
import os
from datetime import date, datetime
from io import StringIO

import pandas as pd
from bson import json_util
from data_types import UserData
from flask import Flask, jsonify, make_response, request
from flask_cors import CORS
from pymongo import MongoClient
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize Flask application
app = Flask(__name__)

# Configure Cross-Origin Resource Sharing (CORS) to allow frontend requests
# Update CORS configuration to explicitly allow file uploads
CORS(
    app,
    resources={
        r"/*": {
            "origins": "*",  # Allow all origins
            "methods": ["GET", "POST", "OPTIONS"],  # Allowed HTTP methods
            "allow_headers": [
                "Content-Type",
                "Authorization",
                "X-Requested-With",
            ],  # Allowed headers
        }
    },
)

# Increase maximum content length to allow larger file uploads
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size

# Set up MongoDB connection
try:
    # Get MongoDB connection URI from environment variable or use default
    mongo_uri = os.getenv("MONGO_URI", "mongodb://root:example@mongodb:27017/")
    client = MongoClient(mongo_uri)
    # Test the connection by requesting server info
    client.server_info()
    db = client.test_database
    users_collection = db.users
    campaign_performance_collection = db.campaign_performance
    logger.info("Successfully connected to MongoDB")
except Exception as e:
    logger.error(f"Error connecting to MongoDB: {e}")


@app.route("/api/db-structure", methods=["GET"])
def get_db_structure():
    """
    Retrieve the structure of all databases and their collections.

    For each non-system database:
    1. Lists all collections
    2. Gets up to 10 sample documents from each collection
    3. Converts BSON to JSON-serializable format

    Skips system databases (admin, local, config)
    """
    try:
        structure = {}
        # Get list of all databases
        database_list = client.list_database_names()

        for db_name in database_list:
            # Skip system databases
            if db_name not in ["admin", "local", "config"]:
                db = client[db_name]
                structure[db_name] = {}

                # Get all collections in the database
                collections = db.list_collection_names()

                for collection_name in collections:
                    collection = db[collection_name]
                    # Get up to 10 documents to display
                    sample_docs = list(collection.find().limit(10))
                    if sample_docs:
                        # Convert ObjectId to string for JSON serialization
                        sample_docs = json.loads(json_util.dumps(sample_docs))
                        structure[db_name][collection_name] = sample_docs
                    else:
                        structure[db_name][collection_name] = "Empty Collection"

        return jsonify(structure)
    except Exception as e:
        logger.error(f"Error getting database structure: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/upload-csv", methods=["POST", "OPTIONS"])
def upload_csv():
    """
    Handle CSV file uploads and import data into MongoDB.

    Supports OPTIONS request for CORS preflight.
    For POST requests:
    1. Validates the uploaded file (must be CSV)
    2. Reads the CSV content using UTF-8 encoding
    3. Checks if the data schema matches any existing collection or known data models
    4. Applies appropriate type conversions based on data model and MongoDB schema requirements
    5. Appends data to matching collection or creates a new one if no match
    6. Imports all CSV records as documents

    Returns count of imported records and collection name.
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
            # Read and decode the file content
            file_content = file.read()
            text_content = file_content.decode("utf-8")
            stream = StringIO(text_content)
            csv_reader = csv.DictReader(stream)

            # Convert to list and validate content
            records = list(csv_reader)
            if not records:
                return jsonify({"error": "CSV file is empty"}), 400

            # Extract the schema (field names) from the CSV
            csv_field_names = set(records[0].keys())

            # Check if this matches known data models
            is_campaign_data = False
            campaign_fields = {
                "date",
                "campaign_id",
                "channel",
                "age_group",
                "ad_spend",
                "views",
                "leads",
                "new_accounts",
                "country",
                "revenue",
            }

            # Check if this is CampaignData
            if csv_field_names == campaign_fields:
                is_campaign_data = True
                logger.info("CSV matches CampaignData schema")

                # Apply type conversions from CampaignData based on MongoDB schema requirements
                for record in records:
                    # Convert date string to datetime object for MongoDB
                    if "date" in record and record["date"]:
                        try:
                            # Parse date string in YYYY-MM-DD format
                            date_parts = record["date"].split("-")
                            if len(date_parts) == 3:
                                year, month, day = map(int, date_parts)
                                # Use datetime instead of date for MongoDB compatibility
                                record["date"] = datetime(year, month, day)
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Error converting date field: {e}")
                            # Skip records with invalid dates to avoid MongoDB validation errors
                            continue

                    # Convert numeric fields to float (double in MongoDB) as required by schema
                    for field in [
                        "ad_spend",
                        "views",
                        "leads",
                        "new_accounts",
                        "revenue",
                    ]:
                        if field in record:
                            try:
                                record[field] = (
                                    float(record[field]) if record[field] else 0.0
                                )
                            except (ValueError, TypeError):
                                record[field] = (
                                    0.0  # Default to 0.0 if conversion fails
                                )

                # Set default collection name for campaign data
                default_collection_name = "campaign_performance"
            else:
                default_collection_name = secure_filename(file.filename).replace(
                    ".csv", ""
                )

            # Check if this schema matches any existing collection
            matching_collection = None
            collection_name = None
            found_match = False

            # Get all collections in the database
            collections = db.list_collection_names()

            for coll_name in collections:
                # Skip matching if this is campaign data - we always use campaign_performance
                if is_campaign_data and coll_name == "campaign_performance":
                    matching_collection = db[coll_name]
                    collection_name = coll_name
                    found_match = True
                    logger.info("Using existing campaign_performance collection")
                    break

                # For non-campaign data, check schema match with existing collections
                if not is_campaign_data:
                    # Get a sample document to check schema
                    sample_doc = db[coll_name].find_one({}, {"_id": 0})

                    if sample_doc:
                        # Extract the field names from the sample document
                        collection_field_names = set(sample_doc.keys())

                        # Check if the field names match
                        if csv_field_names == collection_field_names:
                            matching_collection = db[coll_name]
                            collection_name = coll_name
                            found_match = True
                            logger.info(f"Found matching collection: {collection_name}")
                            break

            # If no matching collection found, create a new one
            if not found_match:
                # For CampaignData, use "campaign_performance" as the collection name
                if is_campaign_data:
                    collection_name = "campaign_performance"
                else:
                    collection_name = default_collection_name

                matching_collection = db[collection_name]
                logger.info(f"Creating new collection: {collection_name}")

            # Filter out any records with missing required fields for campaign data
            if is_campaign_data:
                original_count = len(records)
                valid_records = []
                for record in records:
                    if all(
                        field in record and record[field] is not None
                        for field in campaign_fields
                    ):
                        valid_records.append(record)
                records = valid_records
                if len(records) < original_count:
                    logger.warning(
                        f"Filtered out {original_count - len(records)} invalid records"
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
        except csv.Error as e:
            logger.error(f"CSV format error: {e}")
            return jsonify({"error": f"Invalid CSV format: {str(e)}"}), 400

    except Exception as e:
        logger.error(f"Error uploading CSV: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/revenue_data", methods=["GET"])
def get_data_for_revenue_date_chart():
    try:
        collection = db["campaign_performance"]
        data = list(collection.find({}, {"_id": 0}))
        df = pd.DataFrame(data)
        df = df[["date", "revenue"]]
        df["revenue"] = df["revenue"].astype(
            float
        )  # Convert to float for decimal values
        df_grouped = df.groupby("date", as_index=False).sum()
        df_grouped = df_grouped.sort_values("date").tail(7)

        data_summary = df_grouped.to_dict(orient="records")

        return jsonify(data_summary)
    except Exception as e:
        logger.error(f"Error retrieving revenue data: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/users", methods=["GET"])
def get_users():
    """
    Retrieve all users from the 'users' collection in the database.
    Converts database documents to validated UserData objects.
    """
    try:
        # Access the 'users' collection
        users_raw = list(users_collection.find({}, {"_id": 0}))

        # Convert raw data to UserData objects for validation and proper typing
        users = []
        for user_raw in users_raw:
            # Create UserData object which automatically handles type conversions
            user_obj = UserData(**user_raw)
            # Convert back to dict for JSON serialization
            users.append(
                {
                    "username": user_obj.username,
                    "email": user_obj.email,
                    "role": user_obj.role,
                    "company": user_obj.company,
                    "password": user_obj.password,
                    "chart_access": user_obj.chart_access,
                    "report_generation_access": user_obj.report_generation_access,
                    "user_management_access": user_obj.user_management_access,
                }
            )

        return jsonify(users)
    except Exception as e:
        logger.error(f"Error retrieving users: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/users", methods=["POST"])
def add_user():
    """
    Add a new user to the 'users' collection in the database.
    Uses UserData class for validation of the input data.
    """
    try:
        user_data = request.json

        # Validate through UserData class (will raise exceptions if types don't match)
        try:
            # Create UserData object which automatically validates and converts types
            user_obj = UserData(**user_data)
        except (TypeError, ValueError) as e:
            logger.warning(f"Invalid user data received: {e}")
            return jsonify({"error": f"Invalid user data: {str(e)}"}), 400

        # Convert to dict for database insertion
        validated_user_data = {
            "username": user_obj.username,
            "email": user_obj.email,
            "role": user_obj.role,
            "company": user_obj.company,
            "password": user_obj.password,
            "chart_access": user_obj.chart_access,
            "report_generation_access": user_obj.report_generation_access,
            "user_management_access": user_obj.user_management_access,
        }

        # Access the 'users' collection
        result = users_collection.insert_one(validated_user_data)
        logger.info(f"Added user: {user_obj.username}")
        return jsonify(
            {"message": "User added successfully", "id": str(result.inserted_id)}
        )
    except Exception as e:
        logger.error(f"Error adding user: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/user", methods=["GET"])
def get_user_by_username():
    """
    Retrieve a user's information from the 'users' collection based on the username.
    Converts to UserData object for validation and proper typing.
    """
    try:
        username = request.args.get("username")
        if not username:
            return jsonify({"error": "Username query parameter is required"}), 400

        # Access the 'users' collection
        user_raw = users_collection.find_one(
            {"username": username}, {"_id": 0}
        )  # Exclude the ObjectId from the response
        if user_raw:
            # Create UserData object which automatically handles type conversions
            user_obj = UserData(**user_raw)
            # Convert back to dict for JSON serialization
            user = {
                "username": user_obj.username,
                "email": user_obj.email,
                "role": user_obj.role,
                "company": user_obj.company,
                "password": user_obj.password,
                "chart_access": user_obj.chart_access,
                "report_generation_access": user_obj.report_generation_access,
                "user_management_access": user_obj.user_management_access,
            }
            return jsonify(user)
        else:
            logger.info(f"User not found: {username}")
            return jsonify({"error": "User not found"}), 404
    except Exception as e:
        logger.error(f"Error retrieving user: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Start the Flask development server
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
