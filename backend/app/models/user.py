import logging

from app.database.connection import get_users_collection

logger = logging.getLogger(__name__)


class UserModel:
    """
    Model for user data operations.
    Provides database access methods for user data.
    """

    @staticmethod
    def get_all():
        """
        Retrieve all users from the 'users' collection in the database.

        Returns:
            list: List of user documents
        """
        users_collection = get_users_collection()
        return list(users_collection.find({}, {"_id": 0}))

    @staticmethod
    def get_by_username(username):
        """
        Retrieve a user's information from the 'users' collection based on the username.

        Args:
            username: The username to search for

        Returns:
            dict: User information or None if not found
        """
        users_collection = get_users_collection()
        return users_collection.find_one(
            {"username": username}, {"_id": 0}
        )  # Exclude the ObjectId from the response

    @staticmethod
    def create(user_data):
        """
        Add a new user to the 'users' collection in the database.

        Args:
            user_data: Dictionary containing user data

        Returns:
            str: ID of the inserted user
        """
        users_collection = get_users_collection()
        result = users_collection.insert_one(user_data)
        return str(result.inserted_id)

    @staticmethod
    def update(username, update_data):
        """
        Update a user in the 'users' collection in the database.

        Args:
            username: The username of the user to update
            update_data: Dictionary containing the complete updated user data

        Returns:
            bool: True if user was updated, False otherwise
        """
        users_collection = get_users_collection()
        result = users_collection.update_one(
            {"username": username}, {"$set": update_data}
        )
        return result.matched_count > 0

    @staticmethod
    def update_fields(username, update_fields):
        """
        Update specific fields of a user in the 'users' collection.

        Args:
            username: The username of the user to update
            update_fields: Dictionary containing fields to update

        Returns:
            bool: True if user was updated, False otherwise
        """
        users_collection = get_users_collection()
        result = users_collection.update_one(
            {"username": username}, {"$set": update_fields}
        )
        return result.matched_count > 0

    @staticmethod
    def delete(username):
        """
        Delete a user from the 'users' collection in the database.

        Args:
            username: The username of the user to delete

        Returns:
            bool: True if user was deleted, False otherwise
        """
        users_collection = get_users_collection()
        result = users_collection.delete_one({"username": username})
        return result.deleted_count > 0
