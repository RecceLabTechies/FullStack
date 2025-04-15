"""
Data Processor Module

This module provides functionality for processing and selecting data based on user queries,
including filtering, sorting, and data analysis capabilities.

The module handles:
- Table selection based on query requirements
- Data filtering and transformation
- Structured query processing
"""

import logging

from mypackage.b_data_processor.table_processor import (
    process_table_query,
)
from mypackage.b_data_processor.table_selector import (
    TableAnalysisResult,
    TableNotFoundError,
    select_table_for_query,
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
    "TableNotFoundError",
    "TableAnalysisResult",
    "process_table_query",
    "select_table_for_query",
]
