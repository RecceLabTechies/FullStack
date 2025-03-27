import logging
from app.models.data_types import UserData
from app.database.connection import get_users_collection

logger = logging.getLogger(__name__)


def get_all_users():
    """
    Retrieve all users from the 'users' collection in the database.

    Returns:
        list: List of user dictionaries
    """
    users_collection = get_users_collection()
    users_raw = list(users_collection.find({}, {"_id": 0}))

    # Convert raw data to UserData objects for validation and proper typing
    users = []
    for user_raw in users_raw:
        # Create UserData object which automatically handles type conversions
        user_obj = UserData(**user_raw)
        # Convert back to dict for JSON serialization
        users.append(
            {
                "username": user_obj.username,
                "email": user_obj.email,
                "role": user_obj.role,
                "company": user_obj.company,
                "password": user_obj.password,
                "chart_access": user_obj.chart_access,
                "report_generation_access": user_obj.report_generation_access,
                "user_management_access": user_obj.user_management_access,
            }
        )

    return users


def get_user_by_username(username):
    """
    Retrieve a user's information from the 'users' collection based on the username.

    Args:
        username: The username to search for

    Returns:
        dict: User information or None if not found
    """
    users_collection = get_users_collection()
    user_raw = users_collection.find_one(
        {"username": username}, {"_id": 0}
    )  # Exclude the ObjectId from the response

    if user_raw:
        # Create UserData object which automatically handles type conversions
        user_obj = UserData(**user_raw)
        # Convert back to dict for JSON serialization
        user = {
            "username": user_obj.username,
            "email": user_obj.email,
            "role": user_obj.role,
            "company": user_obj.company,
            "password": user_obj.password,
            "chart_access": user_obj.chart_access,
            "report_generation_access": user_obj.report_generation_access,
            "user_management_access": user_obj.user_management_access,
        }
        return user

    return None


def add_user(user_data):
    """
    Add a new user to the 'users' collection in the database.

    Args:
        user_data: Dictionary containing user data

    Returns:
        tuple: (success, message or error)
    """
    users_collection = get_users_collection()

    # Validate through UserData class
    try:
        # Create UserData object which automatically validates and converts types
        user_obj = UserData(**user_data)
    except (TypeError, ValueError) as e:
        logger.warning(f"Invalid user data received: {e}")
        return False, f"Invalid user data: {str(e)}"

    # Convert to dict for database insertion
    validated_user_data = {
        "username": user_obj.username,
        "email": user_obj.email,
        "role": user_obj.role,
        "company": user_obj.company,
        "password": user_obj.password,
        "chart_access": user_obj.chart_access,
        "report_generation_access": user_obj.report_generation_access,
        "user_management_access": user_obj.user_management_access,
    }

    # Access the 'users' collection
    result = users_collection.insert_one(validated_user_data)
    logger.info(f"Added user: {user_obj.username}")
    return True, str(result.inserted_id)
