"""
Join Session Lambda Handler

This Lambda function handles participant joining quiz sessions.
It validates the participant authentication, verifies the session exists and belongs
to the participant's tenant, and creates a SessionParticipation record (idempotent).

Endpoint: POST /sessions/{sessionId}/join

Validates: Requirements 3.1, 3.2, 3.3, 3.4, 11.2
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
from db import get_item, put_item, query
from participant_middleware import (
    require_participant_auth,
    validate_participant_tenant_access,
)


# Environment variables
QUIZ_SESSIONS_TABLE = os.environ.get("QUIZ_SESSIONS_TABLE", "QuizSessions")
SESSION_PARTICIPATIONS_TABLE = os.environ.get(
    "SESSION_PARTICIPATIONS_TABLE", "SessionParticipations"
)


def lambda_handler(event, context):
    """
    Handle session join requests from authenticated participants.

    Expected path parameters:
        sessionId: UUID of the session to join

    Returns:
        Success (200 or 201):
            {
                "participationId": "uuid",
                "participantId": "uuid",
                "sessionId": "uuid",
                "tenantId": "uuid",
                "joinedAt": "ISO timestamp",
                "totalPoints": 0,
                "correctAnswers": 0
            }

        Error (401): Missing or invalid authentication token
        Error (403): Cross-tenant access attempt
        Error (404): Session not found or participant not found
        Error (500): Internal server error
    """
    try:
        # Require participant authentication
        participant_context, error = require_participant_auth(event)
        if error:
            return error

        participant_id = participant_context["participantId"]
        participant_tenant_id = participant_context["tenantId"]

        # Extract sessionId from path parameters
        path_parameters = event.get("pathParameters", {})
        session_id = path_parameters.get("sessionId")

        if not session_id:
            return error_response(
                400, "MISSING_FIELDS", "sessionId is required in path"
            )

        # Verify session exists
        try:
            session = get_item(QUIZ_SESSIONS_TABLE, {"sessionId": session_id})
        except Exception as e:
            print(f"DynamoDB get error for session {session_id}: {str(e)}")
            return error_response(
                500, "DATABASE_ERROR", "Failed to retrieve quiz session"
            )

        if not session:
            return error_response(
                404, "SESSION_NOT_FOUND", f"Quiz session {session_id} not found"
            )

        # Verify session belongs to participant's tenant
        session_tenant_id = session.get("tenantId")
        if not session_tenant_id:
            # For backward compatibility, if session has no tenantId, allow access
            print(
                f"Warning: Session {session_id} has no tenantId, allowing access for backward compatibility"
            )
        else:
            # Validate tenant access
            access_error = validate_participant_tenant_access(
                participant_context, session_tenant_id
            )
            if access_error:
                return access_error

        # Check if participation already exists (idempotent operation)
        try:
            existing_participations = query(
                SESSION_PARTICIPATIONS_TABLE,
                "participantId = :participantId",
                {":participantId": participant_id},
                index_name="ParticipantIndex",
            )

            # Filter for this specific session
            existing_participation = None
            for participation in existing_participations:
                if participation.get("sessionId") == session_id:
                    existing_participation = participation
                    break

            if existing_participation:
                # Return existing participation (idempotent)
                print(
                    f"Participation already exists for participant {participant_id} in session {session_id}"
                )
                response = {
                    "statusCode": 200,
                    "body": json.dumps(existing_participation),
                }
                return add_cors_headers(response)

        except Exception as e:
            print(f"DynamoDB query error checking existing participation: {str(e)}")
            # Continue to create new participation if query fails
            pass

        # Generate unique participationId
        participation_id = str(uuid.uuid4())

        # Record joinedAt timestamp
        joined_at = datetime.utcnow().isoformat() + "Z"

        # Create SessionParticipation record
        participation_item = {
            "participationId": participation_id,
            "participantId": participant_id,
            "sessionId": session_id,
            "tenantId": session_tenant_id or participant_tenant_id,
            "joinedAt": joined_at,
            "totalPoints": 0,
            "correctAnswers": 0,
        }

        # Store participation in DynamoDB
        try:
            put_item(SESSION_PARTICIPATIONS_TABLE, participation_item)
        except Exception as e:
            print(f"DynamoDB put error: {str(e)}")
            return error_response(
                500, "DATABASE_ERROR", "Failed to create session participation"
            )

        # Return success response (201 Created)
        response = {
            "statusCode": 201,
            "body": json.dumps(participation_item),
        }

        return add_cors_headers(response)

    except Exception as e:
        # Log unexpected errors
        print(f"Unexpected error in join session: {str(e)}")
        import traceback

        traceback.print_exc()

        return error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")
