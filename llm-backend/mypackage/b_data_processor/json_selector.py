#!/usr/bin/env python
import logging
from typing import Any, Dict, List, Optional, Tuple

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from mypackage.utils.llm_config import get_groq_llm, JSON_SELECTOR_MODEL
from mypackage.utils.database import Database

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


DEFAULT_MODEL_NAME = JSON_SELECTOR_MODEL


class CollectionNotFoundError(Exception):
    """Exception raised when a requested collection cannot be found or processed.

    This exception provides detailed information about the search attempt,
    including the query, database searched, and reason for failure.
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


class CollectionAnalysisResult(BaseModel):
    collection_name: Optional[str] = None
    query: str
    reason: Optional[str] = None
    matching_fields: Optional[List[str]] = None
    matching_values: Optional[Dict[str, List[str]]] = None
    error: Optional[str] = None
    alternative_collections: Optional[List[Dict[str, Any]]] = None


def _extract_key_terms(query: str) -> List[str]:
    """
    Extract key terms from a query by removing stop words and short words.

    Args:
        query: User query string

    Returns:
        List of key terms extracted from the query
    """
    logger.debug(f"Extracting key terms from query: '{query}'")
    words = query.lower().split()
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
    key_terms = [word for word in words if word not in stop_words and len(word) > 3]
    logger.debug(f"Extracted key terms: {key_terms}")
    return key_terms


def _extract_collection_info() -> Dict[str, Dict[str, Any]]:
    """
    Extract schema and sample value information from MongoDB collections using Database.analyze_collections().

    Returns:
        Dictionary mapping collection names to their schema and sample data information
    """
    logger.info("Extracting collection info from MongoDB using analyze_collections")
    collection_info = {}

    # Initialize the database connection if not already done
    if not Database.initialize():
        logger.error("Failed to connect to MongoDB")
        return collection_info

    # Use the analyze_collections method to get collection metadata
    collections_analysis = Database.analyze_collections()
    if not collections_analysis:
        logger.warning("No collections or metadata returned from analyze_collections")
        return collection_info

    for collection_name, fields_data in collections_analysis.items():
        # Create collection info structure expected by the rest of the code
        col_info = {}

        # Skip empty collections
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

        # Set collection type and assume a non-zero count since we have fields
        col_info["type"] = "list"
        col_info["count"] = (
            100  # Assume a default count, not critical for selection logic
        )

        # Extract field information from analyze_collections result
        field_list = list(fields_data.keys())
        field_types = {}
        sample_values = {}
        unique_values = {}

        for field_name, field_info in fields_data.items():
            # Skip _id field
            if field_name == "_id":
                continue

            field_type = field_info.get("type", "unknown")
            field_types[field_name] = field_type

            # Extract sample and unique values based on the field type
            if field_type == "numerical":
                stats = field_info.get("stats", {})
                min_val = stats.get("min", "")
                max_val = stats.get("max", "")
                # Store min and max as sample values
                sample_values[field_name] = [str(min_val), str(max_val)]
                unique_values[field_name] = [str(min_val), str(max_val)]

            elif field_type == "datetime":
                stats = field_info.get("stats", {})
                min_val = stats.get("min", "")
                max_val = stats.get("max", "")
                # Store min and max dates as sample values
                sample_values[field_name] = [str(min_val), str(max_val)]
                unique_values[field_name] = [str(min_val), str(max_val)]

            elif field_type == "categorical":
                stats = field_info.get("stats", {})
                unique_list = stats.get("unique_values", [])
                # Store unique values, removing the "..." if present
                clean_list = [v for v in unique_list if v != "..."]
                sample_values[field_name] = (
                    clean_list[:5] if len(clean_list) > 5 else clean_list
                )
                unique_values[field_name] = clean_list
            else:
                # Handle unknown field types
                sample_values[field_name] = []
                unique_values[field_name] = []

        # Store the extracted information
        col_info["fields"] = field_list
        col_info["field_types"] = field_types
        col_info["sample_values"] = sample_values
        col_info["unique_values"] = unique_values

        logger.debug(
            f"Identified {len(field_list)} fields in collection {collection_name}"
        )
        collection_info[collection_name] = col_info

    logger.info(f"Processed {len(collection_info)} collections in MongoDB")
    return collection_info


def _search_for_values(
    collection_info: dict, search_terms: List[str]
) -> Dict[str, Dict[str, List[str]]]:
    """
    Search for values in collections that match the provided search terms.

    Args:
        collection_info: Dictionary of collection information
        search_terms: List of terms to search for

    Returns:
        Dictionary mapping collection names to matching fields and their values
    """
    logger.debug(f"Searching for values matching terms: {search_terms}")
    results = {}
    search_terms_lower = [term.lower() for term in search_terms]

    for collection_name, info in collection_info.items():
        matching_fields = {}
        if "unique_values" not in info:
            logger.warning(f"No unique values found in collection: {collection_name}")
            continue

        for field, unique_values in info["unique_values"].items():
            values_lower = [val.lower() for val in unique_values]
            matches = []
            for term in search_terms_lower:
                for i, val in enumerate(values_lower):
                    if term in val:
                        matches.append(unique_values[i])

            if matches:
                matching_fields[field] = matches
                logger.debug(
                    f"Collection {collection_name}, field '{field}' has {len(matches)} matches"
                )

        if matching_fields:
            results[collection_name] = matching_fields

    logger.info(f"Found value matches in {len(results)} collections")
    return results


def _match_headers_to_query(
    collection_info: dict, query: str
) -> Tuple[Dict[str, Dict[str, Any]], Optional[str], List[str]]:
    """
    Match collection field names to a query to find the most relevant collection.

    Args:
        collection_info: Dictionary of collection information
        query: User query string

    Returns:
        Tuple containing (all matches with scores, best match collection name, best match fields)
    """
    logger.info(f"Matching field names to query: '{query}'")
    query_terms = _extract_key_terms(query)
    best_match = None
    best_match_fields = []
    best_match_score = 0
    all_matches = {}

    for collection_name, info in collection_info.items():
        if "fields" not in info:
            logger.warning(f"No fields found in collection: {collection_name}")
            continue

        matching_fields = []
        field_match_score = 0
        for field in info["fields"]:
            field_lower = field.lower()
            for term in query_terms:
                if term == field_lower or term in field_lower:
                    matching_fields.append(field)
                    field_match_score += 3 if term == field_lower else 1
                    break

        if matching_fields and field_match_score > 0:
            all_matches[collection_name] = {
                "score": field_match_score,
                "fields": matching_fields,
                "reason": f"Field names match query terms: {', '.join(matching_fields)}",
            }
            logger.debug(
                f"Collection {collection_name} matched with score {field_match_score}: {matching_fields}"
            )

            if field_match_score > best_match_score:
                best_match = collection_name
                best_match_fields = matching_fields
                best_match_score = field_match_score

    if best_match:
        logger.info(
            f"Best field name match: {best_match} with score {best_match_score}"
        )
    else:
        logger.info("No field name matches found")

    return all_matches, best_match, best_match_fields


def _match_values_to_query(
    collection_info: dict, query: str
) -> Tuple[Dict[str, Dict[str, Any]], Optional[str], Dict[str, List[str]]]:
    """
    Match collection values to a query to find the most relevant collection.

    Args:
        collection_info: Dictionary of collection information
        query: User query string

    Returns:
        Tuple containing (all matches with scores, best match collection name, best match values)
    """
    logger.info(f"Matching values to query: '{query}'")
    key_terms = _extract_key_terms(query)
    value_matches = _search_for_values(collection_info, key_terms)
    best_match = None
    best_match_values = {}
    best_match_score = 0
    all_matches = {}

    for collection_name, field_matches in value_matches.items():
        match_score = sum(len(values) for values in field_matches.values())
        field_reasons = []
        for field, values in field_matches.items():
            field_reasons.append(f"'{field}' contains values: {', '.join(values[:3])}")

        reason = f"Values in fields match query terms: {'; '.join(field_reasons)}"
        all_matches[collection_name] = {
            "score": match_score,
            "values": field_matches,
            "fields": list(field_matches.keys()),
            "reason": reason,
        }
        logger.debug(
            f"Collection {collection_name} value match with score {match_score}"
        )

        if match_score > best_match_score:
            best_match = collection_name
            best_match_values = field_matches
            best_match_score = match_score

    if best_match:
        logger.info(f"Best value match: {best_match} with score {best_match_score}")
    else:
        logger.info("No value matches found")

    return all_matches, best_match, best_match_values


def _compare_matches(
    header_matches: Dict[str, Dict[str, Any]], value_matches: Dict[str, Dict[str, Any]]
) -> Tuple[Optional[str], Dict[str, Any], List[Dict[str, Any]]]:
    """
    Compare and combine header and value matches to determine the best overall match.

    Args:
        header_matches: Dictionary of collections matching by field names
        value_matches: Dictionary of collections matching by values

    Returns:
        Tuple containing (best match collection name, best match details, alternative matches)
    """
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


def _format_collection_info_for_prompt(collection_info: dict) -> str:
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
    collection_info: dict,
    best_match: str,
    best_match_details: Dict[str, Any],
    alternative_matches: List[Dict[str, Any]],
) -> Tuple[str, str, List[str]]:
    """
    Resolve ambiguous matches between multiple collections using an LLM.

    Args:
        query: User query string
        collection_info: Dictionary of collection information
        best_match: Current best match collection name
        best_match_details: Details about the best match
        alternative_matches: List of alternative matching collections

    Returns:
        Tuple containing (selected collection name, reason for selection, matching fields)
    """
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

        # Extract content from AIMessage if needed
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
    collection_info: dict, query: str, value_matches: Dict[str, Dict[str, List[str]]]
) -> CollectionAnalysisResult:
    """
    Select the most appropriate MongoDB collection for a query using an LLM.

    Args:
        collection_info: Dictionary of collection information
        query: User query string
        value_matches: Dictionary of value matches by collection

    Returns:
        CollectionAnalysisResult with the selected collection and matching information
    """
    logger.info(f"Selecting collection with Groq LLM for query: '{query}'")
    result = CollectionAnalysisResult(query=query)
    formatted_info = _format_collection_info_for_prompt(collection_info)

    value_match_info = ""
    if value_matches:
        value_match_info = "\nValue matches found:\n"
        for collection_name, field_matches in value_matches.items():
            value_match_info += f"Collection: {collection_name}\n"
            for field, matches in field_matches.items():
                value_match_info += f"  Field '{field}' contains values matching query terms: {', '.join(matches)}\n"

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

        # Extract content from AIMessage if needed
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
    """
    Select the most appropriate MongoDB collection for a user query.

    Args:
        query: User query string

    Returns:
        Name of the most appropriate MongoDB collection

    Raises:
        CollectionNotFoundError: If no appropriate collection can be found
    """
    logger.info(f"Selecting collection for query: '{query}'")

    # Initialize Database connection if not already done
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

    value_matches = _search_for_values(collection_info, _extract_key_terms(query))
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
        llm_result = _select_collection_with_llm(collection_info, query, value_matches)
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
    # Set up console logging for script execution
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
