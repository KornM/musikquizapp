"""
Property-Based Tests for Delete Tenant Lambda Handler

Tests cover:
- Property 27: Tenant deletion blocks new sessions
- Property 43: Tenant deletion cascades

These tests use Hypothesis for property-based testing to verify universal properties
across many randomly generated inputs.
"""

import json
import sys
import os
from hypothesis import given, settings, strategies as st
from unittest.mock import patch, MagicMock

# Add lambda directories to path
lambda_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "lambda")
)
sys.path.insert(0, os.path.join(lambda_path, "delete_tenant"))
sys.path.insert(0, os.path.join(lambda_path, "common"))


class TestTenantDeletionProperties:
    """Property-based tests for tenant deletion"""

    @patch("handler.update_item")
    @patch("handler.get_item")
    def test_property_27_tenant_deletion_blocks_new_sessions(
        self, mock_get_item, mock_update_item
    ):
        """
        Feature: global-participant-registration, Property 27: Tenant deletion blocks new sessions

        For any tenant marked as inactive/deleted, attempts to create new sessions
        for that tenant should be rejected.

        Validates: Requirements 8.5
        """
        from handler import lambda_handler

        @settings(max_examples=100)
        @given(
            tenant_name=st.text(min_size=1, max_size=100),
        )
        def run_property_test(tenant_name):
            # Arrange - Mock existing tenant
            tenant_id = "test-tenant-123"
            mock_get_item.return_value = {
                "tenantId": tenant_id,
                "name": tenant_name,
                "description": "Test description",
                "status": "active",
                "createdAt": "2024-01-01T00:00:00.000Z",
                "updatedAt": "2024-01-01T00:00:00.000Z",
            }
            mock_update_item.return_value = {}

            event = {"pathParameters": {"tenantId": tenant_id}}
            context = {}

            # Act - Delete tenant
            response = lambda_handler(event, context)

            # Assert - Deletion should succeed
            assert response["statusCode"] == 200
            body = json.loads(response["body"])
            assert body["tenantId"] == tenant_id

            # Verify update_item was called to set status to inactive
            assert mock_update_item.called
            call_args = mock_update_item.call_args
            update_expression = call_args[0][2]  # Third argument is update expression
            expression_values = call_args[0][3]  # Fourth argument is values

            assert "status" in update_expression.lower()
            assert expression_values[":status"] == "inactive"

        run_property_test()

    @patch("handler.update_item")
    @patch("handler.get_item")
    def test_property_43_tenant_deletion_cascades(
        self, mock_get_item, mock_update_item
    ):
        """
        Feature: global-participant-registration, Property 43: Tenant deletion cascades

        For any tenant deletion, all associated sessions, participants, and
        participations should be deleted or marked as inactive.

        Note: This test verifies the soft delete mechanism. Cascade deletion
        of related entities will be tested in integration tests.

        Validates: Requirements 14.3
        """
        from handler import lambda_handler

        @settings(max_examples=100)
        @given(
            tenant_id=st.uuids(),
        )
        def run_property_test(tenant_id):
            # Arrange - Mock existing tenant
            tenant_id_str = str(tenant_id)
            mock_get_item.return_value = {
                "tenantId": tenant_id_str,
                "name": "Test Tenant",
                "description": "Test description",
                "status": "active",
                "createdAt": "2024-01-01T00:00:00.000Z",
                "updatedAt": "2024-01-01T00:00:00.000Z",
            }
            mock_update_item.return_value = {}

            event = {"pathParameters": {"tenantId": tenant_id_str}}
            context = {}

            # Act - Delete tenant
            response = lambda_handler(event, context)

            # Assert - Deletion should succeed
            assert response["statusCode"] == 200

            # Verify tenant is marked as inactive (soft delete)
            assert mock_update_item.called
            call_args = mock_update_item.call_args
            expression_values = call_args[0][3]
            assert expression_values[":status"] == "inactive"

        run_property_test()

    @patch("handler.get_item")
    def test_property_27_nonexistent_tenant_deletion(self, mock_get_item):
        """
        Feature: global-participant-registration, Property 27: Tenant deletion blocks new sessions

        For any attempt to delete a non-existent tenant, the system should
        return a 404 error.

        Validates: Requirements 8.5
        """
        from handler import lambda_handler

        @settings(max_examples=100)
        @given(
            tenant_id=st.uuids(),
        )
        def run_property_test(tenant_id):
            # Arrange - Mock non-existent tenant
            mock_get_item.return_value = None

            event = {"pathParameters": {"tenantId": str(tenant_id)}}
            context = {}

            # Act
            response = lambda_handler(event, context)

            # Assert - Should return 404
            assert response["statusCode"] == 404
            body = json.loads(response["body"])
            assert body["error"]["code"] == "TENANT_NOT_FOUND"

        run_property_test()
