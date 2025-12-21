"""
Delete Global Participant Lambda Handler

This Lambda function deletes a global participant and cascades the deletion
to all associated SessionParticipation records.

Endpoint: DELETE /participants/{participantId}
"""

import json
import os
import sys

# Add common utilities to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))

from cors import add_cors_headers
from errors import error_response
from db import get_item, delete_item, query
from participant_middleware import extract_participant_from_token


# Environment variables
GLOBAL_PARTICIPANTS_TABLE = os.environ.get(
    "GLOBAL_PARTICIPANTS_TABLE", "GlobalParticipants"
)
SESSION_PARTICIPATIONS_TABLE = os.environ.get(
    "SESSION_PARTICIPATIONS_TABLE", "SessionParticipations"
)


def lambda_handler(event, context):
    """
    Handle global participant deletion requests.

    Path parameters:
        participantId: UUID of the participant to delete

    Headers:
        Authorization: Bearer <participant_jwt_token>

    Returns:
        Success (200):
            {
                "message": "Participant deleted successfully",
                "participantId": "uuid",
                "deletedParticipations": 3
            }

        Error (400): Missing participant ID
        Error (401): Missing or invalid token
        Error (403): Unauthorized access
        Error (404): Participant not found
        Error (500): Internal server error
    """
    try:
        # Extract participantId from path parameters
        participant_id = event.get("pathParameters", {}).get("participantId")
        if not participant_id:
            return error_response(
                400, "MISSING_FIELDS", "Participant ID is required in path"
            )

        # Validate participant authentication
        headers = event.get("headers", {})
        participant_context, auth_error = extract_participant_from_token(event)

        if auth_error:
            return auth_error

        token_participant_id = participant_context.get("participantId")

        # Verify the participant is deleting their own account
        if token_participant_id != participant_id:
            return error_response(
                403,
                "UNAUTHORIZED_ACCESS",
                "You can only delete your own participant account",
            )

        # Check if participant exists
        try:
            participant = get_item(
                GLOBAL_PARTICIPANTS_TABLE, {"participantId": participant_id}
            )
        except Exception as e:
            print(f"DynamoDB get error: {str(e)}")
            return error_response(500, "DATABASE_ERROR", "Failed to query participant")

        if not participant:
            return error_response(
                404, "PARTICIPANT_NOT_FOUND", "Participant does not exist"
            )

        # Find and delete all associated SessionParticipation records
        deleted_participations = 0
        try:
            participations = query(
                SESSION_PARTICIPATIONS_TABLE,
                "participantId = :participantId",
                {":participantId": participant_id},
                index_name="ParticipantIndex",
            )

            for participation in participations:
                try:
                    delete_item(
                        SESSION_PARTICIPATIONS_TABLE,
                        {"participationId": participation.get("participationId")},
                    )
                    deleted_participations += 1
                except Exception as e:
                    print(
                        f"Failed to delete participation {participation.get('participationId')}: {str(e)}"
                    )
                    # Continue with other deletions

        except Exception as e:
            print(f"DynamoDB query error for participations: {str(e)}")
            # Continue with participant deletion even if participation deletion fails

        # Delete the global participant
        try:
            delete_item(GLOBAL_PARTICIPANTS_TABLE, {"participantId": participant_id})
        except Exception as e:
            print(f"DynamoDB delete error: {str(e)}")
            return error_response(500, "DATABASE_ERROR", "Failed to delete participant")

        # Return success response
        response = {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Participant deleted successfully",
                    "participantId": participant_id,
                    "deletedParticipations": deleted_participations,
                }
            ),
        }

        return add_cors_headers(response)

    except Exception as e:
        # Log unexpected errors
        print(f"Unexpected error in delete global participant: {str(e)}")
        import traceback

        traceback.print_exc()

        return error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")
