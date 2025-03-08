#!/usr/bin/env python
import os
import json
import pandas as pd
from typing import Optional, List, Dict
from pydantic import BaseModel
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate


class JSONAnalysisResult(BaseModel):
    """
    Pydantic model for storing the selected JSON file and the original query.

    Attributes:
        json_file: Name of the selected JSON file
        query: Original user query
    """

    json_file: Optional[str] = None
    query: str


def extract_json_info(directory: str) -> dict:
    """
    Extract field and sample value information from all JSON files in a directory.

    Args:
        directory (str): Directory path containing JSON files

    Returns:
        dict: Dictionary mapping JSON filenames to their field and sample value information
    """
    json_info = {}

    # Ensure directory exists
    if not os.path.exists(directory):
        print(f"Warning: Directory {directory} does not exist")
        return json_info

    for entry in os.listdir(directory):
        if entry.lower().endswith(".json"):
            try:
                file_path = os.path.join(directory, entry)
                with open(file_path, "r") as f:
                    data = json.load(f)

                # Handle both single object and array of objects
                if isinstance(data, list) and data:
                    sample_data = data[:5]  # Take up to 5 samples
                    fields = list(data[0].keys())
                elif isinstance(data, dict):
                    sample_data = [data]
                    fields = list(data.keys())
                else:
                    continue

                # Get sample values for each field
                sample_values = {}
                for field in fields:
                    samples = []
                    for item in sample_data:
                        if field in item and item[field] is not None:
                            samples.append(str(item[field]))
                        if len(samples) >= 3:  # Limit to 3 samples
                            break
                    sample_values[field] = samples

                json_info[entry] = {
                    "fields": fields,
                    "sample_values": sample_values,
                    "path": file_path,  # Store the full path
                }
            except Exception as e:
                print(f"Error processing file {entry}: {e}")

    if not json_info:
        print(f"Warning: No JSON files found in {directory}")

    return json_info


def format_json_info_for_prompt(json_info: dict) -> str:
    """
    Format the JSON information into a string suitable for the LLM prompt.

    Args:
        json_info (dict): Dictionary containing JSON file information

    Returns:
        str: Formatted string showing file names, fields, and sample values
    """
    if not json_info:
        return "No JSON files available for analysis."

    formatted_info = []
    for file_name, info in json_info.items():
        file_desc = [f"File: {file_name}"]
        file_desc.append("Fields: " + ", ".join(info["fields"]))

        # Add sample values for each field
        samples = []
        for field in info["fields"]:
            sample_vals = info["sample_values"][field]
            if sample_vals:
                samples.append(f"{field} examples: {', '.join(map(str, sample_vals))}")

        file_desc.append("Sample values:")
        file_desc.extend([f"  {sample}" for sample in samples])
        formatted_info.append("\n".join(file_desc))

    return "\n\n".join(formatted_info)


def select_json_for_query(query: str, data_dir: str = "./data") -> JSONAnalysisResult:
    """
    Select the most appropriate JSON file for a given query using LLM.

    Args:
        query (str): Natural language query about the data
        data_dir (str): Directory containing the JSON files

    Returns:
        JSONAnalysisResult: Selected JSON file and query
    """
    # Extract JSON information
    json_info = extract_json_info(data_dir)

    # Create basic result with query
    result = JSONAnalysisResult(query=query)

    # If no JSON files found, return early
    if not json_info:
        return result

    formatted_info = format_json_info_for_prompt(json_info)

    # Create prompt template
    prompt = ChatPromptTemplate.from_template(
        """Given the following JSON files and their contents, determine the most appropriate file for the query.

Available JSON files and their contents:
{json_info}

Query: {query}

You MUST ONLY select from the JSON files listed above.
Analyze the fields and sample values to determine which JSON file would be most relevant for this query.
Respond in this exact format:
file: [selected json filename]

Important: The filename MUST be exactly as shown in the available files list."""
    )

    # Initialize LLM and create chain
    model = OllamaLLM(model="llama3.2")

    try:
        # Execute the chain
        response = model.invoke(prompt.format(json_info=formatted_info, query=query))

        # Parse the response
        response_lines = response.strip().split("\n")
        if response_lines:
            file_name = response_lines[0].split(":", 1)[1].strip()

            # Validate that the selected file exists in our json_info
            if file_name in json_info:
                result.json_file = file_name
            else:
                print(
                    f"Warning: Selected file '{file_name}' not found in available JSON files"
                )
        else:
            print("Warning: Invalid response format from LLM")

    except Exception as e:
        print(f"Error during JSON selection: {e}")

    return result


if __name__ == "__main__":
    query = input("Enter your query about the data: ")
    result = select_json_for_query(query)

    print("\nResult:")
    print(f"Query: {result.query}")
    print(
        f"Selected JSON: {result.json_file if result.json_file else 'No file selected'}"
    )
