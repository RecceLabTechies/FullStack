import csv
import json
import os
import re
from io import StringIO

import pandas as pd
from bson import json_util
from flask import Flask, jsonify, make_response, request
from flask_cors import CORS
from pymongo import MongoClient
from werkzeug.utils import secure_filename

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
    clicks_collection = db.clicks
    print("Successfully connected to MongoDB")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")


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
        print(f"Error getting database structure: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/upload-csv", methods=["POST", "OPTIONS"])
def upload_csv():
    """
    Handle CSV file uploads and import data into MongoDB.

    Supports OPTIONS request for CORS preflight.
    For POST requests:
    1. Validates the uploaded file (must be CSV)
    2. Reads the CSV content using UTF-8 encoding
    3. Creates a new collection named after the file
    4. Imports all CSV records as documents

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

            # Create new collection for the CSV data
            collection_name = secure_filename(file.filename).replace(".csv", "")
            collection = db[collection_name]

            # Convert to list and validate content
            records = list(csv_reader)
            if not records:
                return jsonify({"error": "CSV file is empty"}), 400

            # Insert all records into MongoDB
            result = collection.insert_many(records)

            # Prepare and send response
            response = jsonify(
                {
                    "message": "CSV uploaded successfully",
                    "count": len(result.inserted_ids),
                    "collection": collection_name,
                }
            )
            response.headers.add("Access-Control-Allow-Origin", "*")
            return response

        except UnicodeDecodeError:
            return (
                jsonify({"error": "Invalid CSV file encoding. Please use UTF-8"}),
                400,
            )
        except csv.Error as e:
            return jsonify({"error": f"Invalid CSV format: {str(e)}"}), 400

    except Exception as e:
        print(f"Error uploading CSV: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/campaign_data_mock", methods=["GET"])
def get_data_for_leads_date_chart():
    try:
        collection = db["campaign_data_mock"]
        data = list(collection.find({}, {"_id": 0}))
        df = pd.DataFrame(data)
        df = df[["date", "leads"]]
        df["leads"] = df["leads"].astype(int)
        df_grouped = df.groupby("date", as_index=False).sum()
        df_grouped = df_grouped.sort_values("date").tail(7)

        data_summary = df_grouped.to_dict(orient="records")

        return jsonify(data_summary)
    except Exception as e:
        print(f"Error retrieving data summary: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/revenue_data", methods=["GET"])
def get_data_for_revenue_date_chart():
    try:
        collection = db["campaign_data_mock"]
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
        print(f"Error retrieving revenue data: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/users", methods=["GET"])
def get_users():
    """
    Retrieve all users from the 'users' collection in the database.
    """
    try:
        # Access the 'users' collection
        users_collection = db["users"]
        users = list(
            users_collection.find({}, {"_id": 0})
        )  # Exclude the ObjectId from the response
        return jsonify(users)
    except Exception as e:
        print(f"Error retrieving users: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/users", methods=["POST"])
def add_user():
    """
    Add a new user to the 'users' collection in the database.
    Expects a JSON payload with user details.
    """
    try:
        user_data = request.json
        # Validate required fields
        required_fields = [
            "username",
            "email",
            "role",
            "company",
            "password",
            "chart_access",
            "report_generation_access",
            "user_management_access",
        ]
        if not all(field in user_data for field in required_fields):
            return jsonify({"error": "Missing required user fields"}), 400

        # Access the 'users' collection
        users_collection = db["users"]
        result = users_collection.insert_one(user_data)
        return jsonify(
            {"message": "User added successfully", "id": str(result.inserted_id)}
        )
    except Exception as e:
        print(f"Error adding user: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/user", methods=["GET"])
def get_user_by_username():
    """
    Retrieve a user's information from the 'users' collection based on the username.
    Expects a query parameter 'username'.
    """
    try:
        username = request.args.get("username")
        if not username:
            return jsonify({"error": "Username query parameter is required"}), 400

        # Access the 'users' collection
        users_collection = db["users"]
        user = users_collection.find_one(
            {"username": username}, {"_id": 0}
        )  # Exclude the ObjectId from the response

        if user:
            return jsonify(user)
        else:
            return jsonify({"error": "User not found"}), 404
    except Exception as e:
        print(f"Error retrieving user: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/data_synth_22mar/filters", methods=["GET"])
def get_data_synth_filters():
    try:
        collection = db["data_synth_22mar"]

        # Use MongoDB's distinct() to get unique values for each field
        countries = collection.distinct("country")
        age_groups = collection.distinct("age_group")
        channels = collection.distinct("channel")

        return jsonify(
            {"countries": countries, "age_groups": age_groups, "channels": channels}
        )
    except Exception as e:
        print(f"Error getting filters: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/filter-data", methods=["POST"])
def filter_data():
    data = request.json
    query = {}

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

    if from_date and to_date:
        try:
            # Wrap the match condition in $expr so MongoDB can evaluate dates
            results = list(
                db["data_synth_22mar"].find(
                    {
                        "$and": [
                            query,
                            {
                                "$expr": {
                                    "$and": [
                                        {
                                            "$gte": [
                                                {
                                                    "$dateFromString": {
                                                        "dateString": "$Date"
                                                    }
                                                },
                                                {
                                                    "$dateFromString": {
                                                        "dateString": from_date
                                                    }
                                                },
                                            ]
                                        },
                                        {
                                            "$lte": [
                                                {
                                                    "$dateFromString": {
                                                        "dateString": "$Date"
                                                    }
                                                },
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
            return jsonify(results)
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    results = list(db["data_synth_22mar"].find(query, {"_id": 0}))
    return jsonify(results)


@app.route("/api/inspect-date-type", methods=["GET"])
def inspect_date_type():
    try:
        # Fetch one sample document
        sample = db["data_synth_22mar"].find_one({}, {"Date": 1, "_id": 0})

        if not sample or "Date" not in sample:
            return jsonify({"message": "No Date field found in sample."}), 404

        date_value = sample["Date"]
        return jsonify({"value": date_value, "type": str(type(date_value))})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Start the Flask development server
    app.run(host=HOST, port=PORT, debug=DEBUG)
