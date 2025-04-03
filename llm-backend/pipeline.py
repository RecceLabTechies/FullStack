#!/usr/bin/env python
import logging
from typing import Union, Dict

from mypackage.a_query_processor import query_classifier, query_validator
from mypackage.b_data_processor import json_processor, json_selector
from mypackage.c_regular_generator import (
    chart_data_generator,
    description_generator,
)
from mypackage.d_report_generator import ReportResults, report_generator

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


def main(query: str) -> Dict[str, Union[str, ReportResults]]:
    """
    Process a user query through the complete analysis pipeline, including validation,
    classification, and appropriate data processing based on the query type.

    Args:
        query: The natural language query string to be processed

    Returns:
        Dict[str, Union[str, ReportResults]]: A dictionary containing:
            - 'type': The type of result ("chart", "description", "report", "error", or "unknown")
            - 'result': The processed result (image URL, description text, or error message)
    """
    query = query.strip()
    logger.info(f"Starting pipeline processing for query: '{query}'")

    # query validator
    try:
        query_validator.get_valid_query(query)
        logger.debug("Query validation successful")
    except Exception as e:
        logger.error(f"Query validation failed: {str(e)}")
        return {"type": "error", "result": f"Error validating query: {str(e)}"}

    # query classifier
    classification_result = query_classifier.classify_query(query)
    logger.debug(f"Query classified as: {classification_result}")
    if classification_result == "error":
        logger.error("Query classification failed")
        return {"type": "error", "result": "Classification failed"}

    # report generator
    if classification_result == "report":
        logger.info("Query identified as report request, initiating report generation")
        try:
            report_result = report_generator.generate_report(query)
            return {"type": "report", "result": report_result}
        except Exception as e:
            return {"type": "error", "result": f"Error generating report: {str(e)}"}

    # data selector
    try:
        json_file_name = json_selector.select_json_for_query(query)
        logger.debug(f"Selected JSON file: {json_file_name}")
    except Exception as e:
        logger.error(f"JSON selection failed: {str(e)}")
        return {"type": "error", "result": f"Error selecting JSON: {str(e)}"}

    # data processor
    try:
        df = json_processor.process_json_query(json_file_name, query)
        logger.debug("JSON data processing completed successfully")
    except Exception as e:
        logger.error(f"JSON processing failed: {str(e)}")
        return {"type": "error", "result": f"Error processing JSON: {str(e)}"}

    # generator
    try:
        if classification_result == "chart":
            logger.info("Generating chart visualization")
            result = chart_data_generator.generate_chart_data(df, query)
            return {"type": "chart", "result": result}
        elif classification_result == "description":
            logger.info("Generating data description")
            result = description_generator.generate_description(df, query)
            return {"type": "description", "result": result}
        else:
            logger.warning(f"Unknown classification result: {classification_result}")
            return {"type": "unknown", "result": ""}
    except Exception as e:
        logger.error(f"Output generation failed: {str(e)}")
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
