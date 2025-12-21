"""
Property-Based Tests for Update Tenant Admin Lambda Handler

Tests cover:
- Property 38: Admin update persistence
- Property 41: Admin tenant reassignment

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
sys.path.insert(0, os.path.join(lambda_path, "update_tenant_admin"))
sys.path.insert(0, os.path.join(lambda_path, "common"))


class TestTenantAdminUpdateProperties:
    """Property-based tests for tenant admin updates"""

    @settings(max_examples=100, deadline=None)
    @given(
        original_username=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
        new_username=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
        new_email=st.one_of(st.none(), st.emails()),
    )
    def test_property_38_admin_update_persistence(
        self, original_username, new_username, new_email
    ):
        """
        Feature: global-participant-registration, Property 38: Admin update persistence

        For any tenant admin update request, the changes should be saved to the database
        and reflected in subsequent queries.

        Validates: Requirements 13.2
        """
        with (
            patch("handler.query") as mock_query,
            patch("handler.get_item") as mock_get_item,
            patch("handler.update_item") as mock_update_item,
        ):
            from handler import lambda_handler
            import uuid

            # Arrange
            admin_id = str(uuid.uuid4())
            tenant_id = str(uuid.uuid4())

            # Mock existing admin
            existing_admin = {
                "adminId": admin_id,
                "tenantId": tenant_id,
                "username": original_username,
                "email": "old@example.com",
                "role": "tenant_admin",
                "passwordHash": "hashed_password",
                "createdAt": "2024-01-01T00:00:00.000Z",
                "updatedAt": "2024-01-01T00:00:00.000Z",
            }

            mock_get_item.return_value = existing_admin

            # Mock no username conflict (if username is changing)
            if new_username != original_username:
                mock_query.return_value = []
            else:
                mock_query.return_value = [existing_admin]

            # Mock updated admin
            updated_admin = existing_admin.copy()
            updated_admin["username"] = new_username
            if new_email is not None:
                updated_admin["email"] = new_email
            updated_admin["updatedAt"] = "2024-01-02T00:00:00.000Z"

            mock_update_item.return_value = updated_admin

            request_body = {"username": new_username}
            if new_email is not None:
                request_body["email"] = new_email

            event = {
                "pathParameters": {"adminId": admin_id},
                "body": json.dumps(request_body),
            }
            context = {}

            # Act
            response = lambda_handler(event, context)

            # Assert
            assert response["statusCode"] == 200
            body = json.loads(response["body"])

            # Verify updated values are in response
            assert body["username"] == new_username
            if new_email is not None:
                assert body["email"] == new_email

            # Verify update_item was called if there were changes
            if new_username != original_username or (
                new_email is not None and new_email != "old@example.com"
            ):
                assert mock_update_item.called

    @settings(max_examples=100, deadline=None)
    @given(
        username=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    )
    def test_property_41_admin_tenant_reassignment(self, username):
        """
        Feature: global-participant-registration, Property 41: Admin tenant reassignment

        For any tenant admin reassigned to a different tenant, the admin's tenantId
        should be updated and they should only see data from the new tenant.

        Validates: Requirements 13.5
        """
        with (
            patch("handler.query") as mock_query,
            patch("handler.get_item") as mock_get_item,
            patch("handler.update_item") as mock_update_item,
        ):
            from handler import lambda_handler
            import uuid

            # Arrange
            admin_id = str(uuid.uuid4())
            old_tenant_id = str(uuid.uuid4())
            new_tenant_id = str(uuid.uuid4())

            # Mock existing admin
            existing_admin = {
                "adminId": admin_id,
                "tenantId": old_tenant_id,
                "username": username,
                "email": "admin@example.com",
                "role": "tenant_admin",
                "passwordHash": "hashed_password",
                "createdAt": "2024-01-01T00:00:00.000Z",
                "updatedAt": "2024-01-01T00:00:00.000Z",
            }

            # Mock new tenant exists and is active
            new_tenant = {
                "tenantId": new_tenant_id,
                "name": "New Tenant",
                "status": "active",
            }

            def get_item_side_effect(table_name, key):
                if "adminId" in key:
                    return existing_admin
                elif "tenantId" in key:
                    return new_tenant
                return None

            mock_get_item.side_effect = get_item_side_effect

            # Mock no username conflict
            mock_query.return_value = []

            # Mock updated admin with new tenantId
            updated_admin = existing_admin.copy()
            updated_admin["tenantId"] = new_tenant_id
            updated_admin["updatedAt"] = "2024-01-02T00:00:00.000Z"

            mock_update_item.return_value = updated_admin

            event = {
                "pathParameters": {"adminId": admin_id},
                "body": json.dumps({"tenantId": new_tenant_id}),
            }
            context = {}

            # Act
            response = lambda_handler(event, context)

            # Assert
            assert response["statusCode"] == 200
            body = json.loads(response["body"])

            # Verify tenantId was updated
            assert body["tenantId"] == new_tenant_id
            assert body["tenantId"] != old_tenant_id

            # Verify update_item was called
            assert mock_update_item.called
            call_args = mock_update_item.call_args

            # Verify the update expression includes tenantId
            update_expression = call_args[0][2]
            assert "tenantId" in update_expression

            expression_values = call_args[0][3]
            assert ":tenantId" in expression_values
            assert expression_values[":tenantId"] == new_tenant_id

    @settings(max_examples=100, deadline=None)
    @given(
        username=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    )
    def test_property_41_admin_tenant_reassignment_inactive_tenant(self, username):
        """
        Feature: global-participant-registration, Property 41: Admin tenant reassignment

        For any tenant admin reassignment to an inactive tenant, the system should
        reject the request.

        Validates: Requirements 13.5
        """
        with patch("handler.get_item") as mock_get_item:
            from handler import lambda_handler
            import uuid

            # Arrange
            admin_id = str(uuid.uuid4())
            old_tenant_id = str(uuid.uuid4())
            new_tenant_id = str(uuid.uuid4())

            # Mock existing admin
            existing_admin = {
                "adminId": admin_id,
                "tenantId": old_tenant_id,
                "username": username,
                "email": "admin@example.com",
                "role": "tenant_admin",
                "passwordHash": "hashed_password",
            }

            # Mock new tenant exists but is inactive
            new_tenant = {
                "tenantId": new_tenant_id,
                "name": "Inactive Tenant",
                "status": "inactive",
            }

            def get_item_side_effect(table_name, key):
                if "adminId" in key:
                    return existing_admin
                elif "tenantId" in key:
                    return new_tenant
                return None

            mock_get_item.side_effect = get_item_side_effect

            event = {
                "pathParameters": {"adminId": admin_id},
                "body": json.dumps({"tenantId": new_tenant_id}),
            }
            context = {}

            # Act
            response = lambda_handler(event, context)

            # Assert - Should be rejected
            assert response["statusCode"] == 400
            body = json.loads(response["body"])
            assert body["error"]["code"] == "TENANT_INACTIVE"

    @settings(max_examples=100, deadline=None)
    @given(
        username=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    )
    def test_property_41_admin_tenant_reassignment_nonexistent_tenant(self, username):
        """
        Feature: global-participant-registration, Property 41: Admin tenant reassignment

        For any tenant admin reassignment to a non-existent tenant, the system should
        reject the request.

        Validates: Requirements 13.5
        """
        with patch("handler.get_item") as mock_get_item:
            from handler import lambda_handler
            import uuid

            # Arrange
            admin_id = str(uuid.uuid4())
            old_tenant_id = str(uuid.uuid4())
            new_tenant_id = str(uuid.uuid4())

            # Mock existing admin
            existing_admin = {
                "adminId": admin_id,
                "tenantId": old_tenant_id,
                "username": username,
                "email": "admin@example.com",
                "role": "tenant_admin",
                "passwordHash": "hashed_password",
            }

            def get_item_side_effect(table_name, key):
                if "adminId" in key:
                    return existing_admin
                elif "tenantId" in key:
                    return None  # Tenant doesn't exist
                return None

            mock_get_item.side_effect = get_item_side_effect

            event = {
                "pathParameters": {"adminId": admin_id},
                "body": json.dumps({"tenantId": new_tenant_id}),
            }
            context = {}

            # Act
            response = lambda_handler(event, context)

            # Assert - Should be rejected
            assert response["statusCode"] == 400
            body = json.loads(response["body"])
            assert body["error"]["code"] == "INVALID_TENANT_ASSIGNMENT"
