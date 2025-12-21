"""
List Tenant Admins Lambda Handler

This Lambda function handles listing all admins for a specific tenant.
It queries admins by tenantId using the TenantIndex GSI.

Endpoint: GET /super-admin/tenants/{tenantId}/admins
"""

import json
import os
import sys

# Add common utilities to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))

from cors import add_cors_headers
from errors import error_response
from db import query, get_item


# Environment variables
ADMINS_TABLE = os.environ.get("ADMINS_TABLE", "Admins")
TENANTS_TABLE = os.environ.get("TENANTS_TABLE", "Tenants")


def lambda_handler(event, context):
    """
    Handle tenant admin listing requests.

    Path parameters:
        tenantId: UUID of the tenant

    Returns:
        Success (200):
            {
                "admins": [
                    {
                        "adminId": "uuid",
                        "tenantId": "uuid",
                        "username": "admin_username",
                        "email": "admin@example.com",
                        "role": "tenant_admin",
                        "createdAt": "2024-01-01T00:00:00.000Z",
                        "updatedAt": "2024-01-01T00:00:00.000Z"
                    },
                    ...
                ]
            }

        Error (400): Missing tenant ID
        Error (404): Tenant not found
        Error (500): Internal server error
    """
    try:
        # Extract tenantId from path parameters
        tenant_id = event.get("pathParameters", {}).get("tenantId")
        if not tenant_id:
            return error_response(
                400, "MISSING_FIELDS", "Tenant ID is required in path"
            )

        # Check if tenant exists
        try:
            tenant = get_item(TENANTS_TABLE, {"tenantId": tenant_id})
        except Exception as e:
            print(f"DynamoDB get error: {str(e)}")
            return error_response(500, "DATABASE_ERROR", "Failed to query tenant")

        if not tenant:
            return error_response(404, "TENANT_NOT_FOUND", "Tenant does not exist")

        # Query admins by tenantId using TenantIndex GSI
        try:
            admins = query(
                ADMINS_TABLE,
                "tenantId = :tenantId",
                {":tenantId": tenant_id},
                index_name="TenantIndex",
            )
        except Exception as e:
            print(f"DynamoDB query error: {str(e)}")
            return error_response(500, "DATABASE_ERROR", "Failed to query admins")

        # Remove password hashes from response
        safe_admins = []
        for admin in admins:
            safe_admin = {k: v for k, v in admin.items() if k != "passwordHash"}
            safe_admins.append(safe_admin)

        # Return success response
        response = {
            "statusCode": 200,
            "body": json.dumps({"admins": safe_admins}),
        }

        return add_cors_headers(response)

    except Exception as e:
        # Log unexpected errors
        print(f"Unexpected error in list tenant admins: {str(e)}")
        import traceback

        traceback.print_exc()

        return error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")
