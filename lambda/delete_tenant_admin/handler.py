"""
Delete Tenant Admin Lambda Handler

This Lambda function handles deleting tenant admins.
It removes the admin from the database, effectively invalidating their tokens.

Endpoint: DELETE /super-admin/admins/{adminId}
"""

import json
import os
import sys

# Add common utilities to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))

from cors import add_cors_headers
from errors import error_response
from db import get_item, delete_item


# Environment variables
ADMINS_TABLE = os.environ.get("ADMINS_TABLE", "Admins")


def lambda_handler(event, context):
    """
    Handle tenant admin deletion requests.

    Path parameters:
        adminId: UUID of the admin to delete

    Returns:
        Success (200):
            {
                "message": "Admin deleted successfully",
                "adminId": "uuid"
            }

        Error (400): Missing admin ID
        Error (404): Admin not found
        Error (500): Internal server error
    """
    try:
        # Extract adminId from path parameters
        admin_id = event.get("pathParameters", {}).get("adminId")
        if not admin_id:
            return error_response(400, "MISSING_FIELDS", "Admin ID is required in path")

        # Check if admin exists
        try:
            admin = get_item(ADMINS_TABLE, {"adminId": admin_id})
        except Exception as e:
            print(f"DynamoDB get error: {str(e)}")
            return error_response(500, "DATABASE_ERROR", "Failed to query admin")

        if not admin:
            return error_response(404, "ADMIN_NOT_FOUND", "Admin does not exist")

        # Delete admin from DynamoDB
        try:
            delete_item(ADMINS_TABLE, {"adminId": admin_id})
        except Exception as e:
            print(f"DynamoDB delete error: {str(e)}")
            return error_response(500, "DATABASE_ERROR", "Failed to delete admin")

        # Return success response
        response = {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Admin deleted successfully",
                    "adminId": admin_id,
                }
            ),
        }

        return add_cors_headers(response)

    except Exception as e:
        # Log unexpected errors
        print(f"Unexpected error in delete tenant admin: {str(e)}")
        import traceback

        traceback.print_exc()

        return error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")
