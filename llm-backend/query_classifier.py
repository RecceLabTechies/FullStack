#!/usr/bin/env python
from pydantic import BaseModel
from langchain.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM
import pandas as pd
from typing import Tuple


class QueryType(BaseModel):
    original_query: str
    query_type: str
    dataframe: pd.DataFrame

    class Config:
        arbitrary_types_allowed = True


class QueryClassifier:
    def __init__(self, model_name: str = "llama3.2"):
        self.template = """Classify the following query into one of these categories:
        - description: Queries asking for specific details or explanations about certain aspects
        - report: Queries requesting comprehen sive analysis of all aspects of the dataset
        - chart: Queries specifically requesting visual representation or graphs

        Query: {query}

        Respond only in this exact format:
        original_query: [the original query]
        query_type: [description/report/chart]"""

        self.prompt = ChatPromptTemplate.from_template(self.template)
        self.model = OllamaLLM(model=model_name)
        self.chain = self.prompt | self.model | self._parse_llm_response

    @staticmethod
    def _parse_llm_response(response: str) -> dict:
        """Parse the LLM response into a dictionary"""
        lines = response.strip().split("\n")
        parsed = {}
        for line in lines:
            key, value = line.split(": ")
            parsed[key] = value.strip()
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
        try:
            result = self.chain.invoke({"query": query})
            return QueryType(**result, dataframe=df)
        except Exception as e:
            raise Exception(f"Error classifying query: {str(e)}")


def classify_query(user_query: str, df: pd.DataFrame) -> Tuple[str, str, pd.DataFrame]:
    """
    Classify a user query into one of three types and return the type along with the DataFrame

    Args:
        user_query (str): The user's input query
        df (pd.DataFrame): The pandas DataFrame to pass through

    Returns:
        Tuple[str, str, pd.DataFrame]: A tuple containing (query_type, original_query, dataframe)
    """
    classifier = QueryClassifier()
    try:
        result = classifier.classify(user_query, df)
        return result.query_type, result.original_query, result.dataframe
    except Exception as e:
        raise Exception(f"Error classifying query: {str(e)}")


if __name__ == "__main__":
    # Create a sample DataFrame for testing
    sample_df = pd.DataFrame({"A": [1, 2, 3], "B": ["x", "y", "z"]})

    query = input("Enter your query: ")
    query_type, original_query, df = classify_query(query, sample_df)
    print(f"Query type: {query_type}")
    print(f"Original query: {original_query}")
    print("\nDataFrame preview:")
    print(df.head())
