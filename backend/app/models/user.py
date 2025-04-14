import logging

from app.database.connection import Database

logger = logging.getLogger(__name__)


class UserModel:
    """
    Model for user data operations.
    Provides database access methods for user data.
    """

    @staticmethod
    def get_all():
        """
        Retrieve all users from the 'users' table in the database.

        Returns:
            list: List of user records
        """
        return Database.execute_query("SELECT * FROM users")

    @staticmethod
    def get_by_username(username):
        """
        Retrieve a user's information from the 'users' table based on the username.

        Args:
            username: The username to search for

        Returns:
            dict: User information or None if not found
        """
        result = Database.execute_query(
            "SELECT * FROM users WHERE username = %s", (username,)
        )
        return result[0] if result else None

    @staticmethod
    def create(user_data):
        """
        Add a new user to the 'users' table in the database.

        Args:
            user_data: Dictionary containing user data

        Returns:
            int: ID of the inserted user
        """
        fields = user_data.keys()
        values = user_data.values()

        placeholders = ", ".join(["%s"] * len(fields))
        columns = ", ".join(fields)

        query = f"INSERT INTO users ({columns}) VALUES ({placeholders}) RETURNING id"
        result = Database.execute_query(query, tuple(values))
        return result[0]["id"] if result else None

    @staticmethod
    def update(username, update_data):
        """
        Update a user in the 'users' table in the database.

        Args:
            username: The username of the user to update
            update_data: Dictionary containing the complete updated user data

        Returns:
            bool: True if user was updated, False otherwise
        """
        set_clause = ", ".join([f"{key} = %s" for key in update_data.keys()])
        query = f"UPDATE users SET {set_clause} WHERE username = %s"
        params = list(update_data.values()) + [username]

        result = Database.execute_query(query, tuple(params), fetch=False)
        return result > 0

    @staticmethod
    def update_fields(username, update_fields):
        """
        Update specific fields of a user in the 'users' table.

        Args:
            username: The username of the user to update
            update_fields: Dictionary containing fields to update

        Returns:
            bool: True if user was updated, False otherwise
        """
        set_clause = ", ".join([f"{key} = %s" for key in update_fields.keys()])
        query = f"UPDATE users SET {set_clause} WHERE username = %s"
        params = list(update_fields.values()) + [username]

        result = Database.execute_query(query, tuple(params), fetch=False)
        return result > 0

    @staticmethod
    def delete(username):
        """
        Delete a user from the 'users' table in the database.

        Args:
            username: The username of the user to delete

        Returns:
            bool: True if user was deleted, False otherwise
        """
        query = "DELETE FROM users WHERE username = %s"
        result = Database.execute_query(query, (username,), fetch=False)
        return result > 0
