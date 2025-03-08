#!/usr/bin/env python
import pandas as pd
import seaborn as sns
from langchain_ollama.llms import OllamaLLM
import matplotlib.pyplot as plt
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from pandas.api.types import (
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
)
import numpy as np
import os
import base64
from io import BytesIO


class ChartInfo(BaseModel):
    """
    Pydantic model to validate and store chart generation parameters.

    Attributes:
        x_axis (str): Column name for x-axis
        y_axis (str): Column name for y-axis
        chart_type (str): Type of chart to generate
    """

    x_axis: str
    y_axis: str
    chart_type: str


def select_columns_for_chart(query: str, df: pd.DataFrame) -> ChartInfo:
    """
    Use LLM to select appropriate columns from DataFrame for visualization.

    Args:
        query (str): Natural language query about the visualization
        df (pd.DataFrame): Input DataFrame

    Returns:
        ChartInfo: Selected columns and chart type
    """
    # Create prompt template for column selection
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

Respond only with:
x_axis: [column name for x-axis]
y_axis: [column name for y-axis]
chart_type: [one of: line, scatter, bar, box, heatmap]"""
    )

    # Format column information
    column_info = []
    for col in df.columns:
        dtype = df[col].dtype
        if is_datetime64_any_dtype(df[col]):
            dtype = "datetime"
        elif is_numeric_dtype(df[col]):
            dtype = "numeric"
        elif is_object_dtype(df[col]):
            dtype = "categorical"
        column_info.append(f"{col}: {dtype}")

    # Initialize LLM
    model = OllamaLLM(model="llama3.2")

    # Create and execute the chain
    chain = prompt | model

    # Get response and parse it
    response = chain.invoke({"column_info": "\n".join(column_info), "query": query})

    # Parse response into ChartInfo
    parsed = dict(line.split(": ") for line in response.strip().split("\n"))
    return ChartInfo(**parsed)


def generate_chart(df: pd.DataFrame, query: str) -> str:
    """
    Generate an appropriate visualization based on the query and DataFrame.

    Args:
        df (pd.DataFrame): Input DataFrame containing the data
        query (str): Natural language query describing the desired visualization

    Returns:
        str: Base64 encoded string of the generated chart image

    Raises:
        ValueError: If the combination of data types is not supported
    """
    # Select columns for visualization
    try:
        chart_info = select_columns_for_chart(query, df)
    except Exception as e:
        raise ValueError(f"Error selecting columns for visualization: {str(e)}")

    # Set up the plot
    plt.figure(figsize=(12, 6))
    sns.set_style("whitegrid")

    try:
        # Generate the appropriate chart type
        if chart_info.chart_type == "line":
            sns.lineplot(data=df, x=chart_info.x_axis, y=chart_info.y_axis)
        elif chart_info.chart_type == "scatter":
            sns.scatterplot(data=df, x=chart_info.x_axis, y=chart_info.y_axis)
        elif chart_info.chart_type == "bar":
            sns.barplot(data=df, x=chart_info.x_axis, y=chart_info.y_axis)
        elif chart_info.chart_type == "box":
            sns.boxplot(data=df, x=chart_info.x_axis, y=chart_info.y_axis)
        elif chart_info.chart_type == "heatmap":
            sns.heatmap(
                pd.crosstab(df[chart_info.x_axis], df[chart_info.y_axis]),
                annot=True,
                fmt="d",
                cmap="YlOrRd",
            )
        else:
            raise ValueError(f"Unsupported chart type: {chart_info.chart_type}")

        # Format the plot
        plt.xticks(rotation=45)
        plt.xlabel(chart_info.x_axis)
        plt.ylabel(chart_info.y_axis)
        plt.title(f"{chart_info.y_axis} vs {chart_info.x_axis}")
        plt.tight_layout()

        # Save plot to BytesIO buffer
        buffer = BytesIO()
        plt.savefig(buffer, format="png", bbox_inches="tight")
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()  # Close the figure to free memory

        return f"data:image/png;base64,{image_base64}"

    except Exception as e:
        plt.close()  # Make sure to close the figure even if there's an error
        raise ValueError(f"Error generating chart: {str(e)}")


if __name__ == "__main__":
    # Example usage with sample DataFrame
    sample_df = pd.DataFrame(
        {
            "date": pd.date_range("2023-01-01", "2023-12-31", freq="D"),
            "sales": np.random.randint(100, 1000, 365),
            "category": np.random.choice(["A", "B", "C"], 365),
            "region": np.random.choice(["North", "South", "East", "West"], 365),
        }
    )

    query = input("Enter your visualization query: ")
    base64_image = generate_chart(sample_df, query)
    print("Generated chart as base64 string")
