#!/usr/bin/env python
"""
Description Generator Module

This module provides functionality for generating natural language descriptions
of data based on user queries. It performs statistical analysis on DataFrame content
and uses LLMs to generate human-readable insights about the data.

Key components:
- Metadata extraction and statistical analysis of DataFrame columns
- LLM-based analysis type selection based on query intent
- Specialized analytical functions for different types of data insights
- Natural language description generation from analytical results
"""

import logging
from typing import Any, Dict, List, Literal, Optional, Union

import numpy as np
import pandas as pd
from langchain_core.prompts import ChatPromptTemplate
from mypackage.utils.llm_config import (
    DESCRIPTION_GENERATOR_MODEL,
    DESCRIPTION_GENERATOR_SELECTOR_MODEL,
    get_groq_llm,
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

logger.debug("description_generator module initialized")


class ColumnMetadata(BaseModel):
    """
    Pydantic model for storing detailed DataFrame column metadata.

    Attributes:
        name: Column name
        dtype: Data type (string representation of pandas dtype)
        unique_values: List of unique values (for low-cardinality columns)
        sample_values: Sample of values from the column
        stats: Dictionary of calculated statistics for the column
    """

    name: str
    dtype: str
    unique_values: Optional[List[str]] = None
    sample_values: List[Union[str, int, float]]
    stats: Dict[str, Any]


class AnalysisRequest(BaseModel):
    """
    Pydantic model representing a structured data analysis request.

    Attributes:
        selected_columns: List of column names to include in the analysis
        analysis_type: Type of analysis to perform (trend, distribution, etc.)
        parameters: Additional parameters for the analysis
    """

    selected_columns: List[str]
    analysis_type: Literal["trend", "distribution", "correlation", "outliers"]
    parameters: Dict[str, Union[str, float]]

    @field_validator("analysis_type")
    @classmethod
    def validate_analysis_type(cls, v):
        """
        Validate that analysis_type is one of the supported types.

        Args:
            v: The analysis type value to validate

        Returns:
            Lowercase version of the validated analysis type

        Raises:
            ValueError: If analysis type is not in the list of valid types
        """
        valid_types = {"trend", "distribution", "correlation", "outliers"}
        if v.lower() not in valid_types:
            raise ValueError(f"Analysis type must be one of: {', '.join(valid_types)}")
        return v.lower()


def _detect_outliers(series: pd.Series) -> Dict[str, Union[bool, int, float]]:
    """
    Detect outliers in a numeric series using the Interquartile Range (IQR) method.

    This function identifies values that fall outside 1.5 * IQR from
    the first and third quartiles.

    Args:
        series: Pandas Series containing numeric values

    Returns:
        Dictionary with outlier information (count, bounds, etc.)
    """
    logger.debug(f"Detecting outliers for series with {len(series)} entries")

    # Check if series is suitable for outlier detection
    if len(series) < 4 or not pd.api.types.is_numeric_dtype(series):
        logger.debug("Series too short or non-numeric, skipping outlier detection")
        return {
            "has_outliers": False,
            "outlier_count": 0,
            "lower_bound": 0.0,
            "upper_bound": 0.0,
        }

    # Calculate quartiles and IQR
    q1 = np.percentile(series, 25)
    q3 = np.percentile(series, 75)
    iqr = q3 - q1
    logger.debug(f"Q1={q1}, Q3={q3}, IQR={iqr}")

    # Define outlier bounds
    lower_bound = q1 - (1.5 * iqr)
    upper_bound = q3 + (1.5 * iqr)
    logger.debug(f"Outlier bounds: [{lower_bound}, {upper_bound}]")

    # Identify outliers
    outliers = series[(series < lower_bound) | (series > upper_bound)]
    logger.debug(f"Found {len(outliers)} outliers out of {len(series)} values")

    return {
        "has_outliers": len(outliers) > 0,
        "outlier_count": len(outliers),
        "lower_bound": float(lower_bound),
        "upper_bound": float(upper_bound),
    }


def extract_column_metadata(df: pd.DataFrame) -> List[ColumnMetadata]:
    """
    Extract detailed metadata and statistics from DataFrame columns.

    This function analyzes each column to extract its data type, sample values,
    unique values (for categorical data), and various statistical measures
    appropriate for the column's data type.

    Args:
        df: The pandas DataFrame to analyze

    Returns:
        List of ColumnMetadata objects containing detailed information about each column
    """
    logger.info(
        f"Extracting metadata for DataFrame with {len(df.columns)} columns and {len(df)} rows"
    )
    metadata = []

    for col in df.columns:
        logger.debug(f"Processing column: {col}")
        series = df[col].dropna()
        stats = {}

        # Extract sample values, handling datetime conversion
        sample_values = series.head(5)
        if pd.api.types.is_datetime64_any_dtype(series):
            logger.debug(f"Converting datetime samples to string for column: {col}")
            sample_values = sample_values.dt.strftime("%Y-%m-%d").tolist()
        else:
            sample_values = sample_values.tolist()
        logger.debug(f"Sample values for {col}: {sample_values}")

        # Calculate type-specific statistics
        if pd.api.types.is_numeric_dtype(series):
            logger.debug(f"Computing numeric statistics for column: {col}")
            stats.update(
                {
                    "min": float(series.min()),
                    "max": float(series.max()),
                    "mean": float(series.mean()),
                    "std": float(series.std()),
                    "outliers": _detect_outliers(series),
                }
            )
            logger.debug(
                f"Numeric stats for {col}: min={stats['min']}, max={stats['max']}, mean={stats['mean']}"
            )

        elif pd.api.types.is_datetime64_any_dtype(series):
            logger.debug(f"Computing datetime statistics for column: {col}")
            stats.update(
                {
                    "start": series.min().strftime("%Y-%m-%d"),
                    "end": series.max().strftime("%Y-%m-%d"),
                    "unique_days": series.nunique(),
                }
            )
            logger.debug(
                f"Datetime stats for {col}: range={stats['start']} to {stats['end']}, unique days={stats['unique_days']}"
            )

        elif pd.api.types.is_categorical_dtype(series) or series.nunique() < 20:
            logger.debug(f"Computing categorical statistics for column: {col}")
            value_counts = series.value_counts(normalize=True).head(3)
            stats.update(
                {
                    "top_values": value_counts.to_dict(),
                    "unique_count": series.nunique(),
                }
            )
            logger.debug(
                f"Categorical stats for {col}: {stats['unique_count']} unique values"
            )

        # Create metadata object for this column
        metadata.append(
            ColumnMetadata(
                name=col,
                dtype=str(series.dtype),
                unique_values=(
                    series.unique().tolist() if series.nunique() < 20 else None
                ),
                sample_values=sample_values,
                stats=stats,
            )
        )

    logger.info(f"Completed metadata extraction for {len(metadata)} columns")
    return metadata


def enhance_query_with_metadata(query: str, metadata: List[ColumnMetadata]) -> str:
    """
    Enhance the user query with statistical highlights from the data.

    This function adds context to the user's query by appending key
    statistical insights about the DataFrame columns, helping the LLM
    to better understand the data.

    Args:
        query: The original user query
        metadata: List of ColumnMetadata objects from the DataFrame

    Returns:
        Enhanced query with statistical highlights
    """
    logger.info("Enhancing query with metadata")
    logger.debug(f"Original query: {query}")

    # Extract statistical highlights for each column
    enhancements = []
    for col in metadata:
        if col.stats:
            highlights = []

            # Add range information for numeric columns
            if "min" in col.stats and "max" in col.stats:
                highlights.append(f"range {col.stats['min']}-{col.stats['max']}")
                logger.debug(f"Added range highlight for column {col.name}")

            # Add value distribution for categorical columns
            if "top_values" in col.stats:
                top_values_str = ", ".join(
                    f"{k} ({v:.1%})" for k, v in col.stats["top_values"].items()
                )
                highlights.append(f"common values: {top_values_str}")
                logger.debug(f"Added top values highlight for column {col.name}")

            # Add date range for datetime columns
            if "start" in col.stats and "end" in col.stats:
                highlights.append(f"period {col.stats['start']} to {col.stats['end']}")
                logger.debug(f"Added date range highlight for column {col.name}")

            # Compile highlights for this column if any exist
            if highlights:
                enhancements.append(f"{col.name}: {', '.join(highlights)}")

    # Create enhanced query with metadata appended
    enhanced_query = query
    if enhancements:
        enhanced_query = f"{query}\n\nData Features:\n- " + "\n- ".join(enhancements)
        logger.debug(f"Added {len(enhancements)} statistical highlights to query")

    logger.debug(f"Enhanced query: {enhanced_query}")
    return enhanced_query


def get_llm_analysis_plan(
    query: str, metadata: List[ColumnMetadata]
) -> AnalysisRequest:
    """
    Use an LLM to determine the most appropriate analysis approach for the query.

    This function sends the query and column metadata to an LLM, which
    then recommends the type of analysis to perform and which columns to use.

    Args:
        query: The user's query (possibly enhanced with metadata)
        metadata: List of ColumnMetadata objects from the DataFrame

    Returns:
        AnalysisRequest object containing the analysis plan

    Raises:
        ValueError: If the LLM response cannot be parsed into a valid analysis request
    """
    logger.info("Getting analysis plan from LLM")
    logger.debug(f"Input query: {query}")

    # Define prompt template for LLM
    prompt_template = ChatPromptTemplate.from_template(
        """Analyze this data request and select analysis parameters:

Query: {query}

Available Columns:
{columns}

Respond STRICTLY in this format:
selected_columns: [comma-separated column names]
analysis_type: [trend/distribution/correlation/outliers]
parameters: [key:value pairs separated by commas]

Examples:
selected_columns: sales, date
analysis_type: trend
parameters: time_column:date, measure:sales

selected_columns: price, category
analysis_type: distribution
parameters: group_by:category, metric:price"""
    )

    # Format column information for the prompt
    columns_str = "\n".join(
        [
            f"- {col.name} ({col.dtype}) "
            + " ".join(
                [
                    f"{k}={v}"
                    for k, v in col.stats.items()
                    if k in ["min", "max", "unique_count"]
                ]
            )
            for col in metadata
        ]
    )
    logger.debug(f"Formatted {len(metadata)} columns for LLM prompt")

    # Setup and execute LLM chain
    logger.debug(f"Using model: {DESCRIPTION_GENERATOR_SELECTOR_MODEL}")
    model = get_groq_llm(DESCRIPTION_GENERATOR_SELECTOR_MODEL)
    chain = prompt_template | model

    logger.debug("Sending request to Groq LLM")
    response = chain.invoke({"query": query, "columns": columns_str})
    logger.debug(f"Received response from Groq LLM: {response.content}")

    # Parse LLM response into structured format
    try:
        analysis_request = _parse_llm_response(response.content)
        logger.info(
            f"Generated analysis plan of type: {analysis_request.analysis_type}"
        )
        logger.debug(f"Selected columns: {analysis_request.selected_columns}")
        logger.debug(f"Analysis parameters: {analysis_request.parameters}")
        return analysis_request
    except Exception as e:
        logger.error(f"Failed to parse LLM response: {str(e)}", exc_info=True)
        raise ValueError(f"Invalid LLM response format: {str(e)}")


def _parse_llm_response(response: str) -> AnalysisRequest:
    """
    Parse LLM response text into a structured AnalysisRequest object.

    This function extracts the selected columns, analysis type, and parameters
    from the LLM's text response.

    Args:
        response: Text response from the LLM

    Returns:
        AnalysisRequest object containing the parsed information

    Raises:
        ValueError: If the response cannot be parsed into a valid request
    """
    logger.debug("Parsing LLM response")
    logger.debug(f"Raw response: {response}")

    # Initialize parsed data structure
    parsed = {"selected_columns": [], "analysis_type": "", "parameters": {}}

    # Process response line by line
    for line in response.strip().split("\n"):
        line = line.strip()

        # Extract selected columns
        if line.startswith("selected_columns:"):
            columns_part = line.split(":", 1)[1].strip()
            parsed["selected_columns"] = [
                col.strip() for col in columns_part.split(",")
            ]
            logger.debug(f"Parsed selected columns: {parsed['selected_columns']}")

        # Extract analysis type
        elif line.startswith("analysis_type:"):
            parsed["analysis_type"] = line.split(":", 1)[1].strip()
            logger.debug(f"Parsed analysis type: {parsed['analysis_type']}")

        # Extract parameters
        elif line.startswith("parameters:"):
            params_part = line.split(":", 1)[1].strip()
            # Split parameters by comma, then each key-value pair by colon
            param_pairs = [pair.strip() for pair in params_part.split(",")]
            for pair in param_pairs:
                if ":" in pair:
                    key, value = [item.strip() for item in pair.split(":", 1)]
                    parsed["parameters"][key] = value
            logger.debug(f"Parsed parameters: {parsed['parameters']}")

    # Create and return AnalysisRequest object
    try:
        logger.debug(f"Creating AnalysisRequest with parsed data: {parsed}")
        return AnalysisRequest(**parsed)
    except Exception as e:
        logger.error(f"Failed to create AnalysisRequest: {str(e)}", exc_info=True)
        raise ValueError(f"Invalid analysis request: {str(e)}")


def _calculate_insights(df: pd.DataFrame, request: AnalysisRequest) -> Dict:
    """
    Calculate data insights based on the specified analysis type.

    This function dispatches to specialized analysis functions based
    on the analysis type specified in the request.

    Args:
        df: The pandas DataFrame containing the data to analyze
        request: AnalysisRequest object specifying the analysis to perform

    Returns:
        Dictionary containing the calculated insights
    """
    logger.info(f"Calculating insights using analysis type: {request.analysis_type}")
    logger.debug(f"Selected columns: {request.selected_columns}")

    # Check if columns exist in DataFrame
    for col in request.selected_columns:
        if col not in df.columns:
            error_msg = f"Column '{col}' not found in DataFrame"
            logger.error(error_msg)
            return {"error": error_msg}

    # Filter DataFrame to selected columns
    selected_df = df[request.selected_columns].copy()
    logger.debug(f"Filtered DataFrame to {len(request.selected_columns)} columns")

    # Dispatch to appropriate analysis function based on type
    try:
        if request.analysis_type == "trend":
            logger.debug("Performing trend analysis")
            time_col = request.parameters.get(
                "time_column", request.selected_columns[0]
            )
            # Check if time column is actually a time/date column
            if time_col in df.columns and pd.api.types.is_datetime64_any_dtype(
                df[time_col]
            ):
                return _analyze_time_series(selected_df, time_col, request)
            else:
                # Fall back to treating as categorical if not a datetime
                logger.debug(
                    f"Column '{time_col}' is not datetime, treating as categorical"
                )
                return _calculate_trend(selected_df[request.selected_columns[0]])

        elif request.analysis_type == "distribution":
            logger.debug("Performing distribution analysis")
            group_by = request.parameters.get("group_by")
            if group_by and group_by in selected_df.columns:
                logger.debug(f"Calculating distribution grouped by '{group_by}'")
                return _calculate_crosstabs(selected_df, request.selected_columns)
            else:
                logger.debug("Calculating single column distribution")
                return _calculate_trend(selected_df[request.selected_columns[0]])

        elif request.analysis_type == "correlation":
            logger.debug("Performing correlation analysis")
            return _calculate_correlation(selected_df, request.selected_columns)

        elif request.analysis_type == "outliers":
            logger.debug("Performing outlier analysis")
            results = {}
            for col in request.selected_columns:
                if pd.api.types.is_numeric_dtype(selected_df[col]):
                    results[col] = _detect_outliers(selected_df[col])
            return {"outlier_analysis": results}

        else:
            error_msg = f"Unsupported analysis type: {request.analysis_type}"
            logger.error(error_msg)
            return {"error": error_msg}

    except Exception as e:
        error_msg = f"Error calculating insights: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"error": error_msg}


def _calculate_trend(series: pd.Series) -> Dict:
    """
    Calculate trend statistics for a single series.

    Args:
        series: The pandas Series to analyze

    Returns:
        Dictionary containing trend statistics
    """
    logger.debug(f"Calculating trend statistics for series: {series.name}")

    results = {
        "column": series.name,
        "data_type": str(series.dtype),
    }

    try:
        # For numeric data, calculate statistical measures
        if pd.api.types.is_numeric_dtype(series):
            logger.debug("Calculating numeric trend statistics")
            results.update(
                {
                    "min": float(series.min()),
                    "max": float(series.max()),
                    "mean": float(series.mean()),
                    "median": float(series.median()),
                    "std": float(series.std()),
                    "trend_direction": (
                        "up"
                        if series.corr(pd.Series(range(len(series)))) > 0.5
                        else (
                            "down"
                            if series.corr(pd.Series(range(len(series)))) < -0.5
                            else "stable"
                        )
                    ),
                }
            )

        # For categorical data, calculate value frequencies
        else:
            logger.debug("Calculating categorical trend statistics")
            value_counts = series.value_counts().head(5)
            results.update(
                {
                    "unique_count": series.nunique(),
                    "most_common": (
                        value_counts.index[0] if not value_counts.empty else None
                    ),
                    "most_common_count": (
                        int(value_counts.iloc[0]) if not value_counts.empty else 0
                    ),
                    "value_distribution": {
                        str(k): int(v) for k, v in value_counts.items()
                    },
                }
            )

    except Exception as e:
        logger.error(f"Error calculating trend: {str(e)}", exc_info=True)
        results["error"] = str(e)

    logger.debug(f"Trend calculation complete: {list(results.keys())}")
    return results


def _calculate_correlation(df: pd.DataFrame, columns: List[str]) -> Dict:
    """
    Calculate correlation statistics between numeric columns.

    Args:
        df: The pandas DataFrame containing the data
        columns: List of column names to analyze

    Returns:
        Dictionary containing correlation statistics
    """
    logger.debug(f"Calculating correlations for {len(columns)} columns")

    results = {"correlations": {}}

    try:
        # Filter to numeric columns
        numeric_df = df[columns].select_dtypes(include=["number"])
        numeric_columns = numeric_df.columns.tolist()
        logger.debug(f"Found {len(numeric_columns)} numeric columns for correlation")

        if len(numeric_columns) >= 2:
            # Calculate correlation matrix
            corr_matrix = numeric_df.corr()

            # Extract top correlations
            for i, col1 in enumerate(numeric_columns):
                for col2 in numeric_columns[i + 1 :]:
                    corr_value = corr_matrix.loc[col1, col2]
                    if abs(corr_value) > 0.3:  # Only include meaningful correlations
                        pair_key = f"{col1}_{col2}"
                        results["correlations"][pair_key] = {
                            "column1": col1,
                            "column2": col2,
                            "correlation": round(float(corr_value), 3),
                            "strength": (
                                "strong"
                                if abs(corr_value) > 0.7
                                else "moderate"
                                if abs(corr_value) > 0.5
                                else "weak"
                            ),
                            "direction": "positive" if corr_value > 0 else "negative",
                        }
                        logger.debug(
                            f"Correlation between {col1} and {col2}: {corr_value}"
                        )

    except Exception as e:
        logger.error(f"Error calculating correlations: {str(e)}", exc_info=True)
        results["error"] = str(e)

    logger.debug(f"Found {len(results['correlations'])} meaningful correlations")
    return results


def _calculate_crosstabs(df: pd.DataFrame, columns: List[str]) -> Dict:
    """
    Calculate cross-tabulation statistics for categorical columns.

    Args:
        df: The pandas DataFrame containing the data
        columns: List of column names to analyze

    Returns:
        Dictionary containing cross-tabulation statistics
    """
    logger.debug(f"Calculating crosstabs for columns: {columns}")

    if len(columns) < 2:
        logger.warning(
            "Need at least 2 columns for crosstabs, falling back to trend analysis"
        )
        return _calculate_trend(df[columns[0]])

    # Take first two columns for crosstab
    col1, col2 = columns[:2]
    logger.debug(f"Creating crosstab between {col1} and {col2}")

    try:
        # Calculate crosstab
        crosstab = pd.crosstab(df[col1], df[col2], normalize=True)

        # Format results
        results = {
            "crosstab": {
                "column1": col1,
                "column2": col2,
                "data": crosstab.to_dict(),
                "insights": {
                    "total_combinations": crosstab.size,
                    "most_common_pair": f"{crosstab.values.argmax() // crosstab.shape[1]}, {crosstab.values.argmax() % crosstab.shape[1]}",
                },
            }
        }

        logger.debug(f"Crosstab calculation complete: {crosstab.shape} table")
        return results

    except Exception as e:
        logger.error(f"Error calculating crosstab: {str(e)}", exc_info=True)
        return {"error": str(e)}


def _analyze_time_series(
    df: pd.DataFrame, time_col: str, request: AnalysisRequest
) -> Dict:
    """
    Analyze time series data to identify patterns over time.

    Args:
        df: The pandas DataFrame containing the data
        time_col: Name of the datetime column
        request: AnalysisRequest object with analysis parameters

    Returns:
        Dictionary containing time series analysis results
    """
    logger.info(f"Analyzing time series with time column: {time_col}")

    try:
        # Ensure time column is properly formatted
        if pd.api.types.is_datetime64_any_dtype(df[time_col]):
            time_df = df.set_index(time_col)
            logger.debug(
                f"Time series spans from {time_df.index.min()} to {time_df.index.max()}"
            )

            # Calculate time-based statistics for each other column
            results = {"time_series": {}}

            for col in [c for c in df.columns if c != time_col]:
                if pd.api.types.is_numeric_dtype(df[col]):
                    # Resample if we have enough data points
                    if len(time_df) > 20:
                        try:
                            # Try to determine appropriate resampling frequency
                            date_range = (
                                time_df.index.max() - time_df.index.min()
                            ).days
                            resample_rule = (
                                "M"
                                if date_range > 60
                                else "W"
                                if date_range > 14
                                else "D"
                            )
                            resampled = time_df[col].resample(resample_rule).mean()

                            # Calculate trends
                            logger.debug(
                                f"Resampled time series to {resample_rule} frequency with {len(resampled)} points"
                            )

                            # Simple trend calculation
                            first_half_mean = resampled[: len(resampled) // 2].mean()
                            second_half_mean = resampled[len(resampled) // 2 :].mean()
                            trend = (
                                "increasing"
                                if second_half_mean > first_half_mean
                                else (
                                    "decreasing"
                                    if second_half_mean < first_half_mean
                                    else "stable"
                                )
                            )

                            results["time_series"][col] = {
                                "start_value": (
                                    float(resampled.iloc[0])
                                    if not resampled.empty
                                    else None
                                ),
                                "end_value": (
                                    float(resampled.iloc[-1])
                                    if not resampled.empty
                                    else None
                                ),
                                "min": float(resampled.min()),
                                "max": float(resampled.max()),
                                "trend": trend,
                                "change_pct": (
                                    ((resampled.iloc[-1] / resampled.iloc[0]) - 1) * 100
                                    if not resampled.empty and resampled.iloc[0] != 0
                                    else 0
                                ),
                            }
                            logger.debug(
                                f"Time series analysis for {col}: trend={trend}"
                            )
                        except Exception as e:
                            logger.warning(f"Error in resampling {col}: {str(e)}")
                            # Fall back to basic stats if resampling fails
                            results["time_series"][col] = _calculate_trend(df[col])
                    else:
                        logger.debug(f"Too few data points for resampling {col}")
                        results["time_series"][col] = _calculate_trend(df[col])

            return results
        else:
            logger.warning(f"Column {time_col} is not a datetime column")
            return _calculate_trend(df[df.columns[0]])

    except Exception as e:
        logger.error(f"Error in time series analysis: {str(e)}", exc_info=True)
        return {"error": f"Time series analysis failed: {str(e)}"}


def generate_description(df: pd.DataFrame, query: str) -> str:
    """
    Main function to generate a natural language description based on a user query.

    This function:
    1. Extracts metadata from the DataFrame
    2. Enhances the query with metadata context
    3. Determines the appropriate analysis approach using an LLM
    4. Performs the selected analysis
    5. Generates a natural language description using an LLM

    Args:
        df: The pandas DataFrame containing the data to analyze
        query: The user's query requesting a description

    Returns:
        Natural language description of the data insights

    Raises:
        ValueError: If description generation fails at any step
    """
    logger.info(f"Generating description for query: {query}")

    try:
        # Step 1: Extract DataFrame metadata
        logger.debug("Extracting column metadata")
        metadata = extract_column_metadata(df)

        # Step 2: Enhance query with statistical context
        logger.debug("Enhancing query with metadata")
        enhanced_query = enhance_query_with_metadata(query, metadata)

        # Step 3: Get analysis plan from LLM
        logger.debug("Getting analysis plan from LLM")
        analysis_request = get_llm_analysis_plan(enhanced_query, metadata)

        # Step 4: Calculate insights based on analysis plan
        logger.debug(
            f"Calculating insights using analysis type: {analysis_request.analysis_type}"
        )
        insights = _calculate_insights(df, analysis_request)

        if "error" in insights:
            logger.error(f"Error during insight calculation: {insights['error']}")
            return f"Error analyzing data: {insights['error']}"

        # Step 5: Generate natural language description
        logger.debug("Generating natural language description using LLM")
        description = _get_description_from_llm(query, insights, analysis_request)

        # Remove <think> sections using regex
        import re

        description = re.sub(
            r"`?\s*<think>.*?</think>\s*`?",
            "",
            description,
            flags=re.IGNORECASE | re.DOTALL,
        )

        logger.info("Description generation complete")
        return description

    except Exception as e:
        logger.error(f"Description generation failed: {str(e)}", exc_info=True)
        return f"Error generating description: {str(e)}"


def _get_description_from_llm(
    query: str, insights: Dict, analysis_request: AnalysisRequest
) -> str:
    """
    Generate a natural language description of the insights using an LLM.

    Args:
        query: The original user query
        insights: Dictionary containing calculated insights
        analysis_request: The AnalysisRequest used to generate the insights

    Returns:
        Natural language description
    """
    logger.info("Generating natural language description from insights")

    # Create prompt template
    prompt_template = ChatPromptTemplate.from_template(
        """Generate a clear, concise description based on the data analysis below.

User Query: {query}

Analysis Type: {analysis_type}

Insights: {insights}

Your description should:
1. Start by directly answering the user's query
2. Highlight 2-3 key insights from the data
3. Use simple, non-technical language
4. Be concise (150 words maximum)
5. Only mention what's supported by the data
6. Be direct and avoid phrases like "the data shows" or "based on the analysis"

Description:"""
    )

    # Format insights for the prompt
    insights_str = str(insights)
    if len(insights_str) > 10000:
        logger.warning("Insights too large, truncating")
        insights_str = insights_str[:10000] + "..."

    logger.debug(f"Using model: {DESCRIPTION_GENERATOR_MODEL}")
    model = get_groq_llm(DESCRIPTION_GENERATOR_MODEL)

    # Generate description
    try:
        logger.debug("Sending prompt to Groq LLM")
        response = model.invoke(
            prompt_template.format(
                query=query,
                analysis_type=analysis_request.analysis_type,
                insights=insights_str,
            )
        )

        # Extract text response
        description = response.content.strip()
        logger.debug(f"Generated description ({len(description)} chars)")

        return description
    except Exception as e:
        logger.error(f"Error generating description with LLM: {str(e)}", exc_info=True)
        return f"Error generating description: {str(e)}"


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
    logger.info("Testing description generator with sample data")

    # Create sample DataFrame
    df = pd.DataFrame(
        {
            "date": pd.date_range(start="2023-01-01", periods=100),
            "sales": np.random.normal(1000, 200, 100),
            "category": np.random.choice(["Electronics", "Clothing", "Home"], 100),
            "region": np.random.choice(["North", "South", "East", "West"], 100),
        }
    )

    # Test query
    test_query = "How have sales changed over time by category?"

    try:
        description = generate_description(df, test_query)
        logger.info(f"Description generated successfully: {description}")
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
