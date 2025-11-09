"""
Unit tests for Admin Login Lambda Handler

Tests cover:
- Successful login with valid credentials
- Invalid credentials (wrong password)
- Invalid credentials (non-existent user)
- Missing request body
- Invalid JSON in request body
- Missing username or password fields
- DynamoDB query errors
- Admin with missing password hash
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
sys.path.insert(0, os.path.join(lambda_path, "admin_login"))
sys.path.insert(0, os.path.join(lambda_path, "common"))


class TestAdminLoginSuccess:
    """Test successful login scenarios"""

    @patch("handler.query")
    @patch("handler.verify_password")
    @patch("handler.generate_token")
    def test_successful_login(
        self, mock_generate_token, mock_verify_password, mock_query
    ):
        """Test successful login with valid credentials"""
        # Import here to ensure mocks are in place
        from handler import lambda_handler

        # Arrange
        mock_query.return_value = [
            {
                "adminId": "admin-123",
                "username": "testadmin",
                "passwordHash": "$2b$12$hashedpassword",
            }
        ]
        mock_verify_password.return_value = True
        mock_generate_token.return_value = "jwt-token-string"

        event = {
            "body": json.dumps({"username": "testadmin", "password": "password123"})
        }
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["token"] == "jwt-token-string"
        assert body["expiresIn"] == 86400
        assert "Access-Control-Allow-Origin" in response["headers"]

        # Verify mocks called correctly
        mock_query.assert_called_once()
        mock_verify_password.assert_called_once_with(
            "password123", "$2b$12$hashedpassword"
        )
        mock_generate_token.assert_called_once_with("admin-123", "admin")


class TestAdminLoginInvalidCredentials:
    """Test invalid credentials scenarios"""

    @patch("handler.query")
    def test_nonexistent_user(self, mock_query):
        """Test login with non-existent username"""
        from handler import lambda_handler

        # Arrange
        mock_query.return_value = []

        event = {
            "body": json.dumps({"username": "nonexistent", "password": "password123"})
        }
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 401
        body = json.loads(response["body"])
        assert body["error"]["code"] == "INVALID_CREDENTIALS"
        assert "Invalid username or password" in body["error"]["message"]
        assert "Access-Control-Allow-Origin" in response["headers"]

    @patch("handler.query")
    @patch("handler.verify_password")
    def test_wrong_password(self, mock_verify_password, mock_query):
        """Test login with incorrect password"""
        from handler import lambda_handler

        # Arrange
        mock_query.return_value = [
            {
                "adminId": "admin-123",
                "username": "testadmin",
                "passwordHash": "$2b$12$hashedpassword",
            }
        ]
        mock_verify_password.return_value = False

        event = {
            "body": json.dumps({"username": "testadmin", "password": "wrongpassword"})
        }
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 401
        body = json.loads(response["body"])
        assert body["error"]["code"] == "INVALID_CREDENTIALS"
        assert "Invalid username or password" in body["error"]["message"]
        assert "Access-Control-Allow-Origin" in response["headers"]


class TestAdminLoginValidation:
    """Test input validation scenarios"""

    def test_missing_request_body(self):
        """Test request with no body"""
        from handler import lambda_handler

        # Arrange
        event = {}
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"]["code"] == "INVALID_REQUEST"
        assert "Request body is required" in body["error"]["message"]
        assert "Access-Control-Allow-Origin" in response["headers"]

    def test_invalid_json(self):
        """Test request with invalid JSON"""
        from handler import lambda_handler

        # Arrange
        event = {"body": "not valid json{"}
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"]["code"] == "INVALID_JSON"
        assert "valid JSON" in body["error"]["message"]
        assert "Access-Control-Allow-Origin" in response["headers"]

    def test_missing_username(self):
        """Test request with missing username field"""
        from handler import lambda_handler

        # Arrange
        event = {"body": json.dumps({"password": "password123"})}
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"]["code"] == "MISSING_FIELDS"
        assert "Username and password are required" in body["error"]["message"]
        assert "Access-Control-Allow-Origin" in response["headers"]

    def test_missing_password(self):
        """Test request with missing password field"""
        from handler import lambda_handler

        # Arrange
        event = {"body": json.dumps({"username": "testadmin"})}
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"]["code"] == "MISSING_FIELDS"
        assert "Username and password are required" in body["error"]["message"]
        assert "Access-Control-Allow-Origin" in response["headers"]

    def test_empty_username(self):
        """Test request with empty username"""
        from handler import lambda_handler

        # Arrange
        event = {"body": json.dumps({"username": "", "password": "password123"})}
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"]["code"] == "MISSING_FIELDS"
        assert "Access-Control-Allow-Origin" in response["headers"]

    def test_empty_password(self):
        """Test request with empty password"""
        from handler import lambda_handler

        # Arrange
        event = {"body": json.dumps({"username": "testadmin", "password": ""})}
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"]["code"] == "MISSING_FIELDS"
        assert "Access-Control-Allow-Origin" in response["headers"]


class TestAdminLoginErrors:
    """Test error handling scenarios"""

    @patch("handler.query")
    def test_dynamodb_query_error(self, mock_query):
        """Test handling of DynamoDB query errors"""
        from handler import lambda_handler

        # Arrange
        mock_query.side_effect = Exception("DynamoDB connection error")

        event = {
            "body": json.dumps({"username": "testadmin", "password": "password123"})
        }
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert body["error"]["code"] == "DATABASE_ERROR"
        assert "Failed to query admin credentials" in body["error"]["message"]
        assert "Access-Control-Allow-Origin" in response["headers"]

    @patch("handler.query")
    def test_admin_missing_password_hash(self, mock_query):
        """Test handling of admin record without password hash"""
        from handler import lambda_handler

        # Arrange
        mock_query.return_value = [
            {
                "adminId": "admin-123",
                "username": "testadmin",
                # passwordHash is missing
            }
        ]

        event = {
            "body": json.dumps({"username": "testadmin", "password": "password123"})
        }
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert body["error"]["code"] == "INVALID_ADMIN_DATA"
        assert "not properly configured" in body["error"]["message"]
        assert "Access-Control-Allow-Origin" in response["headers"]

    @patch("handler.query")
    @patch("handler.verify_password")
    def test_unexpected_error_in_verify_password(
        self, mock_verify_password, mock_query
    ):
        """Test handling of unexpected errors during password verification"""
        from handler import lambda_handler

        # Arrange
        mock_query.return_value = [
            {
                "adminId": "admin-123",
                "username": "testadmin",
                "passwordHash": "$2b$12$hashedpassword",
            }
        ]
        mock_verify_password.side_effect = Exception("Unexpected bcrypt error")

        event = {
            "body": json.dumps({"username": "testadmin", "password": "password123"})
        }
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert body["error"]["code"] == "INTERNAL_ERROR"
        assert "unexpected error" in body["error"]["message"]
        assert "Access-Control-Allow-Origin" in response["headers"]


class TestAdminLoginCORS:
    """Test CORS headers are present in all responses"""

    @patch("handler.query")
    @patch("handler.verify_password")
    @patch("handler.generate_token")
    def test_cors_headers_on_success(
        self, mock_generate_token, mock_verify_password, mock_query
    ):
        """Test CORS headers present on successful response"""
        from handler import lambda_handler

        # Arrange
        mock_query.return_value = [
            {
                "adminId": "admin-123",
                "username": "testadmin",
                "passwordHash": "$2b$12$hashedpassword",
            }
        ]
        mock_verify_password.return_value = True
        mock_generate_token.return_value = "jwt-token"

        event = {
            "body": json.dumps({"username": "testadmin", "password": "password123"})
        }
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert "headers" in response
        assert "Access-Control-Allow-Origin" in response["headers"]
        assert "Access-Control-Allow-Methods" in response["headers"]
        assert "Access-Control-Allow-Headers" in response["headers"]

    def test_cors_headers_on_error(self):
        """Test CORS headers present on error response"""
        from handler import lambda_handler

        # Arrange
        event = {"body": "invalid json"}
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert "headers" in response
        assert "Access-Control-Allow-Origin" in response["headers"]
        assert "Access-Control-Allow-Methods" in response["headers"]
        assert "Access-Control-Allow-Headers" in response["headers"]
