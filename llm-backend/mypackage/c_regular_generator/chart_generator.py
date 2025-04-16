#!/usr/bin/env python
"""
Chart Generator Module

This module provides functionality for generating data visualizations based on user queries
and DataFrame content. It uses LLM to generate complete Python code for the visualization
and executes it using PythonREPL.

Key components:
- Converting DataFrame metadata to a format usable by the LLM
- LLM-based generation of complete Python plotting code
- Execution of that code using PythonREPL with automatic error correction and retries
- Return of the generated visualization to the frontend
"""

import logging
from io import BytesIO, StringIO
import json
from typing import Dict, List, Any, Optional, Tuple

import pandas as pd
import numpy as np
from langchain_core.prompts import ChatPromptTemplate
from langchain_experimental.utilities import PythonREPL
from pydantic import BaseModel

from mypackage.utils.llm_config import CHART_DATA_MODEL, get_groq_llm

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

logger.debug("chart_generator module initialized")


class DataFramePreview(BaseModel):
    """
    Pydantic model for DataFrame preview information to be sent to the LLM.

    Attributes:
        columns: List of column names in the DataFrame
        dtypes: Dictionary mapping column names to their data types
        sample_rows: List of dictionaries representing the first few rows
        shape: Tuple of (rows, columns) describing the DataFrame shape
    """

    columns: List[str]
    dtypes: Dict[str, str]
    sample_rows: List[Dict[str, Any]]
    shape: tuple


def prepare_dataframe_preview(df: pd.DataFrame, max_rows: int = 5) -> DataFramePreview:
    """
    Prepare a preview of the DataFrame for the LLM prompt.

    Args:
        df: The pandas DataFrame to preview
        max_rows: Maximum number of sample rows to include

    Returns:
        DataFramePreview object containing structured preview data
    """
    logger.info(f"Preparing DataFrame preview with shape {df.shape}")

    # Get column names and dtypes
    columns = df.columns.tolist()
    dtypes = {col: str(df[col].dtype) for col in columns}

    # Convert sample rows to list of dicts for JSON serialization
    # Handle NaN, dates, and other special values
    sample_df = df.head(max_rows).copy()
    sample_rows = []

    for _, row in sample_df.iterrows():
        row_dict = {}
        for col in columns:
            value = row[col]
            if pd.isna(value):
                row_dict[col] = None
            elif isinstance(value, (pd.Timestamp, pd.Period)):
                row_dict[col] = str(value)
            elif isinstance(value, (np.int64, np.float64)):
                row_dict[col] = (
                    float(value)
                    if np.isnan(float(value))
                    else int(value)
                    if value.is_integer()
                    else float(value)
                )
            else:
                row_dict[col] = str(value)
        sample_rows.append(row_dict)

    logger.debug(f"Created preview with {len(sample_rows)} sample rows")

    return DataFramePreview(
        columns=columns, dtypes=dtypes, sample_rows=sample_rows, shape=df.shape
    )


def generate_plot_code(query: str, df_preview: DataFramePreview) -> str:
    """
    Generate matplotlib/seaborn plotting code based on the user query and DataFrame preview.

    Args:
        query: The user's query about what visualization they want
        df_preview: Preview data about the DataFrame

    Returns:
        String containing Python code to generate the requested visualization

    Raises:
        ValueError: If the LLM fails to generate valid Python code
    """
    logger.info(f"Generating plot code for query: {query}")

    # Convert DataFrame preview to a readable format for the prompt
    columns_info = "\n".join(
        [f"- {col} ({df_preview.dtypes[col]})" for col in df_preview.columns]
    )

    # Format sample rows as a pretty table for the prompt
    sample_rows_str = json.dumps(df_preview.sample_rows, indent=2)

    # Define the prompt template for the LLM
    prompt_template = ChatPromptTemplate.from_template(
        """You are a data visualization expert. Your task is to generate Python code that creates a visualization 
        based on the user's request and the provided DataFrame information.

        User Query: {query}

        DataFrame Information:
        - Shape: {shape}
        - Columns:
        {columns_info}
        
        Sample Data (first {sample_count} rows):
        {sample_rows}

        INSTRUCTIONS:
        1. Generate complete, executable Python code that:
           - Creates the visualization requested by the user
           - Uses matplotlib, seaborn, or plotly (prefer matplotlib/seaborn)
           - Handles any necessary data transformations
           - Includes proper styling, labels, and title
           - Saves the figure to a BytesIO object as PNG
           - IMPORTANT: Rotates all x-axis labels by 45 degrees
           - IMPORTANT: Sets the figure size to 8x6 inches (figsize=(8, 6))
        2. Your code MUST:
           - Define a function called `create_plot()` that takes a pandas DataFrame as input and returns the image bytes
           - NOT print anything except through logging
           - NOT show the plot (use savefig instead of plt.show())
           - Handle edge cases and possible errors
           - Have proper formatting for dates if applicable
           - Use colors that are visually appealing and accessible
           - Return the BytesIO object containing the PNG bytes
        3. Choose the most appropriate chart type based on the query
        4. ONLY output valid, runnable Python code (no explanations, no markdown)
        5. DO NOT include code fence markers (```) in your response

        Output ONLY the Python code with no additional text or explanations.
        """
    )

    # Prepare and send the prompt to the LLM
    logger.debug("Preparing prompt for Groq LLM")
    model = get_groq_llm(CHART_DATA_MODEL)
    chain = prompt_template | model

    logger.debug("Sending prompt to Groq LLM")
    response = chain.invoke(
        {
            "query": query,
            "shape": df_preview.shape,
            "columns_info": columns_info,
            "sample_count": len(df_preview.sample_rows),
            "sample_rows": sample_rows_str,
        }
    )

    generated_code = response.content.strip()
    logger.debug(f"Received generated code from LLM (length: {len(generated_code)})")

    # Remove markdown code fence markers if present
    generated_code = _clean_code_from_llm(generated_code)

    # Validate the code contains the required function
    if "def create_plot" not in generated_code:
        error_msg = (
            "Generated code does not contain the required create_plot() function"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Print the generated code
    print("\n==== GENERATED VISUALIZATION CODE ====")
    print(generated_code)
    print("=====================================\n")

    return generated_code


def _clean_code_from_llm(code: str) -> str:
    """
    Clean code generated by LLM to remove markdown formatting or other non-code elements.

    Args:
        code: The raw code string from the LLM

    Returns:
        Cleaned code ready for execution
    """
    # Remove markdown code fence markers if present
    code = code.strip()

    # Check if code is wrapped in code fence markers
    if code.startswith("```") and code.endswith("```"):
        # Remove the opening and closing markers
        code = code[3:-3].strip()

        # If there's a language identifier (like ```python), remove it too
        lines = code.split("\n")
        if not lines[0].strip() or lines[0].strip().lower() in ["python", "py"]:
            code = "\n".join(lines[1:])

    # Sometimes only opening marker is present
    elif code.startswith("```"):
        lines = code.split("\n")
        # Remove the first line which contains the marker
        code = "\n".join(lines[1:])

        # If there's a closing marker at the end, remove it
        if code.endswith("```"):
            code = code[:-3].strip()

    return code


def execute_plot_code(
    code: str, df: pd.DataFrame
) -> Tuple[Optional[bytes], Optional[str]]:
    """
    Execute the generated plot code.

    Args:
        code: Python code string to execute
        df: The pandas DataFrame to use for plotting

    Returns:
        Tuple of (image_bytes, error_message):
        - image_bytes: PNG image bytes if successful, None if failed
        - error_message: Error message if failed, None if successful
    """
    logger.info("Executing generated plot code")

    try:
        # Set up the execution namespace
        namespace = {
            "pd": pd,
            "np": np,
            "df": df.copy(),
            "BytesIO": BytesIO,
            "plt": __import__("matplotlib.pyplot"),
            "sns": __import__("seaborn"),
        }

        # First, execute the code that defines the function
        logger.debug("Defining the create_plot function")
        exec(code, namespace)

        # Then, execute the function with our DataFrame
        logger.debug("Calling create_plot() with the DataFrame")
        exec("image_bytes = create_plot(df)", namespace)

        # Extract the image bytes from the namespace
        if "image_bytes" not in namespace:
            error_msg = "create_plot() did not define 'image_bytes' variable"
            logger.error(error_msg)
            return None, error_msg

        image_bytes = namespace["image_bytes"]

        # Validate the result is a BytesIO object or bytes
        if not isinstance(image_bytes, (BytesIO, bytes)):
            error_msg = f"Expected create_plot() to return BytesIO or bytes, got {type(image_bytes)}"
            logger.error(error_msg)
            return None, error_msg

        # Convert to bytes if it's BytesIO
        if isinstance(image_bytes, BytesIO):
            image_bytes.seek(0)
            image_bytes = image_bytes.getvalue()

        logger.info(
            f"Successfully executed plot code, generated {len(image_bytes)} bytes"
        )
        return image_bytes, None

    except Exception as e:
        logger.error(f"Error executing plot code: {str(e)}", exc_info=True)
        return None, f"Execution error: {str(e)}"


def correct_plot_code(
    error: str, code: str, query: str, df_preview: DataFramePreview
) -> str:
    """
    Generate corrected plotting code when initial execution fails.

    Args:
        error: The error message from the failed execution
        code: The original code that failed
        query: The original user query
        df_preview: Preview data about the DataFrame

    Returns:
        Corrected Python code as a string
    """
    logger.info(f"Attempting to correct plot code with error: {error}")

    # Convert DataFrame preview to a readable format for the prompt
    columns_info = "\n".join(
        [f"- {col} ({df_preview.dtypes[col]})" for col in df_preview.columns]
    )

    # Format sample rows as a pretty table for the prompt
    sample_rows_str = json.dumps(df_preview.sample_rows, indent=2)

    # Create correction prompt with error details
    correction_prompt = ChatPromptTemplate.from_template(
        """You are a data visualization expert. Your task is to fix Python code that failed to generate a visualization.

        The code was attempting to create a visualization based on this query:
        "{query}"
        
        DataFrame Information:
        - Shape: {shape}
        - Columns:
        {columns_info}
        
        Sample Data (first {sample_count} rows):
        {sample_rows}
        
        The code failed with this error:
        {error}
        
        Here is the faulty code:
        ```python
        {code}
        ```
        
        INSTRUCTIONS:
        1. Fix the code to address the specific error
        2. Your fixed code MUST:
           - Define a function called `create_plot()` that takes a pandas DataFrame as input
           - Return a BytesIO object containing the PNG image bytes
           - Handle edge cases properly
           - Include appropriate error handling
           - NOT print anything except through logging
           - NOT show the plot (use savefig instead of plt.show())
           - IMPORTANT: Rotate all x-axis labels by 45 degrees
           - IMPORTANT: Set the figure size to 10x12 inches (figsize=(10, 12))
        3. DO NOT explain your changes, just provide the corrected code
        4. Make sure to include all necessary imports
        5. DO NOT include code fence markers (```) in your response
        
        Output ONLY the corrected Python code with no additional text.
        """
    )

    # Prepare and send the prompt to the LLM
    logger.debug("Preparing correction prompt for Groq LLM")
    model = get_groq_llm(CHART_DATA_MODEL)
    chain = correction_prompt | model

    logger.debug("Sending correction prompt to Groq LLM")
    response = chain.invoke(
        {
            "query": query,
            "shape": df_preview.shape,
            "columns_info": columns_info,
            "sample_count": len(df_preview.sample_rows),
            "sample_rows": sample_rows_str,
            "error": error,
            "code": code,
        }
    )

    corrected_code = response.content.strip()
    logger.debug(f"Received corrected code from LLM (length: {len(corrected_code)})")

    # Remove markdown code fence markers if present
    corrected_code = _clean_code_from_llm(corrected_code)

    # Validate the corrected code contains the required function
    if "def create_plot" not in corrected_code:
        error_msg = (
            "Corrected code does not contain the required create_plot() function"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Print the corrected code
    print("\n==== CORRECTED VISUALIZATION CODE ====")
    print(corrected_code)
    print("======================================\n")

    return corrected_code


def execute_with_retries(
    initial_code: str,
    df: pd.DataFrame,
    query: str,
    df_preview: DataFramePreview,
    max_retries: int = 5,
) -> bytes:
    """
    Execute code with automatic error correction and retries.

    Args:
        initial_code: The initial Python code to execute
        df: The DataFrame to process
        query: The original user query
        df_preview: Preview data about the DataFrame
        max_retries: Maximum number of retry attempts

    Returns:
        PNG image bytes of the chart

    Raises:
        ValueError: If all retry attempts fail
    """
    logger.info(f"Executing plot code with up to {max_retries} retries")
    print(f"\n==== STARTING EXECUTION WITH {max_retries} MAX RETRIES ====\n")

    code = initial_code
    for attempt in range(max_retries):
        logger.debug(f"Execution attempt {attempt + 1}/{max_retries}")
        print(f"Attempt {attempt + 1}/{max_retries} to execute visualization code...")

        image_bytes, error = execute_plot_code(code, df)

        if error is None:
            # Success
            logger.info(f"Plot generation succeeded on attempt {attempt + 1}")
            print(f"\n✅ Plot generation SUCCEEDED on attempt {attempt + 1}\n")
            return image_bytes

        logger.warning(f"Attempt {attempt + 1} failed with error: {error}")
        print(f"\n❌ Attempt {attempt + 1} FAILED with error: {error}\n")

        if attempt < max_retries - 1:
            # Try to correct the code for next attempt
            logger.info("Requesting code correction from LLM")
            print("Requesting code correction from LLM...")
            try:
                code = correct_plot_code(error, code, query, df_preview)
                print("Received corrected code, trying again...")
            except Exception as correction_error:
                logger.error(f"Code correction failed: {str(correction_error)}")
                print(f"⚠️ Code correction failed: {str(correction_error)}")
                # If correction fails, we'll try again with the original code
                logger.warning("Continuing with original code for next attempt")
                print("Continuing with original code for next attempt...")

    # All attempts failed
    logger.error(f"All {max_retries} execution attempts failed")
    print(f"\n❌ All {max_retries} execution attempts FAILED\n")
    raise ValueError(f"Failed to generate chart after {max_retries} attempts")


def generate_chart(df: pd.DataFrame, query: str) -> bytes:
    """
    Main function to generate a chart based on a user query.

    Args:
        df: The pandas DataFrame containing the data to visualize
        query: The user's query describing the desired visualization

    Returns:
        PNG image bytes of the generated chart

    Raises:
        ValueError: If any step of the chart generation process fails
    """
    logger.info(f"Generating chart for query: {query}")
    print(f"\n==== GENERATING CHART FOR QUERY ====")
    print(f'Query: "{query}"')
    print(f"DataFrame shape: {df.shape}")
    print("====================================\n")

    try:
        # Step 1: Prepare DataFrame preview for the LLM
        logger.debug("Preparing DataFrame preview")
        print("1. Preparing DataFrame preview...")
        df_preview = prepare_dataframe_preview(df)

        # Step 2: Generate the plotting code
        logger.debug("Generating visualization code")
        print("2. Generating visualization code...")
        plot_code = generate_plot_code(query, df_preview)

        # Step 3: Execute the code to create the plot with retries
        logger.debug("Executing visualization code with retry logic")
        print("3. Executing visualization code with retry logic...")
        image_bytes = execute_with_retries(plot_code, df, query, df_preview)

        logger.info("Chart generation complete")
        print(f"\n✅ Chart generation COMPLETE - generated {len(image_bytes)} bytes\n")
        return image_bytes

    except Exception as e:
        logger.error(f"Chart generation failed: {str(e)}", exc_info=True)
        print(f"\n❌ Chart generation FAILED: {str(e)}\n")
        raise ValueError(f"Failed to generate chart: {str(e)}")


if __name__ == "__main__":
    # Set up console logging for direct script execution
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Set to DEBUG for more detailed logging
    root_logger.addHandler(console_handler)

    # Test with sample data
    logger.info("Testing chart generator with sample data")

    # Create sample DataFrame
    df = pd.DataFrame(
        {
            "month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"] * 3,
            "sales": np.random.randint(1000, 5000, 18),
            "category": ["Electronics", "Clothing", "Home"] * 6,
        }
    )

    # Test query
    test_query = "Show me monthly sales as a bar chart"

    try:
        image_bytes = generate_chart(df, test_query)
        logger.info("Chart generated successfully")
        print(
            f"\nChart generated successfully, image bytes length: {len(image_bytes)}\n"
        )
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
