import csv
import logging
from io import StringIO

from werkzeug.utils import secure_filename

from app.data_types import CampaignData, ProphetPredictionData
from app.database.connection import Database
from app.database.schema import (
    matches_campaign_schema,
    matches_prophet_prediction_schema,
)

logger = logging.getLogger(__name__)


def process_csv_data(file):
    """
    Process uploaded CSV file and return processed records

    Args:
        file: The uploaded file object

    Returns:
        tuple: (records, is_structured_data, table_name)
    """
    # Read and decode the file content
    file_content = file.read()
    text_content = file_content.decode("utf-8")
    stream = StringIO(text_content)
    csv_reader = csv.DictReader(stream)

    # Convert to list and validate content
    records = list(csv_reader)
    if not records:
        raise ValueError("CSV file is empty")

    # Extract the schema (field names) from the CSV
    csv_field_names = set(records[0].keys())

    # Check if this matches known data models
    is_campaign_data = matches_campaign_schema(csv_field_names)
    is_prophet_data = matches_prophet_prediction_schema(csv_field_names)

    if is_campaign_data:
        logger.info("CSV matches CampaignData schema")
        records = process_campaign_data(records)
        default_table_name = "campaign_performance"
    elif is_prophet_data:
        logger.info("CSV matches ProphetPredictionData schema")
        records = process_prophet_prediction_data(records)
        default_table_name = "prophet_predictions"
    else:
        default_table_name = secure_filename(file.filename).replace(".csv", "")

    return records, is_campaign_data or is_prophet_data, default_table_name


def process_campaign_data(records):
    """
    Process campaign data records with type conversions using CampaignData model

    Args:
        records: List of campaign data records

    Returns:
        list: Processed records
    """
    valid_records = []
    original_count = len(records)

    for record in records:
        try:
            # Use CampaignData class for validation and type conversion
            campaign_obj = CampaignData(**record)
            # Convert object to dict for database insertion
            processed_record = {
                "date": campaign_obj.date,
                "campaign_id": campaign_obj.campaign_id,
                "channel": campaign_obj.channel,
                "age_group": campaign_obj.age_group,
                "ad_spend": campaign_obj.ad_spend,
                "views": campaign_obj.views,
                "leads": campaign_obj.leads,
                "new_accounts": campaign_obj.new_accounts,
                "country": campaign_obj.country,
                "revenue": campaign_obj.revenue,
            }
            valid_records.append(processed_record)
        except Exception as e:
            logger.warning(f"Error processing campaign record: {e}")
            continue

    if len(valid_records) < original_count:
        logger.warning(
            f"Filtered out {original_count - len(valid_records)} invalid records"
        )

    return valid_records


def process_prophet_prediction_data(records):
    """
    Process prophet prediction data records with type conversions using ProphetPredictionData model

    Args:
        records: List of prophet prediction data records

    Returns:
        list: Processed records
    """
    valid_records = []
    original_count = len(records)

    for record in records:
        try:
            # Use ProphetPredictionData class for validation and type conversion
            prediction_obj = ProphetPredictionData(**record)
            # Convert object to dict for database insertion
            processed_record = {
                "date": prediction_obj.date,
                "revenue": prediction_obj.revenue,
                "ad_spend": prediction_obj.ad_spend,
                "new_accounts": prediction_obj.new_accounts,
            }
            valid_records.append(processed_record)
        except Exception as e:
            logger.warning(f"Error processing prophet prediction record: {e}")
            continue

    if len(valid_records) < original_count:
        logger.warning(
            f"Filtered out {original_count - len(valid_records)} invalid records"
        )

    return valid_records


def find_matching_table(records, is_structured_data, default_table_name):
    """
    Find a table that matches the schema of the records

    Args:
        records: List of data records
        is_structured_data: Whether this is campaign or prophet prediction data
        default_table_name: Default table name to use

    Returns:
        tuple: (table_name, table_schema, found_match)
    """
    csv_field_names = set(records[0].keys())
    table_schema = None
    table_name = None
    found_match = False

    # Get all tables in the database
    tables = Database.list_tables()

    # First check known tables based on default_table_name
    if is_structured_data and default_table_name in [
        "campaign_performance",
        "prophet_predictions",
    ]:
        table_name = default_table_name
        found_match = True
        logger.info(f"Using existing {default_table_name} table")
        return default_table_name, table_name, found_match

    # For non-structured data, check schema match with existing tables
    if not is_structured_data:
        for table in tables:
            # Get table schema
            query = """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'public' AND table_name = %s
            """
            columns = Database.execute_query(query, (table,))

            if columns:
                # Extract the column names from the result
                table_columns = {col["column_name"] for col in columns}

                # Check if the field names match (excluding id and created_at columns)
                table_columns_filtered = {
                    col for col in table_columns if col not in ("id", "created_at")
                }
                if csv_field_names == table_columns_filtered:
                    table_name = table
                    found_match = True
                    logger.info(f"Found matching table: {table_name}")
                    break

    # If no matching table found, use the default name
    if not found_match:
        table_name = default_table_name
        logger.info(f"Will create new table: {default_table_name}")

    return table_name, table_name, found_match


def get_db_structure():
    """
    Get the structure of all tables in the database.

    Returns:
        dict: Structure of all tables
    """
    structure = {"PostgreSQL": {}}

    # Get list of all tables
    tables = Database.list_tables()

    for table_name in tables:
        # Get up to 10 rows to display
        query = f"SELECT * FROM {table_name} LIMIT 10"
        sample_rows = Database.execute_query(query)

        if sample_rows:
            structure["PostgreSQL"][table_name] = sample_rows
        else:
            structure["PostgreSQL"][table_name] = "Empty Table"

    return structure


# Add a utility function for the Database class to use in bulk inserts
def add_bulk_insert_to_database():
    """Add a bulk insert method to the Database class if it doesn't exist"""
    if not hasattr(Database, "bulk_insert"):

        @classmethod
        def bulk_insert(cls, table_name, records):
            """
            Insert multiple records into a table

            Args:
                table_name: Name of the table
                records: List of record dictionaries

            Returns:
                int: Number of records inserted
            """
            if not records:
                return 0

            # All dictionaries should have same keys
            sample = records[0]
            fields = sample.keys()
            columns = ", ".join(fields)

            # Create placeholder groups for each row
            values_list = []
            placeholders_template = "(" + ", ".join(["%s"] * len(fields)) + ")"
            placeholders = []

            for record in records:
                values_list.extend([record[field] for field in fields])
                placeholders.append(placeholders_template)

            placeholders_str = ", ".join(placeholders)
            query = f"INSERT INTO {table_name} ({columns}) VALUES {placeholders_str}"

            result = cls.execute_query(query, tuple(values_list), fetch=False)
            return result

        # Add the method to the Database class
        setattr(Database, "bulk_insert", bulk_insert)
