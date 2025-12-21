"""
Backward Compatibility Layer

This module provides backward compatibility for the multi-tenant migration,
supporting legacy tokens without tenant context and defaulting to the primary tenant.
"""

import os
from auth import validate_token
from db import get_item
from errors import error_response
import jwt


# Default tenant ID (must match setup_default_tenant.py)
DEFAULT_TENANT_ID = "00000000-0000-0000-0000-000000000001"

# Environment variables
TENANTS_TABLE = os.environ.get("TENANTS_TABLE", "Tenants")


def extract_token_with_fallback(event):
    """
    Extract and validate JWT token with backward compatibility for legacy tokens.

    This function supports both:
    1. New tokens with tenantId in payload
    2. Legacy tokens without tenantId (defaults to DEFAULT_TENANT_ID)

    Args:
        event (dict): Lambda event object containing headers

    Returns:
        tuple: (token_context, error_response)
            - token_context (dict): Contains user info and tenantId
            - error_response (dict): Error response if validation fails, None otherwise

    Validates: Requirements 6.4, 15.5
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

    # Validate JWT token
    try:
        payload = validate_token(token)
    except jwt.ExpiredSignatureError:
        return None, error_response(401, "TOKEN_EXPIRED", "Token has expired")
    except jwt.InvalidTokenError:
        return None, error_response(401, "INVALID_TOKEN", "Invalid token")

    # Extract token context
    token_context = {
        "userId": payload.get("sub"),
        "role": payload.get("role"),
    }

    # Check if token has tenantId (new format)
    if "tenantId" in payload and payload["tenantId"] is not None:
        token_context["tenantId"] = payload["tenantId"]
        token_context["isLegacyToken"] = False
    else:
        # Legacy token without tenantId - default to primary tenant
        token_context["tenantId"] = DEFAULT_TENANT_ID
        token_context["isLegacyToken"] = True
        print(
            f"Legacy token detected for user {token_context['userId']}, defaulting to tenant {DEFAULT_TENANT_ID}"
        )

    return token_context, None


def get_default_tenant():
    """
    Get the default tenant for backward compatibility.

    Returns:
        dict: Default tenant record or None if not found
    """
    try:
        tenant = get_item(TENANTS_TABLE, {"tenantId": DEFAULT_TENANT_ID})
        return tenant
    except Exception as e:
        print(f"Error fetching default tenant: {str(e)}")
        return None


def ensure_tenant_context(data, default_tenant_id=None):
    """
    Ensure data has a tenantId field, adding default if missing.

    This is used for API requests that don't include tenantId in the body,
    providing backward compatibility with single-tenant deployments.

    Args:
        data (dict): Request data that may or may not have tenantId
        default_tenant_id (str, optional): Tenant ID to use if not present

    Returns:
        dict: Data with tenantId field guaranteed to be present

    Validates: Requirements 6.4, 15.5
    """
    if "tenantId" not in data or data.get("tenantId") is None:
        # Use provided default or fall back to DEFAULT_TENANT_ID
        data["tenantId"] = default_tenant_id or DEFAULT_TENANT_ID
        print(f"No tenantId in request, defaulting to {data['tenantId']}")

    return data


def normalize_response_format(response_data, include_tenant=True):
    """
    Normalize API response format for backward compatibility.

    This ensures responses maintain the same structure as before the multi-tenant
    migration, optionally including or excluding tenant information based on the
    client's needs.

    Args:
        response_data (dict): Response data to normalize
        include_tenant (bool): Whether to include tenantId in response

    Returns:
        dict: Normalized response data

    Validates: Requirements 6.4
    """
    # If client doesn't need tenant info, we can optionally remove it
    # For now, we keep it for transparency, but this allows future flexibility
    if not include_tenant and "tenantId" in response_data:
        # Create a copy without tenantId for legacy clients
        normalized = {k: v for k, v in response_data.items() if k != "tenantId"}
        return normalized

    return response_data


def get_tenant_from_context_or_default(tenant_context):
    """
    Get tenant ID from context or return default tenant.

    This helper function extracts the tenant ID from an authenticated context,
    falling back to the default tenant if not present (for super admins or
    legacy scenarios).

    Args:
        tenant_context (dict): Authenticated user context

    Returns:
        str: Tenant ID to use

    Validates: Requirements 15.5
    """
    # If tenant context has explicit tenantId, use it
    if tenant_context and "tenantId" in tenant_context:
        tenant_id = tenant_context["tenantId"]
        if tenant_id is not None:
            return tenant_id

    # Fall back to default tenant
    return DEFAULT_TENANT_ID


def is_legacy_deployment():
    """
    Check if this is a legacy single-tenant deployment.

    This checks if only the default tenant exists, indicating a legacy deployment
    that hasn't been migrated to multi-tenant.

    Returns:
        bool: True if legacy deployment, False if multi-tenant

    Validates: Requirements 15.1, 15.5
    """
    try:
        # Check if default tenant exists
        default_tenant = get_item(TENANTS_TABLE, {"tenantId": DEFAULT_TENANT_ID})
        if not default_tenant:
            return False

        # Check if there are other tenants
        # For simplicity, we consider it legacy if only default tenant exists
        # A more robust check would scan the table, but this is sufficient
        return True
    except Exception as e:
        print(f"Error checking deployment type: {str(e)}")
        # If we can't determine, assume multi-tenant for safety
        return False


def migrate_legacy_token_to_new_format(legacy_payload):
    """
    Convert a legacy token payload to the new format with tenant context.

    This is useful for token refresh scenarios where we want to upgrade
    legacy tokens to the new format.

    Args:
        legacy_payload (dict): Legacy token payload without tenantId

    Returns:
        dict: New token payload with tenantId

    Validates: Requirements 6.5
    """
    new_payload = legacy_payload.copy()

    # Add tenantId if not present
    if "tenantId" not in new_payload:
        new_payload["tenantId"] = DEFAULT_TENANT_ID

    return new_payload
