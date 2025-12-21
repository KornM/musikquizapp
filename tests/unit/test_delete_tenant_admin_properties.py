"""
Property-Based Tests for Tenant Admin Deletion

Tests cover:
- Property 39: Admin deletion blocks access

These tests use Hypothesis for property-based testing to verify universal properties
about tenant admin deletion and access control.
"""

import json
import os
from unittest.mock import MagicMock, patch
from hypothesis import given, settings, strategies as st
import pytest
import sys

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "lambda"))

from delete_tenant_admin.handler import lambda_handler as delete_admin_handler
from admin_login.handler import lambda_handler as login_handler


class TestProperty39AdminDeletionBlocksAccess:
    """
    Property 39: Admin deletion blocks access

    For any tenant admin that is deleted, subsequent login attempts with that
    admin's credentials should fail.
    """

    @settings(max_examples=100)
    @given(
        username=st.text(
            min_size=3,
            max_size=50,
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_-"
            ),
        ),
        password=st.text(min_size=8, max_size=100),
        admin_id=st.uuids(),
        tenant_id=st.uuids(),
    )
    @patch.dict(
        os.environ, {"ADMINS_TABLE": "TestAdmins", "JWT_SECRET": "test-secret-key"}
    )
    def test_property_39_admin_deletion_blocks_login(
        self, username, password, admin_id, tenant_id
    ):
        """
        Feature: global-participant-registration, Property 39: Admin deletion blocks access

        For any tenant admin that is deleted, subsequent login attempts with that
        admin's credentials should fail.
        """
        import bcrypt

        # Hash the password
        password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        admin_record = {
            "adminId": str(admin_id),
            "username": username,
            "passwordHash": password_hash,
            "tenantId": str(tenant_id),
            "role": "tenant_admin",
            "createdAt": "2024-01-01T00:00:00Z",
        }

        # Mock DynamoDB for delete operation
        with (
            patch("delete_tenant_admin.handler.get_item") as mock_get_delete,
            patch("delete_tenant_admin.handler.delete_item") as mock_delete,
        ):
            # Admin exists before deletion
            mock_get_delete.return_value = admin_record

            # Delete the admin
            delete_event = {"pathParameters": {"adminId": str(admin_id)}, "headers": {}}

            delete_response = delete_admin_handler(delete_event, {})

            # Verify deletion was successful
            assert delete_response["statusCode"] == 200
            mock_delete.assert_called_once()

        # Now try to login with the deleted admin's credentials
        with patch("admin_login.handler.query") as mock_query_login:
            # Simulate that the admin no longer exists in the database
            mock_query_login.return_value = []

            login_event = {
                "body": json.dumps({"username": username, "password": password}),
                "headers": {},
            }

            login_response = login_handler(login_event, {})

            # Verify login fails
            assert login_response["statusCode"] == 401
            response_body = json.loads(login_response["body"])
            assert response_body["error"]["code"] == "INVALID_CREDENTIALS"

    @settings(max_examples=100)
    @given(
        admin_id=st.uuids(),
    )
    @patch.dict(os.environ, {"ADMINS_TABLE": "TestAdmins"})
    def test_property_39_nonexistent_admin_deletion_fails(self, admin_id):
        """
        Feature: global-participant-registration, Property 39: Admin deletion blocks access

        For any admin ID that doesn't exist, deletion attempts should fail with 404.
        """
        with patch("delete_tenant_admin.handler.get_item") as mock_get:
            # Admin doesn't exist
            mock_get.return_value = None

            event = {"pathParameters": {"adminId": str(admin_id)}, "headers": {}}

            response = delete_admin_handler(event, {})

            # Verify deletion fails
            assert response["statusCode"] == 404
            response_body = json.loads(response["body"])
            assert response_body["error"]["code"] == "ADMIN_NOT_FOUND"

    @settings(max_examples=100)
    @given(
        username=st.text(
            min_size=3,
            max_size=50,
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_-"
            ),
        ),
        password=st.text(min_size=8, max_size=100),
        admin_id=st.uuids(),
        tenant_id=st.uuids(),
    )
    @patch.dict(
        os.environ, {"ADMINS_TABLE": "TestAdmins", "JWT_SECRET": "test-secret-key"}
    )
    def test_property_39_deleted_admin_cannot_access_resources(
        self, username, password, admin_id, tenant_id
    ):
        """
        Feature: global-participant-registration, Property 39: Admin deletion blocks access

        For any deleted admin, attempts to use their credentials to access
        protected resources should fail.
        """
        import bcrypt

        password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        admin_record = {
            "adminId": str(admin_id),
            "username": username,
            "passwordHash": password_hash,
            "tenantId": str(tenant_id),
            "role": "tenant_admin",
            "createdAt": "2024-01-01T00:00:00Z",
        }

        # Delete the admin
        with (
            patch("delete_tenant_admin.handler.get_item") as mock_get,
            patch("delete_tenant_admin.handler.delete_item") as mock_delete,
        ):
            mock_get.return_value = admin_record

            delete_event = {"pathParameters": {"adminId": str(admin_id)}, "headers": {}}

            delete_response = delete_admin_handler(delete_event, {})
            assert delete_response["statusCode"] == 200

        # Verify login fails after deletion
        with patch("admin_login.handler.query") as mock_query:
            mock_query.return_value = []  # Admin no longer in database

            login_event = {
                "body": json.dumps({"username": username, "password": password}),
                "headers": {},
            }

            login_response = login_handler(login_event, {})

            # Login should fail
            assert login_response["statusCode"] == 401
            response_body = json.loads(login_response["body"])
            assert response_body["error"]["code"] == "INVALID_CREDENTIALS"

    @patch.dict(os.environ, {"ADMINS_TABLE": "TestAdmins"})
    def test_property_39_missing_admin_id_in_path(self):
        """
        Feature: global-participant-registration, Property 39: Admin deletion blocks access

        For any deletion request without an admin ID, the system should reject it.
        """
        event = {"pathParameters": {}, "headers": {}}

        response = delete_admin_handler(event, {})

        assert response["statusCode"] == 400
        response_body = json.loads(response["body"])
        assert response_body["error"]["code"] == "MISSING_FIELDS"

    @settings(max_examples=100)
    @given(
        admin_id=st.uuids(),
        tenant_id=st.uuids(),
    )
    def test_property_39_deletion_is_permanent(self, admin_id, tenant_id):
        """
        Feature: global-participant-registration, Property 39: Admin deletion blocks access

        For any admin that is deleted, the deletion should be permanent and
        the admin record should be removed from the database.
        """
        admin_record = {
            "adminId": str(admin_id),
            "username": "test_admin",
            "passwordHash": "hashed_password",
            "tenantId": str(tenant_id),
            "role": "tenant_admin",
            "createdAt": "2024-01-01T00:00:00Z",
        }

        with (
            patch("delete_tenant_admin.handler.ADMINS_TABLE", "TestAdmins"),
            patch("delete_tenant_admin.handler.get_item") as mock_get,
            patch("delete_tenant_admin.handler.delete_item") as mock_delete,
        ):
            mock_get.return_value = admin_record

            event = {"pathParameters": {"adminId": str(admin_id)}, "headers": {}}

            response = delete_admin_handler(event, {})

            # Verify deletion was called with correct parameters
            assert response["statusCode"] == 200
            mock_delete.assert_called_once_with(
                "TestAdmins", {"adminId": str(admin_id)}
            )

            # Verify response contains confirmation
            response_body = json.loads(response["body"])
            assert response_body["adminId"] == str(admin_id)
            assert "deleted successfully" in response_body["message"].lower()
