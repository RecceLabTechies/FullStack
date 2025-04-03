#!/usr/bin/env python
"""
Test module for report_generator.py

This module contains unit tests for the report generation functionality.
"""

import unittest
from unittest.mock import patch, MagicMock, ANY
import logging

from mypackage.d_report_generator.report_generator import (
    ReportResults,
    report_generator,
)
from mypackage.d_report_generator.generate_analysis_queries import (
    QueryType,
    QueryItem,
    QueryList,
)


class TestReportGenerator(unittest.TestCase):
    """Test cases for the report generator module."""

    def setUp(self):
        """Set up test data."""
        # Sample query list for testing
        self.test_query_list = QueryList(
            queries=[
                QueryItem(
                    query="Generate a chart of sales by region",
                    query_type=QueryType.CHART,
                    collection_name="sales_data",
                ),
                QueryItem(
                    query="Generate a description of customer spending patterns",
                    query_type=QueryType.DESCRIPTION,
                    collection_name="customer_data",
                ),
            ]
        )

        # Sample results for testing
        self.test_chart_result = ["/api/minio/temp-charts/chart_123.png"]
        self.test_description_result = (
            "Sales have increased by 15% in the North region."
        )

    @patch("mypackage.d_report_generator.report_generator.generate_analysis_queries")
    @patch("mypackage.d_report_generator.report_generator.truncated_pipeline")
    def test_report_generator(self, mock_truncated_pipeline, mock_generate_queries):
        """Test the main report_generator function."""
        # Set up mocks
        mock_generate_queries.return_value = self.test_query_list

        # Configure the mock to return different results for different queries
        mock_truncated_pipeline.run_truncated_pipeline.side_effect = [
            self.test_chart_result,
            self.test_description_result,
        ]

        # Test successful report generation
        result = report_generator("What is our sales performance by region?")

        # Verify the result
        self.assertIsInstance(result, ReportResults)
        self.assertEqual(len(result.results), 2)
        self.assertEqual(result.results[0], self.test_chart_result)
        self.assertEqual(result.results[1], self.test_description_result)

        # Verify all the mocks were called correctly
        mock_generate_queries.assert_called_once_with(
            "What is our sales performance by region?"
        )
        self.assertEqual(mock_truncated_pipeline.run_truncated_pipeline.call_count, 2)

        # Test with empty query list
        mock_generate_queries.return_value = QueryList(queries=[])

        result = report_generator("What is our sales performance by region?")

        # Verify the result
        self.assertEqual(len(result.results), 0)

        # Test with pipeline error
        mock_generate_queries.return_value = self.test_query_list
        mock_truncated_pipeline.run_truncated_pipeline.side_effect = Exception(
            "Pipeline error"
        )

        result = report_generator("What is our sales performance by region?")

        # Verify the result
        self.assertEqual(len(result.results), 2)
        self.assertTrue(isinstance(result.results[0], str))
        self.assertTrue(result.results[0].startswith("Error in analysis"))
        self.assertTrue(isinstance(result.results[1], str))
        self.assertTrue(result.results[1].startswith("Error in analysis"))

    def test_report_results_model(self):
        """Test the ReportResults pydantic model."""
        # Test with mixed result types
        results = [["chart1.png", "chart2.png"], "Description text", ["chart3.png"]]

        report_results = ReportResults(results=results)

        self.assertEqual(len(report_results.results), 3)
        self.assertEqual(report_results.results[0], ["chart1.png", "chart2.png"])
        self.assertEqual(report_results.results[1], "Description text")
        self.assertEqual(report_results.results[2], ["chart3.png"])

        # Test with empty results
        empty_results = ReportResults(results=[])
        self.assertEqual(len(empty_results.results), 0)

    @patch("mypackage.d_report_generator.report_generator.generate_analysis_queries")
    def test_report_generator_query_generation_error(self, mock_generate_queries):
        """Test report_generator handling of query generation errors."""
        # Set up mock to raise an exception
        mock_generate_queries.side_effect = ValueError("Invalid query")

        # Test error handling
        with self.assertRaises(ValueError):
            report_generator("What is our sales performance by region?")

        # Verify the mock was called
        mock_generate_queries.assert_called_once()

    @patch("mypackage.d_report_generator.report_generator.generate_analysis_queries")
    @patch("mypackage.d_report_generator.report_generator.truncated_pipeline")
    def test_report_generator_mixed_results(
        self, mock_truncated_pipeline, mock_generate_queries
    ):
        """Test report_generator with mixed successful and failed results."""
        # Set up mocks
        mock_generate_queries.return_value = QueryList(
            queries=[
                QueryItem(
                    query="Generate a chart of sales by region",
                    query_type=QueryType.CHART,
                    collection_name="sales_data",
                ),
                QueryItem(
                    query="Generate a description of customer spending patterns",
                    query_type=QueryType.DESCRIPTION,
                    collection_name="customer_data",
                ),
                QueryItem(
                    query="Generate a chart of product performance",
                    query_type=QueryType.CHART,
                    collection_name="product_data",
                ),
            ]
        )

        # Configure the mock to return different results for different queries
        mock_truncated_pipeline.run_truncated_pipeline.side_effect = [
            self.test_chart_result,
            Exception("Pipeline error for description"),
            self.test_chart_result,
        ]

        # Test with mixed results
        result = report_generator("What is our overall business performance?")

        # Verify the result
        self.assertEqual(len(result.results), 3)
        self.assertEqual(result.results[0], self.test_chart_result)
        self.assertTrue(isinstance(result.results[1], str))
        self.assertTrue(result.results[1].startswith("Error in analysis"))
        self.assertEqual(result.results[2], self.test_chart_result)

        # Verify all the mocks were called correctly
        self.assertEqual(mock_truncated_pipeline.run_truncated_pipeline.call_count, 3)

    @patch("mypackage.d_report_generator.report_generator.generate_analysis_queries")
    @patch("mypackage.d_report_generator.report_generator.truncated_pipeline")
    def test_report_generator_logging(
        self, mock_truncated_pipeline, mock_generate_queries
    ):
        """Test logging in the report_generator function."""
        # Set up mocks
        mock_generate_queries.return_value = self.test_query_list
        mock_truncated_pipeline.run_truncated_pipeline.side_effect = [
            self.test_chart_result,
            self.test_description_result,
        ]

        # Set up logging capture
        with self.assertLogs(level="DEBUG") as log_context:
            report_generator("What is our sales performance by region?")

        # Verify logging output
        log_output = "\n".join(log_context.output)
        self.assertIn("Starting report generation for query", log_output)
        self.assertIn("Generating analysis queries from user query", log_output)
        self.assertIn("Generated", log_output)
        self.assertIn("Beginning to process individual analysis queries", log_output)
        self.assertIn("Processing query", log_output)
        self.assertIn("processed successfully", log_output)
        self.assertIn("Report generation completed", log_output)

        # Test logging of errors
        mock_truncated_pipeline.run_truncated_pipeline.side_effect = Exception(
            "Pipeline error"
        )

        with self.assertLogs(level="DEBUG") as log_context:
            report_generator("What is our sales performance by region?")

        # Verify error logging
        log_output = "\n".join(log_context.output)
        self.assertIn("Error processing query", log_output)
        self.assertIn("Pipeline error", log_output)


if __name__ == "__main__":
    unittest.main()
