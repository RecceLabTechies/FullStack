"""
Database schema definitions for MongoDB collections in LLM backend
"""

# Query fields definition
QUERY_FIELDS = {
    "timestamp",
    "query_text",
    "user_id",
    "status",
    "processing_time",
}

# Results fields definition
RESULTS_FIELDS = {
    "query_id",
    "timestamp",
    "output",
    "original_query",
    "metadata",
    "status",
}


def matches_query_schema(field_names):
    """Check if a set of field names matches the query schema"""
    return field_names == QUERY_FIELDS


def matches_results_schema(field_names):
    """Check if a set of field names matches the results schema"""
    return field_names == RESULTS_FIELDS
