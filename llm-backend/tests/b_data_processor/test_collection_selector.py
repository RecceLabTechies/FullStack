#!/usr/bin/env python
"""
Test module for collection_selector.py

This module contains unit tests for the collection selection functionality.
"""

import unittest
from unittest.mock import patch, MagicMock, ANY

from mypackage.b_data_processor.collection_selector import (
    _extract_key_terms,
    _extract_collection_info,
    _match_headers_to_query,
    _match_values_to_query,
    _compare_matches,
    _format_collection_info_for_prompt,
    _resolve_ambiguous_matches,
    _select_collection_with_llm,
    select_collection_for_query,
    CollectionNotFoundError,
    FieldProcessor,
)


class TestCollectionSelector(unittest.TestCase):
    """Test cases for the collection selector module."""

    def setUp(self):
        """Set up test data."""
        # Sample collection info for testing
        self.test_collection_info = {
            "sales": {
                "type": "list",
                "count": 100,
                "fields": ["date", "product", "revenue", "channel"],
                "field_types": {
                    "date": "datetime",
                    "product": "categorical",
                    "revenue": "numerical",
                    "channel": "categorical",
                },
                "sample_values": {
                    "date": ["2023-01-01", "2023-12-31"],
                    "product": ["WidgetA", "GadgetB", "ToolC"],
                    "revenue": ["1000", "5000"],
                    "channel": ["Facebook", "Google", "LinkedIn"],
                },
                "unique_values": {
                    "date": ["2023-01-01", "2023-12-31"],
                    "product": ["WidgetA", "GadgetB", "ToolC", "DeviceD", "AppE"],
                    "revenue": ["1000", "5000"],
                    "channel": ["Facebook", "Google", "LinkedIn", "Twitter", "Email"],
                },
            },
            "customers": {
                "type": "list",
                "count": 50,
                "fields": ["customer_id", "name", "email", "country"],
                "field_types": {
                    "customer_id": "numerical",
                    "name": "categorical",
                    "email": "categorical",
                    "country": "categorical",
                },
                "sample_values": {
                    "customer_id": ["1001", "1050"],
                    "name": ["John Smith", "Jane Doe", "Bob Johnson"],
                    "email": ["john@example.com", "jane@example.com"],
                    "country": ["USA", "Canada", "UK"],
                },
                "unique_values": {
                    "customer_id": ["1001", "1050"],
                    "name": ["John Smith", "Jane Doe", "Bob Johnson", "Alice Brown"],
                    "email": [
                        "john@example.com",
                        "jane@example.com",
                        "bob@example.com",
                    ],
                    "country": ["USA", "Canada", "UK", "Australia", "Germany"],
                },
            },
        }

    def test_extract_key_terms(self):
        """Test the key term extraction function."""
        # Test with simple query
        terms = _extract_key_terms("Show me sales data for Facebook")
        self.assertIn("sales", terms)
        self.assertIn("facebook", terms)
        self.assertNotIn("me", terms)
        self.assertNotIn("for", terms)

        # Test with more complex query
        terms = _extract_key_terms(
            "What is the revenue from LinkedIn campaigns in December?"
        )
        self.assertIn("revenue", terms)
        self.assertIn("linkedin", terms)
        self.assertIn("campaigns", terms)
        self.assertIn("december", terms)
        self.assertNotIn("what", terms)
        self.assertNotIn("the", terms)
        self.assertNotIn("from", terms)

    @patch("mypackage.b_data_processor.collection_selector.Database")
    def test_extract_collection_info(self, mock_database):
        """Test collection info extraction."""
        # Set up mock database response
        mock_database.analyze_collections.return_value = {
            "sales": {
                "date": {
                    "type": "datetime",
                    "stats": {"min": "2023-01-01", "max": "2023-12-31"},
                },
                "product": {
                    "type": "categorical",
                    "stats": {"unique_values": ["WidgetA", "GadgetB"]},
                },
                "revenue": {"type": "numerical", "stats": {"min": 1000, "max": 5000}},
            }
        }

        # Test the function
        result = _extract_collection_info()

        # Verify the result
        self.assertIn("sales", result)
        self.assertEqual(result["sales"]["type"], "list")
        self.assertIn("date", result["sales"]["fields"])
        self.assertIn("product", result["sales"]["fields"])
        self.assertIn("revenue", result["sales"]["fields"])

        # Verify field types
        self.assertEqual(result["sales"]["field_types"]["date"], "datetime")
        self.assertEqual(result["sales"]["field_types"]["product"], "categorical")
        self.assertEqual(result["sales"]["field_types"]["revenue"], "numerical")

        # Verify sample values
        self.assertEqual(
            result["sales"]["sample_values"]["date"], ["2023-01-01", "2023-12-31"]
        )
        self.assertEqual(
            result["sales"]["sample_values"]["product"], ["WidgetA", "GadgetB"]
        )

        # Test with empty response
        mock_database.analyze_collections.return_value = {}
        result = _extract_collection_info()
        self.assertEqual(result, {})

    def test_match_headers_to_query(self):
        """Test matching headers to query."""
        # Test with matching query
        header_matches, best_match, matching_fields = _match_headers_to_query(
            self.test_collection_info, "Show me revenue by channel"
        )

        # Verify results
        self.assertEqual(best_match, "sales")
        self.assertIn("revenue", matching_fields)
        self.assertIn("channel", matching_fields)
        self.assertIn("sales", header_matches)
        self.assertTrue(header_matches["sales"]["score"] > 0)

        # Test with query matching multiple collections
        header_matches, best_match, matching_fields = _match_headers_to_query(
            self.test_collection_info, "Show me country data"
        )
        self.assertEqual(best_match, "customers")
        self.assertIn("country", matching_fields)

        # Test with non-matching query
        header_matches, best_match, matching_fields = _match_headers_to_query(
            self.test_collection_info, "Show me weather data"
        )
        self.assertIsNone(best_match)
        self.assertEqual(matching_fields, [])
        self.assertEqual(header_matches, {})

    def test_match_values_to_query(self):
        """Test matching values to query."""
        # Test with matching query
        value_matches, best_match, matching_values = _match_values_to_query(
            self.test_collection_info, "Show me data for LinkedIn"
        )

        # Verify results
        self.assertEqual(best_match, "sales")
        self.assertIn("channel", matching_values)
        self.assertIn("LinkedIn", matching_values["channel"])
        self.assertIn("sales", value_matches)
        self.assertTrue(value_matches["sales"]["score"] > 0)

        # Test with query matching multiple collections
        value_matches, best_match, matching_values = _match_values_to_query(
            self.test_collection_info, "Show me data for USA"
        )
        self.assertEqual(best_match, "customers")
        self.assertIn("country", matching_values)
        self.assertIn("USA", matching_values["country"])

        # Test with non-matching query
        value_matches, best_match, matching_values = _match_values_to_query(
            self.test_collection_info, "Show me data for Mars"
        )
        self.assertIsNone(best_match)
        self.assertEqual(matching_values, {})
        self.assertEqual(value_matches, {})

    def test_compare_matches(self):
        """Test comparing and combining matches."""
        # Set up test matches
        header_matches = {
            "sales": {
                "score": 5,
                "fields": ["revenue", "channel"],
                "reason": "Field names match query terms: revenue, channel",
            },
            "customers": {
                "score": 2,
                "fields": ["country"],
                "reason": "Field names match query terms: country",
            },
        }

        value_matches = {
            "sales": {
                "score": 3,
                "fields": ["channel"],
                "values": {"channel": ["LinkedIn"]},
                "reason": "Values match query terms: 'channel' contains: LinkedIn",
            },
            "customers": {
                "score": 1,
                "fields": ["country"],
                "values": {"country": ["USA"]},
                "reason": "Values match query terms: 'country' contains: USA",
            },
        }

        # Test the function
        best_match, best_match_details, alternatives = _compare_matches(
            header_matches, value_matches
        )

        # Verify results
        self.assertEqual(best_match, "sales")
        self.assertTrue(best_match_details["score"] > 0)
        self.assertIn("revenue", best_match_details["fields"])
        self.assertIn("channel", best_match_details["fields"])
        self.assertEqual(len(alternatives), 1)
        self.assertEqual(alternatives[0]["collection"], "customers")

    def test_format_collection_info_for_prompt(self):
        """Test formatting collection info for LLM prompt."""
        formatted_info = _format_collection_info_for_prompt(self.test_collection_info)

        # Verify the formatted string contains key information
        self.assertIn("📄 Collection: sales", formatted_info)
        self.assertIn("📄 Collection: customers", formatted_info)
        self.assertIn("🔑 Fields: date, product, revenue, channel", formatted_info)
        self.assertIn("📊 Sample values:", formatted_info)
        self.assertIn("LinkedIn", formatted_info)
        self.assertIn("🔍 Unique values by field:", formatted_info)

    @patch("mypackage.b_data_processor.collection_selector.get_groq_llm")
    def test_resolve_ambiguous_matches(self, mock_get_groq_llm):
        """Test resolving ambiguous matches with LLM."""
        # Set up mock LLM
        mock_llm = MagicMock()
        mock_get_groq_llm.return_value = mock_llm
        mock_llm.invoke.return_value = MagicMock(
            content="collection: sales\nreason: This collection contains revenue and channel data\nmatching_fields: revenue, channel"
        )

        # Set up test data
        best_match_details = {
            "score": 8,
            "fields": ["revenue", "channel"],
            "values": {"channel": ["LinkedIn"]},
            "reason": "Field and value matches",
            "header_score": 5,
            "value_score": 3,
        }

        alternative_matches = [
            {
                "collection": "customers",
                "score": 6,
                "fields": ["country"],
                "reason": "Field and value matches",
            }
        ]

        # Test the function
        selected, reason, fields = _resolve_ambiguous_matches(
            "Show me revenue by channel for LinkedIn",
            self.test_collection_info,
            "sales",
            best_match_details,
            alternative_matches,
        )

        # Verify results
        self.assertEqual(selected, "sales")
        self.assertEqual(reason, "This collection contains revenue and channel data")
        self.assertEqual(fields, ["revenue", "channel"])

        # Test with LLM error
        mock_llm.invoke.side_effect = Exception("Test error")
        selected, reason, fields = _resolve_ambiguous_matches(
            "Show me revenue by channel for LinkedIn",
            self.test_collection_info,
            "sales",
            best_match_details,
            alternative_matches,
        )

        # Should fall back to best match
        self.assertEqual(selected, "sales")
        self.assertEqual(reason, "Field and value matches")
        self.assertEqual(fields, ["revenue", "channel"])

    @patch("mypackage.b_data_processor.collection_selector.get_groq_llm")
    def test_select_collection_with_llm(self, mock_get_groq_llm):
        """Test selecting collection with LLM."""
        # Set up mock LLM
        mock_llm = MagicMock()
        mock_get_groq_llm.return_value = mock_llm
        mock_llm.invoke.return_value = MagicMock(
            content="collection: sales\nreason: This collection contains revenue data\nmatching_fields: revenue, channel"
        )

        # Set up test data
        value_matches = {
            "sales": {
                "score": 3,
                "fields": ["channel"],
                "values": {"channel": ["LinkedIn"]},
                "reason": "Values match query terms: 'channel' contains: LinkedIn",
            }
        }

        # Test the function
        result = _select_collection_with_llm(
            self.test_collection_info,
            "Show me revenue by channel for LinkedIn",
            value_matches,
        )

        # Verify results
        self.assertEqual(result.collection_name, "sales")
        self.assertEqual(result.reason, "This collection contains revenue data")
        self.assertEqual(result.matching_fields, ["revenue", "channel"])

        # Test with "NONE" response
        mock_llm.invoke.return_value = MagicMock(
            content="collection: NONE\nreason: No appropriate collection found"
        )

        result = _select_collection_with_llm(
            self.test_collection_info,
            "Show me weather data",
            {},
        )

        # Verify results
        self.assertIsNone(result.collection_name)
        self.assertIsNotNone(result.error)

        # Test with LLM error
        mock_llm.invoke.side_effect = Exception("Test error")

        result = _select_collection_with_llm(
            self.test_collection_info,
            "Show me revenue data",
            {},
        )

        # Verify results
        self.assertIsNone(result.collection_name)
        self.assertIsNotNone(result.error)
        self.assertIn("Error during collection selection", result.error)

    @patch("mypackage.b_data_processor.collection_selector.Database")
    @patch("mypackage.b_data_processor.collection_selector._extract_collection_info")
    @patch("mypackage.b_data_processor.collection_selector._match_headers_to_query")
    @patch("mypackage.b_data_processor.collection_selector._match_values_to_query")
    @patch("mypackage.b_data_processor.collection_selector._compare_matches")
    def test_select_collection_for_query(
        self,
        mock_compare_matches,
        mock_match_values,
        mock_match_headers,
        mock_extract_info,
        mock_database,
    ):
        """Test the main select_collection_for_query function."""
        # Set up mocks
        mock_database.initialize.return_value = True
        mock_extract_info.return_value = self.test_collection_info
        mock_match_headers.return_value = (
            {"sales": {"score": 5, "fields": ["revenue"], "reason": "Field match"}},
            "sales",
            ["revenue"],
        )
        mock_match_values.return_value = (
            {
                "sales": {
                    "score": 3,
                    "fields": ["channel"],
                    "values": {"channel": ["LinkedIn"]},
                    "reason": "Value match",
                }
            },
            "sales",
            {"channel": ["LinkedIn"]},
        )
        mock_compare_matches.return_value = (
            "sales",
            {
                "score": 8,
                "fields": ["revenue", "channel"],
                "values": {"channel": ["LinkedIn"]},
                "reason": "Combined match",
                "header_score": 5,
                "value_score": 3,
            },
            [],  # No alternatives
        )

        # Test the function
        result = select_collection_for_query("Show me revenue by channel for LinkedIn")

        # Verify results
        self.assertEqual(result, "sales")

        # Test with alternatives (requires patching _resolve_ambiguous_matches)
        with patch(
            "mypackage.b_data_processor.collection_selector._resolve_ambiguous_matches"
        ) as mock_resolve:
            mock_compare_matches.return_value = (
                "sales",
                {
                    "score": 8,
                    "fields": ["revenue", "channel"],
                    "values": {"channel": ["LinkedIn"]},
                    "reason": "Combined match",
                    "header_score": 5,
                    "value_score": 3,
                },
                [
                    {
                        "collection": "customers",
                        "score": 6,
                        "fields": ["country"],
                        "reason": "Field match",
                    }
                ],
            )
            mock_resolve.return_value = ("customers", "Better match", ["country"])

            result = select_collection_for_query(
                "Show me revenue by channel for LinkedIn"
            )
            self.assertEqual(result, "customers")

        # Test with no matches (requires patching _select_collection_with_llm)
        with patch(
            "mypackage.b_data_processor.collection_selector._select_collection_with_llm"
        ) as mock_select_llm:
            mock_compare_matches.return_value = (None, {}, [])
            mock_select_llm.return_value = MagicMock(collection_name="sales")

            result = select_collection_for_query("Show me revenue data")
            self.assertEqual(result, "sales")

        # Test with no matches and LLM fails
        with patch(
            "mypackage.b_data_processor.collection_selector._select_collection_with_llm"
        ) as mock_select_llm:
            mock_compare_matches.return_value = (None, {}, [])
            mock_select_llm.return_value = MagicMock(collection_name=None)

            with self.assertRaises(CollectionNotFoundError):
                select_collection_for_query("Show me weather data")

        # Test with database initialization failure
        mock_database.initialize.return_value = False
        with self.assertRaises(CollectionNotFoundError):
            select_collection_for_query("Any query")

        # Test with no collections
        mock_database.initialize.return_value = True
        mock_extract_info.return_value = {}
        with self.assertRaises(CollectionNotFoundError):
            select_collection_for_query("Any query")

    def test_field_processor(self):
        """Test the FieldProcessor class methods."""
        # Test numerical field processing
        samples, uniques = FieldProcessor.process_numerical({"min": 1000, "max": 5000})
        self.assertEqual(samples, ["1000", "5000"])
        self.assertEqual(uniques, ["1000", "5000"])

        # Test datetime field processing
        samples, uniques = FieldProcessor.process_datetime(
            {"min": "2023-01-01", "max": "2023-12-31"}
        )
        self.assertEqual(samples, ["2023-01-01", "2023-12-31"])
        self.assertEqual(uniques, ["2023-01-01", "2023-12-31"])

        # Test categorical field processing
        samples, uniques = FieldProcessor.process_categorical(
            {"unique_values": ["A", "B", "C", "D", "E", "F", "..."]}
        )
        self.assertEqual(
            samples, ["A", "B", "C", "D", "E"]
        )  # Should limit to 5 samples
        self.assertEqual(
            uniques, ["A", "B", "C", "D", "E", "F"]
        )  # Should exclude "..."

        # Test process_field with valid field type
        samples, uniques = FieldProcessor.process_field(
            "numerical", {"min": 1000, "max": 5000}
        )
        self.assertEqual(samples, ["1000", "5000"])

        # Test process_field with invalid field type
        samples, uniques = FieldProcessor.process_field(
            "unknown_type", {"some_data": "value"}
        )
        self.assertEqual(samples, [])
        self.assertEqual(uniques, [])


if __name__ == "__main__":
    unittest.main()
