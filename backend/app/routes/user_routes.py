import logging
from flask import Blueprint, jsonify, request
from app.models.user import (
    get_all_users,
    get_user_by_username,
    add_user,
    update_user,
    delete_user,
    patch_user,
)

# Create blueprint
user_bp = Blueprint("user_routes", __name__)
logger = logging.getLogger(__name__)


@user_bp.route("/api/users", methods=["GET"])
def users_get():
    """
    Retrieve all users from the 'users' collection in the database.
    If username query parameter is provided, returns a single user instead.
    Converts database documents to validated UserData objects.
    """
    try:
        username = request.args.get("username")
        if username:
            user = get_user_by_username(username)
            if user:
                return jsonify(user)
            else:
                logger.info(f"User not found: {username}")
                return jsonify({"error": "User not found"}), 404
        else:
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


@user_bp.route("/api/users/<username>", methods=["GET"])
def user_get_by_path(username):
    """
    Retrieve a user's information from the 'users' collection based on the username in the path.
    Converts to UserData object for validation and proper typing.
    """
    try:
        user = get_user_by_username(username)
        if user:
            return jsonify(user)
        else:
            logger.info(f"User not found: {username}")
            return jsonify({"error": "User not found"}), 404
    except Exception as e:
        logger.error(f"Error retrieving user: {e}")
        return jsonify({"error": str(e)}), 500


@user_bp.route("/api/users/<username>", methods=["PUT"])
def user_update(username):
    """
    Update a user in the 'users' collection based on the username.
    Uses UserData class for validation of the input data.
    """
    try:
        update_data = request.json
        success, result = update_user(username, update_data)

        if success:
            return jsonify({"message": result})
        else:
            return jsonify({"error": result}), 400
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        return jsonify({"error": str(e)}), 500


@user_bp.route("/api/users/<username>", methods=["DELETE"])
def user_delete(username):
    """
    Delete a user from the 'users' collection based on the username.
    """
    try:
        success, result = delete_user(username)

        if success:
            return jsonify({"message": result})
        else:
            return jsonify({"error": result}), 404
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        return jsonify({"error": str(e)}), 500


@user_bp.route("/api/users/<username>", methods=["PATCH"])
def user_patch(username):
    """
    Partially update a user in the 'users' collection based on the username.
    Unlike PUT, PATCH only updates the specified fields.
    Uses UserData class for validation of the input data.
    """
    try:
        patch_data = request.json
        if not patch_data:
            return jsonify({"error": "Patch data is required"}), 400

        success, result = patch_user(username, patch_data)

        if success:
            return jsonify({"message": result})
        else:
            return jsonify({"error": result}), 400
    except Exception as e:
        logger.error(f"Error patching user: {e}")
        return jsonify({"error": str(e)}), 500
