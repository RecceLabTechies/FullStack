#!/usr/bin/env python
"""
Collection Selector Module

This module provides functionality for selecting the most appropriate database collection
to query based on natural language user input. It employs both rule-based and LLM-based
approaches to understand the query and match it to the most relevant collection.

Key components:
- Collection metadata extraction and analysis
- Field and value matching between query terms and collection content
- LLM-based disambiguation for complex queries
- Scoring algorithm to rank potential collection matches
"""

import logging
from typing import Any, Dict, List, Optional, Protocol, Tuple, TypeAlias, TypedDict

from langchain_core.prompts import ChatPromptTemplate
from mypackage.utils.database import Database
from mypackage.utils.llm_config import COLLECTION_SELECTOR_MODEL, get_groq_llm
from pydantic import BaseModel

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

logger.debug("collection_selector module initialized")

DEFAULT_MODEL_NAME = COLLECTION_SELECTOR_MODEL


class CollectionNotFoundError(Exception):
    """
    Exception raised when no suitable collection is found for a query.

    Attributes:
        query: The user query that couldn't be matched
        available_collections: List of available collections in the database
        message: Explanation of why the collection was not found
    """

    def __init__(
        self,
        message: str,
        query: Optional[str] = None,
        available_collections: Optional[List[str]] = None,
    ):
        self.query = query
        self.available_collections = available_collections
        super().__init__(message)
        logger.error(f"CollectionNotFoundError: {message} for query '{query}'")


class CollectionInfo(TypedDict):
    """
    Type definition for storing collection metadata.

    Attributes:
        type: The type of collection (typically "list" for MongoDB collections)
        count: Approximate number of documents in the collection
        fields: List of field names in the collection
        field_types: Mapping of field names to their data types
        sample_values: Mapping of field names to lists of sample values
        unique_values: Mapping of field names to lists of unique values
    """

    type: str
    count: int
    fields: List[str]
    field_types: Dict[str, str]
    sample_values: Dict[str, List[str]]
    unique_values: Dict[str, List[str]]


class CollectionAnalysisResult(BaseModel):
    """
    Pydantic model representing the result of collection analysis.

    Attributes:
        collection_name: The name of the selected collection (if found)
        query: The original user query
        reason: Explanation of why this collection was selected
        matching_fields: List of fields that matched the query
        matching_values: Dictionary of fields and values that matched the query
        error: Error message if collection selection failed
        alternative_collections: List of other possible collections with scores
    """

    collection_name: Optional[str] = None
    query: str
    reason: Optional[str] = None
    matching_fields: Optional[List[str]] = None
    matching_values: Optional[Dict[str, List[str]]] = None
    error: Optional[str] = None
    alternative_collections: Optional[List[Dict[str, Any]]] = None


class HeaderMatch(TypedDict):
    """
    Type definition for storing matches between query terms and collection field names.

    Attributes:
        score: Numerical score representing match quality
        fields: List of field names that matched
        reason: Explanation of why these fields matched
    """

    score: int
    fields: List[str]
    reason: str


class ValueMatch(TypedDict):
    """
    Type definition for storing matches between query terms and collection values.

    Attributes:
        score: Numerical score representing match quality
        values: Dictionary mapping field names to lists of matching values
        fields: List of field names that contained matching values
        reason: Explanation of why these values matched
    """

    score: int
    values: Dict[str, List[str]]
    fields: List[str]
    reason: str


class MatchDetails(TypedDict):
    """
    Type definition for storing comprehensive match details for a collection.

    Attributes:
        score: Overall match score (weighted combination of header and value scores)
        fields: List of all matching fields
        values: Dictionary of all matching values
        reason: Explanation of the match
        header_score: Score based on field name matches
        value_score: Score based on field value matches
    """

    score: float
    fields: List[str]
    values: Dict[str, List[str]]
    reason: str
    header_score: float
    value_score: float


class AlternativeMatch(TypedDict):
    """
    Type definition for storing information about alternative collection matches.

    Attributes:
        collection: Name of the alternative collection
        score: Match score
        fields: List of fields that matched
        reason: Explanation of why this collection is a potential match
    """

    collection: str
    score: float
    fields: List[str]
    reason: str


class LLMResponse(Protocol):
    """
    Protocol defining the expected structure of responses from language models.
    """

    content: str


# Type aliases for better code readability
ValueMatchDict = Dict[str, List[str]]
CollectionValueMatches = Dict[str, ValueMatchDict]
HeaderMatches: TypeAlias = Dict[str, HeaderMatch]
ValueMatches: TypeAlias = Dict[str, ValueMatch]


class FieldProcessor:
    """
    Utility class for processing different field types and extracting
    sample and unique values in a standardized format.
    """

    @staticmethod
    def process_numerical(stats: Dict) -> Tuple[List[str], List[str]]:
        """
        Process numerical field statistics to extract representative values.

        Args:
            stats: Dictionary containing numerical field statistics

        Returns:
            Tuple of (sample values, unique values)
        """
        min_val = stats.get("min", "")
        max_val = stats.get("max", "")
        return [str(min_val), str(max_val)], [str(min_val), str(max_val)]

    @staticmethod
    def process_datetime(stats: Dict) -> Tuple[List[str], List[str]]:
        """
        Process datetime field statistics to extract representative values.

        Args:
            stats: Dictionary containing datetime field statistics

        Returns:
            Tuple of (sample values, unique values)
        """
        min_val = stats.get("min", "")
        max_val = stats.get("max", "")
        return [str(min_val), str(max_val)], [str(min_val), str(max_val)]

    @staticmethod
    def process_categorical(stats: Dict) -> Tuple[List[str], List[str]]:
        """
        Process categorical field statistics to extract representative values.

        Args:
            stats: Dictionary containing categorical field statistics

        Returns:
            Tuple of (sample values, unique values)
        """
        unique_list = stats.get("unique_values", [])
        clean_list = [v for v in unique_list if v != "..."]
        samples = clean_list[:5] if len(clean_list) > 5 else clean_list
        return samples, clean_list

    @classmethod
    def process_field(cls, field_type: str, stats: Dict) -> Tuple[List[str], List[str]]:
        """
        Process any field type by dispatching to the appropriate method.

        Args:
            field_type: The type of field (numerical, datetime, categorical)
            stats: Dictionary containing field statistics

        Returns:
            Tuple of (sample values, unique values)
        """
        processor = getattr(cls, f"process_{field_type}", None)
        if processor:
            return processor(stats)
        return [], []


def _extract_key_terms(query: str) -> List[str]:
    """
    Extract key terms from a query by removing stop words and short words.

    Args:
        query: User query string

    Returns:
        List of key terms extracted from the query
    """
    logger.debug(f"Extracting key terms from query: '{query}'")

    # Split query into words and convert to lowercase
    words = query.lower().split()

    # Define common stop words to filter out
    stop_words = {
        "a",
        "an",
        "the",
        "in",
        "on",
        "at",
        "for",
        "to",
        "of",
        "and",
        "or",
        "is",
        "are",
        "was",
        "were",
    }

    # Filter out stop words and short words
    key_terms = [word for word in words if word not in stop_words and len(word) > 3]
    logger.debug(f"Extracted {len(key_terms)} key terms: {key_terms}")
    return key_terms


def _extract_collection_info() -> Dict[str, CollectionInfo]:
    """
    Extract schema and sample value information from MongoDB collections.

    This function analyzes all accessible collections in the database and
    extracts metadata including field names, types, and representative values.

    Returns:
        Dictionary mapping collection names to their schema and sample data information

    Note:
        Uses Database.analyze_collections() to get raw collection data
    """
    logger.info("Extracting collection info from MongoDB using analyze_collections")
    collection_info = {}

    # Get raw collection analysis data
    collections_analysis = Database.analyze_collections()
    if not collections_analysis:
        logger.warning("No collections or metadata returned from analyze_collections")
        return collection_info

    # Process each collection
    for collection_name, fields_data in collections_analysis.items():
        logger.debug(f"Processing metadata for collection: {collection_name}")
        col_info = {}

        # Handle empty collections
        if not fields_data:
            logger.debug(f"Collection {collection_name} has no fields or is empty")
            col_info["type"] = "unknown"
            col_info["count"] = 0
            col_info["fields"] = []
            col_info["field_types"] = {}
            col_info["sample_values"] = {}
            col_info["unique_values"] = {}
            collection_info[collection_name] = col_info
            continue

        # Initialize collection info
        col_info["type"] = "list"
        col_info["count"] = 100

        field_list = list(fields_data.keys())
        field_types = {}
        sample_values = {}
        unique_values = {}

        # Process each field in the collection
        field_count = 0
        for field_name, field_info in fields_data.items():
            # Skip MongoDB internal ID field
            if field_name == "_id":
                continue

            field_count += 1
            field_type = field_info.get("type", "unknown")
            field_types[field_name] = field_type

            # Process field based on its type
            stats = field_info.get("stats", {})
            sample_values[field_name], unique_values[field_name] = (
                FieldProcessor.process_field(field_type, stats)
            )

        # Store processed collection info
        col_info["fields"] = field_list
        col_info["field_types"] = field_types
        col_info["sample_values"] = sample_values
        col_info["unique_values"] = unique_values

        logger.debug(f"Processed {field_count} fields in collection {collection_name}")
        collection_info[collection_name] = col_info

    logger.info(f"Extracted metadata for {len(collection_info)} collections")
    return collection_info


def _match_headers_to_query(
    collection_info: Dict[str, CollectionInfo], query: str
) -> Tuple[Dict[str, HeaderMatch], Optional[str], List[str]]:
    """
    Match collection field names to a query to find the most relevant collection.

    This function analyzes the query and compares key terms to field names in each collection
    to determine which collection is most likely to contain the relevant data.

    Args:
        collection_info: Dictionary of collection information
        query: User query string

    Returns:
        Tuple containing:
        - Dictionary of all collection matches with scores
        - Name of the best matching collection (or None if no match)
        - List of matching fields in the best matching collection
    """
    logger.info(f"Matching field names to query: '{query}'")

    # Extract key terms from the query
    query_terms = _extract_key_terms(query)

    best_match = None
    best_match_fields = []
    best_match_score = 0
    all_matches = {}

    # Process each collection
    for collection_name, info in collection_info.items():
        logger.debug(f"Checking collection '{collection_name}' for field name matches")

        if "fields" not in info or not info["fields"]:
            logger.warning(f"No fields found in collection: {collection_name}")
            continue

        matched_fields = []
        match_score = 0
        match_reasons = []

        # Check each field name for matches with query terms
        for field in info["fields"]:
            if field == "_id":
                continue

            field_lower = field.lower()

            # Check for direct field name matches in query terms
            for term in query_terms:
                if term in field_lower or field_lower in term:
                    matched_fields.append(field)
                    match_score += 1
                    match_reasons.append(f"Term '{term}' matches field '{field}'")
                    logger.debug(f"Match found: term '{term}' -> field '{field}'")
                    break

        # Record match details if any fields matched
        if matched_fields:
            match_reason = "; ".join(match_reasons)
            all_matches[collection_name] = {
                "score": match_score,
                "fields": matched_fields,
                "reason": match_reason,
            }

            # Update best match if this collection has a higher score
            if match_score > best_match_score:
                best_match = collection_name
                best_match_fields = matched_fields
                best_match_score = match_score
                logger.debug(
                    f"New best match: '{collection_name}' with score {match_score}"
                )

    if best_match:
        logger.info(f"Best header match: '{best_match}' with score {best_match_score}")
    else:
        logger.info("No field name matches found in any collection")

    return all_matches, best_match, best_match_fields


def _match_values_to_query(
    collection_info: Dict[str, CollectionInfo], query: str
) -> Tuple[Dict[str, ValueMatch], Optional[str], Dict[str, List[str]]]:
    """
    Match collection values to a query and score matches in a single flow.
    Returns tuple containing (all matches with scores, best collection, best values)
    """
    logger.info(f"Matching values to query: '{query}'")
    key_terms = _extract_key_terms(query)
    search_terms_lower = [term.lower() for term in key_terms]

    all_matches = {}
    best_match = None
    best_match_values = {}
    best_match_score = 0

    # Single pass through collections and fields
    for collection_name, info in collection_info.items():
        if "unique_values" not in info:
            logger.warning(f"No unique values in collection: {collection_name}")
            continue

        field_matches = {}
        field_reasons = []

        # Process each field's unique values
        for field, values in info["unique_values"].items():
            matches = [
                val
                for val in values
                if any(term in val.lower() for term in search_terms_lower)
            ]

            if matches:
                field_matches[field] = matches
                field_reasons.append(f"'{field}' contains: {', '.join(matches[:3])}")

        if field_matches:
            # Calculate match score and build result in same step
            match_score = sum(len(v) for v in field_matches.values())
            reason = f"Values match query terms: {'; '.join(field_reasons)}"

            all_matches[collection_name] = ValueMatch(
                score=match_score,
                values=field_matches,
                fields=list(field_matches.keys()),
                reason=reason,
            )

            # Track best match
            if match_score > best_match_score:
                best_match = collection_name
                best_match_values = field_matches
                best_match_score = match_score

    if best_match:
        logger.info(f"Best value match: {best_match} (score: {best_match_score})")
    else:
        logger.info("No value matches found")

    return all_matches, best_match, best_match_values


def _compare_matches(
    header_matches: HeaderMatches,
    value_matches: ValueMatches,
) -> Tuple[Optional[str], MatchDetails, List[AlternativeMatch]]:
    logger.info("Comparing field name and value matches")
    all_collections = set(list(header_matches.keys()) + list(value_matches.keys()))
    combined_scores = {}

    for collection_name in all_collections:
        header_score = header_matches.get(collection_name, {}).get("score", 0)
        value_score = value_matches.get(collection_name, {}).get("score", 0)
        combined_score = header_score * 1.2 + value_score

        header_fields = header_matches.get(collection_name, {}).get("fields", [])
        value_fields = value_matches.get(collection_name, {}).get("fields", [])
        all_fields = list(set(header_fields + value_fields))
        values = value_matches.get(collection_name, {}).get("values", {})

        reasons = []
        if collection_name in header_matches:
            reasons.append(header_matches[collection_name]["reason"])
        if collection_name in value_matches:
            reasons.append(value_matches[collection_name]["reason"])

        combined_reason = " ".join(reasons)
        combined_scores[collection_name] = {
            "score": combined_score,
            "fields": all_fields,
            "values": values,
            "reason": combined_reason,
            "header_score": header_score,
            "value_score": value_score,
        }
        logger.debug(
            f"Collection {collection_name} combined score: {combined_score} (header: {header_score}, value: {value_score})"
        )

    best_match = None
    best_match_details = {}
    best_score = 0

    for collection_name, details in combined_scores.items():
        if details["score"] > best_score:
            best_match = collection_name
            best_match_details = details
            best_score = details["score"]

    alternative_matches = []
    if best_match and best_score > 0:
        threshold = best_score * 0.7
        for collection_name, details in combined_scores.items():
            if collection_name != best_match and details["score"] >= threshold:
                alternative_matches.append(
                    {
                        "collection": collection_name,
                        "score": details["score"],
                        "fields": details["fields"],
                        "reason": details["reason"],
                    }
                )
                logger.debug(
                    f"Alternative match: {collection_name} with score {details['score']}"
                )

    if best_match:
        logger.info(f"Best overall match: {best_match} with score {best_score}")
        logger.info(f"Found {len(alternative_matches)} alternative matches")
    else:
        logger.warning("No matches found")

    return best_match, best_match_details, alternative_matches


def _format_collection_info_for_prompt(
    collection_info: Dict[str, CollectionInfo],
) -> str:
    """
    Format collection information for use in an LLM prompt.

    Args:
        collection_info: Dictionary of collection information

    Returns:
        Formatted string with collection details for the prompt
    """
    logger.debug("Formatting collection info for LLM prompt")
    if not collection_info:
        logger.warning("No collections available for formatting")
        return "📭 No collections available for analysis."

    formatted_info = []
    for collection_name, info in collection_info.items():
        if (
            "fields" not in info
            or "sample_values" not in info
            or "unique_values" not in info
        ):
            logger.warning(
                f"Incomplete info for collection {collection_name}, skipping"
            )
            continue

        col_desc = [f"📄 Collection: {collection_name}"]
        col_desc.append("🔑 Fields: " + ", ".join(info["fields"]))
        samples = []

        for field in info["fields"]:
            if field in info["sample_values"] and info["sample_values"][field]:
                samples.append(
                    f"{field} examples: {', '.join(map(str, info['sample_values'][field]))}"
                )

        col_desc.append("📊 Sample values:")
        col_desc.extend([f"  ▫️ {sample}" for sample in samples])
        col_desc.append("🔍 Unique values by field:")

        for field in info["fields"]:
            if field in info["unique_values"] and info["unique_values"][field]:
                unique_vals = info["unique_values"][field]
                display_vals = unique_vals[:10]
                has_more = len(unique_vals) > 10
                unique_vals_str = ", ".join(map(str, display_vals))
                if has_more:
                    unique_vals_str += ", ..."
                col_desc.append(f"  ▫️ {field}: {unique_vals_str}")

        formatted_info.append("\n".join(col_desc))

    logger.debug(f"Formatted info for {len(formatted_info)} collections")
    return "\n\n".join(formatted_info)


def _resolve_ambiguous_matches(
    query: str,
    collection_info: Dict[str, CollectionInfo],
    best_match: str,
    best_match_details: MatchDetails,
    alternative_matches: List[AlternativeMatch],
) -> Tuple[str, str, List[str]]:
    logger.info(f"Resolving ambiguous matches for query: '{query}'")
    logger.debug(f"Best match: {best_match}, alternatives: {len(alternative_matches)}")

    best_match_info = f"Collection: {best_match}\nScore: {best_match_details['score']:.2f}\nMatching fields: {', '.join(best_match_details['fields'])}\nReason: {best_match_details['reason']}"
    alternatives_info = []

    for alt in alternative_matches:
        alt_info = f"Collection: {alt['collection']}\nScore: {alt['score']:.2f}\nMatching fields: {', '.join(alt['fields'])}\nReason: {alt['reason']}"
        alternatives_info.append(alt_info)

    alternatives_text = "\n\n".join(alternatives_info)
    prompt = ChatPromptTemplate.from_template(
        """I need to determine which MongoDB collection is most appropriate for a user query when multiple collections match.

User Query: {query}

Current best match:
{best_match_info}

Alternative matches:
{alternatives_info}

Based on the query and the information about each collection, determine which collection would be most appropriate.
Consider:
1. Which collection's fields and values are most relevant to the query's intent
2. Which collection would provide the most useful information for answering the query
3. The semantic meaning of the query and how it relates to each collection's content

Respond in this exact format:
collection: [selected collection name]
reason: [brief explanation of why this collection is most appropriate]
matching_fields: [comma-separated list of fields that match the query criteria]

Important: The collection name MUST be exactly as shown in the available collections list."""
    )

    model = get_groq_llm(DEFAULT_MODEL_NAME)
    try:
        logger.debug("Invoking Groq LLM to resolve ambiguous matches")
        response = model.invoke(
            prompt.format(
                query=query,
                best_match_info=best_match_info,
                alternatives_info=alternatives_text,
            )
        )
        logger.debug(f"Groq LLM response: {response}")

        selected_collection = best_match
        reason = best_match_details["reason"]
        matching_fields = best_match_details["fields"]

        if hasattr(response, "content"):
            response_text = response.content
        else:
            response_text = str(response)

        response_lines = response_text.strip().split("\n")
        if response_lines:
            for line in response_lines:
                if line.lower().startswith("collection:"):
                    collection_name = line.split(":", 1)[1].strip()
                    if collection_name in collection_info:
                        selected_collection = collection_name
                elif line.lower().startswith("reason:"):
                    reason = line.split(":", 1)[1].strip()
                elif line.lower().startswith("matching_fields:"):
                    fields_str = line.split(":", 1)[1].strip()
                    if fields_str and fields_str.lower() != "none":
                        matching_fields = [
                            field.strip() for field in fields_str.split(",")
                        ]

        logger.info(f"Selected collection: {selected_collection}")
        return selected_collection, reason, matching_fields

    except Exception as e:
        logger.error(f"Error resolving ambiguous matches: {str(e)}", exc_info=True)
        return best_match, best_match_details["reason"], best_match_details["fields"]


def _select_collection_with_llm(
    collection_info: Dict[str, CollectionInfo],
    query: str,
    value_matches: Dict[str, ValueMatch],
) -> CollectionAnalysisResult:
    logger.info(f"Selecting collection with Groq LLM for query: '{query}'")
    result = CollectionAnalysisResult(query=query)
    formatted_info = _format_collection_info_for_prompt(collection_info)

    value_match_info = ""
    if value_matches:
        value_match_info = "\nValue matches found:\n"
        for collection_name, match in value_matches.items():
            value_match_info += f"Collection: {collection_name}\n"
            for field, matches in match["values"].items():
                value_match_info += (
                    f"  Field '{field}' contains matches: {', '.join(matches)}\n"
                )

    prompt = ChatPromptTemplate.from_template(
        """Given the following MongoDB collections and their contents, determine the most appropriate collection for the query.

        Available MongoDB collections and their contents:
        {collection_info}

        {value_match_info}

        Query: {query}

        You MUST ONLY select from the MongoDB collections listed above.
        Analyze the fields, sample values, and unique values to determine which collection would be most relevant for this query.
        Pay special attention to any value matches found, as these indicate fields containing values mentioned in the query.

        If NO collection is appropriate for this query, respond with "No appropriate collection found" and explain why.

        Respond in this exact format:
        collection: [selected collection name or "NONE" if no appropriate collection]
        reason: [brief explanation of why this collection is most appropriate or why no collection is appropriate]
        matching_fields: [comma-separated list of fields that match the query criteria]

        Important: The collection name MUST be exactly as shown in the available collections list."""
    )

    model = get_groq_llm(DEFAULT_MODEL_NAME)
    try:
        logger.debug("Invoking Groq LLM for collection selection")
        response = model.invoke(
            prompt.format(
                collection_info=formatted_info,
                query=query,
                value_match_info=value_match_info,
            )
        )
        logger.debug(f"Groq LLM response: {response}")

        if hasattr(response, "content"):
            response_text = response.content
        else:
            response_text = str(response)

        response_lines = response_text.strip().split("\n")
        if response_lines:
            for line in response_lines:
                if line.lower().startswith("collection:"):
                    collection_name = line.split(":", 1)[1].strip()
                    if collection_name.lower() == "none":
                        result.error = "No appropriate collection found for this query"
                        logger.info("Groq LLM found no appropriate collection")
                    elif collection_name in collection_info:
                        result.collection_name = collection_name
                        logger.info(f"Groq LLM selected collection: {collection_name}")
                    else:
                        result.error = f"Selected collection '{collection_name}' not found in available collections"
                        logger.warning(
                            f"Groq LLM selected invalid collection: {collection_name}"
                        )
                elif line.lower().startswith("reason:"):
                    result.reason = line.split(":", 1)[1].strip()
                elif line.lower().startswith("matching_fields:"):
                    fields_str = line.split(":", 1)[1].strip()
                    if fields_str and fields_str.lower() != "none":
                        result.matching_fields = [
                            field.strip() for field in fields_str.split(",")
                        ]

            if (
                result.collection_name
                and result.matching_fields
                and result.collection_name in value_matches
            ):
                result.matching_values = {}
                for field in result.matching_fields:
                    if field in value_matches[result.collection_name]:
                        result.matching_values[field] = value_matches[
                            result.collection_name
                        ][field]
        else:
            result.error = "Invalid response format from Groq LLM"
            logger.error("Invalid response format from Groq LLM")

    except Exception as e:
        error_msg = f"Error during collection selection: {str(e)}"
        result.error = error_msg
        logger.error(error_msg, exc_info=True)

    return result


def select_collection_for_query(query: str) -> str:
    logger.info(f"Selecting collection for query: '{query}'")

    if not Database.initialize():
        error_msg = "Failed to connect to MongoDB"
        logger.error(error_msg)
        raise CollectionNotFoundError(
            error_msg,
            query=query,
            available_collections=[],
        )

    collection_info = _extract_collection_info()
    if not collection_info:
        error_msg = "No collections found in MongoDB database"
        logger.error(error_msg)
        raise CollectionNotFoundError(
            error_msg,
            query=query,
            available_collections=[],
        )

    header_matches, best_match_by_header, matching_fields = _match_headers_to_query(
        collection_info, query
    )

    value_match_dict, best_match_by_value, best_match_values = _match_values_to_query(
        collection_info, query
    )

    best_match, best_match_details, alternative_matches = _compare_matches(
        header_matches, value_match_dict
    )

    if best_match and not alternative_matches:
        logger.info(f"Selected collection without ambiguity: {best_match}")
        return best_match

    if best_match and alternative_matches:
        logger.info(
            f"Resolving ambiguity between {len(alternative_matches) + 1} matches"
        )
        selected_collection, reason, matching_fields = _resolve_ambiguous_matches(
            query, collection_info, best_match, best_match_details, alternative_matches
        )
        logger.info(
            f"Selected collection after resolving ambiguity: {selected_collection}"
        )
        return selected_collection

    if not best_match:
        logger.info("No matching collections found, asking Groq LLM to help")
        llm_result = _select_collection_with_llm(
            collection_info, query, value_match_dict
        )
        if llm_result.collection_name:
            logger.info(f"Groq LLM selected collection: {llm_result.collection_name}")
            return llm_result.collection_name

    error_msg = "No matching collection found for this query. The query terms don't match any field names or values in the available collections."
    logger.error(error_msg)
    raise CollectionNotFoundError(
        error_msg,
        query=query,
        available_collections=list(collection_info.keys()),
    )


if __name__ == "__main__":
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)

    test_query = "create a bar chart of monthly sales for linkedin"
    logger.info(f"Testing with query: '{test_query}'")
    try:
        selected_collection = select_collection_for_query(test_query)
        print(f"Selected collection: {selected_collection}")
    except CollectionNotFoundError as e:
        print(f"Error: {str(e)}")
