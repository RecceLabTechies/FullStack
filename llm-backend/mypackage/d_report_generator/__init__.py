"""
Report Generator Module

This module provides functionality for generating reports based on user queries,
including chart generation and descriptive analysis.

The module handles:
- Breaking down complex report queries into individual analysis tasks
- Running each analysis subtask through appropriate pipeline components
- Assembling individual results into a comprehensive report format
"""

import logging

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

from mypackage.d_report_generator.generate_analysis_queries import (
    QueryItem,
    QueryList,
    QueryType,
    generate_analysis_queries,
)
from mypackage.d_report_generator.report_generator import (
    ReportResults,
    report_generator,
)
from mypackage.d_report_generator.truncated_pipeline import (
    run_truncated_pipeline,
)

logger.debug("d_report_generator module initialized")

__all__ = [
    "QueryItem",
    "QueryList",
    "QueryType",
    "ReportResults",
    "generate_analysis_queries",
    "report_generator",
    "run_truncated_pipeline",
]
