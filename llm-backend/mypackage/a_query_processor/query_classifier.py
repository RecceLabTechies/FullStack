#!/usr/bin/env python
import logging
from enum import Enum
from typing import Dict, Protocol, Union

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from mypackage.utils.llm_config import CLASSIFIER_MODEL, get_groq_llm

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


class QueryTypeEnum(str, Enum):
    DESCRIPTION = "description"
    REPORT = "report"
    CHART = "chart"
    ERROR = "error"


class QueryType(BaseModel):
    query_type: QueryTypeEnum


class LLMResponse(Protocol):
    content: str


def _extract_query_type_from_response(
    response: Union[str, LLMResponse],
) -> Dict[str, QueryTypeEnum]:
    logger.debug(f"Parsing LLM response: '{response}'")

    if hasattr(response, "content"):
        response_text = response.content
    else:
        response_text = str(response)

    response_text = response_text.lower().strip()

    for query_type in QueryTypeEnum:
        if query_type.value in response_text:
            logger.debug(f"Found classification '{query_type.value}' in response")
            return {"query_type": query_type}

    logger.warning(
        f"Could not find valid classification in response: '{response_text}', defaulting to ERROR"
    )
    return {"query_type": QueryTypeEnum.ERROR}


def _classify_query_with_llm(query: str) -> QueryType:
    logger.info(
        f"Classifying query with Groq LLM: '{query}' using model '{CLASSIFIER_MODEL}'"
    )

    prompt_template = """You are a query classifier for a marketing analytics system working with a dataset that contains:
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

    prompt = ChatPromptTemplate.from_template(prompt_template)

    model = get_groq_llm(CLASSIFIER_MODEL)
    chain = prompt | model | _extract_query_type_from_response

    try:
        logger.debug("Invoking Groq LLM chain for classification")
        classification_result = chain.invoke({"query": query})
        logger.info(f"Groq LLM classification result: {classification_result}")
        return QueryType(**classification_result)
    except Exception as e:
        logger.error(f"Error classifying query with Groq LLM: {str(e)}", exc_info=True)
        raise Exception(f"Error classifying query with Groq LLM: {str(e)}")


def classify_query(user_query: str) -> str:
    logger.info(f"Classifying query: '{user_query}'")

    try:
        classification_result = _classify_query_with_llm(user_query)
        logger.info(
            f"Classified by Groq LLM as: {classification_result.query_type.value}"
        )
        return classification_result.query_type.value
    except Exception as e:
        logger.error(f"Error classifying query: {str(e)}", exc_info=True)
        raise Exception(f"Error classifying query: {str(e)}")


if __name__ == "__main__":
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
