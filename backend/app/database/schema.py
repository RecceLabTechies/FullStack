"""
Database schema definitions for PostgreSQL tables
"""

# Campaign performance fields definition
CAMPAIGN_FIELDS = {
    "id",
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
    "id",
    "username",
    "email",
    "role",
    "company",
    "password",
    "chart_access",
    "report_generation_access",
    "user_management_access",
    "created_at",
}

# Prophet prediction data fields definition
PROPHET_PREDICTION_FIELDS = {
    "id",
    "date",
    "revenue",
    "ad_spend",
    "new_accounts",
}


def get_table_schema(table_name):
    """Get the PostgreSQL table schema columns"""
    from app.database.connection import Database

    query = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = %s
    """
    result = Database.execute_query(query, (table_name,))
    return {record["column_name"] for record in result}


def matches_campaign_schema(table_columns):
    """Check if a set of column names matches the campaign schema"""
    return table_columns == CAMPAIGN_FIELDS


def matches_user_schema(table_columns):
    """Check if a set of column names matches the user schema"""
    return table_columns == USER_FIELDS


def matches_prophet_prediction_schema(table_columns):
    """Check if a set of column names matches the prophet prediction schema"""
    return table_columns == PROPHET_PREDICTION_FIELDS


def validate_table_schema(table_name):
    """Validate if a table has the expected schema"""
    table_columns = get_table_schema(table_name)

    if table_name == "users":
        return matches_user_schema(table_columns)
    elif table_name == "campaign_performance":
        return matches_campaign_schema(table_columns)
    elif table_name == "prophet_predictions":
        return matches_prophet_prediction_schema(table_columns)
    return False
