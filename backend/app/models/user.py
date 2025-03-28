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


def patch_user(username, patch_data):
    """
    Partially update a user in the 'users' collection in the database.
    Unlike update_user, patch_user only updates the specified fields.

    Args:
        username: The username of the user to patch
        patch_data: Dictionary containing fields to update

    Returns:
        tuple: (success, message or error)
    """
    users_collection = get_users_collection()

    # First check if user exists
    existing_user = get_user_by_username(username)
    if not existing_user:
        logger.warning(f"User not found for patch: {username}")
        return False, "User not found"

    # Validate the patch data fields
    try:
        # Create a temporary full user object with the patched fields for validation
        merged_data = {**existing_user, **patch_data}
        user_obj = UserData(**merged_data)

        # Only update the fields provided in patch_data
        update_fields = {}
        for key in patch_data:
            # Get the properly validated value from the full user object
            if key in merged_data:
                update_fields[key] = getattr(user_obj, key)

    except (TypeError, ValueError) as e:
        logger.warning(f"Invalid patch data received: {e}")
        return False, f"Invalid patch data: {str(e)}"

    # Update only the specified fields in the user document
    if update_fields:
        result = users_collection.update_one(
            {"username": username}, {"$set": update_fields}
        )

        if result.matched_count > 0:
            logger.info(
                f"Patched user: {username} with fields: {', '.join(update_fields.keys())}"
            )
            return True, "User patched successfully"
        else:
            return False, "User not found or no changes made"
    else:
        return False, "No valid fields to update"


def update_user(username, update_data):
    """
    Update a user in the 'users' collection in the database.
    Requires all fields to be present for a complete update.

    Args:
        username: The username of the user to update
        update_data: Dictionary containing the complete updated user data

    Returns:
        tuple: (success, message or error)
    """
    users_collection = get_users_collection()

    # First check if user exists
    existing_user = get_user_by_username(username)
    if not existing_user:
        logger.warning(f"User not found for update: {username}")
        return False, "User not found"

    # Validate through UserData class
    try:
        # Create UserData object which automatically validates and converts types
        user_obj = UserData(**update_data)
    except (TypeError, ValueError) as e:
        logger.warning(f"Invalid user update data received: {e}")
        return False, f"Invalid user data: {str(e)}"

    # Convert to dict for database update
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

    # Update the user document
    result = users_collection.update_one(
        {"username": username}, {"$set": validated_user_data}
    )

    if result.matched_count > 0:
        logger.info(f"Updated user: {username}")
        return True, "User updated successfully"
    else:
        return False, "User not found or no changes made"


def delete_user(username):
    """
    Delete a user from the 'users' collection in the database.

    Args:
        username: The username of the user to delete

    Returns:
        tuple: (success, message or error)
    """
    users_collection = get_users_collection()

    # Check if user exists
    existing_user = get_user_by_username(username)
    if not existing_user:
        logger.warning(f"User not found for deletion: {username}")
        return False, "User not found"

    # Delete the user
    result = users_collection.delete_one({"username": username})

    if result.deleted_count > 0:
        logger.info(f"Deleted user: {username}")
        return True, "User deleted successfully"
    else:
        return False, "User not found or could not be deleted"
