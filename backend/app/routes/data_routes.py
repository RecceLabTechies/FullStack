import logging
from datetime import datetime
from functools import wraps

from flask import Blueprint, jsonify, make_response, request

from app.database.connection import get_campaign_performance_collection
from app.models.campaign import (
    filter_campaigns,
    get_age_group_roi,
    get_campaign_filter_options,
    get_channel_roi,
    get_monthly_performance_data,
    get_revenue_by_date,
    get_revenue_past_month,
    get_roi_past_month,
    update_monthly_data,
)
from app.utils.data_processing import (
    find_matching_collection,
    get_db_structure,
    process_csv_data,
)

# Create blueprint
data_bp = Blueprint("data_routes", __name__)
logger = logging.getLogger(__name__)


# ----------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------


def handle_exceptions(f):
    """Decorator to standardize exception handling for routes"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {e}")
            return jsonify({"error": str(e)}), 500

    return decorated_function


def format_response(data, status_code=200, headers=None):
    """Standardize API response format"""
    response = jsonify(data)

    if headers:
        for key, value in headers.items():
            response.headers.add(key, value)

    return response, status_code


def validate_campaign_filters(params):
    """
    Validate and sanitize campaign filter parameters.

    Args:
        params (dict): Dictionary of filter parameters

    Returns:
        tuple: (is_valid, error_message or validated_params)
    """
    errors = []

    # Validate page and page_size
    try:
        if params.get("page") is not None:
            page = int(params["page"])
            if page < 1:
                errors.append("Page number must be at least 1")
            params["page"] = page
    except ValueError:
        errors.append("Page number must be an integer")

    try:
        if params.get("page_size") is not None:
            page_size = int(params["page_size"])
            if page_size < 1:
                errors.append("Page size must be at least 1")
            # Cap page size at 100 for performance
            params["page_size"] = min(page_size, 100)
    except ValueError:
        errors.append("Page size must be an integer")

    # Validate numeric ranges
    numeric_fields = [
        "min_revenue",
        "max_revenue",
        "min_ad_spend",
        "max_ad_spend",
        "min_views",
        "min_leads",
    ]

    for field in numeric_fields:
        if params.get(field) is not None:
            try:
                params[field] = float(params[field])
                # Ensure min values are positive or zero
                if field.startswith("min_") and params[field] < 0:
                    errors.append(f"{field} must be a non-negative number")
            except ValueError:
                errors.append(f"{field} must be a valid number")

    # Check that mins are less than maxs
    if (
        params.get("min_revenue") is not None
        and params.get("max_revenue") is not None
        and params["min_revenue"] > params["max_revenue"]
    ):
        errors.append("min_revenue cannot be greater than max_revenue")

    if (
        params.get("min_ad_spend") is not None
        and params.get("max_ad_spend") is not None
        and params["min_ad_spend"] > params["max_ad_spend"]
    ):
        errors.append("min_ad_spend cannot be greater than max_ad_spend")

    # Validate date range
    date_fields = ["from_date", "to_date"]
    for field in date_fields:
        if params.get(field):
            try:
                # Try to parse the date to validate format
                date_value = params[field].split("T")[
                    0
                ]  # Handle potential ISO format with time
                datetime.fromisoformat(date_value)
            except ValueError:
                errors.append(f"{field} must be in ISO format (YYYY-MM-DD)")

    # Check from_date is before to_date
    if (
        params.get("from_date")
        and params.get("to_date")
        and params["from_date"] > params["to_date"]
    ):
        errors.append("from_date cannot be later than to_date")

    # Validate sort_dir
    if params.get("sort_dir") and params["sort_dir"] not in ["asc", "desc"]:
        errors.append("sort_dir must be either 'asc' or 'desc'")

    # Validate sort_by against allowed fields
    allowed_sort_fields = [
        "date",
        "channel",
        "country",
        "age_group",
        "ad_spend",
        "views",
        "leads",
        "revenue",
        "campaign_id",
    ]
    if params.get("sort_by") and params["sort_by"] not in allowed_sort_fields:
        errors.append(f"sort_by must be one of: {', '.join(allowed_sort_fields)}")

    if errors:
        return False, {"errors": errors}

    return True, params


# ----------------------------------------------------------------
# Database structure endpoints
# ----------------------------------------------------------------


@data_bp.route("/api/v1/database-structures", methods=["GET"])
@handle_exceptions
def get_database_structures():
    """
    Retrieve the structure of all databases and their collections.
    """
    structure = get_db_structure()
    return format_response(structure)


# ----------------------------------------------------------------
# Campaign data endpoints
# ----------------------------------------------------------------


@data_bp.route("/api/v1/campaigns/filter-options", methods=["GET"])
@handle_exceptions
def get_campaign_filters():
    """
    Get all available filter options for campaign data.

    Returns a comprehensive set of filter options:
    - Categorical options (countries, age groups, channels, campaign IDs)
    - Numeric range information (min/max values for revenue, ad spend, views, leads)
    - Date range information

    This provides everything needed for a frontend to build dynamic filter controls.
    """
    filter_options = get_campaign_filter_options()
    return format_response(filter_options)


@data_bp.route("/api/v1/campaigns", methods=["GET", "POST"])
@handle_exceptions
def get_filtered_campaigns():
    """
    Filter campaign data based on specified criteria with advanced filtering options.

    Supports both GET and POST methods for backward compatibility.

    GET Query parameters:
    - channels: Comma-separated list of marketing channels
    - countries: Comma-separated list of countries
    - age_groups: Comma-separated list of age groups
    - from_date: Start date in ISO format (YYYY-MM-DD)
    - to_date: End date in ISO format (YYYY-MM-DD)
    - campaign_ids: Comma-separated list of campaign IDs
    - min_revenue: Minimum revenue amount
    - max_revenue: Maximum revenue amount
    - min_ad_spend: Minimum ad spend amount
    - max_ad_spend: Maximum ad spend amount
    - min_views: Minimum views count
    - min_leads: Minimum leads count
    - sort_by: Field to sort by (default: date)
    - sort_dir: Sort direction (asc or desc, default: desc)
    - page: Page number (default: 1)
    - page_size: Number of results per page (default: 20, max: 100)

    POST accepts the same parameters as a JSON object.

    Returns paginated results that match the filter criteria.
    """
    try:
        # Extract parameters based on request method
        if request.method == "POST":
            # Legacy POST method support
            data = request.json or {}

            # Map legacy parameter names to new ones
            params = {
                "channels": data.get("channels", []),
                "countries": data.get("countries", []),
                "age_groups": data.get("ageGroups", []),  # Map ageGroups to age_groups
                "from_date": data.get("from"),  # Map from to from_date
                "to_date": data.get("to"),  # Map to to to_date
                "sort_by": data.get("sort_by", "date"),
                "sort_dir": data.get("sort_dir", "desc"),
                "page": data.get("page", 1),
                "page_size": data.get("page_size", 20),
            }

            # Add any additional filters that might be present
            for key in data:
                if key not in params and key not in ["from", "to", "ageGroups"]:
                    params[key] = data[key]

        else:  # GET method
            # Extract query parameters
            params = {
                "channels": (
                    request.args.get("channels", "").split(",")
                    if request.args.get("channels")
                    else []
                ),
                "countries": (
                    request.args.get("countries", "").split(",")
                    if request.args.get("countries")
                    else []
                ),
                "age_groups": (
                    request.args.get("age_groups", "").split(",")
                    if request.args.get("age_groups")
                    else []
                ),
                "campaign_ids": (
                    request.args.get("campaign_ids", "").split(",")
                    if request.args.get("campaign_ids")
                    else []
                ),
                "from_date": request.args.get("from_date"),
                "to_date": request.args.get("to_date"),
                "min_revenue": request.args.get("min_revenue"),
                "max_revenue": request.args.get("max_revenue"),
                "min_ad_spend": request.args.get("min_ad_spend"),
                "max_ad_spend": request.args.get("max_ad_spend"),
                "min_views": request.args.get("min_views"),
                "min_leads": request.args.get("min_leads"),
                "sort_by": request.args.get("sort_by", "date"),
                "sort_dir": request.args.get("sort_dir", "desc"),
                "page": request.args.get("page", "1"),
                "page_size": request.args.get("page_size", "20"),
            }

            # Clean empty strings from lists
            for list_param in ["channels", "countries", "age_groups", "campaign_ids"]:
                params[list_param] = [
                    item for item in params[list_param] if item.strip()
                ]

        # Validate parameters
        is_valid, result = validate_campaign_filters(params)
        if not is_valid:
            return format_response(result, 400)

        # Use validated parameters
        params = result

        # Call the model function to filter campaigns
        response = filter_campaigns(params)

        return format_response(response)

    except ValueError as e:
        logger.error(f"Invalid parameter value: {e}")
        return format_response({"error": f"Invalid parameter value: {str(e)}"}, 400)

    except Exception as e:
        logger.error(f"Error filtering campaigns: {e}")
        return format_response({"error": str(e)}, 500)


@data_bp.route("/api/v1/revenues", methods=["GET"])
@handle_exceptions
def get_revenue_data():
    """Get aggregated revenue data for charting"""
    data_summary = get_revenue_by_date()
    return format_response(data_summary)


@data_bp.route("/api/v1/chart/monthly-performance", methods=["GET"])
@handle_exceptions
def get_monthly_chart_data():
    """
    Get monthly revenue and ad spend data for charting.

    Optional query parameters:
    - from_date: Start date in ISO format (YYYY-MM-DD)
    - to_date: End date in ISO format (YYYY-MM-DD)
    - channels: Comma-separated list of marketing channels
    - countries: Comma-separated list of countries
    - age_groups: Comma-separated list of age groups

    Returns:
    {
        "months": ["2023-01", "2023-02", ...],
        "revenue": [12345, 23456, ...],
        "ad_spend": [5000, 6000, ...],
        "roi": [2.47, 3.91, ...]
    }
    """
    try:
        # Get filter parameters
        filters = {}

        # Parse date range
        if request.args.get("from_date"):
            filters["from_date"] = request.args.get("from_date")

        if request.args.get("to_date"):
            filters["to_date"] = request.args.get("to_date")

        # Parse categorical filters
        for param in ["channels", "countries", "age_groups"]:
            if request.args.get(param):
                filters[param] = [
                    item for item in request.args.get(param).split(",") if item.strip()
                ]

        # Call model function to get the data
        data = get_monthly_performance_data(filters)
        return format_response(data)

    except ValueError as e:
        logger.error(f"Invalid parameter: {e}")
        return format_response({"error": str(e)}, 400)
    except Exception as e:
        logger.error(f"Error getting monthly chart data: {e}")
        return format_response({"error": str(e)}, 500)


@data_bp.route("/api/v1/chart/update-monthly-data", methods=["POST"])
@handle_exceptions
def update_monthly_chart_data():
    """
    Update revenue and/or ad spend data for specific months.

    Expected JSON payload:
    {
        "updates": [
            {
                "month": "YYYY-MM",
                "revenue": optional_numeric_value,
                "ad_spend": optional_numeric_value
            },
            ...
        ]
    }

    At least one of revenue or ad_spend must be provided for each update.
    Returns the updated monthly chart data.
    """
    try:
        data = request.json
        if not data or "updates" not in data:
            return format_response({"error": "Missing updates data"}, 400)

        # Call model function to update the data
        updated_data = update_monthly_data(data["updates"])

        return format_response(
            {"message": "Monthly data updated successfully", **updated_data}
        )

    except ValueError as e:
        logger.error(f"Invalid update data: {e}")
        return format_response({"error": str(e)}, 400)
    except Exception as e:
        logger.error(f"Error updating monthly chart data: {e}")
        return format_response({"error": str(e)}, 500)


@data_bp.route("/api/v1/channel-roi", methods=["GET"])
@handle_exceptions
def get_channel_roi_data():
    """Get revenue per dollar spent for each marketing channel"""
    data = get_channel_roi()
    return format_response(data)


@data_bp.route("/api/v1/age-group-roi", methods=["GET"])
@handle_exceptions
def get_age_group_roi_data():
    """Get revenue per dollar spent for each age group"""
    data = get_age_group_roi()
    return format_response(data)


@data_bp.route("/api/v1/revenue-past-month", methods=["GET"])
@handle_exceptions
def get_revenue_past_month_data():
    """Get total revenue for the past month"""
    revenue = get_revenue_past_month()
    return format_response({"revenue": revenue})


@data_bp.route("/api/v1/roi-past-month", methods=["GET"])
@handle_exceptions
def get_roi_past_month_data():
    """Get ROI (revenue per dollar spent) for the past month"""
    roi = get_roi_past_month()
    return format_response({"roi": roi})


# ----------------------------------------------------------------
# CSV import endpoints
# ----------------------------------------------------------------


@data_bp.route("/api/v1/csv-imports", methods=["POST", "OPTIONS"])
def handle_csv_import():
    """
    Handle CSV file uploads and import data into MongoDB.
    """
    # Handle CORS preflight request
    if request.method == "OPTIONS":
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "*")
        response.headers.add("Access-Control-Allow-Methods", "POST")
        return response

    try:
        # Validate file presence in request
        if "file" not in request.files:
            return format_response({"error": "No file provided"}, 400)

        file = request.files["file"]
        if file.filename == "":
            return format_response({"error": "No file selected"}, 400)

        if not file.filename.endswith(".csv"):
            return format_response({"error": "File must be a CSV"}, 400)

        # Process the CSV file
        try:
            # Process CSV data
            records, is_campaign_data, default_collection_name = process_csv_data(file)

            # Find matching collection for data
            matching_collection, collection_name, found_match = (
                find_matching_collection(
                    records, is_campaign_data, default_collection_name
                )
            )

            # Check if we have any valid records to insert
            if not records:
                logger.error("No valid records found after validation")
                return format_response(
                    {"error": "No valid records found after validation"}, 400
                )

            # Insert all records into MongoDB
            result = matching_collection.insert_many(records)
            logger.info(
                f"Successfully inserted {len(result.inserted_ids)} records into {collection_name}"
            )

            # Determine operation type for response message
            operation = "appended to existing" if found_match else "uploaded to new"

            # Prepare and send response
            return format_response(
                {
                    "message": f"CSV {operation} collection successfully",
                    "count": len(result.inserted_ids),
                    "collection": collection_name,
                },
                headers={"Access-Control-Allow-Origin": "*"},
            )

        except UnicodeDecodeError:
            logger.error("Invalid CSV file encoding")
            return format_response(
                {"error": "Invalid CSV file encoding. Please use UTF-8"}, 400
            )
        except ValueError as e:
            logger.error(f"CSV validation error: {e}")
            return format_response({"error": str(e)}, 400)

    except Exception as e:
        logger.error(f"Error uploading CSV: {e}")
        return format_response({"error": str(e)}, 500)


# ----------------------------------------------------------------
# Utility endpoints
# ----------------------------------------------------------------


@data_bp.route("/api/v1/date-types", methods=["GET"])
@handle_exceptions
def inspect_date_type():
    """
    Utility endpoint to inspect the date field data type in the campaign collection.
    """
    collection = get_campaign_performance_collection()

    # Fetch one sample document
    sample = collection.find_one({}, {"date": 1, "_id": 0})

    if not sample or "date" not in sample:
        logger.warning("No date field found in sample document")
        return format_response({"message": "No date field found in sample."}, 404)

    date_value = sample["date"]
    return format_response({"value": date_value, "type": str(type(date_value))})


# yuting code


@data_bp.route("/api/get-cost-heatmap-data", methods=["GET"])
def get_cost_heatmap_data():
    try:
        collection = db["final_mock_data"]
        data = list(collection.find({}, {"_id": 0}))  # Fetch data, excluding _id

        if not data:
            return jsonify({"error": "No data found"}), 404

        df = pd.DataFrame(data)

        # Filter for Singapore and campaign_id "January_2022_1"
        # Filter for channels with no missing values
        df = df[
            (df["country"] == "Singapore") & (df["campaign_id"] == "January_2022_1")
        ]
        df = df[
            df["channel"].isin(
                [
                    "LinkedIn",
                    "Facebook ads",
                    "Google banner ads",
                    "Influencer",
                    "Instagram Ads",
                    "TikTok ads",
                    "Sponsored search ads",
                ]
            )
        ]

        if df.empty:
            return jsonify({"error": "No data found for Singapore"}), 404

        # Convert numeric columns
        numeric_columns = ["ad_spend", "leads", "new_accounts", "views"]
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # Drop rows with missing values
        df.dropna(inplace=True)

        if df.empty:
            return jsonify({"error": "No valid data after dropping NaNs"}), 404

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
        df_grouped["costPerLead"] = df_grouped["ad_spend"] / df_grouped[
            "leads"
        ].replace(0, 1e-6)
        df_grouped["costPerView"] = df_grouped["ad_spend"] / df_grouped[
            "views"
        ].replace(0, 1e-6)
        df_grouped["costPerAccount"] = df_grouped["ad_spend"] / df_grouped[
            "new_accounts"
        ].replace(0, 1e-6)

        # Round values
        df_grouped = df_grouped.round(4)

        # Prepare data for response
        data_summary = df_grouped[
            ["channel", "costPerLead", "costPerView", "costPerAccount"]
        ].to_dict(orient="records")

        return jsonify(data_summary)

    except Exception as e:
        print(f"Error retrieving cost heatmap data: {e}")
        return jsonify({"error": str(e)}), 500
