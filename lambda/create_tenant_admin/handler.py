"""
Create Tenant Admin Lambda Handler

This Lambda function handles tenant admin creation for the Music Quiz application.
It creates a new admin user associated with a specific tenant.

Endpoint: POST /super-admin/tenants/{tenantId}/admins
"""

import json
import os
import sys
import uuid
from datetime import datetime

# Add common utilities to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))

from auth import hash_password
from cors import add_cors_headers
from errors import error_response
from db import get_item, put_item, query


# Environment variables
ADMINS_TABLE = os.environ.get("ADMINS_TABLE", "Admins")
TENANTS_TABLE = os.environ.get("TENANTS_TABLE", "Tenants")


def lambda_handler(event, context):
    """
    Handle tenant admin creation requests.

    Expected input:
        {
            "username": "admin_username",
            "password": "admin_password",
            "email": "admin@example.com"  # optional
        }

    Path parameters:
        tenantId: UUID of the tenant

    Returns:
        Success (201):
            {
                "adminId": "uuid",
                "tenantId": "uuid",
                "username": "admin_username",
                "email": "admin@example.com",
                "role": "tenant_admin",
                "createdAt": "2024-01-01T00:00:00.000Z",
                "updatedAt": "2024-01-01T00:00:00.000Z"
            }

        Error (400): Invalid request body or missing required fields
        Error (404): Tenant not found
        Error (409): Username already exists
        Error (500): Internal server error
    """
    try:
        # Extract tenantId from path parameters
        tenant_id = event.get("pathParameters", {}).get("tenantId")
        if not tenant_id:
            return error_response(
                400, "MISSING_FIELDS", "Tenant ID is required in path"
            )

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
        username = body.get("username")
        password = body.get("password")

        if not username or not password:
            return error_response(
                400,
                "MISSING_FIELDS",
                "Username and password are required",
                {"required_fields": ["username", "password"]},
            )

        # Optional email
        email = body.get("email", "")

        # Check if tenant exists and is active
        try:
            tenant = get_item(TENANTS_TABLE, {"tenantId": tenant_id})
        except Exception as e:
            print(f"DynamoDB get error: {str(e)}")
            return error_response(500, "DATABASE_ERROR", "Failed to query tenant")

        if not tenant:
            return error_response(404, "TENANT_NOT_FOUND", "Tenant does not exist")

        if tenant.get("status") != "active":
            return error_response(
                400, "TENANT_INACTIVE", "Cannot create admin for inactive tenant"
            )

        # Check if username already exists
        try:
            existing_admins = query(
                ADMINS_TABLE,
                "username = :username",
                {":username": username},
                index_name="UsernameIndex",
            )
        except Exception as e:
            print(f"DynamoDB query error: {str(e)}")
            return error_response(500, "DATABASE_ERROR", "Failed to check username")

        if existing_admins and len(existing_admins) > 0:
            return error_response(409, "DUPLICATE_USERNAME", "Username already exists")

        # Generate unique admin ID
        admin_id = str(uuid.uuid4())

        # Hash password
        password_hash = hash_password(password)

        # Create timestamp
        now = datetime.utcnow().isoformat() + "Z"

        # Create admin record
        admin = {
            "adminId": admin_id,
            "tenantId": tenant_id,
            "username": username,
            "passwordHash": password_hash,
            "role": "tenant_admin",
            "email": email,
            "createdAt": now,
            "updatedAt": now,
        }

        # Store admin in DynamoDB
        try:
            put_item(ADMINS_TABLE, admin)
        except Exception as e:
            print(f"DynamoDB put error: {str(e)}")
            return error_response(500, "DATABASE_ERROR", "Failed to create admin")

        # Remove password hash from response
        response_admin = {k: v for k, v in admin.items() if k != "passwordHash"}

        # Return success response
        response = {
            "statusCode": 201,
            "body": json.dumps(response_admin),
        }

        return add_cors_headers(response)

    except Exception as e:
        # Log unexpected errors
        print(f"Unexpected error in create tenant admin: {str(e)}")
        import traceback

        traceback.print_exc()

        return error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")
