#!/usr/bin/env python
"""
Table Processor Module

This module provides functionality for processing PostgreSQL tables directly with SQL
based on user queries. It uses a Groq LLM to generate SQL commands for data
manipulation and executes them against the database.

Key components:
- Metadata extraction from database tables
- LLM-based SQL command generation
- Safe SQL execution
- Error handling and SQL correction
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

import psycopg2
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate

from mypackage.utils.database import Database, execute_sql, query_to_dict
from mypackage.utils.llm_config import COLLECTION_PROCESSOR_MODEL, get_groq_llm

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

logger.debug("table_processor module initialized")


def _get_table_metadata(table_name: str) -> Dict:
    """
    Extract table metadata including column information and statistics.

    This function analyzes a PostgreSQL table and extracts useful metadata,
    including column names, data types, constraints, and sample data.

    Args:
        table_name: The name of the PostgreSQL table to analyze

    Returns:
        Dictionary containing table metadata with keys:
        - columns: List of column details (name, type, nullable)
        - constraints: Primary key, foreign keys, and other constraints
        - sample_data: Sample rows from the table
        - statistics: Column statistics (count, distinct, etc.)
    """
    logger.info(f"Extracting metadata from table: {table_name}")

    if not Database.initialize():
        logger.error("Failed to initialize database connection")
        return {}

    metadata = {
        "columns": [],
        "constraints": {},
        "sample_data": [],
        "statistics": {},
    }

    try:
        # Get column information
        column_sql = """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position
        """
        columns = query_to_dict(column_sql, (table_name,))
        metadata["columns"] = columns
        column_names = [col["column_name"] for col in columns]

        # Get primary key
        pk_sql = """
        SELECT c.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.constraint_column_usage AS ccu USING (constraint_schema, constraint_name)
        JOIN information_schema.columns AS c ON c.table_schema = tc.constraint_schema
            AND tc.table_name = c.table_name AND ccu.column_name = c.column_name
        WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_name = %s
        """
        primary_keys = query_to_dict(pk_sql, (table_name,))
        metadata["constraints"]["primary_key"] = [
            pk["column_name"] for pk in primary_keys
        ]

        for col in column_names:
            col_stats_sql = f"""
            SELECT 
                COUNT(*) as total_count,
                COUNT(DISTINCT "{col}") as distinct_count,
                MIN("{col}") as min_value,
                MAX("{col}") as max_value
            FROM {table_name}
            """
            try:
                stats = query_to_dict(col_stats_sql, ())[0]
                metadata["statistics"][col] = stats
            except Exception as e:
                logger.warning(f"Could not get statistics for column {col}: {str(e)}")
                metadata["statistics"][col] = {"error": str(e)}

        # Get sample data (10 rows)
        sample_sql = f"SELECT * FROM {table_name} LIMIT 10"
        metadata["sample_data"] = query_to_dict(sample_sql, ())

        logger.info(f"Metadata extraction complete: {len(metadata['columns'])} columns")
        return metadata

    except Exception as e:
        logger.error(f"Error extracting table metadata: {str(e)}", exc_info=True)
        return {"error": str(e)}


def _extract_sql_commands(response: str) -> List[str]:
    """
    Extract SQL commands from a markdown-formatted LLM response.

    Args:
        response: The raw text response from the LLM

    Returns:
        List of SQL commands to execute

    Raises:
        ValueError: If the response doesn't contain valid SQL commands
    """
    logger.debug("Extracting SQL commands from LLM response")

    if not response or not isinstance(response, str):
        error_msg = f"Invalid LLM response: {type(response)} - {str(response)[:200]}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Try to extract SQL from markdown code blocks
    sql_pattern = re.compile(r"```(?:sql)?\n(.*?)\n```", re.DOTALL)
    matches = sql_pattern.findall(response)

    if not matches:
        # If no code blocks found, look for SQL commands directly
        logger.warning("No SQL code blocks found, looking for SQL commands directly")
        # Look for statements ending with semicolons
        statements = re.findall(
            r"(?:SELECT|UPDATE|INSERT|DELETE|CREATE|ALTER|DROP|WITH)[^;]*;",
            response,
            re.IGNORECASE | re.DOTALL,
        )
        if statements:
            return [stmt.strip() for stmt in statements]

        logger.error(
            f"No SQL commands found in response. Full response:\n{response[:500]}"
        )
        raise ValueError("LLM response didn't contain valid SQL commands")

    # Extract and clean SQL commands from matches
    sql_commands = []
    for match in matches:
        # Split multiple commands by semicolons
        commands = [cmd.strip() for cmd in match.split(";") if cmd.strip()]
        sql_commands.extend([f"{cmd};" for cmd in commands])

    logger.debug(f"Successfully extracted {len(sql_commands)} SQL commands")
    return sql_commands


def _generate_sql_commands(query: str, metadata: Dict) -> List[str]:
    """
    Generate SQL commands using Groq LLM based on the user query.

    This function formulates a prompt that includes table metadata and the
    user query, sends it to the LLM, and extracts the generated SQL commands.

    Args:
        query: The user's query describing the desired data transformation
        metadata: Dictionary of table metadata from _get_table_metadata()

    Returns:
        List of SQL commands to execute

    Raises:
        ValueError: If the LLM response doesn't contain valid SQL commands
    """
    logger.info(f"Generating SQL commands for query: '{query}'")

    # Format column information for the prompt
    column_info = "\n".join(
        [
            f"- {col['column_name']}: {col['data_type']}, {'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'}"
            for col in metadata["columns"]
        ]
    )

    # Format sample data for the prompt
    sample_rows = []
    if metadata["sample_data"]:
        for row in metadata["sample_data"][:5]:  # Limit to 5 rows for readability
            sample_rows.append(str(row))
    sample_data = "\n".join(sample_rows)

    # Format statistics for the prompt
    stats_info = []
    for col, stats in metadata["statistics"].items():
        if "error" not in stats:
            stats_info.append(
                f"- {col}: total={stats.get('total_count', 'N/A')}, distinct={stats.get('distinct_count', 'N/A')}, min={stats.get('min_value', 'N/A')}, max={stats.get('max_value', 'N/A')}"
            )
    statistics = "\n".join(stats_info)

    # Create prompt template with detailed instructions
    prompt_template = ChatPromptTemplate.from_template(
        """You are a PostgreSQL expert working with this table:

Table structure:
{column_info}

Primary key: {primary_keys}

Column statistics:
{statistics}

Sample data:
{sample_data}

Write SQL commands to process the table according to this query:
"{query}"

Rules:
1. Use standard PostgreSQL syntax (version 12+)
2. Prefer clean, efficient SQL over complex solutions
3. Always use double quotes around identifiers with special characters or mixed case
4. Explain complex SQL with inline comments
5. Use CTEs (WITH clauses) for better readability when appropriate
6. The solution might require multiple SQL statements to achieve the desired result
7. Always return readable results with appropriate column names

Examples of good responses:
---
Query: "Filter active users and sort by registration date"
SQL:
```sql
SELECT * 
FROM users
WHERE status = 'active'
ORDER BY registration_date;
```

---
Query: "Calculate average revenue by product category"
SQL:
```sql
SELECT 
    category,
    AVG(revenue) as average_revenue
FROM products
GROUP BY category
ORDER BY average_revenue DESC;
```

Now generate SQL commands for this query:"""
    )

    # Format prompt with metadata
    prompt = prompt_template.format(
        query=query,
        column_info=column_info,
        primary_keys=", ".join(metadata["constraints"].get("primary_key", ["None"])),
        statistics=statistics,
        sample_data=sample_data,
    )

    logger.debug("Prompt prepared for LLM SQL generation")
    logger.info("Sending prompt to Groq LLM for SQL generation")

    # Get response from LLM
    generated_response = get_groq_llm(COLLECTION_PROCESSOR_MODEL).invoke(prompt)
    logger.debug("Received response from Groq LLM")

    if isinstance(generated_response, AIMessage):
        generated_response = generated_response.content

    # Extract SQL commands from response
    sql_commands = _extract_sql_commands(generated_response)

    logger.info(f"SQL generation complete: {len(sql_commands)} commands")
    for i, cmd in enumerate(sql_commands):
        logger.debug(f"Command {i + 1}: {cmd}")

    return sql_commands


def _execute_sql_safe(
    sql_commands: List[str], table_name: str
) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """
    Execute generated SQL commands safely.

    Args:
        sql_commands: List of SQL commands to execute
        table_name: The original table name (for context in error messages)

    Returns:
        Tuple containing:
        - List of results from each command
        - Error message (if any)
    """
    logger.info(f"Executing {len(sql_commands)} SQL commands on table {table_name}")
    results = []

    try:
        if not Database.initialize():
            raise ValueError("Failed to initialize database connection")

        # Execute each command in sequence
        for i, command in enumerate(sql_commands):
            logger.debug(f"Executing command {i + 1}: {command}")

            if command.strip().upper().startswith(("SELECT", "WITH")):
                # For queries, return the results
                result = query_to_dict(command, ())
                results.append(result)
                logger.info(f"Query returned {len(result)} rows")
            else:
                # For other statements (UPDATE, INSERT, etc.)
                rowcount = execute_sql(command)
                results.append({"affected_rows": rowcount})
                logger.info(f"Command affected {rowcount} rows")

        logger.info("All SQL commands executed successfully")
        return results, None

    except (psycopg2.Error, ValueError) as e:
        error_msg = f"SQL execution error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return results, error_msg


def _correct_sql(
    error: str, sql_commands: List[str], query: str, metadata: Dict
) -> List[str]:
    """
    Generate corrected SQL commands when initial execution fails.

    This function sends the original commands, error message, and metadata to the LLM
    to generate corrected versions that avoid the error.

    Args:
        error: The error message from the failed execution
        sql_commands: The original SQL commands that failed
        query: The original user query
        metadata: Dictionary of table metadata

    Returns:
        Corrected SQL commands
    """
    logger.info(f"Attempting to correct SQL commands with error: {error}")

    # Format column information for the correction prompt
    column_info = "\n".join(
        [
            f"- {col['column_name']}: {col['data_type']}, {'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'}"
            for col in metadata["columns"]
        ]
    )

    # Create correction prompt with error details
    correction_prompt = f"""Fix these PostgreSQL commands based on the error:

Original query: "{query}"

Table structure:
{column_info}

Error:
{error}

Faulty SQL commands:
```sql
{chr(10).join(sql_commands)}
```

Create corrected SQL commands that address the error.
Return ONLY the corrected SQL commands in code blocks:
```sql
-- Your corrected SQL here
```
"""

    logger.debug("Sending correction prompt to Groq LLM")
    corrected_response = get_groq_llm(COLLECTION_PROCESSOR_MODEL).invoke(
        correction_prompt
    )

    if isinstance(corrected_response, AIMessage):
        corrected_response = corrected_response.content

    # Extract the corrected SQL commands
    corrected_commands = _extract_sql_commands(corrected_response)
    logger.info(f"SQL correction complete: {len(corrected_commands)} commands")

    for i, cmd in enumerate(corrected_commands):
        logger.debug(f"Corrected command {i + 1}: {cmd}")

    return corrected_commands


def _execute_with_retries(
    initial_commands: List[str],
    table_name: str,
    query: str,
    metadata: Dict,
    max_retries: int = 3,
) -> List[Dict[str, Any]]:
    """
    Execute SQL commands with automatic error correction and retries.

    This function attempts to execute the generated SQL commands and, if they fail,
    uses the LLM to correct them and retry up to max_retries times.

    Args:
        initial_commands: The initial SQL commands to execute
        table_name: The name of the table
        query: The original user query
        metadata: Dictionary of table metadata
        max_retries: Maximum number of retry attempts

    Returns:
        Results from SQL execution (or empty list if all attempts fail)
    """
    logger.info(f"Executing SQL commands with up to {max_retries} retries")

    commands = initial_commands
    for attempt in range(max_retries):
        logger.debug(f"Execution attempt {attempt + 1}/{max_retries}")
        results, error = _execute_sql_safe(commands, table_name)

        if error is None:
            # Success
            logger.info(f"Execution succeeded on attempt {attempt + 1}")
            return results

        logger.warning(f"Attempt {attempt + 1} failed with error: {error}")

        if attempt < max_retries - 1:
            # Try to correct the SQL for next attempt
            logger.info("Requesting SQL correction from LLM")
            commands = _correct_sql(error, commands, query, metadata)

    # All attempts failed
    logger.error(
        f"All {max_retries} execution attempts failed, returning empty results"
    )
    return []


def process_table_query(table_name: str, query: str) -> List[Dict[str, Any]]:
    """
    Main function to process a table based on a user query.

    This function:
    1. Extracts table metadata
    2. Generates SQL commands using an LLM
    3. Executes the commands with retries
    4. Returns the results

    Args:
        table_name: Name of the PostgreSQL table to process
        query: The user's query describing the desired data transformation

    Returns:
        Results from SQL execution

    Raises:
        ValueError: If the table cannot be found or accessed
    """
    logger.info(f"Processing query '{query}' on table '{table_name}'")

    try:
        # Step 1: Extract table metadata
        logger.debug(f"Extracting metadata for table: {table_name}")
        metadata = _get_table_metadata(table_name)

        if not metadata or "error" in metadata:
            error_msg = f"Failed to get metadata for table '{table_name}': {metadata.get('error', 'Unknown error')}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Step 2: Generate SQL commands using LLM
        sql_commands = _generate_sql_commands(query, metadata)

        # Step 3: Execute commands with retries
        results = _execute_with_retries(sql_commands, table_name, query, metadata)

        logger.info(f"Query processing complete, returning {len(results)} result sets")
        return results

    except Exception as e:
        logger.error(f"Error processing table query: {str(e)}", exc_info=True)
        raise ValueError(f"Error processing table: {str(e)}")


if __name__ == "__main__":
    # Set up console logging for direct script execution
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Set to DEBUG for more detailed logging
    root_logger.addHandler(console_handler)

    # Test with a sample table and query
    test_table = "sales"
    test_query = "Calculate monthly revenue by product category in 2023 and show top 3 categories"

    logger.info(f"Testing with table '{test_table}' and query '{test_query}'")

    try:
        results = process_table_query(test_table, test_query)
        logger.info(f"Test successful, returned {len(results)} result sets")
        if results:
            for i, result in enumerate(results):
                if isinstance(result, list) and result:
                    logger.info(f"Result set {i + 1} contains {len(result)} rows")
                    logger.info(f"Preview: {result[:3]}")
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
