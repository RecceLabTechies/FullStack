from flask import Flask, request, jsonify
from flask_cors import CORS
from pipeline import run_pipeline, PipelineResult
import pandas as pd
from typing import Dict, Any

app = Flask(__name__)
CORS(app)


@app.route("/api/pipeline", methods=["POST"])
def pipeline():
    """
    API endpoint to run the LLM pipeline.

    Expected JSON payload:
    {
        "query": "your natural language query here"
    }

    Returns:
    {
        "success": true/false,
        "result": {
            "selected_json": "filename.json",
            "original_query": "query text",
            "query_type": "chart/description/report",
            "output": "generated output (chart path or text)",
            "data_preview": {} // First few rows of processed data if available
        },
        "error": "error message if any"
    }
    """
    try:
        # Get query from request
        data = request.get_json()
        if not data or "query" not in data:
            return (
                jsonify({"success": False, "error": "Missing query in request body"}),
                400,
            )

        query = data["query"]

        # Run the pipeline
        result = run_pipeline(query)

        # Convert PipelineResult to dictionary
        response = _format_pipeline_result(result)

        return jsonify({"success": True, "result": response})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def _format_pipeline_result(result: PipelineResult) -> Dict[str, Any]:
    """
    Format PipelineResult object into a JSON-serializable dictionary.

    Args:
        result (PipelineResult): Pipeline execution result

    Returns:
        Dict[str, Any]: Formatted response dictionary
    """
    response = {
        "selected_json": result.selected_json,
        "original_query": result.original_query,
        "query_type": result.query_type,
        "output": result.output,
    }

    # Add data preview if DataFrame is not empty
    if not result.processed_df.empty:
        response["data_preview"] = result.processed_df.head().to_dict()
        response["data_shape"] = {
            "rows": result.processed_df.shape[0],
            "columns": result.processed_df.shape[1],
        }
        response["columns"] = list(result.processed_df.columns)

    return response


if __name__ == "__main__":
    app.run(debug=True, port=5000, host="0.0.0.0")
