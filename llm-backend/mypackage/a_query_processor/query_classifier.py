#!/usr/bin/env python
import logging
from enum import Enum
from typing import Dict

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

    content = content.lower().strip()

    # Extract just the classification word using pattern matching
    for query_type in QueryTypeEnum:
        if query_type.value in content:
            logger.debug(f"Found classification '{query_type.value}' in response")
            return {"query_type": query_type}

    logger.warning(
        f"Could not find valid classification in response: '{content}', defaulting to ERROR"
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

    _template = """You are a query classifier for a marketing analytics system working with a dataset that contains:
date, campaign_id, channel, age_group, ad_spend, views, leads, new_accounts, country, revenue

Your task is to classify user queries into exactly one of these categories:
- description: Queries asking for specific details, explanations, or summaries about particular aspects of the data
- report: Queries requesting comprehensive analysis across multiple datasets
- chart: Queries specifically requesting visual representation or graphs of data
- error: For ambiguous, unclear queries

### Few-shot examples:

Query: How much did we spend on Facebook ads last month?
Classification: description

Query: Explain our performance in Singapore compared to Malaysia
Classification: description

Query: Create a full marketing report for all channels in Q2
Classification: report

Query: Generate a comprehensive breakdown of all ad campaigns and their ROI
Classification: report

Query: Show me a bar chart of ad spend by country
Classification: chart

Query: Plot the correlation between ad spend and new accounts
Classification: chart

Query: What is the color of marketing?
Classification: error

Query: Plot the invisible unicorn data
Classification: error

### Now classify this query:
Query: {query}

IMPORTANT: Respond with EXACTLY ONE WORD, which must be one of: description, report, chart, or error
Classification:"""

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
    Classify a user query into one of the predefined types using the Groq LLM.

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

    query = "generate a report of apple over time"
    logger.info(f"Testing with query: '{query}'")
    print(classify_query(query))
