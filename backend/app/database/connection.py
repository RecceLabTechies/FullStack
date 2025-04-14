import logging

from psycopg2 import pool
from psycopg2.extras import RealDictCursor

from app.config import DATABASE_URL

logger = logging.getLogger(__name__)


class Database:
    connection_pool = None

    @classmethod
    def initialize(cls):
        """Initialize PostgreSQL connection pool"""
        try:
            # Create a connection pool
            cls.connection_pool = pool.ThreadedConnectionPool(
                minconn=1, maxconn=10, dsn=DATABASE_URL
            )
            # Test the connection
            with cls.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
            logger.info("Successfully connected to PostgreSQL")
            return True
        except Exception as e:
            logger.error(f"Error connecting to PostgreSQL: {e}")
            return False

    @classmethod
    def get_connection(cls):
        """Get a connection from the pool"""
        if cls.connection_pool is None:
            cls.initialize()
        return cls.connection_pool.getconn()

    @classmethod
    def release_connection(cls, conn):
        """Return a connection to the pool"""
        if cls.connection_pool is not None:
            cls.connection_pool.putconn(conn)

    @classmethod
    def execute_query(cls, query, params=None, fetch=True):
        """Execute a query and return results"""
        conn = cls.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                # Always commit for non-SELECT queries
                if not query.strip().upper().startswith("SELECT"):
                    conn.commit()
                if fetch:
                    result = cursor.fetchall()
                    return result
                return cursor.rowcount
        except Exception as e:
            conn.rollback()
            logger.error(f"Query execution error: {e}")
            raise e
        finally:
            cls.release_connection(conn)

    @classmethod
    def list_tables(cls):
        """List all tables in the database"""
        query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """
        return [record["table_name"] for record in cls.execute_query(query)]

    @classmethod
    def delete_table_data(cls, table_name):
        """Safely delete data from a table"""
        if table_name == "users":
            raise ValueError("User table data cannot be deleted")

        if table_name in ["campaign_performance", "prophet_predictions"]:
            # Clear records but keep table structure
            query = f"DELETE FROM {table_name}"
            result = cls.execute_query(query, fetch=False)
            logger.info(f"Cleared {result} records from {table_name}")
        else:
            # Use TRUNCATE for faster deletion
            query = f"TRUNCATE TABLE {table_name} RESTART IDENTITY"
            cls.execute_query(query, fetch=False)
            logger.info(f"Truncated table {table_name}")

    @classmethod
    def bulk_insert(cls, table_name, records):
        """
        Insert multiple records into a table

        Args:
            table_name: Name of the table
            records: List of record dictionaries

        Returns:
            int: Number of records inserted
        """
        if not records:
            return 0

        # All dictionaries should have same keys
        sample = records[0]
        fields = sample.keys()
        columns = ", ".join(fields)

        # Create placeholder groups for each row
        values_list = []
        placeholders_template = "(" + ", ".join(["%s"] * len(fields)) + ")"
        placeholders = []

        # Numeric field names that should have empty strings converted to None
        numeric_fields = ["ad_spend", "views", "leads", "new_accounts", "revenue"]

        for record in records:
            # Convert empty strings to None for numeric fields
            row_values = []
            for field in fields:
                value = record[field]
                # Convert empty strings to None for numeric fields
                if value == "" and field in numeric_fields:
                    row_values.append(None)
                else:
                    row_values.append(value)
            
            values_list.extend(row_values)
            placeholders.append(placeholders_template)

        placeholders_str = ", ".join(placeholders)
        query = f"INSERT INTO {table_name} ({columns}) VALUES {placeholders_str}"

        result = cls.execute_query(query, tuple(values_list), fetch=False)
        return result


# Helper functions to get data from tables
def get_users():
    """Get all users"""
    return Database.execute_query("SELECT * FROM users")


def get_user_by_email(email):
    """Get user by email"""
    return Database.execute_query("SELECT * FROM users WHERE email = %s", (email,))


def get_campaign_performance():
    """Get all campaign performance data"""
    return Database.execute_query("SELECT * FROM campaign_performance")


def get_prophet_predictions():
    """Get all prophet predictions"""
    return Database.execute_query("SELECT * FROM prophet_predictions")
