"""
Get Participants Lambda Handler

This Lambda function retrieves all participants for a quiz session.
It joins SessionParticipations with GlobalParticipants to return
combined data with current profile information.

Endpoint: GET /admin/quiz-sessions/{sessionId}/participants

Validates: Requirements 4.1, 4.2, 4.3, 11.4
"""

import json
import os
import sys
from decimal import Decimal

# Add common utilities to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))

from auth import validate_token
from cors import add_cors_headers
from errors import error_response
from db import query, get_item
import jwt


# Environment variables
PARTICIPANTS_TABLE = os.environ.get("PARTICIPANTS_TABLE", "MusicQuiz-Participants")
SESSION_PARTICIPATIONS_TABLE = os.environ.get(
    "SESSION_PARTICIPATIONS_TABLE", "SessionParticipations"
)
GLOBAL_PARTICIPANTS_TABLE = os.environ.get(
    "GLOBAL_PARTICIPANTS_TABLE", "GlobalParticipants"
)
QUIZ_SESSIONS_TABLE = os.environ.get("QUIZ_SESSIONS_TABLE", "QuizSessions")


# Helper function to convert Decimal to int/float
def decimal_to_number(obj):
    if isinstance(obj, list):
        return [decimal_to_number(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: decimal_to_number(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    else:
        return obj


def lambda_handler(event, context):
    """
    Handle get participants requests.

    Expected headers:
        Authorization: Bearer <jwt_token>

    Expected path parameters:
        sessionId: UUID of the quiz session

    Returns:
        Success (200):
            {
                "participants": [
                    {
                        "participantId": "uuid",
                        "participationId": "uuid",
                        "sessionId": "uuid",
                        "name": "Alice",
                        "avatar": "😀",
                        "totalPoints": 50,
                        "correctAnswers": 5,
                        "joinedAt": "ISO timestamp"
                    }
                ]
            }

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

        # Check if user has admin role (including tenant_admin and super_admin)
        role = payload.get("role")
        if role not in ["admin", "tenant_admin", "super_admin"]:
            return error_response(
                403, "INSUFFICIENT_PERMISSIONS", "Admin role required"
            )

        # Extract tenant ID from token (for tenant admins)
        admin_tenant_id = payload.get("tenantId")

        # Extract session ID from path parameters
        path_parameters = event.get("pathParameters", {})
        session_id = path_parameters.get("sessionId")

        if not session_id:
            return error_response(
                400, "MISSING_SESSION_ID", "Session ID is required in path"
            )

        # Get session to verify it exists and check tenant
        try:
            session = get_item(QUIZ_SESSIONS_TABLE, {"sessionId": session_id})
        except Exception as e:
            print(f"DynamoDB get error for session: {str(e)}")
            return error_response(500, "DATABASE_ERROR", "Failed to retrieve session")

        if not session:
            return error_response(
                404, "SESSION_NOT_FOUND", f"Session {session_id} not found"
            )

        # Verify tenant access for tenant admins
        session_tenant_id = session.get("tenantId")
        if admin_tenant_id and session_tenant_id:
            if admin_tenant_id != session_tenant_id:
                return error_response(
                    403,
                    "CROSS_TENANT_ACCESS",
                    "You do not have permission to access this session",
                )

        # Query SessionParticipations by sessionId using SessionIndex GSI
        try:
            participations = query(
                SESSION_PARTICIPATIONS_TABLE,
                "sessionId = :sessionId",
                {":sessionId": session_id},
                index_name="SessionIndex",
            )
        except Exception as e:
            print(f"DynamoDB query error for participations: {str(e)}")
            return error_response(
                500, "DATABASE_ERROR", "Failed to retrieve session participations"
            )

        # Join with GlobalParticipants to get current profile information
        combined_participants = []
        for participation in participations:
            participant_id = participation.get("participantId")

            # Get global participant profile
            try:
                global_participant = get_item(
                    GLOBAL_PARTICIPANTS_TABLE, {"participantId": participant_id}
                )
            except Exception as e:
                print(f"DynamoDB get error for participant {participant_id}: {str(e)}")
                # Skip this participant if we can't fetch their profile
                continue

            if not global_participant:
                print(f"Warning: Global participant {participant_id} not found")
                # Skip this participant if profile doesn't exist
                continue

            # Filter by tenant if session has tenantId
            if session_tenant_id:
                participant_tenant_id = global_participant.get("tenantId")
                if participant_tenant_id != session_tenant_id:
                    print(
                        f"Warning: Participant {participant_id} tenant mismatch, skipping"
                    )
                    continue

            # Combine participation data with global profile
            combined = {
                "participantId": participant_id,
                "participationId": participation.get("participationId"),
                "sessionId": session_id,
                "name": global_participant.get("name"),
                "avatar": global_participant.get("avatar"),
                "totalPoints": participation.get("totalPoints", 0),
                "correctAnswers": participation.get("correctAnswers", 0),
                "joinedAt": participation.get("joinedAt"),
            }

            combined_participants.append(combined)

        # Convert Decimal types
        combined_participants = decimal_to_number(combined_participants)

        # Sort by total points descending
        combined_participants.sort(key=lambda x: x.get("totalPoints", 0), reverse=True)

        # Return success response
        response = {
            "statusCode": 200,
            "body": json.dumps({"participants": combined_participants}),
        }

        return add_cors_headers(response)

    except Exception as e:
        print(f"Unexpected error in get participants: {str(e)}")
        import traceback

        traceback.print_exc()
        return error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")
