#!/usr/bin/env python
"""
Test module for query_classifier.py

This module contains unit tests for the query classification functionality.
"""

import unittest
from unittest.mock import MagicMock, patch

from mypackage.a_query_processor.query_classifier import (
    QueryType,
    QueryTypeEnum,
    _classify_query_with_llm,
    _extract_query_type_from_response,
    classify_query,
)


class TestQueryClassifier(unittest.TestCase):
    """Test cases for the query classifier module."""

    def test_extract_query_type_from_response_string(self):
        """Test extracting query type from a string response."""
        # Test each query type
        self.assertEqual(
            _extract_query_type_from_response("description"),
            {"query_type": QueryTypeEnum.DESCRIPTION},
        )
        self.assertEqual(
            _extract_query_type_from_response("report"),
            {"query_type": QueryTypeEnum.REPORT},
        )
        self.assertEqual(
            _extract_query_type_from_response("chart"),
            {"query_type": QueryTypeEnum.CHART},
        )

        # Test with extra text
        self.assertEqual(
            _extract_query_type_from_response("This is a description query"),
            {"query_type": QueryTypeEnum.DESCRIPTION},
        )

        # Test default to ERROR
        self.assertEqual(
            _extract_query_type_from_response("invalid response"),
            {"query_type": QueryTypeEnum.ERROR},
        )

    def test_extract_query_type_from_response_object(self):
        """Test extracting query type from an object with content attribute."""
        # Create mock response objects
        description_response = MagicMock()
        description_response.content = "description"

        report_response = MagicMock()
        report_response.content = "report"

        # Test with mock objects
        self.assertEqual(
            _extract_query_type_from_response(description_response),
            {"query_type": QueryTypeEnum.DESCRIPTION},
        )
        self.assertEqual(
            _extract_query_type_from_response(report_response),
            {"query_type": QueryTypeEnum.REPORT},
        )

    @patch("mypackage.a_query_processor.query_classifier.get_groq_llm")
    def test_classify_query_with_llm(self, mock_get_groq_llm):
        """Test the LLM classification function with mocked LLM."""
        # Set up mock LLM and chain
        mock_llm = MagicMock()
        mock_chain = MagicMock()
        mock_get_groq_llm.return_value = mock_llm
        mock_llm.__or__.return_value = mock_chain
        mock_chain.invoke.return_value = {"query_type": QueryTypeEnum.DESCRIPTION}

        # Test classification
        result = _classify_query_with_llm("How much did we spend on Facebook ads?")
        self.assertEqual(result.query_type, QueryTypeEnum.DESCRIPTION)

        # Verify the mock was called correctly
        mock_get_groq_llm.assert_called_once()
        mock_chain.invoke.assert_called_once()

    @patch("mypackage.a_query_processor.query_classifier._classify_query_with_llm")
    def test_classify_query(self, mock_classify_with_llm):
        """Test the public classify_query function."""
        # Set up mock return values for different query types
        mock_classify_with_llm.return_value = QueryType(
            query_type=QueryTypeEnum.DESCRIPTION
        )
        self.assertEqual(
            classify_query("How much revenue did we generate?"), "description"
        )

        mock_classify_with_llm.return_value = QueryType(query_type=QueryTypeEnum.REPORT)
        self.assertEqual(classify_query("Generate a full report"), "report")

        mock_classify_with_llm.return_value = QueryType(query_type=QueryTypeEnum.CHART)
        self.assertEqual(
            classify_query("Show me a chart of revenue by country"), "chart"
        )

        mock_classify_with_llm.return_value = QueryType(query_type=QueryTypeEnum.ERROR)
        self.assertEqual(classify_query("Invalid query"), "error")

    @patch("mypackage.a_query_processor.query_classifier._classify_query_with_llm")
    def test_classify_query_exception(self, mock_classify_with_llm):
        """Test error handling in classify_query."""
        # Set up mock to raise an exception
        mock_classify_with_llm.side_effect = Exception("Test error")

        # Verify exception is propagated
        with self.assertRaises(Exception) as context:
            classify_query("Test query")

        self.assertTrue("Test error" in str(context.exception))


if __name__ == "__main__":
    unittest.main()
