"""
Register Participant Lambda Handler

This Lambda function handles participant registration for quiz sessions.
It validates the session exists and creates a participant record.

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
QUIZ_SESSIONS_TABLE = os.environ.get("QUIZ_SESSIONS_TABLE", "MusicQuiz-Sessions")
PARTICIPANTS_TABLE = os.environ.get("PARTICIPANTS_TABLE", "MusicQuiz-Participants")


def lambda_handler(event, context):
    """
    Handle participant registration requests.

    Expected input:
        {
            "sessionId": "uuid",
            "name": "Participant Name"
        }

    Returns:
        Success (201):
            {
                "participantId": "uuid",
                "sessionId": "uuid",
                "name": "Participant Name",
                "token": "jwt_token",
                "registeredAt": 1234567890
            }

        Error (400): Invalid request body
        Error (404): Session not found
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
        session_id = body.get("sessionId")
        name = body.get("name")

        if not session_id:
            return error_response(
                400,
                "MISSING_FIELDS",
                "sessionId is required",
                {"required_fields": ["sessionId"]},
            )

        if not name:
            return error_response(
                400,
                "MISSING_FIELDS",
                "name is required",
                {"required_fields": ["name"]},
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

        # Generate participant ID and timestamp
        participant_id = str(uuid.uuid4())
        registered_at = int(datetime.utcnow().timestamp())

        # Generate participant token
        token = generate_token(participant_id, "participant")

        # Create participant item
        participant_item = {
            "participantId": participant_id,
            "sessionId": session_id,
            "name": name,
            "token": token,
            "registeredAt": registered_at,
        }

        # Store participant in DynamoDB
        try:
            put_item(PARTICIPANTS_TABLE, participant_item)
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
        print(f"Unexpected error in register participant: {str(e)}")
        import traceback

        traceback.print_exc()

        return error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")
