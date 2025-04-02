import logging
from functools import wraps
from flask import Blueprint, jsonify, make_response, request
from marshmallow import (
    Schema,
    fields,
    ValidationError,
    validate,
    EXCLUDE,
    validates,
)
from app.services.campaign_service import (
    filter_campaigns,
    get_campaign_filter_options,
    get_monthly_aggregated_data,
    get_channel_contribution_data,
    get_cost_metrics_heatmap,
    get_latest_month_roi,
    get_latest_month_revenue,
    get_monthly_age_data,
    get_monthly_channel_data,
    get_monthly_country_data,
    get_latest_twelve_months_data,
)
from app.utils.data_processing import (
    find_matching_collection,
    get_db_structure,
    process_csv_data,
)
from app.data_types import CampaignData

# Create blueprint
data_bp = Blueprint("data_routes", __name__)
logger = logging.getLogger(__name__)


# ----------------------------------------------------------------
# Schema definitions
# ----------------------------------------------------------------


class CampaignFilterSchema(Schema):
    """Schema for validating campaign filter parameters"""

    # List filters
    channels = fields.List(fields.String(), required=False)
    countries = fields.List(fields.String(), required=False)
    age_groups = fields.List(fields.String(), required=False)
    campaign_ids = fields.List(fields.String(), required=False)

    # Date filters (using float for Unix timestamps)
    from_date = fields.Float(required=False, allow_none=True)
    to_date = fields.Float(required=False, allow_none=True)

    # Numeric range filters
    min_revenue = fields.Float(required=False, validate=validate.Range(min=0))
    max_revenue = fields.Float(required=False)
    min_ad_spend = fields.Float(required=False, validate=validate.Range(min=0))
    max_ad_spend = fields.Float(required=False)
    min_views = fields.Float(required=False, validate=validate.Range(min=0))
    min_leads = fields.Float(required=False, validate=validate.Range(min=0))

    # Pagination
    page = fields.Integer(
        required=False, validate=validate.Range(min=1), load_default=1
    )
    page_size = fields.Integer(
        required=False, validate=validate.Range(min=1, max=100), load_default=20
    )

    # Sorting
    sort_by = fields.String(
        required=False,
        validate=validate.OneOf(
            [
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
        ),
        load_default="date",
    )
    sort_dir = fields.String(
        required=False, validate=validate.OneOf(["asc", "desc"]), load_default="desc"
    )

    class Meta:
        unknown = EXCLUDE

    @validates("to_date")
    def validate_date_range(self, value, **kwargs):
        """Validate that to_date is not before from_date"""
        from_date = self.context.get("from_date")
        if from_date and value and from_date > value:
            raise ValidationError("from_date cannot be later than to_date")


class MonthlyUpdateSchema(Schema):
    """Schema for validating monthly data updates"""

    month = fields.Float(required=True)  # Unix timestamp
    revenue = fields.Float(required=False)
    ad_spend = fields.Float(required=False)

    class Meta:
        unknown = EXCLUDE


class MonthlyUpdateListSchema(Schema):
    """Schema for validating a list of monthly data updates"""

    updates = fields.List(
        fields.Nested(MonthlyUpdateSchema),
        required=True,
        validate=validate.Length(min=1),
    )

    class Meta:
        unknown = EXCLUDE


class CampaignDataSchema(Schema):
    """Schema for validating complete campaign data, aligned with CampaignData class"""

    date = fields.Integer(required=True)
    campaign_id = fields.String(required=True)
    channel = fields.String(required=True)
    age_group = fields.String(required=True)
    ad_spend = fields.Float(required=True)
    views = fields.Float(required=True)
    leads = fields.Float(required=True)
    new_accounts = fields.Float(required=True)
    country = fields.String(required=True)
    revenue = fields.Float(required=True)

    class Meta:
        unknown = EXCLUDE

    def convert_to_campaign_data(self, data):
        """Convert validated data to CampaignData object"""
        return CampaignData(**data)


class MonthlyPerformanceFilterSchema(Schema):
    """Schema for validating monthly chart data filter parameters"""

    # Date filters (using float for Unix timestamps)
    from_date = fields.Float(required=False, allow_none=True)
    to_date = fields.Float(required=False, allow_none=True)

    # List filters
    channels = fields.List(fields.String(), required=False)
    countries = fields.List(fields.String(), required=False)
    age_groups = fields.List(fields.String(), required=False)

    class Meta:
        unknown = EXCLUDE

    @validates("to_date")
    def validate_date_range(self, value, **kwargs):
        """Validate that to_date is not before from_date"""
        from_date = self.context.get("from_date")
        if from_date and value and from_date > value:
            raise ValidationError("from_date cannot be later than to_date")


class CostHeatmapSchema(Schema):
    """Schema for validating cost heatmap parameters"""

    country = fields.String(required=False, load_default="Singapore")
    campaign_id = fields.String(required=False, load_default="January_2022_1")
    channels = fields.List(fields.String(), required=False)

    class Meta:
        unknown = EXCLUDE


# ----------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------


def handle_exceptions(f):
    """Decorator to standardize exception handling for routes"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValidationError as ve:
            logger.error(f"Validation error in {f.__name__}: {ve}")
            return validation_error_response(ve.messages)
        except ValueError as e:
            logger.error(f"Value error in {f.__name__}: {e}")
            return error_response(400, str(e), "invalid_value")
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {e}")
            return error_response(500, str(e), "server_error")

    return decorated_function


def error_response(status_code, message, error_type=None):
    """Helper function to create standardized error responses"""
    response = {"error": {"status": status_code, "message": message}}
    if error_type:
        if isinstance(error_type, dict) and "type" in error_type:
            # Handle nested error types with details
            response["error"].update(error_type)
        else:
            response["error"]["type"] = error_type
    return jsonify(response), status_code


def validation_error_response(validation_errors):
    """Formats validation errors into standard error response"""
    return error_response(
        400,
        "Validation error",
        {"type": "validation_error", "details": validation_errors},
    )


def format_response(data, status_code=200, headers=None):
    """Standardize API response format for success responses"""
    # Wrap data in a standard response envelope
    response_body = {"success": True, "data": data, "status": status_code}

    response = jsonify(response_body)

    if headers:
        for key, value in headers.items():
            response.headers.add(key, value)

    return response, status_code


# Helper for parsing list query parameters
def parse_list_param(param_value):
    """Parse a comma-separated query parameter into a list, filtering empty values"""
    if not param_value:
        return []
    return [item for item in param_value.split(",") if item.strip()]


def validate_request_data(data, schema_class, context=None, convert_func=None):
    """
    Helper to validate request data using a schema and optionally convert to domain objects.

    Args:
        data: The data to validate (dict or list)
        schema_class: The schema class to use for validation
        context: Optional context to pass to the schema
        convert_func: Optional function to convert validated data to domain objects

    Returns:
        Validated and possibly converted data

    Raises:
        ValidationError: If validation fails
    """
    schema = schema_class(context=context or {})
    validated_data = schema.load(data)

    if convert_func and callable(convert_func):
        return convert_func(validated_data)

    return validated_data


def validate_and_convert_list(items, schema_class, convert_method_name=None):
    """
    Helper to validate and convert a list of items.

    Args:
        items: List of items to validate and convert
        schema_class: Schema class to use for validation
        convert_method_name: Name of the schema method to use for conversion

    Returns:
        List of validated and converted items
    """
    schema = schema_class()
    result = []

    for item in items:
        try:
            validated_item = schema.load(item)

            # Convert if a conversion method is specified
            if convert_method_name and hasattr(schema, convert_method_name):
                convert_method = getattr(schema, convert_method_name)
                converted_item = convert_method(validated_item)
                result.append(converted_item)
            else:
                result.append(validated_item)

        except ValidationError as err:
            logger.warning(f"Skipping invalid item: {err.messages}")
            continue

    return result


# ----------------------------------------------------------------
# Database structure endpoints
# ----------------------------------------------------------------


@data_bp.route("/api/v1/database/structure", methods=["GET"])
@handle_exceptions
def get_database_structures_data():
    """
    Retrieve the structure of all databases and their collections.

    Returns:
        JSON object containing database and collection structure
    """
    structure = get_db_structure()
    return format_response(structure)


# ----------------------------------------------------------------
# Campaign data endpoints
# ----------------------------------------------------------------


@data_bp.route("/api/v1/campaigns/filter-options", methods=["GET"])
@handle_exceptions
def get_campaign_filters_data():
    """
    Get all available filter options for campaign data.

    Returns a comprehensive set of filter options:
    - Categorical options (countries, age groups, channels, campaign IDs)
    - Numeric range information (min/max values for revenue, ad spend, views, leads)
    - Date range information

    Returns:
        JSON object containing filter options
    """
    filter_options = get_campaign_filter_options()
    return format_response(filter_options)


@data_bp.route("/api/v1/campaigns", methods=["POST"])
@handle_exceptions
def get_campaigns_data():
    """
    Filter campaign data based on specified criteria with advanced filtering options.

    All parameters are optional. When no parameters are provided, all records are returned.
    The API supports incremental filtering - you can specify any combination of filters.



    For POST requests, use JSON body with parameters:
    - channels: List of marketing channels
    - countries: List of countries
    - age_groups: List of age groups
    - from_date: Start date as Unix timestamp
    - to_date: End date as Unix timestamp
    - campaign_ids: List of campaign IDs
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

    Returns:
        JSON object containing paginated campaign data and metadata
    """

    # Extract parameters from request JSON body
    request_data = request.get_json() or {}

    params = {
        "channels": request_data.get("channels", []),
        "countries": request_data.get("countries", []),
        "age_groups": request_data.get("age_groups", []),
        "campaign_ids": request_data.get("campaign_ids", []),
        "from_date": request_data.get("from_date"),
        "to_date": request_data.get("to_date"),
        "min_revenue": request_data.get("min_revenue"),
        "max_revenue": request_data.get("max_revenue"),
        "min_ad_spend": request_data.get("min_ad_spend"),
        "max_ad_spend": request_data.get("max_ad_spend"),
        "min_views": request_data.get("min_views"),
        "min_leads": request_data.get("min_leads"),
        "sort_by": request_data.get("sort_by", "date"),
        "sort_dir": request_data.get("sort_dir", "desc"),
        "page": request_data.get("page", 1),
        "page_size": request_data.get("page_size", 20),
    }

    # Create validation context for date range validation
    context = {}
    if "from_date" in params and params["from_date"]:
        context["from_date"] = params["from_date"]

    # Validate parameters using the helper
    validated_params = validate_request_data(params, CampaignFilterSchema, context)

    # Call the model function to filter campaigns
    response = filter_campaigns(validated_params)

    # Convert campaign data items to domain objects before sending response
    if "items" in response and response["items"]:
        response["items"] = validate_and_convert_list(
            response["items"], CampaignDataSchema, "convert_to_campaign_data"
        )

        # Convert domain objects to dict for serialization if they're not already
        response["items"] = [
            item.__dict__ if hasattr(item, "__dict__") else item
            for item in response["items"]
        ]

    return format_response(response)


@data_bp.route("/api/v1/campaigns/monthly-aggregated", methods=["POST"])
@handle_exceptions
def get_monthly_aggregated_data_route():
    """
    Get monthly aggregated revenue and ad spend data with full campaign filtering support.

    Accepts the same JSON body parameters as /api/v1/campaigns:
    - channels: List of marketing channels
    - countries: List of countries
    - age_groups: List of age groups
    - from_date: Start date as Unix timestamp
    - to_date: End date as Unix timestamp
    - campaign_ids: List of campaign IDs
    - min_revenue: Minimum revenue amount
    - max_revenue: Maximum revenue amount
    - min_ad_spend: Minimum ad spend amount
    - max_ad_spend: Maximum ad spend amount
    - min_views: Minimum views count
    - min_leads: Minimum leads count

    Returns:
        JSON object containing monthly aggregated data and applied filters
    """
    # Extract parameters from request JSON body
    request_data = request.get_json() or {}

    params = {
        "channels": request_data.get("channels", []),
        "countries": request_data.get("countries", []),
        "age_groups": request_data.get("age_groups", []),
        "campaign_ids": request_data.get("campaign_ids", []),
        "from_date": request_data.get("from_date"),
        "to_date": request_data.get("to_date"),
        "min_revenue": request_data.get("min_revenue"),
        "max_revenue": request_data.get("max_revenue"),
        "min_ad_spend": request_data.get("min_ad_spend"),
        "max_ad_spend": request_data.get("max_ad_spend"),
        "min_views": request_data.get("min_views"),
        "min_leads": request_data.get("min_leads"),
    }

    # Create validation context for date range validation
    context = {}
    if "from_date" in params and params["from_date"]:
        context["from_date"] = params["from_date"]

    # Validate parameters using the campaign filter schema
    validated_params = validate_request_data(params, CampaignFilterSchema, context)

    # Call service function to get aggregated data
    data = get_monthly_aggregated_data(validated_params)
    return format_response(data)


@data_bp.route("/api/v1/campaigns/channel-contribution", methods=["GET"])
@handle_exceptions
def get_channel_contribution_data_route():
    """
    Get channel contribution data for various metrics over the latest 3 months.

    Returns data for chart showing percentage contribution of each channel
    to Spending, Views, Leads, New Accounts, and Revenue metrics.

    Returns:
        JSON object containing metrics, channels, and percentage contribution data
    """
    try:
        data = get_channel_contribution_data()
        return format_response(data)

    except Exception as e:
        logger.error(f"Error retrieving channel contribution data: {e}")
        return error_response(500, str(e), "server_error")


@data_bp.route("/api/v1/campaigns/cost-metrics-heatmap", methods=["GET"])
@handle_exceptions
def get_cost_metrics_heatmap_route():
    """
    Get cost metrics heatmap data showing different cost metrics (cost per lead, view, account) by channel.

    Returns:
        JSON object containing heatmap data with metrics, channels, and values with intensity levels
    """
    try:
        data = get_cost_metrics_heatmap()
        return format_response(data)

    except Exception as e:
        logger.error(f"Error retrieving cost metrics heatmap data: {e}")
        return error_response(500, str(e), "server_error")


@data_bp.route("/api/v1/campaigns/latest-month-roi", methods=["GET"])
@handle_exceptions
def get_latest_month_roi_route():
    """
    Get ROI (Return on Investment) for the latest month in the dataset.
    ROI is calculated as (Revenue - Ad Spend) / Ad Spend * 100.

    Returns:
        JSON object containing:
        - roi: ROI value as percentage
        - month: Month number (1-12)
        - year: Year number
    """
    data = get_latest_month_roi()
    return format_response(data)


@data_bp.route("/api/v1/campaigns/latest-month-revenue", methods=["GET"])
@handle_exceptions
def get_latest_month_revenue_route():
    """
    Get total revenue for the latest month in the dataset.

    Returns:
        JSON object containing:
        - revenue: Total revenue value
        - month: Month number (1-12)
        - year: Year number
    """
    data = get_latest_month_revenue()
    return format_response(data)


@data_bp.route("/api/v1/prophet-predictions", methods=["GET"])
@handle_exceptions
def get_prophet_predictions():
    """
    Retrieve prophet prediction data, optionally filtered by date range.
    """
    try:
        # Get date range filters if provided
        from_date = request.args.get("from_date", type=float)
        to_date = request.args.get("to_date", type=float)

        # Import here to avoid circular imports
        from app.models.prophet_prediction import ProphetPredictionModel

        # Retrieve data based on filters
        if from_date and to_date:
            logger.info(f"Retrieving prophet predictions from {from_date} to {to_date}")
            predictions = ProphetPredictionModel.get_date_range(from_date, to_date)
        else:
            logger.info("Retrieving all prophet predictions")
            predictions = ProphetPredictionModel.get_all()

        # Return the data
        return format_response({"data": predictions, "count": len(predictions)})

    except Exception as e:
        logger.error(f"Error retrieving prophet predictions: {e}")
        return error_response(500, f"Internal server error: {str(e)}", "server_error")


@data_bp.route("/api/v1/campaigns/monthly-channel-data", methods=["GET"])
@handle_exceptions
def get_monthly_channel_data_route():
    """
    Get monthly data aggregated by channel for charting purposes.
    Returns revenue and ad spend metrics per month per channel.

    Returns:
        JSON object containing:
        - months: List of months as timestamps
        - channels: List of available channels
        - revenue: Dictionary with channel keys and monthly revenue arrays
        - ad_spend: Dictionary with channel keys and monthly ad spend arrays
    """
    try:

        data = get_monthly_channel_data()
        return format_response(data)

    except Exception as e:
        logger.error(f"Error getting monthly channel data: {e}")
        return error_response(500, f"Internal server error: {str(e)}", "server_error")


@data_bp.route("/api/v1/campaigns/monthly-age-data", methods=["GET"])
@handle_exceptions
def get_monthly_age_data_route():
    """
    Get monthly data aggregated by age group for charting purposes.
    Returns revenue and ad spend metrics per month per age group.

    Returns:
        JSON object containing:
        - months: List of months as timestamps
        - age_groups: List of available age groups
        - revenue: Dictionary with age group keys and monthly revenue arrays
        - ad_spend: Dictionary with age group keys and monthly ad spend arrays
    """
    try:

        data = get_monthly_age_data()
        return format_response(data)

    except Exception as e:
        logger.error(f"Error getting monthly age group data: {e}")
        return error_response(500, f"Internal server error: {str(e)}", "server_error")


@data_bp.route("/api/v1/campaigns/monthly-country-data", methods=["GET"])
@handle_exceptions
def get_monthly_country_data_route():
    """
    Get monthly data aggregated by country for charting purposes.
    Returns revenue and ad spend metrics per month per country.

    Returns:
        JSON object containing:
        - months: List of months as timestamps
        - countries: List of available countries
        - revenue: Dictionary with country keys and monthly revenue arrays
        - ad_spend: Dictionary with country keys and monthly ad spend arrays
    """
    try:
        data = get_monthly_country_data()
        return format_response(data)

    except Exception as e:
        logger.error(f"Error getting monthly country data: {e}")
        return error_response(500, f"Internal server error: {str(e)}", "server_error")


@data_bp.route("/api/v1/campaigns/latest-twelve-months", methods=["GET"])
@handle_exceptions
def get_latest_twelve_months_route():
    """
    Get the latest 12 months of aggregated data, including only date, revenue and ad spend.

    Returns:
        JSON object containing:
        - items: List of dictionaries with date, revenue, and ad_spend for each month
    """
    try:
        data = get_latest_twelve_months_data()
        return format_response(data)

    except Exception as e:
        logger.error(f"Error getting latest twelve months data: {e}")
        return error_response(500, f"Internal server error: {str(e)}", "server_error")


# ----------------------------------------------------------------
# CSV import endpoints
# ----------------------------------------------------------------


@data_bp.route("/api/v1/imports/csv", methods=["POST", "OPTIONS"])
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
            records, is_structured_data, default_collection_name = process_csv_data(
                file
            )

            # Find matching collection for data
            matching_collection, collection_name, found_match = (
                find_matching_collection(
                    records, is_structured_data, default_collection_name
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
