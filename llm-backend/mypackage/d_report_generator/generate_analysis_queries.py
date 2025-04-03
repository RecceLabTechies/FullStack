#!/usr/bin/env python
"""
Analysis Queries Generator

This module provides functionality to break down a complex analysis query into
multiple smaller, focused queries that can be individually processed. It works by:
1. Analyzing available collections in the database
2. Using an LLM to generate structured sub-queries based on the user's request
3. Validating and formatting the generated queries for downstream processing

Key components:
- Collection metadata extraction from MongoDB
- LLM-driven decomposition of complex analytical requests
- Query validation and normalization
- Structured output via Pydantic models
"""

import logging
from enum import Enum
from typing import Dict, List

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from mypackage.utils.database import Database, is_collection_accessible
from mypackage.utils.llm_config import ANALYSIS_QUERIES_MODEL, get_groq_llm

# Set up module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.propagate = False

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

logger.debug("generate_analysis_queries module initialized")

DEFAULT_MODEL_NAME = ANALYSIS_QUERIES_MODEL


class QueryType(Enum):
    """
    Enum defining the types of analyses that can be performed.

    Values:
        CHART: Generates visual representation of data (graphs, plots)
        DESCRIPTION: Generates textual description of data patterns and insights
    """

    CHART = "chart"
    DESCRIPTION = "description"


class QueryItem(BaseModel):
    """
    Pydantic model representing a single analysis query.

    This model encapsulates all information needed to process one sub-query,
    including what type of output to generate and which collection to use.

    Attributes:
        query: The text of the query to be processed
        query_type: The type of query (chart or description)
        collection_name: The database collection to query against
    """

    query: str
    query_type: QueryType
    collection_name: str


class QueryList(BaseModel):
    """
    Pydantic model containing a list of analysis queries.

    This container model holds all the sub-queries generated from a single
    user query and is passed to downstream processing components.

    Attributes:
        queries: List of QueryItem objects to be processed
    """

    queries: List[QueryItem]


def _analyze_collections() -> Dict[str, Dict[str, Dict]]:
    """
    Analyze all accessible collections in the MongoDB database.

    This function extracts metadata about each collection, including field names,
    data types, and statistical properties like min/max values and unique values
    for categorical fields.

    Returns:
        Dictionary mapping collection names to field information with structure:
        {
            "collection_name": {
                "field_name": {
                    "type": "numerical|categorical|datetime|etc",
                    "stats": {
                        "min": minimum value (for numerical/datetime),
                        "max": maximum value (for numerical/datetime),
                        "unique_values": list of values (for categorical)
                    }
                }
            }
        }

    Raises:
        Exception: If there's an error connecting to or analyzing the collections
    """
    logger.info("Analyzing MongoDB collections for query generation")
    try:
        # Initialize database connection if needed
        if Database.db is None:
            logger.debug("Database connection not initialized, initializing now")
            Database.initialize()

        # Get structure and stats for all collections
        logger.debug("Retrieving collection information from database")
        collection_info = Database.analyze_collections()
        logger.info(f"Successfully analyzed {len(collection_info)} collections")

        # Log some details about the collections found
        for coll_name, fields in collection_info.items():
            field_count = len(fields)
            logger.debug(f"Collection '{coll_name}' has {field_count} fields")

        return collection_info
    except Exception as e:
        logger.error(f"Error analyzing collections: {str(e)}", exc_info=True)
        raise


def _format_collections_for_prompt(collections_info: Dict[str, Dict[str, Dict]]) -> str:
    """
    Format collection information into a string suitable for the LLM prompt.

    This function transforms the structured collection metadata into a human-readable
    text format that can be included in the LLM prompt to provide context about
    available data.

    Args:
        collections_info: Dictionary of collection information from _analyze_collections

    Returns:
        Formatted string containing collection and field information, with each
        collection on a new line and fields described with their type and properties
    """
    logger.debug(f"Formatting {len(collections_info)} collections for LLM prompt")
    formatted_str = ""

    # Process each collection
    for collection_name, fields in collections_info.items():
        field_info = []
        logger.debug(f"Formatting fields for collection '{collection_name}'")

        # Process each field in the collection
        for field_name, info in fields.items():
            # Skip MongoDB internal ID field
            if field_name == "_id":
                continue

            field_type = info.get("type", "unknown")
            stats = info.get("stats", {})

            # Format based on field type
            if field_type == "numerical":
                field_desc = f"{field_name} ({field_type}, range: {stats.get('min')} to {stats.get('max')})"
                field_info.append(field_desc)
                logger.debug(f"Added numerical field: {field_desc}")
            elif field_type == "datetime":
                field_desc = f"{field_name} ({field_type}, range: {stats.get('min')} to {stats.get('max')})"
                field_info.append(field_desc)
                logger.debug(f"Added datetime field: {field_desc}")
            elif field_type == "categorical":
                unique_values = stats.get("unique_values", [])
                # Limit the number of displayed values to avoid overly long prompts
                if len(unique_values) > 5:
                    unique_values = unique_values[:5] + ["..."]
                field_desc = f"{field_name} ({field_type}, values: {', '.join(map(str, unique_values))})"
                field_info.append(field_desc)
                logger.debug(f"Added categorical field: {field_desc}")
            else:
                field_desc = f"{field_name} ({field_type})"
                field_info.append(field_desc)
                logger.debug(f"Added generic field: {field_desc}")

        # Add collection with its fields to the formatted string
        formatted_str += f"{collection_name}: [{', '.join(field_info)}]\n"
        logger.debug(
            f"Added collection '{collection_name}' with {len(field_info)} fields"
        )

    logger.debug(
        f"Formatted collection info completed (length: {len(formatted_str)} chars)"
    )
    return formatted_str


# LLM prompt template for generating analysis queries
template = """
Given the following MongoDB collections and their fields, generate comprehensive analytical sub-queries.

Available Collections and their fields:
{collections_info}

User Query: {query}

STRICT FORMAT REQUIREMENTS:
1. Output EXACTLY 3 queries
2. Each query MUST be on its own line
3. Each query MUST use EXACTLY this format:
   Generate a [chart/description] of [query content] | [single_collection_name]
4. Use ONLY ONE collection per query
5. The | symbol MUST separate the query from the collection name
6. DO NOT add any other text, explanations, or formatting
7. DO NOT use phrases like "using collection" - use the | symbol instead

VALID EXAMPLES:
Generate a chart of leads by source | campaign_performance
Generate a description of conversion trends | campaign_performance
Generate a chart of revenue by channel | campaign_performance

INVALID EXAMPLES:
- Here are 3 queries:  <-- NO INTRODUCTORY TEXT
- Generate a chart using campaign_performance  <-- MISSING | SYMBOL
- Generate a chart of performance using collection campaign_performance  <-- WRONG FORMAT
- Generate a chart from multiple collections  <-- ONLY ONE COLLECTION ALLOWED

Your response should contain EXACTLY 3 lines, each following the format:
Generate a [chart/description] of [query content] | [single_collection_name]"""

prompt = ChatPromptTemplate.from_template(template)


def _parse_llm_response(response) -> QueryList:
    """
    Parse the LLM response into structured QueryItem objects.

    This function extracts, validates, and normalizes the queries generated by the LLM,
    ensuring they follow the expected format and reference accessible collections.
    It also deduplicates queries to avoid redundancy.

    Args:
        response: Raw response from the LLM, either as a string or an object with a content attribute

    Returns:
        QueryList containing parsed and validated queries

    Raises:
        ValueError: Implicitly when creating QueryList if validation fails
    """
    # Extract content from response object if needed
    if hasattr(response, "content"):
        response_text = response.content
    else:
        response_text = str(response)

    logger.debug(f"Parsing Groq LLM response of length {len(response_text)}")

    # Split response into lines and filter out empty lines
    lines = [line.strip() for line in response_text.strip().split("\n") if line.strip()]
    logger.debug(f"Found {len(lines)} non-empty lines in LLM response")

    # Filter for valid query patterns
    valid_starters = ("Generate a chart of", "Generate a description of")
    lines = [
        line
        for line in lines
        if any(line.startswith(starter) for starter in valid_starters)
    ]
    logger.debug(f"Found {len(lines)} lines with valid query patterns")

    queries = []
    seen_queries = set()  # Track unique queries to avoid duplicates

    # Process each line in the response
    for i, line in enumerate(lines, 1):
        try:
            query_text = line.strip()
            if not query_text:
                logger.debug(f"Skipping empty line {i}")
                continue

            # Split query by the separator
            parts = query_text.split("|")
            if len(parts) != 2:
                logger.warning(
                    f"Query missing | separator or has multiple separators: {query_text}"
                )
                continue

            query_content = parts[0].strip()
            collection_name = parts[1].strip()

            # Verify the collection exists and is accessible
            if not is_collection_accessible(collection_name):
                logger.warning(
                    f"Skipping query for inaccessible collection: {collection_name}"
                )
                continue

            # Determine query type
            if query_content.lower().startswith("generate a chart"):
                query_type = QueryType.CHART
                logger.debug(f"Line {i} classified as chart query: '{query_content}'")
            elif query_content.lower().startswith("generate a description"):
                query_type = QueryType.DESCRIPTION
                logger.debug(
                    f"Line {i} classified as description query: '{query_content}'"
                )
            else:
                logger.warning(f"Unknown query type in: '{query_content}'")
                continue

            # Create QueryItem
            query_item = QueryItem(
                query=query_content,
                query_type=query_type,
                collection_name=collection_name,
            )

            # Add unique queries only
            query_key = (query_item.query, query_item.collection_name)
            if query_key not in seen_queries:
                queries.append(query_item)
                seen_queries.add(query_key)
                logger.debug(
                    f"Added query: '{query_content}' of type '{query_type}' for collection '{collection_name}'"
                )
            else:
                logger.debug(f"Skipping duplicate query: '{query_content}'")
        except Exception as e:
            logger.warning(f"Error parsing line '{line}': {str(e)}", exc_info=True)
            continue

    logger.info(
        f"Successfully parsed {len(queries)} unique queries from Groq LLM response"
    )
    return QueryList(queries=queries)


def generate_analysis_queries(user_query: str) -> QueryList:
    """
    Main function to generate analysis queries from a user query.

    This function orchestrates the entire query generation process, from analyzing
    database collections to generating and validating sub-queries using an LLM.

    The function aims to decompose a complex user query into multiple simpler queries
    that can be processed independently and then combined to create a comprehensive
    analytical report.

    Args:
        user_query: The original user query for which to generate analysis queries

    Returns:
        QueryList containing the generated and validated queries

    Raises:
        ValueError: If the user query is empty, if there are no accessible collections,
                   or if there's an error in the query generation process
    """
    logger.info(f"Generating analysis queries for user query: '{user_query}'")

    # Validate user input
    if not user_query.strip():
        logger.error("Empty user query")
        raise ValueError("User query cannot be empty")

    try:
        # Step 1: Get collection information
        logger.debug("Getting collection information from database")
        collections_info = _analyze_collections()
        if not collections_info:
            logger.error("No accessible collections available in the database")
            raise ValueError("No accessible collections available in the database")

        # Step 2: Format collection information for the prompt
        logger.debug("Formatting collection information for LLM prompt")
        formatted_collections = _format_collections_for_prompt(collections_info)
        logger.debug(
            f"Formatted collection information for prompt ({len(formatted_collections)} chars)"
        )

        # Step 3: Initialize LLM and prepare chain
        logger.debug(f"Initializing Groq LLM with model: {DEFAULT_MODEL_NAME}")
        model = get_groq_llm(DEFAULT_MODEL_NAME)
        chain = prompt | model | _parse_llm_response

        # Step 4: Generate queries using LLM
        logger.info("Invoking Groq LLM to generate analysis queries")
        result = chain.invoke(
            {"collections_info": formatted_collections, "query": user_query}
        )

        # Log details about the generated queries
        chart_queries = sum(
            1 for q in result.queries if q.query_type == QueryType.CHART
        )
        desc_queries = sum(
            1 for q in result.queries if q.query_type == QueryType.DESCRIPTION
        )
        logger.info(
            f"Generated {len(result.queries)} analysis queries: {chart_queries} charts, {desc_queries} descriptions"
        )

        # Log each generated query for debugging
        for i, query in enumerate(result.queries):
            logger.debug(
                f"Query {i + 1}: '{query.query}' ({query.query_type.value}) on collection '{query.collection_name}'"
            )

        return result
    except Exception as e:
        logger.error(f"Error generating queries: {str(e)}", exc_info=True)
        raise ValueError(f"Error generating queries: {str(e)}")


if __name__ == "__main__":
    # Set up console logging for direct script execution
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Set to DEBUG for more detailed logging
    root_logger.addHandler(console_handler)

    # Test with sample query
    try:
        test_query = "Analyze our marketing campaign performance across different channels and show conversion trends"
        logger.info(f"Testing with query: '{test_query}'")

        query_list = generate_analysis_queries(test_query)
        logger.info(f"Successfully generated {len(query_list.queries)} queries")

        # Print results for inspection
        for i, query in enumerate(query_list.queries):
            logger.info(
                f"Query {i + 1}: {query.query_type.value} | {query.collection_name} | {query.query}"
            )
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
