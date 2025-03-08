#!/usr/bin/env python


import json
import os
from typing import Dict, List, Tuple
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM
from langchain.prompts import ChatPromptTemplate


# Pydantic model for query generation
class QueryList(BaseModel):
    """
    Pydantic model for storing generated analysis queries.
    Each query is a tuple of (query_type, query_text) where
    query_type is either 'chart' or 'description'.
    """

    queries: list[tuple[str, str]]


def extract_headers(file_path: str) -> list[str]:
    """
    Extract column headers from a JSON file.

    This function handles both dictionary and list-based JSON structures,
    extracting the top-level keys as headers.

    Parameters:
        file_path (str): Path to the JSON file to process

    Returns:
        list[str]: List of column headers found in the JSON file

    Raises:
        json.JSONDecodeError: If the file contains invalid JSON
        FileNotFoundError: If the specified file doesn't exist
    """
    try:
        with open(file_path, "r") as f:
            data = json.load(f)

        if isinstance(data, dict):
            return list(data.keys())
        elif isinstance(data, list) and data:
            first_item = data[0]
            if isinstance(first_item, dict):
                return list(first_item.keys())
        return []
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error processing {file_path}: {str(e)}")
        raise


def recursive_json_schema_extractor(directory: str) -> Dict[str, List[str]]:
    """
    Recursively walks through a directory to extract headers from all JSON files.

    This function builds a comprehensive map of all JSON files and their
    corresponding headers in the given directory and its subdirectories.

    Parameters:
        directory (str): Root directory to start the recursive search

    Returns:
        Dict[str, List[str]]: Mapping of file paths to their header lists
    """
    schemas = {}
    for entry in os.listdir(directory):
        full_path = os.path.join(directory, entry)
        if os.path.isdir(full_path):
            # Recursively process subdirectories
            schemas.update(recursive_json_schema_extractor(full_path))
        elif entry.lower().endswith(".json"):
            try:
                headers = extract_headers(full_path)
                schemas[full_path] = headers
            except Exception as e:
                print(f"Error processing file {full_path}: {e}")
    return schemas


data_dir = "./Data"
json_schemas = recursive_json_schema_extractor(data_dir)


# Format json_schemas into a readable string for the prompt (without type info)
def format_schemas_for_prompt(schemas: Dict[str, List[str]]) -> str:
    """
    Format JSON schemas into a readable string for the LLM prompt.

    Converts the schema dictionary into a formatted string where each line
    contains a filename and its associated headers.

    Parameters:
        schemas (Dict[str, List[str]]): Dictionary mapping file paths to headers

    Returns:
        str: Formatted string representation of schemas
    """
    formatted_str = ""
    for file_path, headers in schemas.items():
        file_name = os.path.basename(file_path)
        headers_str = ", ".join(headers)
        formatted_str += f"{file_name}: [{headers_str}]\n"
    return formatted_str


# Template for generating sub-queries
template = """
Given the following JSON file headers and a user query, generate comprehensive analytical sub-queries.

Available JSON files and their headers:
{json_headers}

User Query: {query}

Requirements:
1. Generate BOTH chart and description queries for each insight
2. Focus on:
   - Correlations between numeric columns
   - Distributions of categorical data
   - Trends over time if temporal data exists
   - Summary statistics and key findings
   - Patterns and anomalies in the data
3. Each query must be unique:
   - A chart query can have a matching description query explaining the same insight
   - But no two chart queries or description queries should analyze the same thing
4. Generate at least 8-10 queries total (mix of charts and descriptions)
5. Output ONLY the queries in this exact format (one per line):
   [chart, "query text"]
   [description, "query text"]
6. Do not include any explanations or additional text

Example format:
[chart, "Create a line chart showing daily sales trends over time"]
[description, "Analyze and describe the daily sales trends, highlighting peak periods and patterns"]
[chart, "Generate a pie chart showing distribution of customer segments"]
[description, "Provide a detailed breakdown of customer segment distribution with percentages"]
"""


prompt = ChatPromptTemplate.from_template(template)
model = OllamaLLM(
    model="llama3.2",
    temperature=0.7,  # Balanced setting between creativity and consistency
)


# Function to parse LLM output into QueryList
def parse_llm_response(response: str) -> QueryList:
    """
    Parse the LLM's response into a structured QueryList object.

    This function processes the raw LLM output, validates query types,
    removes duplicates, and ensures proper formatting.

    Parameters:
        response (str): Raw response string from the LLM

    Returns:
        QueryList: Structured object containing validated queries
    """
    print("\n[DEBUG] Parsing LLM response:")
    print(f"Raw response:\n{response}")

    lines = response.strip().split("\n")
    queries = []
    seen_queries = set()

    print("\nProcessing lines:")
    for line in lines:
        try:
            clean_line = line.strip("[]")
            query_type, query_text = clean_line.split(",", 1)
            query_type = query_type.strip().lower()
            query_text = query_text.strip(' "')

            print(f"- Line: {line}")
            print(f"  Type: {query_type}")
            print(f"  Text: {query_text}")

            if query_type not in ["chart", "description"]:
                print("  ⚠️ Invalid query type - skipping")
                continue

            query_pair = (query_type, query_text)
            if query_pair not in seen_queries:
                queries.append(query_pair)
                seen_queries.add(query_pair)
                print("  ✓ Added to queries")
            else:
                print("  ⚠️ Duplicate query - skipping")
        except ValueError:
            print(f"  ⚠️ Error parsing line: {line}")
            continue

    print(f"\nTotal queries parsed: {len(queries)}")
    return QueryList(queries=queries)


# Create the chain with structured output
chain = prompt | model | parse_llm_response


# Function to generate analysis queries
def generate_analysis_queries(user_query: str) -> QueryList:
    """
    Generate analysis queries based on user input using the global JSON schemas.

    This function coordinates the entire query generation process:
    1. Validates inputs
    2. Formats schemas for the prompt
    3. Generates queries using the LLM
    4. Returns structured results

    Parameters:
        user_query (str): The user's analysis request

    Returns:
        QueryList: A structured list of generated queries with their types

    Raises:
        ValueError: If the input parameters are invalid
    """
    if not user_query.strip():
        raise ValueError("User query cannot be empty")
    if not json_schemas:
        raise ValueError("No JSON schemas available in the data directory")

    formatted_headers = format_schemas_for_prompt(json_schemas)

    try:
        result = chain.invoke({"json_headers": formatted_headers, "query": user_query})
        return result
    except Exception as e:
        print(f"Error generating queries: {str(e)}")
        raise


# Example usage
if __name__ == "__main__":
    # Example usage with error handling
    try:
        test_query = "Generate a comprehensive analysis report"
        result = generate_analysis_queries(test_query)

        print("\nGenerated Analysis Queries:")
        for query_type, query in result.queries:
            print(f"[{query_type}] {query}")
    except Exception as e:
        print(f"Error during query generation: {str(e)}")
