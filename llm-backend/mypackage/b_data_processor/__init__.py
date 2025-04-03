"""
Data Processor Module

This module provides functionality for processing and selecting JSON data based on user queries,
including filtering, sorting, and data analysis capabilities.

The module handles:
- Collection selection based on query requirements
- Data filtering and transformation
- Structured query processing
"""

import logging

from mypackage.b_data_processor.collection_processor import (
    process_collection_query,
)
from mypackage.b_data_processor.collection_selector import (
    CollectionAnalysisResult,
    CollectionNotFoundError,
    select_collection_for_query,
)

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


logger.debug("b_data_processor module initialized")

__all__ = [
    "FilterCondition",
    "SortCondition",
    "FilterInfo",
    "CollectionNotFoundError",
    "CollectionAnalysisResult",
    "process_collection_query",
    "select_collection_for_query",
]
