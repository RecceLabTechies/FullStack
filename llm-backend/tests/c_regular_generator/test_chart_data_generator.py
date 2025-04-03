#!/usr/bin/env python
"""
Test module for chart_generator.py

This module contains unit tests for the chart generation functionality.
"""

import unittest
from unittest.mock import patch, MagicMock, ANY
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO

from mypackage.c_regular_generator.chart_generator import (
    ColumnMetadata,
    ChartInfo,
    _get_column_type,
    extract_column_metadata,
    enhance_query_with_metadata,
    _get_column_synonyms,
    get_llm_chart_selection,
    _create_seaborn_plot,
    _save_plot_to_minio,
    generate_chart,
)


class TestChartGenerator(unittest.TestCase):
    """Test cases for the chart generator module."""

    def setUp(self):
        """Set up test data."""
        # Create a sample DataFrame for testing
        self.test_df = pd.DataFrame(
            {
                "date": pd.date_range(start="2023-01-01", periods=5),
                "sales": [1000, 1200, 900, 1500, 1100],
                "category": ["A", "B", "A", "C", "B"],
                "is_promoted": [True, False, True, True, False],
                "description": [
                    "Product X",
                    "Product Y",
                    "Product Z",
                    "Product X",
                    "Product W",
                ],
            }
        )

        # Sample metadata
        self.test_metadata = [
            ColumnMetadata(
                name="date",
                dtype="datetime",
                sample_values=[
                    "2023-01-01",
                    "2023-01-02",
                    "2023-01-03",
                    "2023-01-04",
                    "2023-01-05",
                ],
            ),
            ColumnMetadata(
                name="sales",
                dtype="numeric",
                sample_values=[1000, 1200, 900, 1500, 1100],
            ),
            ColumnMetadata(
                name="category",
                dtype="categorical",
                unique_values=["A", "B", "C"],
                sample_values=["A", "B", "A", "C", "B"],
            ),
            ColumnMetadata(
                name="is_promoted",
                dtype="boolean",
                sample_values=[True, False, True, True, False],
            ),
            ColumnMetadata(
                name="description",
                dtype="text",
                unique_values=["Product X", "Product Y", "Product Z", "Product W"],
                sample_values=[
                    "Product X",
                    "Product Y",
                    "Product Z",
                    "Product X",
                    "Product W",
                ],
            ),
        ]

        # Sample chart info
        self.test_chart_info = ChartInfo(
            x_axis="date", y_axis="sales", chart_type="line"
        )

    def test_get_column_type(self):
        """Test column type detection."""
        # Test datetime column
        self.assertEqual(_get_column_type(self.test_df["date"]), "datetime")

        # Test numeric column
        self.assertEqual(_get_column_type(self.test_df["sales"]), "numeric")

        # Test categorical column
        self.assertEqual(_get_column_type(self.test_df["category"]), "categorical")

        # Test boolean column
        self.assertEqual(_get_column_type(self.test_df["is_promoted"]), "boolean")

        # Test text column
        self.assertEqual(_get_column_type(self.test_df["description"]), "text")

        # Test with custom series
        many_unique_values = pd.Series(np.random.rand(100))
        self.assertEqual(_get_column_type(many_unique_values), "numeric")

        few_unique_categorical = pd.Series(np.random.choice(["X", "Y", "Z"], 100))
        self.assertEqual(_get_column_type(few_unique_categorical), "categorical")

    def test_extract_column_metadata(self):
        """Test metadata extraction from DataFrame."""
        metadata = extract_column_metadata(self.test_df)

        # Check basic structure
        self.assertEqual(len(metadata), 5)  # Should have 5 columns

        # Check column names
        column_names = [col.name for col in metadata]
        self.assertEqual(set(column_names), set(self.test_df.columns))

        # Check data types
        date_col = next(col for col in metadata if col.name == "date")
        self.assertEqual(date_col.dtype, "datetime")

        sales_col = next(col for col in metadata if col.name == "sales")
        self.assertEqual(sales_col.dtype, "numeric")

        category_col = next(col for col in metadata if col.name == "category")
        self.assertEqual(category_col.dtype, "categorical")
        self.assertEqual(set(category_col.unique_values), set(["A", "B", "C"]))

        # Test with empty DataFrame
        empty_metadata = extract_column_metadata(pd.DataFrame())
        self.assertEqual(empty_metadata, [])

    def test_enhance_query_with_metadata(self):
        """Test query enhancement with metadata."""
        # Test with column name in query
        query = "Show me sales over time"
        enhanced = enhance_query_with_metadata(query, self.test_metadata)

        # Check that the enhanced query contains the original query
        self.assertIn(query, enhanced)

        # Check that it contains column information
        self.assertIn("Columns:", enhanced)
        self.assertIn("date (datetime)", enhanced)
        self.assertIn("sales (numeric)", enhanced)

        # Check that it emphasizes relevant columns
        self.assertIn("Emphasized Columns:", enhanced)
        self.assertIn("'sales' (numeric)", enhanced)

        # Test with synonym in query
        query = "Show me revenue by category"
        enhanced = enhance_query_with_metadata(query, self.test_metadata)
        self.assertIn("'sales' (numeric)", enhanced)
        self.assertIn("'category' (categorical)", enhanced)

    def test_get_column_synonyms(self):
        """Test column synonym generation."""
        # Test known synonyms
        self.assertIn("revenue", _get_column_synonyms("sales"))
        self.assertIn("time", _get_column_synonyms("date"))
        self.assertIn("cost", _get_column_synonyms("price"))

        # Test unknown column
        self.assertEqual(_get_column_synonyms("unknown_column"), [])

    @patch("mypackage.c_regular_generator.chart_generator.get_groq_llm")
    def test_get_llm_chart_selection(self, mock_get_groq_llm):
        """Test LLM chart selection."""
        # Set up mock LLM
        mock_llm = MagicMock()
        mock_get_groq_llm.return_value = mock_llm
        mock_chain = MagicMock()
        mock_llm.__or__.return_value = mock_chain

        # Test with valid LLM response
        mock_chain.invoke.return_value = MagicMock(
            content="x_axis: date\ny_axis: sales\nchart_type: line"
        )

        chart_info = get_llm_chart_selection(
            "Show me sales over time", self.test_metadata
        )

        # Verify the result
        self.assertEqual(chart_info.x_axis, "date")
        self.assertEqual(chart_info.y_axis, "sales")
        self.assertEqual(chart_info.chart_type, "line")

        # Test with invalid response format
        mock_chain.invoke.return_value = MagicMock(
            content="I recommend using a line chart with date on x-axis and sales on y-axis."
        )

        with self.assertRaises(ValueError):
            get_llm_chart_selection("Show me sales over time", self.test_metadata)

        # Test with invalid chart type
        mock_chain.invoke.return_value = MagicMock(
            content="x_axis: date\ny_axis: sales\nchart_type: pie"
        )

        with self.assertRaises(ValueError):
            get_llm_chart_selection("Show me sales over time", self.test_metadata)

    def test_create_seaborn_plot(self):
        """Test seaborn plot creation."""
        # Test line chart
        fig = _create_seaborn_plot(
            self.test_df, ChartInfo(x_axis="date", y_axis="sales", chart_type="line")
        )
        self.assertIsInstance(fig, plt.Figure)
        plt.close(fig)

        # Test bar chart
        fig = _create_seaborn_plot(
            self.test_df, ChartInfo(x_axis="category", y_axis="sales", chart_type="bar")
        )
        self.assertIsInstance(fig, plt.Figure)
        plt.close(fig)

        # Test scatter chart
        fig = _create_seaborn_plot(
            self.test_df, ChartInfo(x_axis="date", y_axis="sales", chart_type="scatter")
        )
        self.assertIsInstance(fig, plt.Figure)
        plt.close(fig)

        # Test box chart
        fig = _create_seaborn_plot(
            self.test_df, ChartInfo(x_axis="category", y_axis="sales", chart_type="box")
        )
        self.assertIsInstance(fig, plt.Figure)
        plt.close(fig)

        # Test heatmap
        fig = _create_seaborn_plot(
            self.test_df,
            ChartInfo(x_axis="category", y_axis="is_promoted", chart_type="heatmap"),
        )
        self.assertIsInstance(fig, plt.Figure)
        plt.close(fig)

    @patch("mypackage.c_regular_generator.chart_generator.MINIO_CLIENT")
    def test_save_plot_to_minio(self, mock_minio_client):
        """Test saving plot to MinIO."""
        # Create a simple figure
        fig = plt.figure()
        plt.plot([1, 2, 3], [4, 5, 6])

        # Test successful save
        mock_minio_client.put_object.return_value = None

        url = _save_plot_to_minio(fig, "line")

        # Verify the result
        self.assertTrue(url.startswith("/api/minio/"))
        self.assertTrue("line_" in url)
        self.assertTrue(url.endswith(".png"))

        # Verify MinIO client was called
        mock_minio_client.put_object.assert_called_once()
        self.assertEqual(
            mock_minio_client.put_object.call_args[0][0], "temp-charts"
        )  # bucket name
        self.assertTrue(
            isinstance(mock_minio_client.put_object.call_args[0][2], BytesIO)
        )  # data

        # Test with exception
        mock_minio_client.put_object.side_effect = Exception("MinIO error")

        with self.assertRaises(Exception):
            _save_plot_to_minio(fig, "line")

        plt.close(fig)

    @patch("mypackage.c_regular_generator.chart_generator.extract_column_metadata")
    @patch("mypackage.c_regular_generator.chart_generator.get_llm_chart_selection")
    @patch("mypackage.c_regular_generator.chart_generator._create_seaborn_plot")
    @patch("mypackage.c_regular_generator.chart_generator._save_plot_to_minio")
    def test_generate_chart(
        self,
        mock_save_plot,
        mock_create_plot,
        mock_get_selection,
        mock_extract_metadata,
    ):
        """Test the main generate_chart function."""
        # Set up mocks
        mock_extract_metadata.return_value = self.test_metadata
        mock_get_selection.return_value = self.test_chart_info
        mock_fig = MagicMock()
        mock_create_plot.return_value = mock_fig
        mock_save_plot.return_value = "/api/minio/temp-charts/test_chart.png"

        # Test successful chart generation
        result = generate_chart(self.test_df, "Show me sales over time")

        # Verify the result
        self.assertEqual(result, "/api/minio/temp-charts/test_chart.png")

        # Verify all the mocks were called correctly
        mock_extract_metadata.assert_called_once_with(self.test_df)
        mock_get_selection.assert_called_once()
        mock_create_plot.assert_called_once_with(self.test_df, self.test_chart_info)
        mock_save_plot.assert_called_once_with(mock_fig, "line")

        # Test with invalid column selection
        mock_get_selection.return_value = ChartInfo(
            x_axis="invalid_column", y_axis="sales", chart_type="line"
        )

        with self.assertRaises(ValueError):
            generate_chart(self.test_df, "Show me invalid data")

        # Test with exception in LLM selection
        mock_get_selection.side_effect = ValueError("Invalid LLM response")

        with self.assertRaises(ValueError):
            generate_chart(self.test_df, "Show me sales over time")


if __name__ == "__main__":
    unittest.main()
