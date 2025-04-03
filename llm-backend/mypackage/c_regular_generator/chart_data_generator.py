#!/usr/bin/env python
import logging
import numpy as np
import os
import uuid
from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from minio import Minio
from io import BytesIO
from langchain_core.prompts import ChatPromptTemplate
from mypackage.utils.llm_config import get_groq_llm, CHART_DATA_MODEL
from pandas.api.types import (
    is_bool_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
)
from pydantic import BaseModel, field_validator

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.propagate = False

# Add handler if not already added
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

DEFAULT_MODEL_NAME = CHART_DATA_MODEL

# MinIO client configuration
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "temp-charts")

logger.info(f"Initializing MinIO client with endpoint: {MINIO_ENDPOINT}")
MINIO_CLIENT = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False,  # Set to True if using HTTPS
)

# Ensure bucket exists
try:
    if not MINIO_CLIENT.bucket_exists(BUCKET_NAME):
        logger.info(f"Creating bucket: {BUCKET_NAME}")
        MINIO_CLIENT.make_bucket(BUCKET_NAME)
        logger.info(f"Successfully created bucket: {BUCKET_NAME}")
except Exception as e:
    logger.error(f"Failed to initialize MinIO bucket: {str(e)}")
    # Don't raise the exception here, let the code continue and fail gracefully if needed


def _save_plot_to_minio(fig, chart_type: str) -> str:
    """
    Save a matplotlib figure to MinIO and return the URL.

    Args:
        fig: matplotlib figure object
        chart_type: type of chart for filename

    Returns:
        URL to access the saved image
    """
    try:
        # Generate unique filename
        filename = f"{chart_type}_{uuid.uuid4()}.png"

        # Save plot to bytes buffer
        buf = BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=300)
        buf.seek(0)

        # Upload to MinIO
        MINIO_CLIENT.put_object(
            BUCKET_NAME, filename, buf, buf.getbuffer().nbytes, content_type="image/png"
        )

        # Generate URL
        url = f"/api/minio/{BUCKET_NAME}/{filename}"
        logger.info(f"Saved plot to MinIO: {url}")
        return url
    except Exception as e:
        logger.error(f"Failed to save plot to MinIO: {str(e)}")
        raise


def _create_seaborn_plot(df: pd.DataFrame, chart_info: "ChartInfo") -> plt.Figure:
    """
    Create a seaborn plot based on chart type and data.

    Args:
        df: Input DataFrame
        chart_info: ChartInfo object with plot configuration

    Returns:
        matplotlib Figure object
    """
    plt.clf()
    fig, ax = plt.subplots(figsize=(10, 6))

    if chart_info.chart_type == "line":
        sns.lineplot(data=df, x=chart_info.x_axis, y=chart_info.y_axis, ax=ax)
    elif chart_info.chart_type == "scatter":
        sns.scatterplot(data=df, x=chart_info.x_axis, y=chart_info.y_axis, ax=ax)
    elif chart_info.chart_type == "bar":
        sns.barplot(data=df, x=chart_info.x_axis, y=chart_info.y_axis, ax=ax)
    elif chart_info.chart_type == "box":
        sns.boxplot(data=df, x=chart_info.x_axis, y=chart_info.y_axis, ax=ax)
    elif chart_info.chart_type == "heatmap":
        pivot_table = pd.crosstab(df[chart_info.x_axis], df[chart_info.y_axis])
        sns.heatmap(pivot_table, annot=True, cmap="YlGnBu", ax=ax)

    plt.title(f"{chart_info.y_axis} by {chart_info.x_axis}")
    plt.xticks(rotation=45)
    plt.tight_layout()

    return fig


class ColumnStats(BaseModel):
    type: str
    unique_count: int
    missing_count: int
    total_count: int
    min: Optional[float] = None
    max: Optional[float] = None
    mean: Optional[float] = None
    median: Optional[float] = None
    categories: Optional[Dict[str, int]] = None

    model_config = {"extra": "allow"}


class ColumnMatch(BaseModel):
    score: int
    type: str
    reasons: List[str]
    stats: ColumnStats


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


class AxisConfig(TypedDict):
    dataKey: str
    type: str
    label: str


def _get_column_type(series: pd.Series) -> str:
    """
    Determine the data type of a pandas Series for charting purposes.

    Args:
        series: The pandas Series to analyze

    Returns:
        String representing the column type: "datetime", "numeric", "categorical", "boolean", or "text"
    """
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


def _get_column_stats(df: pd.DataFrame, column: str) -> ColumnStats:
    """
    Calculate statistics for a DataFrame column.

    Args:
        df: Input DataFrame
        column: Column name to analyze

    Returns:
        ColumnStats object with statistics about the column
    """
    stats_dict = {
        "type": _get_column_type(df[column]),
        "unique_count": df[column].nunique(),
        "missing_count": df[column].isna().sum(),
        "total_count": len(df[column]),
    }

    if stats_dict["type"] == "numeric":
        stats_dict.update(
            {
                "min": float(df[column].min()),
                "max": float(df[column].max()),
                "mean": float(df[column].mean()),
                "median": float(df[column].median()),
            }
        )
    elif stats_dict["type"] == "categorical":
        stats_dict["categories"] = df[column].value_counts().to_dict()

    return ColumnStats(**stats_dict)


def _extract_key_terms(query: str) -> List[str]:
    """
    Extract key terms from a query by removing stop words and domain-specific terms.

    Args:
        query: User query string

    Returns:
        List of key terms extracted from the query
    """
    words = query.lower().split()

    stop_words = {
        "a",
        "an",
        "the",
        "in",
        "on",
        "at",
        "for",
        "to",
        "of",
        "and",
        "or",
        "is",
        "are",
        "was",
        "were",
        "chart",
        "plot",
        "graph",
        "show",
        "display",
        "visualize",
        "visualization",
        "data",
    }

    cleaned_words = [word.strip(",.;:") for word in words]
    return [word for word in cleaned_words if word not in stop_words and len(word) > 2]


def _allow_direct_column_selection(df: pd.DataFrame, query: str) -> List[str]:
    """
    Attempt to directly identify column names in the query string.

    Args:
        df: Input DataFrame
        query: User query string

    Returns:
        List of identified column names from the query (up to 2)
    """
    query_lower = query.lower()
    potential_columns = []

    column_lower_dict = {col.lower(): col for col in df.columns}

    for connecting_word in [" and ", " vs ", " versus ", " against ", " with "]:
        if connecting_word in query_lower:
            parts = query_lower.split(connecting_word)
            if len(parts) == 2:
                left_side = parts[0].strip().split()
                right_side = parts[1].strip().split()

                if left_side:
                    left_term = left_side[-1]
                    for col_lower, col in column_lower_dict.items():
                        if (
                            left_term == col_lower
                            or left_term in col_lower
                            or col_lower in left_term
                        ):
                            potential_columns.append(col)
                            break

                if right_side:
                    right_term = right_side[0]
                    for col_lower, col in column_lower_dict.items():
                        if (
                            right_term == col_lower
                            or right_term in col_lower
                            or col_lower in right_term
                        ):
                            potential_columns.append(col)
                            break

                if len(potential_columns) == 2:
                    return potential_columns

    if len(query_lower.split()) == 1 and len(query_lower) > 5:
        word = query_lower.strip()
        found_columns = []

        sorted_cols = sorted(column_lower_dict.keys(), key=len, reverse=True)

        remaining = word
        while remaining and len(remaining) > 2:
            matched = False
            for col_lower in sorted_cols:
                if remaining.startswith(col_lower):
                    found_columns.append(column_lower_dict[col_lower])
                    remaining = remaining[len(col_lower) :]
                    matched = True
                    break
                elif remaining.endswith(col_lower):
                    found_columns.append(column_lower_dict[col_lower])
                    remaining = remaining[: -len(col_lower)]
                    matched = True
                    break

            if not matched:
                if len(remaining) > len(word) // 2:
                    remaining = remaining[1:]
                else:
                    remaining = remaining[:-1]

        if found_columns and len(found_columns) >= 2:
            return list(dict.fromkeys(found_columns))[:2]

    for keyword in [
        "about",
        "analyze",
        "show",
        "of",
        "for",
        "chart",
        "plot",
        "graph",
        "visualize",
    ]:
        if keyword in query_lower:
            after_keyword = query_lower.split(keyword, 1)[1].strip()

            comma_chunks = [chunk.strip() for chunk in after_keyword.split(",")]

            for chunk in comma_chunks:
                chunk_words = chunk.split()
                if len(chunk_words) > 1:
                    whole_chunk_match = False
                    for col in df.columns:
                        if col.lower() == chunk.strip() or chunk.strip() in col.lower():
                            potential_columns.append(chunk.strip())
                            whole_chunk_match = True
                            break

                    if not whole_chunk_match:
                        if " and " in chunk:
                            and_parts = chunk.split(" and ")
                            if len(and_parts) == 2:
                                left_term = and_parts[0].strip()
                                right_term = and_parts[1].strip()
                                left_match = right_match = None

                                for col_lower, col in column_lower_dict.items():
                                    if (
                                        left_term == col_lower
                                        or left_term in col_lower
                                        or col_lower in left_term
                                    ):
                                        left_match = col
                                    if (
                                        right_term == col_lower
                                        or right_term in col_lower
                                        or col_lower in right_term
                                    ):
                                        right_match = col

                                if left_match:
                                    potential_columns.append(left_match)
                                if right_match:
                                    potential_columns.append(right_match)

                                if left_match and right_match:
                                    return [left_match, right_match]

                        potential_columns.extend(chunk_words)
                else:
                    potential_columns.append(chunk)

            break

    if not potential_columns:
        if "," in query_lower:
            potential_columns = [col.strip() for col in query_lower.split(",")]
        else:
            potential_columns = query_lower.split()

    valid_columns = []

    for potential in potential_columns:
        clean_potential = potential.strip().split()
        if clean_potential and clean_potential[-1] in ["and", "or"]:
            clean_potential = clean_potential[:-1]
        if clean_potential and clean_potential[0] in ["and", "or"]:
            clean_potential = clean_potential[1:]

        clean_str = " ".join(clean_potential).strip(",.;: ")

        if clean_str in [
            "me",
            "to",
            "on",
            "with",
            "the",
            "a",
            "an",
            "in",
            "is",
            "are",
            "of",
            "for",
            "it",
            "tell",
            "chart",
            "plot",
            "graph",
            "visualize",
            "show",
            "display",
            "visualization",
        ]:
            continue

        if clean_str in column_lower_dict:
            valid_columns.append(column_lower_dict[clean_str])
            continue

        if clean_str.endswith("s") and clean_str[:-1] in column_lower_dict:
            valid_columns.append(column_lower_dict[clean_str[:-1]])
            continue
        if clean_str + "s" in column_lower_dict:
            valid_columns.append(column_lower_dict[clean_str + "s"])
            continue

        matched = False
        for col_lower, col in column_lower_dict.items():
            if clean_str in col_lower or col_lower in clean_str:
                valid_columns.append(col)
                matched = True
                break

        if not matched and len(clean_str) > 2:
            for col_lower, col in column_lower_dict.items():
                if any(
                    word in col_lower for word in clean_str.split() if len(word) > 2
                ):
                    valid_columns.append(col)
                    break

    unique_cols = list(dict.fromkeys(valid_columns))

    return unique_cols[: min(2, len(unique_cols))]


def _match_columns_to_query(df: pd.DataFrame, query: str) -> Dict[str, ColumnMatch]:
    """
    Match columns to a query based on semantic relevance and query terms.

    Args:
        df: Input DataFrame
        query: User query string

    Returns:
        Dictionary mapping column names to ColumnMatch objects with scores and reasons
    """
    logger.info(f"Matching columns to query: '{query}'")
    query_terms = _extract_key_terms(query)
    matches = {}
    query_lower = query.lower()

    direct_mentions = []
    for column in df.columns:
        if column.lower() in query_lower:
            direct_mentions.append(column)

    if direct_mentions and len(direct_mentions) >= 2:
        logger.debug(f"Found direct column mentions: {direct_mentions}")
        for column in direct_mentions:
            stats = _get_column_stats(df, column)
            matches[column] = ColumnMatch(
                score=10,
                type=stats.type,
                reasons=["Directly mentioned in query"],
                stats=stats,
            )
        return matches

    for column in df.columns:
        column_lower = column.lower()
        stats = _get_column_stats(df, column)
        score = 0
        match_reasons = []

        for term in query_terms:
            if term == column_lower:
                score += 5
                match_reasons.append(f"Column name exactly matches term '{term}'")
            elif term in column_lower:
                score += 3
                match_reasons.append(f"Column name contains term '{term}'")

        time_related_terms = ["time", "trend", "over time"]
        if any(term in query_lower for term in time_related_terms):
            if stats.type == "datetime":
                score += 4
                match_reasons.append("Datetime column matches time-based query")
            elif any(term in column_lower for term in ["date", "time", "year"]):
                score += 3
                match_reasons.append("Column name suggests time data")

        comparison_terms = ["compare", "between", "by"]
        if any(term in query_lower for term in comparison_terms):
            if stats.type == "categorical" and stats.unique_count < 15:
                score += 2
                match_reasons.append("Categorical column good for comparison")

        if stats.type == "numeric":
            score += 1
            if (
                stats.min is not None
                and stats.max is not None
                and stats.min != stats.max
            ):
                score += 1
                match_reasons.append("Numeric column with good distribution")

        if score > 0:
            logger.debug(
                f"Column '{column}' matched with score {score}: {match_reasons}"
            )
            matches[column] = ColumnMatch(
                score=score,
                type=stats.type,
                reasons=match_reasons,
                stats=stats,
            )

    logger.info(f"Found {len(matches)} matching columns")
    return matches


def _select_chart_type(x_type: str, y_type: str, query: str) -> str:
    """
    Select the appropriate chart type based on column types and query.

    Args:
        x_type: Type of the x-axis column
        y_type: Type of the y-axis column
        query: User query string

    Returns:
        Recommended chart type as a string
    """
    query_lower = query.lower()

    chart_types = {
        "line": "line",
        "bar": "bar",
        "scatter": "scatter",
        "box": "box",
        "heat": "heatmap",
    }

    for keyword, chart_type in chart_types.items():
        if keyword in query_lower:
            return chart_type

    if x_type == "datetime" and y_type == "numeric":
        return "line"
    elif x_type == "categorical" and y_type == "numeric":
        return "distribution" in query_lower and "box" or "bar"
    elif x_type == "numeric" and y_type == "numeric":
        return (
            any(term in query_lower for term in ["correlation", "relationship"])
            and "scatter"
            or "line"
        )
    elif x_type == "categorical" and y_type == "categorical":
        return "heatmap"

    return "line"


def _select_columns_for_chart(query: str, df: pd.DataFrame) -> ChartInfo:
    """
    Select the most appropriate columns for a chart based on the query.

    Args:
        query: User query string
        df: Input DataFrame

    Returns:
        ChartInfo object with selected x-axis, y-axis, and chart type

    Raises:
        ValueError: If no suitable columns could be found
    """
    logger.info(f"Selecting columns for chart based on query: '{query}'")

    # Direct column selection from query if possible
    direct_columns = _allow_direct_column_selection(df, query)
    if len(direct_columns) >= 2:
        logger.info(f"Using direct column selection: {direct_columns[:2]}")
        x_axis, y_axis = direct_columns[:2]
        chart_type = _select_chart_type(
            _get_column_type(df[x_axis]), _get_column_type(df[y_axis]), query
        )
        logger.info(f"Selected chart type: {chart_type}")
        return ChartInfo(x_axis=x_axis, y_axis=y_axis, chart_type=chart_type)

    # Otherwise use column matching approach
    column_matches = _match_columns_to_query(df, query)

    if not column_matches:
        logger.warning("No columns matched the query")
        raise ValueError("No columns matched your query. Please be more specific.")

    sorted_columns = sorted(
        column_matches.items(), key=lambda x: x[1].score, reverse=True
    )

    if len(sorted_columns) >= 2:
        if (
            len(sorted_columns) > 2
            and sorted_columns[0][1].score
            == sorted_columns[1][1].score
            == sorted_columns[2][1].score
        ):
            logger.info("Multiple columns with same score, using Groq LLM selection")
            return _select_columns_with_llm(query, df, sorted_columns)

        top_two_columns = [col for col, _ in sorted_columns[:2]]
        logger.info(f"Selected top two columns by score: {top_two_columns}")
        x_axis, y_axis = top_two_columns[0], top_two_columns[1]

        chart_type = _select_chart_type(
            _get_column_type(df[x_axis]), _get_column_type(df[y_axis]), query
        )
        logger.info(f"Selected chart type: {chart_type}")

        return ChartInfo(x_axis=x_axis, y_axis=y_axis, chart_type=chart_type)
    elif len(sorted_columns) == 1:
        logger.warning("Only one column matched the query")
        raise ValueError(
            "Only one column matched your query. Please specify two columns."
        )
    else:
        logger.warning("Could not determine suitable columns")
        raise ValueError("Could not determine suitable columns for visualization")


def _select_columns_with_llm(query: str, df: pd.DataFrame, sorted_columns) -> ChartInfo:
    """
    Use an LLM to select the most appropriate columns when automatic selection is ambiguous.

    Args:
        query: User query string
        df: Input DataFrame
        sorted_columns: List of (column_name, ColumnMatch) tuples sorted by score

    Returns:
        ChartInfo object with LLM-selected x-axis, y-axis, and chart type

    Raises:
        ValueError: If LLM selection fails
    """
    logger.info("Using Groq LLM to resolve column selection ambiguity")
    available_columns = ", ".join(df.columns)

    prompt = ChatPromptTemplate.from_template(
        """You need to choose the best x-axis and y-axis columns for a chart visualization.
        
        User Query: {query}
        
        Available columns (MUST only use these exact names): {available_columns}
        
        Available columns with their match scores:
        {column_details}
        
        Chart Type Guidelines:
        1. Line Charts (time series): datetime/continuous x-axis, numeric y-axis
        2. Scatter Plots (relationships): numeric x and y axes
        3. Bar Charts (comparisons): categorical x-axis, numeric y-axis
        4. Box Plots (distributions): categorical x-axis, numeric y-axis
        5. Heatmaps (2D relationships): categorical x and y axes
        
        IMPORTANT: You MUST select two columns with the exact same score from the available columns.
        
        Based on the column details and user query, determine the most appropriate column for x-axis, y-axis, and chart type.
        IMPORTANT: You MUST ONLY use column names from the available columns list. Do not invent new column names or use misspelled versions from the query.
        
        Respond EXACTLY in this format:
        x_axis: [column name]
        y_axis: [column name]
        chart_type: [line/scatter/bar/box/heatmap]"""
    )

    column_details = []
    for col, details in sorted_columns:
        col_info = [
            f"Column: {col}",
            f"Type: {details.type}",
            f"Match Score: {details.score}",
            f"Reasons: {'; '.join(details.reasons)}",
        ]

        stats = details.stats
        if (
            details.type == "numeric"
            and stats.min is not None
            and stats.mean is not None
        ):
            col_info.append(f"Range: {stats.min} to {stats.max}")
            col_info.append(f"Mean: {stats.mean:.2f}")
        elif (
            details.type == "categorical"
            and stats.unique_count < 10
            and stats.categories is not None
        ):
            categories = ", ".join(list(str(k) for k in stats.categories.keys())[:5])
            col_info.append(f"Categories: {categories}")

        column_details.append("\n".join(col_info))

    try:
        logger.debug("Invoking Groq LLM for column selection")
        model = get_groq_llm(DEFAULT_MODEL_NAME)
        response = (prompt | model).invoke(
            {
                "query": query,
                "available_columns": available_columns,
                "column_details": "\n\n".join(column_details),
            }
        )
        logger.debug(f"Groq LLM response: {response}")

        # Extract content from AIMessage if needed
        if hasattr(response, "content"):
            response_text = response.content
        else:
            response_text = str(response)

        parsed = dict(
            line.split(": ", 1)
            for line in response_text.strip().split("\n")
            if line.strip() and ": " in line
        )

        available_cols = set(df.columns)

        x_axis = parsed.get("x_axis")
        if x_axis not in available_cols:
            logger.error(f"Groq LLM suggested invalid column '{x_axis}'")
            raise ValueError(
                f"Groq LLM suggested invalid column '{x_axis}'. Please try a different query."
            )

        y_axis = parsed.get("y_axis")
        if y_axis not in available_cols:
            logger.error(f"Groq LLM suggested invalid column '{y_axis}'")
            raise ValueError(
                f"Groq LLM suggested invalid column '{y_axis}'. Please try a different query."
            )

        chart_type = parsed.get("chart_type", "line")
        if chart_type not in ["line", "bar", "scatter", "box", "heatmap"]:
            logger.warning(f"Invalid chart type '{chart_type}', defaulting to 'line'")
            chart_type = "line"

        logger.info(
            f"Groq LLM selected x_axis: {x_axis}, y_axis: {y_axis}, chart_type: {chart_type}"
        )
        return ChartInfo(x_axis=x_axis, y_axis=y_axis, chart_type=chart_type)
    except Exception as e:
        logger.error(f"Error in Groq LLM column selection: {str(e)}", exc_info=True)
        raise ValueError(f"Failed to select columns: {str(e)}")


def generate_chart_data(df: pd.DataFrame, query: str) -> str:
    """
    Generate chart data and configuration based on a user query and DataFrame.

    Args:
        df: Input DataFrame with the data to visualize
        query: User query string describing the desired visualization

    Returns:
        String URL of the generated chart image
    """
    logger.info(f"Generating chart data for query: '{query}'")
    chart_info = _select_columns_for_chart(query, df)

    try:
        # Create seaborn plot
        fig = _create_seaborn_plot(df, chart_info)

        # Save plot to MinIO and get URL
        image_url = _save_plot_to_minio(fig, chart_info.chart_type)
        plt.close(fig)

        logger.info(f"Generated chart visualization with URL: {image_url}")
        return image_url
    except Exception as e:
        logger.error(f"Failed to generate chart: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    # Set up console logging for script execution
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)

    # Simple test to demonstrate functionality

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
        chart_data = generate_chart_data(test_df, test_query)
        print("Generated chart visualization URL:")
        print(f"{chart_data}")
    except Exception as e:
        logger.error(f"Error in test: {str(e)}", exc_info=True)
