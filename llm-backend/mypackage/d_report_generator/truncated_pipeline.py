#!/usr/bin/env python
"""
Truncated Pipeline Module

This module provides a simplified pipeline for processing individual analysis queries
as part of report generation. It handles routing queries to the appropriate processor
based on query type (chart or description) and returns formatted results.
"""

import logging
from typing import Dict, List, Union

from mypackage.b_data_processor import collection_processor
from mypackage.c_regular_generator import chart_generator, description_generator
from mypackage.d_report_generator.generate_analysis_queries import QueryItem, QueryType

# Set up module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.propagate = False


if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(funcName)s - %(lineno)d"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

logger.debug("truncated_pipeline module initialized")


def run_truncated_pipeline(queryItem: QueryItem) -> Dict[str, Union[str, List[str]]]:
    """
    Process an individual analysis query through the appropriate pipeline components.

    This function represents a simplified version of the main pipeline, specialized
    for handling individual analysis queries as part of report generation.

    Args:
        queryItem: A QueryItem object containing the query text, type, and target collection

    Returns:
        Dictionary with keys 'type' (chart, description, or error) and 'result' containing
        the output of the processing or error message

    Flow:
        1. Determine query type (chart or description)
        2. Process the data collection query to get a DataFrame
        3. Generate appropriate output based on query type
        4. Return formatted results
    """
    logger.info(f"Processing query: '{queryItem.query}' of type {queryItem.query_type}")

    # Step 1: Determine query type
    if queryItem.query_type == QueryType.CHART:
        classification_result = "chart"
        logger.debug("Query classified as chart request")
    elif queryItem.query_type == QueryType.DESCRIPTION:
        classification_result = "description"
        logger.debug("Query classified as description request")
    else:
        error_msg = f"Invalid query type: {queryItem.query_type}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    collection_name = queryItem.collection_name
    logger.debug(f"Using collection: {collection_name}")

    # Step 2: Process collection query to get DataFrame
    try:
        logger.debug(f"Querying collection '{collection_name}' with: {queryItem.query}")
        df = collection_processor.process_collection_query(
            collection_name, queryItem.query
        )
        logger.debug(
            f"Successfully processed collection query, received DataFrame with shape: {df.shape}"
        )
    except Exception as e:
        error_msg = f"Error processing collection: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"type": "error", "result": error_msg}

    # Step 3: Generate appropriate output based on query type
    try:
        if classification_result == "chart":
            logger.info("Generating chart data")
            result = chart_generator.generate_chart(df, queryItem.query)
            logger.debug("Chart generation successful")
            return {"type": "chart", "result": result}
        elif classification_result == "description":
            logger.info("Generating description")
            result = description_generator.generate_description(df, queryItem.query)
            logger.debug("Description generation successful")
            return {"type": "description", "result": result}
        else:
            # This should never happen given the earlier validation, but included for completeness
            error_msg = f"Unexpected classification result: {classification_result}"
            logger.error(error_msg)
            return {"type": "error", "result": error_msg}
    except Exception as e:
        error_msg = f"Error generating output: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"type": "error", "result": error_msg}


if __name__ == "__main__":
    # Set up console logging for direct script execution
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Set to DEBUG for more detailed logging
    root_logger.addHandler(console_handler)

    # Test the pipeline with a sample query
    test_query = QueryItem(
        query="What is the average spending per customer?",
        query_type=QueryType.DESCRIPTION,
        collection_name="campaign_performance",
    )
    logger.info(f"Testing truncated pipeline with query: {test_query.query}")

    result = run_truncated_pipeline(test_query)
    logger.info(f"Pipeline result type: {result['type']}")
    logger.debug(f"Pipeline result: {result['result']}")
