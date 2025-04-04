#!/usr/bin/env python
"""
Chart Generator Module

This module provides functionality for generating data visualizations based on user queries
and DataFrame content. It uses a combination of machine learning (LLM) for chart selection
and matplotlib/seaborn for rendering.

Key components:
- Data analysis to extract column metadata
- LLM-based selection of appropriate visualization type and axes
- Chart rendering with matplotlib/seaborn
"""

import datetime
import logging
import os
import uuid
from io import BytesIO
from typing import List, Literal, Optional, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from langchain_core.prompts import ChatPromptTemplate
from mypackage.utils.llm_config import CHART_DATA_MODEL, get_groq_llm
from pandas.api.types import (
    is_bool_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
)
from pydantic import BaseModel, field_validator

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

logger.debug("chart_generator module initialized")


class ColumnMetadata(BaseModel):
    """
    Pydantic model for storing DataFrame column metadata.

    Attributes:
        name: Column name
        dtype: Data type (categorical, numeric, datetime, etc.)
        unique_values: List of unique values in the column (limited)
        sample_values: Sample of values from the column
    """

    name: str
    dtype: str
    unique_values: Optional[List[str]] = None
    sample_values: List[Union[str, int, float]]


class ChartInfo(BaseModel):
    """
    Pydantic model for chart configuration.

    Attributes:
        x_axis: Column name to use for x-axis
        y_axis: Column name to use for y-axis
        chart_type: Type of chart to create (line, bar, scatter, etc.)
    """

    x_axis: str
    y_axis: str
    chart_type: str

    @field_validator("chart_type")
    @classmethod
    def validate_chart_type(cls, v):
        """
        Validate that chart_type is one of the supported types.

        Args:
            v: The chart type value to validate

        Returns:
            Lowercase version of the validated chart type

        Raises:
            ValueError: If chart type is not in the list of valid types
        """
        valid_types = {"line", "scatter", "bar", "box", "heatmap"}
        if v.lower() not in valid_types:
            raise ValueError(f"Chart type must be one of: {', '.join(valid_types)}")
        return v.lower()

    model_config = {"frozen": True}


# Type alias for column data types
ColumnType = Literal["datetime", "numeric", "categorical", "boolean", "text"]


def _get_column_type(
    series: pd.Series,
) -> ColumnType:
    """
    Determine the semantic type of a pandas Series.

    This function analyzes the contents of a Series to determine its
    most appropriate type classification beyond just the pandas dtype.

    Args:
        series: The pandas Series to analyze

    Returns:
        A ColumnType value indicating the semantic type
    """
    logger.debug(f"Determining column type for series with dtype: {series.dtype}")

    if is_datetime64_any_dtype(series):
        logger.debug("Series identified as datetime type")
        return "datetime"
    elif is_numeric_dtype(series):
        logger.debug("Series identified as numeric type")
        return "numeric"
    elif isinstance(series.dtype, pd.CategoricalDtype):
        logger.debug(
            "Series identified as categorical type (explicit categorical dtype)"
        )
        return "categorical"
    elif is_bool_dtype(series):
        logger.debug("Series identified as boolean type")
        return "boolean"
    elif is_object_dtype(series) and series.nunique() / len(series) < 0.5:
        # Object type with relatively few unique values is likely categorical
        logger.debug("Series identified as categorical type (based on cardinality)")
        return "categorical"

    logger.debug("Series identified as text type (default)")
    return "text"


def extract_column_metadata(df: pd.DataFrame) -> List[ColumnMetadata]:
    """
    Extract structured metadata about DataFrame columns.

    This function analyzes each column in the DataFrame to determine its
    semantic type, extract sample values, and collect unique values for
    categorical columns.

    Args:
        df: The pandas DataFrame to analyze

    Returns:
        List of ColumnMetadata objects describing each column
    """
    logger.info(f"Extracting column metadata from DataFrame with shape {df.shape}")
    metadata = []

    for col in df.columns:
        logger.debug(f"Processing column: {col}")
        col_type = _get_column_type(df[col])
        unique_vals = None
        sample_vals = df[col].dropna().head(5).tolist()

        # Convert datetime objects to strings
        if col_type == "datetime":
            logger.debug(f"Converting datetime values to strings for column: {col}")
            sample_vals = [str(v) for v in sample_vals]

        # Extract unique values for categorical and text columns
        if col_type in ["categorical", "text"]:
            logger.debug(f"Extracting unique values for categorical/text column: {col}")
            unique_vals = df[col].dropna().unique().tolist()
            if len(unique_vals) > 20:
                logger.debug(
                    f"Limiting unique values to 20 (from {len(unique_vals)}) for column: {col}"
                )
                unique_vals = unique_vals[:20]

        metadata.append(
            ColumnMetadata(
                name=col,
                dtype=col_type,
                unique_values=unique_vals,
                sample_values=sample_vals,
            )
        )
        logger.debug(f"Added metadata for column: {col} (type: {col_type})")

    logger.info(f"Extracted metadata for {len(metadata)} columns")
    return metadata


def enhance_query_with_metadata(
    original_query: str, metadata: List[ColumnMetadata]
) -> str:
    """
    Enhance user query with column metadata to guide LLM interpretation.

    This function adds contextual information about available columns and
    highlights columns that appear to be relevant to the query.

    Args:
        original_query: The user's raw query text
        metadata: List of ColumnMetadata objects from the DataFrame

    Returns:
        Enhanced query string with added context
    """
    logger.info(f"Enhancing query with metadata: {original_query}")
    emphasized = []
    query_lower = original_query.lower()

    # Identify columns referenced in the query
    for col in metadata:
        # Check if column name appears in query
        if col.name.lower() in query_lower:
            emphasized.append(f"'{col.name}' ({col.dtype})")
            logger.debug(f"Column directly referenced in query: {col.name}")
        # Check for semantic matches
        elif any(synonym in query_lower for synonym in _get_column_synonyms(col.name)):
            emphasized.append(f"'{col.name}' ({col.dtype})")
            logger.debug(f"Column matched via synonym in query: {col.name}")

    # Construct enhanced query
    enhanced = f"{original_query}\n\nData Context:\n- Columns: {', '.join([f'{col.name} ({col.dtype})' for col in metadata])}"
    if emphasized:
        enhanced += (
            f"\n- Emphasized Columns: {', '.join(emphasized)} should be prioritized"
        )
        logger.debug(f"Emphasized {len(emphasized)} columns in enhanced query")

    logger.debug(f"Enhanced query length: {len(enhanced)} chars")
    return enhanced


def _get_column_synonyms(col_name: str) -> List[str]:
    """
    Generate potential synonyms for column names to improve matching.

    This function returns common synonyms for frequently used column names
    to help match user query terms to the appropriate columns.

    Args:
        col_name: Column name to find synonyms for

    Returns:
        List of synonym strings
    """
    logger.debug(f"Getting synonyms for column: {col_name}")
    synonyms = {
        "date": ["time", "day", "month", "year"],
        "sales": ["revenue", "income"],
        "price": ["cost", "value"],
        "category": ["type", "group"],
    }
    result = synonyms.get(col_name.lower(), [])
    logger.debug(f"Found {len(result)} synonyms for column: {col_name}")
    return result


def get_llm_chart_selection(query: str, metadata: List[ColumnMetadata]) -> ChartInfo:
    """
    Use LLM to select appropriate chart type and axes based on the query.

    This function sends the query and column metadata to an LLM, which
    then recommends the most appropriate visualization type and columns
    to use for the x and y axes.

    Args:
        query: The user's query (possibly enhanced with metadata)
        metadata: List of ColumnMetadata objects from the DataFrame

    Returns:
        ChartInfo object containing the selected chart configuration

    Raises:
        ValueError: If the LLM response cannot be parsed into valid chart info
    """
    logger.info(f"Getting chart selection for query: {query}")

    # Define prompt template for LLM
    prompt_template = ChatPromptTemplate.from_template(
        """You are a chart configuration assistant. Your ONLY task is to analyze the visualization request and select appropriate columns.

        User Query: {query}

        Available Columns:
        {columns}

        CRITICAL INSTRUCTIONS:
        1. You MUST respond with EXACTLY 3 lines in this format:
           x_axis: [column]
           y_axis: [column]
           chart_type: [type]
        2. The columns MUST be from the provided column names
        3. Chart type MUST be one of: line, bar, scatter, box, heatmap
        4. DO NOT include any other text, explanation, or formatting
        5. Each line MUST start with the exact keys: x_axis:, y_axis:, chart_type:

        Example Valid Response:
        x_axis: date
        y_axis: sales
        chart_type: line"""
    )

    # Format column information for the prompt
    columns_str = "\n".join(
        [
            f"- {col.name} ({col.dtype})"
            + (
                f" [Categories: {', '.join(map(str, col.unique_values))}]"
                if col.unique_values
                else ""
            )
            for col in metadata
        ]
    )

    logger.debug("Preparing prompt for Groq LLM")
    model = get_groq_llm(CHART_DATA_MODEL)
    chain = prompt_template | model

    logger.debug("Sending prompt to Groq LLM")
    response = chain.invoke({"query": query, "columns": columns_str})
    logger.debug(f"Received response from Groq LLM: {response.content}")

    # Parse the response into chart configuration
    try:
        logger.debug("Parsing LLM response into chart configuration")
        # Split by newlines and clean up
        lines = [
            line.strip()
            for line in response.content.strip().split("\n")
            if line.strip()
        ]

        if len(lines) != 3:
            error_msg = f"Expected 3 lines in LLM response, got {len(lines)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        config = {}
        for line in lines:
            key, value = line.split(":", 1)
            key = key.strip()
            if key not in ["x_axis", "y_axis", "chart_type"]:
                error_msg = f"Invalid key in LLM response: {key}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            config[key] = value.strip().lower()
            logger.debug(f"Parsed {key}: {config[key]}")

        chart_info = ChartInfo(
            x_axis=config["x_axis"],
            y_axis=config["y_axis"],
            chart_type=config["chart_type"],
        )
        logger.info(
            f"Selected chart type: {chart_info.chart_type} with x: {chart_info.x_axis}, y: {chart_info.y_axis}"
        )
        return chart_info
    except Exception as e:
        logger.error(f"Failed to parse LLM response: {response.content}")
        logger.error(f"Parse error: {str(e)}", exc_info=True)
        raise ValueError(f"Invalid LLM response format: {str(e)}")


def _create_seaborn_plot(df: pd.DataFrame, chart_info: "ChartInfo") -> plt.Figure:
    """
    Create a seaborn plot based on the chart configuration.

    This function renders a visualization using seaborn based on the
    DataFrame and configuration specified in chart_info.

    Args:
        df: The pandas DataFrame containing the data to visualize
        chart_info: ChartInfo object specifying the chart configuration

    Returns:
        Matplotlib Figure object with the rendered chart

    Raises:
        ValueError: If the chart cannot be created with the given configuration
    """
    logger.info(
        f"Creating {chart_info.chart_type} plot with x_axis: {chart_info.x_axis}, y_axis: {chart_info.y_axis}"
    )

    # Prepare plotting area
    plt.clf()
    fig, ax = plt.subplots(figsize=(10, 6))

    # Log data info before plotting for troubleshooting
    x_count = df[chart_info.x_axis].nunique()
    y_min = df[chart_info.y_axis].min()
    y_max = df[chart_info.y_axis].max()

    logger.debug(f"X-axis column '{chart_info.x_axis}' has {x_count} unique values")
    logger.debug(f"Y-axis column '{chart_info.y_axis}' range: [{y_min}, {y_max}]")

    try:
        # Choose the appropriate chart type
        if chart_info.chart_type == "line":
            logger.debug("Generating line plot")
            sns.lineplot(data=df, x=chart_info.x_axis, y=chart_info.y_axis, ax=ax)
        elif chart_info.chart_type == "scatter":
            logger.debug("Generating scatter plot")
            sns.scatterplot(data=df, x=chart_info.x_axis, y=chart_info.y_axis, ax=ax)
        elif chart_info.chart_type == "bar":
            logger.debug("Generating bar plot")
            # Aggregate if necessary for bar charts with many unique x values
            if x_count > 15:
                logger.debug(
                    f"Too many unique values ({x_count}) for bar chart, aggregating"
                )
                # Sort by mean of y values
                top_x = (
                    df.groupby(chart_info.x_axis)[chart_info.y_axis]
                    .mean()
                    .nlargest(15)
                    .index
                )
                filtered_df = df[df[chart_info.x_axis].isin(top_x)]
                sns.barplot(
                    data=filtered_df, x=chart_info.x_axis, y=chart_info.y_axis, ax=ax
                )
            else:
                sns.barplot(data=df, x=chart_info.x_axis, y=chart_info.y_axis, ax=ax)
        elif chart_info.chart_type == "box":
            logger.debug("Generating box plot")
            sns.boxplot(data=df, x=chart_info.x_axis, y=chart_info.y_axis, ax=ax)
        elif chart_info.chart_type == "heatmap":
            logger.debug("Generating heatmap")
            pivot_data = df.pivot_table(
                index=chart_info.x_axis,
                columns=chart_info.y_axis,
                aggfunc="size",
                fill_value=0,
            )
            sns.heatmap(pivot_data, cmap="YlGnBu", ax=ax)
        else:
            error_msg = f"Unsupported chart type: {chart_info.chart_type}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Enhance chart aesthetics
        plt.title(f"{chart_info.y_axis} by {chart_info.x_axis}")
        plt.tight_layout()

        # Handle long x-axis labels
        if x_count > 10:
            logger.debug("Rotating x-axis labels for better readability")
            plt.xticks(rotation=45, ha="right")

        logger.info("Successfully created plot")
        return fig
    except Exception as e:
        logger.error(f"Error creating plot: {str(e)}", exc_info=True)
        raise ValueError(f"Failed to create {chart_info.chart_type} chart: {str(e)}")


def generate_chart(df: pd.DataFrame, query: str) -> bytes:
    """
    Main function to generate a chart based on a user query.

    Returns:
        PNG image bytes of the generated chart
    """
    logger.info(f"Generating chart for query: {query}")

    try:
        # Step 1: Extract metadata
        logger.debug("Extracting column metadata")
        metadata = extract_column_metadata(df)

        # Step 2: Enhance query with metadata context
        logger.debug("Enhancing query with metadata")
        enhanced_query = enhance_query_with_metadata(query, metadata)

        # Step 3: Get chart configuration from LLM
        logger.debug("Getting chart configuration from LLM")
        chart_info = get_llm_chart_selection(enhanced_query, metadata)

        # Step 4: Create the chart
        logger.debug("Creating the chart visualization")
        fig = _create_seaborn_plot(df, chart_info)

        # Step 5: Create in-memory image buffer
        logger.debug("Creating in-memory image buffer")
        img_buffer = BytesIO()
        fig.savefig(
            img_buffer, format="png", dpi=300, bbox_inches="tight", facecolor="white"
        )
        img_buffer.seek(0)
        image_bytes = img_buffer.getvalue()
        plt.close(fig)

        logger.info("Chart generation complete")
        return image_bytes

    except Exception as e:
        logger.error(f"Chart generation failed: {str(e)}", exc_info=True)
        raise ValueError(f"Failed to generate chart: {str(e)}")


if __name__ == "__main__":
    # Set up console logging for direct script execution
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Set to DEBUG for more detailed logging
    root_logger.addHandler(console_handler)

    # Test with sample data
    logger.info("Testing chart generator with sample data")

    # Create sample DataFrame
    df = pd.DataFrame(
        {
            "month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"] * 3,
            "sales": np.random.randint(1000, 5000, 18),
            "category": ["Electronics", "Clothing", "Home"] * 6,
        }
    )

    # Test query
    test_query = "Show me monthly sales as a bar chart"

    try:
        image_bytes = generate_chart(df, test_query)
        logger.info("Chart generated successfully")
        print(
            f"\nChart generated successfully, image bytes length: {len(image_bytes)}\n"
        )
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
