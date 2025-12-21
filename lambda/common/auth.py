"""
Authentication utility module for JWT token management and password hashing.
"""

import jwt
import os
from datetime import datetime, timedelta
from passlib.hash import pbkdf2_sha256


# JWT secret should be stored in AWS Secrets Manager in production
JWT_SECRET = os.environ.get("JWT_SECRET", "default-secret-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


def generate_token(user_id, role, tenant_id=None):
    """
    Generate a JWT token for authenticated users.

    Args:
        user_id (str): Unique identifier for the user
        role (str): User role ('admin', 'super_admin', 'tenant_admin', or 'participant')
        tenant_id (str, optional): Tenant ID for tenant-scoped users

    Returns:
        str: JWT token string
    """
    now = datetime.utcnow()
    expiration = now + timedelta(hours=JWT_EXPIRATION_HOURS)

    payload = {
        "sub": user_id,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expiration.timestamp()),
    }

    # Add tenant_id to payload if provided
    if tenant_id:
        payload["tenantId"] = tenant_id

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def validate_token(token, allow_legacy=True):
    """
    Validate and decode a JWT token.

    Args:
        token (str): JWT token string
        allow_legacy (bool): If True, accept tokens without tenantId (backward compatibility)

    Returns:
        dict: Decoded token payload if valid

    Raises:
        jwt.ExpiredSignatureError: If token has expired
        jwt.InvalidTokenError: If token is invalid
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        # For backward compatibility, legacy tokens without tenantId are still valid
        # The calling code can add a default tenantId if needed
        if not allow_legacy and "tenantId" not in payload:
            raise jwt.InvalidTokenError("Token missing tenant context")

        return payload
    except jwt.ExpiredSignatureError:
        raise jwt.ExpiredSignatureError("Token has expired")
    except jwt.InvalidTokenError:
        raise jwt.InvalidTokenError("Invalid token")


def hash_password(password):
    """
    Hash a password using PBKDF2-SHA256.

    Args:
        password (str): Plain text password

    Returns:
        str: Hashed password string
    """
    return pbkdf2_sha256.hash(password)


def verify_password(password, password_hash):
    """
    Verify a password against a PBKDF2-SHA256 hash.

    Args:
        password (str): Plain text password to verify
        password_hash (str): Hashed password to compare against

    Returns:
        bool: True if password matches, False otherwise
    """
    return pbkdf2_sha256.verify(password, password_hash)
