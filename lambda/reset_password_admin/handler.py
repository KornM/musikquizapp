"""
Reset Admin Password Lambda Handler

This Lambda function handles resetting a tenant admin's password.
It validates the new password, hashes it, and updates the admin record.

Endpoint: POST /super-admin/admins/{adminId}/reset-password
"""

import json
import os
import sys
from datetime import datetime

# Add common utilities to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))

from auth import hash_password
from cors import add_cors_headers
from errors import error_response
from db import get_item, update_item


# Environment variables
ADMINS_TABLE = os.environ.get("ADMINS_TABLE", "Admins")


def validate_password(password):
    """
    Validate password meets minimum requirements.

    Args:
        password (str): Password to validate

    Returns:
        tuple: (is_valid, error_message)
    """
    if not password:
        return False, "Password is required"

    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    return True, None


def lambda_handler(event, context):
    """
    Handle admin password reset requests.

    Path parameters:
        adminId: UUID of the admin whose password to reset

    Expected input:
        {
            "newPassword": "new_secure_password"
        }

    Returns:
        Success (200):
            {
                "message": "Password reset successfully"
            }

        Error (400): Invalid request body, missing fields, or password validation failure
        Error (404): Admin not found
        Error (500): Internal server error
    """
    try:
        # Extract adminId from path parameters
        admin_id = event.get("pathParameters", {}).get("adminId")
        if not admin_id:
            return error_response(400, "MISSING_FIELDS", "Admin ID is required in path")

        # Parse request body
        if not event.get("body"):
            return error_response(400, "INVALID_REQUEST", "Request body is required")

        try:
            body = json.loads(event["body"])
        except json.JSONDecodeError:
            return error_response(
                400, "INVALID_JSON", "Request body must be valid JSON"
            )

        # Validate required fields
        new_password = body.get("newPassword")
        if not new_password:
            return error_response(
                400,
                "MISSING_FIELDS",
                "New password is required",
                {"required_fields": ["newPassword"]},
            )

        # Validate password meets requirements
        is_valid, error_message = validate_password(new_password)
        if not is_valid:
            return error_response(
                400,
                "INVALID_FIELD_VALUE",
                error_message,
            )

        # Check if admin exists
        try:
            admin = get_item(ADMINS_TABLE, {"adminId": admin_id})
        except Exception as e:
            print(f"DynamoDB get error: {str(e)}")
            return error_response(500, "DATABASE_ERROR", "Failed to query admin")

        if not admin:
            return error_response(404, "ADMIN_NOT_FOUND", "Admin does not exist")

        # Hash new password
        password_hash = hash_password(new_password)

        # Update admin record with new password hash
        now = datetime.utcnow().isoformat() + "Z"

        update_expression = "SET passwordHash = :passwordHash, updatedAt = :updatedAt"
        expression_values = {
            ":passwordHash": password_hash,
            ":updatedAt": now,
        }

        # Update admin in DynamoDB
        try:
            update_item(
                ADMINS_TABLE,
                {"adminId": admin_id},
                update_expression,
                expression_values,
            )
        except Exception as e:
            print(f"DynamoDB update error: {str(e)}")
            return error_response(500, "DATABASE_ERROR", "Failed to update password")

        # Return success response
        response = {
            "statusCode": 200,
            "body": json.dumps({"message": "Password reset successfully"}),
        }

        return add_cors_headers(response)

    except Exception as e:
        # Log unexpected errors
        print(f"Unexpected error in reset admin password: {str(e)}")
        import traceback

        traceback.print_exc()

        return error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")
