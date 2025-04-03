"""
Database schema definitions for MongoDB collections
"""

from typing import Set, Dict, Any, List, Optional, Union
from typing_extensions import TypedDict


class CampaignData(TypedDict):
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


class UserData(TypedDict):
    username: str
    email: str
    role: str
    company: str
    password: str
    chart_access: bool
    report_generation_access: bool
    user_management_access: bool


class ProphetPredictionData(TypedDict):
    date: str
    revenue: float
    ad_spend: float
    new_accounts: int


# Campaign performance fields definition
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

# User fields definition
USER_FIELDS: Set[str] = {
    "username",
    "email",
    "role",
    "company",
    "password",
    "chart_access",
    "report_generation_access",
    "user_management_access",
}

# Prophet prediction data fields definition
PROPHET_PREDICTION_FIELDS: Set[str] = {
    "date",
    "revenue",
    "ad_spend",
    "new_accounts",
}


def matches_campaign_schema(field_names: Set[str]) -> bool:
    """Check if a set of field names matches the campaign schema"""
    return field_names == CAMPAIGN_FIELDS


def matches_user_schema(field_names: Set[str]) -> bool:
    """Check if a set of field names matches the user schema"""
    return field_names == USER_FIELDS


def matches_prophet_prediction_schema(field_names: Set[str]) -> bool:
    """Check if a set of field names matches the prophet prediction schema"""
    return field_names == PROPHET_PREDICTION_FIELDS
