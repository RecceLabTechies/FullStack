#!/usr/bin/env python
import json
import os
import unittest

from mypackage.b_data_processor.json_selector import (
    JSONFileNotFoundError,
    _compare_matches,
    _extract_json_info,
    _extract_key_terms,
    _match_headers_to_query,
    _match_values_to_query,
    _search_for_values,
    select_json_for_query,
)


class TestJSONSelector(unittest.TestCase):
    def setUp(self):
        """Set up test data and environment."""
        self.test_dir = "test_data"
        self.test_files = {
            "sales_data.json": [
                {"month": "Jan", "sales": 1000, "product": "A"},
                {"month": "Feb", "sales": 2000, "product": "B"},
            ],
            "customer_data.json": [
                {"name": "John", "age": 30, "city": "New York"},
                {"name": "Jane", "age": 25, "city": "Los Angeles"},
            ],
            "inventory.json": [
                {"item": "Laptop", "stock": 50, "category": "Electronics"},
                {"item": "Chair", "stock": 100, "category": "Furniture"},
            ],
        }

        # Create test directory if it doesn't exist
        if not os.path.exists(self.test_dir):
            os.makedirs(self.test_dir)

        # Write test files
        for filename, data in self.test_files.items():
            with open(os.path.join(self.test_dir, filename), "w") as f:
                json.dump(data, f)

    def tearDown(self):
        """Clean up test files."""
        for filename in self.test_files:
            filepath = os.path.join(self.test_dir, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_extract_key_terms(self):
        """Test key term extraction from queries."""
        test_cases = [
            ("show me sales data", ["show", "sales", "data"]),
            ("analyze customer demographics", ["analyze", "customer", "demographics"]),
            ("compare product performance", ["compare", "product", "performance"]),
            ("", []),
        ]

        for query, expected in test_cases:
            with self.subTest(query=query):
                result = _extract_key_terms(query)
                self.assertEqual(result, expected)

    def test_extract_json_info(self):
        """Test JSON file information extraction."""
        json_info = _extract_json_info(self.test_dir)

        # Check that all test files are processed
        self.assertEqual(len(json_info), len(self.test_files))

        # Check structure of extracted info
        for filename, info in json_info.items():
            self.assertIn("type", info)
            self.assertIn("fields", info)
            self.assertIn("field_types", info)
            self.assertIn("sample_values", info)
            self.assertIn("unique_values", info)

    def test_search_for_values(self):
        """Test value search functionality."""
        json_info = _extract_json_info(self.test_dir)
        search_terms = ["New York", "Electronics", "1000"]

        results = _search_for_values(json_info, search_terms)

        # Check that matches are found
        self.assertTrue(len(results) > 0)

        # Check specific matches
        self.assertIn("customer_data.json", results)
        self.assertIn("inventory.json", results)
        self.assertIn("sales_data.json", results)

    def test_match_headers_to_query(self):
        """Test header matching functionality."""
        json_info = _extract_json_info(self.test_dir)
        query = "show me sales and customer data"

        matches, best_match, matching_fields = _match_headers_to_query(json_info, query)

        # Check that matches are found
        self.assertTrue(len(matches) > 0)
        self.assertIsNotNone(best_match)
        self.assertTrue(len(matching_fields) > 0)

    def test_match_values_to_query(self):
        """Test value matching functionality."""
        json_info = _extract_json_info(self.test_dir)
        query = "show data for New York and Electronics"

        matches, best_match, matching_values = _match_values_to_query(json_info, query)

        # Check that matches are found
        self.assertTrue(len(matches) > 0)
        self.assertIsNotNone(best_match)
        self.assertTrue(len(matching_values) > 0)

    def test_compare_matches(self):
        """Test match comparison functionality."""
        header_matches = {
            "sales_data.json": {
                "score": 2,
                "fields": ["sales"],
                "reason": "Contains sales data",
            },
            "customer_data.json": {
                "score": 1,
                "fields": ["name"],
                "reason": "Contains customer data",
            },
        }

        value_matches = {
            "sales_data.json": {
                "score": 1,
                "values": {"sales": ["1000"]},
                "fields": ["sales"],
            },
            "customer_data.json": {
                "score": 2,
                "values": {"city": ["New York"]},
                "fields": ["city"],
            },
        }

        best_match, best_match_details, alternative_matches = _compare_matches(
            header_matches, value_matches
        )

        self.assertIsNotNone(best_match)
        self.assertTrue(len(best_match_details) > 0)
        self.assertTrue(len(alternative_matches) > 0)

    def test_select_json_for_query(self):
        """Test JSON file selection for queries."""
        test_cases = [
            ("show me sales data", "sales_data.json"),
            ("analyze customer demographics", "customer_data.json"),
            ("check inventory levels", "inventory.json"),
            ("compare product sales", "sales_data.json"),
        ]

        for query, expected_file in test_cases:
            with self.subTest(query=query):
                result = select_json_for_query(query, self.test_dir)
                self.assertEqual(result, expected_file)

    def test_invalid_queries(self):
        """Test handling of invalid queries."""
        invalid_queries = [
            "show me weather data",  # No matching data
            "analyze non-existent data",  # No matching data
            "",  # Empty query
        ]

        for query in invalid_queries:
            with self.subTest(query=query):
                with self.assertRaises(JSONFileNotFoundError):
                    select_json_for_query(query, self.test_dir)

    def test_nonexistent_directory(self):
        """Test handling of nonexistent directory."""
        with self.assertRaises(JSONFileNotFoundError):
            select_json_for_query("show me sales data", "nonexistent_dir")


if __name__ == "__main__":
    unittest.main(verbosity=2)
