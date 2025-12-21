"""
Register Global Participant Lambda Handler

This Lambda function handles global participant registration for tenants.
It validates the tenant exists and creates a global participant record.

Endpoint: POST /participants/register
"""

import json
import os
import sys
import uuid
from datetime import datetime

# Add common utilities to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))

from auth import generate_token
from cors import add_cors_headers
from errors import error_response
from db import get_item, put_item


# Environment variables
TENANTS_TABLE = os.environ.get("TENANTS_TABLE", "Tenants")
GLOBAL_PARTICIPANTS_TABLE = os.environ.get(
    "GLOBAL_PARTICIPANTS_TABLE", "GlobalParticipants"
)


def lambda_handler(event, context):
    """
    Handle global participant registration requests.

    Expected input:
        {
            "tenantId": "uuid",
            "name": "Participant Name",
            "avatar": "😀"
        }

    Returns:
        Success (201):
            {
                "participantId": "uuid",
                "tenantId": "uuid",
                "name": "Participant Name",
                "avatar": "😀",
                "token": "jwt_token",
                "createdAt": "2024-01-01T00:00:00Z"
            }

        Error (400): Invalid request body or missing fields
        Error (404): Tenant not found
        Error (403): Tenant is inactive
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
        tenant_id = body.get("tenantId")
        name = body.get("name")
        avatar = body.get("avatar", "😀")  # Default avatar if not provided

        if not tenant_id:
            return error_response(
                400,
                "MISSING_FIELDS",
                "tenantId is required",
                {"required_fields": ["tenantId"]},
            )

        if not name:
            return error_response(
                400,
                "MISSING_FIELDS",
                "name is required",
                {"required_fields": ["name"]},
            )

        # Check if tenant exists and is active
        try:
            tenant = get_item(TENANTS_TABLE, {"tenantId": tenant_id})
        except Exception as e:
            print(f"DynamoDB get error: {str(e)}")
            return error_response(500, "DATABASE_ERROR", "Failed to retrieve tenant")

        if not tenant:
            return error_response(
                404, "TENANT_NOT_FOUND", f"Tenant {tenant_id} not found"
            )

        # Validate tenant is active
        if tenant.get("status") != "active":
            return error_response(
                403, "TENANT_INACTIVE", f"Tenant {tenant_id} is not active"
            )

        # Generate participant ID and timestamp
        participant_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat() + "Z"

        # Generate participant token with participantId and tenantId
        token = generate_token(participant_id, "participant", tenant_id)

        # Create global participant item
        participant_item = {
            "participantId": participant_id,
            "tenantId": tenant_id,
            "name": name,
            "avatar": avatar,
            "token": token,
            "createdAt": created_at,
            "updatedAt": created_at,
        }

        # Store participant in GlobalParticipants table
        try:
            put_item(GLOBAL_PARTICIPANTS_TABLE, participant_item)
        except Exception as e:
            print(f"DynamoDB put error: {str(e)}")
            return error_response(
                500, "DATABASE_ERROR", "Failed to register participant"
            )

        # Return success response
        response = {
            "statusCode": 201,
            "body": json.dumps(participant_item),
        }

        return add_cors_headers(response)

    except Exception as e:
        # Log unexpected errors
        print(f"Unexpected error in register global participant: {str(e)}")
        import traceback

        traceback.print_exc()

        return error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")
