"""
Start Round Lambda Handler

This Lambda function marks a round as active for a quiz session.
Only one round can be active at a time.

Endpoint: POST /admin/quiz-sessions/{sessionId}/rounds/{roundNumber}/start
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
QUIZ_ROUNDS_TABLE = os.environ.get("QUIZ_ROUNDS_TABLE", "MusicQuiz-Rounds")


def lambda_handler(event, context):
    """
    Handle start round requests.

    Expected headers:
        Authorization: Bearer <jwt_token>

    Expected path parameters:
        sessionId: UUID of the quiz session
        roundNumber: Number of the round to start

    Returns:
        Success (200): Round started
        Error (401): Missing or invalid token
        Error (403): Insufficient permissions
        Error (404): Session or round not found
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

        # Extract parameters
        path_parameters = event.get("pathParameters", {})
        session_id = path_parameters.get("sessionId")
        round_number_str = path_parameters.get("roundNumber")

        if not session_id or not round_number_str:
            return error_response(
                400, "MISSING_PARAMETERS", "Session ID and round number are required"
            )

        try:
            round_number = int(round_number_str)
        except ValueError:
            return error_response(
                400, "INVALID_ROUND_NUMBER", "Round number must be an integer"
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

        # Check if round exists
        try:
            round_item = get_item(
                QUIZ_ROUNDS_TABLE,
                {"sessionId": session_id, "roundNumber": round_number},
            )
        except Exception as e:
            print(f"DynamoDB get error: {str(e)}")
            return error_response(500, "DATABASE_ERROR", "Failed to retrieve round")

        if not round_item:
            return error_response(404, "ROUND_NOT_FOUND", "Round not found")

        # Update session to set current round, start timestamp, and status to active
        from datetime import datetime

        round_started_at = str(int(datetime.utcnow().timestamp()))

        try:
            update_item(
                QUIZ_SESSIONS_TABLE,
                {"sessionId": session_id},
                "SET currentRound = :round, roundStartedAt = :startTime, #status = :status",
                {
                    ":round": round_number,
                    ":startTime": round_started_at,
                    ":status": "active",
                },
                {"#status": "status"},
            )
        except Exception as e:
            print(f"DynamoDB update error: {str(e)}")
            return error_response(500, "DATABASE_ERROR", "Failed to start round")

        # Return success response
        response = {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Round started successfully",
                    "sessionId": session_id,
                    "roundNumber": round_number,
                }
            ),
        }

        return add_cors_headers(response)

    except Exception as e:
        print(f"Unexpected error in start round: {str(e)}")
        import traceback

        traceback.print_exc()
        return error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")
