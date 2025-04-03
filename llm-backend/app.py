from typing import Dict, Union

from flask import Flask, jsonify, request
from flask_cors import CORS

from config import CORS_CONFIG, DEBUG, HOST, PORT
from mypackage.d_report_generator import ReportResults
from mypackage.utils.database import Database
from mypackage.utils.logging_config import setup_logging
from pipeline import main as run_pipeline

logger = setup_logging("llm_backend")
app = Flask(__name__)

CORS(app, **CORS_CONFIG)
Database.initialize()


@app.route("/api/query", methods=["POST"])
def process_query():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    data = request.get_json()
    if "query" not in data:
        return jsonify({"error": "Query field is required"}), 400
    query = data["query"]
    try:
        result: Dict[str, Union[str, ReportResults]] = run_pipeline(query)
        response = {"output": result, "original_query": query}
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/health", methods=["GET"])
def health_check():
    if Database.db is None:
        success = Database.initialize()
        if not success:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Database connection failed",
                        "healthy": False,
                    }
                ),
                503,
            )
    collections = Database.list_collections()
    if not collections:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "No accessible collections found",
                    "healthy": False,
                }
            ),
            503,
        )
    return (
        jsonify(
            {
                "status": "ok",
                "message": "Database is healthy and collections exist",
                "healthy": True,
                "collections_count": len(collections),
            }
        ),
        200,
    )


if __name__ == "__main__":
    app.run(debug=DEBUG, host=HOST, port=PORT)
