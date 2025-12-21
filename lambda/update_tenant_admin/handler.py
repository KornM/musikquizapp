"""
Update Tenant Admin Lambda Handler

This Lambda function handles updating tenant admin information.
It supports updating username, email, and tenantId (reassignment).

Endpoint: PUT /super-admin/admins/{adminId}
"""

import json
import os
import sys
from datetime import datetime

# Add common utilities to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))

from cors import add_cors_headers
from errors import error_response
from db import get_item, update_item, query


# Environment variables
ADMINS_TABLE = os.environ.get("ADMINS_TABLE", "Admins")
TENANTS_TABLE = os.environ.get("TENANTS_TABLE", "Tenants")


def lambda_handler(event, context):
    """
    Handle tenant admin update requests.

    Path parameters:
        adminId: UUID of the admin to update

    Expected input:
        {
            "username": "new_username",  # optional
            "email": "new_email@example.com",  # optional
            "tenantId": "new_tenant_uuid"  # optional
        }

    Returns:
        Success (200):
            {
                "adminId": "uuid",
                "tenantId": "uuid",
                "username": "admin_username",
                "email": "admin@example.com",
                "role": "tenant_admin",
                "createdAt": "2024-01-01T00:00:00.000Z",
                "updatedAt": "2024-01-01T00:00:00.000Z"
            }

        Error (400): Invalid request body or missing admin ID
        Error (404): Admin or tenant not found
        Error (409): Username already exists
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

        # Check if admin exists
        try:
            admin = get_item(ADMINS_TABLE, {"adminId": admin_id})
        except Exception as e:
            print(f"DynamoDB get error: {str(e)}")
            return error_response(500, "DATABASE_ERROR", "Failed to query admin")

        if not admin:
            return error_response(404, "ADMIN_NOT_FOUND", "Admin does not exist")

        # Build update expression
        update_parts = []
        expression_values = {}
        expression_names = {}

        # Update username if provided
        new_username = body.get("username")
        if new_username and new_username != admin.get("username"):
            # Check if new username already exists
            try:
                existing_admins = query(
                    ADMINS_TABLE,
                    "username = :username",
                    {":username": new_username},
                    index_name="UsernameIndex",
                )
            except Exception as e:
                print(f"DynamoDB query error: {str(e)}")
                return error_response(500, "DATABASE_ERROR", "Failed to check username")

            # Filter out the current admin from results
            existing_admins = [a for a in existing_admins if a["adminId"] != admin_id]

            if existing_admins and len(existing_admins) > 0:
                return error_response(
                    409, "DUPLICATE_USERNAME", "Username already exists"
                )

            update_parts.append("#username = :username")
            expression_values[":username"] = new_username
            expression_names["#username"] = "username"

        # Update email if provided
        new_email = body.get("email")
        if new_email is not None and new_email != admin.get("email"):
            update_parts.append("email = :email")
            expression_values[":email"] = new_email

        # Update tenantId if provided (reassignment)
        new_tenant_id = body.get("tenantId")
        if new_tenant_id and new_tenant_id != admin.get("tenantId"):
            # Validate new tenant exists and is active
            try:
                tenant = get_item(TENANTS_TABLE, {"tenantId": new_tenant_id})
            except Exception as e:
                print(f"DynamoDB get error: {str(e)}")
                return error_response(500, "DATABASE_ERROR", "Failed to query tenant")

            if not tenant:
                return error_response(
                    400,
                    "INVALID_TENANT_ASSIGNMENT",
                    "Target tenant does not exist",
                )

            if tenant.get("status") != "active":
                return error_response(
                    400,
                    "TENANT_INACTIVE",
                    "Cannot assign admin to inactive tenant",
                )

            update_parts.append("tenantId = :tenantId")
            expression_values[":tenantId"] = new_tenant_id

        # If no updates, return current admin
        if not update_parts:
            # Remove password hash from response
            safe_admin = {k: v for k, v in admin.items() if k != "passwordHash"}
            response = {
                "statusCode": 200,
                "body": json.dumps(safe_admin),
            }
            return add_cors_headers(response)

        # Add updatedAt timestamp
        now = datetime.utcnow().isoformat() + "Z"
        update_parts.append("updatedAt = :updatedAt")
        expression_values[":updatedAt"] = now

        # Build update expression
        update_expression = "SET " + ", ".join(update_parts)

        # Update admin in DynamoDB
        try:
            updated_admin = update_item(
                ADMINS_TABLE,
                {"adminId": admin_id},
                update_expression,
                expression_values,
                expression_attribute_names=expression_names
                if expression_names
                else None,
            )
        except Exception as e:
            print(f"DynamoDB update error: {str(e)}")
            return error_response(500, "DATABASE_ERROR", "Failed to update admin")

        # Remove password hash from response
        safe_admin = {k: v for k, v in updated_admin.items() if k != "passwordHash"}

        # Return success response
        response = {
            "statusCode": 200,
            "body": json.dumps(safe_admin),
        }

        return add_cors_headers(response)

    except Exception as e:
        # Log unexpected errors
        print(f"Unexpected error in update tenant admin: {str(e)}")
        import traceback

        traceback.print_exc()

        return error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")
