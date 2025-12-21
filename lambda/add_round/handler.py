"""
Add Quiz Round Lambda Handler

This Lambda function handles adding quiz rounds to existing quiz sessions.
It validates the admin JWT token, checks session existence and round limits,
and creates a new round in the DynamoDB QuizRounds table.

Endpoint: POST /admin/quiz-sessions/{sessionId}/rounds
"""

import json
import os
import sys
import uuid
from datetime import datetime
from decimal import Decimal

# Add common utilities to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))

from auth import validate_token
from cors import add_cors_headers
from errors import error_response
from db import get_item, put_item, update_item
from tenant_middleware import validate_tenant_access
import jwt


# Environment variables
QUIZ_SESSIONS_TABLE = os.environ.get("QUIZ_SESSIONS_TABLE", "MusicQuiz-Sessions")
QUIZ_ROUNDS_TABLE = os.environ.get("QUIZ_ROUNDS_TABLE", "MusicQuiz-Rounds")

# Constants
MAX_ROUNDS_PER_SESSION = 30


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
    Handle add quiz round requests.

    Expected headers:
        Authorization: Bearer <jwt_token>

    Expected path parameters:
        sessionId: UUID of the quiz session

    Expected input:
        {
            "question": "What is the name of this song?",
            "audioKey": "sessions/{sessionId}/audio/{uuid}.mp3",
            "answers": ["Answer 1", "Answer 2", "Answer 3", "Answer 4"],
            "correctAnswer": 0
        }

    Returns:
        Success (201):
            {
                "roundId": "uuid",
                "sessionId": "uuid",
                "audioKey": "...",
                "answers": [...],
                "correctAnswer": 0,
                "roundNumber": 1,
                "createdAt": 1234567890
            }

        Error (400): Invalid request body or validation error
        Error (401): Missing or invalid token
        Error (403): Insufficient permissions
        Error (404): Session not found
        Error (409): Max rounds limit reached
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

        # Extract tenant ID from token and create tenant context
        admin_tenant_id = payload.get("tenantId")
        tenant_context = {
            "adminId": payload.get("sub"),
            "role": role,
            "tenantId": admin_tenant_id,
        }

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

        # Validate tenant access
        session_tenant_id = session.get("tenantId")
        if session_tenant_id:
            access_error = validate_tenant_access(tenant_context, session_tenant_id)
            if access_error:
                return access_error

        # Check round count limit
        current_round_count = session.get("roundCount", 0)
        if current_round_count >= MAX_ROUNDS_PER_SESSION:
            return error_response(
                409,
                "MAX_ROUNDS_REACHED",
                f"Maximum of {MAX_ROUNDS_PER_SESSION} rounds per session reached",
                {
                    "currentRounds": current_round_count,
                    "maxRounds": MAX_ROUNDS_PER_SESSION,
                },
            )

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
        question = body.get("question")
        audio_key = body.get("audioKey")
        image_key = body.get("imageKey")
        answers = body.get("answers")
        correct_answer = body.get("correctAnswer")

        if not question:
            return error_response(
                400,
                "MISSING_FIELDS",
                "question is required",
                {"required_fields": ["question"]},
            )

        # Check if session requires media
        media_type = session.get("mediaType", "audio")
        if media_type == "audio" and not audio_key:
            return error_response(
                400,
                "MISSING_FIELDS",
                "audioKey is required for audio quiz sessions",
                {"required_fields": ["audioKey"]},
            )
        elif media_type == "image" and not image_key:
            return error_response(
                400,
                "MISSING_FIELDS",
                "imageKey is required for image quiz sessions",
                {"required_fields": ["imageKey"]},
            )

        if not answers or not isinstance(answers, list):
            return error_response(
                400,
                "INVALID_ANSWERS",
                "answers must be a list of 4 answer options",
            )

        if len(answers) != 4:
            return error_response(
                400,
                "INVALID_ANSWERS",
                "Exactly 4 answer options are required",
                {"provided": len(answers), "required": 4},
            )

        if correct_answer is None or not isinstance(correct_answer, int):
            return error_response(
                400,
                "INVALID_CORRECT_ANSWER",
                "correctAnswer must be an integer (0-3)",
            )

        if correct_answer < 0 or correct_answer > 3:
            return error_response(
                400,
                "INVALID_CORRECT_ANSWER",
                "correctAnswer must be between 0 and 3",
                {"provided": correct_answer, "valid_range": "0-3"},
            )

        # Generate round ID and timestamp
        round_id = str(uuid.uuid4())
        created_at = str(int(datetime.utcnow().timestamp()))
        round_number = current_round_count + 1

        # Create round item
        round_item = {
            "roundId": round_id,
            "sessionId": session_id,
            "question": question,
            "answers": answers,
            "correctAnswer": correct_answer,
            "roundNumber": round_number,
            "createdAt": created_at,
        }

        # Add media keys if provided
        if audio_key:
            round_item["audioKey"] = audio_key
        if image_key:
            round_item["imageKey"] = image_key

        # Store round in DynamoDB
        try:
            put_item(QUIZ_ROUNDS_TABLE, round_item)
        except Exception as e:
            print(f"DynamoDB put error: {str(e)}")
            return error_response(500, "DATABASE_ERROR", "Failed to create quiz round")

        # Update session round count
        try:
            update_item(
                QUIZ_SESSIONS_TABLE,
                {"sessionId": session_id},
                "SET roundCount = :count",
                {":count": round_number},
            )
        except Exception as e:
            print(f"DynamoDB update error: {str(e)}")
            # Round was created but count update failed - log but don't fail
            print(
                f"Warning: Round created but session count update failed for {session_id}"
            )

        # Convert Decimal types to int/float
        round_item = decimal_to_number(round_item)

        # Return success response
        response = {
            "statusCode": 201,
            "body": json.dumps(round_item),
        }

        return add_cors_headers(response)

    except Exception as e:
        # Log unexpected errors
        print(f"Unexpected error in add quiz round: {str(e)}")
        import traceback

        traceback.print_exc()

        return error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")
