"""
Generate QR Code Data Lambda Handler

This Lambda function generates registration URL data for QR code display.
The frontend can use this URL to generate a QR code for participant registration.

Endpoint: GET /quiz-sessions/{sessionId}/qr
"""
import json
import os
import sys

# Add common utilities to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))

from cors import add_cors_headers
from errors import error_response
from db import get_item


# Environment variables
QUIZ_SESSIONS_TABLE = os.environ.get("QUIZ_SESSIONS_TABLE", "MusicQuiz-Sessions")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://musikquiz.example.com")


def lambda_handler(event, context):
    """
    Handle QR code data generation requests.

    Expected path parameters:
        sessionId: UUID of the quiz session

    Returns:
        Success (200):
            {
                "registrationUrl": "https://frontend.com/register?sessionId=uuid",
                "sessionId": "uuid",
                "sessionTitle": "Quiz Title"
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

        # Construct registration URL
        registration_url = f"{FRONTEND_URL}/register?sessionId={session_id}"

        # Return success response
        response_body = {
            "registrationUrl": registration_url,
            "sessionId": session_id,
            "sessionTitle": session.get("title", ""),
        }

        response = {
            "statusCode": 200,
            "body": json.dumps(response_body),
        }

        return add_cors_headers(response)

    except Exception as e:
        # Log unexpected errors
        print(f"Unexpected error in generate QR: {str(e)}")
        import traceback

        traceback.print_exc()

        return error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")
