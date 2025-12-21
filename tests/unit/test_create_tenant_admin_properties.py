"""
Property-Based Tests for Create Tenant Admin Lambda Handler

Tests cover:
- Property 28: Tenant admin association
- Property 29: Tenant admin creation validation

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
sys.path.insert(0, os.path.join(lambda_path, "create_tenant_admin"))
sys.path.insert(0, os.path.join(lambda_path, "common"))


class TestTenantAdminCreationProperties:
    """Property-based tests for tenant admin creation"""

    @settings(max_examples=100, deadline=None)
    @given(
        username=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
        password=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
        email=st.one_of(st.none(), st.emails()),
    )
    def test_property_28_tenant_admin_association(self, username, password, email):
        """
        Feature: global-participant-registration, Property 28: Tenant admin association

        For any tenant admin created, the admin record should contain a tenantId field
        referencing a valid tenant.

        Validates: Requirements 9.1
        """
        with (
            patch("handler.query") as mock_query,
            patch("handler.get_item") as mock_get_item,
            patch("handler.put_item") as mock_put_item,
        ):
            from handler import lambda_handler
            import uuid

            # Arrange
            tenant_id = str(uuid.uuid4())

            # Mock tenant exists and is active
            mock_get_item.return_value = {
                "tenantId": tenant_id,
                "name": "Test Tenant",
                "status": "active",
            }

            # Mock no existing admin with this username
            mock_query.return_value = []

            mock_put_item.return_value = {}

            request_body = {"username": username, "password": password}
            if email is not None:
                request_body["email"] = email

            event = {
                "pathParameters": {"tenantId": tenant_id},
                "body": json.dumps(request_body),
            }
            context = {}

            # Act
            response = lambda_handler(event, context)

            # Assert
            assert response["statusCode"] == 201
            body = json.loads(response["body"])

            # Verify admin record contains tenantId
            assert "tenantId" in body
            assert body["tenantId"] == tenant_id

            # Verify the stored admin has the correct tenantId
            assert mock_put_item.called
            call_args = mock_put_item.call_args
            stored_admin = call_args[0][1]  # Second argument is the item

            assert stored_admin["tenantId"] == tenant_id
            assert stored_admin["role"] == "tenant_admin"

    @settings(max_examples=100, deadline=None)
    @given(
        username=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
        password=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
        email=st.one_of(st.none(), st.emails()),
    )
    def test_property_29_tenant_admin_creation_validation_valid(
        self, username, password, email
    ):
        """
        Feature: global-participant-registration, Property 29: Tenant admin creation validation

        For any tenant admin creation request with username, password, and tenantId,
        the system should accept the request and create the admin.

        Validates: Requirements 9.2
        """
        with (
            patch("handler.query") as mock_query,
            patch("handler.get_item") as mock_get_item,
            patch("handler.put_item") as mock_put_item,
        ):
            from handler import lambda_handler
            import uuid

            # Arrange
            tenant_id = str(uuid.uuid4())

            # Mock tenant exists and is active
            mock_get_item.return_value = {
                "tenantId": tenant_id,
                "name": "Test Tenant",
                "status": "active",
            }

            # Mock no existing admin with this username
            mock_query.return_value = []

            mock_put_item.return_value = {}

            request_body = {"username": username, "password": password}
            if email is not None:
                request_body["email"] = email

            event = {
                "pathParameters": {"tenantId": tenant_id},
                "body": json.dumps(request_body),
            }
            context = {}

            # Act
            response = lambda_handler(event, context)

            # Assert - Valid requests should succeed
            assert response["statusCode"] == 201
            body = json.loads(response["body"])

            # Verify response contains all required fields
            assert "adminId" in body
            assert "tenantId" in body
            assert body["username"] == username
            assert body["role"] == "tenant_admin"
            assert "createdAt" in body
            assert "updatedAt" in body

            # Verify password is NOT in response
            assert "passwordHash" not in body
            assert "password" not in body

            # Verify put_item was called with correct data
            assert mock_put_item.called
            call_args = mock_put_item.call_args
            stored_admin = call_args[0][1]

            assert stored_admin["username"] == username
            assert stored_admin["tenantId"] == tenant_id
            assert stored_admin["role"] == "tenant_admin"
            assert "passwordHash" in stored_admin  # Password should be hashed

    @settings(max_examples=100)
    @given(
        password=st.text(min_size=1, max_size=100),
    )
    @patch("handler.get_item")
    def test_property_29_tenant_admin_creation_validation_missing_username(
        self, mock_get_item, password
    ):
        """
        Feature: global-participant-registration, Property 29: Tenant admin creation validation

        For any tenant admin creation request without a username, the system should
        reject the request.

        Validates: Requirements 9.2
        """
        from handler import lambda_handler
        import uuid

        # Arrange
        tenant_id = str(uuid.uuid4())

        # Mock tenant exists
        mock_get_item.return_value = {
            "tenantId": tenant_id,
            "name": "Test Tenant",
            "status": "active",
        }

        event = {
            "pathParameters": {"tenantId": tenant_id},
            "body": json.dumps({"password": password}),
        }
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert - Should be rejected
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"]["code"] == "MISSING_FIELDS"
        assert "username" in body["error"]["message"].lower()

    @settings(max_examples=100)
    @given(
        username=st.text(min_size=1, max_size=50),
    )
    @patch("handler.get_item")
    def test_property_29_tenant_admin_creation_validation_missing_password(
        self, mock_get_item, username
    ):
        """
        Feature: global-participant-registration, Property 29: Tenant admin creation validation

        For any tenant admin creation request without a password, the system should
        reject the request.

        Validates: Requirements 9.2
        """
        from handler import lambda_handler
        import uuid

        # Arrange
        tenant_id = str(uuid.uuid4())

        # Mock tenant exists
        mock_get_item.return_value = {
            "tenantId": tenant_id,
            "name": "Test Tenant",
            "status": "active",
        }

        event = {
            "pathParameters": {"tenantId": tenant_id},
            "body": json.dumps({"username": username}),
        }
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert - Should be rejected
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"]["code"] == "MISSING_FIELDS"
        assert "password" in body["error"]["message"].lower()

    @settings(max_examples=100)
    @given(
        username=st.text(min_size=1, max_size=50),
        password=st.text(min_size=1, max_size=100),
    )
    @patch("handler.get_item")
    def test_property_29_tenant_admin_creation_validation_missing_tenant_id(
        self, mock_get_item, username, password
    ):
        """
        Feature: global-participant-registration, Property 29: Tenant admin creation validation

        For any tenant admin creation request without a tenantId in the path,
        the system should reject the request.

        Validates: Requirements 9.2
        """
        from handler import lambda_handler

        # Arrange - No tenantId in path parameters
        event = {
            "pathParameters": {},
            "body": json.dumps({"username": username, "password": password}),
        }
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert - Should be rejected
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"]["code"] == "MISSING_FIELDS"

    @settings(max_examples=100)
    @given(
        username=st.text(min_size=1, max_size=50),
        password=st.text(min_size=1, max_size=100),
    )
    @patch("handler.get_item")
    def test_property_29_tenant_admin_creation_validation_nonexistent_tenant(
        self, mock_get_item, username, password
    ):
        """
        Feature: global-participant-registration, Property 29: Tenant admin creation validation

        For any tenant admin creation request with a non-existent tenantId,
        the system should reject the request.

        Validates: Requirements 9.2
        """
        from handler import lambda_handler
        import uuid

        # Arrange
        tenant_id = str(uuid.uuid4())

        # Mock tenant does not exist
        mock_get_item.return_value = None

        event = {
            "pathParameters": {"tenantId": tenant_id},
            "body": json.dumps({"username": username, "password": password}),
        }
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert - Should be rejected
        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert body["error"]["code"] == "TENANT_NOT_FOUND"

    @settings(max_examples=100)
    @given(
        username=st.text(min_size=1, max_size=50),
        password=st.text(min_size=1, max_size=100),
    )
    @patch("handler.get_item")
    def test_property_29_tenant_admin_creation_validation_inactive_tenant(
        self, mock_get_item, username, password
    ):
        """
        Feature: global-participant-registration, Property 29: Tenant admin creation validation

        For any tenant admin creation request with an inactive tenant,
        the system should reject the request.

        Validates: Requirements 9.2
        """
        from handler import lambda_handler
        import uuid

        # Arrange
        tenant_id = str(uuid.uuid4())

        # Mock tenant exists but is inactive
        mock_get_item.return_value = {
            "tenantId": tenant_id,
            "name": "Test Tenant",
            "status": "inactive",
        }

        event = {
            "pathParameters": {"tenantId": tenant_id},
            "body": json.dumps({"username": username, "password": password}),
        }
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert - Should be rejected
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"]["code"] == "TENANT_INACTIVE"

    @settings(max_examples=100)
    @given(
        username=st.text(min_size=1, max_size=50),
        password=st.text(min_size=1, max_size=100),
    )
    @patch("handler.query")
    @patch("handler.get_item")
    def test_property_29_tenant_admin_creation_validation_duplicate_username(
        self, mock_get_item, mock_query, username, password
    ):
        """
        Feature: global-participant-registration, Property 29: Tenant admin creation validation

        For any tenant admin creation request with a username that already exists,
        the system should reject the request.

        Validates: Requirements 9.2
        """
        from handler import lambda_handler
        import uuid

        # Arrange
        tenant_id = str(uuid.uuid4())

        # Mock tenant exists and is active
        mock_get_item.return_value = {
            "tenantId": tenant_id,
            "name": "Test Tenant",
            "status": "active",
        }

        # Mock existing admin with this username
        mock_query.return_value = [
            {
                "adminId": str(uuid.uuid4()),
                "username": username,
                "tenantId": tenant_id,
            }
        ]

        event = {
            "pathParameters": {"tenantId": tenant_id},
            "body": json.dumps({"username": username, "password": password}),
        }
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert - Should be rejected
        assert response["statusCode"] == 409
        body = json.loads(response["body"])
        assert body["error"]["code"] == "DUPLICATE_USERNAME"
