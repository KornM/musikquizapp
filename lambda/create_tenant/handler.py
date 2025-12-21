"""
Create Tenant Lambda Handler

This Lambda function handles tenant creation for the Music Quiz application.
It creates a new tenant with a unique ID and stores it in the Tenants table.

Endpoint: POST /super-admin/tenants
"""

import json
import os
import sys
import uuid
from datetime import datetime

# Add common utilities to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))

from cors import add_cors_headers
from errors import error_response
from db import put_item


# Environment variables
TENANTS_TABLE = os.environ.get("TENANTS_TABLE", "Tenants")


def lambda_handler(event, context):
    """
    Handle tenant creation requests.

    Expected input:
        {
            "name": "Tenant Name",
            "description": "Optional description"
        }

    Returns:
        Success (201):
            {
                "tenantId": "uuid",
                "name": "Tenant Name",
                "description": "Optional description",
                "status": "active",
                "createdAt": "2024-01-01T00:00:00.000Z",
                "updatedAt": "2024-01-01T00:00:00.000Z"
            }

        Error (400): Invalid request body or missing required fields
        Error (500): Internal server error
    """
    try:
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
        name = body.get("name")
        if not name:
            return error_response(
                400,
                "MISSING_FIELDS",
                "Tenant name is required",
                {"required_fields": ["name"]},
            )

        # Optional description
        description = body.get("description", "")

        # Generate unique tenant ID
        tenant_id = str(uuid.uuid4())

        # Create timestamp
        now = datetime.utcnow().isoformat() + "Z"

        # Create tenant record
        tenant = {
            "tenantId": tenant_id,
            "name": name,
            "description": description,
            "status": "active",
            "createdAt": now,
            "updatedAt": now,
            "settings": {},
        }

        # Store tenant in DynamoDB
        try:
            put_item(TENANTS_TABLE, tenant)
        except Exception as e:
            print(f"DynamoDB put error: {str(e)}")
            return error_response(500, "DATABASE_ERROR", "Failed to create tenant")

        # Return success response
        response = {
            "statusCode": 201,
            "body": json.dumps(tenant),
        }

        return add_cors_headers(response)

    except Exception as e:
        # Log unexpected errors
        print(f"Unexpected error in create tenant: {str(e)}")
        import traceback

        traceback.print_exc()

        return error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")
