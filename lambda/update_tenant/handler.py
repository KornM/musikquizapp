"""
Update Tenant Lambda Handler

This Lambda function handles tenant updates for the Music Quiz application.
It updates tenant information (name, description, status) in the Tenants table.

Endpoint: PUT /super-admin/tenants/{tenantId}
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
    Handle tenant update requests.

    Expected input:
        Path parameter: tenantId
        Body:
        {
            "name": "Updated Tenant Name",
            "description": "Updated description",
            "status": "active" | "inactive"
        }

    Returns:
        Success (200):
            {
                "tenantId": "uuid",
                "name": "Updated Tenant Name",
                "description": "Updated description",
                "status": "active",
                "createdAt": "2024-01-01T00:00:00.000Z",
                "updatedAt": "2024-01-01T12:00:00.000Z"
            }

        Error (400): Invalid request body or missing tenant ID
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

        # Parse request body
        if not event.get("body"):
            return error_response(400, "INVALID_REQUEST", "Request body is required")

        try:
            body = json.loads(event["body"])
        except json.JSONDecodeError:
            return error_response(
                400, "INVALID_JSON", "Request body must be valid JSON"
            )

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

        # Build update expression
        update_parts = []
        expression_values = {}
        expression_names = {}

        # Update name if provided
        if "name" in body:
            update_parts.append("#name = :name")
            expression_values[":name"] = body["name"]
            expression_names["#name"] = "name"

        # Update description if provided
        if "description" in body:
            update_parts.append("description = :description")
            expression_values[":description"] = body["description"]

        # Update status if provided
        if "status" in body:
            status = body["status"]
            if status not in ["active", "inactive"]:
                return error_response(
                    400,
                    "INVALID_FIELD_VALUE",
                    "Status must be 'active' or 'inactive'",
                )
            update_parts.append("#status = :status")
            expression_values[":status"] = status
            expression_names["#status"] = "status"

        # Always update updatedAt timestamp
        now = datetime.utcnow().isoformat() + "Z"
        update_parts.append("updatedAt = :updatedAt")
        expression_values[":updatedAt"] = now

        if not update_parts:
            return error_response(
                400,
                "INVALID_REQUEST",
                "At least one field (name, description, or status) must be provided",
            )

        # Build update expression
        update_expression = "SET " + ", ".join(update_parts)

        # Update tenant in DynamoDB
        try:
            updated_tenant = update_item(
                TENANTS_TABLE,
                {"tenantId": tenant_id},
                update_expression,
                expression_values,
                expression_names if expression_names else None,
            )
        except Exception as e:
            print(f"DynamoDB update error: {str(e)}")
            return error_response(500, "DATABASE_ERROR", "Failed to update tenant")

        # Return success response
        response = {
            "statusCode": 200,
            "body": json.dumps(updated_tenant),
        }

        return add_cors_headers(response)

    except Exception as e:
        # Log unexpected errors
        print(f"Unexpected error in update tenant: {str(e)}")
        import traceback

        traceback.print_exc()

        return error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")
