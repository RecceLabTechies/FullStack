#!/usr/bin/env python
from json_selector import select_json_for_query
from json_processor import process_json_query
from query_classifier import classify_query
from chart_data_generator import generate_chart_data
from description_generator import generate_description, StructuredDescription
from report_generator import generate_analysis_queries
import pandas as pd
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass
import json


@dataclass
class PipelineResult:
    """Class to store the results of the entire pipeline"""

    selected_json: Optional[str]
    original_query: str
    processed_df: pd.DataFrame
    query_type: str
    output: Optional[Union[str, Dict[str, Any], StructuredDescription]] = (
        None  # Store chart data, description text, or report
    )


def run_pipeline(query: str, data_dir: str = "./data") -> PipelineResult:
    """
    Run the complete pipeline with the following flow:
    Query classification -> (if report: generate report) -> JSON selection -> JSON processing -> Output generation

    Args:
        query (str): The user's natural language query
        data_dir (str): Directory containing the JSON files

    Returns:
        PipelineResult: Object containing all results from the pipeline
    """
    # Step 1: Classify the query first
    query_type, original_query, _ = classify_query(query, pd.DataFrame())

    # If it's a report type, handle it directly
    if query_type == "report":
        queries = generate_analysis_queries(original_query)
        output = "\n".join(
            [f"[{q_type}] {q_text}" for q_type, q_text in queries.queries]
        )
        return PipelineResult(
            selected_json=None,
            original_query=original_query,
            processed_df=pd.DataFrame(),
            query_type=query_type,
            output=output,
        )

    # Step 2: Select the appropriate JSON file
    json_result = select_json_for_query(query, data_dir)
    if not json_result.json_file:
        return PipelineResult(
            selected_json=None,
            original_query=original_query,
            processed_df=pd.DataFrame(),
            query_type=query_type,
            output=None,
        )

    # Step 3: Process the JSON file and apply filtering
    processed_df, processed_query = process_json_query(
        json_result.json_file, query, data_dir
    )
    if processed_df.empty:
        return PipelineResult(
            selected_json=json_result.json_file,
            original_query=original_query,
            processed_df=pd.DataFrame(),
            query_type=query_type,
            output=None,
        )

    # Step 4: Generate appropriate output based on query type
    output = None
    if query_type == "chart":
        output = generate_chart_data(processed_df, original_query)
    elif query_type == "description":
        output = generate_description(processed_df, original_query)

    return PipelineResult(
        selected_json=json_result.json_file,
        original_query=original_query,
        processed_df=processed_df,
        query_type=query_type,
        output=output,
    )


def display_results(result: PipelineResult):
    """
    Display the results of the pipeline in a formatted way

    Args:
        result (PipelineResult): The results from the pipeline
    """
    if result.output:
        if result.query_type == "chart":
            if isinstance(result.output, dict):
                print("Chart Details:")
                print(f"Type: {result.output.get('type', 'Unknown')}")
                print(f"Data Points: {len(result.output.get('data', []))}")
                print(
                    f"X-axis: {result.output.get('xAxis', {}).get('label', 'Unknown')}"
                )
                print(
                    f"Y-axis: {result.output.get('yAxis', {}).get('label', 'Unknown')}"
                )
            else:
                print(f"Chart file: {result.output}")
        elif result.query_type == "description":
            print("Analysis:")
            print(result.output)
        elif result.query_type == "report":
            print("Generated Queries:")
            print(result.output)
    else:
        print("No data to display")


if __name__ == "__main__":
    user_query = input("Enter your query about the data: ")
    result = run_pipeline(user_query)
    display_results(result)
