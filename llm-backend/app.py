from flask import Flask, request, jsonify
from flask_cors import CORS
from pipeline import run_pipeline, PipelineResult

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
        result: PipelineResult = run_pipeline(query)

        # Convert the result to a JSON-serializable format
        response = {
            "selected_json": result.selected_json,
            "original_query": result.original_query,
            "query_type": result.query_type,
        }

        # Handle different output types
        if result.query_type == "chart":
            response["output"] = (
                result.output if isinstance(result.output, dict) else str(result.output)
            )
        elif result.query_type in ["description", "report"]:
            response["output"] = str(result.output)
        else:
            response["output"] = None

        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5152)
