"""
Query Processor Module

This module provides functionality for classifying and validating user queries,
determining their type and ensuring they meet the required format and criteria.
"""

from mypackage.a_query_processor.query_classifier import (
    QueryType,
    QueryTypeEnum,
    classify_query,
)
from mypackage.a_query_processor.query_validator import (
    QueryValidationResult,
    get_valid_query,
)

__all__ = [
    # Types
    "QueryType",
    "QueryTypeEnum",
    "QueryValidationResult",
    # Main functions
    "classify_query",
    "get_valid_query",
]
