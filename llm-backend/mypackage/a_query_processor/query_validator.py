#!/usr/bin/env python
import functools
import json
import logging
import re
from typing import List, Optional, Pattern, Protocol, TypedDict, Union

from langchain_core.prompts import ChatPromptTemplate

from mypackage.utils.llm_config import VALIDATOR_MODEL, get_groq_llm

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


VALIDATION_CACHE_SIZE = 100


class InvalidPattern(TypedDict):
    pattern: Pattern[str]
    reason: str


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
    normalized = query.strip()
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = re.sub(r"[,.;:!?]+$", "", normalized)

    if re.search(
        r"^(what|how|why|when|where|which|who|can|could|would|is|are|do|does)\b",
        normalized,
        re.IGNORECASE,
    ) and not normalized.endswith("?"):
        normalized += "?"

    return normalized


class ValidationResult(TypedDict):
    is_valid: bool
    reason: Optional[str]


class LLMResponse(Protocol):
    content: str


@functools.lru_cache(maxsize=VALIDATION_CACHE_SIZE)
def _cached_llm_validation(query: str, model_name: str) -> ValidationResult:
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
    response: Union[str, LLMResponse] = model.invoke(
        validation_prompt.format(query=query)
    )
    logger.debug(f"Received Groq LLM response: '{response}'")

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


def get_valid_query(query: str, model_name: str = VALIDATOR_MODEL) -> bool:
    logger.info(f"Validating query: '{query}'")

    if len(query.strip()) < 2:
        reason = "Query is too short. Please provide a more detailed query."
        logger.warning(f"Query too short: '{query}'")
        return False

    for pattern_dict in INVALID_PATTERNS:
        if pattern_dict["pattern"].match(query):
            logger.warning(f"Query matches invalid pattern: '{query}'")
            return False

    normalized_query_lower = query.lower()
    for keyword in DATA_ANALYSIS_KEYWORDS:
        if keyword in normalized_query_lower:
            logger.info(f"Query '{query}' is valid (contains data analysis keyword)")
            return True

    logger.debug("Query passed preliminary checks, proceeding to Groq LLM validation")

    try:
        normalized_query = normalize_query(query)
        result_dict = _cached_llm_validation(normalized_query, model_name)

        is_valid = result_dict.get("is_valid", True)
        reason = result_dict.get("reason")

        if is_valid:
            logger.info(f"Query '{query}' is valid")
            return True
        else:
            logger.warning(f"Query '{query}' is invalid: {reason}")
            return False

    except Exception as e:
        logger.error(f"Error validating query: {str(e)}", exc_info=True)
        return True


if __name__ == "__main__":
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
