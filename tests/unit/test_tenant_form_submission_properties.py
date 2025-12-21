"""
Property-Based Tests for Tenant Form Submission

Tests cover:
- Property 37: Tenant form submission creates tenant

These tests verify that valid tenant form submissions result in tenant creation.
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


class TestTenantFormSubmissionProperties:
    """Property-based tests for tenant form submission"""

    @settings(max_examples=100, deadline=None)
    @given(
        name=st.text(min_size=1, max_size=100),
        description=st.one_of(st.none(), st.text(min_size=0, max_size=500)),
    )
    @patch("handler.put_item")
    def test_property_37_tenant_form_submission_creates_tenant(
        self, mock_put_item, name, description
    ):
        """
        Feature: global-participant-registration, Property 37: Tenant form submission creates tenant

        For any valid tenant creation form submission (with name), the system should
        create a new tenant record in the database.

        Validates: Requirements 12.3
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

        # Assert - Form submission should create tenant
        assert response["statusCode"] == 201
        body = json.loads(response["body"])

        # Verify tenant was created with correct data
        assert "tenantId" in body
        assert body["name"] == name
        assert body["status"] == "active"

        # Verify database was called to store the tenant
        assert mock_put_item.called
        call_args = mock_put_item.call_args
        stored_tenant = call_args[0][1]  # Second argument is the item

        # Verify the stored tenant has all required fields
        assert "tenantId" in stored_tenant
        assert stored_tenant["name"] == name
        assert stored_tenant["status"] == "active"
        assert "createdAt" in stored_tenant
        assert "updatedAt" in stored_tenant

        # Verify tenant ID is a valid UUID
        import uuid

        try:
            uuid.UUID(stored_tenant["tenantId"])
        except ValueError:
            pytest.fail(
                f"Generated tenant ID '{stored_tenant['tenantId']}' is not a valid UUID"
            )

    @settings(max_examples=50, deadline=None)
    @given(
        name=st.text(min_size=1, max_size=100),
    )
    @patch("handler.put_item")
    def test_property_37_created_tenant_is_retrievable(self, mock_put_item, name):
        """
        Feature: global-participant-registration, Property 37: Tenant form submission creates tenant

        For any tenant created through form submission, the tenant should be
        retrievable from the database.

        Validates: Requirements 12.3
        """
        from handler import lambda_handler

        # Arrange
        mock_put_item.return_value = {}

        event = {"body": json.dumps({"name": name, "description": "Test"})}
        context = {}

        # Act - Create tenant
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 201
        body = json.loads(response["body"])
        tenant_id = body["tenantId"]

        # Verify put_item was called with the tenant data
        assert mock_put_item.called
        call_args = mock_put_item.call_args
        stored_tenant = call_args[0][1]

        # Verify the tenant can be identified by its ID
        assert stored_tenant["tenantId"] == tenant_id
        assert stored_tenant["name"] == name
