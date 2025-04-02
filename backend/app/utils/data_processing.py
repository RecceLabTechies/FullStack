import csv
import json
import logging
from io import StringIO
from bson import json_util
from werkzeug.utils import secure_filename
from app.data_types import CampaignData, ProphetPredictionData
from app.database.schema import (
    matches_campaign_schema,
    matches_prophet_prediction_schema,
)
from app.database.connection import Database

logger = logging.getLogger(__name__)


def process_csv_data(file):
    """
    Process uploaded CSV file and return processed records

    Args:
        file: The uploaded file object

    Returns:
        tuple: (records, is_campaign_data, collection_name)
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
        default_collection_name = "campaign_performance"
    elif is_prophet_data:
        logger.info("CSV matches ProphetPredictionData schema")
        records = process_prophet_prediction_data(records)
        default_collection_name = "prophet_predictions"
    else:
        default_collection_name = secure_filename(file.filename).replace(".csv", "")

    return records, is_campaign_data or is_prophet_data, default_collection_name


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
            # Convert object to dict for MongoDB insertion
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
            # Convert object to dict for MongoDB insertion
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


def find_matching_collection(records, is_structured_data, default_collection_name):
    """
    Find a collection that matches the schema of the records

    Args:
        records: List of data records
        is_structured_data: Whether this is campaign or prophet prediction data
        default_collection_name: Default collection name to use

    Returns:
        tuple: (collection, collection_name, found_match)
    """
    csv_field_names = set(records[0].keys())
    matching_collection = None
    collection_name = None
    found_match = False

    # Get all collections in the database
    collections = Database.list_collections()

    # First check known collections based on default_collection_name
    if is_structured_data and default_collection_name in [
        "campaign_performance",
        "prophet_predictions",
    ]:
        matching_collection = Database.get_collection(default_collection_name)
        collection_name = default_collection_name
        found_match = True
        logger.info(f"Using existing {default_collection_name} collection")
        return matching_collection, collection_name, found_match

    # For non-structured data, check schema match with existing collections
    if not is_structured_data:
        for coll_name in collections:
            # Get a sample document to check schema
            sample_doc = Database.get_collection(coll_name).find_one({}, {"_id": 0})

            if sample_doc:
                # Extract the field names from the sample document
                collection_field_names = set(sample_doc.keys())

                # Check if the field names match
                if csv_field_names == collection_field_names:
                    matching_collection = Database.get_collection(coll_name)
                    collection_name = coll_name
                    found_match = True
                    logger.info(f"Found matching collection: {collection_name}")
                    break

    # If no matching collection found, create a new one
    if not found_match:
        matching_collection = Database.get_collection(default_collection_name)
        logger.info(f"Creating new collection: {default_collection_name}")

    return matching_collection, collection_name, found_match


def get_db_structure():
    """
    Get the structure of all databases and their collections.

    Returns:
        dict: Structure of all databases and collections
    """
    structure = {}
    # Get list of all databases
    database_list = Database.client.list_database_names()

    for db_name in database_list:
        # Skip system databases
        if db_name not in ["admin", "local", "config"]:
            db = Database.client[db_name]
            structure[db_name] = {}

            # Get all collections in the database
            collections = db.list_collection_names()

            for collection_name in collections:
                collection = db[collection_name]
                # Get up to 10 documents to display
                sample_docs = list(collection.find().limit(10))
                if sample_docs:
                    # Convert ObjectId to string for JSON serialization
                    sample_docs = json.loads(json_util.dumps(sample_docs))
                    structure[db_name][collection_name] = sample_docs
                else:
                    structure[db_name][collection_name] = "Empty Collection"

    return structure
