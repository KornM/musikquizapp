"""
Get Global Participant Lambda Handler

This Lambda function retrieves a global participant's profile.

Endpoint: GET /participants/{participantId}
"""

import json
import os
import sys

# Add common utilities to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))

from cors import add_cors_headers
from errors import error_response
from db import get_item


# Environment variables
GLOBAL_PARTICIPANTS_TABLE = os.environ.get(
    "GLOBAL_PARTICIPANTS_TABLE", "GlobalParticipants"
)


def lambda_handler(event, context):
    """
    Handle global participant profile retrieval requests.

    Expected path parameters:
        participantId: UUID of the participant

    Returns:
        Success (200):
            {
                "participantId": "uuid",
                "tenantId": "uuid",
                "name": "Participant Name",
                "avatar": "😀",
                "createdAt": "2024-01-01T00:00:00Z"
            }

        Error (404): Participant not found
        Error (500): Internal server error
    """
    try:
        # Get participant ID from path parameters
        path_parameters = event.get("pathParameters", {})
        participant_id = path_parameters.get("participantId")

        if not participant_id:
            return error_response(
                400,
                "MISSING_FIELDS",
                "participantId is required in path",
            )

        # Retrieve participant from database
        try:
            participant = get_item(
                GLOBAL_PARTICIPANTS_TABLE, {"participantId": participant_id}
            )
        except Exception as e:
            print(f"DynamoDB get error: {str(e)}")
            return error_response(
                500, "DATABASE_ERROR", "Failed to retrieve participant"
            )

        if not participant:
            return error_response(
                404,
                "PARTICIPANT_NOT_FOUND",
                f"Participant {participant_id} not found",
            )

        # Return participant profile (exclude token for security)
        profile = {
            "participantId": participant["participantId"],
            "tenantId": participant["tenantId"],
            "name": participant["name"],
            "avatar": participant["avatar"],
            "createdAt": participant["createdAt"],
        }

        response = {
            "statusCode": 200,
            "body": json.dumps(profile),
        }

        return add_cors_headers(response)

    except Exception as e:
        # Log unexpected errors
        print(f"Unexpected error in get global participant: {str(e)}")
        import traceback

        traceback.print_exc()

        return error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")
