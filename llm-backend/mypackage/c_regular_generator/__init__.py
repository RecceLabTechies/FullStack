"""
Regular Generator Module

This module provides functionality for generating various types of data visualizations
and descriptions based on processed data, including chart generation and text descriptions.

Key components:
- Chart generation for visual data representation
- Natural language descriptions of data trends and insights
- Support for multiple data formats and visualization types
"""

import logging

from mypackage.c_regular_generator.chart_generator import (
    ChartInfo,
    generate_chart,
)
from mypackage.c_regular_generator.description_generator import (
    generate_description,
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


logger.debug("c_regular_generator module initialized")

__all__ = [
    "ChartInfo",
    "ColumnMatch",
    "ColumnStats",
    "generate_chart",
    "generate_description",
]
