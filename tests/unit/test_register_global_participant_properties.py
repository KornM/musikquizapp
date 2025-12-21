"""
Property-Based Tests for Register Global Participant Lambda Handler

Tests cover:
- Property 1: Global participant creation generates unique ID
- Property 2: Participant profile storage
- Property 3: Profile independence from sessions
- Property 4: Authentication token generation
- Property 5: Participant ID in response
- Property 34: Participant tenant association

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
sys.path.insert(0, os.path.join(lambda_path, "register_global_participant"))
sys.path.insert(0, os.path.join(lambda_path, "common"))


class TestGlobalParticipantRegistrationProperties:
    """Property-based tests for global participant registration"""

    @patch("handler.put_item")
    @patch("handler.get_item")
    def test_property_1_unique_participant_id_generation(
        self, mock_get_item, mock_put_item
    ):
        """
        Feature: global-participant-registration, Property 1: Global participant creation generates unique ID

        For any participant registration request, the system should create a global participant
        record with a unique participant ID that doesn't collide with existing IDs.

        Validates: Requirements 1.1, 7.1
        """
        from handler import lambda_handler

        # Arrange
        mock_get_item.return_value = {"tenantId": "test-tenant", "status": "active"}
        mock_put_item.return_value = {}

        # Track generated participant IDs across all calls
        generated_ids = []

        # Act - Create multiple participants
        for i in range(100):
            event = {
                "body": json.dumps(
                    {
                        "tenantId": "test-tenant",
                        "name": f"Participant {i}",
                        "avatar": "😀",
                    }
                )
            }
            context = {}

            response = lambda_handler(event, context)

            # Assert
            assert response["statusCode"] == 201
            body = json.loads(response["body"])
            participant_id = body["participantId"]

            # Verify participant ID is a valid UUID format
            import uuid

            try:
                uuid.UUID(participant_id)
            except ValueError:
                pytest.fail(
                    f"Generated participant ID '{participant_id}' is not a valid UUID"
                )

            generated_ids.append(participant_id)

        # Verify all IDs are unique
        assert len(generated_ids) == len(set(generated_ids)), (
            "Participant ID collision detected"
        )

    @settings(max_examples=100)
    @given(
        name=st.text(min_size=1, max_size=100),
        avatar=st.sampled_from(["😀", "😎", "🤓", "🥳", "🎉", "🎵", "🎸", "🎤"]),
    )
    @patch("handler.put_item")
    @patch("handler.get_item")
    def test_property_2_participant_profile_storage(
        self, mock_get_item, mock_put_item, name, avatar
    ):
        """
        Feature: global-participant-registration, Property 2: Participant profile storage

        For any name and avatar combination provided during registration, the system should
        store these values in the global participant profile and return them unchanged when retrieved.

        Validates: Requirements 1.2
        """
        from handler import lambda_handler

        # Arrange
        mock_get_item.return_value = {"tenantId": "test-tenant", "status": "active"}
        mock_put_item.return_value = {}

        event = {
            "body": json.dumps(
                {"tenantId": "test-tenant", "name": name, "avatar": avatar}
            )
        }
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 201
        body = json.loads(response["body"])

        # Verify stored values match input
        assert body["name"] == name
        assert body["avatar"] == avatar

        # Verify put_item was called with correct data
        assert mock_put_item.called
        call_args = mock_put_item.call_args
        stored_participant = call_args[0][1]  # Second argument is the item

        assert stored_participant["name"] == name
        assert stored_participant["avatar"] == avatar

    @settings(max_examples=100)
    @given(
        name=st.text(min_size=1, max_size=100),
        avatar=st.sampled_from(["😀", "😎", "🤓", "🥳"]),
    )
    @patch("handler.put_item")
    @patch("handler.get_item")
    def test_property_3_profile_independence_from_sessions(
        self, mock_get_item, mock_put_item, name, avatar
    ):
        """
        Feature: global-participant-registration, Property 3: Profile independence from sessions

        For any global participant created, the participant record should exist in the
        GlobalParticipants table without any session reference (sessionId field should not
        exist in the participant record).

        Validates: Requirements 1.3
        """
        from handler import lambda_handler

        # Arrange
        mock_get_item.return_value = {"tenantId": "test-tenant", "status": "active"}
        mock_put_item.return_value = {}

        event = {
            "body": json.dumps(
                {"tenantId": "test-tenant", "name": name, "avatar": avatar}
            )
        }
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 201
        body = json.loads(response["body"])

        # Verify no sessionId field exists in the response
        assert "sessionId" not in body

        # Verify put_item was called without sessionId
        assert mock_put_item.called
        call_args = mock_put_item.call_args
        stored_participant = call_args[0][1]

        assert "sessionId" not in stored_participant

    @settings(max_examples=100)
    @given(
        name=st.text(min_size=1, max_size=100),
        avatar=st.sampled_from(["😀", "😎", "🤓", "🥳"]),
    )
    @patch("handler.put_item")
    @patch("handler.get_item")
    def test_property_4_authentication_token_generation(
        self, mock_get_item, mock_put_item, name, avatar
    ):
        """
        Feature: global-participant-registration, Property 4: Authentication token generation

        For any global participant creation, the system should generate a valid JWT token
        and include it in the response.

        Validates: Requirements 1.4
        """
        from handler import lambda_handler
        import jwt

        # Arrange
        mock_get_item.return_value = {"tenantId": "test-tenant", "status": "active"}
        mock_put_item.return_value = {}

        event = {
            "body": json.dumps(
                {"tenantId": "test-tenant", "name": name, "avatar": avatar}
            )
        }
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 201
        body = json.loads(response["body"])

        # Verify token is present in response
        assert "token" in body
        assert body["token"] is not None
        assert len(body["token"]) > 0

        # Verify token is a valid JWT and contains correct data
        token = body["token"]
        decoded = jwt.decode(token, options={"verify_signature": False})

        # Token should contain participant ID, role, and tenant ID
        assert "sub" in decoded  # participant ID
        assert decoded["role"] == "participant"
        assert decoded["tenantId"] == "test-tenant"

    @settings(max_examples=100)
    @given(
        name=st.text(min_size=1, max_size=100),
        avatar=st.sampled_from(["😀", "😎", "🤓", "🥳"]),
    )
    @patch("handler.put_item")
    @patch("handler.get_item")
    def test_property_5_participant_id_in_response(
        self, mock_get_item, mock_put_item, name, avatar
    ):
        """
        Feature: global-participant-registration, Property 5: Participant ID in response

        For any participant registration, the API response should contain the global participant ID.

        Validates: Requirements 1.5
        """
        from handler import lambda_handler

        # Arrange
        mock_get_item.return_value = {"tenantId": "test-tenant", "status": "active"}
        mock_put_item.return_value = {}

        event = {
            "body": json.dumps(
                {"tenantId": "test-tenant", "name": name, "avatar": avatar}
            )
        }
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 201
        body = json.loads(response["body"])

        # Verify participantId is present in response
        assert "participantId" in body
        assert body["participantId"] is not None
        assert len(body["participantId"]) > 0

        # Verify it's a valid UUID
        import uuid

        try:
            uuid.UUID(body["participantId"])
        except ValueError:
            pytest.fail(f"Participant ID '{body['participantId']}' is not a valid UUID")

    @settings(max_examples=100)
    @given(
        name=st.text(min_size=1, max_size=100),
        avatar=st.sampled_from(["😀", "😎", "🤓", "🥳"]),
        tenant_id=st.uuids(),
    )
    @patch("handler.put_item")
    @patch("handler.get_item")
    def test_property_34_participant_tenant_association(
        self, mock_get_item, mock_put_item, name, avatar, tenant_id
    ):
        """
        Feature: global-participant-registration, Property 34: Participant tenant association

        For any participant registration, the participant record should contain a tenantId field.

        Validates: Requirements 11.1
        """
        from handler import lambda_handler

        # Arrange
        tenant_id_str = str(tenant_id)
        mock_get_item.return_value = {"tenantId": tenant_id_str, "status": "active"}
        mock_put_item.return_value = {}

        event = {
            "body": json.dumps(
                {"tenantId": tenant_id_str, "name": name, "avatar": avatar}
            )
        }
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 201
        body = json.loads(response["body"])

        # Verify tenantId is present in response
        assert "tenantId" in body
        assert body["tenantId"] == tenant_id_str

        # Verify put_item was called with tenantId
        assert mock_put_item.called
        call_args = mock_put_item.call_args
        stored_participant = call_args[0][1]

        assert "tenantId" in stored_participant
        assert stored_participant["tenantId"] == tenant_id_str

    @settings(max_examples=100)
    @given(
        name=st.text(min_size=1, max_size=100),
        avatar=st.sampled_from(["😀", "😎", "🤓", "🥳"]),
    )
    @patch("handler.get_item")
    def test_tenant_not_found_rejection(self, mock_get_item, name, avatar):
        """
        Verify that registration is rejected when tenant doesn't exist.
        """
        from handler import lambda_handler

        # Arrange - Tenant doesn't exist
        mock_get_item.return_value = None

        event = {
            "body": json.dumps(
                {"tenantId": "nonexistent-tenant", "name": name, "avatar": avatar}
            )
        }
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert body["error"]["code"] == "TENANT_NOT_FOUND"

    @settings(max_examples=100)
    @given(
        name=st.text(min_size=1, max_size=100),
        avatar=st.sampled_from(["😀", "😎", "🤓", "🥳"]),
    )
    @patch("handler.get_item")
    def test_inactive_tenant_rejection(self, mock_get_item, name, avatar):
        """
        Verify that registration is rejected when tenant is inactive.
        """
        from handler import lambda_handler

        # Arrange - Tenant exists but is inactive
        mock_get_item.return_value = {"tenantId": "test-tenant", "status": "inactive"}

        event = {
            "body": json.dumps(
                {"tenantId": "test-tenant", "name": name, "avatar": avatar}
            )
        }
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 403
        body = json.loads(response["body"])
        assert body["error"]["code"] == "TENANT_INACTIVE"

    @settings(max_examples=100)
    @given(
        avatar=st.sampled_from(["😀", "😎", "🤓", "🥳"]),
    )
    def test_missing_name_rejection(self, avatar):
        """
        Verify that registration is rejected when name is missing.
        """
        from handler import lambda_handler

        # Arrange - Request without name
        event = {"body": json.dumps({"tenantId": "test-tenant", "avatar": avatar})}
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"]["code"] == "MISSING_FIELDS"
        assert "name" in body["error"]["message"].lower()

    @settings(max_examples=100)
    @given(
        name=st.text(min_size=1, max_size=100),
    )
    def test_missing_tenant_id_rejection(self, name):
        """
        Verify that registration is rejected when tenantId is missing.
        """
        from handler import lambda_handler

        # Arrange - Request without tenantId
        event = {"body": json.dumps({"name": name, "avatar": "😀"})}
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"]["code"] == "MISSING_FIELDS"
        assert "tenantid" in body["error"]["message"].lower()
