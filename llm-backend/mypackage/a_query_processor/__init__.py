"""
Query Processing Module

Exposes core functionality for:
- Classifying queries into types (description/report/chart/error)
- Validating query structure and intent
- Common validation patterns and data analysis keywords
"""

from .query_classifier import QueryType, QueryTypeEnum, classify_query
from .query_validator import (
    DATA_ANALYSIS_KEYWORDS,
    INVALID_PATTERNS,
    InvalidPattern,
    ValidationResult,
    get_valid_query,
    normalize_query,
)

__all__ = [
    # Classifier components
    "QueryType",
    "QueryTypeEnum",
    "classify_query",
    # Validator components
    "get_valid_query",
    "normalize_query",
    "ValidationResult",
    "INVALID_PATTERNS",
    "DATA_ANALYSIS_KEYWORDS",
    "InvalidPattern",
]
