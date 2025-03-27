import csv
import json
import logging
from datetime import datetime
from io import StringIO

import pandas as pd
from bson import json_util
from werkzeug.utils import secure_filename

from app.database.schema import CAMPAIGN_FIELDS, matches_campaign_schema
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

    if is_campaign_data:
        logger.info("CSV matches CampaignData schema")
        records = process_campaign_data(records)
        default_collection_name = "campaign_performance"
    else:
        default_collection_name = secure_filename(file.filename).replace(".csv", "")

    return records, is_campaign_data, default_collection_name


def process_campaign_data(records):
    """
    Process campaign data records with type conversions

    Args:
        records: List of campaign data records

    Returns:
        list: Processed records
    """
    for record in records:
        # Convert date string to datetime object for MongoDB
        if "date" in record and record["date"]:
            try:
                # Parse date string in YYYY-MM-DD format
                date_parts = record["date"].split("-")
                if len(date_parts) == 3:
                    year, month, day = map(int, date_parts)
                    # Use datetime instead of date for MongoDB compatibility
                    record["date"] = datetime(year, month, day)
            except (ValueError, TypeError) as e:
                logger.warning(f"Error converting date field: {e}")
                # Skip records with invalid dates to avoid MongoDB validation errors
                continue

        # Convert numeric fields to float (double in MongoDB) as required by schema
        for field in [
            "ad_spend",
            "views",
            "leads",
            "new_accounts",
            "revenue",
        ]:
            if field in record:
                try:
                    record[field] = float(record[field]) if record[field] else 0.0
                except (ValueError, TypeError):
                    record[field] = 0.0  # Default to 0.0 if conversion fails

    # Filter out records with missing required fields
    valid_records = []
    original_count = len(records)
    for record in records:
        if all(
            field in record and record[field] is not None for field in CAMPAIGN_FIELDS
        ):
            valid_records.append(record)

    if len(valid_records) < original_count:
        logger.warning(
            f"Filtered out {original_count - len(valid_records)} invalid records"
        )

    return valid_records


def find_matching_collection(records, is_campaign_data, default_collection_name):
    """
    Find a collection that matches the schema of the records

    Args:
        records: List of data records
        is_campaign_data: Whether this is campaign data
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

    for coll_name in collections:
        # Skip matching if this is campaign data - we always use campaign_performance
        if is_campaign_data and coll_name == "campaign_performance":
            matching_collection = Database.get_collection(coll_name)
            collection_name = coll_name
            found_match = True
            logger.info("Using existing campaign_performance collection")
            break

        # For non-campaign data, check schema match with existing collections
        if not is_campaign_data:
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
        # For CampaignData, use "campaign_performance" as the collection name
        if is_campaign_data:
            collection_name = "campaign_performance"
        else:
            collection_name = default_collection_name

        matching_collection = Database.get_collection(collection_name)
        logger.info(f"Creating new collection: {collection_name}")

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
