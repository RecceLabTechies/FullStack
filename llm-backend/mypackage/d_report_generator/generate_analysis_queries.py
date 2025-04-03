#!/usr/bin/env python
import logging
from enum import Enum
from typing import Dict, List

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from mypackage.utils.database import Database, is_collection_accessible
from mypackage.utils.llm_config import ANALYSIS_QUERIES_MODEL, get_groq_llm

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

DEFAULT_MODEL_NAME = ANALYSIS_QUERIES_MODEL


class QueryType(Enum):
    CHART = "chart"
    DESCRIPTION = "description"


class QueryItem(BaseModel):
    query: str
    query_type: QueryType
    collection_name: str


class QueryList(BaseModel):
    queries: List[QueryItem]


def _analyze_collections() -> Dict[str, Dict[str, Dict]]:
    logger.info("Analyzing MongoDB collections")
    try:
        if Database.db is None:
            Database.initialize()

        collection_info = Database.analyze_collections()
        logger.info(f"Successfully analyzed {len(collection_info)} collections")
        return collection_info
    except Exception as e:
        logger.error(f"Error analyzing collections: {str(e)}", exc_info=True)
        raise


def _format_collections_for_prompt(collections_info: Dict[str, Dict[str, Dict]]) -> str:
    logger.debug(f"Formatting {len(collections_info)} collections for prompt")
    formatted_str = ""
    for collection_name, fields in collections_info.items():
        field_info = []
        for field_name, info in fields.items():
            if field_name == "_id":
                continue
            field_type = info.get("type", "unknown")
            stats = info.get("stats", {})

            if field_type == "numerical":
                field_info.append(
                    f"{field_name} ({field_type}, range: {stats.get('min')} to {stats.get('max')})"
                )
            elif field_type == "datetime":
                field_info.append(
                    f"{field_name} ({field_type}, range: {stats.get('min')} to {stats.get('max')})"
                )
            elif field_type == "categorical":
                unique_values = stats.get("unique_values", [])
                if len(unique_values) > 5:
                    unique_values = unique_values[:5] + ["..."]
                field_info.append(
                    f"{field_name} ({field_type}, values: {', '.join(map(str, unique_values))})"
                )
            else:
                field_info.append(f"{field_name} ({field_type})")

        formatted_str += f"{collection_name}: [{', '.join(field_info)}]\n"
    return formatted_str


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
    if hasattr(response, "content"):
        response_text = response.content
    else:
        response_text = str(response)

    logger.debug(f"Parsing Groq LLM response of length {len(response_text)}")

    lines = [line.strip() for line in response_text.strip().split("\n") if line.strip()]

    lines = [
        line
        for line in lines
        if line.startswith(("Generate a chart of", "Generate a description of"))
    ]

    queries = []
    seen_queries = set()

    for line in lines:
        try:
            query_text = line.strip()
            if not query_text:
                continue

            parts = query_text.split("|")
            if len(parts) != 2:
                logger.warning(f"Query missing | separator: {query_text}")
                continue

            query_content = parts[0].strip()
            collection_name = parts[1].strip()

            if not is_collection_accessible(collection_name):
                logger.warning(
                    f"Skipping query for inaccessible collection: {collection_name}"
                )
                continue

            if query_content.lower().startswith("generate a chart"):
                query_type = QueryType.CHART
            elif query_content.lower().startswith("generate a description"):
                query_type = QueryType.DESCRIPTION
            else:
                logger.warning(f"Unknown query type in: {query_content}")
                continue

            query_item = QueryItem(
                query=query_content,
                query_type=query_type,
                collection_name=collection_name,
            )

            query_key = (query_item.query, query_item.collection_name)
            if query_key not in seen_queries:
                queries.append(query_item)
                seen_queries.add(query_key)
                logger.debug(
                    f"Added query: '{query_content}' of type '{query_type}' for collection '{collection_name}'"
                )
        except Exception as e:
            logger.warning(f"Error parsing line '{line}': {str(e)}")
            continue

    logger.info(f"Parsed {len(queries)} unique queries from Groq LLM response")
    return QueryList(queries=queries)


def generate_analysis_queries(user_query: str) -> QueryList:
    logger.info(f"Generating analysis queries for user query: '{user_query}'")
    if not user_query.strip():
        logger.error("Empty user query")
        raise ValueError("User query cannot be empty")

    try:
        collections_info = _analyze_collections()
        if not collections_info:
            logger.error("No accessible collections available in the database")
            raise ValueError("No accessible collections available in the database")

        formatted_collections = _format_collections_for_prompt(collections_info)
        logger.debug("Formatted collection information for prompt")

        model = get_groq_llm(DEFAULT_MODEL_NAME)
        chain = prompt | model | _parse_llm_response
        logger.info("Invoking Groq LLM to generate analysis queries")
        result = chain.invoke(
            {"collections_info": formatted_collections, "query": user_query}
        )
        logger.info(f"Generated {len(result.queries)} analysis queries")
        return result
    except Exception as e:
        logger.error(f"Error generating queries: {str(e)}", exc_info=True)
        raise ValueError(f"Error generating queries: {str(e)}")


if __name__ == "__main__":
    if not Database.initialize():
        logger.error("Failed to initialize database connection")
        exit(1)

    user_query = "What is the performance of our marketing campaigns?"
    try:
        result = generate_analysis_queries(user_query)
        for item in result.queries:
            print(f"Query: {item.query}")
            print(f"Type: {item.query_type}")
            print(f"Collection: {item.collection_name}")
            print()
    except Exception as e:
        logger.error(f"Error in test: {str(e)}")
