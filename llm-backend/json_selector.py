#!/usr/bin/env python
import os
import json
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
        reason: Reason why this file was selected
        matching_fields: Fields that match the query criteria
        matching_values: Values that match the query criteria
    """

    json_file: Optional[str] = None
    query: str
    reason: Optional[str] = None
    matching_fields: Optional[List[str]] = None
    matching_values: Optional[Dict[str, List[str]]] = None


def extract_json_info(directory: str, unique_value_limit: int = 10) -> dict:
    """
    Extract field and sample value information from all JSON files in a directory.

    Args:
        directory (str): Directory path containing JSON files
        unique_value_limit (int): Maximum number of unique values to collect per field

    Returns:
        dict: Dictionary mapping JSON filenames to their field and sample value information
    """
    json_info = {}

    # Ensure directory exists
    if not os.path.exists(directory):
        print(f"⚠️ Directory not found: {directory}")
        return json_info

    for entry in os.listdir(directory):
        if entry.lower().endswith(".json"):
            try:
                file_path = os.path.join(directory, entry)
                with open(file_path, "r") as f:
                    data = json.load(f)

                # Handle both single object and array of objects
                if isinstance(data, list) and data:
                    sample_data = data[:5]  # Take up to 5 samples for display
                    all_data = data  # Use all data for unique value extraction
                    fields = list(data[0].keys())
                elif isinstance(data, dict):
                    sample_data = [data]
                    all_data = [data]
                    fields = list(data.keys())
                else:
                    continue

                # Get sample values for each field
                sample_values = {}
                unique_values = {}

                for field in fields:
                    # For sample display
                    samples = []
                    for item in sample_data:
                        if field in item and item[field] is not None:
                            samples.append(str(item[field]))
                        if len(samples) >= 3:  # Limit to 3 samples for display
                            break
                    sample_values[field] = samples

                    # For unique values collection
                    field_values = set()
                    for item in all_data:
                        if field in item and item[field] is not None:
                            # Convert to string for consistency
                            field_values.add(str(item[field]))
                            if len(field_values) >= unique_value_limit:
                                break
                    unique_values[field] = list(field_values)

                json_info[entry] = {
                    "fields": fields,
                    "sample_values": sample_values,
                    "unique_values": unique_values,
                    "path": file_path,  # Store the full path
                }
            except Exception as e:
                print(f"⚠️ Error in file {entry}: {e}")

    if not json_info:
        print(f"⚠️ No JSON files found in {directory}")

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

        # Add unique values for each field
        file_desc.append("Unique values by field:")
        for field in info["fields"]:
            unique_vals = info["unique_values"][field]
            if unique_vals:
                # Truncate the list if it's too long for display
                display_vals = unique_vals[:10]
                has_more = len(unique_vals) > 10

                unique_vals_str = ", ".join(map(str, display_vals))
                if has_more:
                    unique_vals_str += ", ..."

                file_desc.append(f"  {field}: {unique_vals_str}")

        formatted_info.append("\n".join(file_desc))

    return "\n\n".join(formatted_info)


def extract_key_terms(query: str) -> List[str]:
    """
    Extract potential key terms from a query.

    Args:
        query (str): The user query

    Returns:
        List[str]: List of potential key terms
    """
    # Simple extraction of potential key terms
    # This could be enhanced with NLP techniques
    words = query.lower().split()

    # Filter out common words and keep words longer than 3 characters
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
    }
    key_terms = [word for word in words if word not in stop_words and len(word) > 3]

    return key_terms


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

    # Extract key terms from the query
    key_terms = extract_key_terms(query)

    # Search for key terms in the JSON files
    value_matches = search_for_values(json_info, key_terms)

    # Add value matches to the formatted info
    formatted_info = format_json_info_for_prompt(json_info)

    # Add value match information to the prompt
    value_match_info = ""
    if value_matches:
        value_match_info = "\nValue matches found:\n"
        for file_name, field_matches in value_matches.items():
            value_match_info += f"File: {file_name}\n"
            for field, matches in field_matches.items():
                value_match_info += f"  Field '{field}' contains values matching query terms: {', '.join(matches)}\n"

    # Create prompt template
    prompt = ChatPromptTemplate.from_template(
        """Given the following JSON files and their contents, determine the most appropriate file for the query.

Available JSON files and their contents:
{json_info}

{value_match_info}

Query: {query}

You MUST ONLY select from the JSON files listed above.
Analyze the fields, sample values, and unique values to determine which JSON file would be most relevant for this query.
Pay special attention to any value matches found, as these indicate fields containing values mentioned in the query.

Respond in this exact format:
file: [selected json filename]
reason: [brief explanation of why this file is most appropriate]
matching_fields: [comma-separated list of fields that match the query criteria]

Important: The filename MUST be exactly as shown in the available files list."""
    )

    # Initialize LLM and create chain
    model = OllamaLLM(model="dolphin-mistral")

    try:
        # Execute the chain
        response = model.invoke(
            prompt.format(
                json_info=formatted_info, query=query, value_match_info=value_match_info
            )
        )

        # Parse the response
        response_lines = response.strip().split("\n")
        if len(response_lines) >= 1:
            # Extract file name
            for line in response_lines:
                if line.lower().startswith("file:"):
                    file_name = line.split(":", 1)[1].strip()
                    # Validate that the selected file exists in our json_info
                    if file_name in json_info:
                        result.json_file = file_name
                    else:
                        print(
                            f"Warning: Selected file '{file_name}' not found in available JSON files"
                        )

                # Extract reason
                elif line.lower().startswith("reason:"):
                    result.reason = line.split(":", 1)[1].strip()

                # Extract matching fields
                elif line.lower().startswith("matching_fields:"):
                    fields_str = line.split(":", 1)[1].strip()
                    if fields_str:
                        result.matching_fields = [
                            field.strip() for field in fields_str.split(",")
                        ]

            # Add matching values if we have a selected file and matching fields
            if (
                result.json_file
                and result.matching_fields
                and result.json_file in value_matches
            ):
                result.matching_values = {}
                for field in result.matching_fields:
                    if field in value_matches[result.json_file]:
                        result.matching_values[field] = value_matches[result.json_file][
                            field
                        ]
        else:
            print("Warning: Invalid response format from LLM")

    except Exception as e:
        print(f"Error during JSON selection: {e}")

    return result


def search_for_values(
    json_info: dict, search_terms: List[str]
) -> Dict[str, Dict[str, List[str]]]:
    """
    Search for specific values in the JSON files.

    Args:
        json_info (dict): Dictionary containing JSON file information
        search_terms (List[str]): List of terms to search for

    Returns:
        Dict[str, Dict[str, List[str]]]: Dictionary mapping filenames to fields containing matching values
    """
    results = {}

    # Convert search terms to lowercase for case-insensitive matching
    search_terms_lower = [term.lower() for term in search_terms]

    for file_name, info in json_info.items():
        matching_fields = {}

        for field, unique_values in info["unique_values"].items():
            # Convert values to lowercase for case-insensitive matching
            values_lower = [val.lower() for val in unique_values]

            # Find matches
            matches = []
            for term in search_terms_lower:
                for i, val in enumerate(values_lower):
                    if term in val:
                        # Use the original case for the result
                        matches.append(unique_values[i])

            if matches:
                matching_fields[field] = matches

        if matching_fields:
            results[file_name] = matching_fields

    return results


if __name__ == "__main__":
    query = input("Enter your query: ")
    result = select_json_for_query(query)

    if result.json_file:
        print(f"Selected File: {result.json_file}")
        if result.reason:
            print(f"Reason: {result.reason}")
        if result.matching_fields:
            print(f"Matching Fields: {', '.join(result.matching_fields)}")
        if result.matching_values:
            print("Matching Values:")
            for field, values in result.matching_values.items():
                print(f"  {field}: {', '.join(values)}")
    else:
        print("No matching file found")
