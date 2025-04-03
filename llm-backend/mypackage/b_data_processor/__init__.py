"""
Data Processor Module

This module provides functionality for processing and selecting JSON data based on user queries,
including filtering, sorting, and data analysis capabilities.
"""

from mypackage.b_data_processor.json_processor import (
    process_json_query,
)
from mypackage.b_data_processor.json_selector import (
    CollectionNotFoundError,
)

__all__ = [
    # Exceptions
    "CollectionNotFoundError",
    # Main functions
    "process_json_query",
]
