"""
Regular Generator Module

This module provides functionality for generating various types of data visualizations
and descriptions based on processed data, including chart generation and text descriptions.
"""

from mypackage.c_regular_generator.chart_data_generator import (
    AxisConfig,
    ChartDataType,
    ChartInfo,
    ColumnMatch,
    ColumnStats,
    generate_chart_data,
)
from mypackage.c_regular_generator.description_generator import (
    generate_description,
)

__all__ = [
    # Types
    "AxisConfig",
    "ChartDataType",
    "ChartInfo",
    "ColumnMatch",
    "ColumnStats",
    # Main functions
    "generate_chart_data",
    "generate_description",
]
