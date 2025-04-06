"""
Database Schema Definitions Module

This module defines the expected schema for MongoDB collections used in the application.
It provides type definitions and validation functions to ensure data consistency
across database operations.

The module uses typing_extensions.TypedDict to define strongly-typed dictionaries
that represent the expected structure of documents in each collection.
"""

from typing import Set

from typing_extensions import TypedDict


class CampaignData(TypedDict):
    """
    Schema definition for campaign performance data.

    This TypedDict defines the expected structure for documents in the
    campaign_performance collection, including field names and their types.

    Attributes:
        date (str): Date of the campaign metrics in ISO format
        campaign_id (str): Unique identifier for the campaign
        channel (str): Marketing channel used (e.g., "email", "social")
        age_group (str): Target demographic age group
        ad_spend (float): Amount spent on advertising
        views (int): Number of ad views/impressions
        leads (int): Number of leads generated
        new_accounts (int): Number of new accounts created
        country (str): Target country for the campaign
        revenue (float): Revenue generated from the campaign
    """

    date: str
    campaign_id: str
    channel: str
    age_group: str
    ad_spend: float
    views: int
    leads: int
    new_accounts: int
    country: str
    revenue: float


# Define the set of fields expected in the campaign_performance collection
CAMPAIGN_FIELDS: Set[str] = {
    "date",
    "campaign_id",
    "channel",
    "age_group",
    "ad_spend",
    "views",
    "leads",
    "new_accounts",
    "country",
    "revenue",
}


def matches_campaign_schema(field_names: Set[str]) -> bool:
    """
    Check if a set of field names matches the expected campaign schema.

    This function validates that a document or collection has exactly the
    expected fields for campaign data, no more and no less.

    Args:
        field_names (Set[str]): Set of field names to validate

    Returns:
        bool: True if the field names exactly match CAMPAIGN_FIELDS, False otherwise

    Example:
        >>> doc = {"date": "2023-01-01", "campaign_id": "C123", ...}
        >>> matches_campaign_schema(set(doc.keys()))
        True
    """
    return field_names == CAMPAIGN_FIELDS
