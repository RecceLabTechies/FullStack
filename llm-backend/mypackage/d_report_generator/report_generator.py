#!/usr/bin/env python
import logging
from typing import List, Protocol, Union

from pydantic import BaseModel

from mypackage.d_report_generator import truncated_pipeline
from mypackage.d_report_generator.generate_analysis_queries import (
    QueryList,
    generate_analysis_queries,
)

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


class ReportResults(BaseModel):
    results: List[Union[str, List[str]]]


class LLMResponse(Protocol):
    content: str


def report_generator(user_query: str) -> ReportResults:
    logger.info(f"Starting report generation for query: {user_query}")
    queryList: QueryList = generate_analysis_queries(user_query)
    logger.debug(f"Generated {len(queryList.queries)} analysis queries using Groq")

    results: List[Union[str, List[str]]] = []
    for queryItem in queryList.queries:
        logger.debug(f"Processing query: {queryItem}")
        result: Union[str, List[str]] = truncated_pipeline.run_truncated_pipeline(
            queryItem
        )
        results.append(result)
        logger.debug("Query processed successfully")

    logger.info(f"Report generation completed with {len(results)} results")
    return ReportResults(results=results)


if __name__ == "__main__":
    report_generator("What is the average spending per customer?")
