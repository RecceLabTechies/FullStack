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


# Initialize common collection references
def get_campaign_performance_collection():
    return Database.get_collection("campaign_performance")


# Function to check if a collection is accessible
def is_collection_accessible(collection_name):
    return collection_name not in RESTRICTED_COLLECTIONS
