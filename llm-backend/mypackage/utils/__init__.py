"""
Utilities Module

This module provides utility functions and classes for database operations,
logging configuration, LLM configuration, and schema validation.
"""

from mypackage.utils.database import (
    Database,
    get_campaign_performance_collection,
    is_collection_accessible,
)
from mypackage.utils.llm_config import (
    get_groq_llm,
)
from mypackage.utils.logging_config import (
    setup_logging,
)
from mypackage.utils.schema import (
    CampaignData,
    matches_campaign_schema,
)

__all__ = [
    # Classes
    "Database",
    "CampaignData",
    # Functions
    "get_campaign_performance_collection",
    "is_collection_accessible",
    "get_groq_llm",
    "setup_logging",
    "matches_campaign_schema",
]
