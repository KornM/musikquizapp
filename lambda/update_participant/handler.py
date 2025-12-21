"""
Update Participant Lambda Handler

This Lambda function updates a participant's name and avatar.

Endpoint: PUT /admin/quiz-sessions/{sessionId}/participants/{participantId}
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
PARTICIPANTS_TABLE = os.environ.get("PARTICIPANTS_TABLE", "MusicQuiz-Participants")
QUIZ_SESSIONS_TABLE = os.environ.get("QUIZ_SESSIONS_TABLE", "MusicQuiz-Sessions")


def lambda_handler(event, context):
    """
    Handle update participant requests.

    Expected headers:
        Authorization: Bearer <jwt_token>

    Expected path parameters:
        sessionId: UUID of the quiz session
        participantId: UUID of the participant

    Expected input:
        {
            "name": "New Name",
            "avatar": "😎"
        }

    Returns:
        Success (200): Participant updated
        Error (400): Invalid request
        Error (401): Missing or invalid token
        Error (403): Insufficient permissions
        Error (404): Participant not found
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

        # Extract tenant ID from token
        admin_tenant_id = payload.get("tenantId")

        # Extract parameters
        path_parameters = event.get("pathParameters", {})
        session_id = path_parameters.get("sessionId")
        participant_id = path_parameters.get("participantId")

        if not session_id or not participant_id:
            return error_response(
                400,
                "MISSING_PARAMETERS",
                "Session ID and participant ID are required",
            )

        # Validate tenant access to session
        try:
            session = get_item(QUIZ_SESSIONS_TABLE, {"sessionId": session_id})
        except Exception as e:
            print(f"DynamoDB get error for session: {str(e)}")
            return error_response(500, "DATABASE_ERROR", "Failed to retrieve session")

        if not session:
            return error_response(404, "SESSION_NOT_FOUND", "Session not found")

        session_tenant_id = session.get("tenantId")
        if session_tenant_id:
            access_error = validate_tenant_access(tenant_context, session_tenant_id)
            if access_error:
                return access_error

        # Parse request body
        if not event.get("body"):
            return error_response(400, "INVALID_REQUEST", "Request body is required")

        try:
            body = json.loads(event["body"])
        except json.JSONDecodeError:
            return error_response(
                400, "INVALID_JSON", "Request body must be valid JSON"
            )

        name = body.get("name")
        avatar = body.get("avatar")

        if not name or not avatar:
            return error_response(
                400,
                "MISSING_FIELDS",
                "name and avatar are required",
                {"required_fields": ["name", "avatar"]},
            )

        # Check if participant exists
        try:
            participant = get_item(
                PARTICIPANTS_TABLE,
                {"sessionId": session_id, "participantId": participant_id},
            )
        except Exception as e:
            print(f"DynamoDB get error: {str(e)}")
            return error_response(
                500, "DATABASE_ERROR", "Failed to retrieve participant"
            )

        if not participant:
            return error_response(404, "PARTICIPANT_NOT_FOUND", "Participant not found")

        # Update participant
        try:
            update_item(
                PARTICIPANTS_TABLE,
                {"sessionId": session_id, "participantId": participant_id},
                "SET #name = :name, avatar = :avatar",
                {":name": name, ":avatar": avatar},
                {"#name": "name"},  # name is a reserved keyword
            )
        except Exception as e:
            print(f"DynamoDB update error: {str(e)}")
            return error_response(500, "DATABASE_ERROR", "Failed to update participant")

        # Return success response
        response = {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Participant updated successfully",
                    "participantId": participant_id,
                    "name": name,
                    "avatar": avatar,
                }
            ),
        }

        return add_cors_headers(response)

    except Exception as e:
        print(f"Unexpected error in update participant: {str(e)}")
        import traceback

        traceback.print_exc()
        return error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")
