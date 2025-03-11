#!/usr/bin/env python
import json
import pandas as pd
import re
from typing import Tuple
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import Tool
from langchain_experimental.utilities import PythonREPL

print("🚀 Initializing JSON Processor...")


def validate_filter_values(filter_code: str, df: pd.DataFrame) -> str:
    """
    Validate and adjust filter code based on actual column values.

    Args:
        filter_code (str): The original filter code
        df (pd.DataFrame): The DataFrame to validate against

    Returns:
        str: Validated and potentially adjusted filter code
    """
    print("\n🔍 Validating filter values...")
    # Match patterns like df['column'] == 'value' or df["column"] == "value"
    pattern = r"df\[[\'\"](\w+)[\'\"]\]\s*==\s*[\'\"](\w+)[\'\"]"
    match = re.search(pattern, filter_code)

    if match:
        column_name = match.group(1)
        target_value = match.group(2)

        if column_name in df.columns:
            print(f"📊 Checking values in column: {column_name}")
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
                print(f"✨ Found matching value: {actual_value}")
                return f"df[df['{column_name}'] == '{actual_value}']"
            else:
                print(f"⚠️ Value '{target_value}' not found in column '{column_name}'")
                print(
                    f"📋 Available values: {', '.join(map(str, df[column_name].unique()))}"
                )
                return "No filtering required"

    print("ℹ️ No specific filter validation needed")
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
    print(f"\n🔄 Processing JSON query for file: {json_file}")
    # Initialize Python REPL
    python_repl = PythonREPL()
    repl_tool = Tool(
        name="python_repl",
        description="A Python REPL for executing code",
        func=python_repl.run,
    )

    # Load the JSON file into a DataFrame
    try:
        print("💾 Loading JSON file...")
        with open(f"{data_dir}/{json_file}", "r") as f:
            data = json.load(f)

        # Convert to DataFrame
        df = pd.DataFrame(data if isinstance(data, list) else [data])
        print(f"📊 Created DataFrame with shape: {df.shape}")

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
        print("🤖 Consulting LLM for filtering requirements...")
        model = OllamaLLM(model="granite-code:8b")

        # Get sample data for context
        sample_data = df.head().to_string()

        # Get filtering decision from LLM
        response = model.invoke(
            prompt.format(
                columns=list(df.columns), sample_data=sample_data, query=query
            )
        ).strip()

        print(f"🔍 LLM response: {response}")

        # Apply filtering if needed
        if response.lower() != "no filtering required":
            try:
                print("🔄 Validating and applying filters...")
                # Validate and adjust filter code if needed
                validated_response = validate_filter_values(response, df)

                if validated_response != "No filtering required":
                    print("📊 Applying filter to DataFrame...")
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
                        print(f"✨ Filtered DataFrame shape: {df.shape}")
            except Exception as e:
                print(f"❌ Filter application error: {e}")

        print("✅ JSON processing complete")
        return df, query

    except Exception as e:
        print(f"❌ JSON processing error: {e}")
        # Return empty DataFrame if there's an error
        return pd.DataFrame(), query


if __name__ == "__main__":
    print("\n🚀 Running JSON processor demo...")
    # Get user input
    print("\n💭 Please enter the JSON file name and query")
    json_file = input("Enter JSON file name: ")
    query = input("Enter your query: ")

    # Process the query
    print("\n🔄 Processing query...")
    df, original_query = process_json_query(json_file, query)

    if not df.empty:
        print(f"\n✨ Results:")
        print(f"📊 Data Size: {df.shape[0]} rows × {df.shape[1]} columns")
        pd.set_option("display.max_columns", None)
        pd.set_option("display.expand_frame_repr", False)
        pd.set_option("display.max_rows", 5)
        print(df.head())
    else:
        print("⚠️ No data available")
