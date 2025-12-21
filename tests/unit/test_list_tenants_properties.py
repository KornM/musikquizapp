"""
Property-Based Tests for List Tenants Lambda Handler

Tests cover:
- Property 26: Tenant list completeness

These tests use Hypothesis for property-based testing to verify universal properties
across many randomly generated inputs.
"""

import json
import sys
import os
from hypothesis import given, settings, strategies as st
from unittest.mock import patch

# Add lambda directories to path
lambda_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "lambda")
)
sys.path.insert(0, os.path.join(lambda_path, "list_tenants"))
sys.path.insert(0, os.path.join(lambda_path, "common"))


class TestTenantListingProperties:
    """Property-based tests for tenant listing"""

    @patch("handler.scan")
    def test_property_26_tenant_list_completeness(self, mock_scan):
        """
        Feature: global-participant-registration, Property 26: Tenant list completeness

        For any super admin query for tenants, the response should include all tenants
        with their names, creation dates (createdAt), and status fields.

        Validates: Requirements 8.4
        """
        from handler import lambda_handler

        @settings(max_examples=100)
        @given(
            tenant_count=st.integers(min_value=0, max_value=20),
        )
        def run_property_test(tenant_count):
            # Arrange - Create mock tenant data
            mock_tenants = []
            for i in range(tenant_count):
                mock_tenants.append(
                    {
                        "tenantId": f"tenant-{i}",
                        "name": f"Tenant {i}",
                        "description": f"Description {i}",
                        "status": "active" if i % 2 == 0 else "inactive",
                        "createdAt": f"2024-01-{i + 1:02d}T00:00:00.000Z",
                        "updatedAt": f"2024-01-{i + 1:02d}T00:00:00.000Z",
                    }
                )

            mock_scan.return_value = mock_tenants

            event = {}
            context = {}

            # Act
            response = lambda_handler(event, context)

            # Assert
            assert response["statusCode"] == 200
            body = json.loads(response["body"])

            # Verify all tenants are returned
            assert "tenants" in body
            assert len(body["tenants"]) == tenant_count

            # Verify each tenant has required fields
            for i, tenant in enumerate(body["tenants"]):
                assert "tenantId" in tenant
                assert "name" in tenant
                assert "status" in tenant
                assert "createdAt" in tenant

                # Verify values match mock data
                assert tenant["tenantId"] == f"tenant-{i}"
                assert tenant["name"] == f"Tenant {i}"
                assert tenant["status"] in ["active", "inactive"]
                assert tenant["createdAt"] == f"2024-01-{i + 1:02d}T00:00:00.000Z"

        run_property_test()

    @patch("handler.query")
    def test_property_26_tenant_list_status_filtering(self, mock_query):
        """
        Feature: global-participant-registration, Property 26: Tenant list completeness

        For any super admin query for tenants with status filter, the response should
        include only tenants matching that status.

        Validates: Requirements 8.4
        """
        from handler import lambda_handler

        @settings(max_examples=100)
        @given(
            active_count=st.integers(min_value=0, max_value=10),
        )
        def run_property_test(active_count):
            # Arrange - Create mock active tenants
            mock_active_tenants = []
            for i in range(active_count):
                mock_active_tenants.append(
                    {
                        "tenantId": f"active-tenant-{i}",
                        "name": f"Active Tenant {i}",
                        "description": f"Description {i}",
                        "status": "active",
                        "createdAt": f"2024-01-{i + 1:02d}T00:00:00.000Z",
                        "updatedAt": f"2024-01-{i + 1:02d}T00:00:00.000Z",
                    }
                )

            mock_query.return_value = mock_active_tenants

            event = {"queryStringParameters": {"status": "active"}}
            context = {}

            # Act
            response = lambda_handler(event, context)

            # Assert
            assert response["statusCode"] == 200
            body = json.loads(response["body"])

            # Verify only active tenants are returned
            assert "tenants" in body
            assert len(body["tenants"]) == active_count

            # Verify all returned tenants have active status
            for tenant in body["tenants"]:
                assert tenant["status"] == "active"

        run_property_test()
