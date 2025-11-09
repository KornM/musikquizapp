"""
Reset Points Lambda Handler

This Lambda function deletes all answers for a session, effectively resetting all points.

Endpoint: DELETE /admin/quiz-sessions/{sessionId}/points
"""
import json
import os
import sys

# Add common utilities to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))

from auth import validate_token
from cors import add_cors_headers
from errors import error_response
from db import query
import jwt
import boto3

# Environment variables
QUIZ_SESSIONS_TABLE = os.environ.get("QUIZ_SESSIONS_TABLE", "MusicQuiz-Sessions")
ANSWERS_TABLE = os.environ.get("ANSWERS_TABLE", "MusicQuiz-Answers")

dynamodb = boto3.resource("dynamodb")


def lambda_handler(event, context):
    """Handle reset points requests."""
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

        if payload.get("role") != "admin":
            return error_response(
                403, "INSUFFICIENT_PERMISSIONS", "Admin role required"
            )

        # Extract session ID
        path_parameters = event.get("pathParameters", {})
        session_id = path_parameters.get("sessionId")

        if not session_id:
            return error_response(400, "MISSING_SESSION_ID", "Session ID required")

        # Get all answers for this session
        try:
            answers = query(
                ANSWERS_TABLE,
                "sessionId = :sessionId",
                {":sessionId": session_id},
                index_name="SessionRoundIndex",
            )
        except Exception as e:
            print(f"Query error: {str(e)}")
            answers = []

        # Delete all answers
        answers_table = dynamodb.Table(ANSWERS_TABLE)
        deleted_count = 0

        for answer in answers:
            try:
                answers_table.delete_item(Key={"answerId": answer["answerId"]})
                deleted_count += 1
            except Exception as e:
                print(f"Delete error: {str(e)}")

        response = {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Points reset successfully",
                    "deletedAnswers": deleted_count,
                }
            ),
        }

        return add_cors_headers(response)

    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        import traceback

        traceback.print_exc()
        return error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")
