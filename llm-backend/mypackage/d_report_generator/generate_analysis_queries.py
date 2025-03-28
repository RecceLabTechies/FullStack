#!/usr/bin/env python
import json
import logging
import os
from enum import Enum
from typing import Dict, List

from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM
from pydantic import BaseModel

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.propagate = False

# Add handler if not already added
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

DEFAULT_MODEL_NAME = "qwen2.5"


class QueryType(Enum):
    CHART = "chart"
    DESCRIPTION = "description"


class QueryItem(BaseModel):
    query: str
    query_type: QueryType
    file_name: str


class QueryList(BaseModel):
    queries: List[QueryItem]


def _extract_headers(file_path: str) -> List[str]:
    """
    Extract column headers from a JSON file.

    Args:
        file_path: Path to the JSON file

    Returns:
        List of column headers/keys from the JSON file

    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file isn't valid JSON
    """
    logger.debug(f"Extracting headers from JSON file: {file_path}")
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            headers = list(data.keys())
            logger.debug(f"Extracted {len(headers)} headers from dictionary JSON")
            return headers
        elif isinstance(data, list) and data:
            first_item = data[0]
            if isinstance(first_item, dict):
                headers = list(first_item.keys())
                logger.debug(f"Extracted {len(headers)} headers from list JSON")
                return headers
        logger.warning(f"No headers found in file: {file_path}")
        return []
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(
            f"Error extracting headers from {file_path}: {str(e)}", exc_info=True
        )
        raise e


def _recursive_json_schema_extractor(directory: str) -> Dict[str, List[str]]:
    """
    Recursively extract schema information from all JSON files in a directory.

    Args:
        directory: Path to the directory to scan

    Returns:
        Dictionary mapping file paths to their column headers
    """
    logger.info(f"Recursively extracting JSON schemas from directory: {directory}")
    schemas = {}
    for entry in os.listdir(directory):
        full_path = os.path.join(directory, entry)
        if os.path.isdir(full_path):
            logger.debug(f"Scanning subdirectory: {full_path}")
            schemas.update(_recursive_json_schema_extractor(full_path))
        elif entry.lower().endswith(".json"):
            try:
                headers = _extract_headers(full_path)
                schemas[full_path] = headers
                logger.debug(
                    f"Added schema for {full_path} with {len(headers)} headers"
                )
            except Exception as e:
                logger.warning(f"Failed to process {full_path}: {str(e)}")
    logger.info(f"Found schemas for {len(schemas)} JSON files")
    return schemas


def _format_schemas_for_prompt(schemas: Dict[str, List[str]]) -> str:
    """
    Format JSON schema information for inclusion in an LLM prompt.

    Args:
        schemas: Dictionary mapping file paths to their column headers

    Returns:
        Formatted string representation of the schemas
    """
    logger.debug(f"Formatting {len(schemas)} schemas for prompt")
    formatted_str = ""
    for file_path, headers in schemas.items():
        file_name = os.path.basename(file_path)
        headers_str = ", ".join(headers)
        formatted_str += f"{file_name}: [{headers_str}]\n"
    return formatted_str


template = """
Given the following JSON file headers and a user query, generate comprehensive analytical sub-queries.

Available JSON files and their headers:
{json_headers}

User Query: {query}

Requirements:
1. Generate a diverse set of analytical queries that provide comprehensive insights about the data
2. Focus on:
   - Correlations between numeric columns
   - Distributions of categorical data
   - Trends over time if temporal data exists
   - Summary statistics and key findings
   - Patterns and anomalies in the data
3. Each query must be unique and analyze a different aspect of the data
4. Generate 3 unique queries
5. EVERY query must begin with either "Generate a chart of..." or "Generate a description of..."
6. For each query, specify which JSON file should be used for the analysis
7. Format each query as: "Generate a [chart/description] of [query content] | [JSON file name]"
8. Output ONLY the query text, one per line
9. Do not include any prefixes, labels, or additional text

Example format:
Generate a chart of number of leads over time | customers.json
Generate a chart of age group and their spending | transactions.json
Generate a description of spending over time | purchases.json
"""


prompt = ChatPromptTemplate.from_template(template)
model = OllamaLLM(model=DEFAULT_MODEL_NAME, temperature=0.3)


def _parse_llm_response(response: str) -> QueryList:
    """
    Parse the LLM's response into a structured QueryList.

    Args:
        response: Raw string response from the LLM

    Returns:
        QueryList object containing parsed analytical queries
    """
    logger.debug(f"Parsing LLM response of length {len(response)}")
    lines = [line.strip() for line in response.strip().split("\n") if line.strip()]
    queries = []
    seen_queries = set()

    for line in lines:
        try:
            query_text = line.strip()
            if not query_text:
                continue

            # Parse query to extract type and file name
            parts = query_text.split("|")
            if len(parts) != 2:
                logger.warning(f"Skipping malformed query: {query_text}")
                continue

            query_content = parts[0].strip()
            file_name = parts[1].strip()

            # Determine query type
            if query_content.lower().startswith("generate a chart"):
                query_type = QueryType.CHART
            elif query_content.lower().startswith("generate a description"):
                query_type = QueryType.DESCRIPTION
            else:
                logger.warning(f"Unknown query type in: {query_content}")
                continue

            query_item = QueryItem(
                query=query_content, query_type=query_type, file_name=file_name
            )

            # Ensure uniqueness
            query_key = (query_item.query, query_item.file_name)
            if query_key not in seen_queries:
                queries.append(query_item)
                seen_queries.add(query_key)
                logger.debug(
                    f"Added query: '{query_content}' of type '{query_type}' for file '{file_name}'"
                )
        except Exception as e:
            logger.warning(f"Error parsing line '{line}': {str(e)}")
            continue

    logger.info(f"Parsed {len(queries)} unique queries from LLM response")
    return QueryList(queries=queries)


chain = prompt | model | _parse_llm_response


def generate_analysis_queries(user_query: str) -> QueryList:
    """
    Generate a list of analytical queries based on a user query.

    Args:
        user_query: The original user query

    Returns:
        QueryList object containing generated analytical queries

    Raises:
        ValueError: If query is empty or no JSON schemas are available
    """
    logger.info(f"Generating analysis queries for user query: '{user_query}'")
    if not user_query.strip():
        logger.error("Empty user query")
        raise ValueError("User query cannot be empty")
    json_schemas = _recursive_json_schema_extractor("./Data")
    if not json_schemas:
        logger.error("No JSON schemas available in the data directory")
        raise ValueError("No JSON schemas available in the data directory")

    formatted_headers = _format_schemas_for_prompt(json_schemas)
    logger.debug("Formatted schema headers for prompt")

    try:
        logger.info("Invoking LLM to generate analysis queries")
        result = chain.invoke({"json_headers": formatted_headers, "query": user_query})
        logger.info(f"Generated {len(result.queries)} analysis queries")
        return result
    except Exception as e:
        logger.error(f"Error generating queries: {str(e)}", exc_info=True)
        raise ValueError(f"Error generating queries: {str(e)}")


if __name__ == "__main__":
    user_query = "What is the average spending per customer?"
    result = generate_analysis_queries(user_query)
    for item in result.queries:
        print(f"Query: {item.query}")
        print(f"Type: {item.query_type}")
        print(f"File: {item.file_name}")
        print()
