"""
Clear Participants Lambda Handler

This Lambda function removes all participants from a session by deleting
their SessionParticipations and associated answers.

Endpoint: DELETE /admin/quiz-sessions/{sessionId}/participants
"""

import json
import os
import sys

# Add common utilities to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))

from auth import validate_token
from cors import add_cors_headers
from errors import error_response
from db import query, get_item, delete_item, scan
from tenant_middleware import validate_tenant_access
import jwt

# Environment variables
SESSION_PARTICIPATIONS_TABLE = os.environ.get(
    "SESSION_PARTICIPATIONS_TABLE", "SessionParticipations"
)
PARTICIPANTS_TABLE = os.environ.get("PARTICIPANTS_TABLE", "MusicQuiz-Participants")
ANSWERS_TABLE = os.environ.get("ANSWERS_TABLE", "MusicQuiz-Answers")
QUIZ_SESSIONS_TABLE = os.environ.get("QUIZ_SESSIONS_TABLE", "MusicQuiz-Sessions")


def lambda_handler(event, context):
    """Handle clear participants requests."""
    try:
        # Validate Authorization
        headers = event.get("headers", {})
        auth_header = headers.get("Authorization") or headers.get("authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return error_response(401, "MISSING_TOKEN", "Authorization required")

        token = auth_header[7:]

        try:
            payload = validate_token(token)
        except jwt.ExpiredSignatureError:
            return error_response(401, "TOKEN_EXPIRED", "Token has expired")
        except jwt.InvalidTokenError:
            return error_response(401, "INVALID_TOKEN", "Invalid token")

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

        # Extract session ID
        path_parameters = event.get("pathParameters", {})
        session_id = path_parameters.get("sessionId")

        if not session_id:
            return error_response(400, "MISSING_SESSION_ID", "Session ID required")

        # Get session to validate tenant access
        try:
            session = get_item(QUIZ_SESSIONS_TABLE, {"sessionId": session_id})
        except Exception as e:
            print(f"DynamoDB get error: {str(e)}")
            return error_response(500, "DATABASE_ERROR", "Failed to retrieve session")

        if not session:
            return error_response(404, "SESSION_NOT_FOUND", "Session not found")

        # Validate tenant access
        session_tenant_id = session.get("tenantId")
        if session_tenant_id:
            access_error = validate_tenant_access(tenant_context, session_tenant_id)
            if access_error:
                return access_error

        deleted_participations = 0
        deleted_answers = 0

        # Get all session participations for this session
        try:
            print(f"Querying SessionParticipations for session: {session_id}")
            participations = query(
                SESSION_PARTICIPATIONS_TABLE,
                "sessionId = :sessionId",
                {":sessionId": session_id},
                index_name="SessionIndex",
            )
            print(f"Found {len(participations)} participations to delete")
        except Exception as e:
            print(f"Query participations error: {str(e)}")
            import traceback

            traceback.print_exc()
            participations = []

        # Get all answers for this session
        try:
            print(f"Scanning answers for session: {session_id}")
            answers = scan(
                ANSWERS_TABLE,
                filter_expression="sessionId = :sessionId",
                expression_attribute_values={":sessionId": session_id},
            )
            print(f"Found {len(answers)} answers to delete")
        except Exception as e:
            print(f"Scan answers error: {str(e)}")
            import traceback

            traceback.print_exc()
            answers = []

        # Delete all answers first
        for answer in answers:
            try:
                delete_item(ANSWERS_TABLE, {"answerId": answer["answerId"]})
                deleted_answers += 1
            except Exception as e:
                print(f"Delete answer error: {str(e)}")

        # Delete all session participations
        for participation in participations:
            try:
                delete_item(
                    SESSION_PARTICIPATIONS_TABLE,
                    {"participationId": participation["participationId"]},
                )
                deleted_participations += 1
            except Exception as e:
                print(f"Delete participation error: {str(e)}")

        print(
            f"Cleared {deleted_participations} participations and {deleted_answers} answers"
        )

        response = {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Participants cleared successfully",
                    "deletedParticipations": deleted_participations,
                    "deletedAnswers": deleted_answers,
                }
            ),
        }

        return add_cors_headers(response)

    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        import traceback

        traceback.print_exc()
        return error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")
