#!/usr/bin/env python
import unittest
from unittest.mock import patch

from mypackage.d_report_generator.generate_analysis_queries import QueryItem, QueryType
from mypackage.d_report_generator.report_generator import report_generator


class TestReportGenerator(unittest.TestCase):
    def setUp(self):
        """Set up test data."""
        self.test_queries = [
            "What is the average sales amount?",
            "Show customer demographics",
            "Analyze inventory levels",
        ]

    @patch("mypackage.d_report_generator.report_generator.generate_analysis_queries")
    @patch(
        "mypackage.d_report_generator.report_generator.truncated_pipeline.run_truncated_pipeline"
    )
    def test_report_generator_success(self, mock_run_pipeline, mock_generate_queries):
        """Test successful report generation."""
        # Set up mocks
        mock_generate_queries.return_value.queries = [
            QueryItem(
                query="Show sales over time",
                query_type=QueryType.CHART,
                file_name="sales.json",
            ),
            QueryItem(
                query="Describe customer demographics",
                query_type=QueryType.DESCRIPTION,
                file_name="customers.json",
            ),
        ]
        mock_run_pipeline.side_effect = [
            {"type": "LineChart", "data": [], "xAxis": {}, "yAxis": {}},
            "Sample description",
        ]

        # Run report generator
        result = report_generator("What is the average sales amount?")

        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(len(result.results), 2)
        self.assertIsInstance(result.results[0], dict)
        self.assertIsInstance(result.results[1], str)

        # Verify mock calls
        mock_generate_queries.assert_called_once_with(
            "What is the average sales amount?"
        )
        self.assertEqual(mock_run_pipeline.call_count, 2)

    @patch("mypackage.d_report_generator.report_generator.generate_analysis_queries")
    def test_report_generator_empty_query(self, mock_generate_queries):
        """Test report generation with empty query."""
        # Set up mock to raise ValueError
        mock_generate_queries.side_effect = ValueError("Empty query")

        # Run report generator and verify error
        with self.assertRaises(ValueError):
            report_generator("")

        # Verify mock call
        mock_generate_queries.assert_called_once_with("")

    @patch("mypackage.d_report_generator.report_generator.generate_analysis_queries")
    @patch(
        "mypackage.d_report_generator.report_generator.truncated_pipeline.run_truncated_pipeline"
    )
    def test_report_generator_pipeline_error(
        self, mock_run_pipeline, mock_generate_queries
    ):
        """Test report generation with pipeline error."""
        # Set up mocks
        mock_generate_queries.return_value.queries = [
            QueryItem(
                query="Show sales over time",
                query_type=QueryType.CHART,
                file_name="sales.json",
            ),
        ]
        mock_run_pipeline.return_value = "Error processing query"

        # Run report generator
        result = report_generator("What is the average sales amount?")

        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(len(result.results), 1)
        self.assertIsInstance(result.results[0], str)
        self.assertIn("Error", result.results[0])

        # Verify mock calls
        mock_generate_queries.assert_called_once_with(
            "What is the average sales amount?"
        )
        mock_run_pipeline.assert_called_once()

    @patch("mypackage.d_report_generator.report_generator.generate_analysis_queries")
    @patch(
        "mypackage.d_report_generator.report_generator.truncated_pipeline.run_truncated_pipeline"
    )
    def test_report_generator_mixed_results(
        self, mock_run_pipeline, mock_generate_queries
    ):
        """Test report generation with mixed result types."""
        # Set up mocks
        mock_generate_queries.return_value.queries = [
            QueryItem(
                query="Show sales over time",
                query_type=QueryType.CHART,
                file_name="sales.json",
            ),
            QueryItem(
                query="Describe customer demographics",
                query_type=QueryType.DESCRIPTION,
                file_name="customers.json",
            ),
            QueryItem(
                query="Show inventory levels",
                query_type=QueryType.CHART,
                file_name="inventory.json",
            ),
        ]
        mock_run_pipeline.side_effect = [
            {"type": "LineChart", "data": [], "xAxis": {}, "yAxis": {}},
            "Sample description",
            "Error processing query",
        ]

        # Run report generator
        result = report_generator("Analyze business performance")

        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(len(result.results), 3)
        self.assertIsInstance(result.results[0], dict)
        self.assertIsInstance(result.results[1], str)
        self.assertIsInstance(result.results[2], str)

        # Verify mock calls
        mock_generate_queries.assert_called_once_with("Analyze business performance")
        self.assertEqual(mock_run_pipeline.call_count, 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
