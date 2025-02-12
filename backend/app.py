from flask import Flask, jsonify
from pymongo import MongoClient
import os

app = Flask(__name__)

# MongoDB connection
mongo_uri = os.getenv('MONGO_URI', 'mongodb://root:example@mongodb:27017/')
client = MongoClient(mongo_uri)
db = client.test_database

@app.route('/')
def hello():
    return jsonify({"message": "Hello from Python Backend!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000))) 