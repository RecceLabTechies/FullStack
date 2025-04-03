"""
Database schema definitions for MongoDB collections
"""

from typing import Set

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
    return field_names == CAMPAIGN_FIELDS
