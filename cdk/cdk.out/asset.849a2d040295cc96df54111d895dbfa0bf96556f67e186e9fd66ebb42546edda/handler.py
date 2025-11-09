"""
Submit Answer Lambda Handler

This Lambda function handles participant answer submissions for quiz rounds.

Endpoint: POST /participants/answers
"""
import json
import os
import sys
import uuid
from datetime import datetime

# Add common utilities to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))

from cors import add_cors_headers
from errors import error_response
from db import get_item, put_item


# Environment variables
QUIZ_SESSIONS_TABLE = os.environ.get("QUIZ_SESSIONS_TABLE", "MusicQuiz-Sessions")
QUIZ_ROUNDS_TABLE = os.environ.get("QUIZ_ROUNDS_TABLE", "MusicQuiz-Rounds")
PARTICIPANTS_TABLE = os.environ.get("PARTICIPANTS_TABLE", "MusicQuiz-Participants")
ANSWERS_TABLE = os.environ.get("ANSWERS_TABLE", "MusicQuiz-Answers")


def lambda_handler(event, context):
    """
    Handle answer submission requests.

    Expected input:
        {
            "participantId": "uuid",
            "sessionId": "uuid",
            "roundNumber": 1,
            "answer": 0
        }

    Returns:
        Success (201): Answer submitted
        Error (400): Invalid request
        Error (404): Session, round, or participant not found
        Error (500): Internal server error
    """
    try:
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
        participant_id = body.get("participantId")
        session_id = body.get("sessionId")
        round_number = body.get("roundNumber")
        answer = body.get("answer")

        if not all(
            [participant_id, session_id, round_number is not None, answer is not None]
        ):
            return error_response(
                400,
                "MISSING_FIELDS",
                "participantId, sessionId, roundNumber, and answer are required",
            )

        # Validate answer is 0-3
        if not isinstance(answer, int) or answer < 0 or answer > 3:
            return error_response(
                400, "INVALID_ANSWER", "Answer must be an integer between 0 and 3"
            )

        # Check if participant exists
        try:
            participant = get_item(
                PARTICIPANTS_TABLE, {"participantId": participant_id}
            )
        except Exception as e:
            print(f"DynamoDB get error: {str(e)}")
            return error_response(
                500, "DATABASE_ERROR", "Failed to retrieve participant"
            )

        if not participant:
            return error_response(404, "PARTICIPANT_NOT_FOUND", "Participant not found")

        # Check if round exists
        try:
            round_item = get_item(
                QUIZ_ROUNDS_TABLE,
                {"sessionId": session_id, "roundNumber": round_number},
            )
        except Exception as e:
            print(f"DynamoDB get error: {str(e)}")
            return error_response(500, "DATABASE_ERROR", "Failed to retrieve round")

        if not round_item:
            return error_response(404, "ROUND_NOT_FOUND", "Round not found")

        # Check if answer is correct
        is_correct = answer == round_item.get("correctAnswer")

        # Create answer record
        answer_id = str(uuid.uuid4())
        submitted_at = str(int(datetime.utcnow().timestamp()))

        answer_item = {
            "answerId": answer_id,
            "participantId": participant_id,
            "sessionId": session_id,
            "roundNumber": round_number,
            "answer": answer,
            "isCorrect": is_correct,
            "submittedAt": submitted_at,
        }

        # Store answer in DynamoDB
        try:
            put_item(ANSWERS_TABLE, answer_item)
        except Exception as e:
            print(f"DynamoDB put error: {str(e)}")
            return error_response(500, "DATABASE_ERROR", "Failed to submit answer")

        # Return success response
        response = {
            "statusCode": 201,
            "body": json.dumps(
                {
                    "answerId": answer_id,
                    "isCorrect": is_correct,
                    "submittedAt": submitted_at,
                }
            ),
        }

        return add_cors_headers(response)

    except Exception as e:
        print(f"Unexpected error in submit answer: {str(e)}")
        import traceback

        traceback.print_exc()
        return error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")
