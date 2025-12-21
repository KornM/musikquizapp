"""
Admin Login Lambda Handler

This Lambda function handles admin authentication for the Music Quiz application.
It validates admin credentials against the DynamoDB Admins table and returns a JWT token.

Endpoint: POST /admin/login
"""

import json
import os
import sys

# Add common utilities to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))

from auth import generate_token, verify_password
from cors import add_cors_headers
from errors import error_response
from db import query


# Environment variables
ADMINS_TABLE = os.environ.get("ADMINS_TABLE", "MusicQuiz-Admins")


def lambda_handler(event, context):
    """
    Handle admin login requests.

    Expected input:
        {
            "username": "admin_username",
            "password": "admin_password"
        }

    Returns:
        Success (200):
            {
                "token": "jwt_token_string",
                "expiresIn": 86400,
                "tenantId": "uuid"  // Optional, present for tenant admins
            }

        Error (400): Invalid request body
        Error (401): Invalid credentials
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
        username = body.get("username")
        password = body.get("password")

        if not username or not password:
            return error_response(
                400,
                "MISSING_FIELDS",
                "Username and password are required",
                {"required_fields": ["username", "password"]},
            )

        # Query admin by username using GSI
        try:
            admins = query(
                ADMINS_TABLE,
                "username = :username",
                {":username": username},
                index_name="UsernameIndex",
            )
        except Exception as e:
            print(f"DynamoDB query error: {str(e)}")
            return error_response(
                500, "DATABASE_ERROR", "Failed to query admin credentials"
            )

        # Check if admin exists
        if not admins or len(admins) == 0:
            return error_response(
                401, "INVALID_CREDENTIALS", "Invalid username or password"
            )

        admin = admins[0]

        # Verify password
        password_hash = admin.get("passwordHash")
        if not password_hash:
            print(f"Admin {username} has no password hash")
            return error_response(
                500, "INVALID_ADMIN_DATA", "Admin account is not properly configured"
            )

        if not verify_password(password, password_hash):
            return error_response(
                401, "INVALID_CREDENTIALS", "Invalid username or password"
            )

        # Generate JWT token with tenant context
        admin_id = admin.get("adminId")
        tenant_id = admin.get("tenantId")  # May be None for super admins
        role = admin.get(
            "role", "tenant_admin"
        )  # Default to tenant_admin for backward compatibility

        token = generate_token(admin_id, role, tenant_id)

        # Return success response with token and tenant context
        response_body = {
            "token": token,
            "expiresIn": 86400,  # 24 hours in seconds
        }

        # Include tenantId in response if present
        if tenant_id:
            response_body["tenantId"] = tenant_id

        response = {
            "statusCode": 200,
            "body": json.dumps(response_body),
        }

        return add_cors_headers(response)

    except Exception as e:
        # Log unexpected errors
        print(f"Unexpected error in admin login: {str(e)}")
        import traceback

        traceback.print_exc()

        return error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")
