#!/usr/bin/env python
import unittest

import numpy as np
import pandas as pd

from mypackage.c_regular_generator.chart_data_generator import (
    _allow_direct_column_selection,
    _extract_key_terms,
    _get_column_stats,
    _get_column_type,
    _match_columns_to_query,
    _select_chart_type,
    _select_columns_for_chart,
    generate_chart_data,
)


class TestChartDataGenerator(unittest.TestCase):
    def setUp(self):
        """Set up test data."""
        # Create test DataFrame with various data types
        dates = pd.date_range(start="2023-01-01", periods=10)
        self.test_df = pd.DataFrame(
            {
                "date": dates,
                "sales": np.random.normal(1000, 200, 10),
                "customers": np.random.randint(50, 200, 10),
                "category": np.random.choice(["A", "B", "C"], 10),
                "is_active": np.random.choice([True, False], 10),
                "description": ["Sample text " + str(i) for i in range(10)],
            }
        )

    def test_get_column_type(self):
        """Test column type detection."""
        test_cases = [
            ("date", "datetime"),
            ("sales", "numeric"),
            ("customers", "numeric"),
            ("category", "categorical"),
            ("is_active", "boolean"),
            ("description", "text"),
        ]

        for column, expected_type in test_cases:
            with self.subTest(column=column):
                result = _get_column_type(self.test_df[column])
                self.assertEqual(result, expected_type)

    def test_get_column_stats(self):
        """Test column statistics calculation."""
        # Test numeric column
        sales_stats = _get_column_stats(self.test_df, "sales")
        self.assertEqual(sales_stats.type, "numeric")
        self.assertIsNotNone(sales_stats.min)
        self.assertIsNotNone(sales_stats.max)
        self.assertIsNotNone(sales_stats.mean)
        self.assertIsNotNone(sales_stats.median)

        # Test categorical column
        category_stats = _get_column_stats(self.test_df, "category")
        self.assertEqual(category_stats.type, "categorical")
        self.assertIsNotNone(category_stats.categories)
        self.assertEqual(category_stats.unique_count, 3)

        # Test datetime column
        date_stats = _get_column_stats(self.test_df, "date")
        self.assertEqual(date_stats.type, "datetime")
        self.assertIsNotNone(date_stats.min)
        self.assertIsNotNone(date_stats.max)

    def test_extract_key_terms(self):
        """Test key term extraction from queries."""
        test_cases = [
            ("show me sales over time", ["sales", "time"]),
            (
                "create a bar chart of customer categories",
                ["bar", "customer", "categories"],
            ),
            ("plot revenue trends", ["revenue", "trends"]),
            ("", []),
        ]

        for query, expected in test_cases:
            with self.subTest(query=query):
                result = _extract_key_terms(query)
                self.assertEqual(result, expected)

    def test_allow_direct_column_selection(self):
        """Test direct column selection from queries."""
        test_cases = [
            ("show sales vs customers", ["sales", "customers"]),
            ("plot date and sales", ["date", "sales"]),
            ("compare category with customers", ["category", "customers"]),
            ("invalid query", []),
        ]

        for query, expected in test_cases:
            with self.subTest(query=query):
                result = _allow_direct_column_selection(self.test_df, query)
                self.assertEqual(result, expected)

    def test_match_columns_to_query(self):
        """Test column matching to queries."""
        test_cases = [
            ("show sales trends", ["sales"]),
            ("analyze customer categories", ["customers", "category"]),
            ("plot date vs sales", ["date", "sales"]),
        ]

        for query, expected_columns in test_cases:
            with self.subTest(query=query):
                matches = _match_columns_to_query(self.test_df, query)
                matched_columns = list(matches.keys())
                self.assertTrue(all(col in matched_columns for col in expected_columns))

    def test_select_chart_type(self):
        """Test chart type selection."""
        test_cases = [
            ("show sales over time", "datetime", "numeric", "line"),
            ("compare categories", "categorical", "numeric", "bar"),
            (
                "show correlation between sales and customers",
                "numeric",
                "numeric",
                "scatter",
            ),
            ("show distribution of sales by category", "categorical", "numeric", "box"),
            (
                "show relationship between categories",
                "categorical",
                "categorical",
                "heatmap",
            ),
        ]

        for query, x_type, y_type, expected in test_cases:
            with self.subTest(query=query):
                result = _select_chart_type(x_type, y_type, query)
                self.assertEqual(result, expected)

    def test_select_columns_for_chart(self):
        """Test column selection for charts."""
        test_cases = [
            ("show sales over time", ["date", "sales"]),
            ("compare customer categories", ["category", "customers"]),
            ("plot sales vs customers", ["sales", "customers"]),
        ]

        for query, expected_columns in test_cases:
            with self.subTest(query=query):
                chart_info = _select_columns_for_chart(self.test_df, query)
                self.assertEqual(chart_info.x_axis, expected_columns[0])
                self.assertEqual(chart_info.y_axis, expected_columns[1])

    def test_generate_chart_data(self):
        """Test chart data generation."""
        test_cases = [
            ("show sales over time", "LineChart"),
            ("compare customer categories", "BarChart"),
            ("plot sales vs customers", "ScatterChart"),
            ("show distribution of sales by category", "ComposedChart"),
            ("show relationship between categories", "Heatmap"),
        ]

        for query, expected_type in test_cases:
            with self.subTest(query=query):
                chart_data = generate_chart_data(self.test_df, query)
                self.assertEqual(chart_data["type"], expected_type)
                self.assertIn("data", chart_data)
                self.assertIn("xAxis", chart_data)
                self.assertIn("yAxis", chart_data)

    def test_invalid_queries(self):
        """Test handling of invalid queries."""
        invalid_queries = [
            "",  # Empty query
            "show invalid column",  # Non-existent column
            "plot nothing",  # No valid columns
            "show sales and invalid",  # One valid, one invalid column
        ]

        for query in invalid_queries:
            with self.subTest(query=query):
                with self.assertRaises(ValueError):
                    generate_chart_data(self.test_df, query)


if __name__ == "__main__":
    unittest.main(verbosity=2)
