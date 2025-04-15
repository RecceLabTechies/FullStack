#!/usr/bin/env python
"""
Main Pipeline Module

This module implements the core processing pipeline for analyzing user queries.
It orchestrates the entire flow from query validation to result generation,
coordinating between various specialized components.

The pipeline consists of several stages:
1. Query validation - Ensuring the query is valid and well-formed
2. Query classification - Determining the appropriate analysis type
3. Table selection - Identifying the relevant data source
4. Data processing - Retrieving and preparing data for analysis
5. Result generation - Creating charts or descriptions based on the query type

The module exposes a main function that serves as the entry point for the pipeline,
taking a user query and returning structured analysis results.
"""

import json
import logging
from typing import Dict, Union

from mypackage.a_query_processor.query_classifier import classify_query
from mypackage.b_data_processor import table_processor, table_selector
from mypackage.c_regular_generator import (
    chart_generator,
    description_generator,
)
from mypackage.d_report_generator.report_generator import (
    ReportResults,
    report_generator,
)
from mypackage.utils.database import Database

# Set up logging
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

# Initialize database connection
Database.initialize()


def main(query: str) -> Dict[str, Union[str, bytes, ReportResults]]:
    """
    Main function for the end-to-end pipeline: from natural language query to visualization.

    This is the entry point for the application. It takes a natural language query,
    determines what type of query it is, selects the appropriate data,
    and generates the appropriate visualization or description.

    Args:
        query: The natural language query from the user.

    Returns:
        A dictionary with:
        - 'type': The type of result ('chart', 'description', 'report', 'error')
        - 'result': The generated result (chart as SVG, text description, or error message)
    """
    logger.info(f"Processing query: '{query}'")

    # Step 1: Classify the query
    try:
        classification_result = classify_query(query)
        logger.debug(f"Query classified as: {classification_result}")
    except Exception as e:
        logger.error(f"Query classification failed: {str(e)}", exc_info=True)
        return {"type": "error", "result": f"Error classifying query: {str(e)}"}

    # Step 2: For special queries like report generation, handle separately
    if classification_result == "report":
        try:
            logger.info("Generating report")
            report_result = report_generator(query)
            return {"type": "report", "result": report_result}
        except Exception as e:
            logger.error(f"Report generation failed: {str(e)}", exc_info=True)
            return {"type": "error", "result": f"Error generating report: {str(e)}"}

    # Step 4: Select and process the appropriate table for chart/description
    try:
        # Step 4a: Select the appropriate table
        table_name = table_selector.select_table_for_query(query)
        logger.debug(f"Selected table: {table_name}")
    except Exception as e:
        logger.error(f"Table selection failed: {str(e)}", exc_info=True)
        return {"type": "error", "result": f"Error selecting table: {str(e)}"}

    # Step 4b: Process the table to get a DataFrame
    df = table_processor.process_table_query(table_name, query)

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
