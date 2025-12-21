"""
Property-Based Tests for Participant Authentication Middleware

Tests cover:
- Property 22: Unauthorized access denial
- Property 23: Token contains participant ID

These tests use Hypothesis for property-based testing to verify universal properties
across many randomly generated inputs.
"""

import json
import pytest
from hypothesis import given, settings, strategies as st
from unittest.mock import patch, MagicMock
import sys
import os
import jwt
from datetime import datetime, timedelta

# Add lambda directories to path
lambda_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "lambda")
)
sys.path.insert(0, os.path.join(lambda_path, "common"))


class TestParticipantAuthenticationProperties:
    """Property-based tests for participant authentication"""

    @settings(max_examples=100, deadline=None)
    @given(
        participant_id=st.uuids(),
        tenant_id=st.uuids(),
        path=st.text(min_size=1, max_size=50),
    )
    def test_property_22_unauthorized_access_denial_missing_token(
        self, participant_id, tenant_id, path
    ):
        """
        Feature: global-participant-registration, Property 22: Unauthorized access denial

        For any request to access a participant profile with an invalid or missing
        authentication token, the system should return a 401 Unauthorized error.

        Validates: Requirements 7.3, 7.4

        This test verifies missing token scenario.
        """
        from participant_middleware import extract_participant_from_token

        # Arrange - Event without Authorization header
        event = {
            "headers": {},
            "path": path,
            "httpMethod": "GET",
        }

        # Act
        participant_context, error = extract_participant_from_token(event)

        # Assert
        assert participant_context is None
        assert error is not None
        assert error["statusCode"] == 401
        body = json.loads(error["body"])
        assert body["error"]["code"] == "MISSING_TOKEN"

    @settings(max_examples=100, deadline=None)
    @given(
        participant_id=st.uuids(),
        tenant_id=st.uuids(),
        invalid_token=st.text(min_size=1, max_size=100),
    )
    def test_property_22_unauthorized_access_denial_invalid_token(
        self, participant_id, tenant_id, invalid_token
    ):
        """
        Feature: global-participant-registration, Property 22: Unauthorized access denial

        For any request with an invalid authentication token, the system should
        return a 401 Unauthorized error.

        Validates: Requirements 7.3, 7.4

        This test verifies invalid token scenario.
        """
        from participant_middleware import extract_participant_from_token

        # Arrange - Event with invalid token
        event = {
            "headers": {"Authorization": f"Bearer {invalid_token}"},
            "httpMethod": "GET",
        }

        # Act
        participant_context, error = extract_participant_from_token(event)

        # Assert
        assert participant_context is None
        assert error is not None
        assert error["statusCode"] == 401
        body = json.loads(error["body"])
        assert body["error"]["code"] in ["INVALID_TOKEN", "TOKEN_EXPIRED"]

    @settings(max_examples=100, deadline=None)
    @given(
        participant_id=st.uuids(),
        tenant_id=st.uuids(),
        wrong_role=st.sampled_from(["admin", "super_admin", "tenant_admin", "user"]),
    )
    def test_property_22_unauthorized_access_denial_wrong_role(
        self, participant_id, tenant_id, wrong_role
    ):
        """
        Feature: global-participant-registration, Property 22: Unauthorized access denial

        For any request with a token that has the wrong role (not 'participant'),
        the system should return a 403 Forbidden error.

        Validates: Requirements 7.3, 7.4

        This test verifies wrong role scenario.
        """
        from participant_middleware import extract_participant_from_token
        from auth import generate_token

        # Arrange - Generate token with wrong role
        token = generate_token(
            user_id=str(participant_id), role=wrong_role, tenant_id=str(tenant_id)
        )

        event = {
            "headers": {"Authorization": f"Bearer {token}"},
            "httpMethod": "GET",
        }

        # Act
        participant_context, error = extract_participant_from_token(event)

        # Assert
        assert participant_context is None
        assert error is not None
        assert error["statusCode"] == 403
        body = json.loads(error["body"])
        assert body["error"]["code"] == "INSUFFICIENT_PERMISSIONS"

    @settings(max_examples=100, deadline=None)
    @given(
        participant_id=st.uuids(),
        tenant_id=st.uuids(),
    )
    def test_property_22_unauthorized_access_denial_expired_token(
        self, participant_id, tenant_id
    ):
        """
        Feature: global-participant-registration, Property 22: Unauthorized access denial

        For any request with an expired authentication token, the system should
        return a 401 Unauthorized error.

        Validates: Requirements 7.3, 7.4

        This test verifies expired token scenario.
        """
        from participant_middleware import extract_participant_from_token
        import os

        # Arrange - Generate expired token
        JWT_SECRET = os.environ.get("JWT_SECRET", "default-secret-change-in-production")
        JWT_ALGORITHM = "HS256"

        # Create token that expired 1 hour ago
        now = datetime.utcnow()
        expiration = now - timedelta(hours=1)

        payload = {
            "sub": str(participant_id),
            "role": "participant",
            "tenantId": str(tenant_id),
            "iat": int((now - timedelta(hours=2)).timestamp()),
            "exp": int(expiration.timestamp()),
        }

        expired_token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        event = {
            "headers": {"Authorization": f"Bearer {expired_token}"},
            "httpMethod": "GET",
        }

        # Act
        participant_context, error = extract_participant_from_token(event)

        # Assert
        assert participant_context is None
        assert error is not None
        assert error["statusCode"] == 401
        body = json.loads(error["body"])
        assert body["error"]["code"] == "TOKEN_EXPIRED"

    @settings(max_examples=100, deadline=None)
    @given(
        tenant_id=st.uuids(),
    )
    def test_property_22_unauthorized_access_denial_missing_participant_id(
        self, tenant_id
    ):
        """
        Feature: global-participant-registration, Property 22: Unauthorized access denial

        For any request with a token missing the participant ID, the system should
        return a 401 Unauthorized error.

        Validates: Requirements 7.3, 7.4

        This test verifies missing participant ID in token scenario.
        """
        from participant_middleware import extract_participant_from_token
        import os

        # Arrange - Generate token without participant ID (sub)
        JWT_SECRET = os.environ.get("JWT_SECRET", "default-secret-change-in-production")
        JWT_ALGORITHM = "HS256"

        now = datetime.utcnow()
        expiration = now + timedelta(hours=24)

        payload = {
            # Missing "sub" field
            "role": "participant",
            "tenantId": str(tenant_id),
            "iat": int(now.timestamp()),
            "exp": int(expiration.timestamp()),
        }

        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        event = {
            "headers": {"Authorization": f"Bearer {token}"},
            "httpMethod": "GET",
        }

        # Act
        participant_context, error = extract_participant_from_token(event)

        # Assert
        assert participant_context is None
        assert error is not None
        assert error["statusCode"] == 401
        body = json.loads(error["body"])
        assert body["error"]["code"] == "INVALID_TOKEN"
        assert "participant ID" in body["error"]["message"]

    @settings(max_examples=100, deadline=None)
    @given(
        participant_id=st.uuids(),
    )
    def test_property_22_unauthorized_access_denial_missing_tenant_id(
        self, participant_id
    ):
        """
        Feature: global-participant-registration, Property 22: Unauthorized access denial

        For any request with a token missing the tenant ID, the system should
        return a 401 Unauthorized error.

        Validates: Requirements 7.3, 7.4

        This test verifies missing tenant ID in token scenario.
        """
        from participant_middleware import extract_participant_from_token
        import os

        # Arrange - Generate token without tenant ID
        JWT_SECRET = os.environ.get("JWT_SECRET", "default-secret-change-in-production")
        JWT_ALGORITHM = "HS256"

        now = datetime.utcnow()
        expiration = now + timedelta(hours=24)

        payload = {
            "sub": str(participant_id),
            "role": "participant",
            # Missing "tenantId" field
            "iat": int(now.timestamp()),
            "exp": int(expiration.timestamp()),
        }

        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        event = {
            "headers": {"Authorization": f"Bearer {token}"},
            "httpMethod": "GET",
        }

        # Act
        participant_context, error = extract_participant_from_token(event)

        # Assert
        assert participant_context is None
        assert error is not None
        assert error["statusCode"] == 401
        body = json.loads(error["body"])
        assert body["error"]["code"] == "INVALID_TOKEN"
        assert "tenant ID" in body["error"]["message"]

    @settings(max_examples=100, deadline=None)
    @given(
        authorization_header=st.text(min_size=1, max_size=100).filter(
            lambda x: not x.startswith("Bearer ")
        ),
    )
    def test_property_22_unauthorized_access_denial_invalid_auth_format(
        self, authorization_header
    ):
        """
        Feature: global-participant-registration, Property 22: Unauthorized access denial

        For any request with an Authorization header that doesn't follow the
        'Bearer <token>' format, the system should return a 401 Unauthorized error.

        Validates: Requirements 7.3, 7.4

        This test verifies invalid authorization header format scenario.
        """
        from participant_middleware import extract_participant_from_token

        # Arrange - Event with invalid Authorization header format
        event = {
            "headers": {"Authorization": authorization_header},
            "httpMethod": "GET",
        }

        # Act
        participant_context, error = extract_participant_from_token(event)

        # Assert
        assert participant_context is None
        assert error is not None
        assert error["statusCode"] == 401
        body = json.loads(error["body"])
        assert body["error"]["code"] == "INVALID_AUTH_FORMAT"

    @settings(max_examples=100, deadline=None)
    @given(
        participant_id=st.uuids(),
        tenant_id=st.uuids(),
        name=st.text(min_size=1, max_size=100),
    )
    def test_property_23_token_contains_participant_id(
        self, participant_id, tenant_id, name
    ):
        """
        Feature: global-participant-registration, Property 23: Token contains participant ID

        For any participant authentication token generated, decoding the JWT should
        reveal a payload containing the global participant ID.

        Validates: Requirements 7.5

        This test verifies that valid tokens contain the participant ID.
        """
        from participant_middleware import extract_participant_from_token
        from auth import generate_token

        # Arrange - Generate valid participant token
        token = generate_token(
            user_id=str(participant_id), role="participant", tenant_id=str(tenant_id)
        )

        event = {
            "headers": {"Authorization": f"Bearer {token}"},
            "httpMethod": "GET",
        }

        # Act
        participant_context, error = extract_participant_from_token(event)

        # Assert - No error should occur
        assert error is None
        assert participant_context is not None

        # Verify participant ID is in the context
        assert "participantId" in participant_context
        assert participant_context["participantId"] == str(participant_id)

        # Verify tenant ID is also in the context
        assert "tenantId" in participant_context
        assert participant_context["tenantId"] == str(tenant_id)

        # Verify role is correct
        assert "role" in participant_context
        assert participant_context["role"] == "participant"

        # Also verify by decoding the token directly
        decoded = jwt.decode(token, options={"verify_signature": False})
        assert decoded["sub"] == str(participant_id)
        assert decoded["tenantId"] == str(tenant_id)
        assert decoded["role"] == "participant"

    @settings(max_examples=100, deadline=None)
    @given(
        participant_id=st.uuids(),
        tenant_id=st.uuids(),
    )
    @patch("participant_middleware.get_item")
    def test_property_22_unauthorized_access_denial_participant_not_found(
        self, mock_get_item, participant_id, tenant_id
    ):
        """
        Feature: global-participant-registration, Property 22: Unauthorized access denial

        For any request with a valid token but the participant doesn't exist in the database,
        the system should return a 404 Not Found error.

        Validates: Requirements 7.3, 7.4

        This test verifies participant existence validation.
        """
        from participant_middleware import require_participant_auth
        from auth import generate_token

        # Arrange - Generate valid token but participant doesn't exist
        token = generate_token(
            user_id=str(participant_id), role="participant", tenant_id=str(tenant_id)
        )

        # Mock database to return None (participant not found)
        mock_get_item.return_value = None

        event = {
            "headers": {"Authorization": f"Bearer {token}"},
            "httpMethod": "GET",
        }

        # Act
        participant_context, error = require_participant_auth(event)

        # Assert
        assert participant_context is None
        assert error is not None
        assert error["statusCode"] == 404
        body = json.loads(error["body"])
        assert body["error"]["code"] == "PARTICIPANT_NOT_FOUND"

    @settings(max_examples=100, deadline=None)
    @given(
        participant_id=st.uuids(),
        token_tenant_id=st.uuids(),
        db_tenant_id=st.uuids(),
    )
    @patch("participant_middleware.get_item")
    def test_property_22_unauthorized_access_denial_tenant_mismatch(
        self, mock_get_item, participant_id, token_tenant_id, db_tenant_id
    ):
        """
        Feature: global-participant-registration, Property 22: Unauthorized access denial

        For any request where the token's tenant ID doesn't match the participant's
        tenant ID in the database, the system should return a 401 Unauthorized error.

        Validates: Requirements 7.3, 7.4

        This test verifies tenant ID consistency validation.
        """
        # Only run test if tenant IDs are different
        if token_tenant_id == db_tenant_id:
            pytest.skip("Tenant IDs must be different for this test")

        from participant_middleware import require_participant_auth
        from auth import generate_token

        # Arrange - Generate token with one tenant ID
        token = generate_token(
            user_id=str(participant_id),
            role="participant",
            tenant_id=str(token_tenant_id),
        )

        # Mock database to return participant with different tenant ID
        mock_get_item.return_value = {
            "participantId": str(participant_id),
            "tenantId": str(db_tenant_id),
            "name": "Test Participant",
            "avatar": "😀",
        }

        event = {
            "headers": {"Authorization": f"Bearer {token}"},
            "httpMethod": "GET",
        }

        # Act
        participant_context, error = require_participant_auth(event)

        # Assert
        assert participant_context is None
        assert error is not None
        assert error["statusCode"] == 401
        body = json.loads(error["body"])
        assert body["error"]["code"] == "INVALID_TOKEN"
        assert "tenant" in body["error"]["message"].lower()

    @settings(max_examples=100, deadline=None)
    @given(
        participant_id=st.uuids(),
        tenant_id=st.uuids(),
        name=st.text(min_size=1, max_size=100),
        avatar=st.sampled_from(["😀", "😎", "🤓", "🥳"]),
    )
    @patch("participant_middleware.get_item")
    def test_successful_authentication_with_valid_token(
        self, mock_get_item, participant_id, tenant_id, name, avatar
    ):
        """
        Verify that authentication succeeds with a valid token and existing participant.

        This is a positive test case to ensure the authentication flow works correctly.
        """
        from participant_middleware import require_participant_auth
        from auth import generate_token

        # Arrange - Generate valid token and mock participant exists
        token = generate_token(
            user_id=str(participant_id), role="participant", tenant_id=str(tenant_id)
        )

        mock_get_item.return_value = {
            "participantId": str(participant_id),
            "tenantId": str(tenant_id),
            "name": name,
            "avatar": avatar,
        }

        event = {
            "headers": {"Authorization": f"Bearer {token}"},
            "httpMethod": "GET",
        }

        # Act
        participant_context, error = require_participant_auth(event)

        # Assert - Should succeed
        assert error is None
        assert participant_context is not None
        assert participant_context["participantId"] == str(participant_id)
        assert participant_context["tenantId"] == str(tenant_id)
        assert participant_context["role"] == "participant"
        assert "participant" in participant_context
        assert participant_context["participant"]["name"] == name
        assert participant_context["participant"]["avatar"] == avatar
