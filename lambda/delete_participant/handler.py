"""
Delete Participant Lambda Handler

This Lambda function deletes a single participant and their answers.

Endpoint: DELETE /admin/quiz-sessions/{sessionId}/participants/{participantId}
"""

import json
import os
import sys

# Add common utilities to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))

from auth import validate_token
from cors import add_cors_headers
from errors import error_response
from db import get_item, delete_item, scan, query
from tenant_middleware import validate_tenant_access
import jwt


# Environment variables
SESSION_PARTICIPATIONS_TABLE = os.environ.get(
    "SESSION_PARTICIPATIONS_TABLE", "SessionParticipations"
)
GLOBAL_PARTICIPANTS_TABLE = os.environ.get(
    "GLOBAL_PARTICIPANTS_TABLE", "GlobalParticipants"
)
PARTICIPANTS_TABLE = os.environ.get("PARTICIPANTS_TABLE", "MusicQuiz-Participants")
ANSWERS_TABLE = os.environ.get("ANSWERS_TABLE", "MusicQuiz-Answers")
QUIZ_SESSIONS_TABLE = os.environ.get("QUIZ_SESSIONS_TABLE", "MusicQuiz-Sessions")


def lambda_handler(event, context):
    """
    Handle delete participant requests.

    Expected headers:
        Authorization: Bearer <jwt_token>

    Expected path parameters:
        sessionId: UUID of the quiz session
        participantId: UUID of the participant

    Returns:
        Success (200): Participant deleted
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

        # Check if participation exists (SessionParticipations table)
        try:
            # Query SessionParticipations by participantId and sessionId
            participations = query(
                SESSION_PARTICIPATIONS_TABLE,
                "participantId = :participantId",
                {":participantId": participant_id},
                index_name="ParticipantIndex",
            )

            # Find the participation for this specific session
            participation = None
            for p in participations:
                if p.get("sessionId") == session_id:
                    participation = p
                    break

            if not participation:
                return error_response(
                    404,
                    "PARTICIPATION_NOT_FOUND",
                    "Participant is not in this session",
                )

            participation_id = participation.get("participationId")

        except Exception as e:
            print(f"DynamoDB query error: {str(e)}")
            return error_response(
                500, "DATABASE_ERROR", "Failed to retrieve participation"
            )

        # Delete participant's answers for this session
        try:
            answers = scan(
                ANSWERS_TABLE,
                filter_expression="participantId = :participantId AND sessionId = :sessionId",
                expression_attribute_values={
                    ":participantId": participant_id,
                    ":sessionId": session_id,
                },
            )

            deleted_answers = 0
            for answer in answers:
                try:
                    delete_item(ANSWERS_TABLE, {"answerId": answer.get("answerId")})
                    deleted_answers += 1
                except Exception as e:
                    print(f"Failed to delete answer: {str(e)}")

        except Exception as e:
            print(f"DynamoDB scan error: {str(e)}")
            # Continue with participation deletion even if answer deletion fails

        # Delete session participation (removes participant from this session)
        try:
            delete_item(
                SESSION_PARTICIPATIONS_TABLE, {"participationId": participation_id}
            )
        except Exception as e:
            print(f"DynamoDB delete error: {str(e)}")
            return error_response(
                500, "DATABASE_ERROR", "Failed to remove participant from session"
            )

        # Return success response
        response = {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Participant removed from session successfully",
                    "participantId": participant_id,
                    "sessionId": session_id,
                    "deletedAnswers": deleted_answers,
                }
            ),
        }

        return add_cors_headers(response)

    except Exception as e:
        print(f"Unexpected error in delete participant: {str(e)}")
        import traceback

        traceback.print_exc()
        return error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")
