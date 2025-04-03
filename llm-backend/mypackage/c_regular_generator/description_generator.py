#!/usr/bin/env python
import logging
import re
from typing import Any, Dict, List, Literal, Optional, Union

import numpy as np
import pandas as pd
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, field_validator

from mypackage.utils.llm_config import (
    DESCRIPTION_GENERATOR_MODEL,
    DESCRIPTION_GENERATOR_SELECTOR_MODEL,
    get_groq_llm,
)

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


class ColumnMetadata(BaseModel):
    name: str
    dtype: str
    unique_values: Optional[List[str]] = None
    sample_values: List[Union[str, int, float]]
    stats: Dict[str, Any]


class AnalysisRequest(BaseModel):
    selected_columns: List[str]
    analysis_type: Literal["trend", "distribution", "correlation", "outliers"]
    parameters: Dict[str, Union[str, float]]

    @field_validator("analysis_type")
    @classmethod
    def validate_analysis_type(cls, v):
        valid_types = {"trend", "distribution", "correlation", "outliers"}
        if v.lower() not in valid_types:
            raise ValueError(f"Analysis type must be one of: {', '.join(valid_types)}")
        return v.lower()


def _detect_outliers(series: pd.Series) -> Dict[str, Union[bool, int, float]]:
    """Detect outliers using IQR method with pandas/numpy"""
    logger.debug(f"Detecting outliers for series with {len(series)} entries")

    if len(series) < 4 or not pd.api.types.is_numeric_dtype(series):
        logger.debug("Series too short or non-numeric, skipping outlier detection")
        return {
            "has_outliers": False,
            "outlier_count": 0,
            "lower_bound": 0.0,
            "upper_bound": 0.0,
        }

    q1 = np.percentile(series, 25)
    q3 = np.percentile(series, 75)
    iqr = q3 - q1

    lower_bound = q1 - (1.5 * iqr)
    upper_bound = q3 + (1.5 * iqr)

    outliers = series[(series < lower_bound) | (series > upper_bound)]
    logger.debug(f"Found {len(outliers)} outliers")
    return {
        "has_outliers": len(outliers) > 0,
        "outlier_count": len(outliers),
        "lower_bound": float(lower_bound),
        "upper_bound": float(upper_bound),
    }


def extract_column_metadata(df: pd.DataFrame) -> List[ColumnMetadata]:
    """Enhanced metadata extraction with statistical insights"""
    logger.info(f"Extracting metadata for DataFrame with {len(df.columns)} columns")
    metadata = []

    for col in df.columns:
        logger.debug(f"Processing column: {col}")
        series = df[col].dropna()
        stats = {}

        # Convert datetime values to strings for sample_values
        sample_values = series.head(5)
        if pd.api.types.is_datetime64_any_dtype(series):
            sample_values = sample_values.dt.strftime("%Y-%m-%d").tolist()
            logger.debug(f"Converted datetime values for column {col}")
        else:
            sample_values = sample_values.tolist()

        if pd.api.types.is_numeric_dtype(series):
            logger.debug(f"Computing numeric statistics for {col}")
            stats.update(
                {
                    "min": float(series.min()),
                    "max": float(series.max()),
                    "mean": float(series.mean()),
                    "std": float(series.std()),
                    "outliers": _detect_outliers(series),
                }
            )
        elif pd.api.types.is_datetime64_any_dtype(series):
            logger.debug(f"Computing datetime statistics for {col}")
            stats.update(
                {
                    "start": series.min().strftime("%Y-%m-%d"),
                    "end": series.max().strftime("%Y-%m-%d"),
                    "unique_days": series.nunique(),
                }
            )
        elif pd.api.types.is_categorical_dtype(series) or series.nunique() < 20:
            logger.debug(f"Computing categorical statistics for {col}")
            stats.update(
                {
                    "top_values": series.value_counts(normalize=True).head(3).to_dict(),
                    "unique_count": series.nunique(),
                }
            )

        metadata.append(
            ColumnMetadata(
                name=col,
                dtype=str(series.dtype),
                unique_values=series.unique().tolist()
                if series.nunique() < 20
                else None,
                sample_values=sample_values,
                stats=stats,
            )
        )

    logger.info(f"Completed metadata extraction for {len(metadata)} columns")
    return metadata


def enhance_query_with_metadata(query: str, metadata: List[ColumnMetadata]) -> str:
    """Enhance query with statistical highlights"""
    logger.info("Enhancing query with metadata")
    logger.debug(f"Original query: {query}")

    enhancements = []
    for col in metadata:
        if col.stats:
            highlights = []
            if "min" in col.stats and "max" in col.stats:
                highlights.append(f"range {col.stats['min']}-{col.stats['max']}")
            if "top_values" in col.stats:
                highlights.append(
                    "common values: "
                    + ", ".join(
                        f"{k} ({v:.1%})" for k, v in col.stats["top_values"].items()
                    )
                )
            if highlights:
                enhancements.append(f"{col.name}: {', '.join(highlights)}")

    enhanced_query = f"{query}\n\nData Features:\n- " + "\n- ".join(enhancements)
    logger.debug(f"Enhanced query: {enhanced_query}")
    return enhanced_query


def get_llm_analysis_plan(
    query: str, metadata: List[ColumnMetadata]
) -> AnalysisRequest:
    """Get analysis parameters from LLM with structured output"""
    logger.info("Getting analysis plan from LLM")
    logger.debug(f"Input query: {query}")

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

    model = get_groq_llm(DESCRIPTION_GENERATOR_SELECTOR_MODEL)
    chain = prompt_template | model

    logger.debug("Sending request to LLM")
    response = chain.invoke({"query": query, "columns": columns_str})
    logger.debug(f"Received response from LLM: {response.content}")

    analysis_request = _parse_llm_response(response.content)
    logger.info(f"Generated analysis plan of type: {analysis_request.analysis_type}")
    return analysis_request


def _parse_llm_response(response: str) -> AnalysisRequest:
    """Parse LLM response into structured format"""
    logger.debug("Parsing LLM response")
    logger.debug(f"Raw response: {response}")

    parsed = {"selected_columns": [], "analysis_type": "", "parameters": {}}
    for line in response.strip().split("\n"):
        if line.startswith("selected_columns:"):
            parsed["selected_columns"] = [
                x.strip() for x in line.split(":")[1].split(",")
            ]
        elif line.startswith("analysis_type:"):
            parsed["analysis_type"] = line.split(":")[1].strip()
        elif line.startswith("parameters:"):
            params = line.split(":")[1].strip()
            parsed["parameters"] = dict(
                item.split(":") for item in params.split(",") if ":" in item
            )

    logger.debug(f"Parsed response: {parsed}")
    return AnalysisRequest(**parsed)


def _calculate_insights(df: pd.DataFrame, request: AnalysisRequest) -> Dict:
    """Perform calculations based on analysis plan"""
    logger.info("Calculating insights based on analysis plan")
    logger.debug(f"Analysis request: {request}")

    insights = {"summary_stats": {}, "relationships": {}}

    # Column-level statistics
    for col in request.selected_columns:
        if col in df.columns:
            logger.debug(f"Computing statistics for column: {col}")
            series = df[col].dropna()
            insights["summary_stats"][col] = {
                "mean": series.mean() if series.dtype.kind in "iufc" else None,
                "unique_count": series.nunique(),
                "trend": _calculate_trend(series) if series.dtype.kind in "M" else None,
            }

    # Cross-column analysis
    if len(request.selected_columns) >= 2:
        logger.debug("Computing cross-column relationships")
        insights["relationships"] = {
            "correlation": _calculate_correlation(df, request.selected_columns),
            # "cross_tabs": _calculate_crosstabs(df, request.selected_columns),
        }

    # Time-based analysis
    if "time_column" in request.parameters:
        time_col = request.parameters["time_column"]
        if time_col in df.columns:
            logger.debug(f"Performing time-based analysis using column: {time_col}")
            insights["time_analysis"] = _analyze_time_series(df, time_col, request)

    logger.info("Completed insights calculation")
    return insights


def _calculate_trend(series: pd.Series) -> Dict:
    """Calculate linear trend for time series data"""
    if len(series) < 2:
        return {}

    # Convert datetime to numeric format
    if pd.api.types.is_datetime64_any_dtype(series):
        x = series.astype("int64").values.astype(float)
    else:
        x = np.arange(len(series))

    y = x if pd.api.types.is_datetime64_any_dtype(series) else series.values
    slope, intercept = np.polyfit(x, y, 1)

    return {
        "slope_per_observation": float(slope),
        "percent_change": float((slope * len(series)) / y[0]) if y[0] != 0 else 0,
    }


def _calculate_correlation(df: pd.DataFrame, columns: List[str]) -> Dict:
    """Calculate top 5 strongest correlations between numeric columns"""
    numeric_cols = [col for col in columns if pd.api.types.is_numeric_dtype(df[col])]

    if len(numeric_cols) < 2:
        return {}

    corr_matrix = df[numeric_cols].corr().abs()
    np.fill_diagonal(corr_matrix.values, 0)  # Ignore self-correlations

    # Get top 5 correlation pairs
    correlations = corr_matrix.stack().sort_values(ascending=False).head(5).to_dict()

    return {
        "top_correlations": [
            f"{pair[0]} & {pair[1]} ({strength:.2f})"
            for pair, strength in correlations.items()
        ]
    }


def _calculate_crosstabs(df: pd.DataFrame, columns: List[str]) -> Dict:
    """Calculate categorical relationships"""
    if len(columns) >= 2 and all(col in df.columns for col in columns):
        return pd.crosstab(df[columns[0]], df[columns[1]]).to_dict()
    return {}


def _analyze_time_series(
    df: pd.DataFrame, time_col: str, request: AnalysisRequest
) -> Dict:
    """Analyze time-based patterns"""
    df = df.set_index(time_col).sort_index()
    analysis = {}

    if "measure" in request.parameters:
        measure_col = request.parameters["measure"]
        if measure_col in df.columns:
            analysis["rolling_stats"] = {
                "7_day_mean": df[measure_col].rolling("7D").mean().dropna().to_dict(),
                "30_day_max": df[measure_col].rolling("30D").max().dropna().to_dict(),
            }

    return analysis


def generate_description(df: pd.DataFrame, query: str) -> str:
    """Full analysis pipeline"""
    logger.info(f"Starting description generation for query: {query}")
    logger.debug(f"Input DataFrame shape: {df.shape}")

    # 1. Extract metadata
    metadata = extract_column_metadata(df)
    logger.info(f"Extracted metadata for {len(metadata)} columns")

    # 2. Enhance query
    enhanced_query = enhance_query_with_metadata(query, metadata)
    logger.info("Enhanced query with metadata")

    # 3. Get LLM analysis plan
    analysis_plan = get_llm_analysis_plan(enhanced_query, metadata)
    logger.info(f"Generated analysis plan of type: {analysis_plan.analysis_type}")

    # 4. Validate selection
    valid_columns = [col for col in analysis_plan.selected_columns if col in df.columns]
    if not valid_columns:
        logger.warning(
            "No valid columns found in analysis plan, using first two columns"
        )
        valid_columns = [col.name for col in metadata[:2]]

    # 5. Calculate insights
    insights = _calculate_insights(df, analysis_plan)
    logger.info("Calculated insights")

    # 6. Generate final description
    logger.info("Generating final description using LLM")
    prompt = ChatPromptTemplate.from_template(
        """As a marketing data analyst, create a concise report section based on these insights. Structure your response for executive readability:

**Client Query**: {query}

**Analysis Context**:
- Focus Metrics: {columns}
- Analysis Method: ...
- Time Frame: ...

**Key Marketing Insights**:
1. Performance Highlights (Lead with numbers):
   - Include: CTR, Conversion Rates, CAC, ROI where applicable
2. Audience Trends:
   - Segment by: ...
3. Notable Patterns:
   - ...
   - ...
   - ...

**Recommendations** (Max 3 actionable items):
- Budget reallocation suggestions
- Optimization opportunities
- A/B testing ideas

**Visualization Suggestions**:
- 1-2 chart types that best represent these insights
- Brief rationale for each choice

Formatting Rules:
→ Use bold section headers
→ Prepend marketing KPIs with ▸ symbols
→ Keep paragraphs under 50 words
→ Compare to previous period if data allows
→ Highlight statistical significance (p < 0.05) where applicable

Example of good response:
"Email campaigns showed 225% higher conversion vs social ads (p=0.03).  
▸ CAC decreased 15% MoM to $4.50  
Recommend testing subject line variants in top-performing segments..."

Insights Data:
{insights}"""
    )

    model = get_groq_llm(DESCRIPTION_GENERATOR_MODEL)

    response = model.invoke(
        prompt.format(
            query=query,
            columns=", ".join(valid_columns),
            analysis_type=analysis_plan.analysis_type,
            parameters=str(analysis_plan.parameters),
            insights=str(insights),
        )
    )

    logger.info("Description generation completed")

    cleaned_content = re.sub(
        r"\s*<think>.*?</think>\s*",
        "",
        response.content,
        flags=re.IGNORECASE | re.DOTALL,
    )
    cleaned_content = re.sub(
        r"\s*</?gpt[^>]*>\s*", "", cleaned_content, flags=re.IGNORECASE
    )

    logger.info("Description generation completed")
    return cleaned_content


if __name__ == "__main__":
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)

    import numpy as np

    test_data = {
        "date": pd.date_range(start="2023-01-01", periods=100),
        "sales": np.random.normal(1000, 200, 100),
        "customers": np.random.randint(50, 200, 100),
        "category": np.random.choice(["A", "B", "C"], 100),
    }
    test_df = pd.DataFrame(test_data)
    test_query = "Describe the sales trends over customers"

    logger.info(f"Testing with query: '{test_query}'")
    try:
        description = generate_description(test_df, test_query)
        print(f"Generated description:\n{description}")
    except Exception as e:
        logger.error(f"Error in test: {str(e)}", exc_info=True)
