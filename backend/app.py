from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from pymongo import MongoClient
import os
from datetime import datetime
from bson import ObjectId, json_util
import json
import csv
from io import StringIO
from werkzeug.utils import secure_filename

# Initialize Flask application
app = Flask(__name__)

# Configure Cross-Origin Resource Sharing (CORS) to allow frontend requests
# Update CORS configuration to explicitly allow file uploads
CORS(app, resources={
    r"/*": {
        "origins": "*",  # Allow all origins
        "methods": ["GET", "POST", "OPTIONS"],  # Allowed HTTP methods
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"]  # Allowed headers
    }
})

# Increase maximum content length to allow larger file uploads
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Set up MongoDB connection
try:
    # Get MongoDB connection URI from environment variable or use default
    mongo_uri = os.getenv('MONGO_URI', 'mongodb://root:example@mongodb:27017/')
    client = MongoClient(mongo_uri)
    # Test the connection by requesting server info
    client.server_info()
    db = client.test_database
    clicks_collection = db.clicks
    print("Successfully connected to MongoDB")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")

@app.route('/')
def hello():
    """Simple endpoint to verify the API is running."""
    return jsonify({"message": "Hello from Python Backend!"})

@app.route('/api/click', methods=['POST'])
def add_click():
    """
    Record a new click event in the database.
    
    Creates a document with current timestamp and a message.
    Returns the ID of the inserted document.
    """
    try:
        click_data = {
            'timestamp': datetime.now(),
            'message': 'Button clicked!'
        }
        result = clicks_collection.insert_one(click_data)
        return jsonify({"message": "Click recorded!", "id": str(result.inserted_id)})
    except Exception as e:
        print(f"Error adding click: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/clicks', methods=['GET'])
def get_clicks():
    """
    Retrieve all click events from the database.
    
    Formats the MongoDB documents to be JSON serializable by converting:
    - ObjectId to string
    - datetime to ISO format string
    """
    try:
        clicks = list(clicks_collection.find())
        # Convert ObjectId and datetime to string for JSON serialization
        formatted_clicks = []
        for click in clicks:
            formatted_clicks.append({
                '_id': str(click['_id']),
                'timestamp': click['timestamp'].isoformat(),
                'message': click['message']
            })
        return jsonify(formatted_clicks)
    except Exception as e:
        print(f"Error getting clicks: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/db-structure', methods=['GET'])
def get_db_structure():
    """
    Retrieve the structure of all databases and their collections.
    
    For each non-system database:
    1. Lists all collections
    2. Gets a sample document from each collection
    3. Converts BSON to JSON-serializable format
    
    Skips system databases (admin, local, config)
    """
    try:
        structure = {}
        # Get list of all databases
        database_list = client.list_database_names()
        
        for db_name in database_list:
            # Skip system databases
            if db_name not in ['admin', 'local', 'config']:
                db = client[db_name]
                structure[db_name] = {}
                
                # Get all collections in the database
                collections = db.list_collection_names()
                
                for collection_name in collections:
                    collection = db[collection_name]
                    # Get a sample document to understand the structure
                    sample_doc = collection.find_one()
                    if sample_doc:
                        # Convert ObjectId to string for JSON serialization
                        sample_doc = json.loads(json_util.dumps(sample_doc))
                        structure[db_name][collection_name] = sample_doc
                    else:
                        structure[db_name][collection_name] = "Empty Collection"
        
        return jsonify(structure)
    except Exception as e:
        print(f"Error getting database structure: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/upload-csv', methods=['POST', 'OPTIONS'])
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
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

    try:
        # Validate file presence in request
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({"error": "File must be a CSV"}), 400

        # Process the CSV file
        try:
            # Read and decode the file content
            file_content = file.read()
            text_content = file_content.decode('utf-8')
            stream = StringIO(text_content)
            csv_reader = csv.DictReader(stream)
            
            # Create new collection for the CSV data
            collection_name = secure_filename(file.filename).replace('.csv', '')
            collection = db[collection_name]
            
            # Convert to list and validate content
            records = list(csv_reader)
            if not records:
                return jsonify({"error": "CSV file is empty"}), 400
                
            # Insert all records into MongoDB
            result = collection.insert_many(records)
            
            # Prepare and send response
            response = jsonify({
                "message": "CSV uploaded successfully",
                "count": len(result.inserted_ids),
                "collection": collection_name
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response

        except UnicodeDecodeError:
            return jsonify({"error": "Invalid CSV file encoding. Please use UTF-8"}), 400
        except csv.Error as e:
            return jsonify({"error": f"Invalid CSV format: {str(e)}"}), 400

    except Exception as e:
        print(f"Error uploading CSV: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Start the Flask development server
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=True) 