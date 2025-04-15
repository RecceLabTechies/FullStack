import logging
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from typing_extensions import TypedDict

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
    # Build SQL WHERE conditions and parameters
    where_conditions = []
    params = []

    # List-based filters (channel, country, age_group, campaign_id)
    if filter_params.get("channels"):
        placeholders = ", ".join(["%s"] * len(filter_params["channels"]))
        where_conditions.append(f"channel IN ({placeholders})")
        params.extend(filter_params["channels"])

    if filter_params.get("countries"):
        placeholders = ", ".join(["%s"] * len(filter_params["countries"]))
        where_conditions.append(f"country IN ({placeholders})")
        params.extend(filter_params["countries"])

    if filter_params.get("age_groups"):
        placeholders = ", ".join(["%s"] * len(filter_params["age_groups"]))
        where_conditions.append(f"age_group IN ({placeholders})")
        params.extend(filter_params["age_groups"])

    if filter_params.get("campaign_ids"):
        placeholders = ", ".join(["%s"] * len(filter_params["campaign_ids"]))
        where_conditions.append(f"campaign_id IN ({placeholders})")
        params.extend(filter_params["campaign_ids"])

    # Numeric range filters
    for field in ["revenue", "ad_spend"]:
        min_field = f"min_{field}"
        max_field = f"max_{field}"

        if (
            filter_params.get(min_field) is not None
            or filter_params.get(max_field) is not None
        ):
            if filter_params.get(min_field) is not None:
                where_conditions.append(f"{field} >= %s")
                params.append(filter_params[min_field])

            if filter_params.get(max_field) is not None:
                where_conditions.append(f"{field} <= %s")
                params.append(filter_params[max_field])

    # Simple minimum filters
    for field in ["views", "leads"]:
        min_field = f"min_{field}"
        if filter_params.get(min_field) is not None:
            where_conditions.append(f"{field} >= %s")
            params.append(filter_params[min_field])

    # Date range filter
    if filter_params.get("from_date"):
        where_conditions.append("date >= %s")
        params.append(float(filter_params["from_date"]))

    if filter_params.get("to_date"):
        where_conditions.append("date <= %s")
        params.append(float(filter_params["to_date"]))

    # Build the final WHERE clause
    where_clause = " AND ".join(where_conditions) if where_conditions else ""

    # Set default pagination and sorting parameters
    page = filter_params.get("page", 1)
    page_size = filter_params.get("page_size", 20)
    sort_by = filter_params.get("sort_by", "date")
    sort_dir = filter_params.get("sort_dir", "desc")

    # Count total matching records for pagination info
    total_count = CampaignModel.count((where_clause, params) if where_clause else None)

    # Calculate pagination values
    offset = (page - 1) * page_size

    # Get paginated results with sorting
    results = CampaignModel.get_paginated(
        where_conditions=(where_clause, params) if where_clause else None,
        sort_by=sort_by,
        sort_dir=sort_dir,
        offset=offset,
        limit=page_size,
    )

    # Prepare pagination metadata
    total_pages = (total_count + page_size - 1) // page_size

    # Build response with pagination metadata
    response = {
        "items": results,
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
        # Extract month from Unix timestamp
        # Convert timestamp to month key while maintaining Unix timestamps
        timestamp = item["date"]
        # Convert Unix timestamp to datetime temporarily for month extraction only
        dt = datetime.fromtimestamp(timestamp)
        month_key = dt.strftime("%Y-%m")

        # Create Unix timestamp for first day of the month (for consistency)
        dt = datetime(dt.year, dt.month, 1)
        month_timestamp = int(dt.timestamp())

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

    # Get min/max for numeric fields using SQL aggregation
    numeric_ranges = {}
    for field in ["revenue", "ad_spend", "views", "leads"]:
        query = f"""
            SELECT 
                MIN({field}) as min,
                MAX({field}) as max,
                AVG({field}) as avg
            FROM campaign_performance
        """
        result = CampaignModel.aggregate(query)

        if result:
            numeric_ranges[field] = {
                "min": float(result[0]["min"]) if result[0]["min"] is not None else 0,
                "max": float(result[0]["max"]) if result[0]["max"] is not None else 0,
                "avg": float(result[0]["avg"]) if result[0]["avg"] is not None else 0,
            }
        else:
            numeric_ranges[field] = {"min": 0, "max": 0, "avg": 0}

    # Get date range
    date_range = {}
    date_query = """
        SELECT 
            MIN(date) as min_date,
            MAX(date) as max_date
        FROM campaign_performance
    """

    date_result = CampaignModel.aggregate(date_query)

    if date_result:
        date_range["min_date"] = (
            float(date_result[0]["min_date"])
            if date_result[0]["min_date"] is not None
            else None
        )
        date_range["max_date"] = (
            float(date_result[0]["max_date"])
            if date_result[0]["max_date"] is not None
            else None
        )
    else:
        date_range["min_date"] = None
        date_range["max_date"] = None

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

    from_: Optional[float]
    to: Optional[float]


class ChannelContributionResponse(TypedDict):
    """Type definition for channel contribution response."""

    metrics: List[str]
    channels: List[str]
    data: List[ChannelMetricValues]
    time_range: TimeRange
    error: Optional[str]


def get_channel_contribution_data(
    min_date=None, max_date=None
) -> ChannelContributionResponse:
    """
    Generate channel contribution data for various metrics.

    If min_date and max_date are provided, data will be filtered to that range.
    Otherwise, returns data for the latest 3 months.

    Args:
        min_date: Optional start date as Unix timestamp
        max_date: Optional end date as Unix timestamp

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

    # Filter by date range if provided
    if min_date and max_date:
        df = df[(df["date"] >= min_date) & (df["date"] <= max_date)]
    else:
        # Get the latest 3 months of data (default behavior)
        df = df.sort_values("datetime", ascending=False)
        unique_months = df["datetime"].dt.strftime("%Y-%m").unique()
        latest_months = sorted(unique_months[: min(3, len(unique_months))])

        # Filter data for the latest 3 months
        df["month"] = df["datetime"].dt.strftime("%Y-%m")
        df = df[df["month"].isin(latest_months)]

    if df.empty:
        return empty_response

    # Get the actual time range in the filtered data for response metadata
    if not df.empty:
        min_timestamp = (
            float(df["date"].min()) if not pd.isna(df["date"].min()) else None
        )
        max_timestamp = (
            float(df["date"].max()) if not pd.isna(df["date"].max()) else None
        )
    else:
        min_timestamp = None
        max_timestamp = None

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
        total = float(channel_metrics[metric].sum())

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
                channel_value = float(channel_data[metric].iloc[0])
                percentage = (channel_value / total) * 100
                metric_data["values"][channel] = round(float(percentage), 2)
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
            "from_": min_timestamp,
            "to": max_timestamp,
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


def get_cost_metrics_heatmap(min_date=None, max_date=None) -> HeatmapResponse:
    """
    Generate cost metrics heatmap data showing different cost metrics by channel.

    If min_date and max_date are provided, data will be filtered to that range.
    Otherwise, uses data from the latest 3 months similar to channel contribution data.

    Args:
        min_date: Optional start date as Unix timestamp
        max_date: Optional end date as Unix timestamp

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

    # Filter by date range if provided
    if min_date and max_date:
        df = df[(df["date"] >= min_date) & (df["date"] <= max_date)]
    else:
        # Get the latest 3 months of data (default behavior)
        df = df.sort_values("datetime", ascending=False)
        unique_months = df["datetime"].dt.strftime("%Y-%m").unique()
        latest_months = sorted(unique_months[: min(3, len(unique_months))])

        # Filter data for the latest 3 months
        df["month"] = df["datetime"].dt.strftime("%Y-%m")
        df = df[df["month"].isin(latest_months)]

    if df.empty:
        empty_response["error"] = "No data available for the specified date range"
        return empty_response

    # Get the actual time range in the filtered data for response metadata
    if not df.empty:
        min_timestamp = (
            float(df["date"].min()) if not pd.isna(df["date"].min()) else None
        )
        max_timestamp = (
            float(df["date"].max()) if not pd.isna(df["date"].max()) else None
        )
    else:
        min_timestamp = None
        max_timestamp = None

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
        max_value = float(metric_values.max())

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
            "from_": min_timestamp,
            "to": max_timestamp,
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
        query = """
            SELECT 
                EXTRACT(YEAR FROM to_timestamp(date)) AS year,
                EXTRACT(MONTH FROM to_timestamp(date)) AS month,
                age_group,
                SUM(revenue) AS revenue,
                SUM(ad_spend) AS ad_spend,
                MIN(date) AS date
            FROM campaign_performance
            GROUP BY year, month, age_group
            ORDER BY year, month, age_group
        """

        results = CampaignModel.aggregate(query)

        # Transform the data to be suitable for Recharts
        months = []
        revenue_by_age = {age_group: [] for age_group in age_groups}
        ad_spend_by_age = {age_group: [] for age_group in age_groups}

        # Group by month first
        month_data = {}
        for item in results:
            date_key = (int(item["year"]), int(item["month"]))
            age_group = item["age_group"]

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
        query = """
            SELECT 
                EXTRACT(YEAR FROM to_timestamp(date)) AS year,
                EXTRACT(MONTH FROM to_timestamp(date)) AS month,
                channel,
                SUM(revenue) AS revenue,
                SUM(ad_spend) AS ad_spend,
                MIN(date) AS date
            FROM campaign_performance
            GROUP BY year, month, channel
            ORDER BY year, month, channel
        """

        results = CampaignModel.aggregate(query)

        # Transform the data to be suitable for Recharts
        months = []
        revenue_by_channel = {channel: [] for channel in channels}
        ad_spend_by_channel = {channel: [] for channel in channels}

        # Group by month first
        month_data = {}
        for item in results:
            date_key = (int(item["year"]), int(item["month"]))
            channel = item["channel"]

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
        query = """
            SELECT 
                EXTRACT(YEAR FROM to_timestamp(date)) AS year,
                EXTRACT(MONTH FROM to_timestamp(date)) AS month,
                country,
                SUM(revenue) AS revenue,
                SUM(ad_spend) AS ad_spend,
                MIN(date) AS date
            FROM campaign_performance
            GROUP BY year, month, country
            ORDER BY year, month, country
        """

        results = CampaignModel.aggregate(query)

        # Transform the data to be suitable for Recharts
        months = []
        revenue_by_country = {country: [] for country in countries}
        ad_spend_by_country = {country: [] for country in countries}

        # Group by month first
        month_data = {}
        for item in results:
            date_key = (int(item["year"]), int(item["month"]))
            country = item["country"]

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
        # Aggregate the data by month using SQL
        query = """
            SELECT 
                MIN(date) as date,
                SUM(revenue) as revenue,
                SUM(ad_spend) as ad_spend,
                SUM(new_accounts) as new_accounts
            FROM campaign_performance
            GROUP BY EXTRACT(YEAR FROM to_timestamp(date)), EXTRACT(MONTH FROM to_timestamp(date))
            ORDER BY date DESC
            LIMIT 12
        """

        results = CampaignModel.aggregate(query)

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

        # Sort by date ascending
        items.sort(key=lambda x: x["date"])

        return {"items": items}

    except Exception as e:
        logger.error(f"Error getting latest twelve months data: {e}")
        raise


def get_campaign_date_range() -> Dict:
    """
    Get only the date range information for campaign data.

    Returns:
        Dict: Dictionary containing min_date and max_date
    """
    # Get date range using SQL
    date_query = """
        SELECT 
            MIN(date) as min_date,
            MAX(date) as max_date
        FROM campaign_performance
    """

    date_result = CampaignModel.aggregate(date_query)

    date_range = {}
    if date_result:
        date_range["min_date"] = (
            float(date_result[0]["min_date"])
            if date_result[0]["min_date"] is not None
            else None
        )
        date_range["max_date"] = (
            float(date_result[0]["max_date"])
            if date_result[0]["max_date"] is not None
            else None
        )
    else:
        date_range["min_date"] = None
        date_range["max_date"] = None

    return date_range
