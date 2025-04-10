import logging

from pymongo import MongoClient

from config import DB_NAME, MONGO_URI

logger = logging.getLogger(__name__)

# Collections that should not be accessible
RESTRICTED_COLLECTIONS = ["users", "prophet_predictions"]


class Database:
    """
    Singleton class for managing MongoDB database connections and operations.

    This class provides centralized access to the MongoDB database, with methods
    for initializing connections, accessing collections, and analyzing collection
    metadata. It implements a singleton pattern to ensure a single connection
    is maintained throughout the application.

    Attributes:
        client: MongoDB client instance
        db: Reference to the configured MongoDB database
    """

    client = None
    db = None

    @classmethod
    def initialize(cls):
        """
        Initialize the MongoDB connection.

        This method establishes a connection to MongoDB using the configured
        MONGO_URI and DB_NAME from the config module. It sets up the class-level
        client and db attributes for later use.

        Returns:
            bool: True if connection was successful, False otherwise
        """
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
        """
        Get a reference to a MongoDB collection, if it's not restricted.

        This method checks if the requested collection is in the restricted list
        before returning a reference to it. If the database connection hasn't been
        initialized, it will initialize it first.

        Args:
            collection_name (str): Name of the collection to retrieve

        Returns:
            Collection: MongoDB collection reference, or None if the collection is restricted
        """
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
        """
        List all accessible (non-restricted) collections in the database.

        This method retrieves the names of all collections in the database
        and filters out any that are in the RESTRICTED_COLLECTIONS list.

        Returns:
            list: List of accessible collection names
        """
        if cls.db is None:
            cls.initialize()
        all_collections = cls.db.list_collection_names()
        return [col for col in all_collections if col not in RESTRICTED_COLLECTIONS]

    @classmethod
    def analyze_collections(cls):
        """
        Analyze all accessible collections to extract field information and statistics.

        This method examines each accessible collection in the database, identifies
        all fields, and generates statistics about each field (min/max values for
        numerical fields, unique values for categorical fields, etc.).

        Returns:
            dict: Nested dictionary with structure:
                {
                    "collection_name": {
                        "field_name": {
                            "type": "numerical|categorical|datetime|etc",
                            "stats": {
                                "min": minimum value (for numerical/datetime),
                                "max": maximum value (for numerical/datetime),
                                "unique_values": list of values (for categorical)
                            }
                        }
                    }
                }
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
    """
    Get a reference to the campaign_performance collection.

    This is a convenience function for accessing a commonly used collection.

    Returns:
        Collection: MongoDB collection reference for campaign_performance
    """
    return Database.get_collection("campaign_performance")


# Function to check if a collection is accessible
def is_collection_accessible(collection_name):
    """
    Check if a collection is accessible (not in the restricted list).

    Args:
        collection_name (str): Name of the collection to check

    Returns:
        bool: True if the collection is accessible, False if it's restricted
    """
    return collection_name not in RESTRICTED_COLLECTIONS
