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
from db import get_item, put_item, query, update_item


# Environment variables
QUIZ_SESSIONS_TABLE = os.environ.get("QUIZ_SESSIONS_TABLE", "MusicQuiz-Sessions")
QUIZ_ROUNDS_TABLE = os.environ.get("QUIZ_ROUNDS_TABLE", "MusicQuiz-Rounds")
PARTICIPANTS_TABLE = os.environ.get("PARTICIPANTS_TABLE", "MusicQuiz-Participants")
GLOBAL_PARTICIPANTS_TABLE = os.environ.get(
    "GLOBAL_PARTICIPANTS_TABLE", "GlobalParticipants"
)
SESSION_PARTICIPATIONS_TABLE = os.environ.get(
    "SESSION_PARTICIPATIONS_TABLE", "SessionParticipations"
)
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

        # Look up SessionParticipation by participantId and sessionId
        try:
            participations = query(
                SESSION_PARTICIPATIONS_TABLE,
                "participantId = :participantId",
                {":participantId": participant_id},
                index_name="ParticipantIndex",
            )

            # Find the participation for this specific session
            participation = None
            for p in participations:
                if p.get("sessionId") == session_id:
                    participation = p
                    break

            if not participation:
                return error_response(
                    404,
                    "PARTICIPATION_NOT_FOUND",
                    "Participant has not joined this session",
                )

            participation_id = participation.get("participationId")
            tenant_id = participation.get("tenantId")

        except Exception as e:
            print(f"DynamoDB query error: {str(e)}")
            return error_response(
                500, "DATABASE_ERROR", "Failed to retrieve session participation"
            )

        # Check session status - reject answers for completed sessions
        try:
            session = get_item(QUIZ_SESSIONS_TABLE, {"sessionId": session_id})
            if not session:
                return error_response(404, "SESSION_NOT_FOUND", "Session not found")

            session_status = session.get("status", "draft")
            if session_status == "completed":
                return error_response(
                    403,
                    "SESSION_COMPLETED",
                    "Cannot submit answers to a completed session",
                )
        except Exception as e:
            print(f"DynamoDB get error for session: {str(e)}")
            return error_response(500, "DATABASE_ERROR", "Failed to retrieve session")

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

        # Calculate points based on response time
        points = 0
        if is_correct:
            # Get session to find when round started
            try:
                session = get_item(QUIZ_SESSIONS_TABLE, {"sessionId": session_id})
                round_started_at = session.get("roundStartedAt")

                if round_started_at:
                    submitted_at_timestamp = int(datetime.utcnow().timestamp())
                    response_time = submitted_at_timestamp - int(round_started_at)

                    # Award points based on response time
                    if response_time <= 2:
                        points = 10  # Within 2 seconds
                    elif response_time <= 5:
                        points = 8  # Within 5 seconds
                    else:
                        points = 5  # Correct but slower
                else:
                    # No start time recorded, give default points
                    points = 5
            except Exception as e:
                print(f"Error calculating points: {str(e)}")
                points = 5  # Default points if calculation fails

        # Create answer record with participationId and tenantId
        answer_id = str(uuid.uuid4())
        submitted_at = str(int(datetime.utcnow().timestamp()))

        answer_item = {
            "answerId": answer_id,
            "participantId": participant_id,
            "participationId": participation_id,
            "sessionId": session_id,
            "tenantId": tenant_id,
            "roundNumber": round_number,
            "answer": answer,
            "isCorrect": is_correct,
            "points": points,
            "submittedAt": submitted_at,
        }

        # Store answer in DynamoDB
        try:
            put_item(ANSWERS_TABLE, answer_item)
        except Exception as e:
            print(f"DynamoDB put error: {str(e)}")
            return error_response(500, "DATABASE_ERROR", "Failed to submit answer")

        # Update SessionParticipation with new totalPoints and correctAnswers
        try:
            current_total_points = participation.get("totalPoints", 0)
            current_correct_answers = participation.get("correctAnswers", 0)

            new_total_points = current_total_points + points
            new_correct_answers = current_correct_answers + (1 if is_correct else 0)

            update_item(
                SESSION_PARTICIPATIONS_TABLE,
                {"participationId": participation_id},
                "SET totalPoints = :totalPoints, correctAnswers = :correctAnswers",
                {
                    ":totalPoints": new_total_points,
                    ":correctAnswers": new_correct_answers,
                },
            )
        except Exception as e:
            print(f"DynamoDB update error: {str(e)}")
            # Don't fail the request if score update fails, answer is already stored
            print("Warning: Failed to update participation scores")

        # Return success response
        response = {
            "statusCode": 201,
            "body": json.dumps(
                {
                    "answerId": answer_id,
                    "isCorrect": is_correct,
                    "points": points,
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
