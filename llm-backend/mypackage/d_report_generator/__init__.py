"""
Report Generator Module

This module provides functionality for generating reports based on user queries,
including chart generation and descriptive analysis.
"""

from mypackage.d_report_generator.generate_analysis_queries import (
    QueryItem,
    QueryList,
    QueryType,
    generate_analysis_queries,
)
from mypackage.d_report_generator.report_generator import (
    ReportResults,
    generate_report,
)
from mypackage.d_report_generator.truncated_pipeline import (
    run_truncated_pipeline,
)

__all__ = [
    # Types
    "QueryItem",
    "QueryList",
    "QueryType",
    "ReportResults",
    # Main functions
    "generate_report",
    "generate_analysis_queries",
    "run_truncated_pipeline",
]
