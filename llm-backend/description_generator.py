#!/usr/bin/env python
from typing import List, Dict, Any
import numpy as np
import pandas as pd
from pydantic import BaseModel
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_experimental.utilities import PythonREPL
from scipy import stats
from pandas.api.types import (
    is_numeric_dtype,
)

print("🚀 Initializing Description Generator...")


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
    print("\n📊 Starting DataFrame analysis...")
    print(f"📈 Analyzing {len(df.columns)} columns")

    report = {}

    for column in df.columns:
        print(f"🔍 Analyzing column: {column}")
        try:
            if is_numeric_dtype(df[column]):
                print(f"📈 Processing numeric column: {column}")
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
                print(f"📊 Processing categorical column: {column}")
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
            print(f"✅ Completed analysis for {column}")

        except Exception as e:
            print(f"❌ Error analyzing column {column}: {str(e)}")
            report[column] = {"error": str(e)}

    print("✨ DataFrame analysis complete")
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
    print("\n🔍 Selecting relevant columns for analysis...")
    print(f"📊 Available columns: {', '.join(df.columns)}")

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
    print("🤖 Consulting LLM for column selection...")
    model = OllamaLLM(model="wizardlm2")
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
                print("⚠️ Could not find valid column list in response")
                return df

        # Use Python REPL to safely evaluate the string as a Python list
        repl = PythonREPL()
        try:
            selected_columns = eval(cleaned_response)
            if not isinstance(selected_columns, list):
                raise ValueError("Response is not a list")
        except:
            print(f"❌ Invalid column selection: {cleaned_response}")
            return df

        # Filter to only existing columns
        valid_columns = [col for col in selected_columns if col in df.columns]

        if not valid_columns:
            print(f"⚠️ No valid columns found in selection: {cleaned_response}")
            print("Available columns:", list(df.columns))
            return df

        filtered_df = df[valid_columns]
        print(
            f"✨ Selected {len(valid_columns)} relevant columns: {', '.join(valid_columns)}"
        )
        return filtered_df

    except Exception as e:
        print(f"❌ Column selection error: {str(e)}")
        return df


def generate_description(df: pd.DataFrame, query: str) -> StructuredDescription:
    """
    Generate a structured description based on DataFrame analysis and user query.

    Args:
        df (pd.DataFrame): Input DataFrame to analyze
        query (str): Natural language query about the data

    Returns:
        StructuredDescription: A structured description containing HTML elements
    """
    print("\n🔄 Generating structured description...")
    print(f"📝 Query: {query}")

    # First, select relevant columns based on the query
    filtered_df = select_relevant_columns(df, query)

    # Generate statistical report on filtered DataFrame
    print("📊 Analyzing filtered DataFrame...")
    stats_report = analyze_dataframe(filtered_df)

    # Create prompt for generating structured summary
    print("🤖 Generating executive summary...")
    summary_prompt = ChatPromptTemplate.from_template(
        """As a senior data analyst, prepare a detailed executive report analyzing the following marketing campaign statistics in response to this query: {query}
        
        Statistical Report:\n{stats_report}\n
        
        Generate a comprehensive executive summary as a JSON array. Each element must be a 2-element array: [tag, content].
        The tag must be one of: "h2", "h3", "p"
        
        Rules for structure:
        1. Start with an h2 title
        2. Each major section must be h2
        3. Subsections must be h3
        4. All content must be p tags
        5. Required major sections (h2):
           - Key Performance Metrics
           - Trend Analysis
           - Market Segmentation
           - Campaign Effectiveness
           - Areas of Opportunity
           - Risk Factors
        
        Format rules:
        1. Use ONLY double quotes (")
        2. Each array element must end with comma except the last one
        3. Keep all content on a single line - NO line breaks in content
        4. ALL text must be properly escaped JSON strings
        """
    )

    # Generate structured summary
    model = OllamaLLM(model="llama3.2")
    summary_chain = summary_prompt | model
    raw_elements = summary_chain.invoke(
        {"query": query, "stats_report": str(stats_report)}
    )

    # Parse the raw elements into a list of HTMLElement objects
    try:
        print("🔄 Parsing generated summary...")
        # Clean up the response and extract the list
        cleaned_response = raw_elements.strip()

        # Find the outermost list
        start_idx = cleaned_response.find("[")
        end_idx = cleaned_response.rfind("]")

        if start_idx == -1 or end_idx == -1:
            raise ValueError("Could not find valid list structure in response")

        list_content = cleaned_response[start_idx : end_idx + 1]

        # Preprocessing to clean up common JSON issues
        import re

        # 1. Remove any line breaks within content
        list_content = re.sub(r'"\s*\n\s*"', '" "', list_content)

        # 2. Remove any trailing commas before closing brackets
        list_content = re.sub(r",(\s*])", r"\1", list_content)

        # 3. Ensure commas between array elements
        list_content = re.sub(r"]\s*\n\s*\[", "],\n[", list_content)

        # 4. Remove any non-JSON content
        list_content = re.sub(
            r'[^\[\],\s"{}:.\-\d\w@$%&()*+/<>=?^_`~]+', "", list_content
        )

        # Parse JSON
        import json

        elements_list = json.loads(list_content)

        # Validate and convert to HTMLElement objects
        html_elements = []
        valid_tags = {"h2", "h3", "p"}
        required_h2_sections = {
            "Key Performance Metrics",
            "Trend Analysis",
            "Market Segmentation",
            "Campaign Effectiveness",
            "Areas of Opportunity",
            "Risk Factors",
        }
        found_h2_sections = set()
        current_level = None

        print("🔍 Validating generated content structure...")
        for item in elements_list:
            if not isinstance(item, list) or len(item) != 2:
                continue

            tag, content = item
            if not isinstance(tag, str) or not isinstance(content, str):
                continue

            if tag not in valid_tags:
                continue

            # Enforce tag hierarchy
            if tag == "h2":
                current_level = "h2"
                if any(section in content for section in required_h2_sections):
                    found_h2_sections.add(
                        next(
                            section
                            for section in required_h2_sections
                            if section in content
                        )
                    )
            elif tag == "h3":
                if current_level != "h2":
                    continue
                current_level = "h3"
            elif tag == "p":
                if current_level not in ("h2", "h3"):
                    continue

            html_elements.append(HTMLElement(tag=tag, content=content))

        # Verify all required sections are present
        missing_sections = required_h2_sections - found_h2_sections
        if missing_sections:
            print(f"⚠️ Missing sections in analysis: {missing_sections}")

        if not html_elements:
            raise ValueError("No valid elements found after parsing")

        print(f"✨ Generated structured description with {len(html_elements)} elements")
        return StructuredDescription(elements=html_elements)

    except Exception as e:
        print(f"❌ Error generating description: {str(e)}")
        return StructuredDescription(
            elements=[
                HTMLElement(tag="h2", content="Error Generating Report"),
                HTMLElement(tag="p", content=f"Failed to generate report: {str(e)}"),
            ]
        )


if __name__ == "__main__":
    print("\n🚀 Running description generator demo...")
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

    print("\n💭 Please enter your analysis query")
    query = input("\n❓ Enter your analysis query: ")
    result = generate_description(sample_df, query)

    print("\n📝 Analysis Results:")
    for element in result.elements:
        print(f"{element.tag}: {element.content}")
