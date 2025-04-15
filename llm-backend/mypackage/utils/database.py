import logging

import pandas as pd
import psycopg2
import psycopg2.extras

from config import DATABASE_URL

logger = logging.getLogger(__name__)

# Tables that should not be accessible
RESTRICTED_TABLES = ["users", "auth_tokens"]


class Database:
    """
    Singleton class for managing PostgreSQL database connections and operations.

    This class provides centralized access to the PostgreSQL database, with methods
    for initializing connections, accessing tables, and analyzing table metadata.
    It implements a singleton pattern to ensure a single connection is maintained
    throughout the application.

    Attributes:
        conn: PostgreSQL connection instance
        db: Connection cursor with dictionary factory
    """

    conn = None
    db = None

    @classmethod
    def initialize(cls):
        """
        Initialize the PostgreSQL connection.

        This method establishes a connection to PostgreSQL using the configured
        DATABASE_URL from the config module. It sets up the class-level
        connection and cursor attributes for later use.

        Returns:
            bool: True if connection was successful, False otherwise
        """
        try:
            # Connect to PostgreSQL
            cls.conn = psycopg2.connect(DATABASE_URL)
            # Create a cursor with dictionary factory
            cls.db = cls.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            logger.info("Successfully connected to PostgreSQL")
            return True
        except Exception as e:
            logger.error(f"Error connecting to PostgreSQL: {e}")
            return False

    @classmethod
    def get_table(cls, table_name):
        """
        Get a reference to a PostgreSQL table, if it's not restricted.

        This method checks if the requested table is in the restricted list
        before returning a cursor for it. If the database connection hasn't been
        initialized, it will initialize it first.

        Args:
            table_name (str): Name of the table to retrieve

        Returns:
            str: Table name if accessible, None if the table is restricted
        """
        if table_name in RESTRICTED_TABLES:
            logger.warning(f"Access to restricted table '{table_name}' was denied")
            return None

        if cls.db is None:
            cls.initialize()
        return table_name

    @classmethod
    def list_tables(cls):
        """
        List all accessible (non-restricted) tables in the database.

        This method retrieves the names of all tables in the database
        and filters out any that are in the RESTRICTED_TABLES list.

        Returns:
            list: List of accessible table names
        """
        if cls.db is None:
            cls.initialize()

        cls.db.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        all_tables = [row[0] for row in cls.db.fetchall()]
        return [table for table in all_tables if table not in RESTRICTED_TABLES]

    @classmethod
    def analyze_tables(cls):
        """
        Analyze all accessible tables to extract field information and statistics.

        This method examines each accessible table in the database, identifies
        all fields, and generates statistics about each field (min/max values for
        numerical fields, unique values for categorical fields, etc.).

        Returns:
            dict: Nested dictionary with structure:
                {
                    "table_name": {
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
        tables = cls.list_tables()

        for table_name in tables:
            # Get column information
            cls.db.execute(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}'
            """)
            columns = {row[0]: {"type": row[1]} for row in cls.db.fetchall()}

            # Sample data for analysis
            cls.db.execute(f"SELECT * FROM {table_name} LIMIT 100")
            sample = cls.db.fetchall()

            if not sample:
                result[table_name] = columns
                continue

            # Analyze each field
            for field_name, field_info in columns.items():
                # Get sample values for analysis
                sample_values = [row[field_name] for row in sample if field_name in row]
                non_null_values = [v for v in sample_values if v is not None]

                if not non_null_values:
                    field_info["stats"] = "no non-null values"
                    continue

                # Check if numerical
                if field_info["type"] in (
                    "integer",
                    "bigint",
                    "numeric",
                    "double precision",
                    "real",
                ):
                    cls.db.execute(
                        f"SELECT MIN({field_name}), MAX({field_name}) FROM {table_name}"
                    )
                    min_val, max_val = cls.db.fetchone()
                    field_info["stats"] = {"min": min_val, "max": max_val}

                # Check if datetime
                elif field_info["type"] in ("timestamp", "date", "time"):
                    cls.db.execute(
                        f"SELECT MIN({field_name}), MAX({field_name}) FROM {table_name}"
                    )
                    min_val, max_val = cls.db.fetchone()
                    field_info["stats"] = {"min": str(min_val), "max": str(max_val)}

                # Treat as categorical if fewer than 100 unique values
                else:
                    cls.db.execute(f"""
                        SELECT {field_name} 
                        FROM {table_name} 
                        WHERE {field_name} IS NOT NULL 
                        GROUP BY {field_name} 
                        LIMIT 100
                    """)
                    unique_values = [str(row[0]) for row in cls.db.fetchall()]
                    field_info["stats"] = {"unique_values": unique_values}

            result[table_name] = columns

        return result

    @classmethod
    def execute_query(cls, query, params=None):
        """
        Execute a SQL query and return the results.

        Args:
            query (str): The SQL query to execute
            params (tuple, optional): Parameters for the query

        Returns:
            list: List of dictionaries containing the query results
        """
        if cls.db is None:
            cls.initialize()

        try:
            cls.db.execute(query, params)
            return cls.db.fetchall()
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise


# Initialize common table references
def get_campaign_performance_table():
    """
    Get a reference to the campaign_performance table.

    This is a convenience function for accessing a commonly used table.

    Returns:
        str: Table name for campaign_performance if accessible
    """
    return Database.get_table("campaign_performance")


# Function to check if a table is accessible
def is_table_accessible(table_name):
    """
    Check if a table is accessible (not in the restricted list).

    Args:
        table_name (str): Name of the table to check

    Returns:
        bool: True if the table is accessible, False if it's restricted
    """
    return table_name not in RESTRICTED_TABLES


# Function to convert SQL results to a pandas DataFrame
def query_to_dataframe(query, params=None):
    """
    Execute a SQL query and return the results as a pandas DataFrame.

    Args:
        query (str): The SQL query to execute
        params (tuple, optional): Parameters for the query

    Returns:
        pandas.DataFrame: DataFrame containing the query results

    Raises:
        Exception: If there was an error executing the query
    """
    if not Database.conn or not Database.db:
        Database.initialize()

    try:
        return pd.read_sql_query(query, Database.conn, params=params)
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise


def query_to_dict(query, params=None):
    """
    Execute a SQL query and return the results as a list of dictionaries.

    Args:
        query (str): The SQL query to execute
        params (tuple, optional): Parameters for the query

    Returns:
        list: List of dictionaries containing the query results

    Raises:
        Exception: If there was an error executing the query
    """
    if not Database.conn or not Database.db:
        Database.initialize()

    try:
        cursor = Database.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(query, params)
        results = cursor.fetchall()
        cursor.close()
        return [dict(row) for row in results]
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise


def execute_sql(sql, params=None):
    """
    Execute a SQL command that doesn't return results (INSERT, UPDATE, DELETE).

    Args:
        sql (str): The SQL command to execute
        params (tuple, optional): Parameters for the SQL command

    Returns:
        int: Number of rows affected by the command

    Raises:
        Exception: If there was an error executing the SQL command
    """
    if not Database.conn or not Database.db:
        Database.initialize()

    try:
        cursor = Database.conn.cursor()
        cursor.execute(sql, params)
        rowcount = cursor.rowcount
        Database.conn.commit()
        cursor.close()
        return rowcount
    except Exception as e:
        Database.conn.rollback()
        logger.error(f"Error executing SQL command: {e}")
        raise
