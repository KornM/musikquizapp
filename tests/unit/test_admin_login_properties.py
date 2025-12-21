"""
Property-Based Tests for Admin Login Lambda Handler

Tests cover:
- Property 30: Admin login returns tenant context

These tests use Hypothesis for property-based testing to verify universal properties
across many randomly generated inputs.
"""

import json
import pytest
from hypothesis import given, settings, strategies as st
from unittest.mock import patch, MagicMock
import sys
import os
import jwt as pyjwt

# Add lambda directories to path
lambda_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "lambda")
)
sys.path.insert(0, os.path.join(lambda_path, "admin_login"))
sys.path.insert(0, os.path.join(lambda_path, "common"))


class TestAdminLoginProperties:
    """Property-based tests for admin login"""

    @settings(max_examples=100, deadline=None)
    @given(
        username=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
        password=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
        role=st.sampled_from(["super_admin", "tenant_admin"]),
    )
    def test_property_30_admin_login_returns_tenant_context(
        self, username, password, role
    ):
        """
        Feature: global-participant-registration, Property 30: Admin login returns tenant context

        For any tenant admin login, the response should include the admin's tenantId.

        Validates: Requirements 9.4
        """
        # Import handler first
        from handler import lambda_handler

        with (
            patch("db.query") as mock_query,
            patch("auth.verify_password") as mock_verify_password,
        ):
            import uuid

            # Arrange
            admin_id = str(uuid.uuid4())
            tenant_id = str(uuid.uuid4()) if role == "tenant_admin" else None

            # Mock admin exists
            admin_record = {
                "adminId": admin_id,
                "username": username,
                "passwordHash": "hashed_password",
                "role": role,
            }

            if tenant_id:
                admin_record["tenantId"] = tenant_id

            mock_query.return_value = [admin_record]

            # Mock password verification succeeds
            mock_verify_password.return_value = True

            event = {
                "body": json.dumps({"username": username, "password": password}),
            }
            context = {}

            # Act
            response = lambda_handler(event, context)

            # Assert
            assert response["statusCode"] == 200
            body = json.loads(response["body"])

            # Verify token is present
            assert "token" in body
            assert "expiresIn" in body

            # Decode the token to verify it contains tenant context
            token = body["token"]
            # Use the same secret as in auth.py
            jwt_secret = os.environ.get(
                "JWT_SECRET", "default-secret-change-in-production"
            )
            decoded = pyjwt.decode(token, jwt_secret, algorithms=["HS256"])

            # Verify token contains correct user ID and role
            assert decoded["sub"] == admin_id
            assert decoded["role"] == role

            # For tenant admins, verify tenantId is in token and response
            if role == "tenant_admin":
                assert "tenantId" in decoded
                assert decoded["tenantId"] == tenant_id
                assert "tenantId" in body
                assert body["tenantId"] == tenant_id
            else:
                # For super admins, tenantId should not be in response
                # (it may or may not be in token depending on implementation)
                assert "tenantId" not in body

    @settings(max_examples=100, deadline=None)
    @given(
        username=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
        password=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    )
    def test_property_30_admin_login_tenant_admin_always_has_tenant_id(
        self, username, password
    ):
        """
        Feature: global-participant-registration, Property 30: Admin login returns tenant context

        For any tenant admin login, the JWT token should always contain a tenantId field.

        Validates: Requirements 9.4
        """
        with (
            patch("handler.query") as mock_query,
            patch("handler.verify_password") as mock_verify_password,
        ):
            from handler import lambda_handler
            import uuid

            # Arrange
            admin_id = str(uuid.uuid4())
            tenant_id = str(uuid.uuid4())

            # Mock tenant admin exists
            admin_record = {
                "adminId": admin_id,
                "username": username,
                "passwordHash": "hashed_password",
                "role": "tenant_admin",
                "tenantId": tenant_id,
            }

            mock_query.return_value = [admin_record]
            mock_verify_password.return_value = True

            event = {
                "body": json.dumps({"username": username, "password": password}),
            }
            context = {}

            # Act
            response = lambda_handler(event, context)

            # Assert
            assert response["statusCode"] == 200
            body = json.loads(response["body"])

            # Verify token contains tenantId
            token = body["token"]
            jwt_secret = os.environ.get(
                "JWT_SECRET", "default-secret-change-in-production"
            )
            decoded = pyjwt.decode(token, jwt_secret, algorithms=["HS256"])

            assert "tenantId" in decoded
            assert decoded["tenantId"] == tenant_id

            # Verify response body contains tenantId
            assert "tenantId" in body
            assert body["tenantId"] == tenant_id
