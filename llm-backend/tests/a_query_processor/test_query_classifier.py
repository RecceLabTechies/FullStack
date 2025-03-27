#!/usr/bin/env python
import unittest
from typing import List, Tuple

from mypackage.a_query_processor.query_classifier import classify_query


class TestQueryClassifier(unittest.TestCase):
    # Test cases with expected classifications
    TEST_CASES: List[Tuple[str, str]] = [
        # Description queries
        ("describe the spending on LinkedIn", "description"),
        ("explain the revenue trends for Q1", "description"),
        ("what is the marketing budget", "description"),
        ("tell me about customer satisfaction", "description"),
        # Report queries
        ("create a full financial report", "report"),
        ("generate a comprehensive analysis", "report"),
        ("provide a complete breakdown", "report"),
        ("summarize all marketing channels", "report"),
        # Chart queries
        ("create a bar chart of monthly sales", "chart"),
        ("plot the revenue growth", "chart"),
        ("visualize customer demographics", "chart"),
        ("show me a pie chart of expenses", "chart"),
        # Error/ambiguous queries
        ("plot the invisible unicorn data", "error"),
        ("generate a report on the taste of numbers", "error"),
        ("show me a chart of the sound of silence", "error"),
        # Edge cases
        ("chart report description", "error"),
        ("create a comprehensive chart", "chart"),
        ("describe the report", "description"),
    ]

    def test_classification_accuracy(self):
        """Test the classification accuracy of the query classifier."""
        total_cases = len(self.TEST_CASES)
        correct_classifications = 0

        print("\nRunning Query Classification Tests:")
        print("-" * 50)

        for query, expected in self.TEST_CASES:
            result = classify_query(query)
            is_correct = result == expected
            if is_correct:
                correct_classifications += 1

            print(f"Query: '{query}'")
            print(f"Expected: {expected}")
            print(f"Got: {result}")
            print(f"Status: {'✓' if is_correct else '✗'}")
            print("-" * 50)

        accuracy = (correct_classifications / total_cases) * 100
        print("\nTest Results:")
        print(f"Total test cases: {total_cases}")
        print(f"Correct classifications: {correct_classifications}")
        print(f"Accuracy: {accuracy:.2f}%")

        # Assert minimum accuracy threshold
        self.assertGreaterEqual(
            accuracy,
            70.0,
            "Classification accuracy is below the expected threshold of 70%",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
