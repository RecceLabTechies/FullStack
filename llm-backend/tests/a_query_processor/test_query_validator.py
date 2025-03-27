#!/usr/bin/env python
import unittest
from typing import List, Tuple

from mypackage.a_query_processor.query_validator import (
    QueryValidationError,
    get_valid_query,
)


class TestQueryValidator(unittest.TestCase):
    # Test cases with expected validation results
    TEST_CASES: List[Tuple[str, bool]] = [
        # Valid queries
        ("create a bar chart of monthly sales", True),
        ("analyze customer satisfaction trends", True),
        ("generate a financial report", True),
        ("show me the revenue data", True),
        ("compare marketing performance", True),
        # Invalid queries (too short)
        ("a", False),
        ("", False),
        (" ", False),
        # Invalid queries (gibberish)
        ("asdfjkl123", False),
        ("random characters !@#$%", False),
        # Invalid queries (unrelated to data analysis)
        ("what's the weather like?", False),
        ("tell me a joke", False),
        ("how to make pasta", False),
        # Invalid queries (too vague)
        ("show me something", False),
        ("give me data", False),
        ("analyze this", False),
        # Edge cases
        (
            "generate a report",
            True,
        ),  # Valid despite being vague (special case for reports)
        ("chart", False),  # Too vague
        ("describe", False),  # Too vague
    ]

    def test_validation_accuracy(self):
        """Test the validation accuracy of the query validator."""
        total_cases = len(self.TEST_CASES)
        correct_validations = 0

        print("\nRunning Query Validation Tests:")
        print("-" * 50)

        for query, expected in self.TEST_CASES:
            try:
                result = get_valid_query(query)
                is_correct = result == expected
                if is_correct:
                    correct_validations += 1

                print(f"Query: '{query}'")
                print(f"Expected: {'Valid' if expected else 'Invalid'}")
                print(f"Got: {'Valid' if result else 'Invalid'}")
                print(f"Status: {'✓' if is_correct else '✗'}")
                print("-" * 50)
            except QueryValidationError as e:
                is_correct = not expected
                if is_correct:
                    correct_validations += 1

                print(f"Query: '{query}'")
                print(f"Expected: {'Valid' if expected else 'Invalid'}")
                print(f"Got: Invalid (Error: {str(e)})")
                print(f"Status: {'✓' if is_correct else '✗'}")
                print("-" * 50)

        accuracy = (correct_validations / total_cases) * 100
        print("\nTest Results:")
        print(f"Total test cases: {total_cases}")
        print(f"Correct validations: {correct_validations}")
        print(f"Accuracy: {accuracy:.2f}%")

        # Assert minimum accuracy threshold
        self.assertGreaterEqual(
            accuracy,
            80.0,
            "Validation accuracy is below the expected threshold of 80%",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
