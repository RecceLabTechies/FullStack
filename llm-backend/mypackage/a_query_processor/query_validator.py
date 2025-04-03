#!/usr/bin/env python
import json
import logging
import re
import functools
from typing import Optional, Dict, List, Pattern

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from mypackage.utils.llm_config import get_groq_llm, VALIDATOR_MODEL

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

DEFAULT_MODEL_NAME = VALIDATOR_MODEL

# LRU Cache for query validation results
VALIDATION_CACHE_SIZE = 100

# Common invalid query patterns
INVALID_PATTERNS: List[Dict[str, Pattern]] = [
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

# Common data analysis keywords to quickly validate relevant queries
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


class QueryValidationError(Exception):
    def __init__(self, message: str, original_query: str):
        self.message = message
        self.original_query = original_query
        super().__init__(self.message)
        logger.error(f"QueryValidationError: {message} for query '{original_query}'")


class QueryValidationResult(BaseModel):
    is_valid: bool
    original_query: str
    reason: Optional[str] = None
    normalized_query: Optional[str] = None

    model_config = {"extra": "ignore", "validate_assignment": True}


def normalize_query(query: str) -> str:
    """
    Normalize a query by removing extra spaces, normalizing whitespace, and
    other basic text normalizations.

    Args:
        query: The query string to normalize

    Returns:
        Normalized query string
    """
    # Remove leading/trailing whitespace
    normalized = query.strip()

    # Normalize internal whitespace (replace multiple spaces with a single space)
    normalized = re.sub(r"\s+", " ", normalized)

    # Remove punctuation at the end of the query if it doesn't serve a purpose
    normalized = re.sub(r"[,.;:!?]+$", "", normalized)

    # Ensure the query ends with proper punctuation if it's a question
    if re.search(
        r"^(what|how|why|when|where|which|who|can|could|would|is|are|do|does)\b",
        normalized,
        re.IGNORECASE,
    ) and not normalized.endswith("?"):
        normalized += "?"

    return normalized


@functools.lru_cache(maxsize=VALIDATION_CACHE_SIZE)
def _cached_llm_validation(query: str, model_name: str) -> dict:
    """
    Cached wrapper for LLM validation to avoid repeated calls for the same query.

    Args:
        query: The normalized query string to validate
        model_name: Name of the model to use for validation

    Returns:
        Dict containing validation result from LLM
    """
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
    model = get_groq_llm(model_name)
    response = model.invoke(validation_prompt.format(query=query))
    logger.debug(f"Received Groq LLM response: '{response}'")

    # Extract content from AIMessage if needed
    if hasattr(response, "content"):
        response_text = response.content
    else:
        response_text = str(response)

    json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
    if not json_match:
        logger.warning("Could not find JSON in Groq LLM response, assuming valid query")
        return {"is_valid": True}

    json_str = json_match.group(0)
    logger.debug(f"Extracted JSON: {json_str}")

    json_str = re.sub(r'(?<!")true(?!")', "true", json_str)
    json_str = re.sub(r'(?<!")false(?!")', "false", json_str)
    logger.debug(f"Normalized JSON: {json_str}")

    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        logger.warning("JSON decode error, assuming valid query")
        return {"is_valid": True}


def get_valid_query(query: str, model_name: str = DEFAULT_MODEL_NAME) -> bool:
    """
    Check if a query is valid for data analysis.

    Args:
        query: The query string to validate
        model_name: Name of the model to use for validation

    Returns:
        True if the query is valid

    Raises:
        QueryValidationError: If the query is invalid
    """
    logger.info(f"Validating query: '{query}'")

    # Check query length first (fastest check)
    if len(query.strip()) < 2:
        reason = "Query is too short. Please provide a more detailed query."
        logger.warning(f"Query too short: '{query}'")
        raise QueryValidationError(reason, query)

    # Check against invalid patterns
    for pattern_dict in INVALID_PATTERNS:
        if pattern_dict["pattern"].match(query):
            reason = (
                f"{pattern_dict['reason']}. Please provide a valid data analysis query."
            )
            logger.warning(f"Query matches invalid pattern: '{query}'")
            raise QueryValidationError(reason, query)

    # Quick approve if it contains data analysis keywords
    normalized_query_lower = query.lower()
    for keyword in DATA_ANALYSIS_KEYWORDS:
        if keyword in normalized_query_lower:
            logger.info(f"Query '{query}' is valid (contains data analysis keyword)")
            return True

    # If we get here, we need LLM validation
    logger.debug("Query passed preliminary checks, proceeding to Groq LLM validation")

    try:
        # Normalize the query before caching to improve cache hit rate
        normalized_query = normalize_query(query)

        # Use cached validation result if available
        result_dict = _cached_llm_validation(normalized_query, model_name)

        is_valid = result_dict.get("is_valid", True)
        reason = result_dict.get("reason")

        if is_valid:
            logger.info(f"Query '{query}' is valid")
            return True
        else:
            logger.warning(f"Query '{query}' is invalid: {reason}")
            raise QueryValidationError(reason or "Invalid query", query)

    except Exception as e:
        logger.error(f"Error validating query: {str(e)}", exc_info=True)
        # Fail open - assume query is valid if there's an error in the validation process
        return True


if __name__ == "__main__":
    # Set up console logging for script execution
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)

    test_query = "generate a chart of monthly sales"
    logger.info(f"Testing with query: '{test_query}'")
    print(get_valid_query(test_query))
