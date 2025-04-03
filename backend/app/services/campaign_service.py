import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from typing_extensions import TypedDict
import pandas as pd
import numpy as np
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


class ChannelMetricValues(TypedDict):
    """Type definition for a channel's metric values."""

    metric: str
    values: Dict[str, float]


class TimeRange(TypedDict):
    """Type definition for time range information."""

    from_: Optional[str]
    to: Optional[str]


class ChannelContributionResponse(TypedDict):
    """Type definition for channel contribution response."""

    metrics: List[str]
    channels: List[str]
    data: List[ChannelMetricValues]
    time_range: TimeRange
    error: Optional[str]


def get_channel_contribution_data() -> ChannelContributionResponse:
    """
    Generate channel contribution data for various metrics over the latest 3 months.

    Returns:
        ChannelContributionResponse: Dictionary containing channel contribution percentages for
                                    different metrics and metadata
    """
    # Default empty response
    empty_response: ChannelContributionResponse = {
        "metrics": [],
        "channels": [],
        "data": [],
        "time_range": {"from_": None, "to": None},
        "error": None,
    }

    # Get all campaign data
    data = CampaignModel.get_all()

    if not data:
        return empty_response

    # Convert to DataFrame
    df = pd.DataFrame(data)

    # Validate required columns exist
    required_columns = [
        "date",
        "channel",
        "ad_spend",
        "views",
        "leads",
        "new_accounts",
        "revenue",
    ]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        error_msg = f"Missing required columns: {missing_columns}"
        logger.error(error_msg)
        empty_response["error"] = error_msg
        return empty_response

    # Ensure date field contains valid timestamps
    try:
        # Convert date from timestamp to datetime for filtering
        df["datetime"] = pd.to_datetime(df["date"], unit="s", errors="coerce")
        # Drop rows with invalid dates
        invalid_dates = df["datetime"].isna().sum()
        if invalid_dates > 0:
            logger.warning(f"Found {invalid_dates} records with invalid date format")
            df = df.dropna(subset=["datetime"])
    except Exception as e:
        error_msg = f"Date conversion error: {str(e)}"
        logger.error(error_msg)
        empty_response["error"] = error_msg
        return empty_response

    if df.empty:
        return empty_response

    # Get the latest 3 months of data
    df = df.sort_values("datetime", ascending=False)
    unique_months = df["datetime"].dt.strftime("%Y-%m").unique()
    latest_months = sorted(unique_months[: min(3, len(unique_months))])

    # Filter data for the latest 3 months
    df["month"] = df["datetime"].dt.strftime("%Y-%m")
    df = df[df["month"].isin(latest_months)]

    if df.empty:
        return empty_response

    # Ensure numeric columns are parsed correctly
    numeric_columns = ["ad_spend", "views", "leads", "new_accounts", "revenue"]
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop rows with NaN values in numeric columns after conversion
    df = df.dropna(subset=numeric_columns)

    if df.empty:
        return empty_response

    # Group by channel and sum the metrics
    channel_metrics = df.groupby("channel")[numeric_columns].sum().reset_index()

    # Get the list of unique channels
    channels = sorted(channel_metrics["channel"].unique().tolist())

    if not channels:
        return empty_response

    # Define metrics mapping
    metrics_mapping: Dict[str, str] = {
        "ad_spend": "Spending",
        "views": "Views",
        "leads": "Leads",
        "new_accounts": "New Accounts",
        "revenue": "Revenue",
    }

    # Calculate percentage contribution for each metric
    result_data: List[ChannelMetricValues] = []

    for metric, display_name in metrics_mapping.items():
        # Calculate total for the metric
        total = channel_metrics[metric].sum()

        if total <= 0:
            # Skip metrics with zero or negative total to avoid division issues
            logger.warning(f"Skipping metric '{metric}' as total is {total}")
            continue

        # Calculate percentages for each channel
        metric_data: ChannelMetricValues = {"metric": display_name, "values": {}}

        for channel in channels:
            # Use safe filtering to get channel value
            channel_data = channel_metrics[channel_metrics["channel"] == channel]
            if len(channel_data) > 0:
                channel_value = channel_data[metric].iloc[0]
                percentage = (channel_value / total) * 100
                metric_data["values"][channel] = round(percentage, 2)
            else:
                # If channel doesn't have data for this metric, set to zero
                metric_data["values"][channel] = 0.0

        result_data.append(metric_data)

    # Format the response
    response: ChannelContributionResponse = {
        "metrics": [item["metric"] for item in result_data],
        "channels": channels,
        "data": result_data,
        "time_range": {
            "from_": latest_months[0] if latest_months else None,
            "to": latest_months[-1] if latest_months else None,
        },
        "error": None,
    }

    return response


class HeatmapCell(TypedDict):
    """Type definition for a heatmap cell data."""

    value: float
    intensity: float


class HeatmapRow(TypedDict):
    """Type definition for a heatmap row data."""

    metric: str
    values: Dict[str, HeatmapCell]


class HeatmapResponse(TypedDict):
    """Type definition for cost metrics heatmap response."""

    metrics: List[str]
    channels: List[str]
    data: List[HeatmapRow]
    time_range: TimeRange
    error: Optional[str]


def get_cost_metrics_heatmap() -> HeatmapResponse:
    """
    Generate cost metrics heatmap data showing different cost metrics by channel.
    Uses data from the latest 3 months similar to channel contribution data.

    Returns:
        HeatmapResponse: Dictionary containing cost metrics data formatted for heatmap visualization
    """
    # Default empty response
    empty_response: HeatmapResponse = {
        "metrics": [],
        "channels": [],
        "data": [],
        "time_range": {"from_": None, "to": None},
        "error": None,
    }

    # Get all campaign data
    data = CampaignModel.get_all()

    if not data:
        empty_response["error"] = "No campaign data found"
        return empty_response

    # Convert to DataFrame
    df = pd.DataFrame(data)

    # Validate required columns exist
    required_columns = ["date", "channel", "ad_spend", "views", "leads", "new_accounts"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        error_msg = f"Missing required columns: {missing_columns}"
        logger.error(error_msg)
        empty_response["error"] = error_msg
        return empty_response

    # Convert date from timestamp to datetime for filtering
    try:
        # Convert date from timestamp to datetime for filtering
        df["datetime"] = pd.to_datetime(df["date"], unit="s", errors="coerce")
        # Drop rows with invalid dates
        invalid_dates = df["datetime"].isna().sum()
        if invalid_dates > 0:
            logger.warning(f"Found {invalid_dates} records with invalid date format")
            df = df.dropna(subset=["datetime"])
    except Exception as e:
        error_msg = f"Date conversion error: {str(e)}"
        logger.error(error_msg)
        empty_response["error"] = error_msg
        return empty_response

    if df.empty:
        empty_response["error"] = "No valid data after filtering"
        return empty_response

    # Get the latest 3 months of data
    df = df.sort_values("datetime", ascending=False)
    unique_months = df["datetime"].dt.strftime("%Y-%m").unique()
    latest_months = sorted(unique_months[: min(3, len(unique_months))])

    # Filter data for the latest 3 months
    df["month"] = df["datetime"].dt.strftime("%Y-%m")
    df = df[df["month"].isin(latest_months)]

    if df.empty:
        empty_response["error"] = "No data available for the latest 3 months"
        return empty_response

    # Ensure numeric columns are parsed correctly
    numeric_columns = ["ad_spend", "views", "leads", "new_accounts"]
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop rows with NaN values in numeric columns after conversion
    df = df.dropna(subset=numeric_columns)

    if df.empty:
        empty_response["error"] = "No valid data after filtering"
        return empty_response

    # Group by channel and sum metrics
    channel_metrics = (
        df.groupby("channel")
        .agg(
            {
                "ad_spend": "sum",
                "views": "sum",
                "leads": "sum",
                "new_accounts": "sum",
            }
        )
        .reset_index()
    )

    # Calculate cost metrics, avoiding division by zero
    channel_metrics["cost_per_lead"] = channel_metrics["ad_spend"] / channel_metrics[
        "leads"
    ].replace(0, np.nan)
    channel_metrics["cost_per_view"] = channel_metrics["ad_spend"] / channel_metrics[
        "views"
    ].replace(0, np.nan)
    channel_metrics["cost_per_account"] = channel_metrics["ad_spend"] / channel_metrics[
        "new_accounts"
    ].replace(0, np.nan)

    # Get list of channels
    channels = sorted(channel_metrics["channel"].unique().tolist())

    if not channels:
        empty_response["error"] = "No valid channels found"
        return empty_response

    # Define metrics to display
    metrics = ["cost_per_lead", "cost_per_view", "cost_per_account"]
    display_metrics = ["Cost Per Lead", "Cost Per View", "Cost Per New Account"]

    # Calculate heatmap data
    metrics_data: List[HeatmapRow] = []

    for i, metric in enumerate(metrics):
        # Handle NaN values
        metric_values = channel_metrics[metric].replace(np.nan, 0)

        # Skip if all values are zero
        if all(metric_values == 0):
            continue

        # Calculate intensity based on value (higher value = higher intensity)
        max_value = metric_values.max()

        if max_value == 0:
            # Avoid division by zero
            continue

        heatmap_row: HeatmapRow = {"metric": display_metrics[i], "values": {}}

        for channel in channels:
            channel_data = channel_metrics[channel_metrics["channel"] == channel]
            if len(channel_data) > 0:
                value = float(channel_data[metric].iloc[0])
                # Handle NaN values
                if pd.isna(value):
                    value = 0.0

                # Calculate intensity from 0 to 1
                intensity = float(value / max_value) if max_value > 0 else 0

                heatmap_row["values"][channel] = {
                    "value": round(value, 4),
                    "intensity": round(intensity, 2),
                }
            else:
                heatmap_row["values"][channel] = {"value": 0, "intensity": 0}

        metrics_data.append(heatmap_row)

    # Format the response
    response: HeatmapResponse = {
        "metrics": [item["metric"] for item in metrics_data],
        "channels": channels,
        "data": metrics_data,
        "time_range": {
            "from_": latest_months[0] if latest_months else None,
            "to": latest_months[-1] if latest_months else None,
        },
        "error": None,
    }

    return response


def get_latest_month_roi() -> Dict:
    """
    Calculate ROI for the latest month in the dataset.
    ROI = (Revenue - Ad Spend) / Ad Spend * 100

    Returns:
        Dict: Dictionary containing ROI value, month, and year
    """
    # Get all campaign data
    data = CampaignModel.get_all()

    if not data:
        return {"roi": 0, "month": None, "year": None, "error": "No data available"}

    # Convert to DataFrame
    df = pd.DataFrame(data)

    try:
        # Convert date from timestamp to datetime for filtering
        df["datetime"] = pd.to_datetime(df["date"], unit="s")

        # Get the latest month's data
        df["month_year"] = df["datetime"].dt.strftime("%Y-%m")
        latest_month = df["month_year"].max()

        if not latest_month:
            return {
                "roi": 0,
                "month": None,
                "year": None,
                "error": "No valid dates found",
            }

        # Filter for latest month
        latest_data = df[df["month_year"] == latest_month]

        # Calculate total revenue and ad spend
        total_revenue = latest_data["revenue"].sum()
        total_ad_spend = latest_data["ad_spend"].sum()

        # Calculate ROI
        roi = (
            ((total_revenue - total_ad_spend) / total_ad_spend * 100)
            if total_ad_spend > 0
            else 0
        )

        # Extract month and year
        date_parts = latest_month.split("-")

        return {
            "roi": round(roi, 2),
            "month": int(date_parts[1]),
            "year": int(date_parts[0]),
            "error": None,
        }

    except Exception as e:
        logger.error(f"Error calculating ROI: {e}")
        return {"roi": 0, "month": None, "year": None, "error": str(e)}


def get_latest_month_revenue() -> Dict:
    """
    Get total revenue for the latest month in the dataset.

    Returns:
        Dict: Dictionary containing revenue value, month, and year
    """
    # Get all campaign data
    data = CampaignModel.get_all()

    if not data:
        return {"revenue": 0, "month": None, "year": None, "error": "No data available"}

    # Convert to DataFrame
    df = pd.DataFrame(data)

    try:
        # Convert date from timestamp to datetime for filtering
        df["datetime"] = pd.to_datetime(df["date"], unit="s")

        # Get the latest month's data
        df["month_year"] = df["datetime"].dt.strftime("%Y-%m")
        latest_month = df["month_year"].max()

        if not latest_month:
            return {
                "revenue": 0,
                "month": None,
                "year": None,
                "error": "No valid dates found",
            }

        # Filter for latest month
        latest_data = df[df["month_year"] == latest_month]

        # Calculate total revenue
        total_revenue = latest_data["revenue"].sum()

        # Extract month and year
        date_parts = latest_month.split("-")

        return {
            "revenue": round(total_revenue, 2),
            "month": int(date_parts[1]),
            "year": int(date_parts[0]),
            "error": None,
        }

    except Exception as e:
        logger.error(f"Error calculating revenue: {e}")
        return {"revenue": 0, "month": None, "year": None, "error": str(e)}


def get_monthly_age_data() -> Dict:
    """
    Get monthly data aggregated by age group for charting purposes.
    Returns revenue and ad spend metrics per month per age group.

    Returns:
        Dict: Dictionary containing:
            - months: List of months as timestamps
            - age_groups: List of available age groups
            - revenue: Dictionary with age group keys and monthly revenue arrays
            - ad_spend: Dictionary with age group keys and monthly ad spend arrays
    """
    try:
        # Get all distinct age groups
        age_groups = CampaignModel.get_distinct("age_group")

        # Aggregate the data by month and age group
        pipeline = [
            # Group by month and age group, calculating sums
            {
                "$group": {
                    "_id": {
                        # Extract year and month to group by month
                        "year": {"$year": {"$toDate": {"$multiply": ["$date", 1000]}}},
                        "month": {
                            "$month": {"$toDate": {"$multiply": ["$date", 1000]}}
                        },
                        "age_group": "$age_group",
                    },
                    "revenue": {"$sum": "$revenue"},
                    "ad_spend": {"$sum": "$ad_spend"},
                    # Get the first date in each month (for display purposes)
                    "date": {"$first": "$date"},
                }
            },
            # Sort by date and age group
            {"$sort": {"_id.year": 1, "_id.month": 1, "_id.age_group": 1}},
        ]

        results = CampaignModel.aggregate(pipeline)

        # Transform the data to be suitable for Recharts
        months = []
        revenue_by_age = {age_group: [] for age_group in age_groups}
        ad_spend_by_age = {age_group: [] for age_group in age_groups}

        # Group by month first
        month_data = {}
        for item in results:
            date_key = (item["_id"]["year"], item["_id"]["month"])
            age_group = item["_id"]["age_group"]

            if date_key not in month_data:
                month_data[date_key] = {"date": item["date"], "age_groups": {}}

            month_data[date_key]["age_groups"][age_group] = {
                "revenue": item["revenue"],
                "ad_spend": item["ad_spend"],
            }

        # Sort months and fill in the data
        sorted_months = sorted(month_data.keys())
        for month_key in sorted_months:
            month_timestamp = month_data[month_key]["date"]
            months.append(month_timestamp)

            # For each age group, get its data for this month
            for age_group in age_groups:
                if age_group in month_data[month_key]["age_groups"]:
                    age_data = month_data[month_key]["age_groups"][age_group]
                    revenue_by_age[age_group].append(age_data["revenue"])
                    ad_spend_by_age[age_group].append(age_data["ad_spend"])
                else:
                    # Age group has no data for this month, add 0
                    revenue_by_age[age_group].append(0)
                    ad_spend_by_age[age_group].append(0)

        return {
            "months": months,
            "age_groups": age_groups,
            "revenue": revenue_by_age,
            "ad_spend": ad_spend_by_age,
        }

    except Exception as e:
        logger.error(f"Error getting monthly age group data: {e}")
        raise


def get_monthly_channel_data() -> Dict:
    """
    Get monthly data aggregated by channel for charting purposes.
    Returns revenue and ad spend metrics per month per channel.

    Returns:
        Dict: Dictionary containing:
            - months: List of months as timestamps
            - channels: List of available channels
            - revenue: Dictionary with channel keys and monthly revenue arrays
            - ad_spend: Dictionary with channel keys and monthly ad spend arrays
    """
    try:
        # Get all distinct channels
        channels = CampaignModel.get_distinct("channel")

        # Aggregate the data by month and channel
        pipeline = [
            # Group by month and channel, calculating sums
            {
                "$group": {
                    "_id": {
                        # Extract year and month to group by month
                        "year": {"$year": {"$toDate": {"$multiply": ["$date", 1000]}}},
                        "month": {
                            "$month": {"$toDate": {"$multiply": ["$date", 1000]}}
                        },
                        "channel": "$channel",
                    },
                    "revenue": {"$sum": "$revenue"},
                    "ad_spend": {"$sum": "$ad_spend"},
                    # Get the first date in each month (for display purposes)
                    "date": {"$first": "$date"},
                }
            },
            # Sort by date and channel
            {"$sort": {"_id.year": 1, "_id.month": 1, "_id.channel": 1}},
        ]

        results = CampaignModel.aggregate(pipeline)

        # Transform the data to be suitable for Recharts
        months = []
        revenue_by_channel = {channel: [] for channel in channels}
        ad_spend_by_channel = {channel: [] for channel in channels}

        # Group by month first
        month_data = {}
        for item in results:
            date_key = (item["_id"]["year"], item["_id"]["month"])
            channel = item["_id"]["channel"]

            if date_key not in month_data:
                month_data[date_key] = {"date": item["date"], "channels": {}}

            month_data[date_key]["channels"][channel] = {
                "revenue": item["revenue"],
                "ad_spend": item["ad_spend"],
            }

        # Sort months and fill in the data
        sorted_months = sorted(month_data.keys())
        for month_key in sorted_months:
            month_timestamp = month_data[month_key]["date"]
            months.append(month_timestamp)

            # For each channel, get its data for this month
            for channel in channels:
                if channel in month_data[month_key]["channels"]:
                    channel_data = month_data[month_key]["channels"][channel]
                    revenue_by_channel[channel].append(channel_data["revenue"])
                    ad_spend_by_channel[channel].append(channel_data["ad_spend"])
                else:
                    # Channel has no data for this month, add 0
                    revenue_by_channel[channel].append(0)
                    ad_spend_by_channel[channel].append(0)

        return {
            "months": months,
            "channels": channels,
            "revenue": revenue_by_channel,
            "ad_spend": ad_spend_by_channel,
        }

    except Exception as e:
        logger.error(f"Error getting monthly channel data: {e}")
        raise


def get_monthly_country_data() -> Dict:
    """
    Get monthly data aggregated by country for charting purposes.
    Returns revenue and ad spend metrics per month per country.

    Returns:
        Dict: Dictionary containing:
            - months: List of months as timestamps
            - countries: List of available countries
            - revenue: Dictionary with country keys and monthly revenue arrays
            - ad_spend: Dictionary with country keys and monthly ad spend arrays
    """
    try:
        # Get all distinct countries
        countries = CampaignModel.get_distinct("country")

        # Aggregate the data by month and country
        pipeline = [
            # Group by month and country, calculating sums
            {
                "$group": {
                    "_id": {
                        # Extract year and month to group by month
                        "year": {"$year": {"$toDate": {"$multiply": ["$date", 1000]}}},
                        "month": {
                            "$month": {"$toDate": {"$multiply": ["$date", 1000]}}
                        },
                        "country": "$country",
                    },
                    "revenue": {"$sum": "$revenue"},
                    "ad_spend": {"$sum": "$ad_spend"},
                    # Get the first date in each month (for display purposes)
                    "date": {"$first": "$date"},
                }
            },
            # Sort by date and country
            {"$sort": {"_id.year": 1, "_id.month": 1, "_id.country": 1}},
        ]

        results = CampaignModel.aggregate(pipeline)

        # Transform the data to be suitable for Recharts
        months = []
        revenue_by_country = {country: [] for country in countries}
        ad_spend_by_country = {country: [] for country in countries}

        # Group by month first
        month_data = {}
        for item in results:
            date_key = (item["_id"]["year"], item["_id"]["month"])
            country = item["_id"]["country"]

            if date_key not in month_data:
                month_data[date_key] = {"date": item["date"], "countries": {}}

            month_data[date_key]["countries"][country] = {
                "revenue": item["revenue"],
                "ad_spend": item["ad_spend"],
            }

        # Sort months and fill in the data
        sorted_months = sorted(month_data.keys())
        for month_key in sorted_months:
            month_timestamp = month_data[month_key]["date"]
            months.append(month_timestamp)

            # For each country, get its data for this month
            for country in countries:
                if country in month_data[month_key]["countries"]:
                    country_data = month_data[month_key]["countries"][country]
                    revenue_by_country[country].append(country_data["revenue"])
                    ad_spend_by_country[country].append(country_data["ad_spend"])
                else:
                    # Country has no data for this month, add 0
                    revenue_by_country[country].append(0)
                    ad_spend_by_country[country].append(0)

        return {
            "months": months,
            "countries": countries,
            "revenue": revenue_by_country,
            "ad_spend": ad_spend_by_country,
        }

    except Exception as e:
        logger.error(f"Error getting monthly country data: {e}")
        raise


def get_latest_twelve_months_data() -> Dict:
    """
    Get the latest 12 months of aggregated data, including only date, revenue and ad spend.

    Returns:
        Dict: Dictionary containing:
            - items: List of dictionaries with date, revenue, and ad_spend for each month
    """
    try:
        # Aggregate the data by month
        pipeline = [
            # Group by month, calculating sums
            {
                "$group": {
                    "_id": {
                        # Extract year and month to group by month
                        "year": {"$year": {"$toDate": {"$multiply": ["$date", 1000]}}},
                        "month": {
                            "$month": {"$toDate": {"$multiply": ["$date", 1000]}}
                        },
                    },
                    "revenue": {"$sum": "$revenue"},
                    "ad_spend": {"$sum": "$ad_spend"},
                    "new_accounts": {"$sum": "$new_accounts"},
                    # Get the first date in each month (for display purposes)
                    "date": {"$first": "$date"},
                }
            },
            # Sort by date descending to get latest months first
            {"$sort": {"_id.year": -1, "_id.month": -1}},
            # Limit to 12 months
            {"$limit": 12},
            # Project to final format
            {
                "$project": {
                    "_id": 0,
                    "date": "$date",
                    "revenue": "$revenue",
                    "ad_spend": "$ad_spend",
                    "new_accounts": "$new_accounts",
                }
            },
            # Sort by date ascending for consistent display
            {"$sort": {"date": 1}},
        ]

        results = CampaignModel.aggregate(pipeline)

        # Convert to list and round numbers
        items = [
            {
                "date": item["date"],
                "revenue": round(item["revenue"], 3),
                "ad_spend": round(item["ad_spend"], 3),
                "new_accounts": round(item["new_accounts"]),
            }
            for item in results
        ]

        return {"items": items}

    except Exception as e:
        logger.error(f"Error getting latest twelve months data: {e}")
        raise
