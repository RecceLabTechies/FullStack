import logging
from datetime import datetime
from typing import Dict, List
import pandas as pd
from app.database.connection import get_campaign_performance_collection
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


def get_monthly_performance_data(filters: Dict = None) -> Dict:
    """
    Get monthly revenue and ad spend data for charting.

    Args:
        filters (Dict, optional): Dictionary containing filter parameters:
            - from_date: Start date as Unix timestamp
            - to_date: End date as Unix timestamp
            - channels: List of marketing channels
            - countries: List of countries
            - age_groups: List of age groups

    Returns:
        Dict: Dictionary containing arrays for months, revenue, ad_spend, and ROI
    """
    # Initialize filters if None
    if filters is None:
        filters = {}

    # Build query based on filters
    query = {}

    # Date range filters
    if "from_date" in filters:
        query.setdefault("date", {})["$gte"] = float(filters["from_date"])

    if "to_date" in filters:
        query.setdefault("date", {})["$lte"] = float(filters["to_date"])

    # Categorical filters
    if "channels" in filters and filters["channels"]:
        query["channel"] = {"$in": filters["channels"]}

    if "countries" in filters and filters["countries"]:
        query["country"] = {"$in": filters["countries"]}

    if "age_groups" in filters and filters["age_groups"]:
        query["age_group"] = {"$in": filters["age_groups"]}

    # Aggregate data by month
    pipeline = [
        {"$match": query},
        {
            "$addFields": {
                "dateObj": {
                    "$toDate": {
                        "$multiply": [
                            "$date",
                            1000,
                        ]  # Convert Unix timestamp to date object for MongoDB
                    }
                }
            }
        },
        {
            "$group": {
                "_id": {"year": {"$year": "$dateObj"}, "month": {"$month": "$dateObj"}},
                "revenue": {"$sum": "$revenue"},
                "ad_spend": {"$sum": "$ad_spend"},
            }
        },
        {"$sort": {"_id.year": 1, "_id.month": 1}},
    ]

    results = CampaignModel.aggregate(pipeline)

    # Format results
    months = []
    revenue = []
    ad_spend = []
    roi = []

    for result in results:
        # Convert back to Unix timestamp for the first day of the month
        month_date = datetime(result["_id"]["year"], result["_id"]["month"], 1)
        months.append(month_date.timestamp())
        revenue.append(result["revenue"])
        ad_spend.append(result["ad_spend"])
        roi.append(
            (result["revenue"] - result["ad_spend"]) / result["ad_spend"]
            if result["ad_spend"] > 0
            else 0
        )

    return {
        "months": months,
        "revenue": revenue,
        "ad_spend": ad_spend,
        "roi": roi,
    }


def update_monthly_data(updates: List[Dict]) -> Dict:
    """
    Update revenue and/or ad spend data for specific months.

    Args:
        updates (List[Dict]): List of updates, each containing:
            - month (float): Month as Unix timestamp
            - revenue (float, optional): New revenue value
            - ad_spend (float, optional): New ad spend value

    Returns:
        Dict: Updated monthly performance data
    """
    collection = get_campaign_performance_collection()

    for update in updates:
        if "month" not in update:
            raise ValueError("Each update must contain month")

        if "revenue" not in update and "ad_spend" not in update:
            raise ValueError("Each update must contain either revenue or ad_spend")

        # Get the Unix timestamp from the month field
        month_timestamp = update["month"]

        # Convert Unix timestamp to datetime for calculations
        month_date = datetime.fromtimestamp(month_timestamp)
        start_date = month_date.replace(day=1, hour=0, minute=0, second=0).timestamp()

        # Calculate end date (first day of next month)
        if month_date.month == 12:
            end_date = datetime(month_date.year + 1, 1, 1).timestamp()
        else:
            end_date = datetime(month_date.year, month_date.month + 1, 1).timestamp()

        # Find all campaigns in this month
        query = {"date": {"$gte": start_date, "$lt": end_date}}
        campaigns = CampaignModel.get_all(query)

        if not campaigns:
            continue

        # Update revenue if provided
        if "revenue" in update:
            # Calculate current total revenue for the month
            current_total = sum(campaign.get("revenue", 0) for campaign in campaigns)

            if current_total == 0:
                # If no current revenue, distribute equally
                new_value = update["revenue"] / len(campaigns)
                for campaign in campaigns:
                    CampaignModel.update_one(
                        {"_id": campaign["_id"]}, {"$set": {"revenue": new_value}}
                    )
            else:
                # Apply proportional update
                scale_factor = update["revenue"] / current_total
                for campaign in campaigns:
                    new_revenue = campaign.get("revenue", 0) * scale_factor
                    CampaignModel.update_one(
                        {"_id": campaign["_id"]}, {"$set": {"revenue": new_revenue}}
                    )

        # Update ad_spend if provided
        if "ad_spend" in update:
            # Calculate current total ad_spend for the month
            current_total = sum(campaign.get("ad_spend", 0) for campaign in campaigns)

            if current_total == 0:
                # If no current ad_spend, distribute equally
                new_value = update["ad_spend"] / len(campaigns)
                for campaign in campaigns:
                    CampaignModel.update_one(
                        {"_id": campaign["_id"]}, {"$set": {"ad_spend": new_value}}
                    )
            else:
                # Apply proportional update
                scale_factor = update["ad_spend"] / current_total
                for campaign in campaigns:
                    new_ad_spend = campaign.get("ad_spend", 0) * scale_factor
                    CampaignModel.update_one(
                        {"_id": campaign["_id"]}, {"$set": {"ad_spend": new_ad_spend}}
                    )

    # Return updated chart data
    return get_monthly_performance_data()


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
