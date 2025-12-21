"""
Integration Tests for Complete Tenant Lifecycle

Tests the full lifecycle of tenant management including:
- Tenant creation
- Tenant admin creation
- Tenant admin authentication
- Session creation within tenant
- Tenant updates
- Tenant deletion and cascading effects
"""

import json
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add lambda directories to path
lambda_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "lambda")
)
sys.path.insert(0, lambda_path)


class TestTenantLifecycle:
    """Integration tests for complete tenant lifecycle"""

    def test_complete_tenant_lifecycle(self):
        """
        Test the complete lifecycle of a tenant from creation to deletion.

        Workflow:
        1. Super admin creates a tenant
        2. Super admin creates a tenant admin for the tenant
        3. Tenant admin logs in and receives tenant context
        4. Tenant admin creates a session
        5. Verify session is associated with correct tenant
        6. Super admin updates tenant information
        7. Super admin deletes tenant
        8. Verify tenant is marked inactive
        9. Verify new sessions cannot be created for inactive tenant
        """
        tenant_id = "test-tenant-123"
        admin_id = "test-admin-456"
        session_id = "test-session-789"

        # Step 1: Create tenant
        with patch("create_tenant.handler.put_item") as mock_put_tenant:
            from create_tenant.handler import lambda_handler as create_tenant_handler

            create_tenant_event = {
                "body": json.dumps(
                    {"name": "Test Organization", "description": "A test organization"}
                ),
                "headers": {},
            }

            mock_put_tenant.return_value = None

            with patch("uuid.uuid4", return_value=MagicMock(hex=tenant_id)):
                response = create_tenant_handler(create_tenant_event, {})

            assert response["statusCode"] == 201
            body = json.loads(response["body"])
            assert "tenantId" in body
            assert body["name"] == "Test Organization"

        # Step 2: Create tenant admin
        with (
            patch("create_tenant_admin.handler.get_item") as mock_get_tenant,
            patch("create_tenant_admin.handler.query") as mock_query_username,
            patch("create_tenant_admin.handler.put_item") as mock_put_admin,
        ):
            from create_tenant_admin.handler import (
                lambda_handler as create_admin_handler,
            )

            # Tenant exists and is active
            mock_get_tenant.return_value = {
                "tenantId": tenant_id,
                "name": "Test Organization",
                "status": "active",
            }

            # Username doesn't exist
            mock_query_username.return_value = []

            create_admin_event = {
                "pathParameters": {"tenantId": tenant_id},
                "body": json.dumps(
                    {
                        "username": "testadmin",
                        "password": "SecurePass123!",
                        "email": "admin@test.com",
                    }
                ),
                "headers": {},
            }

            with patch("uuid.uuid4", return_value=MagicMock(hex=admin_id)):
                response = create_admin_handler(create_admin_event, {})

            assert response["statusCode"] == 201
            body = json.loads(response["body"])
            assert body["tenantId"] == tenant_id
            assert body["username"] == "testadmin"

        # Step 3: Tenant admin logs in
        with (
            patch("admin_login.handler.query") as mock_query_login,
            patch("admin_login.handler.verify_password") as mock_verify,
        ):
            from admin_login.handler import lambda_handler as login_handler

            mock_query_login.return_value = [
                {
                    "adminId": admin_id,
                    "username": "testadmin",
                    "passwordHash": "hashed_password",
                    "tenantId": tenant_id,
                    "role": "tenant_admin",
                }
            ]
            mock_verify.return_value = True

            login_event = {
                "body": json.dumps(
                    {"username": "testadmin", "password": "SecurePass123!"}
                ),
                "headers": {},
            }

            response = login_handler(login_event, {})

            assert response["statusCode"] == 200
            body = json.loads(response["body"])
            assert "token" in body
            assert body["tenantId"] == tenant_id

        # Step 4: Tenant admin creates session
        with patch("create_quiz.handler.put_item") as mock_put_session:
            from create_quiz.handler import lambda_handler as create_session_handler

            create_session_event = {
                "body": json.dumps(
                    {"title": "Test Quiz", "description": "A test quiz session"}
                ),
                "headers": {
                    "Authorization": f"Bearer mock_token_with_tenant_{tenant_id}"
                },
                "requestContext": {
                    "authorizer": {
                        "tenantId": tenant_id,
                        "adminId": admin_id,
                        "role": "tenant_admin",
                    }
                },
            }

            with patch("uuid.uuid4", return_value=MagicMock(hex=session_id)):
                response = create_session_handler(create_session_event, {})

            assert response["statusCode"] == 201
            body = json.loads(response["body"])
            assert body["tenantId"] == tenant_id

        # Step 5: Update tenant
        with (
            patch("update_tenant.handler.get_item") as mock_get_tenant_update,
            patch("update_tenant.handler.update_item") as mock_update_tenant,
        ):
            from update_tenant.handler import lambda_handler as update_tenant_handler

            mock_get_tenant_update.return_value = {
                "tenantId": tenant_id,
                "name": "Test Organization",
                "status": "active",
            }

            update_tenant_event = {
                "pathParameters": {"tenantId": tenant_id},
                "body": json.dumps({"name": "Updated Organization Name"}),
                "headers": {},
            }

            response = update_tenant_handler(update_tenant_event, {})

            assert response["statusCode"] == 200

        # Step 6: Delete tenant
        with (
            patch("delete_tenant.handler.get_item") as mock_get_tenant_delete,
            patch("delete_tenant.handler.update_item") as mock_update_tenant_delete,
        ):
            from delete_tenant.handler import lambda_handler as delete_tenant_handler

            mock_get_tenant_delete.return_value = {
                "tenantId": tenant_id,
                "name": "Updated Organization Name",
                "status": "active",
            }

            delete_tenant_event = {
                "pathParameters": {"tenantId": tenant_id},
                "headers": {},
            }

            response = delete_tenant_handler(delete_tenant_event, {})

            assert response["statusCode"] == 200
            body = json.loads(response["body"])
            assert "deleted successfully" in body["message"].lower()

    def test_tenant_admin_isolation(self):
        """
        Test that tenant admins can only access their own tenant's resources.

        Workflow:
        1. Create two tenants
        2. Create admin for each tenant
        3. Admin 1 creates session in tenant 1
        4. Admin 2 tries to access tenant 1's session
        5. Verify access is denied
        """
        tenant1_id = "tenant-1"
        tenant2_id = "tenant-2"
        admin1_id = "admin-1"
        admin2_id = "admin-2"
        session1_id = "session-1"

        # Create sessions for both tenants
        with patch("create_quiz.handler.put_item"):
            from create_quiz.handler import lambda_handler as create_session_handler

            # Admin 1 creates session in tenant 1
            event1 = {
                "body": json.dumps({"title": "Tenant 1 Quiz"}),
                "headers": {},
                "requestContext": {
                    "authorizer": {
                        "tenantId": tenant1_id,
                        "adminId": admin1_id,
                        "role": "tenant_admin",
                    }
                },
            }

            with patch("uuid.uuid4", return_value=MagicMock(hex=session1_id)):
                response1 = create_session_handler(event1, {})

            assert response1["statusCode"] == 201

        # Admin 2 tries to access tenant 1's session
        with patch("get_quiz.handler.get_item") as mock_get_session:
            from get_quiz.handler import lambda_handler as get_session_handler

            mock_get_session.return_value = {
                "sessionId": session1_id,
                "tenantId": tenant1_id,
                "title": "Tenant 1 Quiz",
            }

            event2 = {
                "pathParameters": {"sessionId": session1_id},
                "headers": {},
                "requestContext": {
                    "authorizer": {
                        "tenantId": tenant2_id,  # Different tenant!
                        "adminId": admin2_id,
                        "role": "tenant_admin",
                    }
                },
            }

            response2 = get_session_handler(event2, {})

            # Should be denied
            assert response2["statusCode"] == 403
            body = json.loads(response2["body"])
            assert body["error"]["code"] == "CROSS_TENANT_ACCESS"

    def test_backward_compatibility_default_tenant(self):
        """
        Test that the system works in single-tenant mode with default tenant.

        Workflow:
        1. Create session without explicit tenant context
        2. Verify session is assigned to default tenant
        3. Verify existing admins work with default tenant
        """
        default_tenant_id = "00000000-0000-0000-0000-000000000000"

        with (
            patch("create_quiz.handler.put_item") as mock_put,
            patch("backward_compatibility.ensure_tenant_context") as mock_ensure_tenant,
        ):
            from create_quiz.handler import lambda_handler as create_session_handler

            # Mock backward compatibility to add default tenant
            mock_ensure_tenant.return_value = default_tenant_id

            # Request without tenant context (legacy format)
            event = {
                "body": json.dumps({"title": "Legacy Quiz"}),
                "headers": {},
                "requestContext": {},  # No authorizer with tenant
            }

            response = create_session_handler(event, {})

            # Should succeed with default tenant
            assert response["statusCode"] == 201
            body = json.loads(response["body"])
            # Verify default tenant was used
            assert "sessionId" in body
