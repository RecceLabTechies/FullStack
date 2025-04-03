#!/usr/bin/env python
import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from mypackage.utils.llm_config import get_groq_llm, JSON_SELECTOR_MODEL

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


class JSONFileNotFoundError(Exception):
    """Exception raised when a requested JSON file cannot be found or processed.

    This exception provides detailed information about the search attempt,
    including the query, directory searched, and reason for failure.
    """

    def __init__(
        self,
        message: str,
        query: Optional[str] = None,
        directory: Optional[str] = None,
        available_files: Optional[List[str]] = None,
    ):
        self.query = query
        self.directory = directory
        self.available_files = available_files
        super().__init__(message)
        logger.error(f"JSONFileNotFoundError: {message} for query '{query}'")


class JSONAnalysisResult(BaseModel):
    json_file: Optional[str] = None
    query: str
    reason: Optional[str] = None
    matching_fields: Optional[List[str]] = None
    matching_values: Optional[Dict[str, List[str]]] = None
    error: Optional[str] = None
    alternative_files: Optional[List[Dict[str, Any]]] = None


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


def _extract_json_info(
    directory: str, unique_value_limit: int = 10
) -> Dict[str, Dict[str, Any]]:
    """
    Extract schema and sample value information from JSON files in a directory.

    Args:
        directory: Path to directory containing JSON files
        unique_value_limit: Maximum number of unique values to extract per field

    Returns:
        Dictionary mapping filenames to their schema and sample data information
    """
    logger.info(f"Extracting JSON info from directory: {directory}")
    json_info = {}

    if not os.path.exists(directory):
        logger.error(f"Directory not found: {directory}")
        return json_info

    json_files_found = 0
    successful_files = 0

    for entry in os.listdir(directory):
        full_path = os.path.join(directory, entry)
        if not entry.lower().endswith(".json"):
            continue

        json_files_found += 1
        logger.debug(f"Processing JSON file: {entry}")

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            file_info = {}
            if isinstance(data, list) and data:
                file_info["type"] = "list"
                file_info["count"] = len(data)
                fields = set()
                field_types = {}
                sample_values = {}
                unique_values = {}

                logger.debug(f"Processing list data with {len(data)} items")
                for item in data[:100]:
                    if not isinstance(item, dict):
                        continue
                    for key, value in item.items():
                        fields.add(key)
                        field_types[key] = type(value).__name__
                        str_value = str(value)
                        if key not in sample_values:
                            sample_values[key] = []
                        if len(sample_values[key]) < unique_value_limit:
                            sample_values[key].append(str_value)
                        if key not in unique_values:
                            unique_values[key] = set()
                        if len(unique_values[key]) < unique_value_limit:
                            unique_values[key].add(str_value)

                file_info["fields"] = list(fields)
                file_info["field_types"] = field_types
                file_info["sample_values"] = sample_values
                file_info["unique_values"] = {
                    k: list(v) for k, v in unique_values.items()
                }
                logger.debug(f"Identified {len(fields)} fields in list-type JSON")

            elif isinstance(data, dict):
                file_info["type"] = "dict"
                fields = list(data.keys())
                field_types = {key: type(value).__name__ for key, value in data.items()}
                sample_values = {key: [str(value)] for key, value in data.items()}
                unique_values = {key: [str(value)] for key, value in data.items()}
                file_info["fields"] = fields
                file_info["field_types"] = field_types
                file_info["sample_values"] = sample_values
                file_info["unique_values"] = unique_values
                logger.debug(f"Identified {len(fields)} fields in dict-type JSON")

            json_info[entry] = file_info
            successful_files += 1

        except Exception as e:
            logger.error(f"Error processing JSON file {entry}: {str(e)}", exc_info=True)

    logger.info(
        f"Processed {successful_files}/{json_files_found} JSON files in {directory}"
    )
    return json_info


def _search_for_values(
    json_info: dict, search_terms: List[str]
) -> Dict[str, Dict[str, List[str]]]:
    """
    Search for values in JSON files that match the provided search terms.

    Args:
        json_info: Dictionary of JSON file information
        search_terms: List of terms to search for

    Returns:
        Dictionary mapping filenames to matching fields and their values
    """
    logger.debug(f"Searching for values matching terms: {search_terms}")
    results = {}
    search_terms_lower = [term.lower() for term in search_terms]

    for file_name, info in json_info.items():
        matching_fields = {}
        if "unique_values" not in info:
            logger.warning(f"No unique values found in file: {file_name}")
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
                    f"File {file_name}, field '{field}' has {len(matches)} matches"
                )

        if matching_fields:
            results[file_name] = matching_fields

    logger.info(f"Found value matches in {len(results)} files")
    return results


def _match_headers_to_query(
    json_info: dict, query: str
) -> Tuple[Dict[str, Dict[str, Any]], Optional[str], List[str]]:
    """
    Match JSON file headers to a query to find the most relevant file.

    Args:
        json_info: Dictionary of JSON file information
        query: User query string

    Returns:
        Tuple containing (all matches with scores, best match filename, best match fields)
    """
    logger.info(f"Matching headers to query: '{query}'")
    query_terms = _extract_key_terms(query)
    best_match = None
    best_match_fields = []
    best_match_score = 0
    all_matches = {}

    for file_name, info in json_info.items():
        if "fields" not in info:
            logger.warning(f"No fields found in file: {file_name}")
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
            all_matches[file_name] = {
                "score": field_match_score,
                "fields": matching_fields,
                "reason": f"Field names match query terms: {', '.join(matching_fields)}",
            }
            logger.debug(
                f"File {file_name} matched with score {field_match_score}: {matching_fields}"
            )

            if field_match_score > best_match_score:
                best_match = file_name
                best_match_fields = matching_fields
                best_match_score = field_match_score

    if best_match:
        logger.info(f"Best header match: {best_match} with score {best_match_score}")
    else:
        logger.info("No header matches found")

    return all_matches, best_match, best_match_fields


def _match_values_to_query(
    json_info: dict, query: str
) -> Tuple[Dict[str, Dict[str, Any]], Optional[str], Dict[str, List[str]]]:
    """
    Match JSON file values to a query to find the most relevant file.

    Args:
        json_info: Dictionary of JSON file information
        query: User query string

    Returns:
        Tuple containing (all matches with scores, best match filename, best match values)
    """
    logger.info(f"Matching values to query: '{query}'")
    key_terms = _extract_key_terms(query)
    value_matches = _search_for_values(json_info, key_terms)
    best_match = None
    best_match_values = {}
    best_match_score = 0
    all_matches = {}

    for file_name, field_matches in value_matches.items():
        match_score = sum(len(values) for values in field_matches.values())
        field_reasons = []
        for field, values in field_matches.items():
            field_reasons.append(f"'{field}' contains values: {', '.join(values[:3])}")

        reason = f"Values in fields match query terms: {'; '.join(field_reasons)}"
        all_matches[file_name] = {
            "score": match_score,
            "values": field_matches,
            "fields": list(field_matches.keys()),
            "reason": reason,
        }
        logger.debug(f"File {file_name} value match with score {match_score}")

        if match_score > best_match_score:
            best_match = file_name
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
        header_matches: Dictionary of files matching by headers
        value_matches: Dictionary of files matching by values

    Returns:
        Tuple containing (best match filename, best match details, alternative matches)
    """
    logger.info("Comparing header and value matches")
    all_files = set(list(header_matches.keys()) + list(value_matches.keys()))
    combined_scores = {}

    for file_name in all_files:
        header_score = header_matches.get(file_name, {}).get("score", 0)
        value_score = value_matches.get(file_name, {}).get("score", 0)
        combined_score = header_score * 1.2 + value_score

        header_fields = header_matches.get(file_name, {}).get("fields", [])
        value_fields = value_matches.get(file_name, {}).get("fields", [])
        all_fields = list(set(header_fields + value_fields))
        values = value_matches.get(file_name, {}).get("values", {})

        reasons = []
        if file_name in header_matches:
            reasons.append(header_matches[file_name]["reason"])
        if file_name in value_matches:
            reasons.append(value_matches[file_name]["reason"])

        combined_reason = " ".join(reasons)
        combined_scores[file_name] = {
            "score": combined_score,
            "fields": all_fields,
            "values": values,
            "reason": combined_reason,
            "header_score": header_score,
            "value_score": value_score,
        }
        logger.debug(
            f"File {file_name} combined score: {combined_score} (header: {header_score}, value: {value_score})"
        )

    best_match = None
    best_match_details = {}
    best_score = 0

    for file_name, details in combined_scores.items():
        if details["score"] > best_score:
            best_match = file_name
            best_match_details = details
            best_score = details["score"]

    alternative_matches = []
    if best_match and best_score > 0:
        threshold = best_score * 0.7
        for file_name, details in combined_scores.items():
            if file_name != best_match and details["score"] >= threshold:
                alternative_matches.append(
                    {
                        "file": file_name,
                        "score": details["score"],
                        "fields": details["fields"],
                        "reason": details["reason"],
                    }
                )
                logger.debug(
                    f"Alternative match: {file_name} with score {details['score']}"
                )

    if best_match:
        logger.info(f"Best overall match: {best_match} with score {best_score}")
        logger.info(f"Found {len(alternative_matches)} alternative matches")
    else:
        logger.warning("No matches found")

    return best_match, best_match_details, alternative_matches


def _format_json_info_for_prompt(json_info: dict) -> str:
    """
    Format JSON file information for use in an LLM prompt.

    Args:
        json_info: Dictionary of JSON file information

    Returns:
        Formatted string with JSON file details for the prompt
    """
    logger.debug("Formatting JSON info for LLM prompt")
    if not json_info:
        logger.warning("No JSON files available for formatting")
        return "📭 No JSON files available for analysis."

    formatted_info = []
    for file_name, info in json_info.items():
        if (
            "fields" not in info
            or "sample_values" not in info
            or "unique_values" not in info
        ):
            logger.warning(f"Incomplete info for file {file_name}, skipping")
            continue

        file_desc = [f"📄 File: {file_name}"]
        file_desc.append("🔑 Fields: " + ", ".join(info["fields"]))
        samples = []

        for field in info["fields"]:
            if field in info["sample_values"] and info["sample_values"][field]:
                samples.append(
                    f"{field} examples: {', '.join(map(str, info['sample_values'][field]))}"
                )

        file_desc.append("📊 Sample values:")
        file_desc.extend([f"  ▫️ {sample}" for sample in samples])
        file_desc.append("🔍 Unique values by field:")

        for field in info["fields"]:
            if field in info["unique_values"] and info["unique_values"][field]:
                unique_vals = info["unique_values"][field]
                display_vals = unique_vals[:10]
                has_more = len(unique_vals) > 10
                unique_vals_str = ", ".join(map(str, display_vals))
                if has_more:
                    unique_vals_str += ", ..."
                file_desc.append(f"  ▫️ {field}: {unique_vals_str}")

        formatted_info.append("\n".join(file_desc))

    logger.debug(f"Formatted info for {len(formatted_info)} files")
    return "\n\n".join(formatted_info)


def _resolve_ambiguous_matches(
    query: str,
    json_info: dict,
    best_match: str,
    best_match_details: Dict[str, Any],
    alternative_matches: List[Dict[str, Any]],
) -> Tuple[str, str, List[str]]:
    """
    Resolve ambiguous matches between multiple JSON files using an LLM.

    Args:
        query: User query string
        json_info: Dictionary of JSON file information
        best_match: Current best match filename
        best_match_details: Details about the best match
        alternative_matches: List of alternative matching files

    Returns:
        Tuple containing (selected filename, reason for selection, matching fields)
    """
    logger.info(f"Resolving ambiguous matches for query: '{query}'")
    logger.debug(f"Best match: {best_match}, alternatives: {len(alternative_matches)}")

    best_match_info = f"File: {best_match}\nScore: {best_match_details['score']:.2f}\nMatching fields: {', '.join(best_match_details['fields'])}\nReason: {best_match_details['reason']}"
    alternatives_info = []

    for alt in alternative_matches:
        alt_info = f"File: {alt['file']}\nScore: {alt['score']:.2f}\nMatching fields: {', '.join(alt['fields'])}\nReason: {alt['reason']}"
        alternatives_info.append(alt_info)

    alternatives_text = "\n\n".join(alternatives_info)
    prompt = ChatPromptTemplate.from_template(
        """I need to determine which JSON file is most appropriate for a user query when multiple files match.

User Query: {query}

Current best match:
{best_match_info}

Alternative matches:
{alternatives_info}

Based on the query and the information about each file, determine which file would be most appropriate.
Consider:
1. Which file's fields and values are most relevant to the query's intent
2. Which file would provide the most useful information for answering the query
3. The semantic meaning of the query and how it relates to each file's content

Respond in this exact format:
file: [selected json filename]
reason: [brief explanation of why this file is most appropriate]
matching_fields: [comma-separated list of fields that match the query criteria]

Important: The filename MUST be exactly as shown in the available files list."""
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

        selected_file = best_match
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
                if line.lower().startswith("file:"):
                    file_name = line.split(":", 1)[1].strip()
                    if file_name in json_info:
                        selected_file = file_name
                elif line.lower().startswith("reason:"):
                    reason = line.split(":", 1)[1].strip()
                elif line.lower().startswith("matching_fields:"):
                    fields_str = line.split(":", 1)[1].strip()
                    if fields_str and fields_str.lower() != "none":
                        matching_fields = [
                            field.strip() for field in fields_str.split(",")
                        ]

        logger.info(f"Selected file: {selected_file}")
        return selected_file, reason, matching_fields

    except Exception as e:
        logger.error(f"Error resolving ambiguous matches: {str(e)}", exc_info=True)
        return best_match, best_match_details["reason"], best_match_details["fields"]


def _select_json_with_llm(
    json_info: dict, query: str, value_matches: Dict[str, Dict[str, List[str]]]
) -> JSONAnalysisResult:
    """
    Select the most appropriate JSON file for a query using an LLM.

    Args:
        json_info: Dictionary of JSON file information
        query: User query string
        value_matches: Dictionary of value matches by file

    Returns:
        JSONAnalysisResult with the selected file and matching information
    """
    logger.info(f"Selecting JSON with Groq LLM for query: '{query}'")
    result = JSONAnalysisResult(query=query)
    formatted_info = _format_json_info_for_prompt(json_info)

    value_match_info = ""
    if value_matches:
        value_match_info = "\nValue matches found:\n"
        for file_name, field_matches in value_matches.items():
            value_match_info += f"File: {file_name}\n"
            for field, matches in field_matches.items():
                value_match_info += f"  Field '{field}' contains values matching query terms: {', '.join(matches)}\n"

    prompt = ChatPromptTemplate.from_template(
        """Given the following JSON files and their contents, determine the most appropriate file for the query.

        Available JSON files and their contents:
        {json_info}

        {value_match_info}

        Query: {query}

        You MUST ONLY select from the JSON files listed above.
        Analyze the fields, sample values, and unique values to determine which JSON file would be most relevant for this query.
        Pay special attention to any value matches found, as these indicate fields containing values mentioned in the query.

        If NO file is appropriate for this query, respond with "No appropriate file found" and explain why.

        Respond in this exact format:
        file: [selected json filename or "NONE" if no appropriate file]
        reason: [brief explanation of why this file is most appropriate or why no file is appropriate]
        matching_fields: [comma-separated list of fields that match the query criteria]

        Important: The filename MUST be exactly as shown in the available files list."""
    )

    model = get_groq_llm(DEFAULT_MODEL_NAME)
    try:
        logger.debug("Invoking Groq LLM for JSON selection")
        response = model.invoke(
            prompt.format(
                json_info=formatted_info, query=query, value_match_info=value_match_info
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
                if line.lower().startswith("file:"):
                    file_name = line.split(":", 1)[1].strip()
                    if file_name.lower() == "none":
                        result.error = "No appropriate JSON file found for this query"
                        logger.info("Groq LLM found no appropriate file")
                    elif file_name in json_info:
                        result.json_file = file_name
                        logger.info(f"Groq LLM selected file: {file_name}")
                    else:
                        result.error = f"Selected file '{file_name}' not found in available JSON files"
                        logger.warning(f"Groq LLM selected invalid file: {file_name}")
                elif line.lower().startswith("reason:"):
                    result.reason = line.split(":", 1)[1].strip()
                elif line.lower().startswith("matching_fields:"):
                    fields_str = line.split(":", 1)[1].strip()
                    if fields_str and fields_str.lower() != "none":
                        result.matching_fields = [
                            field.strip() for field in fields_str.split(",")
                        ]

            if (
                result.json_file
                and result.matching_fields
                and result.json_file in value_matches
            ):
                result.matching_values = {}
                for field in result.matching_fields:
                    if field in value_matches[result.json_file]:
                        result.matching_values[field] = value_matches[result.json_file][
                            field
                        ]
        else:
            result.error = "Invalid response format from Groq LLM"
            logger.error("Invalid response format from Groq LLM")

    except Exception as e:
        error_msg = f"Error during JSON selection: {str(e)}"
        result.error = error_msg
        logger.error(error_msg, exc_info=True)

    return result


def select_json_for_query(query: str, data_dir: str = "./data") -> str:
    """
    Select the most appropriate JSON file for a user query.

    Args:
        query: User query string
        data_dir: Directory containing JSON files

    Returns:
        Name of the most appropriate JSON file

    Raises:
        JSONFileNotFoundError: If no appropriate file can be found
    """
    logger.info(f"Selecting JSON for query: '{query}' in directory: {data_dir}")

    json_info = _extract_json_info(data_dir)
    if not json_info:
        error_msg = "No JSON files found in directory"
        logger.error(f"{error_msg}: {data_dir}")
        raise JSONFileNotFoundError(
            error_msg,
            query=query,
            directory=data_dir,
            available_files=[],
        )

    header_matches, best_match_by_header, matching_fields = _match_headers_to_query(
        json_info, query
    )

    value_matches = _search_for_values(json_info, _extract_key_terms(query))
    value_match_dict, best_match_by_value, best_match_values = _match_values_to_query(
        json_info, query
    )

    best_match, best_match_details, alternative_matches = _compare_matches(
        header_matches, value_match_dict
    )

    if best_match and not alternative_matches:
        logger.info(f"Selected JSON file without ambiguity: {best_match}")
        return best_match

    if best_match and alternative_matches:
        logger.info(
            f"Resolving ambiguity between {len(alternative_matches) + 1} matches"
        )
        selected_file, reason, matching_fields = _resolve_ambiguous_matches(
            query, json_info, best_match, best_match_details, alternative_matches
        )
        logger.info(f"Selected JSON file after resolving ambiguity: {selected_file}")
        return selected_file

    if not best_match:
        logger.info("No matching files found, asking Groq LLM to help")
        llm_result = _select_json_with_llm(json_info, query, value_matches)
        if llm_result.json_file:
            logger.info(f"Groq LLM selected JSON file: {llm_result.json_file}")
            return llm_result.json_file

    error_msg = "No matching JSON file found for this query. The query terms don't match any column headers or values in the available JSON files."
    logger.error(error_msg)
    raise JSONFileNotFoundError(
        error_msg,
        query=query,
        directory=data_dir,
        available_files=list(json_info.keys()),
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

    test_query = "create a bar chart of monthly sales"
    logger.info(f"Testing with query: '{test_query}'")
    try:
        selected_file = select_json_for_query(test_query)
        print(f"Selected JSON file: {selected_file}")
    except JSONFileNotFoundError as e:
        print(f"Error: {str(e)}")
