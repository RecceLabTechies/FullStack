#!/usr/bin/env python
"""
Test module for generate_analysis_queries.py

This module contains unit tests for the analysis queries generation functionality.
"""

import unittest
from unittest.mock import MagicMock, patch

from mypackage.d_report_generator.generate_analysis_queries import (
    QueryItem,
    QueryList,
    QueryType,
    _analyze_collections,
    _format_collections_for_prompt,
    _parse_llm_response,
    generate_analysis_queries,
)


class TestGenerateAnalysisQueries(unittest.TestCase):
    """Test cases for the generate_analysis_queries module."""

    def setUp(self):
        """Set up test data."""
        # Sample collection info for testing
        self.test_collections_info = {
            "campaign_performance": {
                "date": {
                    "type": "datetime",
                    "stats": {"min": "2023-01-01", "max": "2023-12-31"},
                },
                "channel": {
                    "type": "categorical",
                    "stats": {
                        "unique_values": [
                            "Facebook",
                            "Google",
                            "LinkedIn",
                            "Twitter",
                            "Email",
                        ]
                    },
                },
                "leads": {
                    "type": "numerical",
                    "stats": {"min": 0, "max": 500, "mean": 120.5},
                },
                "revenue": {
                    "type": "numerical",
                    "stats": {"min": 0, "max": 50000, "mean": 12500.75},
                },
            },
            "customer_data": {
                "customer_id": {
                    "type": "categorical",
                    "stats": {"unique_values": ["C001", "C002", "C003", "..."]},
                },
                "signup_date": {
                    "type": "datetime",
                    "stats": {"min": "2022-01-01", "max": "2023-12-31"},
                },
                "country": {
                    "type": "categorical",
                    "stats": {
                        "unique_values": [
                            "USA",
                            "Canada",
                            "UK",
                            "Germany",
                            "France",
                            "...",
                        ]
                    },
                },
                "lifetime_value": {
                    "type": "numerical",
                    "stats": {"min": 0, "max": 25000, "mean": 2750.50},
                },
            },
        }

        # Sample LLM response
        self.test_llm_response = """
Generate a chart of leads by channel | campaign_performance
Generate a description of revenue trends over time | campaign_performance
Generate a chart of customer lifetime value by country | customer_data
"""

    @patch("mypackage.d_report_generator.generate_analysis_queries.Database")
    def test_analyze_collections(self, mock_database):
        """Test collection analysis functionality."""
        # Set up mock database
        mock_database.db = MagicMock()
        mock_database.analyze_collections.return_value = self.test_collections_info

        # Test successful analysis
        result = _analyze_collections()

        # Verify the result
        self.assertEqual(result, self.test_collections_info)
        mock_database.analyze_collections.assert_called_once()

        # Test with database initialization
        mock_database.db = None
        mock_database.initialize.return_value = True

        result = _analyze_collections()

        # Verify the result
        self.assertEqual(result, self.test_collections_info)
        mock_database.initialize.assert_called_once()

        # Test with database error
        mock_database.analyze_collections.side_effect = Exception("Database error")

        with self.assertRaises(Exception):
            _analyze_collections()

    def test_format_collections_for_prompt(self):
        """Test formatting collections for LLM prompt."""
        formatted = _format_collections_for_prompt(self.test_collections_info)

        # Check that the formatted string contains key information
        self.assertIn("campaign_performance:", formatted)
        self.assertIn("customer_data:", formatted)

        # Check field formatting
        self.assertIn("date (datetime, range:", formatted)
        self.assertIn(
            "channel (categorical, values: Facebook, Google, LinkedIn, Twitter, Email)",
            formatted,
        )
        self.assertIn("leads (numerical, range: 0 to 500)", formatted)

        # Check truncation of long lists
        self.assertIn("...", formatted)

        # Test with empty collections
        empty_formatted = _format_collections_for_prompt({})
        self.assertEqual(empty_formatted, "")

    def test_parse_llm_response(self):
        """Test parsing LLM response into structured queries."""
        # Test with valid response
        result = _parse_llm_response(self.test_llm_response)

        # Verify the result
        self.assertIsInstance(result, QueryList)
        self.assertEqual(len(result.queries), 3)

        # Check first query
        self.assertEqual(
            result.queries[0].query, "Generate a chart of leads by channel"
        )
        self.assertEqual(result.queries[0].query_type, QueryType.CHART)
        self.assertEqual(result.queries[0].collection_name, "campaign_performance")

        # Check second query
        self.assertEqual(
            result.queries[1].query,
            "Generate a description of revenue trends over time",
        )
        self.assertEqual(result.queries[1].query_type, QueryType.DESCRIPTION)
        self.assertEqual(result.queries[1].collection_name, "campaign_performance")

        # Test with response object that has content attribute
        mock_response = MagicMock()
        mock_response.content = self.test_llm_response

        result = _parse_llm_response(mock_response)
        self.assertEqual(len(result.queries), 3)

        # Test with invalid format (missing separator)
        invalid_response = """
Generate a chart of leads by channel for campaign_performance
Generate a description of revenue trends
Invalid line
"""
        with patch(
            "mypackage.d_report_generator.generate_analysis_queries.is_collection_accessible",
            return_value=True,
        ):
            result = _parse_llm_response(invalid_response)
            self.assertEqual(len(result.queries), 0)

        # Test with duplicate queries
        duplicate_response = """
Generate a chart of leads by channel | campaign_performance
Generate a chart of leads by channel | campaign_performance
Generate a description of revenue trends | campaign_performance
"""
        with patch(
            "mypackage.d_report_generator.generate_analysis_queries.is_collection_accessible",
            return_value=True,
        ):
            result = _parse_llm_response(duplicate_response)
            self.assertEqual(len(result.queries), 2)  # Should deduplicate

        # Test with inaccessible collection
        with patch(
            "mypackage.d_report_generator.generate_analysis_queries.is_collection_accessible",
            return_value=False,
        ):
            result = _parse_llm_response(self.test_llm_response)
            self.assertEqual(len(result.queries), 0)  # All collections inaccessible

    @patch(
        "mypackage.d_report_generator.generate_analysis_queries._analyze_collections"
    )
    @patch("mypackage.d_report_generator.generate_analysis_queries.get_groq_llm")
    def test_generate_analysis_queries(
        self, mock_get_groq_llm, mock_analyze_collections
    ):
        """Test the main generate_analysis_queries function."""
        # Set up mocks
        mock_analyze_collections.return_value = self.test_collections_info

        # Set up mock LLM
        mock_llm = MagicMock()
        mock_get_groq_llm.return_value = mock_llm
        mock_chain = MagicMock()
        mock_llm.__or__.return_value = mock_chain
        mock_chain.__or__.return_value = mock_chain

        # Mock the chain invoke to return a QueryList
        expected_result = QueryList(
            queries=[
                QueryItem(
                    query="Generate a chart of leads by channel",
                    query_type=QueryType.CHART,
                    collection_name="campaign_performance",
                ),
                QueryItem(
                    query="Generate a description of revenue trends over time",
                    query_type=QueryType.DESCRIPTION,
                    collection_name="campaign_performance",
                ),
            ]
        )
        mock_chain.invoke.return_value = expected_result

        # Test successful query generation
        result = generate_analysis_queries(
            "What is the performance of our marketing campaigns?"
        )

        # Verify the result
        self.assertEqual(result, expected_result)

        # Verify all the mocks were called correctly
        mock_analyze_collections.assert_called_once()
        mock_get_groq_llm.assert_called_once()
        mock_chain.invoke.assert_called_once()

        # Test with empty user query
        with self.assertRaises(ValueError):
            generate_analysis_queries("")

        # Test with no collections
        mock_analyze_collections.return_value = {}

        with self.assertRaises(ValueError):
            generate_analysis_queries(
                "What is the performance of our marketing campaigns?"
            )

        # Test with LLM error
        mock_analyze_collections.return_value = self.test_collections_info
        mock_chain.invoke.side_effect = Exception("LLM error")

        with self.assertRaises(ValueError):
            generate_analysis_queries(
                "What is the performance of our marketing campaigns?"
            )

    def test_query_type_enum(self):
        """Test the QueryType enum."""
        self.assertEqual(QueryType.CHART.value, "chart")
        self.assertEqual(QueryType.DESCRIPTION.value, "description")

        # Test string comparison
        self.assertEqual(QueryType.CHART, QueryType("chart"))
        self.assertEqual(QueryType.DESCRIPTION, QueryType("description"))

    def test_query_item_model(self):
        """Test the QueryItem pydantic model."""
        # Test valid creation
        item = QueryItem(
            query="Generate a chart of leads by channel",
            query_type=QueryType.CHART,
            collection_name="campaign_performance",
        )

        self.assertEqual(item.query, "Generate a chart of leads by channel")
        self.assertEqual(item.query_type, QueryType.CHART)
        self.assertEqual(item.collection_name, "campaign_performance")

        # Test with string for query_type
        item = QueryItem(
            query="Generate a chart of leads by channel",
            query_type="chart",
            collection_name="campaign_performance",
        )

        self.assertEqual(item.query_type, QueryType.CHART)

    def test_query_list_model(self):
        """Test the QueryList pydantic model."""
        # Test valid creation
        items = [
            QueryItem(
                query="Generate a chart of leads by channel",
                query_type=QueryType.CHART,
                collection_name="campaign_performance",
            ),
            QueryItem(
                query="Generate a description of revenue trends",
                query_type=QueryType.DESCRIPTION,
                collection_name="campaign_performance",
            ),
        ]

        query_list = QueryList(queries=items)

        self.assertEqual(len(query_list.queries), 2)
        self.assertEqual(query_list.queries[0].query_type, QueryType.CHART)
        self.assertEqual(query_list.queries[1].query_type, QueryType.DESCRIPTION)


if __name__ == "__main__":
    unittest.main()
