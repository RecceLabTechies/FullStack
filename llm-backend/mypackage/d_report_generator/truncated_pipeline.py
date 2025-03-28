#!/usr/bin/env python
import logging

from mypackage.b_data_processor import json_processor
from mypackage.c_regular_generator import chart_generator, description_generator
from mypackage.d_report_generator.generate_analysis_queries import QueryItem, QueryType

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.propagate = False

# Add handler if not already added
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(funcName)s - %(lineno)d"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def run_truncated_pipeline(queryItem: QueryItem) -> str:
    """
    Main function that processes the given query item.

    Args:
        queryItem (QueryItem): An instance of QueryItem containing the query details.

    Returns:
        str:
            - A string message in case of an error.
            - A URL to the chart image if the query type is 'chart'.
            - A string description if the query type is 'description'.

    Raises:
        ValueError: If the query type is invalid.
    """

    logger.info(f"Processing query: '{queryItem.query}'")

    # query classifier
    if queryItem.query_type == QueryType.CHART:
        classification_result = "chart"
    elif queryItem.query_type == QueryType.DESCRIPTION:
        classification_result = "description"
    else:
        raise ValueError(f"Invalid query type: {queryItem.query_type}")

    # data selector
    json_file_name = queryItem.file_name

    # data processor
    try:
        df = json_processor.process_json_query(json_file_name, queryItem.query)
    except Exception as e:
        logger.error(f"Error processing JSON: {str(e)}")
        return f"Error processing JSON: {str(e)}"

    # generator
    try:
        if classification_result == "chart":
            logger.info("Generating chart and uploading to S3")
            return chart_generator.generate_and_upload_chart(df, queryItem.query)
        elif classification_result == "description":
            logger.info("Generating description")
            return description_generator.generate_description(df, queryItem.query)
        else:
            return f"Error generating output: {classification_result}"
    except Exception as e:
        logger.error(f"Error generating output: {str(e)}")
        return f"Error generating output: {str(e)}"


if __name__ == "__main__":
    run_truncated_pipeline(
        QueryItem(
            query="What is the average spending per customer?",
            query_type=QueryType.CHART,
            file_name="data.json",
        )
    )
