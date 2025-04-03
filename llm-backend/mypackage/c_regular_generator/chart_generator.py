#!/usr/bin/env python
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
from minio import Minio
from pandas.api.types import (
    is_bool_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
)
from pydantic import BaseModel, field_validator

from mypackage.utils.llm_config import CHART_DATA_MODEL, get_groq_llm

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


MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "temp-charts")

logger.info(f"Initializing MinIO client with endpoint: {MINIO_ENDPOINT}")
MINIO_CLIENT = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False,
)


class ColumnMetadata(BaseModel):
    name: str
    dtype: str
    unique_values: Optional[List[str]] = None
    sample_values: List[Union[str, int, float]]


class ChartInfo(BaseModel):
    x_axis: str
    y_axis: str
    chart_type: str

    @field_validator("chart_type")
    @classmethod
    def validate_chart_type(cls, v):
        valid_types = {"line", "scatter", "bar", "box", "heatmap"}
        if v.lower() not in valid_types:
            raise ValueError(f"Chart type must be one of: {', '.join(valid_types)}")
        return v.lower()

    model_config = {"frozen": True}


ColumnType = Literal["datetime", "numeric", "categorical", "boolean", "text"]


def _get_column_type(
    series: pd.Series,
) -> ColumnType:
    if is_datetime64_any_dtype(series):
        return "datetime"
    elif is_numeric_dtype(series):
        return "numeric"
    elif isinstance(series.dtype, pd.CategoricalDtype):
        return "categorical"
    elif is_bool_dtype(series):
        return "boolean"
    elif is_object_dtype(series) and series.nunique() / len(series) < 0.5:
        return "categorical"
    return "text"


def extract_column_metadata(df: pd.DataFrame) -> List[ColumnMetadata]:
    """Extract structured metadata about DataFrame columns"""
    metadata = []
    for col in df.columns:
        col_type = _get_column_type(df[col])
        unique_vals = None
        sample_vals = df[col].dropna().head(5).tolist()

        # Convert datetime objects to strings
        if col_type == "datetime":
            sample_vals = [str(v) for v in sample_vals]

        if col_type in ["categorical", "text"]:
            unique_vals = df[col].dropna().unique().tolist()
            if len(unique_vals) > 20:
                unique_vals = unique_vals[:20]

        metadata.append(
            ColumnMetadata(
                name=col,
                dtype=col_type,
                unique_values=unique_vals,
                sample_values=sample_vals,  # Use converted values
            )
        )
    return metadata


def enhance_query_with_metadata(
    original_query: str, metadata: List[ColumnMetadata]
) -> str:
    """Enhance user query with column metadata emphasis"""
    emphasized = []
    query_lower = original_query.lower()

    for col in metadata:
        # Check if column name appears in query
        if col.name.lower() in query_lower:
            emphasized.append(f"'{col.name}' ({col.dtype})")
        # Check for semantic matches
        elif any(synonym in query_lower for synonym in _get_column_synonyms(col.name)):
            emphasized.append(f"'{col.name}' ({col.dtype})")

    enhanced = f"{original_query}\n\nData Context:\n- Columns: {', '.join([f'{col.name} ({col.dtype})' for col in metadata])}"
    if emphasized:
        enhanced += (
            f"\n- Emphasized Columns: {', '.join(emphasized)} should be prioritized"
        )
    return enhanced


def _get_column_synonyms(col_name: str) -> List[str]:
    """Generate potential synonyms for column names"""
    synonyms = {
        "date": ["time", "day", "month", "year"],
        "sales": ["revenue", "income"],
        "price": ["cost", "value"],
        "category": ["type", "group"],
    }
    return synonyms.get(col_name.lower(), [])


def get_llm_chart_selection(query: str, metadata: List[ColumnMetadata]) -> ChartInfo:
    """Get chart parameters from LLM with strict output formatting"""
    logger.info(f"Getting chart selection for query: {query}")
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

    model = get_groq_llm(CHART_DATA_MODEL)
    chain = prompt_template | model

    response = chain.invoke({"query": query, "columns": columns_str})

    # Improved response parsing
    try:
        # Split by newlines and clean up
        lines = [
            line.strip()
            for line in response.content.strip().split("\n")
            if line.strip()
        ]

        if len(lines) != 3:
            raise ValueError(f"Expected 3 lines, got {len(lines)}")

        config = {}
        for line in lines:
            key, value = line.split(":", 1)
            key = key.strip()
            if key not in ["x_axis", "y_axis", "chart_type"]:
                raise ValueError(f"Invalid key: {key}")
            config[key] = value.strip().lower()

        return ChartInfo(
            x_axis=config["x_axis"],
            y_axis=config["y_axis"],
            chart_type=config["chart_type"],
        )
    except Exception as e:
        logger.error(f"Failed to parse LLM response: {response.content}")
        logger.error(f"Parse error: {str(e)}")
        raise ValueError("Invalid LLM response format")


def _create_seaborn_plot(df: pd.DataFrame, chart_info: "ChartInfo") -> plt.Figure:
    logger.info(
        f"Creating {chart_info.chart_type} plot with x_axis: {chart_info.x_axis}, y_axis: {chart_info.y_axis}"
    )
    plt.clf()
    fig, ax = plt.subplots(figsize=(10, 6))

    # Log data info before plotting
    logger.info(f"X-axis unique values count: {df[chart_info.x_axis].nunique()}")
    logger.info(
        f"Y-axis value range: [{df[chart_info.y_axis].min()}, {df[chart_info.y_axis].max()}]"
    )

    if chart_info.chart_type == "line":
        logger.info("Generating line plot")
        sns.lineplot(data=df, x=chart_info.x_axis, y=chart_info.y_axis, ax=ax)
    elif chart_info.chart_type == "scatter":
        logger.info("Generating scatter plot")
        sns.scatterplot(data=df, x=chart_info.x_axis, y=chart_info.y_axis, ax=ax)
    elif chart_info.chart_type == "bar":
        logger.info("Generating bar plot")
        sns.barplot(data=df, x=chart_info.x_axis, y=chart_info.y_axis, ax=ax)
    elif chart_info.chart_type == "box":
        logger.info("Generating box plot")
        sns.boxplot(data=df, x=chart_info.x_axis, y=chart_info.y_axis, ax=ax)
    elif chart_info.chart_type == "heatmap":
        logger.info("Generating heatmap")
        pivot_table = pd.crosstab(df[chart_info.x_axis], df[chart_info.y_axis])
        sns.heatmap(pivot_table, annot=True, cmap="YlGnBu", ax=ax)

    plt.title(f"{chart_info.y_axis} by {chart_info.x_axis}")
    plt.xticks(rotation=45)
    plt.tight_layout()
    logger.info("Plot generation completed successfully")

    return fig


def _save_plot_to_minio(fig: plt.Figure, chart_type: str) -> str:
    try:
        filename = f"{chart_type}_{uuid.uuid4()}.png"

        buf = BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=300)
        buf.seek(0)

        MINIO_CLIENT.put_object(
            BUCKET_NAME, filename, buf, buf.getbuffer().nbytes, content_type="image/png"
        )

        url = f"/api/minio/{BUCKET_NAME}/{filename}"
        logger.info(f"Saved plot to MinIO: {url}")
        return url
    except Exception as e:
        logger.error(f"Failed to save plot to MinIO: {str(e)}")
        raise


def generate_chart(df: pd.DataFrame, query: str) -> str:
    """Modified pipeline following new requirements"""
    logger.info(f"Starting chart generation for query: {query}")
    logger.info(f"DataFrame shape: {df.shape}")

    # Step 1: Extract metadata
    metadata = extract_column_metadata(df)
    logger.info(f"Extracted metadata for {len(metadata)} columns")

    # Step 2: Enhance query with metadata
    enhanced_query = enhance_query_with_metadata(query, metadata)
    logger.info(f"Enhanced query: {enhanced_query}")

    # Step 3: Get LLM selection
    chart_info = get_llm_chart_selection(enhanced_query, metadata)
    logger.info(
        f"Selected chart configuration: type={chart_info.chart_type}, x={chart_info.x_axis}, y={chart_info.y_axis}"
    )

    # Validate columns exist in DataFrame
    if chart_info.x_axis not in df.columns or chart_info.y_axis not in df.columns:
        logger.error(
            f"Invalid columns selected. Available columns: {df.columns.tolist()}"
        )
        raise ValueError("LLM selected invalid columns")

    # Step 4: Generate and save chart
    fig = _create_seaborn_plot(df, chart_info)
    image_url = _save_plot_to_minio(fig, chart_info.chart_type)
    plt.close(fig)
    logger.info(f"Chart generated and saved successfully at: {image_url}")

    return image_url


if __name__ == "__main__":
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)

    test_data = {
        "date": pd.date_range(start="2023-01-01", periods=100),
        "sales": np.random.normal(1000, 200, 100),
        "customers": np.random.randint(50, 200, 100),
        "category": np.random.choice(["A", "B", "C"], 100),
    }
    test_df = pd.DataFrame(test_data)
    test_query = "Show me sales over time"

    logger.info(f"Testing with query: '{test_query}'")
    try:
        chart_data = generate_chart(test_df, test_query)
        print("Generated chart visualization URL:")
        print(f"{chart_data}")
    except Exception as e:
        logger.error(f"Error in test: {str(e)}", exc_info=True)
