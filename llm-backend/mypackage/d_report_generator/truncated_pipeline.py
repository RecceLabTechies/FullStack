#!/usr/bin/env python
"""
Truncated Pipeline Module for Report Generator

This module provides a simplified pipeline flow specifically for the report generator,
where collection selection has already been handled and we just need to process
the query and generate content.
"""

import logging
from enum import Enum, auto
from typing import Any, Dict, Optional

import pandas as pd
from pydantic import BaseModel

from mypackage.a_query_processor.query_classifier import classify_query
from mypackage.b_data_processor import table_processor
from mypackage.c_regular_generator.chart_generator import (
    generate_chart as chart_generator,
)
from mypackage.c_regular_generator.description_generator import (
    generate_description as description_generator,
)

# Set up module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.propagate = False

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

logger.debug("truncated_pipeline module initialized")


class QueryType(Enum):
    """Enumeration of possible query types for the truncated pipeline."""

    CHART = auto()
    DESCRIPTION = auto()


class QueryItem(BaseModel):
    """
    Pydantic model for a single query item in a report.

    Attributes:
        query: The natural language query text
        query_type: The type of output expected (chart or description)
        collection_name: Name of the MongoDB collection to query (optional)
    """

    query: str
    query_type: QueryType
    collection_name: Optional[str] = None


def run_truncated_pipeline(query_item: QueryItem) -> Dict[str, Any]:
    """
    Run a simplified pipeline process for report generation.

    This function processes a single query item, assuming that collection selection
    has already been handled. It extracts data from the specified collection,
    processes it according to the query, and generates the appropriate output.

    Args:
        query_item: The QueryItem containing the query, type, and collection name

    Returns:
        dict: A dictionary with the result type and content
    """
    # Step 0: Validate the query and extract details
    classification_result = classify_query(query_item.query)
    logger.debug(f"Query classified as: {classification_result}")

    if classification_result not in ["chart", "description"]:
        error_msg = f"Invalid query type: Expected 'chart' or 'description', got '{classification_result}'"
        logger.error(error_msg)
        return {"type": "error", "result": error_msg}

    if query_item.query_type == QueryType.CHART and classification_result != "chart":
        error_msg = f"Query type mismatch: Expected chart query, but classified as '{classification_result}'"
        logger.error(error_msg)
        return {"type": "error", "result": error_msg}

    if (
        query_item.query_type == QueryType.DESCRIPTION
        and classification_result != "description"
    ):
        error_msg = f"Query type mismatch: Expected description query, but classified as '{classification_result}'"
        logger.error(error_msg)
        return {"type": "error", "result": error_msg}

    if not query_item.collection_name:
        error_msg = "No collection name provided for query processing"
        logger.error(error_msg)
        raise ValueError(error_msg)

    table_name = query_item.collection_name
    logger.debug(f"Using table: '{table_name}'")

    # Step 2: Process table query to get DataFrame
    try:
        logger.debug(f"Querying table '{table_name}' with: '{query_item.query}'")
        results = table_processor.process_table_query(table_name, query_item.query)

        # Convert results to DataFrame if needed
        if isinstance(results, list) and results:
            if isinstance(results[0], dict):
                df = pd.DataFrame(results)
            else:
                df = pd.DataFrame(results[0])  # Take first result set
        else:
            df = pd.DataFrame()

        if df.empty:
            logger.warning(f"Query returned empty DataFrame from table '{table_name}'")
            return {
                "type": "error",
                "result": f"No data found in table '{table_name}' for query: '{query_item.query}'",
            }

        logger.debug(
            f"Successfully processed table query, received DataFrame with shape: {df.shape}, columns: {list(df.columns)}"
        )
    except Exception as e:
        error_msg = f"Error processing table '{table_name}': {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"type": "error", "result": error_msg}

    # Step 3: Generate appropriate output based on query type
    try:
        if classification_result == "chart":
            logger.info(f"Generating chart for DataFrame with {len(df)} rows")
            chart_bytes = chart_generator(df, query_item.query)
            logger.debug(f"Chart generation successful, {len(chart_bytes)} bytes")
            return {"type": "chart", "result": chart_bytes}

        elif classification_result == "description":
            logger.info(f"Generating description for DataFrame with {len(df)} rows")
            description = description_generator(df, query_item.query)
            logger.debug(
                f"Description generation successful ({len(description)} chars)"
            )
            return {"type": "description", "result": description}

        else:
            # This should never happen given the earlier validation, but included for completeness
            error_msg = f"Unexpected classification result: {classification_result}"
            logger.error(error_msg)
            return {"type": "error", "result": error_msg}

    except Exception as e:
        error_msg = f"Error generating {classification_result} output: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"type": "error", "result": error_msg}


if __name__ == "__main__":
    # Set up console logging for direct script execution
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    root_logger = logging.getLogger()
    # root_logger.setLevel(logging.DEBUG)  # Set to DEBUG for more detailed logging
    root_logger.addHandler(console_handler)

    # Test the pipeline with a sample query
    from mypackage.utils.database import Database

    # Initialize database if needed
    if Database.db is None:
        logger.info("Initializing database connection for test")
        Database.initialize()

    # Sample description query
    test_desc_query = QueryItem(
        query="What is the average spending per customer?",
        query_type=QueryType.DESCRIPTION,
        collection_name="campaign_performance",
    )
    logger.info(
        f"Testing truncated pipeline with description query: '{test_desc_query.query}'"
    )

    desc_result = run_truncated_pipeline(test_desc_query)
    logger.info(f"Pipeline result type: {desc_result['type']}")
    result_preview = (
        desc_result["result"][:100] + "..."
        if len(str(desc_result["result"])) > 100
        else desc_result["result"]
    )
    logger.info(f"Result preview: {result_preview}")

    # Sample chart query
    test_chart_query = QueryItem(
        query="Show customer spending by channel",
        query_type=QueryType.CHART,
        collection_name="campaign_performance",
    )
    logger.info(
        f"Testing truncated pipeline with chart query: '{test_chart_query.query}'"
    )

    chart_result = run_truncated_pipeline(test_chart_query)
    logger.info(f"Pipeline result type: {chart_result['type']}")
    logger.info(f"Chart URL: {chart_result['result']}")
