#!/usr/bin/env python
import logging
from typing import Union, Dict

from mypackage.b_data_processor import json_processor
from mypackage.c_regular_generator import chart_data_generator, description_generator
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


def run_truncated_pipeline(queryItem: QueryItem) -> Dict[str, str]:
    """
    Main function that processes the given query item.

    Args:
        queryItem (QueryItem): An instance of QueryItem containing the query details.

    Returns:
        Dict[str, str]: A dictionary containing:
            - 'type': The type of result ("chart", "description", "error")
            - 'result': The processed result (image URL, description text, or error message)

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
    collection_name = queryItem.collection_name

    # data processor
    try:
        df = json_processor.process_json_query(collection_name, queryItem.query)
    except Exception as e:
        logger.error(f"Error processing JSON: {str(e)}")
        return {"type": "error", "result": f"Error processing JSON: {str(e)}"}

    # generator
    try:
        if classification_result == "chart":
            logger.info("Generating chart data")
            result = chart_data_generator.generate_chart_data(df, queryItem.query)
            return {"type": "chart", "result": result}
        elif classification_result == "description":
            logger.info("Generating description")
            result = description_generator.generate_description(df, queryItem.query)
            return {"type": "description", "result": result}
        else:
            return {
                "type": "error",
                "result": f"Error generating output: {classification_result}",
            }
    except Exception as e:
        logger.error(f"Error generating output: {str(e)}")
        return {"type": "error", "result": f"Error generating output: {str(e)}"}


if __name__ == "__main__":
    result = run_truncated_pipeline(
        QueryItem(
            query="What is the average spending per customer?",
            query_type=QueryType.DESCRIPTION,
            collection_name="campaign_performance",
        )
    )
    print(f"Type: {result['type']}")
    print(f"Result: {result['result']}")
