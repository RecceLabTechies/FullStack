from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
import os
from datetime import datetime
from bson import ObjectId, json_util
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# MongoDB connection
try:
    mongo_uri = os.getenv('MONGO_URI', 'mongodb://root:example@mongodb:27017/')
    client = MongoClient(mongo_uri)
    # Test the connection
    client.server_info()
    db = client.test_database
    clicks_collection = db.clicks
    print("Successfully connected to MongoDB")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")

@app.route('/')
def hello():
    return jsonify({"message": "Hello from Python Backend!"})

@app.route('/api/click', methods=['POST'])
def add_click():
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=True) 