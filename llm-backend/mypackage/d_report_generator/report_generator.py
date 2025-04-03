#!/usr/bin/env python
"""
Report Generator Module

This module contains functionality for generating comprehensive reports based on user queries.
It handles the process of breaking down complex queries into smaller analysis tasks,
executing each analysis, and collecting the results.

Key components:
- Query decomposition into multiple analysis questions
- Execution of individual analysis tasks via the truncated pipeline
- Result aggregation from multiple analyses
- Structured output via Pydantic models
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

    This protocol is used to ensure type safety when working with
    responses from language models that may come from different providers.

    Attributes:
        content: The text content of the LLM response
    """

    content: str


def report_generator(user_query: str) -> ReportResults:
    """
    Generate a comprehensive report by breaking down a complex query
    into smaller analysis tasks and executing each task.

    This function serves as the primary entry point for report generation,
    orchestrating the entire process from query decomposition to result
    collection.

    Args:
        user_query: The original user query requesting a report

    Returns:
        ReportResults object containing all analysis results

    Flow:
        1. Generate list of analysis queries using LLM
        2. Process each query through the truncated pipeline
        3. Collect and return all results

    Raises:
        Exception: Individual query failures are logged but don't halt
                  the overall report generation process
    """
    logger.info(f"Starting report generation for query: '{user_query}'")

    # Step 1: Generate analysis queries from the user query
    logger.debug("Generating analysis queries from user query")
    try:
        queryList: QueryList = generate_analysis_queries(user_query)
        logger.info(f"Generated {len(queryList.queries)} analysis queries")
        logger.debug(f"Analysis queries: {queryList.queries}")
    except Exception as e:
        logger.error(f"Failed to generate analysis queries: {str(e)}", exc_info=True)
        return ReportResults(results=["Error generating analysis queries: " + str(e)])

    # Step 2: Process each query and collect results
    results: List[Union[str, List[str]]] = []
    logger.debug("Beginning to process individual analysis queries")

    for i, queryItem in enumerate(queryList.queries):
        logger.info(f"Processing query {i + 1}/{len(queryList.queries)}: '{queryItem}'")

        try:
            # Execute the query through the truncated pipeline
            logger.debug(f"Sending query to truncated pipeline: '{queryItem}'")
            result: Union[str, List[str]] = truncated_pipeline.run_truncated_pipeline(
                queryItem
            )

            # Add result to our collection
            results.append(result)

            # Log result type for debugging
            if isinstance(result, list):
                logger.debug(f"Query {i + 1} produced {len(result)} chart URLs")
            else:
                logger.debug(
                    f"Query {i + 1} produced text description ({len(str(result))} chars)"
                )

            logger.info(f"Query {i + 1} processed successfully")
        except Exception as e:
            # Log any errors but continue with other queries
            logger.error(f"Error processing query {i + 1}: {str(e)}", exc_info=True)
            error_message = f"Error in analysis {i + 1}: {str(e)}"
            results.append(error_message)
            logger.warning(f"Added error message to results: '{error_message}'")

    # Step 3: Return the collected results
    logger.info(f"Report generation completed with {len(results)} results")

    # Log summary of results for debugging
    text_results = sum(1 for r in results if isinstance(r, str))
    chart_results = sum(1 for r in results if isinstance(r, list))
    logger.debug(
        f"Result summary: {text_results} text descriptions, {chart_results} chart sets"
    )

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
    test_query = (
        "What is the average spending per customer and how has it changed over time?"
    )
    logger.info(f"Testing report generator with sample query: '{test_query}'")

    try:
        result = report_generator(test_query)
        logger.info(f"Received {len(result.results)} results from report generator")

        # Print abbreviated results for visual inspection
        for i, res in enumerate(result.results):
            if isinstance(res, list):
                logger.info(f"Result {i + 1}: {len(res)} chart URLs")
            else:
                abbreviated = res[:100] + "..." if len(res) > 100 else res
                logger.info(f"Result {i + 1}: {abbreviated}")
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
