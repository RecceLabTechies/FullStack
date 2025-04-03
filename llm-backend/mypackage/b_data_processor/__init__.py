"""
Data Processor Module

This module provides functionality for processing and selecting JSON data based on user queries,
including filtering, sorting, and data analysis capabilities.
"""

from mypackage.b_data_processor.collection_processor import (
    process_collection_query,
)
from mypackage.b_data_processor.collection_selector import (
    CollectionAnalysisResult,
    CollectionNotFoundError,
    select_collection_for_query,
)

__all__ = [
    "FilterCondition",
    "SortCondition",
    "FilterInfo",
    "CollectionNotFoundError",
    "CollectionAnalysisResult",
    "process_collection_query",
    "select_collection_for_query",
]
