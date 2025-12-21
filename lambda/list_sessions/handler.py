"""
List Quiz Sessions Lambda Handler

This Lambda function retrieves all quiz sessions.
This is a public endpoint - no authentication required.

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

    This is a public endpoint - returns all active quiz sessions.

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
        # Query all sessions (public endpoint)
        try:
            sessions = scan(QUIZ_SESSIONS_TABLE)
        except Exception as e:
            print(f"DynamoDB query error: {str(e)}")
            return error_response(
                500, "DATABASE_ERROR", "Failed to retrieve quiz sessions"
            )

        # Convert Decimal types to int/float
        sessions = decimal_to_number(sessions)

        # Sort sessions by creation date (newest first)
        # Handle both string (ISO format) and numeric (Unix timestamp) formats
        def get_sort_key(session):
            created_at = session.get("createdAt", 0)
            if isinstance(created_at, (int, float)):
                return float(created_at)
            elif isinstance(created_at, str):
                try:
                    from datetime import datetime

                    dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    return dt.timestamp()
                except:
                    return 0
            return 0

        sessions.sort(key=get_sort_key, reverse=True)

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
