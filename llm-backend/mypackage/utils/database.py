import logging
from pymongo import MongoClient
from config import MONGO_URI, DB_NAME

logger = logging.getLogger(__name__)

# Collections that should not be accessible
RESTRICTED_COLLECTIONS = ["users", "prophet_predictions"]


class Database:
    client = None
    db = None

    @classmethod
    def initialize(cls):
        """Initialize MongoDB connection and reference collections"""
        try:
            # Connect to MongoDB
            cls.client = MongoClient(MONGO_URI)
            # Test the connection
            cls.client.server_info()
            # Get database reference
            cls.db = cls.client[DB_NAME]
            logger.info("Successfully connected to MongoDB")
            return True
        except Exception as e:
            logger.error(f"Error connecting to MongoDB: {e}")
            return False

    @classmethod
    def get_collection(cls, collection_name):
        """Get a reference to a specific collection"""
        if collection_name in RESTRICTED_COLLECTIONS:
            logger.warning(
                f"Access to restricted collection '{collection_name}' was denied"
            )
            return None

        if cls.db is None:
            cls.initialize()
        return cls.db[collection_name]

    @classmethod
    def list_collections(cls):
        """List all collections in the database except restricted ones"""
        if cls.db is None:
            cls.initialize()
        all_collections = cls.db.list_collection_names()
        return [col for col in all_collections if col not in RESTRICTED_COLLECTIONS]

    @classmethod
    def analyze_collections(cls):
        """
        Analyze all accessible collections and their fields with statistics.

        Returns:
            dict: A dictionary where:
                - Keys are collection names
                - Values are dictionaries where:
                    - Keys are field names
                    - Values are dictionaries with field statistics
        """
        if cls.db is None:
            cls.initialize()

        result = {}
        collections = cls.list_collections()

        for collection_name in collections:
            collection = cls.db[collection_name]
            # Get sample documents to determine fields
            sample = list(collection.find())

            if not sample:
                result[collection_name] = {}
                continue

            fields = {}
            # First, identify all fields in the sample
            for doc in sample:
                for field_name, value in doc.items():
                    if field_name not in fields:
                        fields[field_name] = {"type": str(type(value).__name__)}

            # Analyze each field
            for field_name, field_info in fields.items():
                # Skip the _id field
                if field_name == "_id":
                    continue

                # Determine field type and calculate statistics
                sample_values = [
                    doc.get(field_name) for doc in sample if field_name in doc
                ]
                non_null_values = [v for v in sample_values if v is not None]

                if not non_null_values:
                    fields[field_name] = {
                        "type": "unknown",
                        "stats": "no non-null values",
                    }
                    continue

                # Check if numerical
                if all(isinstance(v, (int, float)) for v in non_null_values):
                    min_val = min(non_null_values)
                    max_val = max(non_null_values)
                    fields[field_name] = {
                        "type": "numerical",
                        "stats": {"min": min_val, "max": max_val},
                    }
                # Check if datetime
                elif all(hasattr(v, "strftime") for v in non_null_values):
                    min_val = min(non_null_values)
                    max_val = max(non_null_values)
                    fields[field_name] = {
                        "type": "datetime",
                        "stats": {"min": min_val, "max": max_val},
                    }
                # Treat as categorical
                else:
                    unique_values = list(set(str(v) for v in non_null_values))
                    # Don't limit unique values
                    fields[field_name] = {
                        "type": "categorical",
                        "stats": {"unique_values": unique_values},
                    }

            result[collection_name] = fields

        return result


# Initialize common collection references
def get_campaign_performance_collection():
    return Database.get_collection("campaign_performance")


# Function to check if a collection is accessible
def is_collection_accessible(collection_name):
    return collection_name not in RESTRICTED_COLLECTIONS
