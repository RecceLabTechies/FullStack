#!/usr/bin/env python
import unittest

import numpy as np
import pandas as pd

from mypackage.c_regular_generator.description_generator import (
    _allow_direct_column_selection,
    _analyze_dataframe,
    _extract_key_terms,
    _get_column_stats,
    _interpret_correlation,
    _match_columns_to_query,
    _select_columns_for_analysis,
    generate_description,
)


class TestDescriptionGenerator(unittest.TestCase):
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

    def test_extract_key_terms(self):
        """Test key term extraction from queries."""
        test_cases = [
            ("describe sales trends", ["describe", "sales", "trends"]),
            ("analyze customer demographics", ["analyze", "customer", "demographics"]),
            ("summarize product performance", ["summarize", "product", "performance"]),
            ("", []),
        ]

        for query, expected in test_cases:
            with self.subTest(query=query):
                result = _extract_key_terms(query)
                self.assertEqual(result, expected)

    def test_analyze_dataframe(self):
        """Test DataFrame analysis."""
        analysis = _analyze_dataframe(self.test_df)

        # Check basic structure
        self.assertIn("row_count", analysis)
        self.assertIn("column_count", analysis)
        self.assertIn("column_names", analysis)
        self.assertIn("column_types", analysis)
        self.assertIn("missing_values", analysis)
        self.assertIn("numeric_columns", analysis)
        self.assertIn("categorical_columns", analysis)
        self.assertIn("datetime_columns", analysis)

        # Check specific values
        self.assertEqual(analysis["row_count"], 10)
        self.assertEqual(analysis["column_count"], 6)
        self.assertEqual(len(analysis["column_names"]), 6)
        self.assertEqual(len(analysis["column_types"]), 6)
        self.assertEqual(len(analysis["missing_values"]), 6)

    def test_get_column_stats(self):
        """Test column statistics calculation."""
        # Test numeric column
        sales_stats = _get_column_stats(self.test_df, "sales")
        self.assertEqual(sales_stats["type"], "numeric")
        self.assertIn("min", sales_stats)
        self.assertIn("max", sales_stats)
        self.assertIn("mean", sales_stats)
        self.assertIn("median", sales_stats)
        self.assertIn("std", sales_stats)
        self.assertIn("unique_count", sales_stats)
        self.assertIn("missing_count", sales_stats)
        self.assertIn("skewness", sales_stats)
        self.assertIn("has_outliers", sales_stats)
        self.assertIn("outlier_count", sales_stats)

        # Test categorical column
        category_stats = _get_column_stats(self.test_df, "category")
        self.assertEqual(category_stats["type"], "categorical")
        self.assertIn("unique_count", category_stats)
        self.assertIn("missing_count", category_stats)
        self.assertIn("categories", category_stats)

        # Test datetime column
        date_stats = _get_column_stats(self.test_df, "date")
        self.assertEqual(date_stats["type"], "datetime")
        self.assertIn("min", date_stats)
        self.assertIn("max", date_stats)
        self.assertIn("unique_count", date_stats)
        self.assertIn("missing_count", date_stats)

    def test_match_columns_to_query(self):
        """Test column matching to queries."""
        test_cases = [
            ("describe sales trends", ["sales"]),
            ("analyze customer categories", ["customers", "category"]),
            ("summarize date and sales", ["date", "sales"]),
        ]

        for query, expected_columns in test_cases:
            with self.subTest(query=query):
                matches = _match_columns_to_query(self.test_df, query)
                matched_columns = list(matches.keys())
                self.assertTrue(all(col in matched_columns for col in expected_columns))

    def test_allow_direct_column_selection(self):
        """Test direct column selection from queries."""
        test_cases = [
            ("describe sales and customers", ["sales", "customers"]),
            ("analyze date and sales", ["date", "sales"]),
            ("summarize category and customers", ["category", "customers"]),
            ("invalid query", []),
        ]

        for query, expected in test_cases:
            with self.subTest(query=query):
                result = _allow_direct_column_selection(self.test_df, query)
                self.assertEqual(result, expected)

    def test_select_columns_for_analysis(self):
        """Test column selection for analysis."""
        test_cases = [
            ("describe sales trends", ["sales"]),
            ("analyze customer categories", ["customers", "category"]),
            ("summarize date and sales", ["date", "sales"]),
        ]

        for query, expected_columns in test_cases:
            with self.subTest(query=query):
                result = _select_columns_for_analysis(query, self.test_df)
                self.assertTrue(all(col in result for col in expected_columns))

    def test_interpret_correlation(self):
        """Test correlation interpretation."""
        test_cases = [
            (0.8, "very strong positive"),
            (0.5, "moderate positive"),
            (0.2, "weak positive"),
            (-0.8, "very strong negative"),
            (-0.5, "moderate negative"),
            (-0.2, "weak negative"),
            (0.05, "negligible positive"),
            (-0.05, "negligible negative"),
        ]

        for value, expected in test_cases:
            with self.subTest(value=value):
                result = _interpret_correlation(value)
                self.assertEqual(result, expected)

    def test_generate_description(self):
        """Test description generation."""
        test_cases = [
            "describe sales trends",
            "analyze customer categories",
            "summarize date and sales",
            "compare sales and customers",
        ]

        for query in test_cases:
            with self.subTest(query=query):
                description = generate_description(self.test_df, query)
                self.assertIsInstance(description, str)
                self.assertTrue(len(description) > 0)

    def test_invalid_queries(self):
        """Test handling of invalid queries."""
        invalid_queries = [
            "",  # Empty query
            "describe invalid column",  # Non-existent column
            "analyze nothing",  # No valid columns
            "summarize sales and invalid",  # One valid, one invalid column
        ]

        for query in invalid_queries:
            with self.subTest(query=query):
                description = generate_description(self.test_df, query)
                self.assertIsInstance(description, str)
                self.assertTrue(len(description) > 0)  # Should return error message


if __name__ == "__main__":
    unittest.main(verbosity=2)
