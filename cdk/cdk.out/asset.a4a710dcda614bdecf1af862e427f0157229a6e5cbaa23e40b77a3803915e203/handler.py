"""
Delete Quiz Session Lambda Handler

This Lambda function deletes a quiz session along with all its rounds and audio files.
It validates the admin JWT token and performs cascading deletion.

Endpoint: DELETE /admin/quiz-sessions/{sessionId}
"""
import json
import os
import sys

# Add common utilities to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))

from auth import validate_token
from cors import add_cors_headers
from errors import error_response
from db import get_item, delete_item, query
import jwt
import boto3
from botocore.exceptions import ClientError


# Environment variables
QUIZ_SESSIONS_TABLE = os.environ.get("QUIZ_SESSIONS_TABLE", "MusicQuiz-Sessions")
QUIZ_ROUNDS_TABLE = os.environ.get("QUIZ_ROUNDS_TABLE", "MusicQuiz-Rounds")
AUDIO_BUCKET = os.environ.get("AUDIO_BUCKET", "music-quiz-audio")

# Initialize S3 client
s3_client = boto3.client("s3")


def lambda_handler(event, context):
    """
    Handle delete quiz session requests.

    Expected headers:
        Authorization: Bearer <jwt_token>

    Expected path parameters:
        sessionId: UUID of the quiz session

    Returns:
        Success (200): Session and all related data deleted
        Error (401): Missing or invalid token
        Error (403): Insufficient permissions
        Error (404): Session not found
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
        if payload.get("role") != "admin":
            return error_response(
                403, "INSUFFICIENT_PERMISSIONS", "Admin role required"
            )

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

        # Get all rounds for this session
        try:
            rounds = query(
                QUIZ_ROUNDS_TABLE,
                "sessionId = :sessionId",
                {":sessionId": session_id},
            )
        except Exception as e:
            print(f"DynamoDB query error: {str(e)}")
            rounds = []

        # Delete audio files from S3
        deleted_files = 0
        for round_item in rounds:
            audio_key = round_item.get("audioKey")
            if audio_key:
                try:
                    s3_client.delete_object(Bucket=AUDIO_BUCKET, Key=audio_key)
                    deleted_files += 1
                    print(f"Deleted S3 object: {audio_key}")
                except ClientError as e:
                    print(f"Failed to delete S3 object {audio_key}: {str(e)}")
                    # Continue with deletion even if S3 delete fails

        # Delete all rounds
        deleted_rounds = 0
        for round_item in rounds:
            try:
                delete_item(
                    QUIZ_ROUNDS_TABLE,
                    {
                        "sessionId": session_id,
                        "roundNumber": round_item.get("roundNumber"),
                    },
                )
                deleted_rounds += 1
            except Exception as e:
                print(f"Failed to delete round: {str(e)}")

        # Delete the session
        try:
            delete_item(QUIZ_SESSIONS_TABLE, {"sessionId": session_id})
        except Exception as e:
            print(f"DynamoDB delete error: {str(e)}")
            return error_response(
                500, "DATABASE_ERROR", "Failed to delete quiz session"
            )

        # Return success response
        response = {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Session deleted successfully",
                    "sessionId": session_id,
                    "deletedRounds": deleted_rounds,
                    "deletedAudioFiles": deleted_files,
                }
            ),
        }

        return add_cors_headers(response)

    except Exception as e:
        # Log unexpected errors
        print(f"Unexpected error in delete session: {str(e)}")
        import traceback

        traceback.print_exc()

        return error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")
