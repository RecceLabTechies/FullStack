"""
Query Processing Module

This module provides tools for analyzing and processing user queries including:
- Classifying queries into types (description/report/chart/error)
- Validating query structure and intent
- Common validation patterns and data analysis keywords

The module ensures queries are properly categorized and validated before
they are processed by downstream components.
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

# Import components from submodules
from .query_classifier import (
    QueryType,
    QueryTypeEnum,
    classify_query,
)
from .query_validator import (
    DATA_ANALYSIS_KEYWORDS,
    INVALID_PATTERNS,
    InvalidPattern,
    ValidationResult,
    get_valid_query,
    normalize_query,
)

logger.debug("a_query_processor module initialized")

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
