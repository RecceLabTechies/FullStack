"""
Database schema definitions for MongoDB collections
"""

# Campaign performance fields definition
CAMPAIGN_FIELDS = {
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
USER_FIELDS = {
    "username",
    "email",
    "role",
    "company",
    "password",
    "chart_access",
    "report_generation_access",
    "user_management_access",
}


def matches_campaign_schema(field_names):
    """Check if a set of field names matches the campaign schema"""
    return field_names == CAMPAIGN_FIELDS


def matches_user_schema(field_names):
    """Check if a set of field names matches the user schema"""
    return field_names == USER_FIELDS
