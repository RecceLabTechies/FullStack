#!/usr/bin/env python
import logging
from typing import Dict, List, Union

from mypackage.b_data_processor import collection_processor
from mypackage.c_regular_generator import chart_generator, description_generator
from mypackage.d_report_generator.generate_analysis_queries import QueryItem, QueryType

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


def run_truncated_pipeline(queryItem: QueryItem) -> Dict[str, Union[str, List[str]]]:
    logger.info(f"Processing query: '{queryItem.query}'")

    if queryItem.query_type == QueryType.CHART:
        classification_result = "chart"
    elif queryItem.query_type == QueryType.DESCRIPTION:
        classification_result = "description"
    else:
        raise ValueError(f"Invalid query type: {queryItem.query_type}")

    collection_name = queryItem.collection_name

    try:
        df = collection_processor.process_collection_query(
            collection_name, queryItem.query
        )
    except Exception as e:
        logger.error(f"Error processing JSON: {str(e)}")
        return {"type": "error", "result": f"Error processing JSON: {str(e)}"}

    try:
        if classification_result == "chart":
            logger.info("Generating chart data")
            result = chart_generator.generate_chart(df, queryItem.query)
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
