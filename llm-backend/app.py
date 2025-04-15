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
import json
from typing import Dict, Union

from flask import Flask, jsonify, request
from flask_cors import CORS

from config import CORS_CONFIG, DEBUG, HOST, PORT
from mypackage.d_report_generator import ReportResults
from mypackage.utils.chroma_db import ChromaDBManager
from mypackage.utils.database import Database
from mypackage.utils.example_vectorizer import initialize_examples
from mypackage.utils.logging_config import setup_logging
from pipeline import main as run_pipeline

logger = setup_logging("llm_backend")
app = Flask(__name__)

CORS(app, **CORS_CONFIG)
Database.initialize()
ChromaDBManager.initialize()


# Utility function to convert collection data to embedding input
def prepare_collection_for_embedding(collection_data):
    """
    Convert collection metadata into a string format suitable for embedding.

    Args:
        collection_data (dict): Collection metadata from analyze_collections

    Returns:
        str: Formatted string representation of the collection
    """
    collection_text = json.dumps(collection_data, default=str, sort_keys=True)
    return collection_text


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


@app.route("/api/chroma/health", methods=["GET"])
def chroma_health_check():
    """
    Check the health status of ChromaDB and its collections.

    Returns:
        JSON response with:
        - status: "ok" or "error"
        - message: Descriptive status message
        - healthy: boolean indicating if ChromaDB is healthy
        - collections: List of available collections and their details
    """
    try:
        # Check if we can connect to ChromaDB
        collections = ChromaDBManager.list_collections()

        # Get details for each collection
        collections_info = []
        for collection in collections:
            collection_info = {
                "name": collection.name,
                "count": collection.count(),
                "metadata": collection.metadata,
            }
            collections_info.append(collection_info)

        return jsonify(
            {
                "status": "ok",
                "message": "ChromaDB is healthy and accessible",
                "healthy": True,
                "collections": collections_info,
            }
        ), 200

    except Exception as e:
        logger.error(f"ChromaDB health check failed: {str(e)}", exc_info=True)
        return jsonify(
            {
                "status": "error",
                "message": f"ChromaDB health check failed: {str(e)}",
                "healthy": False,
                "collections": [],
            }
        ), 503


@app.route("/api/vectorize_collections", methods=["POST"])
def vectorize_collections():
    """
    Generate vector embeddings for all accessible PostgreSQL tables.

    This endpoint analyzes all accessible tables using the Database.analyze_tables
    method, then generates embeddings for each table using the embeddings model.
    The embeddings are stored in ChromaDB for later use in search and retrieval operations.

    The process:
    1. Deletes all existing ChromaDB collections to ensure fresh embeddings
    2. Analyzes all PostgreSQL tables to extract metadata
    3. Generates embeddings for each table
    4. Stores the embeddings in ChromaDB with table metadata

    Returns:
        JSON response with:
        - status: "success" or "error"
        - message: Description of the operation result
        - tables_processed: Number of tables processed
        - embedding_dimensions: Size of the embedding vectors
    """
    try:
        logger.info("Starting table vectorization process")

        # Step 1: Delete existing embeddings (delete all collections in ChromaDB)
        existing_collections = ChromaDBManager.list_collections()
        for collection in existing_collections:
            logger.info(f"Deleting existing ChromaDB collection: {collection.name}")
            ChromaDBManager.delete_collection(collection.name)

        # Step 2: Analyze PostgreSQL tables to extract metadata
        logger.info("Analyzing PostgreSQL tables")
        table_data = Database.analyze_tables()

        if not table_data:
            return jsonify(
                {
                    "status": "error",
                    "message": "No tables found or analysis failed",
                    "tables_processed": 0,
                }
            ), 404

        # Step 3: Create a vector store in ChromaDB for table embeddings
        chroma_collection = ChromaDBManager.get_or_create_collection("table_embeddings")

        # Step 4: Process each table and generate embeddings
        processed_tables = []
        embedding_dimensions = 0

        for table_name, fields_data in table_data.items():
            logger.info(f"Processing table: {table_name}")

            # Prepare table data for embedding
            table_text = prepare_collection_for_embedding(
                {"name": table_name, "fields": fields_data}
            )

            # Generate embedding using model from ChromaDBManager
            try:
                embedding = ChromaDBManager.generate_embedding(table_text)

                # Add to ChromaDB
                chroma_collection.add(
                    ids=[table_name],
                    embeddings=[embedding],
                    metadatas=[
                        {
                            "name": table_name,
                            "field_count": len(fields_data),
                            "raw_metadata": json.dumps(fields_data, default=str),
                        }
                    ],
                    documents=[table_text],
                )

                if embedding_dimensions == 0:
                    embedding_dimensions = len(embedding)

                processed_tables.append(table_name)
                logger.info(f"Successfully vectorized table: {table_name}")

            except Exception as e:
                logger.error(f"Error vectorizing table {table_name}: {str(e)}")

        return jsonify(
            {
                "status": "success",
                "message": f"Successfully vectorized {len(processed_tables)} tables",
                "tables_processed": len(processed_tables),
                "tables": processed_tables,
                "embedding_dimensions": embedding_dimensions,
            }
        ), 200

    except Exception as e:
        logger.error(f"Error in vectorization process: {str(e)}", exc_info=True)
        return jsonify(
            {
                "status": "error",
                "message": f"Vectorization failed: {str(e)}",
                "tables_processed": 0,
            }
        ), 500


@app.route("/api/vectorize_examples", methods=["POST"])
def vectorize_examples():
    """
    Generate vector embeddings for all example JSON files.

    This endpoint reads example JSON files from the examples directory,
    generates embeddings for each example, and stores them in ChromaDB
    for use in various LLM functions.

    Query Parameters:
        force_refresh: If "true", deletes existing collections before recreating them

    Returns:
        JSON response with:
        - status: "success" or "error"
        - message: Description of the operation result
        - examples_processed: Dict mapping function names to number of examples processed
    """
    try:
        logger.info("Starting example vectorization process")

        # Check if force refresh is requested
        force_refresh = request.args.get("force_refresh", "false").lower() == "true"
        if force_refresh:
            logger.info("Force refresh requested, will delete existing collections")

        # Vectorize examples
        results = initialize_examples(force_refresh=force_refresh)

        # Calculate total examples
        total_examples = sum(results.values())

        return jsonify(
            {
                "status": "success",
                "message": f"Successfully vectorized {total_examples} examples across {len(results)} collections",
                "examples_processed": results,
            }
        ), 200

    except Exception as e:
        logger.error(f"Error in example vectorization process: {str(e)}", exc_info=True)
        return jsonify(
            {
                "status": "error",
                "message": f"Example vectorization failed: {str(e)}",
                "examples_processed": {},
            }
        ), 500


if __name__ == "__main__":
    logger.info(f"Starting Flask application on {HOST}:{PORT} (debug={DEBUG})")
    app.run(debug=DEBUG, host=HOST, port=PORT)
