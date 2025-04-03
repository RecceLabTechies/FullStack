#!/usr/bin/env python
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
    query = query.strip()
    logger.info(f"Starting pipeline processing for query: '{query}'")
    try:
        query_validator.get_valid_query(query)
        logger.debug("Query validation successful")
    except Exception as e:
        logger.error(f"Query validation failed: {str(e)}")
        return {"type": "error", "result": f"Error validating query: {str(e)}"}
    classification_result = query_classifier.classify_query(query)
    logger.debug(f"Query classified as: {classification_result}")

    if classification_result == "error":
        logger.error("Query classification failed")
        return {"type": "error", "result": "Classification failed"}

    if classification_result == "report":
        logger.info("Query identified as report request, initiating report generation")
        try:
            report_result = report_generator.generate_report(query)
            return {"type": "report", "result": report_result}
        except Exception as e:
            return {"type": "error", "result": f"Error generating report: {str(e)}"}
    try:
        collection_name = collection_selector.select_collection_for_query(query)
        logger.debug(f"Selected JSON file: {collection_name}")
    except Exception as e:
        logger.error(f"JSON selection failed: {str(e)}")
        return {"type": "error", "result": f"Error selecting JSON: {str(e)}"}
    df = collection_processor._collection_to_dataframe(collection_name)
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
