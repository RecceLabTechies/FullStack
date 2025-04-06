"""
LLM Configuration Module

This module provides centralized configuration for Large Language Model (LLM)
providers used throughout the application. It handles API key management,
model configuration, and provides a factory function for creating configured
LLM instances.

Key features:
- Environment variable loading for API keys
- Centralized model name configuration
- Factory function for creating properly configured LLM instances
"""

import logging
import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Groq API configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    logger.warning("GROQ_API_KEY not found in environment variables")

# Model configurations
CLASSIFIER_MODEL = "llama3-8b-8192"
VALIDATOR_MODEL = "llama3-8b-8192"
COLLECTION_SELECTOR_MODEL = "llama3-8b-8192"
COLLECTION_PROCESSOR_MODEL = "qwen-2.5-coder-32b"
DESCRIPTION_GENERATOR_SELECTOR_MODEL = "llama3-8b-8192"
DESCRIPTION_GENERATOR_MODEL = "deepseek-r1-distill-llama-70b"
ANALYSIS_QUERIES_MODEL = "llama3-8b-8192"
CHART_DATA_MODEL = "llama3-8b-8192"


# Function to get a configured Groq LLM
def get_groq_llm(model_name=None):
    """
    Get a configured Groq LLM instance.

    This factory function creates and returns a properly configured ChatGroq instance
    ready to be used for making LLM API calls. It ensures the API key is available and
    sets the appropriate model.

    Args:
        model_name (str, optional): The model name to use. If None, defaults to CLASSIFIER_MODEL
                                    which is "llama3-8b-8192"

    Returns:
        ChatGroq: A configured ChatGroq instance ready for use

    Raises:
        ValueError: If GROQ_API_KEY is not found in environment variables
    """
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not found in environment variables")

    if model_name is None:
        model_name = CLASSIFIER_MODEL

    logger.debug(f"Creating ChatGroq instance with model: {model_name}")
    return ChatGroq(api_key=GROQ_API_KEY, model_name=model_name)
