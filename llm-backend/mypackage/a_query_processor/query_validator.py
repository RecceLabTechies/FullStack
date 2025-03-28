#!/usr/bin/env python
import json
import logging
import re
from typing import Optional

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

    model_config = {"extra": "ignore", "validate_assignment": True}


def _validate_query_with_llm(
    query: str, model_name: str = DEFAULT_MODEL_NAME
) -> QueryValidationResult:
    """
    Validate a query using an LLM to determine if it's well-formed for data analysis.

    Args:
        query: The query string to validate
        model_name: Name of the model to use for validation

    Returns:
        QueryValidationResult object containing validation status and reason if invalid
    """
    logger.info(f"Validating query with LLM: '{query}' using model '{model_name}'")

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

    try:
        logger.debug(f"Sending query to LLM for validation: '{query}'")
        model = OllamaLLM(model=model_name)
        response = model.invoke(validation_prompt.format(query=query))
        logger.debug(f"Received LLM response: '{response}'")

        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if not json_match:
            logger.warning("Could not find JSON in LLM response, assuming valid query")
            return QueryValidationResult(is_valid=True, original_query=query)

        json_str = json_match.group(0)
        logger.debug(f"Extracted JSON: {json_str}")

        json_str = re.sub(r'(?<!")true(?!")', "true", json_str)
        json_str = re.sub(r'(?<!")false(?!")', "false", json_str)
        logger.debug(f"Normalized JSON: {json_str}")

        try:
            result_dict = json.loads(json_str)
            result = QueryValidationResult(
                is_valid=result_dict.get("is_valid", True),
                original_query=query,
                reason=result_dict.get("reason"),
            )
            logger.info(f"Validation result: {result}")
            return result
        except json.JSONDecodeError:
            logger.warning("JSON decode error, assuming valid query")
            return QueryValidationResult(is_valid=True, original_query=query)

    except Exception as e:
        logger.error(f"Error validating query: {str(e)}", exc_info=True)
        raise Exception(f"Error validating query: {str(e)}")


def _check_query_length(query: str) -> Optional[QueryValidationResult]:
    """
    Check if a query is too short to be meaningful.

    Args:
        query: The query string to check

    Returns:
        QueryValidationResult if query is too short, None otherwise
    """
    logger.debug(f"Checking query length for: '{query}'")

    if len(query.strip()) < 2:
        logger.warning(f"Query too short: '{query}'")
        return QueryValidationResult(
            is_valid=False,
            original_query=query,
            reason="Query is too short. Please provide a more detailed query.",
        )
    logger.debug("Query length check passed")
    return None


def _validate_query(
    query: str, model_name: str = DEFAULT_MODEL_NAME
) -> QueryValidationResult:
    """
    Validate a query by checking its length and using an LLM.

    Args:
        query: The query string to validate
        model_name: Name of the model to use for validation

    Returns:
        QueryValidationResult object containing validation status and reason if invalid
    """
    logger.info(f"Starting validation for query: '{query}'")

    length_result = _check_query_length(query)
    if length_result:
        logger.info("Query failed length validation")
        return length_result

    logger.debug("Query passed length check, proceeding to LLM validation")
    return _validate_query_with_llm(query, model_name)


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

    validation_result = _validate_query(query, model_name)

    if validation_result.is_valid:
        logger.info(f"Query '{query}' is valid")
        return True

    logger.warning(f"Query '{query}' is invalid: {validation_result.reason}")
    raise QueryValidationError(
        validation_result.reason or "Invalid query", validation_result.original_query
    )


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
