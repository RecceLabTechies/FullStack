#!/usr/bin/env python
import logging
from enum import Enum
from typing import Dict, Set

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from mypackage.utils.llm_config import get_groq_llm, CLASSIFIER_MODEL

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

DEFAULT_MODEL_NAME = CLASSIFIER_MODEL


class QueryTypeEnum(str, Enum):
    DESCRIPTION = "description"
    REPORT = "report"
    CHART = "chart"
    ERROR = "error"


class QueryType(BaseModel):
    query_type: QueryTypeEnum


def _count_keyword_matches(query: str) -> Dict[QueryTypeEnum, int]:
    """
    Count the number of keyword matches for each query type in the query string.

    Args:
        query: User's query string

    Returns:
        Dictionary mapping query types to their match counts
    """
    logger.debug(f"Counting keyword matches for query: '{query}'")

    _chart_keywords: Set[str] = {
        "chart",
        "plot",
        "graph",
        "visualize",
        "visualization",
        "bar chart",
        "line chart",
        "pie chart",
        "scatter plot",
        "histogram",
        "show me",
    }

    _description_keywords: Set[str] = {
        "describe",
        "description",
        "explain",
        "summarize",
        "details about",
        "tell me about",
        "what is",
        "how is",
        "why is",
        "details of",
    }

    _report_keywords: Set[str] = {
        "report",
        "comprehensive",
        "complete",
        "full",
        "overview",
        "analysis",
        "analyze",
        "breakdown",
        "summary",
        "summarize all",
    }

    query_lower = query.lower()
    matches = {
        QueryTypeEnum.CHART: sum(1 for word in _chart_keywords if word in query_lower),
        QueryTypeEnum.DESCRIPTION: sum(
            1 for word in _description_keywords if word in query_lower
        ),
        QueryTypeEnum.REPORT: sum(
            1 for word in _report_keywords if word in query_lower
        ),
    }

    logger.debug(f"Keyword match counts: {matches}")
    return matches


def _parse_llm_response(response) -> Dict[str, QueryTypeEnum]:
    """
    Parse the LLM's response into a query type dictionary.

    Args:
        response: Response from the LLM (can be string or AIMessage)

    Returns:
        Dictionary with query_type key mapped to the appropriate QueryTypeEnum
    """
    logger.debug(f"Parsing LLM response: '{response}'")

    # Handle AIMessage objects by extracting content
    if hasattr(response, "content"):
        content = response.content
    else:
        content = str(response)

    query_type = content.strip().lower()
    try:
        result = {"query_type": QueryTypeEnum(query_type)}
        logger.debug(f"Successfully parsed response to {result}")
        return result
    except ValueError:
        logger.warning(
            f"Invalid query type '{query_type}' from LLM, defaulting to ERROR"
        )
        return {"query_type": QueryTypeEnum.ERROR}


def _classify_with_llm(query: str, model_name: str = DEFAULT_MODEL_NAME) -> QueryType:
    """
    Classify the query using the LLM.

    Args:
        query: User's query string
        model_name: Name of the model to use for classification

    Returns:
        QueryType object containing the classified query type

    Raises:
        Exception: If there is an error during classification
    """
    logger.info(
        f"Classifying query with Groq LLM: '{query}' using model '{model_name}'"
    )

    _template = """Classify the following query into one of these categories:
- description: Queries asking for specific details, explanations, or summaries about particular aspects of the data. These often focus on a specific topic, metric, or segment. Examples: "describe the spending on LinkedIn", "generate description of marketing expenses", "explain the revenue trends for Q1", "summarize the customer acquisition costs"        
- report: Queries requesting comprehensive analysis across multiple aspects of the dataset, often requiring a full overview or detailed breakdown of the entire dataset. Examples: "create a full financial report", "generate a comprehensive analysis of all marketing channels", "provide a complete breakdown of all expenses"
- chart: Queries specifically requesting visual representation or graphs of data. Examples: "create a bar chart of monthly sales", "plot the revenue growth over time", "visualize the customer demographics"
- error: For ambiguous, unclear queries. Examples: "plot the invisible unicorn data", "show me a chart of the sound of silence", "generate a report on the taste of numbers"
Query: {query}

Respond with exactly one word: description, report, chart, or error"""

    _prompt = ChatPromptTemplate.from_template(_template)

    model = get_groq_llm(model_name)
    chain = _prompt | model | _parse_llm_response

    try:
        logger.debug("Invoking Groq LLM chain for classification")
        result = chain.invoke({"query": query})
        logger.info(f"Groq LLM classification result: {result}")
        return QueryType(**result)
    except Exception as e:
        logger.error(f"Error classifying query with Groq LLM: {str(e)}", exc_info=True)
        raise Exception(f"Error classifying query with Groq LLM: {str(e)}")


def classify_query(user_query: str, model_name: str = DEFAULT_MODEL_NAME) -> str:
    """
    Classify a user query into one of the predefined types.

    Args:
        user_query: The query string to classify
        model_name: Name of the model to use for classification

    Returns:
        String representation of the query type ("description", "report", "chart", or "error")

    Raises:
        Exception: If there is an error during classification
    """
    logger.info(f"Classifying query: '{user_query}'")

    try:
        matches = _count_keyword_matches(user_query)
        logger.debug(f"Keyword matches: {matches}")

        max_matches = max(matches.values())
        if max_matches > 0:
            max_categories = [
                cat for cat, count in matches.items() if count == max_matches
            ]
            logger.debug(f"Max categories with {max_matches} matches: {max_categories}")

            if len(max_categories) == 1:
                result = max_categories[0].value
                logger.info(f"Classified by keywords as: {result}")
                return result

        logger.debug("No clear keyword match, falling back to Groq LLM classification")
        result = _classify_with_llm(user_query, model_name)
        logger.info(f"Classified by Groq LLM as: {result.query_type.value}")
        return result.query_type.value
    except Exception as e:
        logger.error(f"Error classifying query: {str(e)}", exc_info=True)
        raise Exception(f"Error classifying query: {str(e)}")


if __name__ == "__main__":
    # Set up console logging for script execution
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)

    query = "create an apple"
    logger.info(f"Testing with query: '{query}'")
    print(classify_query(query))
