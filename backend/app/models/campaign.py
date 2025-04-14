import logging

from app.database.connection import Database

logger = logging.getLogger(__name__)


class CampaignModel:
    """
    Model for campaign data operations.
    Provides database access methods for campaign data.
    """

    @staticmethod
    def get_all(where_conditions=None, columns=None):
        """
        Get all campaign records matching the conditions.

        Args:
            where_conditions: SQL WHERE conditions as a tuple (query_string, params)
            columns: List of columns to include in the result

        Returns:
            list: List of campaign records
        """
        columns_str = "*" if not columns else ", ".join(columns)

        if where_conditions:
            query_string, params = where_conditions
            query = (
                f"SELECT {columns_str} FROM campaign_performance WHERE {query_string}"
            )
            return Database.execute_query(query, params)
        else:
            query = f"SELECT {columns_str} FROM campaign_performance"
            return Database.execute_query(query)

    @staticmethod
    def count(where_conditions=None):
        """
        Count campaign records matching the conditions.

        Args:
            where_conditions: SQL WHERE conditions as a tuple (query_string, params)

        Returns:
            int: Number of matching records
        """
        if where_conditions:
            query_string, params = where_conditions
            query = f"SELECT COUNT(*) FROM campaign_performance WHERE {query_string}"
            result = Database.execute_query(query, params)
        else:
            query = "SELECT COUNT(*) FROM campaign_performance"
            result = Database.execute_query(query)

        return result[0]["count"] if result else 0

    @staticmethod
    def get_paginated(
        where_conditions=None,
        columns=None,
        sort_by="date",
        sort_dir="DESC",
        offset=0,
        limit=20,
    ):
        """
        Get paginated campaign records.

        Args:
            where_conditions: SQL WHERE conditions as a tuple (query_string, params)
            columns: List of columns to include in the result
            sort_by: Field to sort by
            sort_dir: Sort direction ('ASC' or 'DESC')
            offset: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            list: List of campaign records
        """
        columns_str = "*" if not columns else ", ".join(columns)
        sort_direction = (
            "DESC" if sort_dir == -1 or sort_dir.upper() == "DESC" else "ASC"
        )

        if where_conditions:
            query_string, params = where_conditions
            query = f"""
                SELECT {columns_str} 
                FROM campaign_performance 
                WHERE {query_string} 
                ORDER BY {sort_by} {sort_direction}
                LIMIT {limit} OFFSET {offset}
            """
            return Database.execute_query(query, params)
        else:
            query = f"""
                SELECT {columns_str} 
                FROM campaign_performance 
                ORDER BY {sort_by} {sort_direction}
                LIMIT {limit} OFFSET {offset}
            """
            return Database.execute_query(query)

    @staticmethod
    def get_distinct(field, where_conditions=None):
        """
        Get distinct values for a field.

        Args:
            field: Field name to get distinct values for
            where_conditions: SQL WHERE conditions as a tuple (query_string, params)

        Returns:
            list: List of distinct values
        """
        if where_conditions:
            query_string, params = where_conditions
            query = f"SELECT DISTINCT {field} FROM campaign_performance WHERE {query_string}"
            result = Database.execute_query(query, params)
        else:
            query = f"SELECT DISTINCT {field} FROM campaign_performance"
            result = Database.execute_query(query)

        return [record[field] for record in result]

    @staticmethod
    def aggregate(agg_query, params=None):
        """
        Perform a custom aggregation query.

        Args:
            agg_query: SQL aggregation query
            params: Query parameters

        Returns:
            list: Result of the aggregation
        """
        return Database.execute_query(agg_query, params)

    @staticmethod
    def update_many(where_conditions, update_data):
        """
        Update multiple records.

        Args:
            where_conditions: SQL WHERE conditions as a tuple (query_string, params)
            update_data: Dictionary with fields to update

        Returns:
            int: Number of records modified
        """
        set_clause = ", ".join([f"{key} = %s" for key in update_data.keys()])
        query_string, where_params = where_conditions

        query = f"UPDATE campaign_performance SET {set_clause} WHERE {query_string}"
        params = list(update_data.values()) + where_params

        return Database.execute_query(query, tuple(params), fetch=False)

    @staticmethod
    def update_one(where_conditions, update_data):
        """
        Update a single record.

        Args:
            where_conditions: SQL WHERE conditions as a tuple (query_string, params)
            update_data: Dictionary with fields to update

        Returns:
            bool: True if a record was modified, False otherwise
        """
        set_clause = ", ".join([f"{key} = %s" for key in update_data.keys()])
        query_string, where_params = where_conditions

        query = f"""
            UPDATE campaign_performance SET {set_clause} 
            WHERE {query_string}
            LIMIT 1
        """
        params = list(update_data.values()) + where_params

        result = Database.execute_query(query, tuple(params), fetch=False)
        return result > 0

    @staticmethod
    def create(document):
        """
        Insert a new campaign record.

        Args:
            document: Dictionary with data to insert

        Returns:
            int: ID of the inserted record
        """
        fields = document.keys()
        values = document.values()

        placeholders = ", ".join(["%s"] * len(fields))
        columns = ", ".join(fields)

        query = f"INSERT INTO campaign_performance ({columns}) VALUES ({placeholders}) RETURNING id"
        result = Database.execute_query(query, tuple(values))
        return result[0]["id"] if result else None

    @staticmethod
    def create_many(documents):
        """
        Insert multiple campaign records.

        Args:
            documents: List of dictionaries with data to insert

        Returns:
            int: Number of records inserted
        """
        if not documents:
            return 0

        # All dictionaries should have same keys
        sample = documents[0]
        fields = sample.keys()
        columns = ", ".join(fields)

        # Create placeholder groups for each row
        values_list = []
        placeholders_template = "(" + ", ".join(["%s"] * len(fields)) + ")"
        placeholders = []

        for doc in documents:
            values_list.extend([doc[field] for field in fields])
            placeholders.append(placeholders_template)

        placeholders_str = ", ".join(placeholders)
        query = (
            f"INSERT INTO campaign_performance ({columns}) VALUES {placeholders_str}"
        )

        result = Database.execute_query(query, tuple(values_list), fetch=False)
        return result
