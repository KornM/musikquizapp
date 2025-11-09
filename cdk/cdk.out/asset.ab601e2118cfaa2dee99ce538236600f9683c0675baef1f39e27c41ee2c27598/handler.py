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

# Add common utilities to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))

from auth import validate_token
from cors import add_cors_headers
from errors import error_response
from db import get_item, put_item, update_item
import jwt


# Environment variables
QUIZ_SESSIONS_TABLE = os.environ.get("QUIZ_SESSIONS_TABLE", "MusicQuiz-Sessions")
QUIZ_ROUNDS_TABLE = os.environ.get("QUIZ_ROUNDS_TABLE", "MusicQuiz-Rounds")

# Constants
MAX_ROUNDS_PER_SESSION = 30


def lambda_handler(event, context):
    """
    Handle add quiz round requests.

    Expected headers:
        Authorization: Bearer <jwt_token>

    Expected path parameters:
        sessionId: UUID of the quiz session

    Expected input:
        {
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
        audio_key = body.get("audioKey")
        answers = body.get("answers")
        correct_answer = body.get("correctAnswer")

        if not audio_key:
            return error_response(
                400,
                "MISSING_FIELDS",
                "audioKey is required",
                {"required_fields": ["audioKey"]},
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
            "audioKey": audio_key,
            "answers": answers,
            "correctAnswer": correct_answer,
            "roundNumber": round_number,
            "createdAt": created_at,
        }

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
