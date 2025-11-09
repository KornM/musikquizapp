"""
Create Quiz Session Lambda Handler

This Lambda function handles creation of new quiz sessions by authenticated admins.
It validates the admin JWT token and creates a new session in the DynamoDB QuizSessions table.

Endpoint: POST /admin/quiz-sessions
"""
import json
import os
import sys
import uuid
from datetime import datetime

# Add common utilities to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))

from auth import validate_token
from cors import add_cors_headers
from errors import error_response
from db import put_item
import jwt


# Environment variables
QUIZ_SESSIONS_TABLE = os.environ.get("QUIZ_SESSIONS_TABLE", "MusicQuiz-Sessions")


def lambda_handler(event, context):
    """
    Handle create quiz session requests.

    Expected headers:
        Authorization: Bearer <jwt_token>

    Expected input:
        {
            "title": "Quiz Title",
            "description": "Quiz Description"
        }

    Returns:
        Success (201):
            {
                "sessionId": "uuid",
                "title": "Quiz Title",
                "description": "Quiz Description",
                "createdAt": 1234567890,
                "createdBy": "admin_id",
                "roundCount": 0,
                "status": "draft"
            }

        Error (400): Invalid request body
        Error (401): Missing or invalid token
        Error (403): Insufficient permissions
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

        # Extract token from "Bearer <token>" format
        if not auth_header.startswith("Bearer "):
            return error_response(
                401,
                "INVALID_AUTH_FORMAT",
                "Authorization header must be 'Bearer <token>'",
            )

        token = auth_header[7:]  # Remove "Bearer " prefix

        # Validate JWT token
        try:
            payload = validate_token(token)
        except jwt.ExpiredSignatureError:
            return error_response(401, "TOKEN_EXPIRED", "Token has expired")
        except jwt.InvalidTokenError:
            return error_response(401, "INVALID_TOKEN", "Invalid token")

        # Check if user has admin role
        if payload.get("role") != "admin":
            return error_response(
                403, "INSUFFICIENT_PERMISSIONS", "Admin role required"
            )

        admin_id = payload.get("sub")

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
        title = body.get("title")
        if not title:
            return error_response(
                400,
                "MISSING_FIELDS",
                "Title is required",
                {"required_fields": ["title"]},
            )

        description = body.get("description", "")

        # Generate session ID and timestamp
        session_id = str(uuid.uuid4())
        created_at = int(datetime.utcnow().timestamp())

        # Create session item
        session_item = {
            "sessionId": session_id,
            "title": title,
            "description": description,
            "createdBy": admin_id,
            "createdAt": created_at,
            "roundCount": 0,
            "status": "draft",
        }

        # Store session in DynamoDB
        try:
            put_item(QUIZ_SESSIONS_TABLE, session_item)
        except Exception as e:
            print(f"DynamoDB put error: {str(e)}")
            return error_response(
                500, "DATABASE_ERROR", "Failed to create quiz session"
            )

        # Return success response
        response = {
            "statusCode": 201,
            "body": json.dumps(session_item),
        }

        return add_cors_headers(response)

    except Exception as e:
        # Log unexpected errors
        print(f"Unexpected error in create quiz session: {str(e)}")
        import traceback

        traceback.print_exc()

        return error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")
