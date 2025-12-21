"""
Create Quiz Session Lambda Handler

This Lambda function handles creation of new quiz sessions by authenticated admins.
It validates the admin JWT token, extracts tenant context, and creates a new session
in the DynamoDB QuizSessions table with automatic tenant association.

Endpoint: POST /admin/quiz-sessions
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
from tenant_middleware import require_tenant_admin


# Environment variables
QUIZ_SESSIONS_TABLE = os.environ.get("QUIZ_SESSIONS_TABLE", "MusicQuiz-Sessions")


def lambda_handler(event, context):
    """
    Handle create quiz session requests.

    Expected headers:
        Authorization: Bearer <jwt_token>

    Expected input:
        {
            "title": "Quiz Title",
            "description": "Quiz Description",
            "mediaType": "audio"  // "none", "audio", or "image"
        }

    Returns:
        Success (201):
            {
                "sessionId": "uuid",
                "tenantId": "uuid",
                "title": "Quiz Title",
                "description": "Quiz Description",
                "createdAt": 1234567890,
                "createdBy": "admin_id",
                "roundCount": 0,
                "status": "draft"
            }

        Error (400): Invalid request body or inactive tenant
        Error (401): Missing or invalid token
        Error (403): Insufficient permissions
        Error (404): Tenant not found
        Error (500): Internal server error
    """
    try:
        # Validate admin authentication and extract tenant context
        tenant_context, error = require_tenant_admin(event)
        if error:
            return error

        admin_id = tenant_context.get("adminId")
        tenant_id = tenant_context.get("tenantId")
        role = tenant_context.get("role")

        # For tenant admins, tenant_id is required and already validated
        # For super admins, we need a tenant_id to be provided or use a default
        if not tenant_id and role == "super_admin":
            # Super admins must specify a tenant when creating sessions
            # This could be enhanced to accept tenantId in request body
            return error_response(
                400,
                "MISSING_TENANT_ID",
                "Super admins must specify a tenant ID for session creation",
            )

        # Tenant is already validated by require_tenant_admin if tenant_id exists

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
        title = body.get("title")
        if not title:
            return error_response(
                400,
                "MISSING_FIELDS",
                "Title is required",
                {"required_fields": ["title"]},
            )

        description = body.get("description", "")
        media_type = body.get(
            "mediaType", "audio"
        )  # Default to "audio" for backward compatibility

        # Validate media type
        valid_media_types = ["none", "audio", "image"]
        if media_type not in valid_media_types:
            return error_response(
                400,
                "INVALID_MEDIA_TYPE",
                f"mediaType must be one of: {', '.join(valid_media_types)}",
                {"provided": media_type, "valid": valid_media_types},
            )

        # Generate session ID and timestamp
        session_id = str(uuid.uuid4())
        created_at = str(int(datetime.utcnow().timestamp()))

        # Create session item with tenant context
        session_item = {
            "sessionId": session_id,
            "tenantId": tenant_id,  # Automatically add tenantId from admin's context
            "title": title,
            "description": description,
            "createdBy": admin_id,
            "createdAt": created_at,
            "roundCount": 0,
            "status": "draft",
            "mediaType": media_type,
        }

        # Store session in DynamoDB
        try:
            put_item(QUIZ_SESSIONS_TABLE, session_item)
        except Exception as e:
            print(f"DynamoDB put error: {str(e)}")
            return error_response(
                500, "DATABASE_ERROR", "Failed to create quiz session"
            )

        # Return success response
        response = {
            "statusCode": 201,
            "body": json.dumps(session_item),
        }

        return add_cors_headers(response)

    except Exception as e:
        # Log unexpected errors
        print(f"Unexpected error in create quiz session: {str(e)}")
        import traceback

        traceback.print_exc()

        return error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")
