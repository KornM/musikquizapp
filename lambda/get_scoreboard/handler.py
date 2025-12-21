"""
Get Scoreboard Lambda Handler

This Lambda function retrieves the current scoreboard for a quiz session.
It retrieves scores from SessionParticipations and joins with GlobalParticipants.

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
GLOBAL_PARTICIPANTS_TABLE = os.environ.get(
    "GLOBAL_PARTICIPANTS_TABLE", "GlobalParticipants"
)
SESSION_PARTICIPATIONS_TABLE = os.environ.get(
    "SESSION_PARTICIPATIONS_TABLE", "SessionParticipations"
)
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

        # Check if session exists and get tenantId
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

        session_tenant_id = session.get("tenantId")

        # Query SessionParticipations by sessionId
        try:
            participations = query(
                SESSION_PARTICIPATIONS_TABLE,
                "sessionId = :sessionId",
                {":sessionId": session_id},
                index_name="SessionIndex",
            )
        except Exception as e:
            print(f"DynamoDB query error: {str(e)}")
            participations = []

        # Build scoreboard by joining with GlobalParticipants
        scoreboard = []

        for participation in participations:
            participant_id = participation.get("participantId")

            # Filter by session's tenantId if present
            if session_tenant_id and participation.get("tenantId") != session_tenant_id:
                continue

            # Get participant profile from GlobalParticipants
            try:
                participant = get_item(
                    GLOBAL_PARTICIPANTS_TABLE, {"participantId": participant_id}
                )

                if participant:
                    # Use GlobalParticipant data
                    name = participant.get("name", "Unknown")
                    avatar = participant.get("avatar", "😀")
                else:
                    # Fallback: try legacy Participants table
                    legacy_participant = get_item(
                        PARTICIPANTS_TABLE, {"participantId": participant_id}
                    )
                    if legacy_participant:
                        name = legacy_participant.get("name", "Unknown")
                        avatar = legacy_participant.get("avatar", "😀")
                    else:
                        name = "Unknown"
                        avatar = "😀"

            except Exception as e:
                print(f"Error retrieving participant {participant_id}: {str(e)}")
                name = "Unknown"
                avatar = "😀"

            # Add to scoreboard with session-specific scores
            scoreboard.append(
                {
                    "participantId": participant_id,
                    "name": name,
                    "avatar": avatar,
                    "totalPoints": participation.get("totalPoints", 0),
                    "correctAnswers": participation.get("correctAnswers", 0),
                }
            )

        # Sort by total points (descending)
        scoreboard.sort(key=lambda x: x["totalPoints"], reverse=True)

        # Add rank
        for index, entry in enumerate(scoreboard):
            entry["rank"] = index + 1

        # Convert Decimal types to int/float for JSON serialization
        from decimal import Decimal

        def decimal_to_number(obj):
            if isinstance(obj, list):
                return [decimal_to_number(i) for i in obj]
            elif isinstance(obj, dict):
                return {k: decimal_to_number(v) for k, v in obj.items()}
            elif isinstance(obj, Decimal):
                return int(obj) if obj % 1 == 0 else float(obj)
            else:
                return obj

        scoreboard = decimal_to_number(scoreboard)

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
