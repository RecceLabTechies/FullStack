"""
Data Processor Module

This module provides functionality for processing and selecting JSON data based on user queries,
including filtering, sorting, and data analysis capabilities.
"""

from mypackage.b_data_processor.json_processor import (
    process_json_query,
)
from mypackage.b_data_processor.json_selector import (
    JSONFileNotFoundError,
    select_json_for_query,
)

__all__ = [
    # Exceptions
    "JSONFileNotFoundError",
    # Main functions
    "process_json_query",
    "select_json_for_query",
]
