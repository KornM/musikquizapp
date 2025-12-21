"""
Get Quiz Session Lambda Handler

This Lambda function retrieves a quiz session with all its rounds.
This is a public endpoint - no authentication required.

Endpoint: GET /quiz-sessions/{sessionId}
"""

import json
import os
import sys
from decimal import Decimal

# Add common utilities to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))

from cors import add_cors_headers
from errors import error_response
from db import get_item, query


# Environment variables
QUIZ_SESSIONS_TABLE = os.environ.get("QUIZ_SESSIONS_TABLE", "MusicQuiz-Sessions")
QUIZ_ROUNDS_TABLE = os.environ.get("QUIZ_ROUNDS_TABLE", "MusicQuiz-Rounds")


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
    Handle get quiz session requests.

    This is a public endpoint - returns session details with rounds.

    Expected path parameters:
        sessionId: UUID of the quiz session

    Returns:
        Success (200):
            {
                "sessionId": "uuid",
                "title": "Quiz Title",
                "description": "...",
                "createdBy": "admin_id",
                "createdAt": 1234567890,
                "roundCount": 2,
                "status": "draft",
                "rounds": [
                    {
                        "roundId": "uuid",
                        "roundNumber": 1,
                        "audioKey": "...",
                        "answers": ["A", "B", "C", "D"],
                        "correctAnswer": 0
                    }
                ]
            }

        Error (400): Missing session ID
        Error (404): Session not found
        Error (500): Internal server error
    """
    try:
        # Extract session ID from path parameters
        path_parameters = event.get("pathParameters", {})
        session_id = path_parameters.get("sessionId")

        if not session_id:
            return error_response(
                400, "MISSING_SESSION_ID", "Session ID is required in path"
            )

        # Get session from DynamoDB
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

        # Query rounds for this session
        try:
            rounds = query(
                QUIZ_ROUNDS_TABLE,
                "sessionId = :sessionId",
                {":sessionId": session_id},
            )
        except Exception as e:
            print(f"DynamoDB query error: {str(e)}")
            # If rounds query fails, return session without rounds
            rounds = []

        # Sort rounds by round number
        rounds.sort(key=lambda r: r.get("roundNumber", 0))

        # Add rounds to session
        session["rounds"] = rounds

        # Convert Decimal types to int/float
        session = decimal_to_number(session)

        # Return success response
        response = {
            "statusCode": 200,
            "body": json.dumps(session),
        }

        return add_cors_headers(response)

    except Exception as e:
        # Log unexpected errors
        print(f"Unexpected error in get quiz session: {str(e)}")
        import traceback

        traceback.print_exc()

        return error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")
