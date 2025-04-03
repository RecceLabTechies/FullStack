#!/usr/bin/env python
import logging
from typing import Any, Dict, List, cast

import pandas as pd
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field, field_validator

from mypackage.utils.llm_config import get_groq_llm, DESCRIPTION_GENERATOR_MODEL

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

# Global variable for LLM model name
DEFAULT_MODEL_NAME = DESCRIPTION_GENERATOR_MODEL


def _extract_key_terms(query: str) -> List[str]:
    """
    Extract key terms from a query by removing stop words and short words.

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
        "describe",
        "explain",
        "tell",
        "me",
        "about",
        "summary",
        "summarize",
        "details",
        "detail",
        "information",
    }
    return [word for word in words if word not in stop_words and len(word) > 2]


def _analyze_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze a DataFrame to extract key statistics and information.

    Args:
        df: Input DataFrame to analyze

    Returns:
        Dictionary containing analysis results including row/column counts and data types
    """
    logger.info(
        f"Analyzing DataFrame with {len(df)} rows and {len(df.columns)} columns"
    )
    result = {
        "row_count": len(df),
        "column_count": len(df.columns),
        "column_names": list(df.columns),
        "column_types": {},
        "missing_values": {},
        "numeric_columns": [],
        "categorical_columns": [],
        "datetime_columns": [],
    }

    for column in df.columns:
        dtype = str(df[column].dtype)
        result["column_types"][column] = dtype
        missing = df[column].isna().sum()
        result["missing_values"][column] = missing

        if pd.api.types.is_numeric_dtype(df[column]):
            result["numeric_columns"].append(column)
        elif pd.api.types.is_datetime64_any_dtype(df[column]):
            result["datetime_columns"].append(column)
        else:
            unique_count = df[column].nunique()
            if unique_count < len(df) * 0.5:
                result["categorical_columns"].append(column)

    logger.debug(
        f"Found {len(result['numeric_columns'])} numeric, {len(result['categorical_columns'])} categorical, and {len(result['datetime_columns'])} datetime columns"
    )
    return result


def _get_column_stats(df: pd.DataFrame, column: str) -> Dict[str, Any]:
    """
    Calculate detailed statistics for a specific DataFrame column.

    Args:
        df: Input DataFrame
        column: Name of the column to analyze

    Returns:
        Dictionary containing column statistics appropriate for the column's data type
    """
    logger.debug(f"Calculating statistics for column: '{column}'")
    # Using Dict[str, Any] to allow different value types
    stats: Dict[str, Any] = {"name": column, "dtype": str(df[column].dtype)}

    if pd.api.types.is_numeric_dtype(df[column]):
        stats["type"] = "numeric"
        stats["min"] = float(df[column].min())
        stats["max"] = float(df[column].max())
        stats["mean"] = float(df[column].mean())
        stats["median"] = float(df[column].median())
        stats["std"] = float(df[column].std())
        stats["unique_count"] = int(df[column].nunique())
        stats["missing_count"] = int(df[column].isna().sum())

        # Check for skewness - cast to float to ensure type compatibility
        stats["skewness"] = float(cast(float, df[column].skew()))

        # Detect potential outliers using IQR
        q1 = float(df[column].quantile(0.25))
        q3 = float(df[column].quantile(0.75))
        iqr = q3 - q1
        outlier_low = q1 - 1.5 * iqr
        outlier_high = q3 + 1.5 * iqr
        potential_outliers = df[
            (df[column] < outlier_low) | (df[column] > outlier_high)
        ][column]
        stats["has_outliers"] = len(potential_outliers) > 0
        stats["outlier_count"] = len(potential_outliers)
        logger.debug(
            f"Numeric column '{column}' has {stats['outlier_count']} potential outliers"
        )

    elif pd.api.types.is_datetime64_any_dtype(df[column]):
        stats["type"] = "datetime"
        stats["min"] = df[column].min().strftime("%Y-%m-%d %H:%M:%S")
        stats["max"] = df[column].max().strftime("%Y-%m-%d %H:%M:%S")
        stats["unique_count"] = int(df[column].nunique())
        stats["missing_count"] = int(df[column].isna().sum())
        logger.debug(
            f"Datetime column '{column}' range: {stats['min']} to {stats['max']}"
        )

    else:
        unique_values = df[column].nunique()
        stats["unique_count"] = int(unique_values)
        stats["missing_count"] = int(df[column].isna().sum())

        if unique_values < 20:
            # For categorical with few unique values
            stats["type"] = "categorical"
            value_counts = df[column].value_counts(normalize=True)
            stats["categories"] = {
                str(k): {"count": int(v * len(df)), "percentage": float(v)}
                for k, v in value_counts.items()
                if k is not None
            }
            logger.debug(
                f"Categorical column '{column}' has {unique_values} unique values"
            )
        else:
            # For text or high-cardinality categorical
            stats["type"] = "text"
            stats["avg_length"] = float(df[column].astype(str).str.len().mean())
            logger.debug(f"Text column '{column}' has {unique_values} unique values")

    return stats


def _match_columns_to_query(df: pd.DataFrame, query: str) -> Dict[str, Dict[str, Any]]:
    """
    Match DataFrame columns to a query based on keyword matching.

    Args:
        df: Input DataFrame
        query: User query string

    Returns:
        Dictionary mapping column names to match information including score and reasons
    """
    logger.info(f"Matching columns to query: '{query}'")
    query_terms = _extract_key_terms(query)
    matches = {}

    for column in df.columns:
        column_lower = column.lower()
        match_score = 0
        match_terms = []

        # Check for direct column name matches
        for term in query_terms:
            if term == column_lower:
                match_score += 3
                match_terms.append(term)
            elif term in column_lower or column_lower in term:
                match_score += 2
                match_terms.append(term)

        # Add columns that might be relevant even without direct match
        if pd.api.types.is_numeric_dtype(df[column]) and any(
            term in query
            for term in ["statistic", "number", "amount", "count", "total"]
        ):
            match_score += 1
            match_terms.append("numeric relevance")

        if match_score > 0:
            logger.debug(
                f"Column '{column}' matched with score {match_score}: {match_terms}"
            )
            matches[column] = {
                "score": match_score,
                "matching_terms": match_terms,
                "stats": _get_column_stats(df, column),
            }

    logger.info(f"Found {len(matches)} matching columns")
    return matches


def _allow_direct_column_selection(df: pd.DataFrame, query: str) -> List[str]:
    """
    Attempt to directly extract column names mentioned in the query.

    Args:
        df: Input DataFrame
        query: User query string

    Returns:
        List of column names found in the query
    """
    query_lower = query.lower()
    columns_found = []

    # Check for exact matches first
    for column in df.columns:
        if column.lower() in query_lower:
            columns_found.append(column)

    # Check for partial matches if no exact matches found
    if not columns_found:
        for column in df.columns:
            column_words = column.lower().split()
            for word in column_words:
                if len(word) > 3 and word in query_lower:
                    columns_found.append(column)
                    break

    return columns_found


def _select_columns_for_analysis(query: str, df: pd.DataFrame) -> List[str]:
    """
    Select the most relevant columns for analysis based on the query.

    Args:
        query: User query string
        df: Input DataFrame

    Returns:
        List of column names selected for analysis
    """
    logger.info(f"Selecting columns for analysis based on query: '{query}'")
    # Try direct column selection first
    direct_columns = _allow_direct_column_selection(df, query)
    if direct_columns:
        logger.info(f"Using direct column selection: {direct_columns}")
        return direct_columns

    # If direct selection fails, use matching algorithm
    column_matches = _match_columns_to_query(df, query)
    if not column_matches:
        logger.warning("No specific columns matched the query, using default selection")
        df_analysis = _analyze_dataframe(df)

        # If no specific columns match, return a sensible default selection
        if df_analysis["numeric_columns"]:
            selected = df_analysis["numeric_columns"][
                :5
            ]  # Return top 5 numeric columns
            logger.info(f"Selected default numeric columns: {selected}")
            return selected
        else:
            selected = list(df.columns[:5])  # Return first 5 columns as fallback
            logger.info(f"Selected first 5 columns as fallback: {selected}")
            return selected

    # Sort columns by match score
    sorted_matches = sorted(
        column_matches.items(), key=lambda x: x[1]["score"], reverse=True
    )

    # Take top 5 matching columns or all if less than 5
    selected_columns = [col for col, _ in sorted_matches[:5]]
    logger.info(f"Selected top matching columns: {selected_columns}")
    return selected_columns


class ColumnSelection(BaseModel):
    columns: List[str] = Field(
        ..., description="List of column names to include in the analysis"
    )

    @field_validator("columns")
    @classmethod
    def validate_columns(cls, columns):
        """
        Validate that the column list is not empty and contains valid strings.

        Args:
            columns: List of column names to validate

        Returns:
            Validated list of column names

        Raises:
            ValueError: If validation fails
        """
        if not columns:
            raise ValueError("Must include at least one column")
        if not all(isinstance(col, str) for col in columns):
            raise ValueError("All column names must be strings")
        return columns


def _select_columns_with_llm(query: str, df: pd.DataFrame, sorted_columns) -> List[str]:
    """
    Use an LLM to select the most appropriate columns for analysis in ambiguous cases.

    Args:
        query: User query string
        df: Input DataFrame
        sorted_columns: Columns sorted by match score

    Returns:
        List of column names selected by the LLM
    """
    logger.info("Using Groq LLM to resolve column selection ambiguity")
    prompt = ChatPromptTemplate.from_template(
        """I need to select the most relevant columns from a DataFrame to answer a user's query.

User Query: {query}

Available columns in the DataFrame:
{available_columns}

My goal is to select columns that are most relevant to the query. The columns should help address the specific aspects the user is asking about.

Based on the user query, select between 1 and 5 columns that would be most helpful for generating a description or analysis that answers the query.

Respond with ONLY a comma-separated list of column names, exactly as they appear in the available columns list."""
    )

    model = get_groq_llm(DEFAULT_MODEL_NAME)

    column_dict = {col: df[col].dtype for col in df.columns}
    formatted_columns = "\n".join(
        [f"- {col} ({dtype})" for col, dtype in column_dict.items()]
    )

    try:
        logger.debug("Invoking Groq LLM for column selection")
        response = model.invoke(
            prompt.format(
                query=query,
                available_columns=formatted_columns,
            )
        )
        logger.debug(f"Groq LLM response: {response}")

        # Extract content from AIMessage if needed
        if hasattr(response, "content"):
            response_text = response.content
        else:
            response_text = str(response)

        # Parse response
        selected_columns = [col.strip() for col in response_text.split(",")]

        # Validate columns exist in DataFrame
        valid_columns = [col for col in selected_columns if col in df.columns]

        if not valid_columns:
            logger.warning(
                "Groq LLM returned no valid columns, using fallback selection"
            )
            # If no valid columns selected, use top matched columns
            valid_columns = [col for col, _ in sorted_columns[:5]]

        logger.info(f"Groq LLM selected columns: {valid_columns}")
        return valid_columns

    except Exception as e:
        logger.error(f"Error in Groq LLM column selection: {str(e)}", exc_info=True)
        # Fallback to sorted columns from matching algorithm
        fallback_columns = [col for col, _ in sorted_columns[:5]]
        logger.info(f"Using fallback columns after Groq LLM error: {fallback_columns}")
        return fallback_columns


def _interpret_correlation(value: float) -> str:
    """
    Interpret a correlation coefficient with a descriptive label.

    Args:
        value: Correlation coefficient value (-1 to 1)

    Returns:
        String describing the correlation strength and direction
    """
    abs_value = abs(value)
    direction = "positive" if value > 0 else "negative"

    if abs_value < 0.1:
        strength = "negligible"
    elif abs_value < 0.3:
        strength = "weak"
    elif abs_value < 0.5:
        strength = "moderate"
    elif abs_value < 0.7:
        strength = "strong"
    else:
        strength = "very strong"

    return f"{strength} {direction}"


def generate_description(df: pd.DataFrame, query: str) -> str:
    """
    Generate a descriptive analysis of a DataFrame based on a user query.

    Args:
        df: Input DataFrame to analyze
        query: User query string describing the analysis needed

    Returns:
        String containing the descriptive analysis
    """
    logger.info(f"Generating description for query: '{query}'")
    # Overall DataFrame analysis
    df_analysis = _analyze_dataframe(df)

    # Select relevant columns
    try:
        # Match columns with highest scores to the query
        column_matches = _match_columns_to_query(df, query)
        sorted_matches = sorted(
            column_matches.items(), key=lambda x: x[1]["score"], reverse=True
        )

        if (
            len(sorted_matches) >= 2
            and sorted_matches[0][1]["score"] == sorted_matches[1][1]["score"]
        ):
            logger.info("Multiple columns with same score, using Groq LLM selection")
            selected_columns = _select_columns_with_llm(query, df, sorted_matches)
        else:
            selected_columns = _select_columns_for_analysis(query, df)

        if not selected_columns:
            logger.warning("No columns selected, using default selection")
            # If no columns selected, use a sensible default
            if df_analysis["numeric_columns"]:
                selected_columns = df_analysis["numeric_columns"][:3]
            else:
                selected_columns = list(df.columns[:3])

    except Exception as e:
        logger.error(f"Error selecting columns: {str(e)}", exc_info=True)
        # Fallback to basic column selection
        if df_analysis["numeric_columns"]:
            selected_columns = df_analysis["numeric_columns"][:3]
        else:
            selected_columns = list(df.columns[:3])
        logger.info(f"Using fallback column selection: {selected_columns}")

    # Calculate detailed stats for selected columns
    logger.info(f"Analyzing selected columns: {selected_columns}")
    column_stats = {}
    for column in selected_columns:
        column_stats[column] = _get_column_stats(df, column)

    # Calculate correlations between numeric columns
    correlations = {}
    numeric_cols = [
        col for col in selected_columns if col in df_analysis["numeric_columns"]
    ]

    if len(numeric_cols) > 1:
        logger.info(
            f"Calculating correlations between {len(numeric_cols)} numeric columns"
        )
        corr_matrix = df[numeric_cols].corr()
        for i, col1 in enumerate(numeric_cols):
            for j, col2 in enumerate(numeric_cols):
                if i < j:  # Only include each pair once
                    corr_value = corr_matrix.loc[col1, col2]
                    if not pd.isna(corr_value):
                        # Cast correlation value to float for type safety
                        float_corr_value = float(cast(float, corr_value))
                        correlations[f"{col1} vs {col2}"] = {
                            "value": float_corr_value,
                            "interpretation": _interpret_correlation(float_corr_value),
                        }
        logger.debug(f"Found {len(correlations)} valid correlations")

    # Format the query context
    query_context = {
        "query": query,
        "selected_columns": selected_columns,
        "dataframe_info": {
            "rows": df_analysis["row_count"],
            "columns": df_analysis["column_count"],
            "column_types": df_analysis["column_types"],
        },
        "column_statistics": column_stats,
        "correlations": correlations,
    }

    # Generate description with LLM
    prompt = ChatPromptTemplate.from_template(
        """
        I'm analyzing a DataFrame based on this query: "{query}"
        
        DataFrame Information:
        - Total rows: {rows}
        - Total columns: {columns}
        
        Selected columns for this analysis:
        {column_details}
        
        Correlation Information:
        {correlation_info}
        
        Based on the above information, provide a concise, factual description that directly answers the query.
        Focus on quantitative insights, notable patterns, and key statistics that address what the user is asking about.
        Use simple language and avoid unnecessary technical jargon.
        
        Include relevant statistics like means, ranges, correlations, distributions, or trends when they help answer the query.
        Do not include meta-commentary about the analysis process itself.
        """
    )

    # Format column details
    column_details = []
    for col, stats in column_stats.items():
        if stats["type"] == "numeric":
            column_details.append(
                f"- {col}: numeric column with range {stats['min']} to {stats['max']}, "
                f"mean: {stats['mean']:.2f}, median: {stats['median']:.2f}"
            )
            if stats.get("has_outliers"):
                column_details.append(
                    f"  Contains {stats['outlier_count']} potential outliers"
                )

        elif stats["type"] == "categorical" and "categories" in stats:
            top_cats = sorted(
                stats["categories"].items(), key=lambda x: x[1]["count"], reverse=True
            )[:3]
            cats_text = ", ".join(
                f"{cat} ({info['percentage']:.1%})" for cat, info in top_cats
            )
            column_details.append(
                f"- {col}: categorical column with {stats['unique_count']} unique values. "
                f"Top categories: {cats_text}"
            )

        elif stats["type"] == "datetime":
            column_details.append(
                f"- {col}: datetime column ranging from {stats['min']} to {stats['max']}"
            )

        else:
            column_details.append(
                f"- {col}: text column with {stats['unique_count']} unique values"
            )

    # Format correlation information
    correlation_info = []
    for pair, corr in correlations.items():
        correlation_info.append(
            f"- {pair}: {corr['interpretation']} correlation ({corr['value']:.2f})"
        )

    if not correlation_info:
        correlation_info = ["No relevant correlations to report"]

    model = get_groq_llm(DEFAULT_MODEL_NAME)

    try:
        logger.info("Invoking Groq LLM to generate description")
        description = model.invoke(
            prompt.format(
                query=query,
                rows=query_context["dataframe_info"]["rows"],
                columns=query_context["dataframe_info"]["columns"],
                column_details="\n".join(column_details),
                correlation_info="\n".join(correlation_info),
            )
        )

        # Extract content from AIMessage if needed
        if hasattr(description, "content"):
            description_text = description.content
        else:
            description_text = str(description)

        logger.info(f"Generated description of {len(description_text)} characters")
        return description_text.strip()
    except Exception as e:
        error_msg = f"Error generating description: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg


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
    import numpy as np

    test_data = {
        "date": pd.date_range(start="2023-01-01", periods=100),
        "sales": np.random.normal(1000, 200, 100),
        "customers": np.random.randint(50, 200, 100),
        "category": np.random.choice(["A", "B", "C"], 100),
    }
    test_df = pd.DataFrame(test_data)
    test_query = "Describe the sales trends over time"

    logger.info(f"Testing with query: '{test_query}'")
    try:
        description = generate_description(test_df, test_query)
        print(f"Generated description:\n{description}")
    except Exception as e:
        logger.error(f"Error in test: {str(e)}", exc_info=True)
