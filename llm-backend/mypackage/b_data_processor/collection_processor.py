#!/usr/bin/env python
"""
Collection Processor Module

This module provides functionality for processing collections from a database
based on user queries. It uses a Groq LLM to generate pandas code for data
transformation and executes the code in a sandboxed environment.

Key components:
- Metadata extraction from pandas DataFrames
- LLM-based code generation for data processing
- Safe code execution in a sandboxed environment
- Error handling and code correction
"""

import logging
import re
from typing import Dict, Optional, Tuple

import pandas as pd
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_experimental.utilities import PythonREPL
from pandas.api.types import is_numeric_dtype, is_string_dtype

from mypackage.utils.database import Database
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

logger.debug("collection_processor module initialized")

# Initialize Python REPL for code execution
python_repl = PythonREPL()


def _get_column_metadata(df: pd.DataFrame) -> Dict:
    """
    Extract column metadata including unique values and statistics.

    This function analyzes a DataFrame and extracts useful metadata for each column,
    including data types, unique values for string columns, and statistical information
    for numeric columns.

    Args:
        df: The pandas DataFrame to analyze

    Returns:
        Dictionary containing column metadata with keys:
        - columns: List of column names
        - dtypes: Column data types
        - unique_values: Dictionary of unique values for string columns
        - numeric_stats: Dictionary of statistics for numeric columns
    """
    logger.info(f"Extracting column metadata from DataFrame with shape {df.shape}")
    if df.empty:
        logger.warning("DataFrame is empty, returning empty metadata")
        return {}

    metadata = {
        "columns": list(df.columns),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "unique_values": {},
        "numeric_stats": {},
    }

    # Process each column to extract appropriate metadata
    for col in df.columns:
        logger.debug(f"Processing metadata for column: '{col}'")

        if is_string_dtype(df[col]):
            # Handle NaN values before getting unique values
            clean_series = df[col].dropna()
            unique_values = clean_series.unique().tolist()
            metadata["unique_values"][col] = unique_values
            logger.debug(f"Column '{col}': {len(unique_values)} unique string values")

        elif is_numeric_dtype(df[col]):
            stats = {
                "min": df[col].min(),
                "max": df[col].max(),
                "mean": df[col].mean(),
                "median": df[col].median(),
                "std": df[col].std(),
                "null_count": df[col].isnull().sum(),
            }
            metadata["numeric_stats"][col] = stats
            logger.debug(f"Column '{col}': numeric stats extracted")

    logger.info(
        f"Metadata extraction complete: {len(metadata['columns'])} columns processed"
    )
    return metadata


def _extract_code_block(response: str) -> str:
    """
    Extract Python code block from a markdown-formatted LLM response.

    Args:
        response: The raw text response from the LLM

    Returns:
        Extracted Python code as a string

    Raises:
        ValueError: If the response doesn't contain a valid code block
    """
    logger.debug("Extracting code block from LLM response")

    if not response or not isinstance(response, str):
        error_msg = f"Invalid LLM response: {type(response)} - {str(response)[:200]}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    code_pattern = re.compile(
        r"```(?:python)?\n(.*?)\n```", re.DOTALL
    )  # Flexible pattern to match code blocks
    match = code_pattern.search(response)

    if not match:
        logger.error(
            f"No code block found in response. Full response:\n{response[:500]}"
        )
        raise ValueError("LLM response didn't contain valid code block")

    extracted_code = match.group(1).strip()
    logger.debug(f"Successfully extracted code block ({len(extracted_code)} chars)")
    return extracted_code


def _generate_processing_code(query: str, metadata: Dict) -> str:
    """
    Generate pandas processing code using Groq LLM based on the user query.

    This function formulates a prompt that includes DataFrame metadata and the
    user query, sends it to the LLM, and extracts the generated Python code.

    Args:
        query: The user's query describing the desired data transformation
        metadata: Dictionary of DataFrame metadata from _get_column_metadata()

    Returns:
        Generated Python code as a string

    Raises:
        ValueError: If the LLM response doesn't contain a valid code block
    """
    logger.info(f"Generating processing code for query: '{query}'")

    # Create prompt template with detailed instructions
    prompt_template = ChatPromptTemplate.from_template(
        """You are a pandas expert working with this dataset:
- Columns: {columns}
- Data types: {dtypes}
- Unique values (string columns): {unique_values}
- Numeric statistics: {numeric_stats}

Write Python code to process the DataFrame according to this query:
"{query}"

Rules:
1. Use only pandas/numpy operations
2. Preserve original columns unless explicitly asked to modify
3. Handle null values appropriately
4. Return the result as `result_df`
5. Never modify the DataFrame in-place
6. Provide ONLY the code without any explanations or text outside the code block

Examples of good responses:
---
Query: "Filter active users and sort by registration date"
Code:
```python
import pandas as pd
import numpy as np

def process_data(df: pd.DataFrame) -> pd.DataFrame:
    processed_df = df.copy()
    processed_df = processed_df[processed_df['status'] == 'active']
    processed_df = processed_df.sort_values('registration_date')
    result_df = processed_df
    return result_df
```

---
Query: "Calculate average revenue by product category"
Code:
```python
import pandas as pd
import numpy as np

def process_data(df: pd.DataFrame) -> pd.DataFrame:
    processed_df = df.copy()
    result_df = processed_df.groupby('category')['revenue'].mean().reset_index()
    return result_df
```

Now generate the code for this query:"""
    )

    # Format prompt with metadata
    prompt = prompt_template.format(
        query=query,
        columns=metadata["columns"],
        dtypes=metadata["dtypes"],
        unique_values=metadata["unique_values"],
        numeric_stats=metadata["numeric_stats"],
    )

    logger.debug("Prompt prepared for LLM code generation")
    logger.info("Sending prompt to Groq LLM for code generation")

    # Get response from LLM
    generated_response = get_groq_llm(COLLECTION_PROCESSOR_MODEL).invoke(prompt)
    logger.debug("Received response from Groq LLM")

    if isinstance(generated_response, AIMessage):
        generated_response = generated_response.content

    # Extract code block from response
    generated_code = _extract_code_block(generated_response)

    logger.info("Code generation complete")
    logger.debug(f"Generated code:\n{generated_code}")
    return generated_code


def _execute_code_safe(
    code: str, df: pd.DataFrame
) -> Tuple[pd.DataFrame, Optional[str]]:
    """
    Execute generated code using a restricted PythonREPL for safety.

    This function runs the generated code in a sandboxed environment with
    limited capabilities to prevent security issues.

    Args:
        code: The Python code to execute
        df: The DataFrame to process

    Returns:
        Tuple containing:
        - Processed DataFrame (or original if execution failed)
        - Error message if execution failed, None otherwise
    """
    logger.info(f"Executing code on DataFrame with shape {df.shape}")
    try:
        logger.debug("Setting up safe execution environment")
        # Add datetime support to safe globals

        # Prepare full code with DataFrame setup and safety measures
        logger.debug("Preparing code for execution")
        full_code = (
            "import pandas as pd\n"
            "from pandas import Timestamp\n"
            "import numpy as np\n"
            f"df = pd.DataFrame({df.to_dict('list')})\n"
            f"{PythonREPL.sanitize_input(code)}\n"
            "result_df = process_data(df)\n"
            "# Convert Timestamps to strings for CSV\n"
            "csv_df = result_df.copy()\n"
            "for col in csv_df.select_dtypes(include=['datetime']):\n"
            "    csv_df[col] = csv_df[col].astype(str)\n"
            "print(csv_df.to_csv(index=False))"
        )

        print("\n", code, "\n")

        # Execute code with timeout for safety
        logger.debug("Executing code with 30-second timeout")
        output = python_repl.run(full_code, timeout=30)

        # Check for error messages in output
        if "Traceback (most recent call last):" in output:
            error = output.split("\n")[-1].strip()
            logger.warning(f"Code execution failed: {error}")
            return df, f"Execution error: {error}"

        # Convert CSV output back to DataFrame
        logger.debug("Processing execution output")
        from io import StringIO

        result_df = pd.read_csv(StringIO(output))
        logger.info(
            f"Code executed successfully, returned DataFrame with shape {result_df.shape}"
        )
        return result_df, None

    except Exception as e:
        logger.error(f"REPL error during code execution: {str(e)}", exc_info=True)
        return df, f"REPL error: {str(e)}"


def _correct_code(error: str, code: str, query: str, metadata: Dict) -> str:
    """
    Generate corrected code when initial execution fails.

    This function sends the original code, error message, and metadata to the LLM
    to generate a corrected version that avoids the error.

    Args:
        error: The error message from the failed execution
        code: The original code that failed
        query: The original user query
        metadata: Dictionary of DataFrame metadata

    Returns:
        Corrected Python code as a string
    """
    logger.info(f"Attempting to correct code with error: {error}")

    # Create correction prompt with error details
    correction_prompt = f"""Fix this Python code based on the error:

Original query: "{query}"
Dataset columns: {metadata["columns"]}
Data types: {metadata["dtypes"]}

Error:
{error}

Faulty code:
{code}

Create a corrected version of the function that addresses the error.
Return ONLY the corrected code in a code block:
```python
# Your corrected code here
```
"""

    logger.debug("Sending correction prompt to Groq LLM")
    corrected_response = get_groq_llm(COLLECTION_PROCESSOR_MODEL).invoke(
        correction_prompt
    )

    if isinstance(corrected_response, AIMessage):
        corrected_response = corrected_response.content

    # Extract the corrected code
    corrected_code = _extract_code_block(corrected_response)
    logger.info("Code correction complete")
    logger.debug(f"Corrected code:\n{corrected_code}")

    return corrected_code


def _execute_with_retries(
    initial_code: str,
    df: pd.DataFrame,
    query: str,
    metadata: Dict,
    max_retries: int = 5,
) -> pd.DataFrame:
    """
    Execute code with automatic error correction and retries.

    This function attempts to execute the generated code and, if it fails,
    uses the LLM to correct the code and retry up to max_retries times.

    Args:
        initial_code: The initial Python code to execute
        df: The DataFrame to process
        query: The original user query
        metadata: Dictionary of DataFrame metadata
        max_retries: Maximum number of retry attempts

    Returns:
        Processed DataFrame (or original if all attempts fail)
    """
    logger.info(f"Executing code with up to {max_retries} retries")

    code = initial_code
    for attempt in range(max_retries):
        logger.debug(f"Execution attempt {attempt + 1}/{max_retries}")
        result_df, error = _execute_code_safe(code, df)

        if error is None:
            # Success
            logger.info(f"Execution succeeded on attempt {attempt + 1}")
            return result_df

        logger.warning(f"Attempt {attempt + 1} failed with error: {error}")

        if attempt < max_retries - 1:
            # Try to correct the code for next attempt
            logger.info("Requesting code correction from LLM")
            code = _correct_code(error, code, query, metadata)

    # All attempts failed
    logger.error(
        f"All {max_retries} execution attempts failed, returning original DataFrame"
    )
    return df


def process_collection_query(collection_name: str, query: str) -> pd.DataFrame:
    """
    Main function to process a collection based on a user query.

    This function:
    1. Retrieves the collection from MongoDB
    2. Converts it to a pandas DataFrame
    3. Extracts metadata
    4. Generates processing code using an LLM
    5. Executes the code with retries
    6. Returns the processed DataFrame

    Args:
        collection_name: Name of the MongoDB collection to process
        query: The user's query describing the desired data transformation

    Returns:
        Processed pandas DataFrame

    Raises:
        ValueError: If the collection cannot be found or accessed
    """
    logger.info(f"Processing query '{query}' on collection '{collection_name}'")

    try:
        # Step 1: Retrieve collection from database
        logger.debug(f"Connecting to database for collection: {collection_name}")
        if Database.db is None:
            logger.debug("Database connection not initialized, initializing now")
            Database.initialize()

        collection = Database.db[collection_name]
        logger.debug(f"Successfully connected to collection '{collection_name}'")

        # Step 2: Convert collection to DataFrame
        df = pd.DataFrame(list(collection.find({}, {"_id": 0})))
        logger.info(f"Converted collection to DataFrame with shape {df.shape}")

        if df.empty:
            logger.warning(f"Collection '{collection_name}' is empty")
            return df

        # Step 3: Extract metadata for code generation
        metadata = _get_column_metadata(df)

        # Step 4: Generate processing code using LLM
        code = _generate_processing_code(query, metadata)

        # Step 5: Execute code with retries
        result_df = _execute_with_retries(code, df, query, metadata)

        logger.info(
            f"Query processing complete, returning DataFrame with shape {result_df.shape}"
        )
        return result_df

    except Exception as e:
        logger.error(f"Error processing collection query: {str(e)}", exc_info=True)
        raise ValueError(f"Error processing collection: {str(e)}")


if __name__ == "__main__":
    # Set up console logging for direct script execution
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Set to DEBUG for more detailed logging
    root_logger.addHandler(console_handler)

    # Test with a sample collection and query
    test_collection = "campaign_performance"
    test_query = "Calculate average revenue by channel and sort by descending revenue"

    logger.info(f"Testing with collection '{test_collection}' and query '{test_query}'")

    try:
        result = process_collection_query(test_collection, test_query)
        logger.info(f"Test successful, result shape: {result.shape}")
        logger.info(f"Result preview:\n{result.head().to_string()}")
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
