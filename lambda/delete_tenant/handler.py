"""
Delete Tenant Lambda Handler

This Lambda function handles tenant deletion (soft delete) for the Music Quiz application.
It marks a tenant as inactive rather than physically deleting it.

Endpoint: DELETE /super-admin/tenants/{tenantId}
"""

import json
import os
import sys
from datetime import datetime

# Add common utilities to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))

from cors import add_cors_headers
from errors import error_response
from db import get_item, update_item


# Environment variables
TENANTS_TABLE = os.environ.get("TENANTS_TABLE", "Tenants")


def lambda_handler(event, context):
    """
    Handle tenant deletion requests (soft delete).

    Expected input:
        Path parameter: tenantId

    Returns:
        Success (200):
            {
                "message": "Tenant successfully deleted",
                "tenantId": "uuid"
            }

        Error (400): Missing tenant ID
        Error (404): Tenant not found
        Error (500): Internal server error
    """
    try:
        # Get tenant ID from path parameters
        path_parameters = event.get("pathParameters", {})
        if not path_parameters or not path_parameters.get("tenantId"):
            return error_response(
                400, "MISSING_TENANT_ID", "Tenant ID is required in path"
            )

        tenant_id = path_parameters["tenantId"]

        # Check if tenant exists
        try:
            existing_tenant = get_item(TENANTS_TABLE, {"tenantId": tenant_id})
        except Exception as e:
            print(f"DynamoDB get error: {str(e)}")
            return error_response(500, "DATABASE_ERROR", "Failed to retrieve tenant")

        if not existing_tenant:
            return error_response(
                404, "TENANT_NOT_FOUND", f"Tenant with ID {tenant_id} not found"
            )

        # Soft delete: mark tenant as inactive
        now = datetime.utcnow().isoformat() + "Z"

        try:
            update_item(
                TENANTS_TABLE,
                {"tenantId": tenant_id},
                "SET #status = :status, updatedAt = :updatedAt",
                {":status": "inactive", ":updatedAt": now},
                {"#status": "status"},
            )
        except Exception as e:
            print(f"DynamoDB update error: {str(e)}")
            return error_response(500, "DATABASE_ERROR", "Failed to delete tenant")

        # Return success response
        response = {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Tenant successfully deleted",
                    "tenantId": tenant_id,
                }
            ),
        }

        return add_cors_headers(response)

    except Exception as e:
        # Log unexpected errors
        print(f"Unexpected error in delete tenant: {str(e)}")
        import traceback

        traceback.print_exc()

        return error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")
