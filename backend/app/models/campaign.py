import logging
from datetime import datetime, timedelta
from typing import Dict, List, cast

import pandas as pd

from app.database.connection import get_campaign_performance_collection
from app.models.data_types import CampaignData

logger = logging.getLogger(__name__)


def get_channel_roi() -> List[Dict[str, float]]:
    """
    Get revenue per dollar spent for each marketing channel.

    Returns:
        List[Dict[str, float]]: List of dictionaries with channel and ROI (revenue per dollar spent)
    """
    collection = get_campaign_performance_collection()
    data = list(collection.find({}, {"_id": 0}))

    if not data:
        return []

    validated_data: List[Dict[str, float]] = []
    for item in data:
        try:
            campaign_obj = CampaignData(**item)
            validated_data.append(
                {
                    "channel": campaign_obj.channel,
                    "revenue": campaign_obj.revenue,
                    "ad_spend": campaign_obj.ad_spend,
                }
            )
        except Exception as e:
            logger.warning(f"Error converting campaign data: {e}")

    if not validated_data:
        df = pd.DataFrame(data)
    else:
        df = pd.DataFrame(validated_data)

    # Calculate total revenue and spend by channel
    df["revenue"] = df["revenue"].astype(float)
    df["ad_spend"] = df["ad_spend"].astype(float)

    channel_summary = df.groupby("channel", as_index=False).agg(
        {"revenue": "sum", "ad_spend": "sum"}
    )

    # Calculate ROI (revenue per dollar spent)
    channel_summary["roi"] = channel_summary["revenue"] / channel_summary["ad_spend"]

    # Select only channel and roi columns
    result = channel_summary[["channel", "roi"]]

    return cast(List[Dict[str, float]], result.to_dict(orient="records"))


def get_age_group_roi() -> List[Dict[str, float]]:
    """
    Get revenue per dollar spent for each age group.
    Age groups: 18-24, 25-34, 35-44, 45-54, 55+

    Returns:
        List[Dict[str, float]]: List of dictionaries with age_group and ROI (revenue per dollar spent)
    """
    collection = get_campaign_performance_collection()
    data = list(collection.find({}, {"_id": 0}))

    if not data:
        return []

    # Convert raw data to CampaignData objects for proper typing
    validated_data: List[Dict[str, float]] = []
    for item in data:
        try:
            campaign_obj = CampaignData(**item)
            validated_data.append(
                {
                    "age_group": campaign_obj.age_group,
                    "revenue": campaign_obj.revenue,
                    "ad_spend": campaign_obj.ad_spend,
                }
            )
        except Exception as e:
            logger.warning(f"Error converting campaign data: {e}")

    if not validated_data:
        df = pd.DataFrame(data)
    else:
        df = pd.DataFrame(validated_data)

    # Calculate total revenue and spend by age group
    df["revenue"] = df["revenue"].astype(float)
    df["ad_spend"] = df["ad_spend"].astype(float)

    age_group_summary = df.groupby("age_group", as_index=False).agg(
        {"revenue": "sum", "ad_spend": "sum"}
    )

    # Calculate ROI (revenue per dollar spent)
    age_group_summary["roi"] = (
        age_group_summary["revenue"] / age_group_summary["ad_spend"]
    )

    # Select only age_group and roi columns
    result = age_group_summary[["age_group", "roi"]]

    # Ensure we only include the specified age groups in the correct order
    age_groups = ["18-24", "25-34", "35-44", "45-54", "55+"]
    result = result[result["age_group"].isin(age_groups)]

    # Sort by the specified age group order
    result["sort_order"] = result["age_group"].apply(
        lambda x: age_groups.index(x) if x in age_groups else 999
    )
    result = result.sort_values("sort_order")
    result = result.drop("sort_order", axis=1)

    return cast(List[Dict[str, float]], result.to_dict(orient="records"))


def get_revenue_past_month() -> float:
    """
    Get total revenue for the past month.
    Uses the full previous calendar month (e.g., if current month is January, returns December data).

    Returns:
        float: Total revenue for the past month
    """
    collection = get_campaign_performance_collection()

    # Calculate first and last day of previous month
    today = datetime.now()
    first_day_current_month = datetime(today.year, today.month, 1)
    last_day_prev_month = first_day_current_month - timedelta(days=1)
    first_day_prev_month = datetime(
        last_day_prev_month.year, last_day_prev_month.month, 1
    )

    # Query for data from the previous month
    query = {"date": {"$gte": first_day_prev_month, "$lte": last_day_prev_month}}
    data = list(collection.find(query, {"_id": 0}))

    if not data:
        return 0.0

    # Convert raw data to CampaignData objects for proper typing
    validated_data: List[Dict[str, float]] = []
    for item in data:
        try:
            campaign_obj = CampaignData(**item)
            validated_data.append({"revenue": campaign_obj.revenue})
        except Exception as e:
            logger.warning(f"Error converting campaign data: {e}")

    if not validated_data:
        return 0.0

    df = pd.DataFrame(validated_data)
    df["revenue"] = df["revenue"].astype(float)

    # Calculate total revenue
    total_revenue = df["revenue"].sum()

    return float(total_revenue)


def get_roi_past_month() -> float:
    """
    Get ROI (revenue per dollar spent) for the past month.
    Uses the full previous calendar month (e.g., if current month is January, returns December data).

    Returns:
        float: ROI for the past month (revenue / ad_spend)
    """
    collection = get_campaign_performance_collection()

    # Calculate first and last day of previous month
    today = datetime.now()
    first_day_current_month = datetime(today.year, today.month, 1)
    last_day_prev_month = first_day_current_month - timedelta(days=1)
    first_day_prev_month = datetime(
        last_day_prev_month.year, last_day_prev_month.month, 1
    )

    # Query for data from the previous month
    query = {"date": {"$gte": first_day_prev_month, "$lte": last_day_prev_month}}
    data = list(collection.find(query, {"_id": 0}))

    if not data:
        return 0.0

    # Convert raw data to CampaignData objects for proper typing
    validated_data: List[Dict[str, float]] = []
    for item in data:
        try:
            campaign_obj = CampaignData(**item)
            validated_data.append(
                {"revenue": campaign_obj.revenue, "ad_spend": campaign_obj.ad_spend}
            )
        except Exception as e:
            logger.warning(f"Error converting campaign data: {e}")

    if not validated_data:
        return 0.0

    df = pd.DataFrame(validated_data)
    df["revenue"] = df["revenue"].astype(float)
    df["ad_spend"] = df["ad_spend"].astype(float)

    # Calculate total revenue and ad spend
    total_revenue = df["revenue"].sum()
    total_ad_spend = df["ad_spend"].sum()

    # Avoid division by zero
    if total_ad_spend == 0:
        return 0.0

    # Calculate ROI
    roi = total_revenue / total_ad_spend

    return float(roi)


def filter_campaigns(filter_params: Dict) -> Dict:
    """
    Filter campaigns based on specified criteria with advanced filtering options.

    Args:
        filter_params (Dict): Dictionary containing filter parameters:
            - channels: List of marketing channels
            - countries: List of countries
            - age_groups: List of age groups
            - campaign_ids: List of campaign IDs
            - from_date: Start date (datetime or ISO string)
            - to_date: End date (datetime or ISO string)
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
    query = {}

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
            from_date = filter_params["from_date"]
            # Convert string to datetime if needed
            if isinstance(from_date, str):
                from_date = datetime.fromisoformat(from_date.split("T")[0])
            query["date"]["$gte"] = from_date

        if filter_params.get("to_date"):
            to_date = filter_params["to_date"]
            # Convert string to datetime if needed
            if isinstance(to_date, str):
                to_date = datetime.fromisoformat(to_date.split("T")[0])
                # Include the entire day
                to_date = datetime(to_date.year, to_date.month, to_date.day, 23, 59, 59)
            query["date"]["$lte"] = to_date

    # Get the collection
    collection = get_campaign_performance_collection()

    # Set default pagination and sorting parameters
    page = filter_params.get("page", 1)
    page_size = filter_params.get("page_size", 20)
    sort_by = filter_params.get("sort_by", "date")
    sort_dir = filter_params.get("sort_dir", "desc")

    # Count total matching documents for pagination info
    total_count = collection.count_documents(query)

    # Calculate pagination values
    skip = (page - 1) * page_size

    # Determine sort direction (1 for ascending, -1 for descending)
    sort_direction = 1 if sort_dir.lower() == "asc" else -1

    # Get paginated results with sorting
    results = list(
        collection.find(query, {"_id": 0})
        .sort(sort_by, sort_direction)
        .skip(skip)
        .limit(page_size)
    )

    # Format dates to ISO strings for JSON serialization
    for result in results:
        if isinstance(result.get("date"), datetime):
            result["date"] = result["date"].isoformat()

    # Prepare pagination metadata
    total_pages = (total_count + page_size - 1) // page_size

    # Build response with pagination metadata
    response = {
        "data": results,
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
    collection = get_campaign_performance_collection()

    # Get distinct values for categorical fields
    countries = sorted(collection.distinct("country"))
    age_groups = collection.distinct("age_group")
    channels = sorted(collection.distinct("channel"))
    campaign_ids = sorted(collection.distinct("campaign_id"))

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
        result = list(
            collection.aggregate(
                [
                    {
                        "$group": {
                            "_id": None,
                            "min": {"$min": f"${field}"},
                            "max": {"$max": f"${field}"},
                            "avg": {"$avg": f"${field}"},
                        }
                    }
                ]
            )
        )

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
    date_result = list(
        collection.aggregate(
            [
                {
                    "$group": {
                        "_id": None,
                        "min_date": {"$min": "$date"},
                        "max_date": {"$max": "$date"},
                    }
                }
            ]
        )
    )

    if date_result:
        min_date = date_result[0]["min_date"]
        max_date = date_result[0]["max_date"]

        # Convert to ISO string format
        if isinstance(min_date, datetime):
            date_range["min_date"] = min_date.isoformat()
        if isinstance(max_date, datetime):
            date_range["max_date"] = max_date.isoformat()

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


def get_revenue_by_date() -> Dict:
    """
    Get aggregated revenue and ad spend data by date for charting.

    Returns:
        Dict: Dictionary containing date-based revenue and ad spend data
    """
    collection = get_campaign_performance_collection()

    # Aggregate data by date
    pipeline = [
        {
            "$group": {
                "_id": "$date",
                "revenue": {"$sum": "$revenue"},
                "ad_spend": {"$sum": "$ad_spend"},
            }
        },
        {"$sort": {"_id": 1}},  # Sort by date ascending
    ]

    results = list(collection.aggregate(pipeline))

    # Format the results
    dates = []
    revenues = []
    ad_spends = []

    for result in results:
        date = result["_id"]
        # Convert date to ISO format if it's a datetime
        if isinstance(date, datetime):
            date = date.isoformat().split("T")[0]  # Just the date part

        dates.append(date)
        revenues.append(round(result["revenue"], 2))
        ad_spends.append(round(result["ad_spend"], 2))

    return {"dates": dates, "revenues": revenues, "ad_spends": ad_spends}


def get_monthly_performance_data(filters: Dict = None) -> Dict:
    """
    Get monthly revenue and ad spend data for charting.

    Args:
        filters (Dict, optional): Dictionary containing filter parameters:
            - from_date: Start date (datetime or ISO string)
            - to_date: End date (datetime or ISO string)
            - channels: List of marketing channels
            - countries: List of countries
            - age_groups: List of age groups

    Returns:
        Dict: Dictionary containing arrays for months, revenue, ad_spend, and ROI
    """
    # Initialize filters if None
    if filters is None:
        filters = {}

    # Get campaign collection
    collection = get_campaign_performance_collection()

    # Build query based on filters
    query = {}

    # Date range filters
    if "from_date" in filters:
        from_date = filters["from_date"]
        # Convert string to datetime if needed
        if isinstance(from_date, str):
            from_date = datetime.fromisoformat(from_date.split("T")[0])
        query.setdefault("date", {})["$gte"] = from_date

    if "to_date" in filters:
        to_date = filters["to_date"]
        # Convert string to datetime if needed
        if isinstance(to_date, str):
            to_date = datetime.fromisoformat(to_date.split("T")[0])
        query.setdefault("date", {})["$lte"] = to_date

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
            "$group": {
                "_id": {"year": {"$year": "$date"}, "month": {"$month": "$date"}},
                "revenue": {"$sum": "$revenue"},
                "ad_spend": {"$sum": "$ad_spend"},
            }
        },
        {"$sort": {"_id.year": 1, "_id.month": 1}},
    ]

    results = list(collection.aggregate(pipeline))

    # Format response
    months = []
    revenue = []
    ad_spend = []
    roi = []

    for item in results:
        year = item["_id"]["year"]
        month = item["_id"]["month"]
        month_str = f"{year}-{month:02d}"

        months.append(month_str)
        revenue.append(round(item["revenue"], 2))
        ad_spend.append(round(item["ad_spend"], 2))

        # Calculate ROI (return on investment)
        if item["ad_spend"] > 0:
            roi.append(round(item["revenue"] / item["ad_spend"], 2))
        else:
            roi.append(0)

    return {"months": months, "revenue": revenue, "ad_spend": ad_spend, "roi": roi}


def update_monthly_data(updates: List[Dict]) -> Dict:
    """
    Update revenue and/or ad spend data for specific months.

    Args:
        updates (List[Dict]): List of updates, each containing:
            - month (str): Month in YYYY-MM format
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

        # Parse month string to get start and end dates
        month_date = datetime.strptime(update["month"], "%Y-%m")
        start_date = month_date.replace(day=1)

        # Calculate end date (first day of next month)
        if month_date.month == 12:
            end_date = datetime(month_date.year + 1, 1, 1)
        else:
            end_date = datetime(month_date.year, month_date.month + 1, 1)

        # Find all campaigns in this month
        campaigns = list(
            collection.find({"date": {"$gte": start_date, "$lt": end_date}})
        )

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
                    collection.update_one(
                        {"_id": campaign["_id"]}, {"$set": {"revenue": new_value}}
                    )
            else:
                # Apply proportional update
                scale_factor = update["revenue"] / current_total
                for campaign in campaigns:
                    new_revenue = campaign.get("revenue", 0) * scale_factor
                    collection.update_one(
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
                    collection.update_one(
                        {"_id": campaign["_id"]}, {"$set": {"ad_spend": new_value}}
                    )
            else:
                # Apply proportional update
                scale_factor = update["ad_spend"] / current_total
                for campaign in campaigns:
                    new_ad_spend = campaign.get("ad_spend", 0) * scale_factor
                    collection.update_one(
                        {"_id": campaign["_id"]}, {"$set": {"ad_spend": new_ad_spend}}
                    )

    # Return updated chart data
    return get_monthly_performance_data()
