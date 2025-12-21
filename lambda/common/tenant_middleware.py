"""
Tenant Validation Middleware

This module provides middleware functions for validating tenant context in JWT tokens
and ensuring tenant isolation across API endpoints.
"""

import os
from auth import validate_token
from db import get_item
from errors import error_response
import jwt


# Environment variables
TENANTS_TABLE = os.environ.get("TENANTS_TABLE", "MusicQuiz-Tenants")


def extract_tenant_from_token(event):
    """
    Extract and validate tenant context from JWT token in the Authorization header.

    Args:
        event (dict): Lambda event object containing headers

    Returns:
        tuple: (tenant_context, error_response)
            - tenant_context (dict): Contains adminId, role, tenantId (if present)
            - error_response (dict): Error response if validation fails, None otherwise

    Example tenant_context:
        {
            "adminId": "uuid",
            "role": "tenant_admin",
            "tenantId": "uuid"
        }
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

    # Extract tenant context
    tenant_context = {
        "adminId": payload.get("sub"),
        "role": payload.get("role"),
    }

    # Add tenantId if present (will be None for super admins)
    if "tenantId" in payload:
        tenant_context["tenantId"] = payload["tenantId"]

    return tenant_context, None


def validate_tenant_active(tenant_id):
    """
    Validate that a tenant exists and is active.

    Args:
        tenant_id (str): Tenant ID to validate

    Returns:
        tuple: (tenant, error_response)
            - tenant (dict): Tenant record if valid and active
            - error_response (dict): Error response if validation fails, None otherwise
    """
    if not tenant_id:
        return None, error_response(400, "MISSING_TENANT_ID", "Tenant ID is required")

    try:
        tenant = get_item(TENANTS_TABLE, {"tenantId": tenant_id})
    except Exception as e:
        print(f"Error fetching tenant {tenant_id}: {str(e)}")
        return None, error_response(500, "DATABASE_ERROR", "Failed to validate tenant")

    if not tenant:
        return None, error_response(
            404, "TENANT_NOT_FOUND", f"Tenant {tenant_id} not found"
        )

    if tenant.get("status") != "active":
        return None, error_response(
            400,
            "TENANT_INACTIVE",
            f"Tenant {tenant_id} is not active",
            {"status": tenant.get("status")},
        )

    return tenant, None


def require_tenant_admin(event):
    """
    Middleware to require tenant admin authentication and extract tenant context.

    This function:
    1. Extracts and validates the JWT token
    2. Verifies the user has admin role
    3. Validates the tenant exists and is active
    4. Returns tenant context for use in the handler

    Args:
        event (dict): Lambda event object

    Returns:
        tuple: (tenant_context, error_response)
            - tenant_context (dict): Contains adminId, role, tenantId, and tenant record
            - error_response (dict): Error response if validation fails, None otherwise

    Example usage in a Lambda handler:
        tenant_context, error = require_tenant_admin(event)
        if error:
            return error

        # Use tenant_context
        tenant_id = tenant_context["tenantId"]
        admin_id = tenant_context["adminId"]
    """
    # Extract tenant context from token
    tenant_context, error = extract_tenant_from_token(event)
    if error:
        return None, error

    # Check if user has admin role
    role = tenant_context.get("role")
    if role not in ["admin", "tenant_admin", "super_admin"]:
        return None, error_response(
            403, "INSUFFICIENT_PERMISSIONS", "Admin role required"
        )

    # For tenant admins, validate tenant is active
    tenant_id = tenant_context.get("tenantId")
    if tenant_id:
        tenant, error = validate_tenant_active(tenant_id)
        if error:
            return None, error

        # Add tenant record to context
        tenant_context["tenant"] = tenant

    return tenant_context, None


def validate_tenant_access(tenant_context, resource_tenant_id):
    """
    Validate that the authenticated user has access to a resource belonging to a specific tenant.

    This enforces tenant isolation by ensuring:
    - Tenant admins can only access resources from their own tenant
    - Super admins can access resources from any tenant

    Args:
        tenant_context (dict): Tenant context from require_tenant_admin
        resource_tenant_id (str): Tenant ID of the resource being accessed

    Returns:
        dict: Error response if access denied, None if access allowed
    """
    user_role = tenant_context.get("role")
    user_tenant_id = tenant_context.get("tenantId")

    # Super admins can access any tenant's resources
    if user_role == "super_admin":
        return None

    # Tenant admins can only access their own tenant's resources
    if user_tenant_id != resource_tenant_id:
        print(
            f"Cross-tenant access attempt: user tenant {user_tenant_id}, "
            f"resource tenant {resource_tenant_id}"
        )
        return error_response(
            403,
            "CROSS_TENANT_ACCESS",
            "You do not have permission to access this resource",
        )

    return None
