#!/usr/bin/env python
import logging
import re
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_experimental.utilities import PythonREPL
from pandas.api.types import is_numeric_dtype, is_string_dtype
from pymongo.collection import Collection

from mypackage.utils.database import Database
from mypackage.utils.llm_config import COLLECTION_PROCESSOR_MODEL, get_groq_llm

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


python_repl = PythonREPL()


def _get_column_metadata(df: pd.DataFrame) -> Dict:
    """Extract column metadata including unique values and statistics."""
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

    for col in df.columns:
        if is_string_dtype(df[col]):
            # Handle NaN values before getting unique values
            clean_series = df[col].dropna()
            unique_values = clean_series.unique().tolist()
            metadata["unique_values"][col] = unique_values
            logger.info(f"Column '{col}': {len(unique_values)} unique string values")

        elif is_numeric_dtype(df[col]):
            stats = {
                "min": df[col].min(),
                "max": df[col].max(),
                "mean": df[col].mean(),
                "median": df[col].median(),  # Added
                "std": df[col].std(),  # Added
                "null_count": df[col].isnull().sum(),
            }
            metadata["numeric_stats"][col] = stats
            logger.info(f"Column '{col}': numeric stats - {stats}")

    logger.info(
        f"Metadata extraction complete: {len(metadata['columns'])} columns processed"
    )
    return metadata


def _extract_code_block(response: str) -> str:
    """Extract code block from markdown response"""
    if not response or not isinstance(response, str):
        raise ValueError(
            f"Invalid LLM response: {type(response)} - {str(response)[:200]}"
        )

    code_pattern = re.compile(
        r"```(?:python)?\n(.*?)\n```", re.DOTALL
    )  # More flexible pattern
    match = code_pattern.search(response)
    if not match:
        logger.error(
            f"No code block found in response. Full response:\n{response[:500]}"
        )
        raise ValueError("LLM response didn't contain valid code block")
    return match.group(1).strip()


def _generate_processing_code(query: str, metadata: Dict) -> str:
    """Generate pandas processing code using LLM."""
    logger.info(f"Generating processing code for query: '{query}'")
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

    prompt = prompt_template.format(
        query=query,
        columns=metadata["columns"],
        dtypes=metadata["dtypes"],
        unique_values=metadata["unique_values"],
        numeric_stats=metadata["numeric_stats"],
    )

    logger.info("Sending prompt to LLM for code generation")

    generated_response = get_groq_llm(COLLECTION_PROCESSOR_MODEL).invoke(prompt)

    if isinstance(generated_response, AIMessage):
        generated_response = generated_response.content

    generated_code = _extract_code_block(generated_response)

    logger.info("Code generation complete")
    logger.info(f"Generated code:\n{generated_code}")
    return generated_code


def _execute_code_safe(
    code: str, df: pd.DataFrame
) -> Tuple[pd.DataFrame, Optional[str]]:
    """Execute code using restricted PythonREPL."""
    logger.info(f"Executing code on DataFrame with shape {df.shape}")
    try:
        # Add datetime support to safe globals
        from pandas import Timestamp  # Add this import

        safe_globals = {
            "pd": pd,
            "np": np,
            "Timestamp": Timestamp,  # Include Timestamp
            "__builtins__": {
                "print": print,
                "range": range,
                "list": list,
                "dict": dict,
                "str": str,
                "float": float,
                "int": int,
            },
        }

        # Update code generation with datetime handling
        full_code = (
            "import pandas as pd\n"
            "from pandas import Timestamp\n"  # Explicit import
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

        # Execute with timeout
        output = python_repl.run(full_code, timeout=30)  # 30 second timeout

        # Handle potential error messages
        if "Traceback (most recent call last):" in output:
            error = output.split("\n")[-1].strip()
            return df, f"Execution error: {error}"

        # Convert CSV output back to DataFrame
        from io import StringIO

        result_df = pd.read_csv(StringIO(output))
        return result_df, None

    except Exception as e:
        return df, f"REPL error: {str(e)}"


def _correct_code(error: str, code: str, query: str, metadata: Dict) -> str:
    """Generate corrected code using error feedback."""
    logger.info(f"Attempting to correct code with error: {error}")
    correction_prompt = f"""Fix this Python code based on the error:

Original query: "{query}"
Dataset columns: {metadata["columns"]}
Data types: {metadata["dtypes"]}

Error:
{error}

Faulty code:
{code}

Examples of good corrections:
---
Error: KeyError: 'status'
Faulty code:
processed_df = df[df['statu'] == 'active']
Corrected:
processed_df = df[df['status'] == 'active']

---
Error: TypeError: '>' not supported between 'str' and 'int'
Faulty code:
df = df[df['price'] > 100]
Corrected:
df = df[pd.to_numeric(df['price']) > 100]

---
Error: AttributeError: 'DataFrame' object has no attribute 'sort'
Faulty code:
df.sort('date')
Corrected:
df = df.sort_values('date')

Now fix this code following these patterns. Provide ONLY the corrected code using this template:
```python
import pandas as pd
import numpy as np

def process_data(df: pd.DataFrame) -> pd.DataFrame:
    # Corrected logic
    ...
```"""

    logger.info("Sending correction prompt to LLM")
    corrected_response = get_groq_llm(COLLECTION_PROCESSOR_MODEL).invoke(
        correction_prompt
    )
    if isinstance(corrected_response, AIMessage):  # Add this check
        corrected_response = corrected_response.content
    corrected_code = _extract_code_block(corrected_response)
    logger.info("Received corrected code")
    logger.info(f"Corrected code:\n{corrected_code}")
    return corrected_code


def _execute_with_retries(
    initial_code: str,
    df: pd.DataFrame,
    query: str,
    metadata: Dict,
    max_retries: int = 5,
) -> pd.DataFrame:
    """Execute code with error correction retries."""
    logger.info(f"Executing with retries (max: {max_retries})")
    current_code = initial_code
    original_df = df.copy()

    for attempt in range(max_retries + 1):
        logger.info(f"Execution attempt {attempt + 1}/{max_retries + 1}")

        result_df, error = _execute_code_safe(
            current_code,
            original_df,
        )

        if not error:
            logger.info(f"Execution successful on attempt {attempt + 1}")
            logger.info(f"Final result shape: {result_df.shape}")
            return result_df

        logger.warning(
            f"Execution failed (attempt {attempt + 1}/{max_retries + 1}): {error}"
        )
        if attempt < max_retries:
            logger.info(f"Attempting code correction, retry {attempt + 1}")
            current_code = _correct_code(error, current_code, query, metadata)

    logger.error("Max retries exceeded, returning original DataFrame")
    return original_df


def process_collection_query(collection_name: str, query: str) -> pd.DataFrame:
    """Process a collection query using LLM-generated pandas code."""
    logger.info(f"Processing query on '{collection_name}': {query}")

    try:
        # Get MongoDB collection
        logger.info(f"Retrieving collection: {collection_name}")
        collection = Database.get_collection(collection_name)
        if not isinstance(collection, Collection):
            logger.error(f"Invalid collection: {collection_name}")
            raise ValueError(f"Invalid collection: {collection_name}")

        # Convert to DataFrame
        logger.info("Converting MongoDB collection to DataFrame")
        df = pd.DataFrame(list(collection.find({}, {"_id": 0})))
        logger.info(f"Converted to DataFrame with shape: {df.shape}")
        if df.empty:
            logger.warning("Empty DataFrame retrieved")
            return df

        # Extract metadata
        logger.info("Extracting DataFrame metadata")
        metadata = _get_column_metadata(df)

        # Generate initial code
        logger.info("Generating initial processing code")
        initial_code = _generate_processing_code(query, metadata)
        logger.info(f"Generated initial code:\n{initial_code}")

        # Execute with retry mechanism
        logger.info("Executing generated code with retry mechanism")
        processed_df = _execute_with_retries(
            initial_code=initial_code,
            df=df,
            query=query,
            metadata=metadata,
        )

        logger.info(f"Query processing complete. Result shape: {processed_df.shape}")
        return processed_df

    except Exception as e:
        logger.error(f"Processing failed: {str(e)}", exc_info=True)
        return pd.DataFrame()


# Example usage
if __name__ == "__main__":
    # Set up logging for main execution
    logger.info("Starting example execution")

    # Generate fake data
    logger.info("Generating fake data for testing")
    fake_data = (
        pd.DataFrame(
            {
                "status": ["active"] * 15 + ["inactive"] * 5 + ["pending"] * 5,
                "revenue": np.concatenate(
                    [
                        np.random.normal(1500, 200, 15),  # Active records
                        np.random.normal(800, 100, 5),  # Inactive
                        np.random.normal(1200, 300, 5),  # Pending
                    ]
                ),
                "date": pd.date_range("2024-01-01", periods=25, freq="D"),
                "product": np.random.choice(["WidgetA", "GadgetB", "ToolC"], 25),
                "customer_id": np.random.randint(1000, 9999, 25),
            }
        )
        .sample(frac=1)
        .reset_index(drop=True)
    )
    logger.info(f"Fake data generated with shape: {fake_data.shape}")

    # Original query
    test_query = (
        "Filter records where status is 'active' and revenue > 1000, then sort by date"
    )
    logger.info(f"Test query: '{test_query}'")

    # Bypass database and process directly
    logger.info("Processing test data directly (bypassing database)")
    metadata = _get_column_metadata(fake_data)
    code = _generate_processing_code(test_query, metadata)
    processed_df = _execute_with_retries(
        initial_code=code, df=fake_data, query=test_query, metadata=metadata
    )

    logger.info("Example execution complete")
    logger.info(f"Original DataFrame shape: {fake_data.shape}")
    logger.info(f"Processed DataFrame shape: {processed_df.shape}")

    print("Original DataFrame:")
    print(fake_data.head())
    print("\nProcessed DataFrame:")
    print(processed_df)
    print(f"\nOriginal shape: {fake_data.shape}, Processed shape: {processed_df.shape}")
