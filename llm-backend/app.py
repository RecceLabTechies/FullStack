"""
LLM Backend API Application

This Flask application provides a RESTful API for processing analytical queries
using a pipeline of LLM-powered components. It serves as the entry point for HTTP
requests and handles request validation, processing, and response formatting.

The application exposes endpoints for:
- Processing queries via the main pipeline
- Health checking the application and its database connection

The API is CORS-enabled for cross-origin requests and uses JSON for all request
and response data.
"""

import base64
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
    """
    Process an analytical query submitted via POST request.

    This endpoint accepts a JSON payload with a 'query' field containing the
    user's analytical query. It validates the request format, processes the
    query through the main pipeline, and returns the results.

    Expected Request Format:
        {
            "query": "String containing the user's analytical question"
        }

    Response Format:
        {
            "output": {
                "type": "chart|description|report|error",
                "result": <base64-encoded bytes for charts, text, or error message>
            },
            "original_query": "The original query string"
        }

    Returns:
        JSON response with results or error message
        HTTP 400 for malformed requests
        HTTP 500 for server-side errors
    """
    # Validate that the request contains JSON
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    # Extract and validate the query field
    data = request.get_json()
    if "query" not in data:
        return jsonify({"error": "Query field is required"}), 400

    query = data["query"]
    logger.info(f"Received query: '{query}'")

    # Process the query through the pipeline
    try:
        result: Dict[str, Union[str, bytes, ReportResults]] = run_pipeline(query)

        if result["type"] == "chart" and isinstance(result["result"], bytes):
            logger.debug(
                f"Encoding chart bytes ({len(result['result'])} bytes) to base64"
            )
            result["result"] = base64.b64encode(result["result"]).decode("utf-8")

        elif result["type"] == "report":
            report_result: ReportResults = result["result"]
            serialized_results = []
            for item in report_result.results:
                if isinstance(item, bytes):
                    # Add data URL prefix for images in reports
                    base64_data = base64.b64encode(item).decode("utf-8")
                    serialized_results.append(f"data:image/png;base64,{base64_data}")
                else:
                    serialized_results.append(item)
            result["result"] = {"results": serialized_results}

        response = {"output": result, "original_query": query}
        logger.info(f"Successfully processed query, result type: {result['type']}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/health", methods=["GET"])
def health_check():
    """
    Perform a health check of the application and its dependencies.

    This endpoint checks:
    1. Database connection status
    2. Availability of accessible tables

    It returns a JSON response indicating whether the application is healthy
    and can function properly.

    Response Format:
        {
            "status": "ok|error",
            "message": "Descriptive status message",
            "healthy": true|false,
            "tables_count": <number of accessible tables> (if healthy)
        }

    Returns:
        JSON response with health status
        HTTP 200 if healthy
        HTTP 503 if service is unavailable or unhealthy
    """
    # Check database connection
    if Database.db is None:
        success = Database.initialize()
        if not success:
            logger.error("Health check failed: Database connection failed")
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

    # Check for accessible tables
    tables = Database.list_tables()
    if not tables:
        logger.error("Health check failed: No accessible tables found")
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "No accessible tables found",
                    "healthy": False,
                }
            ),
            503,
        )

    # All checks passed
    logger.info(f"Health check successful: {len(tables)} tables available")
    return (
        jsonify(
            {
                "status": "ok",
                "message": "Database is healthy and tables exist",
                "healthy": True,
                "tables_count": len(tables),
            }
        ),
        200,
    )


if __name__ == "__main__":
    logger.info(f"Starting Flask application on {HOST}:{PORT} (debug={DEBUG})")
    app.run(debug=DEBUG, host=HOST, port=PORT)
