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
VALIDATOR_MODEL = "mixtral-8x7b-32768"
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

    Args:
        model_name: The model name to use. If None, uses CLASSIFIER_MODEL

    Returns:
        A configured ChatGroq instance
    """
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not found in environment variables")

    if model_name is None:
        model_name = CLASSIFIER_MODEL

    return ChatGroq(api_key=GROQ_API_KEY, model_name=model_name)
