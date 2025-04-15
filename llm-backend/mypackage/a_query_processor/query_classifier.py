#!/usr/bin/env python
"""
Query Classification Module

This module provides functionality to classify user queries into predefined types
using an LLM-based classification approach. It determines whether a query is asking
for a description, report, chart, or is invalid.

It now enhances classification accuracy by using vector similarity search to find
similar previously classified queries.
"""

import logging
from enum import Enum
from typing import Dict, List, Protocol, Union

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from mypackage.utils.example_vectorizer import ExampleVectorizer
from mypackage.utils.llm_config import CLASSIFIER_MODEL, get_groq_llm

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

logger.debug("query_classifier module initialized")


class QueryTypeEnum(str, Enum):
    """
    Enumeration of possible query types that can be classified.
    """

    DESCRIPTION = "description"
    REPORT = "report"
    CHART = "chart"
    ERROR = "error"


class QueryType(BaseModel):
    """
    Pydantic model representing the classification result.
    """

    query_type: QueryTypeEnum


class LLMResponse(Protocol):
    """
    Protocol defining the expected structure of responses from language models.
    """

    content: str


def _extract_query_type_from_response(
    response: Union[str, LLMResponse],
) -> Dict[str, QueryTypeEnum]:
    """
    Parse LLM response to extract the query type classification.

    Args:
        response: The raw response from the LLM, either as a string or object with content attribute

    Returns:
        Dictionary containing the classified query type
    """
    logger.debug(f"Parsing LLM response: '{response}'")

    if hasattr(response, "content"):
        response_text = response.content
    else:
        response_text = str(response)

    response_text = response_text.lower().strip()
    logger.debug(f"Normalized response text: '{response_text}'")

    for query_type in QueryTypeEnum:
        if query_type.value in response_text:
            logger.debug(f"Found classification '{query_type.value}' in response")
            return {"query_type": query_type}

    logger.warning(
        f"Could not find valid classification in response: '{response_text}', defaulting to ERROR"
    )
    return {"query_type": QueryTypeEnum.ERROR}


def _get_similar_classified_queries(query: str, n_results: int = 5) -> List[Dict]:
    """
    Retrieve similar classified queries from the vectorized example database.

    Args:
        query: The user's query to find similar examples for
        n_results: Number of examples to return

    Returns:
        List of dictionaries containing similar queries and their classifications
    """
    logger.info(f"Finding similar classified queries for: '{query}'")

    examples = ExampleVectorizer.get_similar_examples(
        function_name="query_classifier", query=query, n_results=n_results
    )

    if not examples:
        logger.warning("No similar classified queries found")
        return []

    similar_queries = []
    for example in examples:
        if (
            "query" in example
            and "result" in example
            and "query_type" in example["result"]
        ):
            similarity_score = example.get("distance", 1.0)
            # Lower distance means more similar (convert to similarity percentage)
            similarity = round((1 - min(similarity_score, 0.99)) * 100)

            similar_queries.append(
                {
                    "query": example["query"],
                    "classification": example["result"]["query_type"],
                    "similarity": similarity,
                }
            )

    logger.info(f"Found {len(similar_queries)} similar classified queries")
    return similar_queries


def _classify_query_with_llm(query: str) -> QueryType:
    """
    Use the Groq LLM to classify the user query.

    Args:
        query: The user's raw query text

    Returns:
        QueryType object with the classification result

    Raises:
        Exception: If there is an error in the LLM classification process
    """
    logger.info(
        f"Classifying query with Groq LLM: '{query}' using model '{CLASSIFIER_MODEL}'"
    )

    # Retrieve similar examples using vector embeddings
    similar_queries = _get_similar_classified_queries(query)

    # Check for very similar queries (>90% similarity) for fast path
    for similar in similar_queries:
        if similar["similarity"] > 90:
            logger.info(
                f"Found highly similar query with {similar['similarity']}% similarity, using existing classification: {similar['classification']}"
            )
            return QueryType(query_type=QueryTypeEnum(similar["classification"]))

    # Format similar queries for prompt inclusion
    similar_examples = ""
    if similar_queries:
        similar_examples = "### Similar queries and their classifications:\n\n"
        for similar in similar_queries:
            similar_examples += f"Query: {similar['query']}\n"
            similar_examples += f"Classification: {similar['classification']}\n"
            similar_examples += f"Similarity: {similar['similarity']}%\n\n"

    prompt_template = """You are a query classifier for a marketing analytics system working with a dataset that contains:
date, campaign_id, channel, age_group, ad_spend, views, leads, new_accounts, country, revenue

Your task is to classify user queries into exactly one of these categories:
- description: Queries asking for specific details, explanations, or summaries about particular aspects of the data
- report: Queries requesting comprehensive analysis across multiple datasets
- chart: Queries specifically requesting visual representation or graphs of data
- error: For ambiguous, unclear queries

{similar_examples}

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

    # Creating the prompt and model chain
    logger.debug("Preparing prompt template for LLM classification")
    prompt = ChatPromptTemplate.from_template(prompt_template)

    logger.debug(f"Initializing Groq LLM with model: {CLASSIFIER_MODEL}")
    model = get_groq_llm(CLASSIFIER_MODEL)
    chain = prompt | model | _extract_query_type_from_response

    try:
        logger.debug("Invoking Groq LLM chain for classification")
        classification_result = chain.invoke(
            {"query": query, "similar_examples": similar_examples}
        )
        logger.info(f"Groq LLM classification result: {classification_result}")
        return QueryType(**classification_result)
    except Exception as e:
        logger.error(f"Error classifying query with Groq LLM: {str(e)}", exc_info=True)
        raise Exception(f"Error classifying query with Groq LLM: {str(e)}")


def classify_query(user_query: str) -> str:
    """
    Public function to classify a user query into one of the predefined types.
    Now uses vector similarity search to enhance classification accuracy.

    Args:
        user_query: The raw query text from the user

    Returns:
        String representation of the query type (description, report, chart, or error)

    Raises:
        Exception: If there is an error in the classification process
    """
    logger.info(f"Classifying query: '{user_query}'")

    try:
        # Track start of classification process
        logger.debug("Starting LLM classification process")
        classification_result = _classify_query_with_llm(user_query)
        logger.info(
            f"Classified by Groq LLM as: {classification_result.query_type.value}"
        )
        return classification_result.query_type.value
    except Exception as e:
        logger.error(f"Error classifying query: {str(e)}", exc_info=True)
        raise Exception(f"Error classifying query: {str(e)}")


if __name__ == "__main__":
    # Additional logging configuration for direct script execution
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)

    test_query = "generate a report of apple over time"
    logger.info(f"Testing with query: '{test_query}'")
    print(classify_query(test_query))
