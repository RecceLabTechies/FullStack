#!/usr/bin/env python
from typing import List, Dict, Any
import numpy as np
import pandas as pd
from pydantic import BaseModel
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import Tool
from langchain_experimental.utilities import PythonREPL
from scipy import stats
from pandas.api.types import (
    is_numeric_dtype,
)


class ColumnSelections(BaseModel):
    """Pydantic model for storing selected columns from JSON files."""

    selections: list[tuple[str, str]]


class HTMLElement(BaseModel):
    """
    Pydantic model for a single HTML element.

    Attributes:
        tag: The HTML tag (h1, h2, h3, p, etc.)
        content: The text content for this element
    """

    tag: str
    content: str


class StructuredDescription(BaseModel):
    """
    Pydantic model for the complete structured description.

    Attributes:
        elements: List of HTMLElement objects representing the formatted description
    """

    elements: List[HTMLElement]


def analyze_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate comprehensive statistical analysis for all columns in the DataFrame.

    Args:
        df (pd.DataFrame): Input DataFrame to analyze

    Returns:
        Dict[str, Any]: Dictionary containing detailed statistics for each column
    """
    report = {}

    for column in df.columns:
        try:
            if is_numeric_dtype(df[column]):
                # Numeric column analysis
                statistics = {
                    "Total Records": len(df),
                    "Missing Values": df[column].isnull().sum(),
                    "Missing Values %": (df[column].isnull().sum() / len(df)) * 100,
                    "Unique Values": df[column].nunique(),
                    "Unique Values %": (df[column].nunique() / len(df)) * 100,
                    "Basic Statistics": {
                        "Mean": df[column].mean(),
                        "Median": df[column].median(),
                        "Mode": (
                            df[column].mode().iloc[0]
                            if not df[column].mode().empty
                            else None
                        ),
                        "Standard Deviation": df[column].std(),
                        "Variance": df[column].var(),
                        "Skewness": df[column].skew(),
                        "Kurtosis": df[column].kurtosis(),
                    },
                    "Distribution": {
                        "Min": df[column].min(),
                        "Max": df[column].max(),
                        "Range": df[column].max() - df[column].min(),
                        "Q1": df[column].quantile(0.25),
                        "Q3": df[column].quantile(0.75),
                        "IQR": df[column].quantile(0.75) - df[column].quantile(0.25),
                    },
                    "Percentiles": {
                        "10th": df[column].quantile(0.1),
                        "25th": df[column].quantile(0.25),
                        "50th": df[column].quantile(0.5),
                        "75th": df[column].quantile(0.75),
                        "90th": df[column].quantile(0.9),
                        "95th": df[column].quantile(0.95),
                        "99th": df[column].quantile(0.99),
                    },
                    "Outliers": {
                        "Count": len(df[np.abs(stats.zscore(df[column])) > 3]),
                        "Percentage": (
                            len(df[np.abs(stats.zscore(df[column])) > 3]) / len(df)
                        )
                        * 100,
                    },
                }
            else:
                # Categorical or datetime column analysis
                value_counts = df[column].value_counts()
                value_percentages = (value_counts / len(df)) * 100

                statistics = {
                    "Total Records": len(df),
                    "Missing Values": df[column].isnull().sum(),
                    "Missing Values %": (df[column].isnull().sum() / len(df)) * 100,
                    "Unique Values": df[column].nunique(),
                    "Unique Values %": (df[column].nunique() / len(df)) * 100,
                    "Category Analysis": {
                        "Top 5 Categories": value_counts.head().to_dict(),
                        "Top 5 Percentages": value_percentages.head().to_dict(),
                        "Bottom 5 Categories": value_counts.tail().to_dict(),
                        "Bottom 5 Percentages": value_percentages.tail().to_dict(),
                    },
                    "Distribution": {
                        "Category Count": len(value_counts),
                        "Most Common": value_counts.index[0],
                        "Most Common Count": value_counts.iloc[0],
                        "Most Common %": value_percentages.iloc[0],
                    },
                }

                if len(value_counts) <= 20:  # Only for reasonable number of categories
                    statistics["Complete Distribution"] = {
                        "Categories": value_counts.to_dict(),
                        "Percentages": value_percentages.to_dict(),
                    }

            report[column] = statistics

        except Exception as e:
            report[column] = {"error": str(e)}

    return report


def select_relevant_columns(df: pd.DataFrame, query: str) -> pd.DataFrame:
    """
    Select relevant columns from the DataFrame based on the query.

    Args:
        df (pd.DataFrame): Input DataFrame
        query (str): User's analysis query

    Returns:
        pd.DataFrame: DataFrame with only relevant columns
    """
    # Create prompt for column selection
    column_selection_prompt = ChatPromptTemplate.from_template(
        """You are a data analysis assistant. Given a user's query and available columns, select the most relevant columns for analysis.
        
        Query: {query}
        
        Available columns: {columns}
        
        INSTRUCTIONS:
        1. Analyze the query carefully
        2. Select ONLY columns that are directly relevant to answering the query
        3. Return EXACTLY a Python list of strings containing only the column names
        4. Do not include any explanation or additional text
        
        Example response format:
        ["column1", "column2"]
        
        Available columns for selection: {columns}
        
        Return only the Python list:"""
    )

    # Generate column selection
    model = OllamaLLM(model="llama3.2")
    selection_chain = column_selection_prompt | model
    raw_selection = selection_chain.invoke(
        {"query": query, "columns": list(df.columns)}
    )

    # Parse the response to get column list
    try:
        # Clean up the response
        cleaned_response = raw_selection.strip()
        if not cleaned_response.startswith("["):
            # Try to find the list in the response
            start_idx = cleaned_response.find("[")
            end_idx = cleaned_response.rfind("]")
            if start_idx != -1 and end_idx != -1:
                cleaned_response = cleaned_response[start_idx : end_idx + 1]
            else:
                print("Warning: Could not find valid column list in response")
                return df

        # Use Python REPL to safely evaluate the string as a Python list
        repl = PythonREPL()
        try:
            selected_columns = eval(cleaned_response)
            if not isinstance(selected_columns, list):
                raise ValueError("Response is not a list")
        except:
            print(f"Error parsing response: {cleaned_response}")
            return df

        # Filter to only existing columns
        valid_columns = [col for col in selected_columns if col in df.columns]

        if not valid_columns:
            print(f"\nWarning: No valid columns found in response: {cleaned_response}")
            print("Available columns:", list(df.columns))
            return df

        filtered_df = df[valid_columns]
        print(f"\nSelected columns for analysis: {valid_columns}")
        print("\nFiltered DataFrame preview:")
        print(filtered_df.head())
        return filtered_df

    except Exception as e:
        print(f"Error in column selection: {str(e)}")
        print("Using all columns instead")
        return df


def generate_description(df: pd.DataFrame, query: str) -> str:
    """
    Generate a markdown formatted description based on DataFrame analysis and user query.

    Args:
        df (pd.DataFrame): Input DataFrame to analyze
        query (str): Natural language query about the data

    Returns:
        str: Markdown formatted description
    """
    # First, select relevant columns based on the query
    filtered_df = select_relevant_columns(df, query)

    # Generate statistical report on filtered DataFrame
    stats_report = analyze_dataframe(filtered_df)

    # Create prompt for generating structured summary
    summary_prompt = ChatPromptTemplate.from_template(
        """As a senior data analyst, prepare a detailed executive report analyzing the following marketing campaign statistics in response to this query: {query}
        
        Statistical Report:\n{stats_report}\n
        
        Generate a comprehensive executive summary in markdown format that MUST:
        1. Begin with a level 1 heading (#) for the executive summary title that includes specific metrics
        2. Provide a detailed overview with:
           - Key numerical findings (use exact numbers)
           - Most significant trends
           - Critical insights
        3. For EACH of the following sections, provide specific metrics, comparisons, and actionable insights:
           
           Key Performance Metrics (##):
           - Compare actual numbers against targets
           - Highlight top and bottom performing metrics
           - Include specific percentage changes
           
           Trend Analysis (##):
           - Identify specific patterns in the data
           - Compare current performance with historical data
           - Quantify growth rates or decline
           
           Market Segmentation (##):
           - Break down performance by key segments
           - Identify best and worst performing segments
           - Include specific market share numbers
           
           Campaign Effectiveness (##):
           - ROI calculations with exact numbers
           - Cost per acquisition/conversion
           - Compare effectiveness across channels
           
           Areas of Opportunity (##):
           - Specific recommendations based on data
           - Potential impact in percentage/numbers
           - Priority areas for improvement
           
           Risk Factors (##):
           - Quantify potential risks
           - Impact assessment with numbers
           - Mitigation strategies
        
        IMPORTANT:
        - Every section MUST include specific numbers from the statistical report
        - Use ### headers for subsections within each major section
        - Each paragraph must contain at least 3 specific metrics or findings
        - Avoid generic statements - be specific and data-driven
        - Make clear connections between data points and business implications
        - Use proper markdown formatting (# for h1, ## for h2, ### for h3)
        - Use bullet points (- ) where appropriate
        - Use bold (**) and italic (*) for emphasis
        
        Example format (but with real numbers from the data):
        # Q3 Marketing Campaign Analysis: 28% ROI Growth with 12% Cost Reduction
        
        Analysis of 47,892 campaign touchpoints reveals a 28.3% increase in ROI, driven by a 12% reduction in customer acquisition costs and 15% higher conversion rates across digital channels. Mobile engagement showed particular strength, with a 42% year-over-year improvement in click-through rates.
        
        ## Key Performance Metrics
        Digital channel conversion rates increased from 3.2% to 4.8%, representing a 50% improvement. Cost per acquisition decreased from $34.50 to $30.36, while customer lifetime value increased by 23% to $156.78.
        
        ### Channel Performance
        Social media campaigns delivered the highest ROI at 312%, followed by email at 289% and display ads at 187%...
        
        [Continue with similar detailed, data-driven content for each section...]
        """
    )

    # Generate markdown summary
    model = OllamaLLM(model="llama3.2")
    summary_chain = summary_prompt | model
    markdown_summary = summary_chain.invoke(
        {"query": query, "stats_report": str(stats_report)}
    )

    return markdown_summary.strip()


if __name__ == "__main__":
    # Example usage with sample DataFrame
    sample_df = pd.DataFrame(
        {
            "age": np.random.normal(35, 10, 1000),
            "income": np.random.normal(50000, 15000, 1000),
            "satisfaction": np.random.choice([1, 2, 3, 4, 5], 1000),
            "category": np.random.choice(["A", "B", "C"], 1000),
            "region": np.random.choice(["North", "South", "East", "West"], 1000),
            "purchase_amount": np.random.normal(100, 30, 1000),
            "visit_frequency": np.random.poisson(5, 1000),
            "last_purchase_date": pd.date_range(
                end="2024-03-14", periods=1000, freq="D"
            ),
        }
    )

    print("\nOriginal DataFrame:")
    print(sample_df.head())

    query = input("\nEnter your analysis query: ")
    result = generate_description(sample_df, query)

    # Display the results
    print("\n=== Generated Description ===")
    print(result)
