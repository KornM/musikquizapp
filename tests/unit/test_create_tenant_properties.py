"""
Property-Based Tests for Create Tenant Lambda Handler

Tests cover:
- Property 24: Unique tenant ID generation
- Property 25: Tenant creation validation

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
sys.path.insert(0, os.path.join(lambda_path, "create_tenant"))
sys.path.insert(0, os.path.join(lambda_path, "common"))


class TestTenantCreationProperties:
    """Property-based tests for tenant creation"""

    @patch("handler.put_item")
    def test_property_24_unique_tenant_id_generation(self, mock_put_item):
        """
        Feature: global-participant-registration, Property 24: Unique tenant ID generation

        For any tenant creation request, the system should generate a unique tenant ID
        that doesn't collide with existing tenant IDs.

        Validates: Requirements 8.1
        """
        from handler import lambda_handler

        # Arrange
        mock_put_item.return_value = {}

        # Track generated tenant IDs across all calls
        generated_ids = []

        # Act - Create multiple tenants
        for i in range(100):
            event = {
                "body": json.dumps(
                    {"name": f"Test Tenant {i}", "description": f"Description {i}"}
                )
            }
            context = {}

            response = lambda_handler(event, context)

            # Assert
            assert response["statusCode"] == 201
            body = json.loads(response["body"])
            tenant_id = body["tenantId"]

            # Verify tenant ID is a valid UUID format
            import uuid

            try:
                uuid.UUID(tenant_id)
            except ValueError:
                pytest.fail(f"Generated tenant ID '{tenant_id}' is not a valid UUID")

            generated_ids.append(tenant_id)

        # Verify all IDs are unique
        assert len(generated_ids) == len(set(generated_ids)), (
            "Tenant ID collision detected"
        )

    @settings(max_examples=100)
    @given(
        name=st.text(min_size=1, max_size=100),
        description=st.one_of(st.none(), st.text(min_size=0, max_size=500)),
    )
    @patch("handler.put_item")
    def test_property_25_tenant_creation_validation_valid(
        self, mock_put_item, name, description
    ):
        """
        Feature: global-participant-registration, Property 25: Tenant creation validation

        For any tenant creation request with a name and optional description,
        the system should accept the request and create the tenant.

        Validates: Requirements 8.2
        """
        from handler import lambda_handler

        # Arrange
        mock_put_item.return_value = {}

        request_body = {"name": name}
        if description is not None:
            request_body["description"] = description

        event = {"body": json.dumps(request_body)}
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert - Valid requests should succeed
        assert response["statusCode"] == 201
        body = json.loads(response["body"])

        # Verify response contains all required fields
        assert "tenantId" in body
        assert body["name"] == name
        assert "description" in body
        assert body["status"] == "active"
        assert "createdAt" in body
        assert "updatedAt" in body

        # Verify put_item was called with correct data
        assert mock_put_item.called
        call_args = mock_put_item.call_args
        stored_tenant = call_args[0][1]  # Second argument is the item

        assert stored_tenant["name"] == name
        assert stored_tenant["status"] == "active"

    @settings(max_examples=100)
    @given(
        description=st.text(min_size=0, max_size=500),
    )
    def test_property_25_tenant_creation_validation_missing_name(self, description):
        """
        Feature: global-participant-registration, Property 25: Tenant creation validation

        For any tenant creation request without a name, the system should reject
        the request with an error.

        Validates: Requirements 8.2
        """
        from handler import lambda_handler

        # Arrange - Request without name
        event = {"body": json.dumps({"description": description})}
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert - Should be rejected
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"]["code"] == "MISSING_FIELDS"
        assert "name" in body["error"]["message"].lower()

    @settings(max_examples=100)
    @given(
        invalid_name=st.one_of(st.none(), st.just("")),
        description=st.text(min_size=0, max_size=500),
    )
    def test_property_25_tenant_creation_validation_empty_name(
        self, invalid_name, description
    ):
        """
        Feature: global-participant-registration, Property 25: Tenant creation validation

        For any tenant creation request with an empty or null name, the system
        should reject the request.

        Validates: Requirements 8.2
        """
        from handler import lambda_handler

        # Arrange
        event = {"body": json.dumps({"name": invalid_name, "description": description})}
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert - Should be rejected
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"]["code"] == "MISSING_FIELDS"
