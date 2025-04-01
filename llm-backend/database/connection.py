import logging
from pymongo import MongoClient
from config import MONGO_URI, DB_NAME

logger = logging.getLogger(__name__)


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
        if not cls.db:
            cls.initialize()
        return cls.db[collection_name]

    @classmethod
    def list_collections(cls):
        """List all collections in the database"""
        if not cls.db:
            cls.initialize()
        return cls.db.list_collection_names()


# Initialize common collection references
def get_queries_collection():
    return Database.get_collection("queries")


def get_results_collection():
    return Database.get_collection("results")
