"""
Property-Based Tests for Cross-Tenant Session Access

Tests cover:
- Property 33: Cross-tenant session access denial

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
sys.path.insert(0, os.path.join(lambda_path, "get_quiz"))
sys.path.insert(0, os.path.join(lambda_path, "common"))


class TestCrossTenantAccessProperties:
    """Property-based tests for cross-tenant access denial"""

    @settings(max_examples=100, deadline=None)
    @given(
        session_title=st.text(min_size=1, max_size=100),
        session_status=st.sampled_from(["draft", "active", "completed"]),
    )
    def test_property_33_cross_tenant_session_access_denial(
        self, session_title, session_status
    ):
        """
        Feature: global-participant-registration, Property 33: Cross-tenant session access denial

        For any tenant admin attempting to access a session with a different tenantId
        than their own, the system should deny access with a 403 Forbidden error.

        Validates: Requirements 10.3, 14.4
        """
        with (
            patch("handler.require_tenant_admin") as mock_require_tenant_admin,
            patch("handler.get_item") as mock_get_item,
            patch("handler.validate_tenant_access") as mock_validate_tenant_access,
        ):
            from handler import lambda_handler
            import uuid

            # Arrange
            admin_id = str(uuid.uuid4())
            admin_tenant_id = str(uuid.uuid4())
            session_tenant_id = str(uuid.uuid4())  # Different tenant
            session_id = str(uuid.uuid4())

            # Ensure tenant IDs are different
            assert admin_tenant_id != session_tenant_id

            # Mock tenant admin authentication
            tenant_context = {
                "adminId": admin_id,
                "role": "tenant_admin",
                "tenantId": admin_tenant_id,
                "tenant": {
                    "tenantId": admin_tenant_id,
                    "name": "Admin Tenant",
                    "status": "active",
                },
            }

            mock_require_tenant_admin.return_value = (tenant_context, None)

            # Mock session from different tenant
            session = {
                "sessionId": session_id,
                "tenantId": session_tenant_id,
                "title": session_title,
                "status": session_status,
                "createdAt": "2024-01-01T00:00:00Z",
                "roundCount": 0,
            }

            mock_get_item.return_value = session

            # Mock validate_tenant_access to return 403 error for cross-tenant access
            from errors import error_response

            mock_validate_tenant_access.return_value = error_response(
                403,
                "CROSS_TENANT_ACCESS",
                "You do not have permission to access this resource",
            )

            event = {
                "headers": {"Authorization": "Bearer fake_token"},
                "pathParameters": {"sessionId": session_id},
            }
            context = {}

            # Act
            response = lambda_handler(event, context)

            # Assert
            assert response["statusCode"] == 403
            body = json.loads(response["body"])

            # Verify error details
            assert "error" in body
            assert body["error"]["code"] == "CROSS_TENANT_ACCESS"
            assert "permission" in body["error"]["message"].lower()

            # Verify validate_tenant_access was called with correct parameters
            mock_validate_tenant_access.assert_called_once_with(
                tenant_context, session_tenant_id
            )

    @settings(max_examples=100, deadline=None)
    @given(
        num_sessions=st.integers(min_value=1, max_value=10),
    )
    def test_property_33_multiple_cross_tenant_attempts_all_denied(self, num_sessions):
        """
        Feature: global-participant-registration, Property 33: Cross-tenant session access denial

        For any tenant admin attempting to access multiple sessions from different tenants,
        all access attempts should be denied with 403 Forbidden errors.

        Validates: Requirements 10.3, 14.4
        """
        with (
            patch("handler.require_tenant_admin") as mock_require_tenant_admin,
            patch("handler.get_item") as mock_get_item,
            patch("handler.validate_tenant_access") as mock_validate_tenant_access,
        ):
            from handler import lambda_handler
            import uuid

            # Arrange
            admin_id = str(uuid.uuid4())
            admin_tenant_id = str(uuid.uuid4())

            tenant_context = {
                "adminId": admin_id,
                "role": "tenant_admin",
                "tenantId": admin_tenant_id,
                "tenant": {
                    "tenantId": admin_tenant_id,
                    "name": "Admin Tenant",
                    "status": "active",
                },
            }

            mock_require_tenant_admin.return_value = (tenant_context, None)

            from errors import error_response

            # Test accessing multiple sessions from different tenants
            for i in range(num_sessions):
                session_id = str(uuid.uuid4())
                other_tenant_id = str(uuid.uuid4())

                # Ensure different tenant
                assert other_tenant_id != admin_tenant_id

                session = {
                    "sessionId": session_id,
                    "tenantId": other_tenant_id,
                    "title": f"Session {i}",
                    "status": "draft",
                }

                mock_get_item.return_value = session
                mock_validate_tenant_access.return_value = error_response(
                    403,
                    "CROSS_TENANT_ACCESS",
                    "You do not have permission to access this resource",
                )

                event = {
                    "headers": {"Authorization": "Bearer fake_token"},
                    "pathParameters": {"sessionId": session_id},
                }

                # Act
                response = lambda_handler(event, {})

                # Assert - all attempts should be denied
                assert response["statusCode"] == 403
                body = json.loads(response["body"])
                assert body["error"]["code"] == "CROSS_TENANT_ACCESS"

    @settings(max_examples=100, deadline=None)
    @given(
        session_title=st.text(min_size=1, max_size=100),
    )
    def test_property_33_same_tenant_access_allowed(self, session_title):
        """
        Feature: global-participant-registration, Property 33: Cross-tenant session access denial

        For any tenant admin attempting to access a session from their own tenant,
        the system should allow access (not return 403).

        This is the inverse property - verifying that same-tenant access is NOT denied.

        Validates: Requirements 10.3, 14.4
        """
        with (
            patch("handler.require_tenant_admin") as mock_require_tenant_admin,
            patch("handler.get_item") as mock_get_item,
            patch("handler.validate_tenant_access") as mock_validate_tenant_access,
            patch("handler.query") as mock_query,
        ):
            from handler import lambda_handler
            import uuid

            # Arrange
            admin_id = str(uuid.uuid4())
            tenant_id = str(uuid.uuid4())  # Same tenant for both admin and session
            session_id = str(uuid.uuid4())

            tenant_context = {
                "adminId": admin_id,
                "role": "tenant_admin",
                "tenantId": tenant_id,
                "tenant": {
                    "tenantId": tenant_id,
                    "name": "Shared Tenant",
                    "status": "active",
                },
            }

            mock_require_tenant_admin.return_value = (tenant_context, None)

            # Mock session from same tenant
            session = {
                "sessionId": session_id,
                "tenantId": tenant_id,  # Same tenant
                "title": session_title,
                "status": "draft",
                "createdAt": "2024-01-01T00:00:00Z",
                "roundCount": 0,
            }

            mock_get_item.return_value = session

            # Mock validate_tenant_access to return None (access allowed)
            mock_validate_tenant_access.return_value = None

            # Mock query for rounds
            mock_query.return_value = []

            event = {
                "headers": {"Authorization": "Bearer fake_token"},
                "pathParameters": {"sessionId": session_id},
            }
            context = {}

            # Act
            response = lambda_handler(event, context)

            # Assert - access should be allowed (200 OK, not 403)
            assert response["statusCode"] == 200
            body = json.loads(response["body"])

            # Verify session data is returned
            assert body["sessionId"] == session_id
            assert body["tenantId"] == tenant_id
            assert body["title"] == session_title

            # Verify validate_tenant_access was called and returned None
            mock_validate_tenant_access.assert_called_once_with(
                tenant_context, tenant_id
            )

    @settings(max_examples=100, deadline=None)
    @given(
        session_title=st.text(min_size=1, max_size=100),
    )
    def test_property_33_super_admin_can_access_any_tenant(self, session_title):
        """
        Feature: global-participant-registration, Property 33: Cross-tenant session access denial

        For any super admin, they should be able to access sessions from any tenant
        (cross-tenant access restrictions do not apply).

        Validates: Requirements 10.3, 14.4
        """
        with (
            patch("handler.require_tenant_admin") as mock_require_tenant_admin,
            patch("handler.get_item") as mock_get_item,
            patch("handler.validate_tenant_access") as mock_validate_tenant_access,
            patch("handler.query") as mock_query,
        ):
            from handler import lambda_handler
            import uuid

            # Arrange
            admin_id = str(uuid.uuid4())
            session_tenant_id = str(uuid.uuid4())
            session_id = str(uuid.uuid4())

            # Mock super admin authentication (no tenantId)
            tenant_context = {
                "adminId": admin_id,
                "role": "super_admin",
                # No tenantId for super admin
            }

            mock_require_tenant_admin.return_value = (tenant_context, None)

            # Mock session from any tenant
            session = {
                "sessionId": session_id,
                "tenantId": session_tenant_id,
                "title": session_title,
                "status": "draft",
                "createdAt": "2024-01-01T00:00:00Z",
                "roundCount": 0,
            }

            mock_get_item.return_value = session

            # Mock validate_tenant_access to return None for super admin
            mock_validate_tenant_access.return_value = None

            # Mock query for rounds
            mock_query.return_value = []

            event = {
                "headers": {"Authorization": "Bearer fake_token"},
                "pathParameters": {"sessionId": session_id},
            }
            context = {}

            # Act
            response = lambda_handler(event, context)

            # Assert - super admin should have access
            assert response["statusCode"] == 200
            body = json.loads(response["body"])

            # Verify session data is returned
            assert body["sessionId"] == session_id
            assert body["tenantId"] == session_tenant_id

            # Verify validate_tenant_access was called
            mock_validate_tenant_access.assert_called_once_with(
                tenant_context, session_tenant_id
            )
