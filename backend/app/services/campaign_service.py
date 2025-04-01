import logging
from datetime import datetime
from typing import Dict, List
import pandas as pd
from app.models.campaign import CampaignModel


logger = logging.getLogger(__name__)


def filter_campaigns(filter_params: Dict) -> Dict:
    """
    Filter campaigns based on specified criteria with advanced filtering options.
    When no filter parameters are provided, all campaigns are returned.

    Args:
        filter_params (Dict): Dictionary containing filter parameters:
            - channels: List of marketing channels
            - countries: List of countries
            - age_groups: List of age groups
            - campaign_ids: List of campaign IDs
            - from_date: Start date (Unix timestamp)
            - to_date: End date (Unix timestamp)
            - min_revenue: Minimum revenue amount
            - max_revenue: Maximum revenue amount
            - min_ad_spend: Minimum ad spend amount
            - max_ad_spend: Maximum ad spend amount
            - min_views: Minimum views count
            - min_leads: Minimum leads count
            - sort_by: Field to sort by (default: date)
            - sort_dir: Sort direction (asc or desc, default: desc)
            - page: Page number (default: 1)
            - page_size: Number of results per page (default: 20)

    Returns:
        Dict: Response containing filtered data with pagination metadata
    """
    # Build query
    query = {}  # Empty query matches all documents by default

    # List-based filters (channel, country, age_group, campaign_id)
    if filter_params.get("channels"):
        query["channel"] = {"$in": filter_params["channels"]}

    if filter_params.get("countries"):
        query["country"] = {"$in": filter_params["countries"]}

    if filter_params.get("age_groups"):
        query["age_group"] = {"$in": filter_params["age_groups"]}

    if filter_params.get("campaign_ids"):
        query["campaign_id"] = {"$in": filter_params["campaign_ids"]}

    # Numeric range filters
    for field in ["revenue", "ad_spend"]:
        min_field = f"min_{field}"
        max_field = f"max_{field}"

        if (
            filter_params.get(min_field) is not None
            or filter_params.get(max_field) is not None
        ):
            query.setdefault(field, {})

            if filter_params.get(min_field) is not None:
                query[field]["$gte"] = filter_params[min_field]

            if filter_params.get(max_field) is not None:
                query[field]["$lte"] = filter_params[max_field]

    # Simple minimum filters
    for field in ["views", "leads"]:
        min_field = f"min_{field}"
        if filter_params.get(min_field) is not None:
            query[field] = {"$gte": filter_params[min_field]}

    # Date range filter
    if filter_params.get("from_date") or filter_params.get("to_date"):
        query.setdefault("date", {})

        if filter_params.get("from_date"):
            query["date"]["$gte"] = float(filter_params["from_date"])

        if filter_params.get("to_date"):
            query["date"]["$lte"] = float(filter_params["to_date"])

    # Set default pagination and sorting parameters
    page = filter_params.get("page", 1)
    page_size = filter_params.get("page_size", 20)
    sort_by = filter_params.get("sort_by", "date")
    sort_dir = filter_params.get("sort_dir", "desc")

    # Count total matching documents for pagination info
    total_count = CampaignModel.count(query)

    # Calculate pagination values
    skip = (page - 1) * page_size

    # Determine sort direction (1 for ascending, -1 for descending)
    sort_direction = 1 if sort_dir.lower() == "asc" else -1

    # Get paginated results with sorting
    results = CampaignModel.get_paginated(
        query=query,
        sort_by=sort_by,
        sort_dir=sort_direction,
        skip=skip,
        limit=page_size,
    )

    # Prepare pagination metadata
    total_pages = (total_count + page_size - 1) // page_size

    # Build response with pagination metadata
    response = {
        "items": results,  # Changed from "data" to "items" for consistency with route handler
        "pagination": {
            "total_count": total_count,
            "total_pages": total_pages,
            "page": page,
            "page_size": page_size,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        },
        "filters": {
            k: v
            for k, v in filter_params.items()
            if k not in ["page", "page_size", "sort_by", "sort_dir"]
        },
    }

    return response


def get_monthly_aggregated_data(filter_params: Dict) -> Dict:
    """
    Get monthly aggregated revenue and ad spend data with full campaign filtering support.

    Args:
        filter_params (Dict): Dictionary containing filter parameters:
            - channels: List of marketing channels
            - countries: List of countries
            - age_groups: List of age groups
            - from_date: Start date (Unix timestamp)
            - to_date: End date (Unix timestamp)
            - campaign_ids: List of campaign IDs
            - min_revenue: Minimum revenue amount
            - max_revenue: Maximum revenue amount
            - min_ad_spend: Minimum ad spend amount
            - max_ad_spend: Maximum ad spend amount
            - min_views: Minimum views count
            - min_leads: Minimum leads count

    Returns:
        Dict: Dictionary containing items (monthly aggregated data) and applied filters
    """
    # Make a copy of filter_params without pagination to get all matching data
    query_params = {
        k: v
        for k, v in filter_params.items()
        if k not in ["page", "page_size", "sort_by", "sort_dir"]
    }

    # Add a large page_size to get all data at once for aggregation
    query_params["page_size"] = 10000
    query_params["page"] = 1

    # Get filtered campaign data
    response = filter_campaigns(query_params)

    if not response.get("items"):
        return {"items": [], "filters": query_params}

    # Group data by month and calculate aggregates
    monthly_data = {}

    for item in response["items"]:
        # Convert Unix timestamp to month key (e.g., "2024-01")
        month_key = datetime.fromtimestamp(item["date"]).strftime("%Y-%m")
        month_timestamp = int(datetime.strptime(month_key, "%Y-%m").timestamp())

        if month_key not in monthly_data:
            monthly_data[month_key] = {
                "date": month_timestamp,
                "revenue": 0,
                "ad_spend": 0,
                "views": 0,
                "leads": 0,
                "new_accounts": 0,
            }

        # Aggregate all metrics
        monthly_data[month_key]["revenue"] += item["revenue"]
        monthly_data[month_key]["ad_spend"] += item["ad_spend"]
        monthly_data[month_key]["views"] += item["views"]
        monthly_data[month_key]["leads"] += item["leads"]
        monthly_data[month_key]["new_accounts"] += item["new_accounts"]

    # Sort months chronologically
    sorted_months = sorted(monthly_data.keys())

    # Convert to list of items
    items = [monthly_data[month] for month in sorted_months]

    # Return in the same format as filter_campaigns but without pagination
    return {
        "items": items,
        "filters": {
            k: v
            for k, v in filter_params.items()
            if k not in ["page", "page_size", "sort_by", "sort_dir"]
        },
    }


def get_campaign_filter_options() -> Dict:
    """
    Get all available filter options for campaign data.

    Returns a dictionary with:
    - List of unique values for categorical fields (countries, age_groups, channels, campaign_ids)
    - Range information for numeric fields (revenue, ad_spend, views, leads)
    - Date range information (min_date, max_date)

    Returns:
        Dict: Dictionary containing all available filter options
    """
    # Get distinct values for categorical fields
    countries = sorted(CampaignModel.get_distinct("country"))
    age_groups = CampaignModel.get_distinct("age_group")
    channels = sorted(CampaignModel.get_distinct("channel"))
    campaign_ids = sorted(CampaignModel.get_distinct("campaign_id"))

    # Sort age groups in proper order
    standard_age_groups = ["18-24", "25-34", "35-44", "45-54", "55+"]
    # Filter out any non-standard age groups and sort them
    standard_groups = [g for g in age_groups if g in standard_age_groups]
    other_groups = sorted([g for g in age_groups if g not in standard_age_groups])
    # Combine them with standard groups first in the right order, then any others
    age_groups = (
        sorted(standard_groups, key=lambda x: standard_age_groups.index(x))
        + other_groups
    )

    # Get min/max for numeric fields using aggregation
    numeric_ranges = {}
    for field in ["revenue", "ad_spend", "views", "leads"]:
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "min": {"$min": f"${field}"},
                    "max": {"$max": f"${field}"},
                    "avg": {"$avg": f"${field}"},
                }
            }
        ]

        result = CampaignModel.aggregate(pipeline)

        if result:
            numeric_ranges[field] = {
                "min": result[0]["min"],
                "max": result[0]["max"],
                "avg": result[0]["avg"],
            }
        else:
            numeric_ranges[field] = {"min": 0, "max": 0, "avg": 0}

    # Get date range
    date_range = {}
    date_pipeline = [
        {
            "$group": {
                "_id": None,
                "min_date": {"$min": "$date"},
                "max_date": {"$max": "$date"},
            }
        }
    ]

    date_result = CampaignModel.aggregate(date_pipeline)

    if date_result:
        date_range["min_date"] = float(date_result[0]["min_date"])
        date_range["max_date"] = float(date_result[0]["max_date"])

    # Build and return complete filter options
    return {
        "categorical": {
            "countries": countries,
            "age_groups": age_groups,
            "channels": channels,
            "campaign_ids": campaign_ids,
        },
        "numeric_ranges": numeric_ranges,
        "date_range": date_range,
    }


def get_cost_heatmap_data(
    country: str, campaign_id: str, channels: List[str] = None
) -> List[Dict]:
    """
    Generate cost heatmap data showing cost metrics by channel.

    Args:
        country (str): Country to filter data for
        campaign_id (str): Campaign ID to filter data for
        channels (List[str], optional): List of channels to include. If None, uses default channels.

    Returns:
        List[Dict]: List of dictionaries with channel and cost metrics (costPerLead, costPerView, costPerAccount)
    """
    data = CampaignModel.get_all()  # Fetch data, excluding _id

    if not data:
        return []

    df = pd.DataFrame(data)

    # Apply filters
    df = df[(df["country"] == country) & (df["campaign_id"] == campaign_id)]

    # Filter for specific channels if provided, otherwise use default channels
    default_channels = [
        "LinkedIn",
        "Facebook ads",
        "Google banner ads",
        "Influencer",
        "Instagram Ads",
        "TikTok ads",
        "Sponsored search ads",
    ]

    channels_to_use = channels if channels else default_channels
    df = df[df["channel"].isin(channels_to_use)]

    if df.empty:
        return []

    # Convert numeric columns
    numeric_columns = ["ad_spend", "leads", "new_accounts", "views"]
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop rows with missing values
    df.dropna(inplace=True)

    if df.empty:
        return []

    # Grouping by channel and calculating sums
    df_grouped = (
        df.groupby("channel")
        .agg(
            {
                "ad_spend": "sum",
                "leads": "sum",
                "new_accounts": "sum",
                "views": "sum",
            }
        )
        .reset_index()
    )

    # Calculate cost metrics, avoiding division by zero
    df_grouped["costPerLead"] = df_grouped["ad_spend"] / df_grouped["leads"].replace(
        0, 1e-6
    )
    df_grouped["costPerView"] = df_grouped["ad_spend"] / df_grouped["views"].replace(
        0, 1e-6
    )
    df_grouped["costPerAccount"] = df_grouped["ad_spend"] / df_grouped[
        "new_accounts"
    ].replace(0, 1e-6)

    # Round values
    df_grouped = df_grouped.round(4)

    # Prepare data for response
    data_summary = df_grouped[
        ["channel", "costPerLead", "costPerView", "costPerAccount"]
    ].to_dict(orient="records")

    return data_summary
