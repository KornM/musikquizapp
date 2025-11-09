"""
List Quiz Sessions Lambda Handler

This Lambda function retrieves all quiz sessions.
It scans the QuizSessions table and returns a list of all sessions.

Endpoint: GET /quiz-sessions
"""
import json
import os
import sys
from decimal import Decimal

# Add common utilities to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))

from cors import add_cors_headers
from errors import error_response
from db import scan


# Environment variables
QUIZ_SESSIONS_TABLE = os.environ.get("QUIZ_SESSIONS_TABLE", "MusicQuiz-Sessions")


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
    Handle list quiz sessions requests.

    Returns:
        Success (200):
            {
                "sessions": [
                    {
                        "sessionId": "uuid",
                        "title": "Quiz Title",
                        "description": "...",
                        "createdBy": "admin_id",
                        "createdAt": 1234567890,
                        "roundCount": 2,
                        "status": "draft"
                    }
                ]
            }

        Error (500): Internal server error
    """
    try:
        # Scan all sessions from DynamoDB
        try:
            sessions = scan(QUIZ_SESSIONS_TABLE)
        except Exception as e:
            print(f"DynamoDB scan error: {str(e)}")
            return error_response(
                500, "DATABASE_ERROR", "Failed to retrieve quiz sessions"
            )

        # Convert Decimal types to int/float
        sessions = decimal_to_number(sessions)

        # Sort sessions by creation date (newest first)
        sessions.sort(key=lambda s: s.get("createdAt", "0"), reverse=True)

        # Return success response
        response = {
            "statusCode": 200,
            "body": json.dumps({"sessions": sessions}),
        }

        return add_cors_headers(response)

    except Exception as e:
        # Log unexpected errors
        print(f"Unexpected error in list sessions: {str(e)}")
        import traceback

        traceback.print_exc()

        return error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")
