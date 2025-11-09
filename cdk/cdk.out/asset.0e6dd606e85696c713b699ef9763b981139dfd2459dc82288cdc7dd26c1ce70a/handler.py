"""
Get Scoreboard Lambda Handler

This Lambda function retrieves the current scoreboard for a quiz session.
It calculates total points for each participant.

Endpoint: GET /quiz-sessions/{sessionId}/scoreboard
"""
import json
import os
import sys
from collections import defaultdict

# Add common utilities to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))

from cors import add_cors_headers
from errors import error_response
from db import get_item, query


# Environment variables
QUIZ_SESSIONS_TABLE = os.environ.get("QUIZ_SESSIONS_TABLE", "MusicQuiz-Sessions")
PARTICIPANTS_TABLE = os.environ.get("PARTICIPANTS_TABLE", "MusicQuiz-Participants")
ANSWERS_TABLE = os.environ.get("ANSWERS_TABLE", "MusicQuiz-Answers")


def lambda_handler(event, context):
    """
    Handle scoreboard requests.

    Expected path parameters:
        sessionId: UUID of the quiz session

    Returns:
        Success (200): Scoreboard data
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

        # Get all participants for this session
        try:
            participants = query(
                PARTICIPANTS_TABLE,
                "sessionId = :sessionId",
                {":sessionId": session_id},
                index_name="SessionIndex",
            )
        except Exception as e:
            print(f"DynamoDB query error: {str(e)}")
            participants = []

        # Get all answers for this session
        try:
            answers = query(
                ANSWERS_TABLE,
                "sessionId = :sessionId",
                {":sessionId": session_id},
                index_name="SessionRoundIndex",
            )
        except Exception as e:
            print(f"DynamoDB query error: {str(e)}")
            answers = []

        # Calculate total points for each participant
        participant_scores = defaultdict(
            lambda: {"name": "", "totalPoints": 0, "correctAnswers": 0}
        )

        # Initialize with participant names
        for participant in participants:
            participant_id = participant.get("participantId")
            participant_scores[participant_id]["name"] = participant.get(
                "name", "Unknown"
            )
            participant_scores[participant_id]["participantId"] = participant_id

        # Add up points from answers
        for answer in answers:
            participant_id = answer.get("participantId")
            points = answer.get("points", 0)
            is_correct = answer.get("isCorrect", False)

            participant_scores[participant_id]["totalPoints"] += points
            if is_correct:
                participant_scores[participant_id]["correctAnswers"] += 1

        # Convert to list and sort by total points (descending)
        scoreboard = list(participant_scores.values())
        scoreboard.sort(key=lambda x: x["totalPoints"], reverse=True)

        # Add rank
        for index, entry in enumerate(scoreboard):
            entry["rank"] = index + 1

        # Return success response
        response = {
            "statusCode": 200,
            "body": json.dumps({"sessionId": session_id, "scoreboard": scoreboard}),
        }

        return add_cors_headers(response)

    except Exception as e:
        print(f"Unexpected error in get scoreboard: {str(e)}")
        import traceback

        traceback.print_exc()
        return error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")
