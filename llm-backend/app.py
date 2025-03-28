from typing import Union

from flask import Flask, jsonify, request
from flask_cors import CORS

from mypackage.c_regular_generator import ChartDataType
from mypackage.d_report_generator import ReportResults
from pipeline import main as run_pipeline

app = Flask(__name__)
CORS(app)


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
        return jsonify({"error": str(e)}), 500


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5152)
