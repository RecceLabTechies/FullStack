#!/usr/bin/env python
import unittest
from unittest.mock import patch

import pandas as pd

from mypackage.d_report_generator.generate_analysis_queries import QueryItem, QueryType
from mypackage.d_report_generator.truncated_pipeline import run_truncated_pipeline


class TestTruncatedPipeline(unittest.TestCase):
    def setUp(self):
        """Set up test data."""
        # Create test DataFrame
        self.test_df = pd.DataFrame(
            {
                "date": pd.date_range(start="2023-01-01", periods=10),
                "sales": [100, 150, 200, 180, 220, 250, 230, 280, 300, 350],
                "customers": [50, 60, 70, 65, 75, 80, 85, 90, 95, 100],
                "category": ["A", "B", "A", "C", "B", "A", "C", "B", "A", "C"],
            }
        )

    @patch("mypackage.b_data_processor.json_processor.process_json_query")
    @patch("mypackage.c_regular_generator.chart_data_generator.generate_chart_data")
    @patch("mypackage.c_regular_generator.description_generator.generate_description")
    def test_run_truncated_pipeline_chart(
        self, mock_generate_description, mock_generate_chart, mock_process_json
    ):
        """Test pipeline execution for chart generation."""
        # Set up mocks
        mock_process_json.return_value = self.test_df
        mock_generate_chart.return_value = {
            "type": "LineChart",
            "data": [],
            "xAxis": {"dataKey": "date", "type": "datetime", "label": "Date"},
            "yAxis": {"dataKey": "sales", "type": "numeric", "label": "Sales"},
        }

        # Create test query
        query_item = QueryItem(
            query="Show sales over time",
            query_type=QueryType.CHART,
            file_name="sales.json",
        )

        # Run pipeline
        result = run_truncated_pipeline(query_item)

        # Verify result
        self.assertIsInstance(result, dict)
        self.assertEqual(result["type"], "LineChart")
        self.assertIn("data", result)
        self.assertIn("xAxis", result)
        self.assertIn("yAxis", result)

        # Verify mock calls
        mock_process_json.assert_called_once_with("sales.json", query_item.query)
        mock_generate_chart.assert_called_once_with(self.test_df, query_item.query)
        mock_generate_description.assert_not_called()

    @patch("mypackage.b_data_processor.json_processor.process_json_query")
    @patch("mypackage.c_regular_generator.chart_data_generator.generate_chart_data")
    @patch("mypackage.c_regular_generator.description_generator.generate_description")
    def test_run_truncated_pipeline_description(
        self, mock_generate_description, mock_generate_chart, mock_process_json
    ):
        """Test pipeline execution for description generation."""
        # Set up mocks
        mock_process_json.return_value = self.test_df
        mock_generate_description.return_value = "Sample description"

        # Create test query
        query_item = QueryItem(
            query="Describe sales trends",
            query_type=QueryType.DESCRIPTION,
            file_name="sales.json",
        )

        # Run pipeline
        result = run_truncated_pipeline(query_item)

        # Verify result
        self.assertIsInstance(result, str)
        self.assertEqual(result, "Sample description")

        # Verify mock calls
        mock_process_json.assert_called_once_with("sales.json", query_item.query)
        mock_generate_description.assert_called_once_with(
            self.test_df, query_item.query
        )
        mock_generate_chart.assert_not_called()

    @patch("mypackage.b_data_processor.json_processor.process_json_query")
    def test_run_truncated_pipeline_invalid_query_type(self, mock_process_json):
        """Test pipeline execution with invalid query type."""
        # Create test query with invalid type
        query_item = QueryItem(
            query="Invalid query",
            query_type="invalid",  # type: ignore
            file_name="sales.json",
        )

        # Run pipeline and verify error
        with self.assertRaises(ValueError):
            run_truncated_pipeline(query_item)

        # Verify no mock calls
        mock_process_json.assert_not_called()

    @patch("mypackage.b_data_processor.json_processor.process_json_query")
    def test_run_truncated_pipeline_json_error(self, mock_process_json):
        """Test pipeline execution with JSON processing error."""
        # Set up mock to raise exception
        mock_process_json.side_effect = Exception("JSON processing error")

        # Create test query
        query_item = QueryItem(
            query="Show sales over time",
            query_type=QueryType.CHART,
            file_name="sales.json",
        )

        # Run pipeline
        result = run_truncated_pipeline(query_item)

        # Verify error message
        self.assertIsInstance(result, str)
        self.assertIn("Error processing JSON", result)

    @patch("mypackage.b_data_processor.json_processor.process_json_query")
    @patch("mypackage.c_regular_generator.chart_data_generator.generate_chart_data")
    def test_run_truncated_pipeline_chart_error(
        self, mock_generate_chart, mock_process_json
    ):
        """Test pipeline execution with chart generation error."""
        # Set up mocks
        mock_process_json.return_value = self.test_df
        mock_generate_chart.side_effect = Exception("Chart generation error")

        # Create test query
        query_item = QueryItem(
            query="Show sales over time",
            query_type=QueryType.CHART,
            file_name="sales.json",
        )

        # Run pipeline
        result = run_truncated_pipeline(query_item)

        # Verify error message
        self.assertIsInstance(result, str)
        self.assertIn("Error generating output", result)

    @patch("mypackage.b_data_processor.json_processor.process_json_query")
    @patch("mypackage.c_regular_generator.description_generator.generate_description")
    def test_run_truncated_pipeline_description_error(
        self, mock_generate_description, mock_process_json
    ):
        """Test pipeline execution with description generation error."""
        # Set up mocks
        mock_process_json.return_value = self.test_df
        mock_generate_description.side_effect = Exception(
            "Description generation error"
        )

        # Create test query
        query_item = QueryItem(
            query="Describe sales trends",
            query_type=QueryType.DESCRIPTION,
            file_name="sales.json",
        )

        # Run pipeline
        result = run_truncated_pipeline(query_item)

        # Verify error message
        self.assertIsInstance(result, str)
        self.assertIn("Error generating output", result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
