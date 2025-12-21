"""
Property-Based Tests for Reset Admin Password Lambda Handler

Tests cover:
- Property 40: Password change effectiveness

These tests use Hypothesis for property-based testing to verify universal properties
across many randomly generated inputs.
"""

import json
import pytest
from hypothesis import given, settings, strategies as st
from unittest.mock import patch, MagicMock
import sys
import os

# Add lambda directories to path
lambda_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "lambda")
)
sys.path.insert(0, os.path.join(lambda_path, "reset_password_admin"))
sys.path.insert(0, os.path.join(lambda_path, "common"))


class TestResetPasswordAdminProperties:
    """Property-based tests for admin password reset"""

    @settings(max_examples=100, deadline=None)
    @given(
        old_password=st.text(min_size=8, max_size=100).filter(lambda x: x.strip()),
        new_password=st.text(min_size=8, max_size=100).filter(lambda x: x.strip()),
        username=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    )
    def test_property_40_password_change_effectiveness(
        self, old_password, new_password, username
    ):
        """
        Feature: global-participant-registration, Property 40: Password change effectiveness

        For any tenant admin password change, the admin should be able to login with
        the new password and unable to login with the old password.

        Validates: Requirements 13.4
        """
        # Skip if passwords are the same (edge case handled by idempotence test)
        if old_password == new_password:
            return

        with (
            patch("handler.get_item") as mock_reset_get_item,
            patch("handler.update_item") as mock_update_item,
        ):
            from handler import lambda_handler as reset_handler
            from auth import hash_password, verify_password
            import uuid

            # Arrange
            admin_id = str(uuid.uuid4())
            tenant_id = str(uuid.uuid4())

            # Create admin with old password
            old_password_hash = hash_password(old_password)
            admin = {
                "adminId": admin_id,
                "tenantId": tenant_id,
                "username": username,
                "passwordHash": old_password_hash,
                "role": "tenant_admin",
                "createdAt": "2024-01-01T00:00:00.000Z",
                "updatedAt": "2024-01-01T00:00:00.000Z",
            }

            # Mock get_item for reset password handler
            mock_reset_get_item.return_value = admin

            # Track the updated password hash
            updated_password_hash = None

            def update_item_side_effect(table_name, key, update_expr, expr_values):
                nonlocal updated_password_hash
                # Capture the new password hash
                updated_password_hash = expr_values.get(":passwordHash")
                return None

            mock_update_item.side_effect = update_item_side_effect

            # Act: Reset password
            reset_event = {
                "pathParameters": {"adminId": admin_id},
                "body": json.dumps({"newPassword": new_password}),
            }
            reset_response = reset_handler(reset_event, {})

            # Assert: Password reset succeeded
            assert reset_response["statusCode"] == 200
            reset_body = json.loads(reset_response["body"])
            assert reset_body["message"] == "Password reset successfully"

            # Verify update_item was called
            assert mock_update_item.called
            assert updated_password_hash is not None

            # Verify that old password no longer works with new hash
            assert not verify_password(old_password, updated_password_hash)
            # Verify that new password works with new hash
            assert verify_password(new_password, updated_password_hash)

    @settings(max_examples=100, deadline=None)
    @given(
        password=st.text(min_size=8, max_size=100).filter(lambda x: x.strip()),
    )
    def test_property_40_password_change_idempotence(self, password):
        """
        Feature: global-participant-registration, Property 40: Password change effectiveness

        For any password change to the same password value, the admin should still
        be able to login with that password.

        Validates: Requirements 13.4
        """
        with (
            patch("handler.get_item") as mock_get_item,
            patch("handler.update_item") as mock_update_item,
        ):
            from handler import lambda_handler
            from auth import hash_password, verify_password
            import uuid

            # Arrange
            admin_id = str(uuid.uuid4())
            tenant_id = str(uuid.uuid4())

            # Create admin with password
            password_hash = hash_password(password)
            admin = {
                "adminId": admin_id,
                "tenantId": tenant_id,
                "username": "testuser",
                "passwordHash": password_hash,
                "role": "tenant_admin",
            }

            mock_get_item.return_value = admin

            # Track the updated password hash
            updated_password_hash = None

            def update_item_side_effect(table_name, key, update_expr, expr_values):
                nonlocal updated_password_hash
                updated_password_hash = expr_values.get(":passwordHash")
                return None

            mock_update_item.side_effect = update_item_side_effect

            # Act: Reset password to the same value
            reset_event = {
                "pathParameters": {"adminId": admin_id},
                "body": json.dumps({"newPassword": password}),
            }
            reset_response = lambda_handler(reset_event, {})

            # Assert: Password reset succeeded
            assert reset_response["statusCode"] == 200

            # Verify the new hash still validates the same password
            assert updated_password_hash is not None
            assert verify_password(password, updated_password_hash)

    @settings(max_examples=100)
    @given(
        short_password=st.text(min_size=1, max_size=7).filter(lambda x: x.strip()),
    )
    def test_property_40_password_validation_too_short(self, short_password):
        """
        Feature: global-participant-registration, Property 40: Password change effectiveness

        For any password shorter than 8 characters, the password reset should be rejected.

        Validates: Requirements 13.4
        """
        with patch("handler.get_item") as mock_get_item:
            from handler import lambda_handler
            import uuid

            # Arrange
            admin_id = str(uuid.uuid4())
            admin = {
                "adminId": admin_id,
                "username": "testuser",
                "passwordHash": "old_hash",
            }

            mock_get_item.return_value = admin

            # Act
            reset_event = {
                "pathParameters": {"adminId": admin_id},
                "body": json.dumps({"newPassword": short_password}),
            }
            reset_response = lambda_handler(reset_event, {})

            # Assert: Should be rejected
            assert reset_response["statusCode"] == 400
            body = json.loads(reset_response["body"])
            assert body["error"]["code"] == "INVALID_FIELD_VALUE"
            assert "8 characters" in body["error"]["message"]

    @settings(max_examples=100)
    @given(
        password=st.text(min_size=8, max_size=100).filter(lambda x: x.strip()),
    )
    def test_property_40_password_change_nonexistent_admin(self, password):
        """
        Feature: global-participant-registration, Property 40: Password change effectiveness

        For any password reset attempt on a non-existent admin, the system should
        reject the request.

        Validates: Requirements 13.4
        """
        with patch("handler.get_item") as mock_get_item:
            from handler import lambda_handler
            import uuid

            # Arrange
            admin_id = str(uuid.uuid4())

            # Mock admin does not exist
            mock_get_item.return_value = None

            # Act
            reset_event = {
                "pathParameters": {"adminId": admin_id},
                "body": json.dumps({"newPassword": password}),
            }
            reset_response = lambda_handler(reset_event, {})

            # Assert: Should be rejected
            assert reset_response["statusCode"] == 404
            body = json.loads(reset_response["body"])
            assert body["error"]["code"] == "ADMIN_NOT_FOUND"
