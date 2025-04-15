#!/usr/bin/env python
"""
Table Selector Module

This module provides functionality for selecting the most appropriate PostgreSQL table
based on a user's analytical query. It analyzes table metadata, field names, and sample
values to determine which table is most likely to contain the data needed to answer
the query.

It now also uses vector similarity search to find similar historical queries and
improve table selection accuracy.
"""

import logging
from typing import Any, Dict, List, Optional, Protocol, Tuple, TypedDict

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from mypackage.utils.database import Database
from mypackage.utils.example_vectorizer import ExampleVectorizer
from mypackage.utils.llm_config import COLLECTION_SELECTOR_MODEL, get_groq_llm

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

logger.debug("table_selector module initialized")

DEFAULT_MODEL_NAME = COLLECTION_SELECTOR_MODEL


class LLMResponse(Protocol):
    """
    Protocol defining the expected structure of responses from language models.
    """

    content: str


class TableNotFoundError(Exception):
    """
    Exception raised when no suitable table is found for a query.

    Attributes:
        query: The user query that couldn't be matched
        available_tables: List of available tables in the database
        message: Explanation of why the table was not found
    """

    def __init__(
        self,
        message: str,
        query: Optional[str] = None,
        available_tables: Optional[List[str]] = None,
    ):
        self.query = query
        self.available_tables = available_tables
        super().__init__(message)
        logger.error(f"TableNotFoundError: {message} for query '{query}'")


class TableInfo(TypedDict):
    """
    Type definition for storing table metadata.

    Attributes:
        type: The type of table (typically "relational" for PostgreSQL tables)
        count: Approximate number of rows in the table
        fields: List of field names in the table
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


class TableAnalysisResult(BaseModel):
    """
    Pydantic model representing the result of table analysis.

    Attributes:
        table_name: The name of the selected table (if found)
        query: The original user query
        reason: Explanation of why this table was selected
        matching_fields: List of fields that matched the query
        matching_values: Dictionary of fields and values that matched the query
        error: Error message if table selection failed
        alternative_tables: List of other possible tables with scores
    """

    table_name: Optional[str] = None
    query: str
    reason: Optional[str] = None
    matching_fields: Optional[List[str]] = None
    matching_values: Optional[Dict[str, List[str]]] = None
    error: Optional[str] = None
    alternative_tables: Optional[List[Dict[str, Any]]] = None


class FieldProcessor:
    """
    Static class for processing field metadata based on field types.

    This class provides methods for extracting sample and unique values
    from different types of fields (numerical, datetime, categorical).
    """

    @classmethod
    def process_numerical(cls, stats: Dict) -> Tuple[List[str], List[str]]:
        """
        Process numerical field statistics to generate sample and unique values.

        Args:
            stats: Dictionary containing min and max values

        Returns:
            Tuple of (sample values, unique values)
        """
        if not stats or "min" not in stats or "max" not in stats:
            return [], []

        min_val = stats.get("min")
        max_val = stats.get("max")

        # Generate representative sample values
        if min_val is not None and max_val is not None:
            # Create a list of values between min and max
            values = []
            if min_val == max_val:
                values = [str(min_val)]
            else:
                # Add min, max, and some evenly distributed values
                values = [
                    str(min_val),
                    str((min_val + max_val) / 2),
                    str(max_val),
                ]
            return values, values

        return [], []

    @classmethod
    def process_categorical(cls, stats: Dict) -> Tuple[List[str], List[str]]:
        """
        Process categorical field statistics to generate sample and unique values.

        Args:
            stats: Dictionary containing unique_values list

        Returns:
            Tuple of (sample values, unique values)
        """
        if not stats or "unique_values" not in stats:
            return [], []

        unique_values = stats.get("unique_values", [])
        if not unique_values:
            return [], []

        # Use all unique values as samples
        return unique_values[:10], unique_values  # Limit to 10 samples

    @classmethod
    def process_datetime(cls, stats: Dict) -> Tuple[List[str], List[str]]:
        """
        Process datetime field statistics to generate sample and unique values.

        Args:
            stats: Dictionary containing min and max values

        Returns:
            Tuple of (sample values, unique values)
        """
        if not stats or "min" not in stats or "max" not in stats:
            return [], []

        min_val = stats.get("min")
        max_val = stats.get("max")

        if min_val and max_val:
            return [min_val, max_val], [min_val, max_val]

        return [], []

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
        if field_type in ("integer", "bigint", "numeric", "double precision", "real"):
            return cls.process_numerical(stats)
        elif field_type in ("timestamp", "date", "time"):
            return cls.process_datetime(stats)
        else:
            return cls.process_categorical(stats)


def _extract_table_info() -> Dict[str, TableInfo]:
    """
    Extract schema and sample value information from PostgreSQL tables.

    This function analyzes all accessible tables in the database and
    extracts metadata including field names, types, and representative values.

    Returns:
        Dictionary mapping table names to their schema and sample data information

    Note:
        Uses Database.analyze_tables() to get raw table data
    """
    logger.info("Extracting table info from PostgreSQL using analyze_tables")
    table_info = {}

    # Get raw table analysis data
    tables_analysis = Database.analyze_tables()
    if not tables_analysis:
        logger.warning("No tables or metadata returned from analyze_tables")
        return table_info

    # Process each table
    for table_name, fields_data in tables_analysis.items():
        logger.debug(f"Processing metadata for table: {table_name}")
        tbl_info = {}

        # Handle empty tables
        if not fields_data:
            logger.debug(f"Table {table_name} has no fields or is empty")
            tbl_info["type"] = "unknown"
            tbl_info["count"] = 0
            tbl_info["fields"] = []
            tbl_info["field_types"] = {}
            tbl_info["sample_values"] = {}
            tbl_info["unique_values"] = {}
            table_info[table_name] = tbl_info
            continue

        # Initialize table info
        tbl_info["type"] = "relational"
        tbl_info["count"] = 100  # Placeholder

        field_list = list(fields_data.keys())
        field_types = {}
        sample_values = {}
        unique_values = {}

        # Process each field in the table
        field_count = 0
        for field_name, field_info in fields_data.items():
            field_count += 1
            field_type = field_info.get("type", "unknown")
            field_types[field_name] = field_type

            # Process field based on its type
            stats = field_info.get("stats", {})
            sample_values[field_name], unique_values[field_name] = (
                FieldProcessor.process_field(field_type, stats)
            )

        # Store processed table info
        tbl_info["fields"] = field_list
        tbl_info["field_types"] = field_types
        tbl_info["sample_values"] = sample_values
        tbl_info["unique_values"] = unique_values

        logger.debug(f"Processed {field_count} fields in table {table_name}")
        table_info[table_name] = tbl_info

    logger.info(f"Extracted metadata for {len(table_info)} tables")
    return table_info


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


def _match_headers_to_query(
    table_info: Dict[str, TableInfo], query: str
) -> Tuple[Dict[str, Dict], Optional[str], List[str]]:
    """
    Match table field names to a query to find the most relevant table.

    This function analyzes the query and compares key terms to field names in each table
    to determine which table is most likely to contain the relevant data.

    Args:
        table_info: Dictionary of table information
        query: User query string

    Returns:
        Tuple containing:
        - Dictionary of all table matches with scores
        - Name of the best matching table (or None if no match)
        - List of matching fields in the best matching table
    """
    logger.info(f"Matching field names to query: '{query}'")

    # Extract key terms from the query
    query_terms = _extract_key_terms(query)

    best_match = None
    best_match_fields = []
    best_match_score = 0
    all_matches = {}

    # Process each table
    for table_name, info in table_info.items():
        logger.debug(f"Checking table '{table_name}' for field name matches")

        if "fields" not in info or not info["fields"]:
            logger.warning(f"No fields found in table: {table_name}")
            continue

        matched_fields = []
        match_score = 0
        match_reasons = []

        # Check each field name for matches with query terms
        for field in info["fields"]:
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
            all_matches[table_name] = {
                "score": match_score,
                "fields": matched_fields,
                "reason": match_reason,
            }

            # Update best match if this table has a higher score
            if match_score > best_match_score:
                best_match = table_name
                best_match_fields = matched_fields
                best_match_score = match_score
                logger.debug(f"New best match: '{table_name}' with score {match_score}")

    if best_match:
        logger.info(f"Best header match: '{best_match}' with score {best_match_score}")
    else:
        logger.info("No field name matches found in any table")

    return all_matches, best_match, best_match_fields


def _match_values_to_query(
    table_info: Dict[str, TableInfo], query: str
) -> Tuple[Dict[str, Dict], Optional[str], Dict[str, List[str]]]:
    """
    Match table values to a query and score matches in a single flow.

    Args:
        table_info: Dictionary of table information
        query: User query string

    Returns:
        Tuple containing:
        - Dictionary of all value matches with scores
        - Name of the best matching table (or None if no match)
        - Dictionary of matching values in the best matching table
    """
    logger.info(f"Matching values to query: '{query}'")
    key_terms = _extract_key_terms(query)
    search_terms_lower = [term.lower() for term in key_terms]

    all_matches = {}
    best_match = None
    best_match_values = {}
    best_match_score = 0

    # Single pass through tables and fields
    for table_name, info in table_info.items():
        if "unique_values" not in info:
            logger.warning(f"No unique values in table: {table_name}")
            continue

        field_matches = {}
        field_reasons = []

        # Process each field's unique values
        for field, values in info["unique_values"].items():
            matches = [
                val
                for val in values
                if any(term in str(val).lower() for term in search_terms_lower)
            ]

            if matches:
                field_matches[field] = matches
                field_reasons.append(
                    f"'{field}' contains: {', '.join(str(m) for m in matches[:3])}"
                )

        if field_matches:
            # Calculate match score and build result in same step
            match_score = sum(len(v) for v in field_matches.values())
            reason = f"Values match query terms: {'; '.join(field_reasons)}"

            all_matches[table_name] = {
                "score": match_score,
                "values": field_matches,
                "fields": list(field_matches.keys()),
                "reason": reason,
            }

            # Track best match
            if match_score > best_match_score:
                best_match = table_name
                best_match_values = field_matches
                best_match_score = match_score

    if best_match:
        logger.info(f"Best value match: {best_match} (score: {best_match_score})")
    else:
        logger.info("No value matches found")

    return all_matches, best_match, best_match_values


def _compare_matches(
    header_matches: Dict[str, Dict],
    value_matches: Dict[str, Dict],
) -> Tuple[Optional[str], Dict, List[Dict]]:
    """
    Compare header and value matches to determine the best overall match.

    Args:
        header_matches: Dictionary of header matches by table
        value_matches: Dictionary of value matches by table

    Returns:
        Tuple containing:
        - Name of the best matching table (or None if no match)
        - Details of the best match
        - List of alternative matches
    """
    logger.info("Comparing field name and value matches")
    all_tables = set(list(header_matches.keys()) + list(value_matches.keys()))
    combined_scores = {}

    for table_name in all_tables:
        header_score = header_matches.get(table_name, {}).get("score", 0)
        value_score = value_matches.get(table_name, {}).get("score", 0)
        combined_score = header_score * 1.2 + value_score

        header_fields = header_matches.get(table_name, {}).get("fields", [])
        value_fields = value_matches.get(table_name, {}).get("fields", [])
        all_fields = list(set(header_fields + value_fields))
        values = value_matches.get(table_name, {}).get("values", {})

        reasons = []
        if table_name in header_matches:
            reasons.append(header_matches[table_name]["reason"])
        if table_name in value_matches:
            reasons.append(value_matches[table_name]["reason"])

        combined_reason = " ".join(reasons)
        combined_scores[table_name] = {
            "score": combined_score,
            "fields": all_fields,
            "values": values,
            "reason": combined_reason,
            "header_score": header_score,
            "value_score": value_score,
        }
        logger.debug(
            f"Table {table_name} combined score: {combined_score} (header: {header_score}, value: {value_score})"
        )

    best_match = None
    best_match_details = {}
    best_score = 0

    for table_name, details in combined_scores.items():
        if details["score"] > best_score:
            best_match = table_name
            best_match_details = details
            best_score = details["score"]

    alternative_matches = []
    if best_match and best_score > 0:
        threshold = best_score * 0.7
        for table_name, details in combined_scores.items():
            if table_name != best_match and details["score"] >= threshold:
                alternative_matches.append(
                    {
                        "table": table_name,
                        "score": details["score"],
                        "fields": details["fields"],
                        "reason": details["reason"],
                    }
                )
                logger.debug(
                    f"Alternative match: {table_name} with score {details['score']}"
                )

    if best_match:
        logger.info(f"Best overall match: {best_match} with score {best_score}")
        logger.info(f"Found {len(alternative_matches)} alternative matches")
    else:
        logger.warning("No matches found")

    return best_match, best_match_details, alternative_matches


def _resolve_ambiguous_matches(
    query: str,
    table_info: Dict[str, TableInfo],
    best_match: str,
    best_match_details: Dict,
    alternative_matches: List[Dict],
) -> Tuple[str, str, List[str]]:
    """
    Resolve ambiguous matches between tables with similar scores.

    This function analyzes the best match and alternatives to determine
    which table is most appropriate for the query.

    Args:
        query: User query string
        table_info: Dictionary of table information
        best_match: Name of the current best match
        best_match_details: Details of the best match
        alternative_matches: List of alternative matches

    Returns:
        Tuple containing:
        - Name of the selected table
        - Reason for selection
        - List of matching fields
    """
    logger.info(f"Resolving ambiguous matches for query: '{query}'")
    logger.debug(f"Best match: {best_match}, alternatives: {len(alternative_matches)}")

    # If no alternatives, just return the best match
    if not alternative_matches:
        return best_match, best_match_details["reason"], best_match_details["fields"]

    # Simple resolution strategy: use a heuristic approach
    # In a real implementation, this could use an LLM like in collection_selector.py

    # Analyze query intent
    query_lower = query.lower()
    analytical_keywords = [
        "analyze",
        "chart",
        "trend",
        "report",
        "dashboard",
        "statistics",
    ]
    transactional_keywords = ["transaction", "record", "entry", "log", "recent"]
    time_keywords = ["date", "time", "period", "year", "month", "day"]

    # Score each match based on these heuristics
    scores = {}
    scores[best_match] = best_match_details["score"]

    for alt in alternative_matches:
        table_name = alt["table"]
        base_score = alt["score"]

        # Apply heuristic adjustments
        adjusted_score = base_score

        # Check if table name appears directly in query
        if table_name.lower().replace("_", " ") in query_lower:
            adjusted_score *= 1.5
            logger.debug(f"Table {table_name} directly mentioned in query: +50%")

        # Check for analytical intent
        if (
            any(keyword in query_lower for keyword in analytical_keywords)
            and "summary" in table_name.lower()
        ):
            adjusted_score *= 1.3
            logger.debug(f"Table {table_name} matches analytical intent: +30%")

        # Check for transactional intent
        if any(keyword in query_lower for keyword in transactional_keywords) and any(
            x in table_name.lower() for x in ["transaction", "log", "entry"]
        ):
            adjusted_score *= 1.3
            logger.debug(f"Table {table_name} matches transactional intent: +30%")

        # Check for time-based intent
        if any(keyword in query_lower for keyword in time_keywords) and any(
            x in table_name.lower() for x in ["date", "time", "history"]
        ):
            adjusted_score *= 1.2
            logger.debug(f"Table {table_name} matches time-based intent: +20%")

        scores[table_name] = adjusted_score

    # Select the table with the highest adjusted score
    selected_table = max(scores.items(), key=lambda x: x[1])[0]

    if selected_table != best_match:
        logger.info(
            f"Ambiguity resolution changed selection from {best_match} to {selected_table}"
        )

        # Get reason and fields for the selected table
        if selected_table in table_info:
            reason = next(
                (
                    alt["reason"]
                    for alt in alternative_matches
                    if alt["table"] == selected_table
                ),
                "Selected after ambiguity resolution",
            )
            fields = next(
                (
                    alt["fields"]
                    for alt in alternative_matches
                    if alt["table"] == selected_table
                ),
                [],
            )
        else:
            reason = best_match_details["reason"]
            fields = best_match_details["fields"]
    else:
        logger.info(f"Ambiguity resolution confirmed original selection: {best_match}")
        reason = best_match_details["reason"]
        fields = best_match_details["fields"]

    return selected_table, reason, fields


def _format_table_info_for_prompt(
    table_info: Dict[str, TableInfo],
) -> str:
    """
    Format table information for use in an LLM prompt.

    Args:
        table_info: Dictionary of table information

    Returns:
        Formatted string with table details for the prompt
    """
    logger.debug("Formatting table info for LLM prompt")
    if not table_info:
        logger.warning("No tables available for formatting")
        return "📭 No tables available for analysis."

    formatted_info = []
    for table_name, info in table_info.items():
        if (
            "fields" not in info
            or "sample_values" not in info
            or "unique_values" not in info
        ):
            logger.warning(f"Incomplete info for table {table_name}, skipping")
            continue

        tbl_desc = [f"📄 Table: {table_name}"]
        tbl_desc.append("🔑 Fields: " + ", ".join(info["fields"]))
        samples = []

        for field in info["fields"]:
            if field in info["sample_values"] and info["sample_values"][field]:
                samples.append(
                    f"{field} examples: {', '.join(map(str, info['sample_values'][field]))}"
                )

        tbl_desc.append("📊 Sample values:")
        tbl_desc.extend([f"  ▫️ {sample}" for sample in samples])
        tbl_desc.append("🔍 Unique values by field:")

        for field in info["fields"]:
            if field in info["unique_values"] and info["unique_values"][field]:
                unique_vals = info["unique_values"][field]
                display_vals = unique_vals[:10]
                has_more = len(unique_vals) > 10
                unique_vals_str = ", ".join(map(str, display_vals))
                if has_more:
                    unique_vals_str += ", ..."
                tbl_desc.append(f"  ▫️ {field}: {unique_vals_str}")

        formatted_info.append("\n".join(tbl_desc))

    logger.debug(f"Formatted info for {len(formatted_info)} tables")
    return "\n\n".join(formatted_info)


def _get_similar_table_selections(query: str, n_results: int = 3) -> List[Dict]:
    """
    Fetch similar table selection examples based on vector similarity.

    Args:
        query: The user query to find similar examples for
        n_results: Number of examples to return

    Returns:
        List of similar table selection examples with their similarity scores
    """
    logger.info(f"Finding similar table selection examples for query: '{query}'")

    examples = ExampleVectorizer.get_similar_examples(
        function_name="table_selector", query=query, n_results=n_results
    )

    if not examples:
        logger.warning("No similar table selection examples found")
        return []

    processed_examples = []
    for example in examples:
        if (
            "query" in example
            and "result" in example
            and "collection_name" in example["result"]
        ):
            similarity_score = example.get("distance", 1.0)
            # Lower distance means more similar (convert to similarity percentage)
            similarity = round((1 - min(similarity_score, 0.99)) * 100)

            processed_examples.append(
                {
                    "query": example["query"],
                    "table": example["result"]["collection_name"],
                    "reason": example["result"].get("reason", ""),
                    "matching_fields": example["result"].get("matching_fields", []),
                    "similarity": similarity,
                }
            )

    logger.info(f"Found {len(processed_examples)} similar table selection examples")
    return processed_examples


def _select_table_with_llm(
    table_info: Dict[str, TableInfo],
    query: str,
    value_matches: Dict[str, Dict],
) -> TableAnalysisResult:
    """
    Select the most appropriate table using a Groq LLM.

    This function formats table information and value matches into a prompt
    for the LLM, which then selects the most relevant table for the query.
    It now enriches the prompt with similar examples from vector search.

    Args:
        table_info: Dictionary of table information
        query: User query string
        value_matches: Dictionary of value matches by table

    Returns:
        TableAnalysisResult with the selected table and match details
    """
    logger.info(f"Selecting table with Groq LLM for query: '{query}'")
    result = TableAnalysisResult(query=query)
    formatted_info = _format_table_info_for_prompt(table_info)

    value_match_info = ""
    if value_matches:
        value_match_info = "\nValue matches found:\n"
        for table_name, match in value_matches.items():
            value_match_info += f"Table: {table_name}\n"
            for field, matches in match["values"].items():
                value_match_info += f"  Field '{field}' contains matches: {', '.join(map(str, matches))}\n"

    # Retrieve similar examples using vector embeddings
    similar_examples = _get_similar_table_selections(query)

    # Format similar examples for inclusion in the prompt
    similar_examples_text = ""
    if similar_examples:
        similar_examples_text = (
            "\nSimilar historical queries and their table selections:\n"
        )
        for i, example in enumerate(similar_examples):
            similar_examples_text += (
                f"Example {i + 1} (similarity: {example['similarity']}%):\n"
            )
            similar_examples_text += f'- Query: "{example["query"]}"\n'
            similar_examples_text += f"- Selected table: {example['table']}\n"
            similar_examples_text += f"- Reason: {example['reason']}\n"
            if example["matching_fields"]:
                similar_examples_text += (
                    f"- Matching fields: {', '.join(example['matching_fields'])}\n"
                )
            similar_examples_text += "\n"

    prompt = ChatPromptTemplate.from_template(
        """Given the following PostgreSQL tables and their contents, determine the most appropriate table for the query.

        Available PostgreSQL tables and their contents:
        {table_info}

        {value_match_info}

        {similar_examples}

        Query: {query}

        You MUST ONLY select from the PostgreSQL tables listed above.
        Analyze the fields, sample values, and unique values to determine which table would be most relevant for this query.
        Pay special attention to any value matches found, as these indicate fields containing values mentioned in the query.
        Consider the similar historical queries and their table selections as guidance, especially for highly similar queries.

        If NO table is appropriate for this query, respond with "No appropriate table found" and explain why.

        Respond in this exact format:
        table: [selected table name or "NONE" if no appropriate table]
        reason: [brief explanation of why this table is most appropriate or why no table is appropriate]
        matching_fields: [comma-separated list of fields that match the query criteria]

        Important: The table name MUST be exactly as shown in the available tables list."""
    )

    model = get_groq_llm(DEFAULT_MODEL_NAME)
    try:
        logger.debug("Invoking Groq LLM for table selection")
        response = model.invoke(
            prompt.format(
                table_info=formatted_info,
                query=query,
                value_match_info=value_match_info,
                similar_examples=similar_examples_text,
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
                if line.lower().startswith("table:"):
                    table_name = line.split(":", 1)[1].strip()
                    if table_name.lower() == "none":
                        result.error = "No appropriate table found for this query"
                        logger.info("Groq LLM found no appropriate table")
                    elif table_name in table_info:
                        result.table_name = table_name
                        logger.info(f"Groq LLM selected table: {table_name}")
                    else:
                        result.error = f"Selected table '{table_name}' not found in available tables"
                        logger.warning(f"Groq LLM selected invalid table: {table_name}")
                elif line.lower().startswith("reason:"):
                    result.reason = line.split(":", 1)[1].strip()
                elif line.lower().startswith("matching_fields:"):
                    fields_str = line.split(":", 1)[1].strip()
                    if fields_str and fields_str.lower() != "none":
                        result.matching_fields = [
                            field.strip() for field in fields_str.split(",")
                        ]

            if (
                result.table_name
                and result.matching_fields
                and result.table_name in value_matches
            ):
                result.matching_values = {}
                for field in result.matching_fields:
                    if field in value_matches[result.table_name]:
                        result.matching_values[field] = value_matches[
                            result.table_name
                        ][field]
        else:
            result.error = "Invalid response format from Groq LLM"
            logger.error("Invalid response format from Groq LLM")

    except Exception as e:
        error_msg = f"Error during table selection: {str(e)}"
        result.error = error_msg
        logger.error(error_msg, exc_info=True)

    return result


def select_table_for_query(query: str) -> str:
    """
    Select the most appropriate table for a given query.

    This function analyzes the query and available tables to determine
    which table is most likely to contain the data needed to answer
    the query. It now also uses vector similarity search to find similar
    historical queries and their selected tables.

    Args:
        query: User's analytical query

    Returns:
        Name of the selected table

    Raises:
        TableNotFoundError: If no suitable table can be found
    """
    logger.info(f"Selecting table for query: '{query}'")

    # Check for similar historical queries first via vector similarity search
    similar_examples = _get_similar_table_selections(query, n_results=1)

    # If we have a very similar query (>90% similarity), use its table directly
    if similar_examples and similar_examples[0]["similarity"] > 90:
        selected_table = similar_examples[0]["table"]
        logger.info(
            f"Using table '{selected_table}' from highly similar historical query (similarity: {similar_examples[0]['similarity']}%)"
        )
        return selected_table

    # Otherwise proceed with standard table selection logic
    if not Database.initialize():
        error_msg = "Failed to connect to PostgreSQL"
        logger.error(error_msg)
        raise TableNotFoundError(
            error_msg,
            query=query,
            available_tables=[],
        )

    table_info = _extract_table_info()
    if not table_info:
        error_msg = "No tables found in PostgreSQL database"
        logger.error(error_msg)
        raise TableNotFoundError(
            error_msg,
            query=query,
            available_tables=[],
        )

    # Match field names to query
    header_matches, best_match_by_header, matching_fields = _match_headers_to_query(
        table_info, query
    )

    # Match values to query
    value_match_dict, best_match_by_value, best_match_values = _match_values_to_query(
        table_info, query
    )

    # Compare and combine matches
    best_match, best_match_details, alternative_matches = _compare_matches(
        header_matches, value_match_dict
    )

    # If we have a clear winner with no close alternatives, return it
    if best_match and not alternative_matches:
        logger.info(f"Selected table without ambiguity: {best_match}")
        return best_match

    # If we have a best match but also alternatives, resolve the ambiguity
    if best_match and alternative_matches:
        logger.info(
            f"Resolving ambiguity between {len(alternative_matches) + 1} matches"
        )
        # First try using the heuristic approach
        selected_table, reason, matching_fields = _resolve_ambiguous_matches(
            query, table_info, best_match, best_match_details, alternative_matches
        )

        # If the heuristic approach changed the selection, it's likely worth checking with LLM
        if selected_table != best_match:
            try:
                logger.info(
                    "Ambiguity resulted in a different table selection, consulting LLM for verification"
                )
                llm_result = _select_table_with_llm(table_info, query, value_match_dict)

                if llm_result.table_name:
                    logger.info(f"LLM selected table: {llm_result.table_name}")
                    return llm_result.table_name

                # If LLM couldn't decide, stick with heuristic choice
                logger.info(
                    f"LLM could not decide, keeping heuristic selection: {selected_table}"
                )
            except Exception as e:
                logger.warning(
                    f"Error using LLM for verification: {e}. Using heuristic selection."
                )

        logger.info(f"Selected table after resolving ambiguity: {selected_table}")
        return selected_table

    # If no matches were found at all, try using LLM
    if not best_match:
        logger.info("No matching tables found, asking Groq LLM to help")
        try:
            llm_result = _select_table_with_llm(table_info, query, value_match_dict)
            if llm_result.table_name:
                logger.info(f"Groq LLM selected table: {llm_result.table_name}")
                return llm_result.table_name
        except Exception as e:
            logger.error(f"Error using LLM to select table: {e}")

    # Fall back to first available table if needed
    available_tables = list(table_info.keys())
    if available_tables:
        logger.warning(
            f"No match found, falling back to first table: {available_tables[0]}"
        )
        return available_tables[0]

    # If no tables at all, raise exception
    error_msg = "No matching table found for this query. The query terms don't match any field names or values in the available tables."
    logger.error(error_msg)
    raise TableNotFoundError(
        error_msg,
        query=query,
        available_tables=[],
    )
