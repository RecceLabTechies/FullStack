#!/usr/bin/env python
import json
import os
import unittest

import pandas as pd

from mypackage.b_data_processor.json_processor import (
    FilterCondition,
    SortCondition,
    _convert_metric,
    _filter_dataframe,
    _get_sample_data,
    _json_to_dataframe,
    process_json_query,
)


class TestJSONProcessor(unittest.TestCase):
    def setUp(self):
        """Set up test data and environment."""
        # Create a temporary test JSON file
        self.test_data = [
            {"name": "Product A", "price": 100, "category": "Electronics"},
            {"name": "Product B", "price": 200, "category": "Electronics"},
            {"name": "Product C", "price": 150, "category": "Furniture"},
            {"name": "Product D", "price": 300, "category": "Furniture"},
        ]
        self.test_file = "test_data.json"
        self.test_dir = "test_data"

        # Create test directory if it doesn't exist
        if not os.path.exists(self.test_dir):
            os.makedirs(self.test_dir)

        # Write test data to file
        with open(os.path.join(self.test_dir, self.test_file), "w") as f:
            json.dump(self.test_data, f)

    def tearDown(self):
        """Clean up test files."""
        if os.path.exists(os.path.join(self.test_dir, self.test_file)):
            os.remove(os.path.join(self.test_dir, self.test_file))
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_convert_metric(self):
        """Test metric conversion functionality."""
        test_cases = [
            (None, None),
            (100, 100),
            (100.5, 100.5),
            ("100", 100),
            ("100.5", 100.5),
            ("abc", "abc"),
        ]

        for input_value, expected in test_cases:
            with self.subTest(input_value=input_value):
                result = _convert_metric(input_value)
                self.assertEqual(result, expected)

    def test_filter_dataframe(self):
        """Test DataFrame filtering functionality."""
        df = pd.DataFrame(self.test_data)

        # Test cases for filtering
        test_cases = [
            (
                [
                    FilterCondition(
                        column="category", operator="==", metric="Electronics"
                    )
                ],
                None,
                None,
                2,  # Expected row count
            ),
            (
                [FilterCondition(column="price", operator=">", metric=150)],
                None,
                None,
                3,  # Expected row count
            ),
            (
                [FilterCondition(column="price", operator="<=", metric=150)],
                None,
                None,
                2,  # Expected row count
            ),
            (
                None,
                None,
                [SortCondition(column="price", ascending=True)],
                4,  # Expected row count
            ),
            (
                None,
                2,  # Limit
                None,
                2,  # Expected row count
            ),
        ]

        for filter_conditions, limit, sort_conditions, expected_rows in test_cases:
            with self.subTest(
                filter_conditions=filter_conditions,
                limit=limit,
                sort_conditions=sort_conditions,
            ):
                result = _filter_dataframe(
                    df, filter_conditions, limit, sort_conditions
                )
                self.assertEqual(len(result), expected_rows)

    def test_json_to_dataframe(self):
        """Test JSON to DataFrame conversion."""
        # Test successful conversion
        df = _json_to_dataframe(os.path.join(self.test_dir, self.test_file))
        self.assertEqual(len(df), 4)
        self.assertEqual(len(df.columns), 3)
        self.assertTrue(all(col in df.columns for col in ["name", "price", "category"]))

        # Test non-existent file
        df = _json_to_dataframe("nonexistent.json")
        self.assertTrue(df.empty)

    def test_get_sample_data(self):
        """Test sample data extraction."""
        df = pd.DataFrame(self.test_data)
        sample_data = _get_sample_data(df)

        self.assertIn("name", sample_data)
        self.assertIn("price", sample_data)
        self.assertIn("category", sample_data)

        # Check that sample data contains appropriate number of values
        self.assertEqual(len(sample_data["name"]), 4)  # All unique names
        self.assertEqual(len(sample_data["price"]), 4)  # All unique prices
        self.assertEqual(len(sample_data["category"]), 2)  # Two unique categories

    def test_process_json_query(self):
        """Test JSON query processing."""
        test_cases = [
            ("show me products with price > 150", 3),  # Should return 3 products
            ("show me electronics products", 2),  # Should return 2 products
            ("show me furniture products", 2),  # Should return 2 products
            ("show me products with price <= 150", 2),  # Should return 2 products
        ]

        for query, expected_rows in test_cases:
            with self.subTest(query=query):
                result = process_json_query(self.test_file, query, self.test_dir)
                self.assertEqual(len(result), expected_rows)

    def test_invalid_queries(self):
        """Test handling of invalid queries."""
        invalid_queries = [
            "show me products with invalid_column > 100",
            "show me products with price > invalid_value",
            "show me products with price invalid_operator 100",
        ]

        for query in invalid_queries:
            with self.subTest(query=query):
                result = process_json_query(self.test_file, query, self.test_dir)
                # Should return original DataFrame for invalid queries
                self.assertEqual(len(result), 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
