#!/usr/bin/env python
"""
Report Generator Module

This module contains functionality for generating comprehensive reports based on user queries.
It handles the process of breaking down complex queries into smaller analysis tasks,
executing each analysis, and collecting the results.
"""

import logging
from typing import List, Protocol, Union

from pydantic import BaseModel

from mypackage.d_report_generator import truncated_pipeline
from mypackage.d_report_generator.generate_analysis_queries import (
    QueryList,
    generate_analysis_queries,
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

logger.debug("report_generator module initialized")


class ReportResults(BaseModel):
    """
    Pydantic model to store and structure the results of report generation.

    Attributes:
        results: List of results from processed analysis queries, which can be
                strings (for descriptions) or lists of strings (for charts/visuals)
    """

    results: List[Union[str, List[str]]]


class LLMResponse(Protocol):
    """
    Protocol defining the expected interface for LLM response objects.
    """

    content: str


def report_generator(user_query: str) -> ReportResults:
    """
    Generate a comprehensive report by breaking down a complex query
    into smaller analysis tasks and executing each task.

    Args:
        user_query: The original user query requesting a report

    Returns:
        ReportResults object containing all analysis results

    Flow:
        1. Generate list of analysis queries using LLM
        2. Process each query through the truncated pipeline
        3. Collect and return all results
    """
    logger.info(f"Starting report generation for query: {user_query}")

    # Step 1: Generate analysis queries from the user query
    logger.debug("Generating analysis queries from user query")
    queryList: QueryList = generate_analysis_queries(user_query)
    logger.debug(f"Generated {len(queryList.queries)} analysis queries using Groq")

    # Step 2: Process each query and collect results
    results: List[Union[str, List[str]]] = []
    logger.debug("Beginning to process individual analysis queries")

    for i, queryItem in enumerate(queryList.queries):
        logger.info(f"Processing query {i + 1}/{len(queryList.queries)}: {queryItem}")

        try:
            # Execute the query through the truncated pipeline
            result: Union[str, List[str]] = truncated_pipeline.run_truncated_pipeline(
                queryItem
            )
            results.append(result)
            logger.debug(f"Query {i + 1} processed successfully")
        except Exception as e:
            # Log any errors but continue with other queries
            logger.error(f"Error processing query {i + 1}: {str(e)}", exc_info=True)
            results.append(f"Error in analysis: {str(e)}")

    # Step 3: Return the collected results
    logger.info(f"Report generation completed with {len(results)} results")
    return ReportResults(results=results)


if __name__ == "__main__":
    # Set up console logging for direct script execution
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Set to DEBUG for more detailed logging
    root_logger.addHandler(console_handler)

    # Test the report generator with a sample query
    logger.info("Testing report generator with sample query")
    result = report_generator("What is the average spending per customer?")
    logger.info(f"Received {len(result.results)} results from report generator")
