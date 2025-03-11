#!/usr/bin/env python
from pydantic import BaseModel
from langchain.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM
import pandas as pd
from typing import Tuple

print("🚀 Initializing Query Classifier...")


class QueryType(BaseModel):
    original_query: str
    query_type: str
    dataframe: pd.DataFrame

    class Config:
        arbitrary_types_allowed = True


class QueryClassifier:
    def __init__(self, model_name: str = "llama3.2"):
        print(f"🤖 Initializing classifier with model: {model_name}")
        self.template = """Classify the following query into one of these categories:
        - description: Queries asking for specific details, explanations, or summaries about particular aspects of the data. These often focus on a specific topic, metric, or segment. Examples: "describe the spending on LinkedIn", "generate description of marketing expenses", "explain the revenue trends for Q1", "summarize the customer acquisition costs"
        
        - report: Queries requesting comprehensive analysis across multiple aspects of the dataset, often requiring a full overview or detailed breakdown of the entire dataset. Examples: "create a full financial report", "generate a comprehensive analysis of all marketing channels", "provide a complete breakdown of all expenses"
        
        - chart: Queries specifically requesting visual representation or graphs of data. Examples: "create a bar chart of monthly sales", "plot the revenue growth over time", "visualize the customer demographics"

        Important rules:
        1. If the query contains words like "describe", "description", "explain", "summarize" or "details about" a specific topic, it's likely a description query.
        2. If the query asks about a specific aspect or dimension (like "spending on LinkedIn" or "marketing expenses"), it's likely a description query.
        3. Reports are broader in scope and typically cover multiple aspects or the entire dataset.

        Query: {query}

        Respond only in this exact format:
        original_query: [the original query]
        query_type: [description/report/chart]"""

        self.prompt = ChatPromptTemplate.from_template(self.template)
        self.model = OllamaLLM(model=model_name)
        self.chain = self.prompt | self.model | self._parse_llm_response
        print("✨ Classifier initialized successfully")

    @staticmethod
    def _parse_llm_response(response: str) -> dict:
        """Parse the LLM response into a dictionary"""
        print("🔍 Parsing LLM response...")
        lines = response.strip().split("\n")
        parsed = {}
        for line in lines:
            key, value = line.split(": ")
            parsed[key] = value.strip()
        print("✨ Response parsed successfully")
        return parsed

    def classify(self, query: str, df: pd.DataFrame) -> QueryType:
        """
        Classify a user query into one of three types: description, report, or chart

        Args:
            query (str): The user's input query
            df (pd.DataFrame): The pandas DataFrame to pass through

        Returns:
            QueryType: A Pydantic model containing the original query, its classification, and the DataFrame
        """
        print("\n🔄 Classifying query...")
        print(f"📝 Query: {query}")
        try:
            print("🤖 Consulting LLM...")
            result = self.chain.invoke({"query": query})
            result["original_query"] = query

            # Apply post-processing rules to handle edge cases
            print("🔍 Applying post-processing rules...")
            result["query_type"] = self._apply_post_processing_rules(
                query, result["query_type"]
            )

            print(f"✨ Query classified as: {result['query_type']}")
            return QueryType(**result, dataframe=df)
        except Exception as e:
            print(f"❌ Error classifying query: {str(e)}")
            raise Exception(f"Error classifying query: {str(e)}")

    def _apply_post_processing_rules(self, query: str, query_type: str) -> str:
        """
        Apply additional rules to refine the classification for edge cases

        Args:
            query (str): The original user query
            query_type (str): The initial classification from the LLM

        Returns:
            str: The potentially updated classification
        """
        print("🔍 Applying classification rules...")
        query_lower = query.lower()

        # Rule 1: If query explicitly mentions "description" or "describe" and is about a specific topic,
        # it should be a description query
        description_indicators = [
            "description of",
            "describe",
            "explain",
            "summarize",
            "details about",
            "details of",
        ]
        if any(indicator in query_lower for indicator in description_indicators):
            # Check if it's about a specific topic (not a general request for everything)
            if not any(
                term in query_lower
                for term in ["all", "every", "complete", "comprehensive", "full"]
            ):
                print("📝 Detected description indicators")
                return "description"

        # Rule 2: If query explicitly asks for a chart or visualization, it should be a chart query
        chart_indicators = [
            "chart",
            "graph",
            "plot",
            "visualize",
            "visualization",
            "diagram",
        ]
        if any(indicator in query_lower for indicator in chart_indicators):
            print("📊 Detected chart indicators")
            return "chart"

        # Rule 3: If query explicitly asks for a comprehensive report, it should be a report query
        report_indicators = [
            "report",
            "analysis of all",
            "comprehensive",
            "full breakdown",
            "complete overview",
        ]
        if any(indicator in query_lower for indicator in report_indicators) and any(
            term in query_lower
            for term in ["all", "every", "complete", "comprehensive", "full"]
        ):
            print("📋 Detected report indicators")
            return "report"

        print(f"✨ Using original classification: {query_type}")
        return query_type


def classify_query(user_query: str, df: pd.DataFrame) -> Tuple[str, str, pd.DataFrame]:
    """
    Classify a user query into one of three types and return the type along with the DataFrame

    Args:
        user_query (str): The user's input query
        df (pd.DataFrame): The pandas DataFrame to pass through

    Returns:
        Tuple[str, str, pd.DataFrame]: A tuple containing (query_type, original_query, dataframe)
    """
    print("\n🔄 Starting query classification...")
    classifier = QueryClassifier()
    try:
        result = classifier.classify(user_query, df)
        print("✅ Classification complete")
        return result.query_type, result.original_query, result.dataframe
    except Exception as e:
        print(f"❌ Error classifying query: {str(e)}")
        raise Exception(f"Error classifying query: {str(e)}")


if __name__ == "__main__":
    print("\n🚀 Running query classifier demo...")
    # Create a sample DataFrame for testing
    sample_df = pd.DataFrame({"A": [1, 2, 3], "B": ["x", "y", "z"]})

    # Test cases
    test_cases = [
        ("generate description of spending on linkedin", "description"),
        ("describe the marketing expenses", "description"),
        ("explain the revenue for Q2", "description"),
        ("create a comprehensive financial report", "report"),
        ("analyze all aspects of our business performance", "report"),
        ("generate a chart showing monthly sales", "chart"),
        ("visualize the customer demographics", "chart"),
        ("summarize the spending on Facebook ads", "description"),
        ("provide details about the ROI for Google Ads", "description"),
        ("create a full breakdown of all marketing channels", "report"),
    ]

    print("\n🧪 Testing Classification Accuracy")
    for query, expected in test_cases:
        print(f"\n📝 Testing query: '{query}'")
        query_type, _, _ = classify_query(query, sample_df)
        result = (
            "✅"
            if query_type == expected
            else f"❌ (got {query_type}, expected {expected})"
        )
        print(f"Expected: {expected}, Result: {result}")

    # Interactive testing
    print("\n🔄 Starting Interactive Testing")
    print("\n💭 Please enter your query")
    query = input("Enter your query: ")
    query_type, original_query, df = classify_query(query, sample_df)
    print(f"\n✨ Results:")
    print(f"📊 Query type: {query_type}")
    print(f"📝 Original query: {original_query}")
    print("\n📋 DataFrame preview:")
    print(df.head())
