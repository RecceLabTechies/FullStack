#!/usr/bin/env python
"""
Test module for collection_processor.py

This module contains unit tests for the collection processing functionality.
"""

import unittest
from unittest.mock import MagicMock, patch

import pandas as pd
from mypackage.b_data_processor.collection_processor import (
    _correct_code,
    _execute_code_safe,
    _execute_with_retries,
    _extract_code_block,
    _generate_processing_code,
    _get_column_metadata,
    process_collection_query,
)


class TestCollectionProcessor(unittest.TestCase):
    """Test cases for the collection processor module."""

    def setUp(self):
        """Set up test data."""
        # Create a sample DataFrame for testing
        self.test_df = pd.DataFrame(
            {
                "status": ["active", "inactive", "pending", "active", "inactive"],
                "revenue": [1500, 800, 1200, 1600, 750],
                "date": pd.date_range("2024-01-01", periods=5, freq="D"),
                "product": ["WidgetA", "GadgetB", "ToolC", "WidgetA", "ToolC"],
                "customer_id": [1001, 1002, 1003, 1004, 1005],
            }
        )

        # Sample metadata
        self.test_metadata = {
            "columns": ["status", "revenue", "date", "product", "customer_id"],
            "dtypes": {
                "status": "object",
                "revenue": "int64",
                "date": "datetime64[ns]",
                "product": "object",
                "customer_id": "int64",
            },
            "unique_values": {
                "status": ["active", "inactive", "pending"],
                "product": ["WidgetA", "GadgetB", "ToolC"],
            },
            "numeric_stats": {
                "revenue": {
                    "min": 750,
                    "max": 1600,
                    "mean": 1170,
                    "median": 1200,
                    "std": 378.15,
                    "null_count": 0,
                },
                "customer_id": {
                    "min": 1001,
                    "max": 1005,
                    "mean": 1003,
                    "median": 1003,
                    "std": 1.58,
                    "null_count": 0,
                },
            },
        }

        # Sample code
        self.test_code = """
import pandas as pd
import numpy as np

def process_data(df: pd.DataFrame) -> pd.DataFrame:
    processed_df = df.copy()
    processed_df = processed_df[processed_df['status'] == 'active']
    processed_df = processed_df[processed_df['revenue'] > 1000]
    processed_df = processed_df.sort_values('date')
    result_df = processed_df
    return result_df
"""

    def test_get_column_metadata(self):
        """Test the column metadata extraction function."""
        metadata = _get_column_metadata(self.test_df)

        # Check basic structure
        self.assertIn("columns", metadata)
        self.assertIn("dtypes", metadata)
        self.assertIn("unique_values", metadata)
        self.assertIn("numeric_stats", metadata)

        # Check columns
        self.assertEqual(set(metadata["columns"]), set(self.test_df.columns))

        # Check unique values for string columns
        self.assertIn("status", metadata["unique_values"])
        self.assertIn("product", metadata["unique_values"])
        self.assertEqual(
            set(metadata["unique_values"]["status"]),
            set(["active", "inactive", "pending"]),
        )

        # Check numeric stats
        self.assertIn("revenue", metadata["numeric_stats"])
        self.assertIn("customer_id", metadata["numeric_stats"])
        self.assertIn("min", metadata["numeric_stats"]["revenue"])
        self.assertIn("max", metadata["numeric_stats"]["revenue"])
        self.assertIn("mean", metadata["numeric_stats"]["revenue"])

        # Test with empty DataFrame
        empty_metadata = _get_column_metadata(pd.DataFrame())
        self.assertEqual(empty_metadata, {})

    def test_extract_code_block(self):
        """Test code block extraction from markdown."""
        # Test with Python code block
        markdown = "Here's some code:\n```python\nprint('hello')\n```\nEnd"
        code = _extract_code_block(markdown)
        self.assertEqual(code, "print('hello')")

        # Test with unmarked code block
        markdown = "Code:\n```\nx = 1 + 2\n```\nDone"
        code = _extract_code_block(markdown)
        self.assertEqual(code, "x = 1 + 2")

        # Test with invalid input
        with self.assertRaises(ValueError):
            _extract_code_block(None)

        with self.assertRaises(ValueError):
            _extract_code_block("No code block here")

    @patch("mypackage.b_data_processor.collection_processor.get_groq_llm")
    def test_generate_processing_code(self, mock_get_groq_llm):
        """Test code generation using LLM."""
        # Set up mock LLM
        mock_llm = MagicMock()
        mock_get_groq_llm.return_value = mock_llm
        mock_llm.invoke.return_value = (
            "Here's the code:\n```python\ndef process_data(df):\n    return df\n```"
        )

        # Test code generation
        query = "Filter active users"
        code = _generate_processing_code(query, self.test_metadata)

        # Verify the result
        self.assertEqual(code, "def process_data(df):\n    return df")

        # Verify LLM was called with appropriate prompt
        mock_get_groq_llm.assert_called_once()
        mock_llm.invoke.assert_called_once()
        # Check that the prompt contains the query and metadata
        self.assertIn(query, mock_llm.invoke.call_args[0][0])

    def test_execute_code_safe(self):
        """Test safe code execution."""
        # Test successful execution
        code = """
def process_data(df: pd.DataFrame) -> pd.DataFrame:
    result_df = df[df['status'] == 'active']
    return result_df
"""
        result_df, error = _execute_code_safe(code, self.test_df)
        self.assertIsNone(error)
        self.assertEqual(len(result_df), 2)  # Should have 2 active records

        # Test execution with error
        bad_code = """
def process_data(df: pd.DataFrame) -> pd.DataFrame:
    result_df = df[df['nonexistent_column'] == 'value']
    return result_df
"""
        result_df, error = _execute_code_safe(bad_code, self.test_df)
        self.assertIsNotNone(error)
        self.assertTrue("error" in error.lower())

    @patch("mypackage.b_data_processor.collection_processor.get_groq_llm")
    def test_correct_code(self, mock_get_groq_llm):
        """Test code correction using LLM."""
        # Set up mock LLM
        mock_llm = MagicMock()
        mock_get_groq_llm.return_value = mock_llm
        mock_llm.invoke.return_value = "```python\ndef process_data(df):\n    result_df = df[df['status'] == 'active']\n    return result_df\n```"

        # Test code correction
        error = "KeyError: 'statu'"
        faulty_code = "def process_data(df):\n    result_df = df[df['statu'] == 'active']\n    return result_df"
        query = "Filter active users"

        corrected_code = _correct_code(error, faulty_code, query, self.test_metadata)

        # Verify the result
        self.assertIn("status", corrected_code)  # Should have fixed the column name

        # Verify LLM was called with appropriate prompt
        mock_get_groq_llm.assert_called_once()
        mock_llm.invoke.assert_called_once()
        # Check that the prompt contains the error and faulty code
        self.assertIn(error, mock_llm.invoke.call_args[0][0])
        self.assertIn(faulty_code, mock_llm.invoke.call_args[0][0])

    @patch("mypackage.b_data_processor.collection_processor._execute_code_safe")
    @patch("mypackage.b_data_processor.collection_processor._correct_code")
    def test_execute_with_retries(self, mock_correct_code, mock_execute_code_safe):
        """Test execution with retries."""
        # Test successful execution on first attempt
        mock_execute_code_safe.return_value = (
            pd.DataFrame({"result": [1, 2, 3]}),
            None,
        )

        result = _execute_with_retries(
            self.test_code, self.test_df, "test query", self.test_metadata
        )

        self.assertEqual(len(result), 3)
        mock_execute_code_safe.assert_called_once()
        mock_correct_code.assert_not_called()

        # Reset mocks
        mock_execute_code_safe.reset_mock()
        mock_correct_code.reset_mock()

        # Test with one retry
        mock_execute_code_safe.side_effect = [
            (self.test_df, "Error on first attempt"),  # First attempt fails
            (pd.DataFrame({"result": [1, 2]}), None),  # Second attempt succeeds
        ]
        mock_correct_code.return_value = "corrected code"

        result = _execute_with_retries(
            self.test_code, self.test_df, "test query", self.test_metadata
        )

        self.assertEqual(len(result), 2)
        self.assertEqual(mock_execute_code_safe.call_count, 2)
        mock_correct_code.assert_called_once()

        # Reset mocks
        mock_execute_code_safe.reset_mock()
        mock_correct_code.reset_mock()

        # Test with max retries exceeded
        mock_execute_code_safe.return_value = (self.test_df, "Persistent error")
        mock_correct_code.return_value = "still faulty code"

        result = _execute_with_retries(
            self.test_code,
            self.test_df,
            "test query",
            self.test_metadata,
            max_retries=2,
        )

        # Should return original DataFrame after max retries
        self.assertEqual(len(result), len(self.test_df))
        self.assertEqual(mock_execute_code_safe.call_count, 3)  # Initial + 2 retries
        self.assertEqual(mock_correct_code.call_count, 2)  # 2 correction attempts

    @patch("mypackage.b_data_processor.collection_processor.Database")
    @patch("mypackage.b_data_processor.collection_processor._get_column_metadata")
    @patch("mypackage.b_data_processor.collection_processor._generate_processing_code")
    @patch("mypackage.b_data_processor.collection_processor._execute_with_retries")
    def test_process_collection_query(
        self,
        mock_execute_with_retries,
        mock_generate_processing_code,
        mock_get_column_metadata,
        mock_database,
    ):
        """Test the main process_collection_query function."""
        # Set up mocks
        mock_collection = MagicMock()
        mock_collection.find.return_value = [
            {"status": "active", "revenue": 1500},
            {"status": "inactive", "revenue": 800},
        ]
        mock_database.get_collection.return_value = mock_collection

        mock_get_column_metadata.return_value = self.test_metadata
        mock_generate_processing_code.return_value = self.test_code
        mock_execute_with_retries.return_value = pd.DataFrame({"result": [1, 2]})

        # Test the function
        result = process_collection_query("test_collection", "test query")

        # Verify the result
        self.assertEqual(len(result), 2)

        # Verify all the mocks were called correctly
        mock_database.get_collection.assert_called_once_with("test_collection")
        mock_collection.find.assert_called_once_with({}, {"_id": 0})
        mock_get_column_metadata.assert_called_once()
        mock_generate_processing_code.assert_called_once_with(
            "test query", self.test_metadata
        )
        mock_execute_with_retries.assert_called_once()

        # Test with invalid collection
        mock_database.get_collection.return_value = None
        with self.assertRaises(ValueError):
            process_collection_query("invalid_collection", "test query")

        # Test with exception
        mock_database.get_collection.side_effect = Exception("Test error")
        result = process_collection_query("error_collection", "test query")
        self.assertTrue(result.empty)


if __name__ == "__main__":
    unittest.main()
