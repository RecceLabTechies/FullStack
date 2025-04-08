#!/usr/bin/env python
"""
Truncated Pipeline Module

This module provides a simplified pipeline for processing individual analysis queries
as part of report generation. It handles routing queries to the appropriate processor
based on query type (chart or description) and returns formatted results.

Key components:
- Query type classification (chart vs. description)
- Data retrieval and processing from MongoDB collections
- Result generation via specialized generators
- Error handling and standardized response format
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


def run_truncated_pipeline(query_item: QueryItem) -> Union[str, bytes]:
    """
    Process an individual analysis query through the appropriate pipeline components.

    This function represents a simplified version of the main pipeline, specialized
    for handling individual analysis queries as part of report generation. It serves
    as the entry point for processing sub-queries generated during report creation.

    Args:
        query_item: A QueryItem object containing the query text, type, and target collection

    Returns:
        Either a string (for descriptions or error messages) or bytes (for chart images)

    Raises:
        ValueError: If the query type is invalid

    Flow:
        1. Determine query type (chart or description)
        2. Process the data collection query to get a DataFrame
        3. Generate appropriate output based on query type
        4. Return formatted results
    """
    logger.info(
        f"Processing query: '{query_item.query}' of type {query_item.query_type.value}"
    )
    logger.debug(f"Target collection: '{query_item.collection_name}'")

    # Step 1: Determine query type
    if query_item.query_type == QueryType.CHART:
        classification_result = "chart"
        logger.debug("Query classified as chart request - will generate visualization")
    elif query_item.query_type == QueryType.DESCRIPTION:
        classification_result = "description"
        logger.debug(
            "Query classified as description request - will generate text analysis"
        )
    else:
        error_msg = f"Invalid query type: {query_item.query_type}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    collection_name = query_item.collection_name
    logger.debug(f"Using collection: '{collection_name}'")

    # Step 2: Process collection query to get DataFrame
    try:
        logger.debug(
            f"Querying collection '{collection_name}' with: '{query_item.query}'"
        )
        df = collection_processor.process_collection_query(
            collection_name, query_item.query
        )
        if df.empty:
            logger.warning(
                f"Query returned empty DataFrame from collection '{collection_name}'"
            )
            return f"No data found in collection '{collection_name}' for query: '{query_item.query}'"

        logger.debug(
            f"Successfully processed collection query, received DataFrame with shape: {df.shape}, columns: {list(df.columns)}"
        )
    except Exception as e:
        error_msg = f"Error processing collection '{collection_name}': {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg

    # Step 3: Generate appropriate output based on query type
    try:
        if classification_result == "chart":
            logger.info(f"Generating chart for DataFrame with {len(df)} rows")
            chart_bytes = chart_generator.generate_chart(df, query_item.query)
            logger.debug(f"Chart generation successful, {len(chart_bytes)} bytes")
            return chart_bytes

        elif classification_result == "description":
            logger.info(f"Generating description for DataFrame with {len(df)} rows")
            description = description_generator.generate_description(
                df, query_item.query
            )
            logger.debug(
                f"Description generation successful ({len(description)} chars)"
            )
            return description

        else:
            # This should never happen given the earlier validation, but included for completeness
            error_msg = f"Unexpected classification result: {classification_result}"
            logger.error(error_msg)
            return error_msg

    except Exception as e:
        error_msg = f"Error generating {classification_result} output: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg



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
