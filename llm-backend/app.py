from flask import Flask, request, jsonify
from flask_cors import CORS
from pipeline import run_pipeline, PipelineResult
import pandas as pd

app = Flask(__name__)
CORS(app)

print("🚀 Starting Flask API server...")


@app.route("/api/query", methods=["POST"])
def process_query():
    """
    Endpoint to process queries through the pipeline
    Expects a JSON body with format: {"query": "your query here"}
    """
    print("\n🔄 Processing new query request...")

    if not request.is_json:
        print("❌ Error: Request must be JSON")
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    if "query" not in data:
        print("❌ Error: Query field is required")
        return jsonify({"error": "Query field is required"}), 400

    query = data["query"]
    print(f"📝 Received query: {query}")

    try:
        print("🔄 Running pipeline...")
        result: PipelineResult = run_pipeline(query)
        print("✨ Pipeline completed successfully")

        # Convert the result to a JSON-serializable format
        response = {
            "selected_json": result.selected_json,
            "original_query": result.original_query,
            "query_type": result.query_type,
        }

        # Handle different output types
        if result.query_type == "chart":
            print("📊 Preparing chart data response")
            response["output"] = (
                result.output if isinstance(result.output, dict) else str(result.output)
            )
        elif result.query_type in ["description", "report"]:
            print("📝 Preparing text response")
            response["output"] = str(result.output)
        else:
            response["output"] = None

        print("✅ Request processed successfully")
        return jsonify(response)

    except Exception as e:
        print(f"❌ Error processing request: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    print("💓 Health check requested")
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    print("🌐 Starting development server on port 5152...")
    app.run(debug=True, host="0.0.0.0", port=5152)
