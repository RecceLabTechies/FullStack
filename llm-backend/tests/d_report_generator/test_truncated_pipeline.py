#!/usr/bin/env python
"""
Test module for truncated_pipeline.py

This module contains unit tests for the truncated pipeline functionality.
"""

import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import logging

from mypackage.d_report_generator.truncated_pipeline import run_truncated_pipeline
from mypackage.d_report_generator.generate_analysis_queries import QueryItem, QueryType


class TestTruncatedPipeline(unittest.TestCase):
    """Test cases for the truncated pipeline module."""

    def setUp(self):
        """Set up test data."""
        # Sample query items for testing
        self.chart_query = QueryItem(
            query="Generate a chart of sales by region",
            query_type=QueryType.CHART,
            collection_name="sales_data",
        )

        self.description_query = QueryItem(
            query="Generate a description of customer spending patterns",
            query_type=QueryType.DESCRIPTION,
            collection_name="customer_data",
        )

        # Sample DataFrame for testing
        self.test_df = pd.DataFrame(
            {
                "region": ["North", "South", "East", "West", "North"],
                "sales": [1000, 1200, 900, 1500, 1100],
                "date": pd.date_range(start="2023-01-01", periods=5),
            }
        )

        # Sample results
        self.chart_result = "/api/minio/temp-charts/chart_123.png"
        self.description_result = "Sales have increased by 15% in the North region."

    @patch("mypackage.d_report_generator.truncated_pipeline.collection_processor")
    @patch("mypackage.d_report_generator.truncated_pipeline.chart_generator")
    def test_run_truncated_pipeline_chart(
        self, mock_chart_generator, mock_collection_processor
    ):
        """Test the run_truncated_pipeline function with a chart query."""
        # Set up mocks
        mock_collection_processor.process_collection_query.return_value = self.test_df
        mock_chart_generator.generate_chart.return_value = self.chart_result

        # Test chart query processing
        result = run_truncated_pipeline(self.chart_query)

        # Verify the result
        self.assertEqual(result["type"], "chart")
        self.assertEqual(result["result"], self.chart_result)

        # Verify all the mocks were called correctly
        mock_collection_processor.process_collection_query.assert_called_once_with(
            "sales_data", "Generate a chart of sales by region"
        )
        mock_chart_generator.generate_chart.assert_called_once_with(
            self.test_df, "Generate a chart of sales by region"
        )

    @patch("mypackage.d_report_generator.truncated_pipeline.collection_processor")
    @patch("mypackage.d_report_generator.truncated_pipeline.description_generator")
    def test_run_truncated_pipeline_description(
        self, mock_description_generator, mock_collection_processor
    ):
        """Test the run_truncated_pipeline function with a description query."""
        # Set up mocks
        mock_collection_processor.process_collection_query.return_value = self.test_df
        mock_description_generator.generate_description.return_value = (
            self.description_result
        )

        # Test description query processing
        result = run_truncated_pipeline(self.description_query)

        # Verify the result
        self.assertEqual(result["type"], "description")
        self.assertEqual(result["result"], self.description_result)

        # Verify all the mocks were called correctly
        mock_collection_processor.process_collection_query.assert_called_once_with(
            "customer_data", "Generate a description of customer spending patterns"
        )
        mock_description_generator.generate_description.assert_called_once_with(
            self.test_df, "Generate a description of customer spending patterns"
        )

    @patch("mypackage.d_report_generator.truncated_pipeline.collection_processor")
    def test_run_truncated_pipeline_invalid_query_type(self, mock_collection_processor):
        """Test the run_truncated_pipeline function with an invalid query type."""
        # Create an invalid query item (using string instead of QueryType enum)
        invalid_query = QueryItem(
            query="Generate something",
            query_type="invalid_type",  # This should be a QueryType enum
            collection_name="test_collection",
        )

        # Test with invalid query type
        with self.assertRaises(ValueError):
            run_truncated_pipeline(invalid_query)

        # Verify collection processor was not called
        mock_collection_processor.process_collection_query.assert_not_called()

    @patch("mypackage.d_report_generator.truncated_pipeline.collection_processor")
    def test_run_truncated_pipeline_collection_error(self, mock_collection_processor):
        """Test the run_truncated_pipeline function with a collection processing error."""
        # Set up mock to raise an exception
        mock_collection_processor.process_collection_query.side_effect = Exception(
            "Collection error"
        )

        # Test with collection processing error
        result = run_truncated_pipeline(self.chart_query)

        # Verify the result
        self.assertEqual(result["type"], "error")
        self.assertIn("Error processing collection", result["result"])
        self.assertIn("Collection error", result["result"])

        # Verify the mock was called
        mock_collection_processor.process_collection_query.assert_called_once()

    @patch("mypackage.d_report_generator.truncated_pipeline.collection_processor")
    @patch("mypackage.d_report_generator.truncated_pipeline.chart_generator")
    def test_run_truncated_pipeline_chart_generation_error(
        self, mock_chart_generator, mock_collection_processor
    ):
        """Test the run_truncated_pipeline function with a chart generation error."""
        # Set up mocks
        mock_collection_processor.process_collection_query.return_value = self.test_df
        mock_chart_generator.generate_chart.side_effect = Exception(
            "Chart generation error"
        )

        # Test with chart generation error
        result = run_truncated_pipeline(self.chart_query)

        # Verify the result
        self.assertEqual(result["type"], "error")
        self.assertIn("Error generating output", result["result"])
        self.assertIn("Chart generation error", result["result"])

        # Verify all the mocks were called correctly
        mock_collection_processor.process_collection_query.assert_called_once()
        mock_chart_generator.generate_chart.assert_called_once()

    @patch("mypackage.d_report_generator.truncated_pipeline.collection_processor")
    @patch("mypackage.d_report_generator.truncated_pipeline.description_generator")
    def test_run_truncated_pipeline_description_generation_error(
        self, mock_description_generator, mock_collection_processor
    ):
        """Test the run_truncated_pipeline function with a description generation error."""
        # Set up mocks
        mock_collection_processor.process_collection_query.return_value = self.test_df
        mock_description_generator.generate_description.side_effect = Exception(
            "Description generation error"
        )

        # Test with description generation error
        result = run_truncated_pipeline(self.description_query)

        # Verify the result
        self.assertEqual(result["type"], "error")
        self.assertIn("Error generating output", result["result"])
        self.assertIn("Description generation error", result["result"])

        # Verify all the mocks were called correctly
        mock_collection_processor.process_collection_query.assert_called_once()
        mock_description_generator.generate_description.assert_called_once()

    def test_run_truncated_pipeline_logging(self):
        """Test logging in the run_truncated_pipeline function."""
        # Set up patches for all dependencies
        with patch(
            "mypackage.d_report_generator.truncated_pipeline.collection_processor"
        ) as mock_collection_processor, patch(
            "mypackage.d_report_generator.truncated_pipeline.chart_generator"
        ) as mock_chart_generator:

            # Set up mocks
            mock_collection_processor.process_collection_query.return_value = (
                self.test_df
            )
            mock_chart_generator.generate_chart.return_value = self.chart_result

            # Set up logging capture
            with self.assertLogs(level="DEBUG") as log_context:
                run_truncated_pipeline(self.chart_query)

            # Verify logging output
            log_output = "\n".join(log_context.output)
            self.assertIn("Processing query", log_output)
            self.assertIn("Query classified as chart request", log_output)
            self.assertIn("Using collection", log_output)
            self.assertIn("Querying collection", log_output)
            self.assertIn("Successfully processed collection query", log_output)
            self.assertIn("Generating chart data", log_output)
            self.assertIn("Chart generation successful", log_output)

            # Test logging of errors
            mock_chart_generator.generate_chart.side_effect = Exception(
                "Chart generation error"
            )

            with self.assertLogs(level="DEBUG") as log_context:
                run_truncated_pipeline(self.chart_query)

            # Verify error logging
            log_output = "\n".join(log_context.output)
            self.assertIn("Error generating output", log_output)
            self.assertIn("Chart generation error", log_output)


if __name__ == "__main__":
    unittest.main()
