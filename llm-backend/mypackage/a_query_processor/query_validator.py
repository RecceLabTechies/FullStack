#!/usr/bin/env python
"""
Query Validator Module

This module provides functionality to validate user queries before processing them.
It performs pattern-based validation and optional LLM-based validation to determine
if a query is suitable for data analysis.

Key components:
- Pattern-based validation using regular expressions
- Normalization of query text
- LLM-based semantic validation for more complex cases
- Cached validation results to improve performance
"""

import functools
import json
import logging
import re
from typing import List, Optional, Pattern, Protocol, TypedDict, Union

from langchain_core.prompts import ChatPromptTemplate
from mypackage.utils.llm_config import VALIDATOR_MODEL, get_groq_llm

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

logger.debug("query_validator module initialized")

# Cache size for LLM validation responses
VALIDATION_CACHE_SIZE = 100


class InvalidPattern(TypedDict):
    """
    Type definition for invalid query patterns.

    Attributes:
        pattern: Compiled regular expression pattern
        reason: Human-readable explanation of why the pattern is invalid
    """

    pattern: Pattern[str]
    reason: str


# List of patterns that indicate invalid queries
INVALID_PATTERNS: List[InvalidPattern] = [
    {"pattern": re.compile(r"^\s*$"), "reason": "Empty query"},
    {
        "pattern": re.compile(r"^[^a-zA-Z0-9\s]+$"),
        "reason": "Query contains only special characters",
    },
    {
        "pattern": re.compile(r"^(hi|hello|hey|test)[\s!.]*$", re.IGNORECASE),
        "reason": "Greeting or test message",
    },
]

# Keywords that indicate a query is likely related to data analysis
DATA_ANALYSIS_KEYWORDS = [
    "chart",
    "plot",
    "graph",
    "analyze",
    "analysis",
    "report",
    "dashboard",
    "visualization",
    "trend",
    "compare",
    "correlation",
    "data",
    "metric",
    "statistics",
    "forecast",
    "prediction",
    "regression",
    "cluster",
    "segment",
    "distribution",
    "average",
    "mean",
    "median",
    "sum",
    "count",
    "min",
    "max",
    "percentage",
    "proportion",
    "growth",
]


def normalize_query(query: str) -> str:
    """
    Normalize a query by standardizing formatting and punctuation.

    This function:
    1. Trims whitespace
    2. Standardizes internal spacing
    3. Removes trailing punctuation
    4. Adds a question mark to questions if missing

    Args:
        query: The raw user query

    Returns:
        Normalized query string
    """
    logger.debug(f"Normalizing query: '{query}'")

    # Trim whitespace and standardize internal spacing
    normalized = query.strip()
    normalized = re.sub(r"\s+", " ", normalized)

    # Remove trailing punctuation
    normalized = re.sub(r"[,.;:!?]+$", "", normalized)

    # Add question mark to questions if missing
    if re.search(
        r"^(what|how|why|when|where|which|who|can|could|would|is|are|do|does)\b",
        normalized,
        re.IGNORECASE,
    ) and not normalized.endswith("?"):
        normalized += "?"

    logger.debug(f"Normalized query: '{normalized}'")
    return normalized


class ValidationResult(TypedDict):
    """
    Type definition for validation results.

    Attributes:
        is_valid: Boolean indicating if the query is valid
        reason: Optional explanation if the query is invalid
    """

    is_valid: bool
    reason: Optional[str]


class LLMResponse(Protocol):
    """
    Protocol defining the expected interface for LLM response objects.
    """

    content: str


@functools.lru_cache(maxsize=VALIDATION_CACHE_SIZE)
def _cached_llm_validation(query: str, model_name: str) -> ValidationResult:
    """
    Validate a query using an LLM with caching for performance.

    This function sends the query to an LLM to determine if it's a valid
    data analysis request. Results are cached to avoid repeated LLM calls.

    Args:
        query: The normalized query to validate
        model_name: The LLM model to use for validation

    Returns:
        ValidationResult with is_valid flag and optional reason

    Note:
        This is decorated with lru_cache for performance optimization
    """
    logger.debug(
        f"Performing LLM validation for query: '{query}' using model {model_name}"
    )

    # Define the prompt for the LLM
    validation_prompt = ChatPromptTemplate.from_template(
        """You are a data analysis assistant that validates user queries before processing them.
        
        Analyze this query and determine if it makes sense for data analysis:
        
        Query: {query}
        
        A query makes sense if:
        1. It asks for specific information, visualization, or analysis on a dataset
        2. It contains clear intent related to data analysis
        3. It is specific enough to guide what kind of analysis should be performed
        
        A query does NOT make sense if:
        1. It contains gibberish or random characters
        2. It asks for something unrelated to data analysis
        3. It is too vague (EXCEPT FOR REPORT REQUESTS like "generate a report")
        4. It contains contradictory or impossible requests
        
        Respond with JSON:
        {{"is_valid": true/false, "reason": "explanation if invalid"}}"""
    )

    logger.debug(f"Sending query to Groq LLM for validation: '{query}'")
    # Initialize LLM and send request
    model = get_groq_llm(model_name)
    response: Union[str, LLMResponse] = model.invoke(
        validation_prompt.format(query=query)
    )
    logger.debug(f"Received Groq LLM response: '{response}'")

    # Extract content from response
    if hasattr(response, "content"):
        response_text = response.content
    else:
        response_text = str(response)

    # Extract JSON from response
    json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
    if not json_match:
        logger.warning("Could not find JSON in Groq LLM response, assuming valid query")
        return {"is_valid": True, "reason": None}

    json_str = json_match.group(0)
    logger.debug(f"Extracted JSON: {json_str}")

    # Normalize JSON boolean values
    json_str = re.sub(r'(?<!")true(?!")', "true", json_str)
    json_str = re.sub(r'(?<!")false(?!")', "false", json_str)
    logger.debug(f"Normalized JSON: {json_str}")

    # Parse JSON
    try:
        validation_result = json.loads(json_str)
        logger.debug(f"JSON parsed successfully: {validation_result}")
        return validation_result
    except json.JSONDecodeError as e:
        logger.warning(f"JSON decode error: {str(e)}, assuming valid query")
        return {"is_valid": True, "reason": None}


def get_valid_query(query: str, model_name: str = VALIDATOR_MODEL) -> bool:
    """
    Main function to validate if a query is suitable for data analysis.

    This function performs multiple validation checks:
    1. Basic length check
    2. Pattern-based validation using INVALID_PATTERNS
    3. Keyword-based validation using DATA_ANALYSIS_KEYWORDS
    4. LLM-based semantic validation for more complex cases

    Args:
        query: The raw user query
        model_name: The LLM model to use for validation (optional)

    Returns:
        Boolean indicating if the query is valid
    """
    logger.info(f"Validating query: '{query}'")

    # Step 1: Perform length check
    if len(query.strip()) < 2:
        reason = "Query is too short. Please provide a more detailed query."
        logger.warning(f"Query too short: '{query}'")
        return False

    # Step 2: Check against invalid patterns
    for pattern_dict in INVALID_PATTERNS:
        if pattern_dict["pattern"].match(query):
            logger.warning(
                f"Query matches invalid pattern '{pattern_dict['reason']}': '{query}'"
            )
            return False

    # Step 3: Check for data analysis keywords
    normalized_query_lower = query.lower()
    for keyword in DATA_ANALYSIS_KEYWORDS:
        if keyword in normalized_query_lower:
            logger.info(
                f"Query '{query}' is valid (contains data analysis keyword: '{keyword}')"
            )
            return True

    # Step 4: Use LLM for more complex validation
    logger.debug("Query passed preliminary checks, proceeding to Groq LLM validation")

    try:
        # Normalize the query before LLM validation
        normalized_query = normalize_query(query)
        logger.debug(f"Using normalized query for LLM validation: '{normalized_query}'")

        # Get validation result from LLM
        result_dict = _cached_llm_validation(normalized_query, model_name)

        is_valid = result_dict.get("is_valid", True)
        reason = result_dict.get("reason")

        if is_valid:
            logger.info(f"Query '{query}' is valid according to LLM validation")
            return True
        else:
            logger.warning(f"Query '{query}' is invalid according to LLM: {reason}")
            return False

    except Exception as e:
        # If there's an error in the validation process, assume the query is valid
        logger.error(f"Error validating query: {str(e)}", exc_info=True)
        logger.info("Assuming query is valid due to validation error")
        return True


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
    test_query = "generate a chart of monthly sales"
    logger.info(f"Testing query validator with: '{test_query}'")
    result = get_valid_query(test_query)
    logger.info(f"Validation result: {result}")

    # Test with invalid query
    test_invalid = "hello there"
    logger.info(f"Testing with invalid query: '{test_invalid}'")
    result = get_valid_query(test_invalid)
    logger.info(f"Validation result: {result}")
