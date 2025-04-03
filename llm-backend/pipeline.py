#!/usr/bin/env python
"""
Main Pipeline Module

This module implements the core processing pipeline for analyzing user queries.
It orchestrates the entire flow from query validation to result generation,
coordinating between various specialized components.

The pipeline consists of several stages:
1. Query validation - Ensuring the query is valid and well-formed
2. Query classification - Determining the appropriate analysis type
3. Collection selection - Identifying the relevant data source
4. Data processing - Retrieving and preparing data for analysis
5. Result generation - Creating charts or descriptions based on the query type

The module exposes a main function that serves as the entry point for the pipeline,
taking a user query and returning structured analysis results.
"""

import logging
from typing import Dict, Union

from mypackage.a_query_processor import query_classifier, query_validator
from mypackage.b_data_processor import collection_processor, collection_selector
from mypackage.c_regular_generator import chart_generator, description_generator
from mypackage.d_report_generator import ReportResults, report_generator

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


def main(query: str) -> Dict[str, Union[str, ReportResults]]:
    """
    Execute the complete processing pipeline for a user query.

    This function orchestrates the full analysis pipeline, from validating the input
    query to generating the appropriate output based on the query's classification.
    It handles different query types (chart, description, report) and manages error
    cases.

    Args:
        query (str): The user query to process

    Returns:
        Dict[str, Union[str, ReportResults]]: A dictionary containing:
            - 'type': The result type ('chart', 'description', 'report', or 'error')
            - 'result': The output of the processing, which could be:
                - A URL for chart results
                - A text description for description results
                - A ReportResults object for report results
                - An error message for error cases

    Flow:
        1. Validate the input query
        2. Classify the query (chart, description, report)
        3. For reports, delegate to the report generator
        4. For charts/descriptions:
            a. Select the appropriate data collection
            b. Process the data
            c. Generate the appropriate output
    """
    query = query.strip()
    logger.info(f"Starting pipeline processing for query: '{query}'")

    # Step 1: Validate the query
    try:
        query_validator.get_valid_query(query)
        logger.debug("Query validation successful")
    except Exception as e:
        logger.error(f"Query validation failed: {str(e)}")
        return {"type": "error", "result": f"Error validating query: {str(e)}"}

    # Step 2: Classify the query
    classification_result = query_classifier.classify_query(query)
    logger.debug(f"Query classified as: {classification_result}")

    if classification_result == "error":
        logger.error("Query classification failed")
        return {"type": "error", "result": "Classification failed"}

    # Step 3: Handle report requests separately
    if classification_result == "report":
        logger.info("Query identified as report request, initiating report generation")
        try:
            report_result = report_generator.generate_report(query)
            return {"type": "report", "result": report_result}
        except Exception as e:
            logger.error(f"Report generation failed: {str(e)}", exc_info=True)
            return {"type": "error", "result": f"Error generating report: {str(e)}"}

    # Step 4: Select and process the appropriate collection for chart/description
    try:
        # Step 4a: Select the appropriate collection
        collection_name = collection_selector.select_collection_for_query(query)
        logger.debug(f"Selected collection: {collection_name}")
    except Exception as e:
        logger.error(f"Collection selection failed: {str(e)}", exc_info=True)
        return {"type": "error", "result": f"Error selecting collection: {str(e)}"}

    # Step 4b: Process the collection to get a DataFrame
    df = collection_processor.process_collection_query(collection_name, query)

    # Step 5: Generate the appropriate output based on classification
    try:
        if classification_result == "chart":
            logger.info("Generating chart visualization")
            result = chart_generator.generate_chart(df, query)
            return {"type": "chart", "result": result}
        elif classification_result == "description":
            logger.info("Generating data description")
            result = description_generator.generate_description(df, query)
            return {"type": "description", "result": result}
        else:
            logger.warning(f"Unknown classification result: {classification_result}")
            return {"type": "unknown", "result": ""}
    except Exception as e:
        logger.error(f"Output generation failed: {str(e)}", exc_info=True)
        return {"type": "error", "result": f"Error generating output: {str(e)}"}


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) > 1:
        result = main(sys.argv[1])
        print(json.dumps(result, indent=2))
    else:
        logger.error("No query provided in command line arguments")
        print("Usage: python pipeline.py <query>")
        sys.exit(1)
