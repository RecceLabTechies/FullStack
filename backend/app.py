from flask import Flask, jsonify
from flask_cors import CORS
from pymongo import MongoClient

app = Flask(__name__)
CORS(app)

# MongoDB connection
client = MongoClient('mongodb://mongodb:27017/')
db = client.mydatabase

@app.route('/api/test')
def test():
    return jsonify({"message": "Backend is working!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000) 