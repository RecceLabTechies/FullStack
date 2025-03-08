#!/usr/bin/env python
import json
import pandas as pd
import re
from typing import Tuple
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import Tool
from langchain_experimental.utilities import PythonREPL


def validate_filter_values(filter_code: str, df: pd.DataFrame) -> str:
    """
    Validate and adjust filter code based on actual column values.

    Args:
        filter_code (str): The original filter code
        df (pd.DataFrame): The DataFrame to validate against

    Returns:
        str: Validated and potentially adjusted filter code
    """
    # Match patterns like df['column'] == 'value' or df["column"] == "value"
    pattern = r"df\[[\'\"](\w+)[\'\"]\]\s*==\s*[\'\"](\w+)[\'\"]"
    match = re.search(pattern, filter_code)

    if match:
        column_name = match.group(1)
        target_value = match.group(2)

        if column_name in df.columns:
            unique_values = df[column_name].unique()
            # Convert all values to strings for comparison
            unique_values = [str(val).lower() for val in unique_values]
            target_value = target_value.lower()

            # Check if the target value exists (case-insensitive)
            if target_value in unique_values:
                # Find the exact value with correct case
                actual_value = df[df[column_name].str.lower() == target_value][
                    column_name
                ].iloc[0]
                return f"df[df['{column_name}'] == '{actual_value}']"
            else:
                print(
                    f"Warning: Value '{target_value}' not found in column '{column_name}'."
                )
                print(
                    f"Available values: {', '.join(map(str, df[column_name].unique()))}"
                )
                return "No filtering required"

    return filter_code


def process_json_query(
    json_file: str, query: str, data_dir: str = "./data"
) -> Tuple[pd.DataFrame, str]:
    """
    Process a JSON file based on a query, potentially filtering the data as needed.

    Args:
        json_file (str): Name of the JSON file to process
        query (str): Original user query
        data_dir (str): Directory containing the JSON files

    Returns:
        Tuple[pd.DataFrame, str]: Processed DataFrame and the original query
    """
    # Initialize Python REPL
    python_repl = PythonREPL()
    repl_tool = Tool(
        name="python_repl",
        description="A Python REPL for executing code",
        func=python_repl.run,
    )

    # Load the JSON file into a DataFrame
    try:
        with open(f"{data_dir}/{json_file}", "r") as f:
            data = json.load(f)

        # Convert to DataFrame
        df = pd.DataFrame(data if isinstance(data, list) else [data])

        # Create a prompt to analyze if filtering is needed
        prompt = ChatPromptTemplate.from_template(
            """Given the following query and DataFrame information, determine if any filtering is needed and provide the filtering conditions in Python code.

DataFrame Columns: {columns}
Sample Data (first few rows):
{sample_data}

Query: {query}

Analyze if the query implies any filtering requirements.
If filtering is needed, respond with Python code that would filter the DataFrame.
If no filtering is needed, respond with "No filtering required."

Example responses:
"df[df['age'] > 25]"
"df[df['status'] == 'active']"
"No filtering required"

Response format - ONLY provide the filtering code or "No filtering required":"""
        )

        # Initialize LLM
        model = OllamaLLM(model="llama3.2")

        # Get sample data for context
        sample_data = df.head().to_string()

        # Get filtering decision from LLM
        response = model.invoke(
            prompt.format(
                columns=list(df.columns), sample_data=sample_data, query=query
            )
        ).strip()

        # Apply filtering if needed
        if response.lower() != "no filtering required":
            try:
                # Validate and adjust filter code if needed
                validated_response = validate_filter_values(response, df)

                if validated_response != "No filtering required":
                    # Set up the environment for the REPL
                    setup_code = f"""
import pandas as pd
df = pd.DataFrame({df.to_dict()})
result = {validated_response}
"""
                    # Execute the code using the REPL tool
                    repl_tool.run(setup_code)
                    # Get the filtered DataFrame from the REPL's namespace
                    filtered_df = eval("result", python_repl.locals)
                    if isinstance(filtered_df, pd.DataFrame):
                        df = filtered_df
            except Exception as e:
                print(f"Warning: Error applying filter: {e}")

        return df, query

    except Exception as e:
        print(f"Error processing JSON file: {e}")
        # Return empty DataFrame if there's an error
        return pd.DataFrame(), query


if __name__ == "__main__":
    # Get user input
    print("\n=== JSON Data Processor ===")
    json_file = input("Enter the JSON file name (e.g., data.json): ")
    query = input("Enter your query about the data: ")

    # Process the query
    print("\nProcessing query...")
    df, original_query = process_json_query(json_file, query)

    # Display results
    print("\n=== Results ===")
    print(f"Original Query: {original_query}")
    print(f"\nDataFrame Shape: {df.shape[0]} rows × {df.shape[1]} columns")

    if not df.empty:
        print("\nFirst few rows of the processed DataFrame:")
        # Set display options for better output
        pd.set_option("display.max_columns", None)
        pd.set_option("display.expand_frame_repr", False)
        pd.set_option("display.max_rows", 5)
        print(df.head())

        print("\nColumn Information:")
        for col in df.columns:
            unique_values = df[col].nunique()
            print(f"- {col}: {unique_values} unique values")
    else:
        print(
            "\nNo data to display. Please check if the JSON file exists and the query is valid."
        )
