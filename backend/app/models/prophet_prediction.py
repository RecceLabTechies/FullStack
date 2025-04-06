import logging

from app.database.connection import get_prophet_prediction_collection

logger = logging.getLogger(__name__)


class ProphetPredictionModel:
    """
    Model for prophet prediction data operations.
    Provides database access methods for prophet prediction data.
    """

    @staticmethod
    def get_all():
        """
        Retrieve all prophet predictions from the 'prophet_predictions' collection in the database.

        Returns:
            list: List of prophet prediction documents
        """
        collection = get_prophet_prediction_collection()
        return list(collection.find({}, {"_id": 0}))

    @staticmethod
    def get_by_date(date):
        """
        Retrieve prophet prediction data for a specific date.

        Args:
            date: The timestamp to search for

        Returns:
            dict: Prophet prediction data or None if not found
        """
        collection = get_prophet_prediction_collection()
        return collection.find_one({"date": date}, {"_id": 0})

    @staticmethod
    def get_date_range(start_date, end_date):
        """
        Retrieve prophet prediction data within a date range.

        Args:
            start_date: Start timestamp for the date range
            end_date: End timestamp for the date range

        Returns:
            list: List of prophet prediction data documents within the date range
        """
        collection = get_prophet_prediction_collection()
        return list(
            collection.find(
                {"date": {"$gte": start_date, "$lte": end_date}},
                {"_id": 0},
            ).sort("date", 1)
        )

    @staticmethod
    def create(prediction_data):
        """
        Add a new prophet prediction data document to the collection.

        Args:
            prediction_data: Dictionary containing prophet prediction data

        Returns:
            str: ID of the inserted document
        """
        collection = get_prophet_prediction_collection()
        result = collection.insert_one(prediction_data)
        return str(result.inserted_id)

    @staticmethod
    def create_many(prediction_data_list):
        """
        Add multiple prophet prediction data documents to the collection.

        Args:
            prediction_data_list: List of dictionaries containing prophet prediction data

        Returns:
            int: Number of documents inserted
        """
        collection = get_prophet_prediction_collection()
        result = collection.insert_many(prediction_data_list)
        return len(result.inserted_ids)

    @staticmethod
    def update(date, update_data):
        """
        Update a prophet prediction data document in the collection.

        Args:
            date: The timestamp of the document to update
            update_data: Dictionary containing the updated data

        Returns:
            bool: True if document was updated, False otherwise
        """
        collection = get_prophet_prediction_collection()
        result = collection.update_one({"date": date}, {"$set": update_data})
        return result.matched_count > 0

    @staticmethod
    def delete(date):
        """
        Delete a prophet prediction data document from the collection.

        Args:
            date: The timestamp of the document to delete

        Returns:
            bool: True if document was deleted, False otherwise
        """
        collection = get_prophet_prediction_collection()
        result = collection.delete_one({"date": date})
        return result.deleted_count > 0

    @staticmethod
    def delete_all():
        """
        Delete all prophet prediction data documents from the collection.

        Returns:
            int: Number of documents deleted
        """
        collection = get_prophet_prediction_collection()
        result = collection.delete_many({})
        return result.deleted_count
