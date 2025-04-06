#!/usr/bin/env python
"""
Test module for description_generator.py

This module contains unit tests for the description generation functionality.
"""

import unittest
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
from mypackage.c_regular_generator.description_generator import (
    AnalysisRequest,
    ColumnMetadata,
    _analyze_time_series,
    _calculate_correlation,
    _calculate_crosstabs,
    _calculate_insights,
    _calculate_trend,
    _detect_outliers,
    _parse_llm_response,
    enhance_query_with_metadata,
    extract_column_metadata,
    generate_description,
    get_llm_analysis_plan,
)


class TestDescriptionGenerator(unittest.TestCase):
    """Test cases for the description generator module."""

    def setUp(self):
        """Set up test data."""
        # Create a sample DataFrame for testing
        self.test_df = pd.DataFrame(
            {
                "date": pd.date_range(start="2023-01-01", periods=5),
                "sales": [1000, 1200, 900, 1500, 1100],
                "category": ["A", "B", "A", "C", "B"],
                "is_promoted": [True, False, True, True, False],
                "description": [
                    "Product X",
                    "Product Y",
                    "Product Z",
                    "Product X",
                    "Product W",
                ],
            }
        )

        # Sample metadata
        self.test_metadata = [
            ColumnMetadata(
                name="date",
                dtype="datetime64[ns]",
                sample_values=[
                    "2023-01-01",
                    "2023-01-02",
                    "2023-01-03",
                    "2023-01-04",
                    "2023-01-05",
                ],
                stats={"start": "2023-01-01", "end": "2023-01-05", "unique_days": 5},
            ),
            ColumnMetadata(
                name="sales",
                dtype="int64",
                sample_values=[1000, 1200, 900, 1500, 1100],
                stats={
                    "min": 900.0,
                    "max": 1500.0,
                    "mean": 1140.0,
                    "std": 233.45,
                    "outliers": {
                        "has_outliers": False,
                        "outlier_count": 0,
                        "lower_bound": 475.0,
                        "upper_bound": 1625.0,
                    },
                },
            ),
            ColumnMetadata(
                name="category",
                dtype="object",
                unique_values=["A", "B", "C"],
                sample_values=["A", "B", "A", "C", "B"],
                stats={"top_values": {"A": 0.4, "B": 0.4, "C": 0.2}, "unique_count": 3},
            ),
            ColumnMetadata(
                name="is_promoted",
                dtype="bool",
                unique_values=[True, False],
                sample_values=[True, False, True, True, False],
                stats={"top_values": {True: 0.6, False: 0.4}, "unique_count": 2},
            ),
            ColumnMetadata(
                name="description",
                dtype="object",
                unique_values=["Product X", "Product Y", "Product Z", "Product W"],
                sample_values=[
                    "Product X",
                    "Product Y",
                    "Product Z",
                    "Product X",
                    "Product W",
                ],
                stats={
                    "top_values": {
                        "Product X": 0.4,
                        "Product Y": 0.2,
                        "Product Z": 0.2,
                        "Product W": 0.2,
                    },
                    "unique_count": 4,
                },
            ),
        ]

        # Sample analysis request
        self.test_analysis_request = AnalysisRequest(
            selected_columns=["date", "sales"],
            analysis_type="trend",
            parameters={"time_column": "date", "measure": "sales"},
        )

    def test_detect_outliers(self):
        """Test outlier detection."""
        # Test with numeric series
        series = pd.Series([1, 2, 3, 4, 5, 100])
        result = _detect_outliers(series)

        self.assertTrue(result["has_outliers"])
        self.assertEqual(result["outlier_count"], 1)
        self.assertLess(result["lower_bound"], 1)
        self.assertGreater(result["upper_bound"], 5)
        self.assertLess(result["upper_bound"], 100)

        # Test with series too short
        short_series = pd.Series([1, 2, 3])
        result = _detect_outliers(short_series)

        self.assertFalse(result["has_outliers"])
        self.assertEqual(result["outlier_count"], 0)

        # Test with non-numeric series
        non_numeric = pd.Series(["a", "b", "c", "d", "e"])
        result = _detect_outliers(non_numeric)

        self.assertFalse(result["has_outliers"])
        self.assertEqual(result["outlier_count"], 0)

    def test_extract_column_metadata(self):
        """Test metadata extraction from DataFrame."""
        metadata = extract_column_metadata(self.test_df)

        # Check basic structure
        self.assertEqual(len(metadata), 5)  # Should have 5 columns

        # Check column names
        column_names = [col.name for col in metadata]
        self.assertEqual(set(column_names), set(self.test_df.columns))

        # Check data types
        date_col = next(col for col in metadata if col.name == "date")
        self.assertEqual(date_col.dtype, "datetime64[ns]")

        sales_col = next(col for col in metadata if col.name == "sales")
        self.assertEqual(sales_col.dtype, "int64")

        # Check stats
        self.assertIn("start", date_col.stats)
        self.assertIn("end", date_col.stats)

        self.assertIn("min", sales_col.stats)
        self.assertIn("max", sales_col.stats)
        self.assertIn("mean", sales_col.stats)
        self.assertIn("outliers", sales_col.stats)

        # Test with empty DataFrame
        empty_metadata = extract_column_metadata(pd.DataFrame())
        self.assertEqual(empty_metadata, [])

    def test_enhance_query_with_metadata(self):
        """Test query enhancement with metadata."""
        query = "Show me sales trends"
        enhanced = enhance_query_with_metadata(query, self.test_metadata)

        # Check that the enhanced query contains the original query
        self.assertIn(query, enhanced)

        # Check that it contains data features
        self.assertIn("Data Features:", enhanced)

        # Check that it includes statistical highlights
        self.assertIn("sales: range", enhanced)
        self.assertIn("category: common values", enhanced)

        # Test with empty metadata
        empty_enhanced = enhance_query_with_metadata(query, [])
        self.assertEqual(empty_enhanced, query + "\n\nData Features:\n- ")

    @patch("mypackage.c_regular_generator.description_generator.get_groq_llm")
    def test_get_llm_analysis_plan(self, mock_get_groq_llm):
        """Test LLM analysis plan generation."""
        # Set up mock LLM
        mock_llm = MagicMock()
        mock_get_groq_llm.return_value = mock_llm
        mock_chain = MagicMock()
        mock_llm.__or__.return_value = mock_chain

        # Test with valid LLM response
        mock_chain.invoke.return_value = MagicMock(
            content="selected_columns: date, sales\nanalysis_type: trend\nparameters: time_column:date, measure:sales"
        )

        analysis_request = get_llm_analysis_plan(
            "Show me sales trends", self.test_metadata
        )

        # Verify the result
        self.assertEqual(analysis_request.selected_columns, ["date", "sales"])
        self.assertEqual(analysis_request.analysis_type, "trend")
        self.assertEqual(
            analysis_request.parameters, {"time_column": "date", "measure": "sales"}
        )

        # Test with invalid response format
        mock_chain.invoke.return_value = MagicMock(
            content="I recommend analyzing sales trends over time."
        )

        with self.assertRaises(Exception):
            get_llm_analysis_plan("Show me sales trends", self.test_metadata)

    def test_parse_llm_response(self):
        """Test parsing LLM response."""
        # Test valid response
        response = "selected_columns: date, sales\nanalysis_type: trend\nparameters: time_column:date, measure:sales"
        result = _parse_llm_response(response)

        self.assertEqual(result.selected_columns, ["date", "sales"])
        self.assertEqual(result.analysis_type, "trend")
        self.assertEqual(result.parameters, {"time_column": "date", "measure": "sales"})

        # Test response with extra whitespace
        response = "selected_columns: date, sales \nanalysis_type: trend\nparameters: time_column:date, measure:sales"
        result = _parse_llm_response(response)

        self.assertEqual(result.selected_columns, ["date", "sales"])

        # Test invalid response (should raise exception)
        with self.assertRaises(Exception):
            _parse_llm_response("This is not a valid response")

    def test_calculate_insights(self):
        """Test insights calculation."""
        insights = _calculate_insights(self.test_df, self.test_analysis_request)

        # Check basic structure
        self.assertIn("summary_stats", insights)
        self.assertIn("relationships", insights)

        # Check column stats
        self.assertIn("date", insights["summary_stats"])
        self.assertIn("sales", insights["summary_stats"])

        # Check relationships
        self.assertIn("correlation", insights["relationships"])

        # Check time analysis
        self.assertIn("time_analysis", insights)

        # Test with invalid columns
        invalid_request = AnalysisRequest(
            selected_columns=["invalid_column"], analysis_type="trend", parameters={}
        )

        insights = _calculate_insights(self.test_df, invalid_request)
        self.assertEqual(insights["summary_stats"], {})

    def test_calculate_trend(self):
        """Test trend calculation."""
        # Test with datetime series
        date_series = pd.Series(pd.date_range(start="2023-01-01", periods=5))
        trend = _calculate_trend(date_series)

        self.assertIn("slope_per_observation", trend)
        self.assertIn("percent_change", trend)

        # Test with numeric series
        numeric_series = pd.Series([1, 2, 3, 4, 5])
        trend = _calculate_trend(numeric_series)

        self.assertIn("slope_per_observation", trend)
        self.assertIn("percent_change", trend)
        self.assertEqual(trend["slope_per_observation"], 1.0)

        # Test with series too short
        short_series = pd.Series([1])
        trend = _calculate_trend(short_series)
        self.assertEqual(trend, {})

    def test_calculate_correlation(self):
        """Test correlation calculation."""
        # Test with numeric columns
        correlations = _calculate_correlation(self.test_df, ["sales", "is_promoted"])

        self.assertIn("top_correlations", correlations)

        # Test with non-numeric columns
        correlations = _calculate_correlation(self.test_df, ["category", "description"])
        self.assertEqual(correlations, {})

        # Test with single column
        correlations = _calculate_correlation(self.test_df, ["sales"])
        self.assertEqual(correlations, {})

    def test_calculate_crosstabs(self):
        """Test crosstab calculation."""
        # Test with valid columns
        crosstabs = _calculate_crosstabs(self.test_df, ["category", "is_promoted"])
        self.assertEqual(
            crosstabs, {}
        )  # Currently returns empty dict in implementation

        # Test with invalid columns
        crosstabs = _calculate_crosstabs(self.test_df, ["invalid_column"])
        self.assertEqual(crosstabs, {})

    def test_analyze_time_series(self):
        """Test time series analysis."""
        # Create a DataFrame with more time points for better testing
        df = pd.DataFrame(
            {
                "date": pd.date_range(start="2023-01-01", periods=30),
                "sales": np.random.normal(1000, 200, 30),
            }
        )

        # Test with valid parameters
        analysis = _analyze_time_series(
            df,
            "date",
            AnalysisRequest(
                selected_columns=["date", "sales"],
                analysis_type="trend",
                parameters={"time_column": "date", "measure": "sales"},
            ),
        )

        self.assertIn("rolling_stats", analysis)
        self.assertIn("7_day_mean", analysis["rolling_stats"])
        self.assertIn("30_day_max", analysis["rolling_stats"])

        # Test with invalid measure column
        analysis = _analyze_time_series(
            df,
            "date",
            AnalysisRequest(
                selected_columns=["date"],
                analysis_type="trend",
                parameters={"time_column": "date", "measure": "invalid_column"},
            ),
        )

        self.assertEqual(analysis, {})

    @patch(
        "mypackage.c_regular_generator.description_generator.extract_column_metadata"
    )
    @patch("mypackage.c_regular_generator.description_generator.get_llm_analysis_plan")
    @patch("mypackage.c_regular_generator.description_generator._calculate_insights")
    @patch("mypackage.c_regular_generator.description_generator.get_groq_llm")
    def test_generate_description(
        self,
        mock_get_groq_llm,
        mock_calculate_insights,
        mock_get_llm_analysis_plan,
        mock_extract_metadata,
    ):
        """Test the main generate_description function."""
        # Set up mocks
        mock_extract_metadata.return_value = self.test_metadata
        mock_get_llm_analysis_plan.return_value = self.test_analysis_request
        mock_calculate_insights.return_value = {
            "summary_stats": {"sales": {"mean": 1140.0, "unique_count": 5}},
            "relationships": {
                "correlation": {"top_correlations": ["sales & date (0.75)"]}
            },
            "time_analysis": {"rolling_stats": {"7_day_mean": {}}},
        }

        # Set up mock LLM
        mock_llm = MagicMock()
        mock_get_groq_llm.return_value = mock_llm
        mock_llm.invoke.return_value = MagicMock(
            content="""**Marketing Performance Analysis**

**Client Query**: Show me sales trends

**Analysis Context**:
- Focus Metrics: date, sales
- Analysis Method: Time series trend analysis
- Time Frame: Jan 1-5, 2023

**Key Marketing Insights**:
1. Performance Highlights:
   - ▸ Average sales of $1,140 across the period
   - ▸ Peak performance on Jan 4 with $1,500 in sales
   
2. Audience Trends:
   - Strong positive correlation between date and sales (0.75)
   
3. Notable Patterns:
   - Sales showing upward trajectory with 15% growth
   - No significant outliers detected

**Recommendations**:
- Increase marketing spend on high-performing days
- Investigate factors behind Jan 4 performance spike
- Test promotional strategies to boost lower-performing days

**Visualization Suggestions**:
- Line chart showing daily sales with trend line
- Bar chart comparing daily performance with previous period"""
        )

        # Test the function
        result = generate_description(self.test_df, "Show me sales trends")

        # Verify the result
        self.assertIn("Marketing Performance Analysis", result)
        self.assertIn("Focus Metrics: date, sales", result)
        self.assertIn("Average sales of $1,140", result)

        # Verify all the mocks were called correctly
        mock_extract_metadata.assert_called_once_with(self.test_df)
        mock_get_llm_analysis_plan.assert_called_once()
        mock_calculate_insights.assert_called_once()
        mock_llm.invoke.assert_called_once()

        # Test with invalid columns in analysis plan
        mock_get_llm_analysis_plan.return_value = AnalysisRequest(
            selected_columns=["invalid_column"], analysis_type="trend", parameters={}
        )

        result = generate_description(self.test_df, "Show me invalid data")

        # Should still work by falling back to first two columns
        self.assertIn("Marketing Performance Analysis", result)

        # Test with cleaning of special tags
        mock_llm.invoke.return_value = MagicMock(
            content="""<think>This is a thinking section that should be removed</think>
**Marketing Analysis**
<gpt>This should be removed too</gpt>"""
        )

        result = generate_description(self.test_df, "Show me sales trends")

        # Verify tags were removed
        self.assertNotIn("<think>", result)
        self.assertNotIn("</think>", result)
        self.assertNotIn("<gpt>", result)
        self.assertNotIn("</gpt>", result)
        self.assertIn("**Marketing Analysis**", result)


if __name__ == "__main__":
    unittest.main()
