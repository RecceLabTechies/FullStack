import logging

from app.database.connection import Database

logger = logging.getLogger(__name__)


class ProphetPredictionModel:
    """
    Model for prophet prediction data operations.
    Provides database access methods for prophet prediction data.
    """

    @staticmethod
    def get_all():
        """
        Retrieve all prophet predictions from the 'prophet_predictions' table in the database.

        Returns:
            list: List of prophet prediction records
        """
        return Database.execute_query("SELECT * FROM prophet_predictions ORDER BY date")

    @staticmethod
    def get_by_date(date):
        """
        Retrieve prophet prediction data for a specific date.

        Args:
            date: The timestamp to search for

        Returns:
            dict: Prophet prediction data or None if not found
        """
        result = Database.execute_query(
            "SELECT * FROM prophet_predictions WHERE date = %s", (date,)
        )
        return result[0] if result else None

    @staticmethod
    def get_date_range(start_date, end_date):
        """
        Retrieve prophet prediction data within a date range.

        Args:
            start_date: Start timestamp for the date range
            end_date: End timestamp for the date range

        Returns:
            list: List of prophet prediction data records within the date range
        """
        return Database.execute_query(
            "SELECT * FROM prophet_predictions WHERE date >= %s AND date <= %s ORDER BY date",
            (start_date, end_date),
        )

    @staticmethod
    def create(prediction_data):
        """
        Add a new prophet prediction data record to the table.

        Args:
            prediction_data: Dictionary containing prophet prediction data

        Returns:
            int: ID of the inserted record
        """
        fields = prediction_data.keys()
        values = prediction_data.values()

        placeholders = ", ".join(["%s"] * len(fields))
        columns = ", ".join(fields)

        query = f"INSERT INTO prophet_predictions ({columns}) VALUES ({placeholders}) RETURNING id"
        result = Database.execute_query(query, tuple(values))
        return result[0]["id"] if result else None

    @staticmethod
    def create_many(prediction_data_list):
        """
        Add multiple prophet prediction data records to the table.

        Args:
            prediction_data_list: List of dictionaries containing prophet prediction data

        Returns:
            int: Number of records inserted
        """
        if not prediction_data_list:
            return 0

        # All dictionaries should have same keys
        sample = prediction_data_list[0]
        fields = sample.keys()
        columns = ", ".join(fields)

        # Create placeholder groups for each row
        values_list = []
        placeholders_template = "(" + ", ".join(["%s"] * len(fields)) + ")"
        placeholders = []

        for data in prediction_data_list:
            values_list.extend([data[field] for field in fields])
            placeholders.append(placeholders_template)

        placeholders_str = ", ".join(placeholders)
        query = f"INSERT INTO prophet_predictions ({columns}) VALUES {placeholders_str}"

        result = Database.execute_query(query, tuple(values_list), fetch=False)
        return result

    @staticmethod
    def update(date, update_data):
        """
        Update a prophet prediction data record in the table.

        Args:
            date: The timestamp of the record to update
            update_data: Dictionary containing the updated data

        Returns:
            bool: True if record was updated, False otherwise
        """
        set_clause = ", ".join([f"{key} = %s" for key in update_data.keys()])
        query = f"UPDATE prophet_predictions SET {set_clause} WHERE date = %s"
        params = list(update_data.values()) + [date]

        result = Database.execute_query(query, tuple(params), fetch=False)
        return result > 0

    @staticmethod
    def delete(date):
        """
        Delete a prophet prediction data record from the table.

        Args:
            date: The timestamp of the record to delete

        Returns:
            bool: True if record was deleted, False otherwise
        """
        query = "DELETE FROM prophet_predictions WHERE date = %s"
        result = Database.execute_query(query, (date,), fetch=False)
        return result > 0

    @staticmethod
    def delete_all():
        """
        Delete all prophet prediction data records from the table.

        Returns:
            int: Number of records deleted
        """
        query = "DELETE FROM prophet_predictions"
        result = Database.execute_query(query, fetch=False)
        return result
