from typing import Union
import os
from flask import Flask, jsonify, request
from flask_cors import CORS

from mypackage.c_regular_generator import ChartDataType
from mypackage.d_report_generator import ReportResults
from mypackage.utils.database import Database
from mypackage.utils.logging_config import setup_logging
from pipeline import main as run_pipeline

from config import DEBUG, HOST, PORT, CORS_CONFIG

# Setup logging
logger = setup_logging("llm_backend")

# Initialize Flask app
app = Flask(__name__)
CORS(app, **CORS_CONFIG)

# Initialize database connection
Database.initialize()


@app.route("/api/query", methods=["POST"])
def process_query():
    """
    Endpoint to process queries through the pipeline
    Expects a JSON body with format: {"query": "your query here"}
    """
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    if "query" not in data:
        return jsonify({"error": "Query field is required"}), 400

    query = data["query"]
    try:
        result: Union[str, ChartDataType, ReportResults] = run_pipeline(query)

        # Convert the result to a JSON-serializable format
        response = {"output": result, "original_query": query}

        return jsonify(response)

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "database": Database.client is not None}), 200


@app.route("/api/collections", methods=["GET"])
def list_collections():
    """List available MongoDB collections"""
    try:
        collections = Database.list_collections()
        return jsonify({"collections": collections}), 200
    except Exception as e:
        logger.error(f"Error listing collections: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=DEBUG, host=HOST, port=PORT)
