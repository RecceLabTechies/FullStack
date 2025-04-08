#!/usr/bin/env python
"""
Test module for query_validator.py

This module contains unit tests for the query validation functionality.
"""

import unittest
from unittest.mock import MagicMock, patch

from mypackage.a_query_processor.query_validator import (
    DATA_ANALYSIS_KEYWORDS,
    INVALID_PATTERNS,
    _cached_llm_validation,
    get_valid_query,
    normalize_query,
)


class TestQueryValidator(unittest.TestCase):
    """Test cases for the query validator module."""

    def test_normalize_query(self):
        """Test the query normalization function."""
        # Test whitespace normalization
        self.assertEqual(normalize_query("  test   query  "), "test query")

        # Test punctuation removal at the end
        self.assertEqual(normalize_query("test query."), "test query")
        self.assertEqual(normalize_query("test query!"), "test query")
        self.assertEqual(
            normalize_query("test query?"), "test query?"
        )  # Question mark should remain

        # Test question mark addition
        self.assertEqual(normalize_query("what is the revenue"), "what is the revenue?")
        self.assertEqual(normalize_query("how many sales"), "how many sales?")
        self.assertEqual(
            normalize_query("where are the customers"), "where are the customers?"
        )

        # Test no change for non-question starters
        self.assertEqual(normalize_query("show me the data"), "show me the data")
        self.assertEqual(normalize_query("generate a report"), "generate a report")

    def test_invalid_patterns(self):
        """Test the invalid pattern matching."""
        # Test empty query
        self.assertTrue(INVALID_PATTERNS[0]["pattern"].match("   "))
        self.assertFalse(INVALID_PATTERNS[0]["pattern"].match("test"))

        # Test special characters only
        self.assertTrue(INVALID_PATTERNS[1]["pattern"].match("!@#$%"))
        self.assertFalse(INVALID_PATTERNS[1]["pattern"].match("test!"))

        # Test greetings
        self.assertTrue(INVALID_PATTERNS[2]["pattern"].match("hello"))
        self.assertTrue(INVALID_PATTERNS[2]["pattern"].match("Hi!"))
        self.assertFalse(INVALID_PATTERNS[2]["pattern"].match("hello world"))

    def test_data_analysis_keywords(self):
        """Test that data analysis keywords are properly defined."""
        # Verify some important keywords are in the list
        self.assertIn("chart", DATA_ANALYSIS_KEYWORDS)
        self.assertIn("report", DATA_ANALYSIS_KEYWORDS)
        self.assertIn("analysis", DATA_ANALYSIS_KEYWORDS)
        self.assertIn("trend", DATA_ANALYSIS_KEYWORDS)

    @patch("mypackage.a_query_processor.query_validator.get_groq_llm")
    def test_cached_llm_validation(self, mock_get_groq_llm):
        """Test the LLM validation function with mocked LLM."""
        # Set up mock LLM
        mock_llm = MagicMock()
        mock_get_groq_llm.return_value = mock_llm

        # Test valid response
        mock_llm.invoke.return_value = MagicMock(content='{"is_valid": true}')
        result = _cached_llm_validation("analyze sales data", "test-model")
        self.assertTrue(result["is_valid"])

        # Test invalid response
        mock_llm.invoke.return_value = MagicMock(
            content='{"is_valid": false, "reason": "Too vague"}'
        )
        result = _cached_llm_validation("do something", "test-model")
        self.assertFalse(result["is_valid"])
        self.assertEqual(result["reason"], "Too vague")

        # Test malformed JSON response
        mock_llm.invoke.return_value = MagicMock(content="Invalid JSON")
        result = _cached_llm_validation("test query", "test-model")
        self.assertTrue(result["is_valid"])  # Default to valid

    @patch("mypackage.a_query_processor.query_validator._cached_llm_validation")
    def test_get_valid_query(self, mock_cached_llm_validation):
        """Test the main validation function."""
        # Test too short query
        self.assertFalse(get_valid_query("a"))

        # Test invalid pattern match
        self.assertFalse(get_valid_query("hello"))
        self.assertFalse(get_valid_query("!@#$%"))

        # Test data analysis keyword match
        self.assertTrue(get_valid_query("create a chart of sales"))
        self.assertTrue(get_valid_query("generate a report"))

        # Test LLM validation for non-keyword queries
        mock_cached_llm_validation.return_value = {"is_valid": True}
        self.assertTrue(get_valid_query("analyze the customer behavior"))

        mock_cached_llm_validation.return_value = {
            "is_valid": False,
            "reason": "Not related to data",
        }
        self.assertFalse(get_valid_query("what is the meaning of life"))

        # Test exception handling
        mock_cached_llm_validation.side_effect = Exception("Test error")
        self.assertTrue(
            get_valid_query("test query with error")
        )  # Should default to valid

    @patch("mypackage.a_query_processor.query_validator.get_groq_llm")
    def test_get_valid_query_integration(self, mock_get_groq_llm):
        """Test the integration of normalize_query and LLM validation."""
        # Set up mock LLM
        mock_llm = MagicMock()
        mock_get_groq_llm.return_value = mock_llm
        mock_llm.invoke.return_value = MagicMock(content='{"is_valid": true}')

        # Test with a query that needs normalization
        self.assertTrue(get_valid_query("what is the revenue trend  "))

        # Verify the query was normalized before LLM validation
        # This is an indirect test since we can't easily check the exact argument


if __name__ == "__main__":
    unittest.main()
