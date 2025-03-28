#!/usr/bin/env python
import logging
from typing import Any, Dict, List

from pydantic import BaseModel

from mypackage.d_report_generator import truncated_pipeline
from mypackage.d_report_generator.generate_analysis_queries import (
    QueryList,
    generate_analysis_queries,
)

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.propagate = False

# Add handler if not already added
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class ReportResults(BaseModel):
    results: List[Dict[str, str]]


def generate_report(user_query: str) -> Dict[str, ReportResults]:
    """
    Generate a report based on the user's query by processing it through the analysis pipeline.

    Args:
        user_query: The natural language query from the user requesting specific analysis

    Returns:
        Dict[str, ReportResults]: A dictionary with "report" as key and ReportResults object as value,
        containing a list of results, which can be dictionaries with query type and result
    """
    logger.info(f"Starting report generation for query: {user_query}")
    queryList: QueryList = generate_analysis_queries(user_query)
    logger.debug(f"Generated {len(queryList.queries)} analysis queries")

    results: List[Dict[str, Any]] = []
    for queryItem in queryList.queries:
        logger.debug(f"Processing query: {queryItem}")
        # Convert string results to dictionary format if needed
        pipeline_result = truncated_pipeline.run_truncated_pipeline(queryItem)

        # Ensure the result is in the right format
        if isinstance(pipeline_result, str):
            result = {"description": pipeline_result}
        elif isinstance(pipeline_result, dict):
            result = pipeline_result
        else:
            # For ChartDataType or other types, wrap in appropriate type
            result = {"chart": pipeline_result}

        results.append(result)
        logger.debug("Query processed successfully")

    logger.info(f"Report generation completed with {len(results)} results")
    return {"report": ReportResults(results=results)}


if __name__ == "__main__":
    generate_report("What is the average spending per customer?")
