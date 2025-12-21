"""
Participant Authentication Middleware

This module provides middleware functions for validating participant JWT tokens
and ensuring participant authentication across API endpoints.
"""

import os
import jwt
from auth import validate_token
from db import get_item
from errors import error_response


# Environment variables
GLOBAL_PARTICIPANTS_TABLE = os.environ.get(
    "GLOBAL_PARTICIPANTS_TABLE", "GlobalParticipants"
)


def extract_participant_from_token(event):
    """
    Extract and validate participant context from JWT token in the Authorization header.

    This function:
    1. Extracts the Authorization header from the event
    2. Validates the JWT token format and signature
    3. Verifies the token hasn't expired
    4. Extracts participantId and tenantId from the token payload
    5. Returns participant context for use in handlers

    Args:
        event (dict): Lambda event object containing headers

    Returns:
        tuple: (participant_context, error_response)
            - participant_context (dict): Contains participantId, tenantId, role
            - error_response (dict): Error response if validation fails, None otherwise

    Example participant_context:
        {
            "participantId": "uuid",
            "tenantId": "uuid",
            "role": "participant"
        }

    Validates: Requirements 7.3, 7.4, 7.5
    """
    # Extract Authorization header
    headers = event.get("headers", {})
    auth_header = headers.get("Authorization") or headers.get("authorization")

    if not auth_header:
        return None, error_response(
            401, "MISSING_TOKEN", "Authorization header is required"
        )

    # Extract token from "Bearer <token>" format
    if not auth_header.startswith("Bearer "):
        return None, error_response(
            401,
            "INVALID_AUTH_FORMAT",
            "Authorization header must be 'Bearer <token>'",
        )

    token = auth_header[7:]  # Remove "Bearer " prefix

    # Validate JWT token signature and expiration
    try:
        payload = validate_token(token)
    except jwt.ExpiredSignatureError:
        return None, error_response(401, "TOKEN_EXPIRED", "Token has expired")
    except jwt.InvalidTokenError:
        return None, error_response(401, "INVALID_TOKEN", "Invalid token")

    # Extract participant context from token payload
    participant_id = payload.get("sub")
    tenant_id = payload.get("tenantId")
    role = payload.get("role")

    # Validate that this is a participant token
    if role != "participant":
        return None, error_response(
            403,
            "INSUFFICIENT_PERMISSIONS",
            "Participant authentication required",
        )

    # Validate required fields are present in token
    if not participant_id:
        return None, error_response(
            401, "INVALID_TOKEN", "Token missing participant ID"
        )

    if not tenant_id:
        return None, error_response(401, "INVALID_TOKEN", "Token missing tenant ID")

    # Build participant context
    participant_context = {
        "participantId": participant_id,
        "tenantId": tenant_id,
        "role": role,
    }

    return participant_context, None


def require_participant_auth(event):
    """
    Middleware to require participant authentication and extract participant context.

    This function:
    1. Extracts and validates the JWT token
    2. Verifies the user has participant role
    3. Validates the participant exists in the database
    4. Returns participant context for use in the handler

    Args:
        event (dict): Lambda event object

    Returns:
        tuple: (participant_context, error_response)
            - participant_context (dict): Contains participantId, tenantId, role, and participant record
            - error_response (dict): Error response if validation fails, None otherwise

    Example usage in a Lambda handler:
        participant_context, error = require_participant_auth(event)
        if error:
            return error

        # Use participant_context
        participant_id = participant_context["participantId"]
        tenant_id = participant_context["tenantId"]
        participant = participant_context["participant"]

    Validates: Requirements 7.3, 7.4, 7.5
    """
    # Extract participant context from token
    participant_context, error = extract_participant_from_token(event)
    if error:
        return None, error

    participant_id = participant_context["participantId"]

    # Verify participant exists in database
    try:
        participant = get_item(
            GLOBAL_PARTICIPANTS_TABLE, {"participantId": participant_id}
        )
    except Exception as e:
        print(f"Error fetching participant {participant_id}: {str(e)}")
        return None, error_response(
            500, "DATABASE_ERROR", "Failed to validate participant"
        )

    if not participant:
        return None, error_response(
            404,
            "PARTICIPANT_NOT_FOUND",
            f"Participant {participant_id} not found",
        )

    # Verify tenant ID in token matches participant record
    if participant.get("tenantId") != participant_context["tenantId"]:
        print(
            f"Token tenant mismatch: token has {participant_context['tenantId']}, "
            f"participant record has {participant.get('tenantId')}"
        )
        return None, error_response(
            401, "INVALID_TOKEN", "Token tenant ID does not match participant record"
        )

    # Add participant record to context
    participant_context["participant"] = participant

    return participant_context, None


def validate_participant_tenant_access(participant_context, resource_tenant_id):
    """
    Validate that the authenticated participant has access to a resource belonging to a specific tenant.

    This enforces tenant isolation by ensuring participants can only access resources
    from their own tenant.

    Args:
        participant_context (dict): Participant context from require_participant_auth
        resource_tenant_id (str): Tenant ID of the resource being accessed

    Returns:
        dict: Error response if access denied, None if access allowed

    Validates: Requirements 11.2, 11.3
    """
    participant_tenant_id = participant_context.get("tenantId")

    # Participants can only access resources from their own tenant
    if participant_tenant_id != resource_tenant_id:
        print(
            f"Cross-tenant access attempt: participant tenant {participant_tenant_id}, "
            f"resource tenant {resource_tenant_id}"
        )
        return error_response(
            403,
            "CROSS_TENANT_ACCESS",
            "You do not have permission to access this resource",
        )

    return None
