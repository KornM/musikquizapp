"""
Lambda function to delete a round from a quiz session.
"""

import json
import os
import sys

# Add common utilities to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))

from auth import validate_token
from cors import add_cors_headers
from errors import error_response
from tenant_middleware import validate_tenant_access
import jwt
import boto3
from botocore.exceptions import ClientError

QUIZ_SESSIONS_TABLE = os.environ.get("QUIZ_SESSIONS_TABLE", "MusicQuiz-Sessions")
QUIZ_ROUNDS_TABLE = os.environ.get("QUIZ_ROUNDS_TABLE", "MusicQuiz-Rounds")
AUDIO_BUCKET = os.environ.get("AUDIO_BUCKET", "music-quiz-audio")

# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")
s3_client = boto3.client("s3")


def lambda_handler(event, context):
    """
    Delete a round from a quiz session.

    DELETE /admin/quiz-sessions/{sessionId}/rounds/{roundNumber}
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
        role = payload.get("role", "admin")
        if role not in ["admin", "tenant_admin", "super_admin"]:
            return error_response(
                403, "INSUFFICIENT_PERMISSIONS", "Admin role required"
            )

        # Extract tenant ID from token
        admin_tenant_id = payload.get("tenantId")

        # Extract parameters
        path_parameters = event.get("pathParameters", {})
        session_id = path_parameters.get("sessionId")
        round_number_str = path_parameters.get("roundNumber")

        if not session_id or not round_number_str:
            return error_response(
                400, "MISSING_PARAMETERS", "Session ID and round number are required"
            )

        try:
            round_number = int(round_number_str)
        except ValueError:
            return error_response(
                400, "INVALID_ROUND_NUMBER", "Round number must be an integer"
            )

        sessions_table = dynamodb.Table(QUIZ_SESSIONS_TABLE)
        rounds_table = dynamodb.Table(QUIZ_ROUNDS_TABLE)

        # Get session to validate tenant access
        session_response = sessions_table.get_item(Key={"sessionId": session_id})

        if "Item" not in session_response:
            return error_response(404, "SESSION_NOT_FOUND", "Session not found")

        session = session_response["Item"]

        # Validate tenant access
        session_tenant_id = session.get("tenantId")
        if session_tenant_id:
            access_error = validate_tenant_access(tenant_context, session_tenant_id)
            if access_error:
                return access_error

        # Get the round to find the audio key
        round_response = rounds_table.get_item(
            Key={"sessionId": session_id, "roundNumber": round_number}
        )

        if "Item" not in round_response:
            return error_response(404, "ROUND_NOT_FOUND", "Round not found")

        round_item = round_response["Item"]

        # Delete audio file from S3 if it exists
        if "audioKey" in round_item:
            try:
                s3_client.delete_object(Bucket=AUDIO_BUCKET, Key=round_item["audioKey"])
                print(f"Deleted S3 object: {round_item['audioKey']}")
            except ClientError as e:
                print(f"Error deleting audio file: {e}")
                # Continue with deletion even if S3 delete fails

        # Delete the round from DynamoDB
        rounds_table.delete_item(
            Key={"sessionId": session_id, "roundNumber": round_number}
        )

        # Update session's round count
        # Get all remaining rounds for this session
        remaining_rounds = rounds_table.query(
            KeyConditionExpression="sessionId = :sid",
            ExpressionAttributeValues={":sid": session_id},
        )

        new_round_count = remaining_rounds["Count"]

        # Update session
        sessions_table.update_item(
            Key={"sessionId": session_id},
            UpdateExpression="SET roundCount = :count",
            ExpressionAttributeValues={":count": new_round_count},
        )

        response = {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Round deleted successfully",
                    "sessionId": session_id,
                    "roundNumber": round_number,
                }
            ),
        }

        return add_cors_headers(response)

    except Exception as e:
        print(f"Unexpected error in delete round: {str(e)}")
        import traceback

        traceback.print_exc()
        return error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")
