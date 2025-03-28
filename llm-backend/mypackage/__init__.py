"""
MyPackage

A comprehensive package for query processing, data processing, regular expression generation,
and report generation.
"""

from mypackage.a_query_processor import (
    QueryType,
    QueryTypeEnum,
    QueryValidationResult,
    classify_query,
    get_valid_query,
)
from mypackage.b_data_processor import *
from mypackage.c_regular_generator import *
from mypackage.d_report_generator import *

__version__ = "0.1.0"

__all__ = [
    # Query Processor
    "QueryType",
    "QueryTypeEnum",
    "QueryValidationResult",
    "classify_query",
    "get_valid_query",
    # Add other main exports as needed
]
