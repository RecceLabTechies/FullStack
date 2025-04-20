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
import time
import uuid
from typing import Dict, Union, Any
import threading

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

# Task storage for async queries with metadata
task_storage = {}  # job_id -> {"status": str, "result": Any, "query": str, "created_at": float}

# Configuration for task cleanup
TASK_EXPIRY_HOURS = 24  # Tasks expire after 24 hours
CLEANUP_INTERVAL_HOURS = 1  # Run cleanup every hour

def cleanup_expired_tasks():
    """
    Periodically remove expired tasks from the task storage to prevent memory leaks.
    """
    while True:
        try:
            current_time = time.time()
            expiry_time = current_time - (TASK_EXPIRY_HOURS * 3600)
            expired_jobs = []
            
            for job_id, task in task_storage.items():
                if task["created_at"] < expiry_time:
                    expired_jobs.append(job_id)
            
            for job_id in expired_jobs:
                logger.info(f"Removing expired job {job_id} from task storage")
                del task_storage[job_id]
                
            logger.info(f"Task cleanup complete. Removed {len(expired_jobs)} expired tasks. Current task count: {len(task_storage)}")
        except Exception as e:
            logger.error(f"Error during task cleanup: {e}", exc_info=True)
            
        # Sleep for the cleanup interval
        time.sleep(CLEANUP_INTERVAL_HOURS * 3600)

# Start the cleanup thread
cleanup_thread = threading.Thread(target=cleanup_expired_tasks, daemon=True)
cleanup_thread.start()

@app.route("/api/query", methods=["POST"])
def process_query():
    """
    Process an analytical query asynchronously via POST request.

    This endpoint accepts a JSON payload with a 'query' field, creates a background
    task for processing, and returns a job ID for status checking.

    Expected Request Format:
        {
            "query": "String containing the user's analytical question"
        }

    Response Format:
        {
            "job_id": "Unique identifier for checking query status",
            "status": "pending",
            "message": "Query has been submitted for processing"
        }

    Returns:
        JSON response with job_id
        HTTP 400 for malformed requests
    """
    # Validate that the request contains JSON
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    # Extract and validate the query field
    data = request.get_json()
    if "query" not in data:
        return jsonify({"error": "Query field is required"}), 400

    query = data["query"]
    job_id = str(uuid.uuid4())
    logger.info(f"Received query: '{query}', assigned job_id: {job_id}")
    
    # Create task entry with creation timestamp
    task_storage[job_id] = {
        "status": "pending",
        "query": query,
        "result": None,
        "created_at": time.time()
    }
    
    # Start processing in background (this would ideally use a proper task queue like Celery)
    thread = threading.Thread(target=_process_query_async, args=(job_id, query))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        "job_id": job_id,
        "status": "pending",
        "message": "Query has been submitted for processing"
    })


def _process_query_async(job_id, query):
    """
    Background task to process a query asynchronously.
    Updates the task storage with results when complete.
    """
    logger.info(f"Starting background processing for job_id: {job_id}")
    task_storage[job_id]["status"] = "processing"
    
    try:
        result: Dict[str, Union[str, bytes, ReportResults]] = run_pipeline(query)
        
        # Process chart results
        if result["type"] == "chart" and isinstance(result["result"], bytes):
            logger.debug(
                f"Encoding chart bytes ({len(result['result'])} bytes) to base64"
            )
            result["result"] = base64.b64encode(result["result"]).decode("utf-8")
        
        # Process report results
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
        
        # Store successful result
        task_storage[job_id]["result"] = result
        task_storage[job_id]["status"] = "completed"
        logger.info(f"Successfully processed query for job_id: {job_id}, result type: {result['type']}")
    
    except Exception as e:
        logger.error(f"Error processing query for job_id: {job_id}: {str(e)}", exc_info=True)
        task_storage[job_id]["status"] = "error"
        task_storage[job_id]["result"] = {"type": "error", "result": str(e)}


@app.route("/api/query/status/<job_id>", methods=["GET"])
def check_query_status(job_id):
    """
    Check the status of an asynchronous query processing job.
    
    This endpoint accepts a job_id and returns the current status and results if available.
    
    Response Format:
        {
            "job_id": "The job ID being checked",
            "status": "pending|processing|completed|error",
            "created_at": timestamp when the job was created,
            "expires_at": timestamp when the job will expire,
            "result": null (if pending/processing) or result object (if completed/error),
            "original_query": "The original query string"
        }
    
    Returns:
        JSON response with current status and results if available
        HTTP 404 if job_id is not found
    """
    if job_id not in task_storage:
        return jsonify({"error": f"Job ID {job_id} not found"}), 404
    
    task = task_storage[job_id]
    
    response = {
        "job_id": job_id,
        "status": task["status"],
        "original_query": task["query"],
        "created_at": task["created_at"],
        "expires_at": task["created_at"] + (TASK_EXPIRY_HOURS * 3600)
    }
    
    # Only include results if processing is complete
    if task["status"] in ["completed", "error"]:
        response["output"] = task["result"]
    
    return jsonify(response)


@app.route("/api/health", methods=["GET"])
def health_check():
    """
    Perform a health check of the application and its dependencies.

    This endpoint checks:
    1. Database connection status
    2. Availability of accessible collections

    It returns a JSON response indicating whether the application is healthy
    and can function properly.

    Response Format:
        {
            "status": "ok|error",
            "message": "Descriptive status message",
            "healthy": true|false,
            "collections_count": <number of accessible collections> (if healthy)
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

    # Check for accessible collections
    collections = Database.list_collections()
    if not collections:
        logger.error("Health check failed: No accessible collections found")
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

    # All checks passed
    logger.info(f"Health check successful: {len(collections)} collections available")
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
    logger.info(f"Starting Flask application on {HOST}:{PORT} (debug={DEBUG})")
    app.run(debug=DEBUG, host=HOST, port=PORT)
