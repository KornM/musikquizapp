"""
Property-Based Tests for List Sessions Lambda Handler

Tests cover:
- Property 32: Session list tenant filtering

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
sys.path.insert(0, os.path.join(lambda_path, "list_sessions"))
sys.path.insert(0, os.path.join(lambda_path, "common"))


class TestListSessionsProperties:
    """Property-based tests for session listing"""

    @settings(max_examples=100, deadline=None)
    @given(
        num_own_sessions=st.integers(min_value=0, max_value=10),
        num_other_sessions=st.integers(min_value=0, max_value=10),
    )
    def test_property_32_session_list_tenant_filtering(
        self, num_own_sessions, num_other_sessions
    ):
        """
        Feature: global-participant-registration, Property 32: Session list tenant filtering

        For any tenant admin querying sessions, the results should only include sessions
        where the session's tenantId matches the admin's tenantId.

        Validates: Requirements 10.2, 10.4
        """
        with (
            patch("handler.require_tenant_admin") as mock_require_tenant_admin,
            patch("handler.query") as mock_query,
            patch("handler.scan") as mock_scan,
        ):
            from handler import lambda_handler
            import uuid

            # Arrange
            admin_id = str(uuid.uuid4())
            admin_tenant_id = str(uuid.uuid4())
            other_tenant_id = str(uuid.uuid4())

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

            # Create sessions for admin's tenant
            own_sessions = [
                {
                    "sessionId": str(uuid.uuid4()),
                    "tenantId": admin_tenant_id,
                    "title": f"Session {i}",
                    "createdAt": str(1000000 + i),
                    "status": "draft",
                }
                for i in range(num_own_sessions)
            ]

            # Create sessions for other tenant (should not be returned)
            other_sessions = [
                {
                    "sessionId": str(uuid.uuid4()),
                    "tenantId": other_tenant_id,
                    "title": f"Other Session {i}",
                    "createdAt": str(2000000 + i),
                    "status": "draft",
                }
                for i in range(num_other_sessions)
            ]

            # Mock query to return only admin's tenant sessions
            mock_query.return_value = own_sessions

            event = {
                "headers": {"Authorization": "Bearer fake_token"},
            }
            context = {}

            # Act
            response = lambda_handler(event, context)

            # Assert
            assert response["statusCode"] == 200
            body = json.loads(response["body"])

            # Verify only admin's tenant sessions are returned
            assert "sessions" in body
            returned_sessions = body["sessions"]
            assert len(returned_sessions) == num_own_sessions

            # Verify all returned sessions belong to admin's tenant
            for session in returned_sessions:
                assert session["tenantId"] == admin_tenant_id

            # Verify query was called with correct tenant filter
            if num_own_sessions > 0 or num_other_sessions > 0:
                assert mock_query.called
                call_args = mock_query.call_args
                # Check that tenantId filter is applied
                assert admin_tenant_id in str(call_args)

    @settings(max_examples=100, deadline=None)
    @given(
        num_tenant1_sessions=st.integers(min_value=1, max_value=5),
        num_tenant2_sessions=st.integers(min_value=1, max_value=5),
    )
    def test_property_32_different_admins_see_different_sessions(
        self, num_tenant1_sessions, num_tenant2_sessions
    ):
        """
        Feature: global-participant-registration, Property 32: Session list tenant filtering

        For any two tenant admins from different tenants, each should only see
        sessions from their respective tenant.

        Validates: Requirements 10.2, 10.4
        """
        with (
            patch("handler.require_tenant_admin") as mock_require_tenant_admin,
            patch("handler.query") as mock_query,
        ):
            from handler import lambda_handler
            import uuid

            # Arrange - Tenant 1
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

            sessions_1 = [
                {
                    "sessionId": str(uuid.uuid4()),
                    "tenantId": tenant_id_1,
                    "title": f"T1 Session {i}",
                    "createdAt": str(1000000 + i),
                }
                for i in range(num_tenant1_sessions)
            ]

            mock_require_tenant_admin.return_value = (tenant_context_1, None)
            mock_query.return_value = sessions_1

            event_1 = {"headers": {"Authorization": "Bearer token1"}}

            # Act - Admin 1 lists sessions
            response_1 = lambda_handler(event_1, {})

            # Assert - Admin 1 sees only tenant 1 sessions
            assert response_1["statusCode"] == 200
            body_1 = json.loads(response_1["body"])
            assert len(body_1["sessions"]) == num_tenant1_sessions
            for session in body_1["sessions"]:
                assert session["tenantId"] == tenant_id_1

            # Arrange - Tenant 2
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

            sessions_2 = [
                {
                    "sessionId": str(uuid.uuid4()),
                    "tenantId": tenant_id_2,
                    "title": f"T2 Session {i}",
                    "createdAt": str(2000000 + i),
                }
                for i in range(num_tenant2_sessions)
            ]

            mock_require_tenant_admin.return_value = (tenant_context_2, None)
            mock_query.return_value = sessions_2

            event_2 = {"headers": {"Authorization": "Bearer token2"}}

            # Act - Admin 2 lists sessions
            response_2 = lambda_handler(event_2, {})

            # Assert - Admin 2 sees only tenant 2 sessions
            assert response_2["statusCode"] == 200
            body_2 = json.loads(response_2["body"])
            assert len(body_2["sessions"]) == num_tenant2_sessions
            for session in body_2["sessions"]:
                assert session["tenantId"] == tenant_id_2

            # Verify no overlap in session IDs
            session_ids_1 = {s["sessionId"] for s in body_1["sessions"]}
            session_ids_2 = {s["sessionId"] for s in body_2["sessions"]}
            assert session_ids_1.isdisjoint(session_ids_2)

    @settings(max_examples=100, deadline=None)
    @given(
        num_sessions=st.integers(min_value=1, max_value=20),
    )
    def test_property_32_super_admin_sees_all_sessions(self, num_sessions):
        """
        Feature: global-participant-registration, Property 32: Session list tenant filtering

        For any super admin, they should see all sessions regardless of tenant.

        Validates: Requirements 10.2
        """
        with (
            patch("handler.require_tenant_admin") as mock_require_tenant_admin,
            patch("handler.scan") as mock_scan,
        ):
            from handler import lambda_handler
            import uuid

            # Arrange
            admin_id = str(uuid.uuid4())

            # Mock super admin authentication (no tenantId)
            tenant_context = {
                "adminId": admin_id,
                "role": "super_admin",
            }

            mock_require_tenant_admin.return_value = (tenant_context, None)

            # Create sessions from multiple tenants
            all_sessions = [
                {
                    "sessionId": str(uuid.uuid4()),
                    "tenantId": str(uuid.uuid4()),
                    "title": f"Session {i}",
                    "createdAt": str(1000000 + i),
                }
                for i in range(num_sessions)
            ]

            mock_scan.return_value = all_sessions

            event = {"headers": {"Authorization": "Bearer super_admin_token"}}

            # Act
            response = lambda_handler(event, {})

            # Assert
            assert response["statusCode"] == 200
            body = json.loads(response["body"])

            # Verify all sessions are returned
            assert len(body["sessions"]) == num_sessions

            # Verify scan was called (not query with tenant filter)
            assert mock_scan.called
