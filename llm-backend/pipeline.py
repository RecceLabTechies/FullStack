#!/usr/bin/env python
from json_selector import select_json_for_query
from json_processor import process_json_query
from query_classifier import classify_query
from chart_generator import generate_chart
from description_generator import generate_description
from report_generator import generate_analysis_queries
import pandas as pd
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class PipelineResult:
    """Class to store the results of the entire pipeline"""

    selected_json: Optional[str]
    original_query: str
    processed_df: pd.DataFrame
    query_type: str
    output: Optional[str] = None  # Store chart path or description text


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
    print("\n=== Starting Pipeline ===")

    # Step 1: Classify the query first
    print("\n1. Classifying query...")
    query_type, original_query, _ = classify_query(query, pd.DataFrame())
    print(f"Query classified as: {query_type}")

    # If it's a report type, handle it directly
    if query_type == "report":
        print("\n2. Generating report...")
        queries = generate_analysis_queries(original_query)
        # Convert QueryList to string format
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

    # For non-report queries, continue with normal pipeline
    # Step 2: Select the appropriate JSON file
    print("\n2. Selecting JSON file...")
    json_result = select_json_for_query(query, data_dir)
    if not json_result.json_file:
        return PipelineResult(
            selected_json=None,
            original_query=original_query,
            processed_df=pd.DataFrame(),
            query_type=query_type,
            output=None,
        )
    print(f"Selected JSON file: {json_result.json_file}")

    # Step 3: Process the JSON file and apply filtering
    print("\n3. Processing JSON data...")
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
    print(f"Processed DataFrame shape: {processed_df.shape}")

    # Step 4: Generate appropriate output based on query type
    print("\n4. Generating output...")
    output = None
    if query_type == "chart":
        output = generate_chart(processed_df, original_query)
        print("Chart generated successfully")
    elif query_type == "description":
        output = generate_description(processed_df, original_query)
        print("Description generated successfully")

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
    print("\n=== Pipeline Results ===")
    print(f"Original Query: {result.original_query}")
    print(f"Selected JSON: {result.selected_json or 'No file selected'}")
    print(f"Query Type: {result.query_type}")

    if result.output:
        print("\nGenerated Output:")
        if result.query_type == "chart":
            print(f"Chart saved to: {result.output}")
        elif result.query_type == "description":
            print("\nAnalysis Description:")
            print(result.output)
        # Report output will be handled in future implementation

    if not result.processed_df.empty:
        print("\nDataFrame Information:")
        print(
            f"Shape: {result.processed_df.shape[0]} rows × {result.processed_df.shape[1]} columns"
        )
        print("\nColumn Overview:")
        for col in result.processed_df.columns:
            unique_values = result.processed_df[col].nunique()
            print(f"- {col}: {unique_values} unique values")

        print("\nFirst few rows of the processed DataFrame:")
        pd.set_option("display.max_columns", None)
        pd.set_option("display.expand_frame_repr", False)
        pd.set_option("display.max_rows", 5)
        print(result.processed_df.head())
    else:
        print(
            "\nNo data to display. Please check if the query is valid and the data exists."
        )


if __name__ == "__main__":
    # Get user input
    print("=== Data Analysis Pipeline ===")
    user_query = input("Enter your query about the data: ")

    # Run the pipeline
    result = run_pipeline(user_query)

    # Display results
    display_results(result)
