"""
Regular Generator Module

This module provides functionality for generating various types of data visualizations
and descriptions based on processed data, including chart generation and text descriptions.
"""

from mypackage.c_regular_generator.chart_generator import (
    ChartInfo,
    generate_chart,
)
from mypackage.c_regular_generator.description_generator import (
    generate_description,
)

__all__ = [
    "ChartInfo",
    "ColumnMatch",
    "ColumnStats",
    "generate_chart",
    "generate_description",
]
