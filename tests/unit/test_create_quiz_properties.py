"""
Property-Based Tests for Create Quiz Session Lambda Handler

Tests cover:
- Property 31: Session inherits admin tenant

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
sys.path.insert(0, os.path.join(lambda_path, "create_quiz"))
sys.path.insert(0, os.path.join(lambda_path, "common"))


class TestCreateQuizProperties:
    """Property-based tests for quiz session creation"""

    @settings(max_examples=100, deadline=None)
    @given(
        title=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
        description=st.text(max_size=500),
        media_type=st.sampled_from(["none", "audio", "image"]),
    )
    def test_property_31_session_inherits_admin_tenant(
        self, title, description, media_type
    ):
        """
        Feature: global-participant-registration, Property 31: Session inherits admin tenant

        For any session created by a tenant admin, the session record should contain
        the same tenantId as the admin who created it.

        Validates: Requirements 10.1
        """
        with (
            patch("handler.require_tenant_admin") as mock_require_tenant_admin,
            patch("handler.put_item") as mock_put_item,
        ):
            from handler import lambda_handler
            import uuid

            # Arrange
            admin_id = str(uuid.uuid4())
            tenant_id = str(uuid.uuid4())

            # Mock tenant admin authentication
            tenant_context = {
                "adminId": admin_id,
                "role": "tenant_admin",
                "tenantId": tenant_id,
                "tenant": {
                    "tenantId": tenant_id,
                    "name": "Test Tenant",
                    "status": "active",
                },
            }

            mock_require_tenant_admin.return_value = (tenant_context, None)
            mock_put_item.return_value = {}

            event = {
                "headers": {"Authorization": "Bearer fake_token"},
                "body": json.dumps(
                    {
                        "title": title,
                        "description": description,
                        "mediaType": media_type,
                    }
                ),
            }
            context = {}

            # Act
            response = lambda_handler(event, context)

            # Assert
            assert response["statusCode"] == 201
            body = json.loads(response["body"])

            # Verify session contains the admin's tenantId
            assert "tenantId" in body
            assert body["tenantId"] == tenant_id

            # Verify the stored session has the correct tenantId
            assert mock_put_item.called
            call_args = mock_put_item.call_args
            stored_session = call_args[0][1]  # Second argument is the item

            assert stored_session["tenantId"] == tenant_id
            assert stored_session["createdBy"] == admin_id
            assert stored_session["title"] == title
            assert stored_session["description"] == description
            assert stored_session["mediaType"] == media_type

    @settings(max_examples=100, deadline=None)
    @given(
        title=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
        description=st.text(max_size=500),
    )
    def test_property_31_multiple_admins_different_tenants(self, title, description):
        """
        Feature: global-participant-registration, Property 31: Session inherits admin tenant

        For any two admins from different tenants creating sessions, each session
        should inherit the respective admin's tenantId.

        Validates: Requirements 10.1
        """
        with (
            patch("handler.require_tenant_admin") as mock_require_tenant_admin,
            patch("handler.put_item") as mock_put_item,
        ):
            from handler import lambda_handler
            import uuid

            # Arrange - Admin 1
            admin_id_1 = str(uuid.uuid4())
            tenant_id_1 = str(uuid.uuid4())

            tenant_context_1 = {
                "adminId": admin_id_1,
                "role": "tenant_admin",
                "tenantId": tenant_id_1,
                "tenant": {
                    "tenantId": tenant_id_1,
                    "name": "Tenant 1",
                    "status": "active",
                },
            }

            mock_require_tenant_admin.return_value = (tenant_context_1, None)
            mock_put_item.return_value = {}

            event_1 = {
                "headers": {"Authorization": "Bearer token1"},
                "body": json.dumps(
                    {"title": title, "description": description, "mediaType": "audio"}
                ),
            }

            # Act - Admin 1 creates session
            response_1 = lambda_handler(event_1, {})

            # Assert - Session 1 has tenant 1
            assert response_1["statusCode"] == 201
            body_1 = json.loads(response_1["body"])
            assert body_1["tenantId"] == tenant_id_1

            # Arrange - Admin 2
            admin_id_2 = str(uuid.uuid4())
            tenant_id_2 = str(uuid.uuid4())

            tenant_context_2 = {
                "adminId": admin_id_2,
                "role": "tenant_admin",
                "tenantId": tenant_id_2,
                "tenant": {
                    "tenantId": tenant_id_2,
                    "name": "Tenant 2",
                    "status": "active",
                },
            }

            mock_require_tenant_admin.return_value = (tenant_context_2, None)

            event_2 = {
                "headers": {"Authorization": "Bearer token2"},
                "body": json.dumps(
                    {"title": title, "description": description, "mediaType": "audio"}
                ),
            }

            # Act - Admin 2 creates session
            response_2 = lambda_handler(event_2, {})

            # Assert - Session 2 has tenant 2
            assert response_2["statusCode"] == 201
            body_2 = json.loads(response_2["body"])
            assert body_2["tenantId"] == tenant_id_2

            # Verify sessions have different tenant IDs
            assert body_1["tenantId"] != body_2["tenantId"]
