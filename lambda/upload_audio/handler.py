"""
Upload Audio Lambda Handler

This Lambda function handles uploading audio files to S3 for quiz rounds.
It validates the admin JWT token, generates a unique S3 key, and uploads the audio data.

Endpoint: POST /admin/audio
"""

import json
import os
import sys
import uuid
import base64
from datetime import datetime

# Add common utilities to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))

from auth import validate_token
from cors import add_cors_headers
from errors import error_response
from db import get_item
from tenant_middleware import validate_tenant_access
import jwt
import boto3
from botocore.exceptions import ClientError


# Environment variables
AUDIO_BUCKET = os.environ.get("AUDIO_BUCKET", "music-quiz-audio")
QUIZ_SESSIONS_TABLE = os.environ.get("QUIZ_SESSIONS_TABLE", "MusicQuiz-Sessions")

# Initialize S3 client
s3_client = boto3.client("s3")


def lambda_handler(event, context):
    """
    Handle audio upload requests.

    Expected headers:
        Authorization: Bearer <jwt_token>
        Content-Type: audio/* or application/json (for base64)

    Expected input (JSON with base64):
        {
            "audioData": "base64_encoded_audio",
            "fileName": "song.mp3",
            "sessionId": "uuid"
        }

    Or raw binary data in body with query parameters

    Returns:
        Success (201):
            {
                "audioKey": "sessions/{sessionId}/audio/{uuid}.mp3",
                "url": "presigned_url"
            }

        Error (400): Invalid request
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
        role = payload.get("role", "admin")
        if role not in ["admin", "tenant_admin", "super_admin"]:
            return error_response(
                403, "INSUFFICIENT_PERMISSIONS", "Admin role required"
            )

        # Extract tenant ID from token
        admin_tenant_id = payload.get("tenantId")

        # Parse request body
        if not event.get("body"):
            return error_response(400, "INVALID_REQUEST", "Request body is required")

        content_type = headers.get("Content-Type") or headers.get("content-type", "")

        # Handle JSON with base64 encoded audio
        if "application/json" in content_type:
            try:
                body = json.loads(event["body"])
            except json.JSONDecodeError:
                return error_response(
                    400, "INVALID_JSON", "Request body must be valid JSON"
                )

            audio_data_b64 = body.get("audioData")
            file_name = body.get("fileName", "audio.mp3")
            session_id = body.get("sessionId")

            if not audio_data_b64:
                return error_response(
                    400,
                    "MISSING_FIELDS",
                    "audioData is required",
                    {"required_fields": ["audioData"]},
                )

            if not session_id:
                return error_response(
                    400,
                    "MISSING_FIELDS",
                    "sessionId is required",
                    {"required_fields": ["sessionId"]},
                )

            # Decode base64 audio data
            try:
                audio_data = base64.b64decode(audio_data_b64)
            except Exception as e:
                print(f"Base64 decode error: {str(e)}")
                return error_response(
                    400, "INVALID_AUDIO_DATA", "audioData must be valid base64"
                )

        else:
            # Handle raw binary data
            audio_data = event["body"]
            if event.get("isBase64Encoded"):
                audio_data = base64.b64decode(audio_data)
            else:
                audio_data = (
                    audio_data.encode("utf-8")
                    if isinstance(audio_data, str)
                    else audio_data
                )

            # Get session ID from query parameters
            query_params = event.get("queryStringParameters") or {}
            session_id = query_params.get("sessionId")
            file_name = query_params.get("fileName", "audio.mp3")

            if not session_id:
                return error_response(
                    400,
                    "MISSING_SESSION_ID",
                    "sessionId is required in query parameters or JSON body",
                )

        # Validate tenant access to session
        try:
            session = get_item(QUIZ_SESSIONS_TABLE, {"sessionId": session_id})
        except Exception as e:
            print(f"DynamoDB get error for session: {str(e)}")
            return error_response(500, "DATABASE_ERROR", "Failed to retrieve session")

        if not session:
            return error_response(404, "SESSION_NOT_FOUND", "Session not found")

        session_tenant_id = session.get("tenantId")
        if session_tenant_id:
            access_error = validate_tenant_access(tenant_context, session_tenant_id)
            if access_error:
                return access_error

        # Extract file extension
        file_extension = file_name.split(".")[-1] if "." in file_name else "mp3"

        # Generate unique S3 key
        unique_id = str(uuid.uuid4())
        audio_key = f"sessions/{session_id}/audio/{unique_id}.{file_extension}"

        # Upload to S3
        try:
            s3_client.put_object(
                Bucket=AUDIO_BUCKET,
                Key=audio_key,
                Body=audio_data,
                ContentType=f"audio/{file_extension}",
            )
        except ClientError as e:
            print(f"S3 upload error: {str(e)}")
            return error_response(500, "UPLOAD_ERROR", "Failed to upload audio file")

        # Generate presigned URL (valid for 1 hour)
        try:
            presigned_url = s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": AUDIO_BUCKET, "Key": audio_key},
                ExpiresIn=3600,
            )
        except ClientError as e:
            print(f"Presigned URL generation error: {str(e)}")
            # File uploaded but URL generation failed - still return success
            presigned_url = None

        # Return success response
        response_body = {"audioKey": audio_key}
        if presigned_url:
            response_body["url"] = presigned_url

        response = {
            "statusCode": 201,
            "body": json.dumps(response_body),
        }

        return add_cors_headers(response)

    except Exception as e:
        # Log unexpected errors
        print(f"Unexpected error in upload audio: {str(e)}")
        import traceback

        traceback.print_exc()

        return error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")
