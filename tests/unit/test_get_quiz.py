"""
Unit tests for get_quiz Lambda handler
"""

import json
import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "lambda"))
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "..", "lambda", "get_quiz")
)
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "..", "lambda", "common")
)


@pytest.fixture
def mock_env():
    """Set up environment variables"""
    os.environ["QUIZ_SESSIONS_TABLE"] = "MusicQuiz-Sessions"
    os.environ["QUIZ_ROUNDS_TABLE"] = "MusicQuiz-Rounds"
    os.environ["JWT_SECRET"] = "test-secret-key"


@pytest.fixture
def tenant_admin_event():
    """Create a mock event for a tenant admin"""
    return {
        "headers": {"Authorization": "Bearer valid-token"},
        "pathParameters": {"sessionId": "session-123"},
    }


@pytest.fixture
def mock_session():
    """Create a mock session"""
    return {
        "sessionId": "session-123",
        "tenantId": "tenant-1",
        "title": "Test Quiz",
        "description": "Test Description",
        "createdBy": "admin-1",
        "createdAt": "2024-01-01T00:00:00Z",
        "roundCount": 2,
        "status": "draft",
    }


@pytest.fixture
def mock_rounds():
    """Create mock rounds"""
    return [
        {
            "roundId": "round-1",
            "sessionId": "session-123",
            "roundNumber": 1,
            "audioKey": "audio1.mp3",
            "answers": ["A", "B", "C", "D"],
            "correctAnswer": 0,
        },
        {
            "roundId": "round-2",
            "sessionId": "session-123",
            "roundNumber": 2,
            "audioKey": "audio2.mp3",
            "answers": ["E", "F", "G", "H"],
            "correctAnswer": 1,
        },
    ]


def test_get_quiz_success_same_tenant(
    mock_env, tenant_admin_event, mock_session, mock_rounds
):
    """Test successful session retrieval when admin and session are in same tenant"""
    with (
        patch("handler.require_tenant_admin") as mock_auth,
        patch("handler.get_item") as mock_get,
        patch("handler.query") as mock_query,
    ):
        # Mock authentication - tenant admin with matching tenant
        mock_auth.return_value = (
            {
                "adminId": "admin-1",
                "role": "tenant_admin",
                "tenantId": "tenant-1",
            },
            None,
        )

        # Mock database responses
        mock_get.return_value = mock_session
        mock_query.return_value = mock_rounds

        # Import handler after mocking
        from handler import lambda_handler

        # Execute
        response = lambda_handler(tenant_admin_event, None)

        # Verify
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["sessionId"] == "session-123"
        assert body["tenantId"] == "tenant-1"
        assert len(body["rounds"]) == 2
        assert body["rounds"][0]["roundNumber"] == 1


def test_get_quiz_cross_tenant_access_denied(
    mock_env, tenant_admin_event, mock_session
):
    """Test that cross-tenant access is denied with 403"""
    with (
        patch("handler.require_tenant_admin") as mock_auth,
        patch("handler.get_item") as mock_get,
        patch("handler.validate_tenant_access") as mock_validate,
    ):
        # Mock authentication - tenant admin with different tenant
        mock_auth.return_value = (
            {
                "adminId": "admin-2",
                "role": "tenant_admin",
                "tenantId": "tenant-2",  # Different tenant
            },
            None,
        )

        # Mock database response
        mock_get.return_value = mock_session  # Session belongs to tenant-1

        # Mock validation to return error
        mock_validate.return_value = {
            "statusCode": 403,
            "body": json.dumps(
                {
                    "error": {
                        "code": "CROSS_TENANT_ACCESS",
                        "message": "You do not have permission to access this resource",
                    }
                }
            ),
        }

        # Import handler after mocking
        from handler import lambda_handler

        # Execute
        response = lambda_handler(tenant_admin_event, None)

        # Verify
        assert response["statusCode"] == 403
        body = json.loads(response["body"])
        assert body["error"]["code"] == "CROSS_TENANT_ACCESS"


def test_get_quiz_super_admin_access_any_tenant(
    mock_env, tenant_admin_event, mock_session, mock_rounds
):
    """Test that super admin can access sessions from any tenant"""
    with (
        patch("handler.require_tenant_admin") as mock_auth,
        patch("handler.get_item") as mock_get,
        patch("handler.query") as mock_query,
        patch("handler.validate_tenant_access") as mock_validate,
    ):
        # Mock authentication - super admin
        mock_auth.return_value = (
            {
                "adminId": "super-admin-1",
                "role": "super_admin",
                "tenantId": None,
            },
            None,
        )

        # Mock database responses
        mock_get.return_value = mock_session
        mock_query.return_value = mock_rounds

        # Mock validation to allow access (super admin)
        mock_validate.return_value = None

        # Import handler after mocking
        from handler import lambda_handler

        # Execute
        response = lambda_handler(tenant_admin_event, None)

        # Verify
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["sessionId"] == "session-123"


def test_get_quiz_missing_token(mock_env, tenant_admin_event):
    """Test that missing authentication token returns 401"""
    with patch("handler.require_tenant_admin") as mock_auth:
        # Mock authentication failure
        mock_auth.return_value = (
            None,
            {
                "statusCode": 401,
                "body": json.dumps(
                    {
                        "error": {
                            "code": "MISSING_TOKEN",
                            "message": "Authorization header is required",
                        }
                    }
                ),
            },
        )

        # Import handler after mocking
        from handler import lambda_handler

        # Execute
        response = lambda_handler(tenant_admin_event, None)

        # Verify
        assert response["statusCode"] == 401
        body = json.loads(response["body"])
        assert body["error"]["code"] == "MISSING_TOKEN"


def test_get_quiz_session_not_found(mock_env, tenant_admin_event):
    """Test that non-existent session returns 404"""
    with (
        patch("handler.require_tenant_admin") as mock_auth,
        patch("handler.get_item") as mock_get,
    ):
        # Mock authentication
        mock_auth.return_value = (
            {
                "adminId": "admin-1",
                "role": "tenant_admin",
                "tenantId": "tenant-1",
            },
            None,
        )

        # Mock database response - session not found
        mock_get.return_value = None

        # Import handler after mocking
        from handler import lambda_handler

        # Execute
        response = lambda_handler(tenant_admin_event, None)

        # Verify
        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert body["error"]["code"] == "SESSION_NOT_FOUND"
