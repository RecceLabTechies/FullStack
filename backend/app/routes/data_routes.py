import logging
from functools import wraps

from flask import Blueprint, jsonify, make_response, request
import pandas as pd
from marshmallow import Schema, fields, ValidationError, validate, EXCLUDE, validates

from app.database.connection import get_campaign_performance_collection
from app.services.campaign_service import (
    filter_campaigns,
    get_age_group_roi,
    get_campaign_filter_options,
    get_channel_roi,
    get_cost_heatmap_data,
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

    # Date filters
    from_date = fields.Date(format="%Y-%m-%d", required=False)
    to_date = fields.Date(format="%Y-%m-%d", required=False)

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

    month = fields.String(required=True, validate=validate.Regexp(r"^\d{4}-\d{2}$"))
    revenue = fields.Float(required=False)
    ad_spend = fields.Float(required=False)

    class Meta:
        unknown = EXCLUDE

    @validates("month")
    def validate_month_format(self, value, **kwargs):
        """Validate month string is in correct YYYY-MM format"""
        try:
            year, month = map(int, value.split("-"))
            if not (1 <= month <= 12):
                raise ValidationError("Month must be between 1 and 12")
            if not (2000 <= year <= 2100):  # Reasonable year range
                raise ValidationError("Year must be between 2000 and 2100")
        except ValueError:
            raise ValidationError("Month must be in YYYY-MM format")

    @validates("month")
    def validate_required_values(self, value, **kwargs):
        """Validate that at least one of revenue or ad_spend is provided"""
        revenue = self.get("revenue")
        ad_spend = self.get("ad_spend")
        if revenue is None and ad_spend is None:
            raise ValidationError(
                "At least one of revenue or ad_spend must be provided"
            )

    def convert_to_monthly_update(self, data):
        """Convert validated data to a monthly update object"""
        return {
            "month": data["month"],
            "revenue": data.get("revenue"),
            "ad_spend": data.get("ad_spend"),
        }


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

    date = fields.DateTime(required=True)
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

    # Date filters
    from_date = fields.Date(format="%Y-%m-%d", required=False, allow_none=True)
    to_date = fields.Date(format="%Y-%m-%d", required=False, allow_none=True)

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


class CsvImportSchema(Schema):
    """Schema for validating CSV import request"""

    file = fields.Raw(required=True)

    class Meta:
        unknown = EXCLUDE

    @validates("file")
    def validate_file(self, value, **kwargs):
        """Validate the file is present and is a CSV"""
        if not value or not value.filename:
            raise ValidationError("No file selected")

        if not value.filename.endswith(".csv"):
            raise ValidationError("File must be a CSV")

        return value


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


@data_bp.route("/api/v1/campaigns", methods=["GET", "POST"])
@handle_exceptions
def get_campaigns_data():
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

    Returns:
        JSON object containing paginated campaign data and metadata
    """
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
            "channels": parse_list_param(request.args.get("channels")),
            "countries": parse_list_param(request.args.get("countries")),
            "age_groups": parse_list_param(request.args.get("age_groups")),
            "campaign_ids": parse_list_param(request.args.get("campaign_ids")),
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


@data_bp.route("/api/v1/campaigns/revenues", methods=["GET"])
@handle_exceptions
def get_revenue_by_date_data():
    """
    Get aggregated revenue data by date for charting.

    Returns:
        JSON object with dates, revenues, and ad_spends arrays
    """
    data_summary = get_revenue_by_date()
    return format_response(data_summary)


@data_bp.route("/api/v1/campaigns/monthly-performance", methods=["GET"])
@handle_exceptions
def get_monthly_performance_data_route():
    """
    Get monthly revenue and ad spend data for charting.

    Optional query parameters:
    - from_date: Start date in ISO format (YYYY-MM-DD)
    - to_date: End date in ISO format (YYYY-MM-DD)
    - channels: Comma-separated list of marketing channels
    - countries: Comma-separated list of countries
    - age_groups: Comma-separated list of age groups

    Returns:
        JSON object with months, revenue, ad_spend, and roi arrays
    """
    # Extract and prepare filter parameters
    params = {
        "from_date": request.args.get("from_date"),
        "to_date": request.args.get("to_date"),
        "channels": parse_list_param(request.args.get("channels")),
        "countries": parse_list_param(request.args.get("countries")),
        "age_groups": parse_list_param(request.args.get("age_groups")),
    }

    # Create context for date validation
    context = {}
    if params.get("from_date"):
        context["from_date"] = params["from_date"]

    # Validate with the helper
    validated_filters = validate_request_data(
        params, MonthlyPerformanceFilterSchema, context
    )

    # Call model function to get the data
    data = get_monthly_performance_data(validated_filters)
    return format_response(data)


@data_bp.route("/api/v1/campaigns/monthly-data", methods=["POST"])
@handle_exceptions
def update_monthly_data_route():
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

    Returns:
        JSON object with updated monthly chart data
    """
    # Get request data
    data = request.json or {}

    # Validate overall request structure with list schema
    validated_data = validate_request_data(data, MonthlyUpdateListSchema)

    # Process each update item in the list
    converted_updates = validate_and_convert_list(
        validated_data["updates"], MonthlyUpdateSchema, "convert_to_monthly_update"
    )

    # Check if we have any valid updates
    if not converted_updates:
        raise ValueError("No valid updates found after validation")

    # Call model function to update the data with converted objects
    updated_data = update_monthly_data(converted_updates)

    return format_response(
        {"message": "Monthly data updated successfully", **updated_data}
    )


@data_bp.route("/api/v1/campaigns/channels/roi", methods=["GET"])
@handle_exceptions
def get_channel_roi_data_route():
    """
    Get revenue per dollar spent for each marketing channel.

    Returns:
        Array of objects with channel and roi values
    """
    data = get_channel_roi()
    return format_response(data)


@data_bp.route("/api/v1/campaigns/age-groups/roi", methods=["GET"])
@handle_exceptions
def get_age_group_roi_data_route():
    """
    Get revenue per dollar spent for each age group.

    Returns:
        Array of objects with age_group and roi values
    """
    data = get_age_group_roi()
    return format_response(data)


@data_bp.route("/api/v1/campaigns/past-month/revenue", methods=["GET"])
@handle_exceptions
def get_revenue_past_month_data_route():
    """
    Get total revenue for the past month.

    Returns:
        JSON object with revenue value
    """
    revenue = get_revenue_past_month()
    return format_response({"revenue": revenue})


@data_bp.route("/api/v1/campaigns/past-month/roi", methods=["GET"])
@handle_exceptions
def get_roi_past_month_data_route():
    """
    Get ROI (revenue per dollar spent) for the past month.

    Returns:
        JSON object with roi value
    """
    roi = get_roi_past_month()
    return format_response({"roi": roi})


@data_bp.route("/api/v1/campaigns/cost-heatmap", methods=["GET"])
@handle_exceptions
def get_cost_heatmap_data_route():
    """
    Get cost heatmap data showing cost metrics by channel.

    Query parameters:
    - country: Country to filter data for (default: Singapore)
    - campaign_id: Campaign ID to filter data for (default: January_2022_1)
    - channels: Comma-separated list of channels to include

    Returns:
        Array of objects with channel and cost metrics (costPerLead, costPerView, costPerAccount)
    """
    try:
        # Extract and prepare parameters
        params = {
            "country": request.args.get("country", "Singapore"),
            "campaign_id": request.args.get("campaign_id", "January_2022_1"),
            "channels": parse_list_param(request.args.get("channels")),
        }

        # Validate with Marshmallow schema
        try:
            schema = CostHeatmapSchema()
            validated_params = schema.load(params)
        except ValidationError as err:
            return validation_error_response(err.messages)

        # Call the model function
        channels = validated_params.get("channels")
        data_summary = get_cost_heatmap_data(
            validated_params["country"], validated_params["campaign_id"], channels
        )

        # Check if we have data
        if not data_summary:
            return error_response(
                404,
                f"No data found for {validated_params['country']} and campaign {validated_params['campaign_id']}",
                "resource_not_found",
            )

        return format_response(data_summary)

    except Exception as e:
        logger.error(f"Error retrieving cost heatmap data: {e}")
        return error_response(500, str(e), "server_error")


# ----------------------------------------------------------------
# CSV import endpoints
# ----------------------------------------------------------------


@data_bp.route("/api/v1/imports/csv", methods=["POST", "OPTIONS"])
@handle_exceptions
def create_csv_import_data():
    """
    Handle CSV file uploads and import data into MongoDB.

    Form data:
    - file: CSV file to upload

    Returns:
        JSON object with import results
    """
    # Handle CORS preflight request
    if request.method == "OPTIONS":
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "*")
        response.headers.add("Access-Control-Allow-Methods", "POST")
        return response

    # Validate file upload
    file = validate_request_data(request.files, CsvImportSchema)["file"]

    try:
        # Process CSV data
        records, is_campaign_data, default_collection_name = process_csv_data(file)

        # Convert records to domain objects if they are campaign data
        if is_campaign_data and records:
            converted_records = validate_and_convert_list(
                records, CampaignDataSchema, "convert_to_campaign_data"
            )

            # Convert to dict for MongoDB storage
            records = [
                record.__dict__ if hasattr(record, "__dict__") else record
                for record in converted_records
            ]

        # Check if we have any valid records
        if not records:
            raise ValueError("No valid records found after validation")

        # Find matching collection for data
        matching_collection, collection_name, found_match = find_matching_collection(
            records, is_campaign_data, default_collection_name
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
        raise ValueError("Invalid CSV file encoding. Please use UTF-8")


# ----------------------------------------------------------------
# Utility endpoints
# ----------------------------------------------------------------


@data_bp.route("/api/v1/utils/date-types", methods=["GET"])
@handle_exceptions
def get_date_type_data():
    """
    Utility endpoint to inspect the date field data type in the campaign collection.

    Returns:
        JSON object with value and type information
    """
    collection = get_campaign_performance_collection()

    # Fetch one sample document
    sample = collection.find_one({}, {"date": 1, "_id": 0})

    if not sample or "date" not in sample:
        logger.warning("No date field found in sample document")
        return error_response(
            404, "No date field found in sample", "resource_not_found"
        )

    date_value = sample["date"]
    return format_response({"value": date_value, "type": str(type(date_value))})
