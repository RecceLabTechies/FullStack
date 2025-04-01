from typing import Dict, Union
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from mypackage.d_report_generator import ReportResults
from pipeline import main as run_pipeline
from database.connection import Database, get_queries_collection, get_results_collection
from config import CORS_CONFIG

app = Flask(__name__)
CORS(app, resources={r"/*": CORS_CONFIG})

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
    start_time = datetime.utcnow()

    try:
        # Store query in database
        query_doc = {
            "timestamp": start_time,
            "query_text": query,
            "user_id": data.get("user_id", "anonymous"),
            "status": "processing",
            "processing_time": None,
        }
        query_result = get_queries_collection().insert_one(query_doc)
        query_id = str(query_result.inserted_id)

        # Run the pipeline
        result: Dict[str, Union[str, Dict[str, ReportResults]]] = run_pipeline(query)

        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds()

        # Store results in database
        result_doc = {
            "query_id": query_id,
            "timestamp": datetime.utcnow(),
            "output": result,
            "original_query": query,
            "metadata": {"processing_time": processing_time, "status": "success"},
            "status": "completed",
        }
        get_results_collection().insert_one(result_doc)

        # Update query status
        get_queries_collection().update_one(
            {"_id": query_result.inserted_id},
            {"$set": {"status": "completed", "processing_time": processing_time}},
        )

        # Prepare response
        response = {
            "output": result,
            "original_query": query,
            "query_id": query_id,
            "processing_time": processing_time,
        }

        return jsonify(response)

    except Exception as e:
        # Update query status to failed
        if "query_result" in locals():
            get_queries_collection().update_one(
                {"_id": query_result.inserted_id},
                {
                    "$set": {
                        "status": "failed",
                        "processing_time": (
                            datetime.utcnow() - start_time
                        ).total_seconds(),
                    }
                },
            )

        return jsonify({"error": str(e)}), 500


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5152)
