"""
Update Global Participant Lambda Handler

This Lambda function updates a global participant's profile.

Endpoint: PUT /participants/{participantId}
"""

import json
import os
import sys
from datetime import datetime

# Add common utilities to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))

from cors import add_cors_headers
from errors import error_response
from db import update_item, scan
from participant_middleware import require_participant_auth


# Environment variables
GLOBAL_PARTICIPANTS_TABLE = os.environ.get(
    "GLOBAL_PARTICIPANTS_TABLE", "GlobalParticipants"
)


def lambda_handler(event, context):
    """
    Handle global participant profile update requests.

    Expected path parameters:
        participantId: UUID of the participant

    Expected input:
        {
            "name": "Updated Name",
            "avatar": "😎"
        }

    Returns:
        Success (200):
            {
                "participantId": "uuid",
                "tenantId": "uuid",
                "name": "Updated Name",
                "avatar": "😎",
                "createdAt": "2024-01-01T00:00:00Z",
                "updatedAt": "2024-01-02T00:00:00Z"
            }

        Error (400): Invalid request body
        Error (401): Unauthorized
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

        # Validate participant authentication
        participant_context, error = require_participant_auth(event)
        if error:
            return error

        # Verify the token belongs to the participant being updated
        token_participant_id = participant_context["participantId"]
        if token_participant_id != participant_id:
            return error_response(
                403,
                "INSUFFICIENT_PERMISSIONS",
                "You can only update your own profile",
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

        # Get fields to update
        name = body.get("name")
        avatar = body.get("avatar")

        if not name and not avatar:
            return error_response(
                400,
                "MISSING_FIELDS",
                "At least one field (name or avatar) must be provided",
            )

        # Get participant from context (already validated by middleware)
        participant = participant_context["participant"]
        tenant_id = participant.get("tenantId")

        # If updating name, check for duplicates
        if name and name != participant.get("name"):
            try:
                # Scan for participants with the same name in this tenant (excluding current participant)
                existing_participants = scan(
                    GLOBAL_PARTICIPANTS_TABLE,
                    filter_expression="tenantId = :tenantId AND #name = :name AND participantId <> :participantId",
                    expression_attribute_values={
                        ":tenantId": tenant_id,
                        ":name": name.strip(),
                        ":participantId": participant_id,
                    },
                    expression_attribute_names={"#name": "name"},
                )

                if existing_participants and len(existing_participants) > 0:
                    return error_response(
                        409,
                        "NICKNAME_TAKEN",
                        f"The nickname '{name}' is already taken. Please choose a different name.",
                    )
            except Exception as e:
                print(f"DynamoDB scan error checking nickname: {str(e)}")
                # Continue with update if scan fails (don't block update)
                import traceback

                traceback.print_exc()

        # Build update expression
        update_expression_parts = []
        expression_attribute_values = {}
        expression_attribute_names = {}

        if name:
            update_expression_parts.append("#name = :name")
            expression_attribute_values[":name"] = name
            expression_attribute_names["#name"] = "name"

        if avatar:
            update_expression_parts.append("avatar = :avatar")
            expression_attribute_values[":avatar"] = avatar

        # Always update the updatedAt timestamp
        updated_at = datetime.utcnow().isoformat() + "Z"
        update_expression_parts.append("updatedAt = :updatedAt")
        expression_attribute_values[":updatedAt"] = updated_at

        update_expression = "SET " + ", ".join(update_expression_parts)

        # Update participant in database
        try:
            updated_participant = update_item(
                GLOBAL_PARTICIPANTS_TABLE,
                {"participantId": participant_id},
                update_expression,
                expression_attribute_values,
                expression_attribute_names if expression_attribute_names else None,
            )
        except Exception as e:
            print(f"DynamoDB update error: {str(e)}")
            return error_response(500, "DATABASE_ERROR", "Failed to update participant")

        # Return updated profile (exclude token for security)
        profile = {
            "participantId": updated_participant["participantId"],
            "tenantId": updated_participant["tenantId"],
            "name": updated_participant["name"],
            "avatar": updated_participant["avatar"],
            "createdAt": updated_participant["createdAt"],
            "updatedAt": updated_participant["updatedAt"],
        }

        response = {
            "statusCode": 200,
            "body": json.dumps(profile),
        }

        return add_cors_headers(response)

    except Exception as e:
        # Log unexpected errors
        print(f"Unexpected error in update global participant: {str(e)}")
        import traceback

        traceback.print_exc()

        return error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")
