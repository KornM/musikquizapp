"""
Update Session Lambda Handler

This Lambda function updates a quiz session's properties, including status.
Admins can activate/deactivate sessions.

Endpoint: PUT /admin/quiz-sessions/{sessionId}
"""

import json
import os
import sys

# Add common utilities to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))

from auth import validate_token
from cors import add_cors_headers
from errors import error_response
from db import get_item, update_item
from tenant_middleware import validate_tenant_access
import jwt


# Environment variables
QUIZ_SESSIONS_TABLE = os.environ.get("QUIZ_SESSIONS_TABLE", "MusicQuiz-Sessions")


def lambda_handler(event, context):
    """
    Handle update session requests.

    Expected headers:
        Authorization: Bearer <jwt_token>

    Expected path parameters:
        sessionId: UUID of the quiz session

    Expected body:
        {
            "status": "active" | "draft" | "completed",  # optional
            "title": "string",  # optional
            "description": "string"  # optional
        }

    Returns:
        Success (200): Session updated successfully
        Error (401): Missing or invalid token
        Error (403): Insufficient permissions
        Error (404): Session not found
        Error (500): Internal server error
    """
    try:
        # Validate Authorization header
        headers = event.get("headers", {})
        auth_header = headers.get("Authorization") or headers.get("authorization")

        if not auth_header:
            return error_response(
                401, "MISSING_TOKEN", "Authorization header is required"
            )

        if not auth_header.startswith("Bearer "):
            return error_response(
                401,
                "INVALID_AUTH_FORMAT",
                "Authorization header must be 'Bearer <token>'",
            )

        token = auth_header[7:]

        # Validate JWT token
        try:
            payload = validate_token(token)
        except jwt.ExpiredSignatureError:
            return error_response(401, "TOKEN_EXPIRED", "Token has expired")
        except jwt.InvalidTokenError:
            return error_response(401, "INVALID_TOKEN", "Invalid token")

        # Check if user has admin role
        role = payload.get("role", "admin")
        if role not in ["admin", "tenant_admin", "super_admin"]:
            return error_response(
                403, "INSUFFICIENT_PERMISSIONS", "Admin role required"
            )

        # Extract tenant ID from token and create tenant context
        admin_tenant_id = payload.get("tenantId")
        tenant_context = {
            "adminId": payload.get("sub"),
            "role": role,
            "tenantId": admin_tenant_id,
        }

        # Extract session ID from path parameters
        path_parameters = event.get("pathParameters", {})
        session_id = path_parameters.get("sessionId")

        if not session_id:
            return error_response(
                400, "MISSING_SESSION_ID", "Session ID is required in path"
            )

        # Parse request body
        try:
            body = json.loads(event.get("body", "{}"))
        except json.JSONDecodeError:
            return error_response(
                400, "INVALID_JSON", "Request body must be valid JSON"
            )

        # Check if session exists
        try:
            session = get_item(QUIZ_SESSIONS_TABLE, {"sessionId": session_id})
        except Exception as e:
            print(f"DynamoDB get error: {str(e)}")
            return error_response(
                500, "DATABASE_ERROR", "Failed to retrieve quiz session"
            )

        if not session:
            return error_response(
                404, "SESSION_NOT_FOUND", f"Quiz session {session_id} not found"
            )

        # Validate tenant access
        session_tenant_id = session.get("tenantId")
        if session_tenant_id:
            access_error = validate_tenant_access(tenant_context, session_tenant_id)
            if access_error:
                return access_error

        # Build update expression
        update_parts = []
        expression_values = {}
        expression_names = {}

        # Update status if provided
        if "status" in body:
            status = body["status"]
            if status not in ["draft", "active", "completed"]:
                return error_response(
                    400,
                    "INVALID_STATUS",
                    "Status must be 'draft', 'active', or 'completed'",
                )
            update_parts.append("#status = :status")
            expression_values[":status"] = status
            expression_names["#status"] = "status"

        # Update title if provided
        if "title" in body:
            update_parts.append("title = :title")
            expression_values[":title"] = body["title"]

        # Update description if provided
        if "description" in body:
            update_parts.append("description = :description")
            expression_values[":description"] = body["description"]

        # If no updates provided, return error
        if not update_parts:
            return error_response(
                400, "NO_UPDATES", "At least one field must be provided for update"
            )

        # Add updatedAt timestamp
        from datetime import datetime

        updated_at = str(int(datetime.utcnow().timestamp()))
        update_parts.append("updatedAt = :updatedAt")
        expression_values[":updatedAt"] = updated_at

        # Perform update
        update_expression = "SET " + ", ".join(update_parts)

        try:
            update_item(
                QUIZ_SESSIONS_TABLE,
                {"sessionId": session_id},
                update_expression,
                expression_values,
                expression_names if expression_names else None,
            )
        except Exception as e:
            print(f"DynamoDB update error: {str(e)}")
            return error_response(500, "DATABASE_ERROR", "Failed to update session")

        # Get updated session
        try:
            updated_session = get_item(QUIZ_SESSIONS_TABLE, {"sessionId": session_id})
        except Exception as e:
            print(f"DynamoDB get error: {str(e)}")
            # Return success even if we can't fetch updated session
            updated_session = None

        # Return success response
        response = {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Session updated successfully",
                    "sessionId": session_id,
                    "session": updated_session,
                }
            ),
        }

        return add_cors_headers(response)

    except Exception as e:
        print(f"Unexpected error in update session: {str(e)}")
        import traceback

        traceback.print_exc()
        return error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")
