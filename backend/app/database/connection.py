import logging

from pymongo import MongoClient

from app.config import DB_NAME, MONGO_URI

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
        if cls.db is None:
            cls.initialize()
        return cls.db[collection_name]

    @classmethod
    def list_collections(cls):
        """List all collections in the database"""
        if cls.db is None:
            cls.initialize()
        return cls.db.list_collection_names()


    @classmethod
    def delete_collection(cls, collection_name):
        """Safely delete or clear a collection based on its type"""
        if collection_name == "users":
            raise ValueError("User collection cannot be deleted")
            
        collection = cls.get_collection(collection_name)
        
        if collection_name in ["campaign_performance", "prophet_predictions"]:
            # Clear documents but keep collection structure
            result = collection.delete_many({})
            logger.info(f"Cleared {result.deleted_count} documents from {collection_name}")
        else:
            # Permanently delete the collection
            collection.drop()
            logger.info(f"Deleted collection {collection_name}")



# Initialize common collection references
def get_users_collection():
    return Database.get_collection("users")


def get_campaign_performance_collection():
    return Database.get_collection("campaign_performance")


def get_prophet_prediction_collection():
    return Database.get_collection("prophet_predictions")
