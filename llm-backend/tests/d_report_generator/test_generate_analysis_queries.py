#!/usr/bin/env python
import json
import unittest
from pathlib import Path

from mypackage.d_report_generator.generate_analysis_queries import (
    QueryType,
    _extract_headers,
    _format_schemas_for_prompt,
    _parse_llm_response,
    _recursive_json_schema_extractor,
    generate_analysis_queries,
)


class TestGenerateAnalysisQueries(unittest.TestCase):
    def setUp(self):
        """Set up test data and create temporary test files."""
        # Create a temporary test directory
        self.test_dir = Path("test_data")
        self.test_dir.mkdir(exist_ok=True)

        # Create test JSON files with different structures
        self.sales_data = {
            "date": "2023-01-01",
            "amount": 1000,
            "customer_id": "C001",
            "product": "Product A",
        }
        self.customer_data = [
            {"id": "C001", "name": "John Doe", "age": 30, "city": "New York"},
            {"id": "C002", "name": "Jane Smith", "age": 25, "city": "Los Angeles"},
        ]
        self.inventory_data = {
            "products": [
                {"id": "P001", "name": "Product A", "stock": 100, "price": 50},
                {"id": "P002", "name": "Product B", "stock": 200, "price": 75},
            ]
        }

        # Write test files
        with open(self.test_dir / "sales.json", "w") as f:
            json.dump(self.sales_data, f)
        with open(self.test_dir / "customers.json", "w") as f:
            json.dump(self.customer_data, f)
        with open(self.test_dir / "inventory.json", "w") as f:
            json.dump(self.inventory_data, f)

    def tearDown(self):
        """Clean up test files."""
        # Remove test files
        for file in self.test_dir.glob("*.json"):
            file.unlink()
        # Remove test directory
        self.test_dir.rmdir()

    def test_extract_headers(self):
        """Test header extraction from JSON files."""
        test_cases = [
            ("sales.json", ["date", "amount", "customer_id", "product"]),
            ("customers.json", ["id", "name", "age", "city"]),
            ("inventory.json", ["products"]),
        ]

        for file_name, expected_headers in test_cases:
            with self.subTest(file_name=file_name):
                file_path = self.test_dir / file_name
                headers = _extract_headers(str(file_path))
                self.assertEqual(set(headers), set(expected_headers))

    def test_extract_headers_invalid_file(self):
        """Test header extraction from invalid files."""
        # Test non-existent file
        with self.assertRaises(FileNotFoundError):
            _extract_headers("nonexistent.json")

        # Test invalid JSON file
        invalid_json_path = self.test_dir / "invalid.json"
        with open(invalid_json_path, "w") as f:
            f.write("invalid json content")
        with self.assertRaises(json.JSONDecodeError):
            _extract_headers(str(invalid_json_path))

    def test_recursive_json_schema_extractor(self):
        """Test recursive schema extraction from directory."""
        # Create a subdirectory with additional JSON file
        subdir = self.test_dir / "subdir"
        subdir.mkdir()
        with open(subdir / "subdata.json", "w") as f:
            json.dump({"key": "value"}, f)

        schemas = _recursive_json_schema_extractor(str(self.test_dir))

        # Check that all JSON files are included
        self.assertEqual(len(schemas), 4)  # 3 in root + 1 in subdir
        self.assertIn(str(self.test_dir / "sales.json"), schemas)
        self.assertIn(str(self.test_dir / "customers.json"), schemas)
        self.assertIn(str(self.test_dir / "inventory.json"), schemas)
        self.assertIn(str(subdir / "subdata.json"), schemas)

    def test_format_schemas_for_prompt(self):
        """Test schema formatting for prompt."""
        schemas = {
            "sales.json": ["date", "amount", "customer_id"],
            "customers.json": ["id", "name", "age"],
        }
        formatted = _format_schemas_for_prompt(schemas)

        # Check format
        self.assertIn("sales.json: [date, amount, customer_id]", formatted)
        self.assertIn("customers.json: [id, name, age]", formatted)

    def test_parse_llm_response(self):
        """Test parsing of LLM response."""
        test_responses = [
            """Generate a chart of sales over time | sales.json
Generate a description of customer demographics | customers.json
Generate a chart of inventory levels | inventory.json""",
            """Generate a description of sales trends | sales.json
Generate a chart of customer age distribution | customers.json""",
        ]

        for response in test_responses:
            with self.subTest(response=response):
                result = _parse_llm_response(response)
                self.assertIsNotNone(result)
                self.assertTrue(len(result.queries) > 0)

                # Check query types
                for query in result.queries:
                    self.assertIn(
                        query.query_type, [QueryType.CHART, QueryType.DESCRIPTION]
                    )
                    self.assertTrue(query.file_name.endswith(".json"))

    def test_parse_llm_response_invalid(self):
        """Test parsing of invalid LLM responses."""
        invalid_responses = [
            "",  # Empty response
            "Invalid format",  # Missing separator
            "Generate a chart of sales |",  # Missing file name
            "Invalid type of sales | sales.json",  # Invalid query type
        ]

        for response in invalid_responses:
            with self.subTest(response=response):
                result = _parse_llm_response(response)
                self.assertEqual(len(result.queries), 0)

    def test_generate_analysis_queries(self):
        """Test generation of analysis queries."""
        test_queries = [
            "What is the average sales amount?",
            "Show customer demographics",
            "Analyze inventory levels",
        ]

        for query in test_queries:
            with self.subTest(query=query):
                result = generate_analysis_queries(query)
                self.assertIsNotNone(result)
                self.assertTrue(len(result.queries) > 0)

                # Check query structure
                for query_item in result.queries:
                    self.assertIsInstance(query_item.query, str)
                    self.assertIn(
                        query_item.query_type, [QueryType.CHART, QueryType.DESCRIPTION]
                    )
                    self.assertTrue(query_item.file_name.endswith(".json"))

    def test_generate_analysis_queries_invalid(self):
        """Test handling of invalid queries."""
        invalid_queries = [
            "",  # Empty query
            "   ",  # Whitespace only
            None,  # None value
        ]

        for query in invalid_queries:
            with self.subTest(query=query):
                with self.assertRaises(ValueError):
                    generate_analysis_queries(query)


if __name__ == "__main__":
    unittest.main(verbosity=2)
