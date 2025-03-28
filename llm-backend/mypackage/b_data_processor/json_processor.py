#!/usr/bin/env python
import json
import logging
import os
from typing import List, Optional, Union

import pandas as pd
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM
from pandas.api.types import is_numeric_dtype
from pydantic import BaseModel, Field

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


class FilterCondition(BaseModel):
    column: str = Field(..., description="Column name for filtering.")
    operator: Optional[str] = Field(None, description="Comparison operator.")
    metric: Union[int, str, float] = Field(..., description="Value to filter by.")


class SortCondition(BaseModel):
    column: str = Field(..., description="Column name for sorting.")
    ascending: bool = Field(..., description="Sorting order.")


class FilterInfo(BaseModel):
    file_name: Optional[str] = Field(None, description="Selected JSON file name")
    filter_conditions: Optional[List[FilterCondition]] = Field(
        None, description="List of filtering conditions."
    )
    limit: Optional[int] = Field(None, description="Maximum number of results.")
    sorting_conditions: Optional[List[SortCondition]] = Field(
        None, description="Sorting conditions."
    )


def _convert_metric(
    metric: Optional[Union[int, str, float]],
) -> Optional[Union[int, float, str]]:
    """
    Convert a metric value to the appropriate type (int, float, or str).

    Args:
        metric: The metric value to convert

    Returns:
        Converted metric value with appropriate type
    """
    logger.debug(f"Converting metric value: {metric}, type: {type(metric)}")

    if metric is None:
        return None
    if isinstance(metric, (int, float)):
        return metric
    try:
        result = float(metric) if "." in metric else int(metric)
        logger.debug(f"Converted metric to {type(result).__name__}: {result}")
        return result
    except ValueError:
        logger.debug(f"Keeping metric as string: {metric}")
        return metric


def _filter_dataframe(
    df: pd.DataFrame,
    filter_conditions: Optional[List[FilterCondition]] = None,
    limit: Optional[int] = None,
    sorting_conditions: Optional[List[SortCondition]] = None,
) -> pd.DataFrame:
    """
    Filter and sort a dataframe based on provided conditions.

    Args:
        df: Input DataFrame
        filter_conditions: List of filtering conditions
        limit: Maximum number of rows to return
        sorting_conditions: List of sorting conditions

    Returns:
        Filtered and sorted DataFrame
    """
    logger.debug(f"Filtering DataFrame with {len(df)} rows")
    if df.empty:
        logger.warning("Empty DataFrame provided, returning as is")
        return df

    original_row_count = len(df)

    if filter_conditions:
        logger.debug(f"Applying {len(filter_conditions)} filter conditions")
        for condition in filter_conditions:
            if (
                not condition.column
                or condition.metric is None
                or not condition.operator
            ):
                logger.warning(f"Skipping incomplete filter condition: {condition}")
                continue

            column = condition.column
            metric = _convert_metric(condition.metric)
            operator = condition.operator

            if column not in df.columns:
                logger.warning(f"Column '{column}' not found in DataFrame")
                continue

            logger.debug(f"Filtering on {column} {operator} {metric}")

            if is_numeric_dtype(df[column]):
                operators_map = {
                    "==": df[column] == metric,
                    "!=": df[column] != metric,
                    ">": df[column] > metric,
                    "<": df[column] < metric,
                    ">=": df[column] >= metric,
                    "<=": df[column] <= metric,
                }
            else:
                metric_str = str(metric).lower()
                operators_map = {
                    "==": df[column].astype(str).str.lower() == metric_str,
                    "!=": df[column].astype(str).str.lower() != metric_str,
                }

            if operator in operators_map:
                df = df.loc[operators_map[operator]]
                logger.debug(f"After filter: {len(df)} rows remaining")
            else:
                logger.warning(f"Unsupported operator: {operator}")

    if sorting_conditions:
        logger.debug(f"Applying {len(sorting_conditions)} sorting conditions")
        sort_columns, sort_orders = [], []
        for sort_condition in sorting_conditions:
            if not sort_condition.column or sort_condition.ascending is None:
                logger.warning(f"Skipping incomplete sort condition: {sort_condition}")
                continue
            column = sort_condition.column
            if column not in df.columns:
                logger.warning(f"Sort column '{column}' not found in DataFrame")
                continue
            sort_columns.append(column)
            sort_orders.append(sort_condition.ascending)

        if sort_columns:
            logger.debug(f"Sorting by columns: {sort_columns}")
            df = df.sort_values(by=sort_columns, ascending=sort_orders)

    if limit is not None and isinstance(limit, int) and limit > 0:
        logger.debug(f"Limiting results to {limit} rows")
        df = df.head(limit)

    logger.info(f"Filtered DataFrame from {original_row_count} to {len(df)} rows")
    return df


def _json_to_dataframe(json_file_path: str) -> pd.DataFrame:
    """
    Convert a JSON file to a pandas DataFrame.

    Args:
        json_file_path: Path to the JSON file

    Returns:
        DataFrame representation of the JSON data or empty DataFrame if conversion fails
    """
    logger.debug(f"Converting JSON file to DataFrame: {json_file_path}")
    try:
        with open(json_file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        df = pd.DataFrame(data)
        logger.info(
            f"Successfully converted JSON to DataFrame with {len(df)} rows and {len(df.columns)} columns"
        )
        return df
    except Exception as e:
        logger.error(f"Failed to convert JSON to DataFrame: {str(e)}", exc_info=True)
        return pd.DataFrame()


def _get_sample_data(df: pd.DataFrame) -> dict:
    """
    Extract sample data from DataFrame columns for presentation.

    Args:
        df: Input DataFrame

    Returns:
        Dictionary mapping column names to sample values
    """
    logger.debug(
        f"Extracting sample data from DataFrame with {len(df.columns)} columns"
    )
    sample_data = {}

    for col in df.columns:
        if df[col].dtype == "object":
            unique_values = list(df[col].dropna().unique())
            sample_data[col] = unique_values
            logger.debug(f"Column '{col}' (object): {len(unique_values)} unique values")
        else:
            sample_values = df[col].dropna().head(5).tolist()
            sample_data[col] = sample_values
            logger.debug(f"Column '{col}' ({df[col].dtype}): 5 sample values")

    return sample_data


def process_json_query(
    file_name: str, query: str, directory: str = "./data"
) -> pd.DataFrame:
    """
    Process a user query on a JSON file to extract filtering conditions and return filtered data.

    Args:
        file_name: Name of the JSON file
        query: User query string
        directory: Directory containing the JSON file

    Returns:
        Filtered DataFrame or empty DataFrame if processing fails
    """
    logger.info(f"Processing JSON query: '{query}' on file: '{file_name}'")

    # Move template, parser, and prompt into the function
    parser = PydanticOutputParser(pydantic_object=FilterInfo)

    template = """Given the following Column headers and Sample Values, determine the filtering operation.

Available headers:
{format_headers}

Sample Values:
{sample_data}

Request: {query}

Firstly, extract the data manipulation request from the query. If there is no data manipulation request, leave the fields blank.

Respond only in valid format that matches this structure:
{format_instructions}

Leave all unnecessary fields blank. If there is no filter metric, leave filter column blank.

IMPORTANT:
- If the filter condition uses `=`, replace it with `==` (e.g., `Number of Views = 10` → `Number of Views == 10`).
- Other operators (`>=`, `<=`, `!=`, `>`, `<`) should remain unchanged.
"""

    prompt = ChatPromptTemplate.from_template(template).partial(
        format_instructions=parser.get_format_instructions()
    )

    model = OllamaLLM(model="dolphin-mistral", temperature=0)
    chain = prompt | model | parser
    json_file_path = os.path.join(directory, file_name)

    if not os.path.isfile(json_file_path):
        logger.error(f"JSON file not found: {json_file_path}")
        return pd.DataFrame()

    df = _json_to_dataframe(json_file_path)
    if df.empty:
        logger.error(f"Failed to parse JSON file: {file_name}")
        return df

    formatted_headers = list(df.columns)
    sample_data = _get_sample_data(df)

    logger.debug("Invoking LLM chain for query processing")
    try:
        result = chain.invoke(
            {
                "format_headers": formatted_headers,
                "sample_data": sample_data,
                "query": query,
            }
        )
        logger.info(f"Extracted filter conditions: {result}")

        filtered_df = _filter_dataframe(
            df,
            filter_conditions=result.filter_conditions,
            limit=result.limit,
            sorting_conditions=result.sorting_conditions,
        )

        return filtered_df
    except Exception as e:
        logger.error(f"Error processing JSON query: {str(e)}", exc_info=True)
        return df


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
    df = process_json_query(
        "cleaned_Adjusted_Ad_Campaign_Performance_Data.json", test_query
    )
    print(f"Processed DataFrame with {len(df)} rows")
