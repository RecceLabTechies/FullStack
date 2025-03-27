import logging
from flask import Blueprint, jsonify, request
from app.models.user import get_all_users, get_user_by_username, add_user

# Create blueprint
user_bp = Blueprint("user_routes", __name__)
logger = logging.getLogger(__name__)


@user_bp.route("/api/users", methods=["GET"])
def users_get():
    """
    Retrieve all users from the 'users' collection in the database.
    Converts database documents to validated UserData objects.
    """
    try:
        users = get_all_users()
        return jsonify(users)
    except Exception as e:
        logger.error(f"Error retrieving users: {e}")
        return jsonify({"error": str(e)}), 500


@user_bp.route("/api/users", methods=["POST"])
def users_post():
    """
    Add a new user to the 'users' collection in the database.
    Uses UserData class for validation of the input data.
    """
    try:
        user_data = request.json
        success, result = add_user(user_data)

        if success:
            return jsonify({"message": "User added successfully", "id": result})
        else:
            return jsonify({"error": result}), 400
    except Exception as e:
        logger.error(f"Error adding user: {e}")
        return jsonify({"error": str(e)}), 500


@user_bp.route("/api/user", methods=["GET"])
def user_get():
    """
    Retrieve a user's information from the 'users' collection based on the username.
    Converts to UserData object for validation and proper typing.
    """
    try:
        username = request.args.get("username")
        if not username:
            return jsonify({"error": "Username query parameter is required"}), 400

        user = get_user_by_username(username)
        if user:
            return jsonify(user)
        else:
            logger.info(f"User not found: {username}")
            return jsonify({"error": "User not found"}), 404
    except Exception as e:
        logger.error(f"Error retrieving user: {e}")
        return jsonify({"error": str(e)}), 500
