import logging

from flask import Blueprint, jsonify, request
from marshmallow import EXCLUDE, Schema, ValidationError, fields, validate

from app.data_types import UserData
from app.services.user_service import (
    add_user,
    delete_user,
    get_all_users,
    get_user_by_username,
    patch_user,
    update_user,
)

# Create blueprint
user_bp = Blueprint("user_routes", __name__)
logger = logging.getLogger(__name__)


# Define Marshmallow schemas for validation
class UserSchema(Schema):
    """Schema for validating complete user data, aligned with UserData class"""

    username = fields.String(required=True, validate=validate.Length(min=3, max=50))
    email = fields.Email(required=True)
    role = fields.String(required=True)
    company = fields.String(required=True)
    password = fields.String(required=True, validate=validate.Length(min=8))
    chart_access = fields.Boolean(default=False)
    report_generation_access = fields.Boolean(default=False)
    user_management_access = fields.Boolean(default=False)

    class Meta:
        # Unknown fields will be excluded instead of raising errors
        unknown = EXCLUDE

    def convert_to_user_data(self, data):
        """Convert validated data to UserData object"""
        return UserData(**data)


class UserPatchSchema(Schema):
    """Schema for validating partial user updates"""

    email = fields.Email()
    role = fields.String()
    company = fields.String()
    password = fields.String(validate=validate.Length(min=8))
    chart_access = fields.Boolean()
    report_generation_access = fields.Boolean()
    user_management_access = fields.Boolean()

    class Meta:
        unknown = EXCLUDE


def error_response(status_code, message, error_type=None):
    """Helper function to create standardized error responses"""
    response = {"error": {"status": status_code, "message": message}}
    if error_type:
        response["error"]["type"] = error_type
    return jsonify(response), status_code


def validation_error_response(validation_err):
    """Formats marshmallow validation errors into standard error response"""
    return error_response(
        400,
        "Validation error",
        {"type": "validation_error", "details": validation_err.messages},
    )


@user_bp.route("/api/v1/users", methods=["GET"])
def users_get():
    """
    Retrieve all users from the 'users' table in the database.
    If username query parameter is provided, returns a single user instead.
    Converts database records to validated UserData objects.
    """
    try:
        username = request.args.get("username")
        if username:
            user = get_user_by_username(username)
            if user:
                return jsonify(user)
            else:
                logger.info(f"User not found: {username}")
                return error_response(
                    404, f"User '{username}' not found", "resource_not_found"
                )
        else:
            users = get_all_users()
            return jsonify(users)
    except Exception as e:
        logger.error(f"Error retrieving users: {e}")
        return error_response(500, f"Internal server error: {str(e)}", "server_error")


@user_bp.route("/api/v1/users", methods=["POST"])
def users_post():
    """
    Add a new user to the 'users' table in the database.
    Uses Marshmallow schema for validation of the input data.
    """
    try:
        # Get request data
        user_data = request.json
        if not user_data:
            return error_response(400, "Request body is required", "missing_data")

        # Validate with Marshmallow schema
        try:
            schema = UserSchema()
            validated_data = schema.load(user_data)
            # Convert to UserData for consistent typing
            user_data_obj = schema.convert_to_user_data(validated_data)
        except ValidationError as err:
            return validation_error_response(err)

        # Process validated data
        success, result = add_user(user_data_obj.__dict__)

        if success:
            return jsonify({"message": "User added successfully", "id": result})
        else:
            return error_response(400, result, "validation_error")
    except Exception as e:
        logger.error(f"Error adding user: {e}")
        return error_response(500, f"Internal server error: {str(e)}", "server_error")


@user_bp.route("/api/v1/users/<username>", methods=["GET"])
def user_get_by_path(username):
    """
    Retrieve a user's information from the 'users' table based on the username in the path.
    Converts to UserData object for validation and proper typing.
    """
    try:
        user = get_user_by_username(username)
        if user:
            return jsonify(user)
        else:
            logger.info(f"User not found: {username}")
            return error_response(
                404, f"User '{username}' not found", "resource_not_found"
            )
    except Exception as e:
        logger.error(f"Error retrieving user: {e}")
        return error_response(500, f"Internal server error: {str(e)}", "server_error")


@user_bp.route("/api/v1/users/<username>", methods=["PUT"])
def user_update(username):
    """
    Update a user in the 'users' table based on the username.
    Uses Marshmallow schema for validation of the input data.
    """
    try:
        # Get request data
        update_data = request.json
        if not update_data:
            return error_response(400, "Request body is required", "missing_data")

        # Validate with Marshmallow schema
        try:
            schema = UserSchema()
            validated_data = schema.load(update_data)
            # Convert to UserData for consistent typing
            user_data_obj = schema.convert_to_user_data(validated_data)
        except ValidationError as err:
            return validation_error_response(err)

        # Process validated data
        success, result = update_user(username, user_data_obj.__dict__)

        if success:
            return jsonify({"message": result})
        else:
            return error_response(400, result, "validation_error")
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        return error_response(500, f"Internal server error: {str(e)}", "server_error")


@user_bp.route("/api/v1/users/<username>", methods=["DELETE"])
def user_delete(username):
    """
    Delete a user from the 'users' table based on the username.
    """
    try:
        success, result = delete_user(username)

        if success:
            return jsonify({"message": result})
        else:
            return error_response(404, result, "resource_not_found")
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        return error_response(500, f"Internal server error: {str(e)}", "server_error")


@user_bp.route("/api/v1/users/<username>", methods=["PATCH"])
def user_patch(username):
    """
    Partially update a user in the 'users' table based on the username.
    Unlike PUT, PATCH only updates the specified fields.
    Uses Marshmallow schema for validation of the input data.
    """
    try:
        # Get request data
        patch_data = request.json
        if not patch_data:
            return error_response(400, "Patch data is required", "missing_data")

        # Validate with Marshmallow schema for partial updates
        try:
            schema = UserPatchSchema()
            validated_data = schema.load(patch_data)

            # If no valid fields were provided after validation
            if not validated_data:
                return error_response(
                    400, "No valid fields to update", "validation_error"
                )

            # Get current user data for proper type conversion
            current_user = get_user_by_username(username)
            if not current_user:
                return error_response(
                    404, f"User '{username}' not found", "resource_not_found"
                )

            # Apply patch data to current user data
            for key, value in validated_data.items():
                current_user[key] = value

            # Convert to UserData object for type conversion
            user_data_obj = UserData(**current_user)

        except ValidationError as err:
            return validation_error_response(err)

        # Process validated data
        success, result = patch_user(username, user_data_obj.__dict__)

        if success:
            return jsonify({"message": result})
        else:
            return error_response(400, result, "validation_error")
    except Exception as e:
        logger.error(f"Error patching user: {e}")
        return error_response(500, f"Internal server error: {str(e)}", "server_error")
