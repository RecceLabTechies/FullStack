#!/usr/bin/env python
from typing import Dict, Any, List
import pandas as pd
import numpy as np
import json
from langchain_ollama.llms import OllamaLLM
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from pandas.api.types import (
    is_datetime64_any_dtype,
    is_numeric_dtype,
)

print("🚀 Initializing Chart Data Generator...")


class ChartInfo(BaseModel):
    """
    Pydantic model for chart generation parameters.

    Attributes:
        x_axis (str): Column name for x-axis
        y_axis (str): Column name for y-axis
        chart_type (str): Type of chart to generate (line, scatter, bar, box, heatmap)
    """

    x_axis: str
    y_axis: str
    chart_type: str

    class Config:
        frozen = True


def get_column_type(series: pd.Series) -> str:
    """
    Determine the data type of a pandas Series.

    Args:
        series (pd.Series): Input series to check

    Returns:
        str: Data type category ('datetime', 'numeric', or 'categorical')
    """
    if is_datetime64_any_dtype(series):
        return "datetime"
    elif is_numeric_dtype(series):
        return "numeric"
    return "categorical"


def select_columns_for_chart(query: str, df: pd.DataFrame) -> ChartInfo:
    """
    Use LLM to select appropriate columns from DataFrame for visualization.

    Args:
        query (str): Natural language query about the visualization
        df (pd.DataFrame): Input DataFrame

    Returns:
        ChartInfo: Selected columns and chart type

    Raises:
        ValueError: If LLM response is invalid or column selection fails
    """
    print("\n🔍 Analyzing query for chart column selection...")
    print(f"📊 Available columns: {', '.join(df.columns)}")

    prompt = ChatPromptTemplate.from_template(
        """Given the following DataFrame columns and query, determine the most appropriate columns for visualization.

Available columns and their data types:
{column_info}

Query: {query}

Consider the data types when selecting columns:
- For time series: use datetime columns
- For comparisons: use numeric vs categorical columns
- For distributions: use numeric columns
- For relationships: use numeric vs numeric columns
- For categorical analysis: use categorical columns

You must respond in EXACTLY this format (no other text):
x_axis: [column name for x-axis]
y_axis: [column name for y-axis]
chart_type: [one of: line, scatter, bar, box, heatmap]"""
    )

    column_info = [f"{col}: {get_column_type(df[col])}" for col in df.columns]
    print("📋 Column types identified")

    try:
        print("🤖 Consulting LLM for column selection...")
        model = OllamaLLM(model="olmo2")
        response = (prompt | model).invoke(
            {"column_info": "\n".join(column_info), "query": query}
        )

        parsed = dict(
            line.split(": ", 1)
            for line in response.strip().split("\n")
            if line.strip() and ": " in line
        )

        chart_info = ChartInfo(**parsed)
        print(
            f"✨ Selected columns - X: {chart_info.x_axis}, Y: {chart_info.y_axis}, Type: {chart_info.chart_type}"
        )
        return chart_info
    except Exception as e:
        print(f"❌ Column selection failed: {str(e)}")
        raise ValueError(f"Failed to select columns: {str(e)}")


def generate_chart_data(df: pd.DataFrame, query: str) -> Dict[str, Any]:
    """
    Generate chart data structured for Recharts based on the query and DataFrame.

    Args:
        df (pd.DataFrame): Input DataFrame containing the data
        query (str): Natural language query describing the desired visualization

    Returns:
        Dict[str, Any]: JSON-structured data for Recharts

    Raises:
        ValueError: If data preparation fails
    """
    print("\n🔄 Generating chart data...")
    print(f"📊 DataFrame shape: {df.shape}")

    chart_info = select_columns_for_chart(query, df)

    CHART_TYPE_MAPPING = {
        "line": "LineChart",
        "scatter": "ScatterChart",
        "bar": "BarChart",
        "box": "ComposedChart",
        "heatmap": "Heatmap",
    }

    print(f"📈 Preparing {CHART_TYPE_MAPPING[chart_info.chart_type]} visualization...")
    data: List[Dict[str, Any]] = []

    if chart_info.chart_type == "heatmap":
        print("🔥 Generating heatmap data...")
        crosstab = pd.crosstab(df[chart_info.x_axis], df[chart_info.y_axis])
        data = [
            {"x": str(idx), "y": str(col), "value": float(np.asarray(value))}
            for idx in crosstab.index
            for col, value in crosstab.loc[idx].items()
        ]
    else:
        print("📊 Processing standard chart data...")
        data = [
            {
                chart_info.x_axis: (
                    row[chart_info.x_axis].isoformat()
                    if isinstance(row[chart_info.x_axis], pd.Timestamp)
                    else row[chart_info.x_axis]
                ),
                chart_info.y_axis: row[chart_info.y_axis],
            }
            for _, row in df.iterrows()
        ]

        # Limit to 100 data points if there are more
        if len(data) > 100:
            print("⚡ Optimizing data points (limiting to 100)...")
            step = len(data) // 100
            data = data[::step][:100]

    print(f"✨ Generated {len(data)} data points")

    def get_axis_config(column: str, is_heatmap: bool = False) -> Dict[str, str]:
        return {
            "dataKey": (
                "x"
                if is_heatmap and column == chart_info.x_axis
                else "y" if is_heatmap and column == chart_info.y_axis else column
            ),
            "type": get_column_type(df[column]),
            "label": column,
        }

    chart_data = {
        "data": data,
        "type": CHART_TYPE_MAPPING.get(chart_info.chart_type, "LineChart"),
        "xAxis": get_axis_config(chart_info.x_axis, chart_info.chart_type == "heatmap"),
        "yAxis": get_axis_config(chart_info.y_axis, chart_info.chart_type == "heatmap"),
    }

    print("✅ Chart data generation complete")
    return chart_data


if __name__ == "__main__":
    print("\n🚀 Running chart data generator demo...")
    # Example usage
    sample_df = pd.DataFrame(
        {
            "date": pd.date_range("2023-01-01", "2023-12-31", freq="D"),
            "sales": np.random.randint(100, 1000, 365),
            "category": np.random.choice(["A", "B", "C"], 365),
            "region": np.random.choice(["North", "South", "East", "West"], 365),
        }
    )
    try:
        print("\n💭 Please enter your visualization query")
        query = input("Enter your visualization query: ")
        print("\n🔄 Processing query...")
        chart_data = generate_chart_data(sample_df, query)
        print("✨ Chart data generated successfully")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
