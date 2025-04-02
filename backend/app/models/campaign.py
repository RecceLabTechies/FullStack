import logging
from app.database.connection import get_campaign_performance_collection

logger = logging.getLogger(__name__)


class CampaignModel:
    """
    Model for campaign data operations.
    Provides database access methods for campaign data.
    """

    @staticmethod
    def get_all(query=None, projection=None):
        """
        Get all campaign documents matching the query.

        Args:
            query: MongoDB query dict (default: all documents)
            projection: Fields to include/exclude

        Returns:
            list: List of campaign documents
        """
        collection = get_campaign_performance_collection()
        query = query or {}
        projection = projection or {"_id": 0}

        return list(collection.find(query, projection))

    @staticmethod
    def count(query=None):
        """
        Count campaign documents matching the query.

        Args:
            query: MongoDB query dict (default: all documents)

        Returns:
            int: Number of matching documents
        """
        collection = get_campaign_performance_collection()
        query = query or {}

        return collection.count_documents(query)

    @staticmethod
    def get_paginated(
        query=None, projection=None, sort_by="date", sort_dir=-1, skip=0, limit=20
    ):
        """
        Get paginated campaign documents.

        Args:
            query: MongoDB query dict
            projection: Fields to include/exclude
            sort_by: Field to sort by
            sort_dir: Sort direction (1 for ascending, -1 for descending)
            skip: Number of documents to skip
            limit: Maximum number of documents to return

        Returns:
            list: List of campaign documents
        """
        collection = get_campaign_performance_collection()
        query = query or {}
        projection = projection or {"_id": 0}

        return list(
            collection.find(query, projection)
            .sort(sort_by, sort_dir)
            .skip(skip)
            .limit(limit)
        )

    @staticmethod
    def get_distinct(field, query=None):
        """
        Get distinct values for a field.

        Args:
            field: Field name to get distinct values for
            query: Optional query to filter the documents

        Returns:
            list: List of distinct values
        """
        collection = get_campaign_performance_collection()
        query = query or {}

        return collection.distinct(field, query)

    @staticmethod
    def aggregate(pipeline):
        """
        Perform an aggregation pipeline query.

        Args:
            pipeline: MongoDB aggregation pipeline

        Returns:
            list: Result of the aggregation
        """
        collection = get_campaign_performance_collection()

        return list(collection.aggregate(pipeline))

    @staticmethod
    def update_many(query, update):
        """
        Update multiple documents.

        Args:
            query: MongoDB query to select documents
            update: Update operation to apply

        Returns:
            int: Number of documents modified
        """
        collection = get_campaign_performance_collection()

        result = collection.update_many(query, update)
        return result.modified_count

    @staticmethod
    def update_one(query, update):
        """
        Update a single document.

        Args:
            query: MongoDB query to select the document
            update: Update operation to apply

        Returns:
            bool: True if a document was modified, False otherwise
        """
        collection = get_campaign_performance_collection()

        result = collection.update_one(query, update)
        return result.modified_count > 0

    @staticmethod
    def create(document):
        """
        Insert a new campaign document.

        Args:
            document: Document to insert

        Returns:
            str: ID of the inserted document
        """
        collection = get_campaign_performance_collection()

        result = collection.insert_one(document)
        return str(result.inserted_id)

    @staticmethod
    def create_many(documents):
        """
        Insert multiple campaign documents.

        Args:
            documents: List of documents to insert

        Returns:
            int: Number of documents inserted
        """
        collection = get_campaign_performance_collection()

        result = collection.insert_many(documents)
        return len(result.inserted_ids)
