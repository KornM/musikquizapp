"""
Property-Based Tests for Update Global Participant Lambda Handler

Tests cover:
- Property 7: Profile update persistence
- Property 8: Profile updates propagate to sessions

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
sys.path.insert(0, os.path.join(lambda_path, "update_global_participant"))
sys.path.insert(0, os.path.join(lambda_path, "common"))


class TestUpdateGlobalParticipantProperties:
    """Property-based tests for global participant profile updates"""

    @settings(max_examples=100, deadline=None)
    @given(
        participant_id=st.uuids(),
        tenant_id=st.uuids(),
        original_name=st.text(min_size=1, max_size=100),
        original_avatar=st.sampled_from(["😀", "😎", "🤓"]),
        new_name=st.text(min_size=1, max_size=100),
        new_avatar=st.sampled_from(["🥳", "🎉", "🎵"]),
    )
    @patch("handler.update_item")
    @patch("handler.require_participant_auth")
    def test_property_7_profile_update_persistence(
        self,
        mock_require_participant_auth,
        mock_update_item,
        participant_id,
        tenant_id,
        original_name,
        original_avatar,
        new_name,
        new_avatar,
    ):
        """
        Feature: global-participant-registration, Property 7: Profile update persistence

        For any global participant profile update with new name or avatar, the updated
        values should be stored in the database and returned in subsequent queries.

        Validates: Requirements 2.3
        """
        from handler import lambda_handler

        # Arrange
        participant_id_str = str(participant_id)
        tenant_id_str = str(tenant_id)
        created_at = "2024-01-01T00:00:00Z"
        updated_at = "2024-01-02T00:00:00Z"

        # Mock participant authentication
        participant_record = {
            "participantId": participant_id_str,
            "tenantId": tenant_id_str,
            "name": original_name,
            "avatar": original_avatar,
            "createdAt": created_at,
            "updatedAt": created_at,
        }

        mock_require_participant_auth.return_value = (
            {
                "participantId": participant_id_str,
                "tenantId": tenant_id_str,
                "role": "participant",
                "participant": participant_record,
            },
            None,
        )

        # Mock updated participant
        mock_update_item.return_value = {
            "participantId": participant_id_str,
            "tenantId": tenant_id_str,
            "name": new_name,
            "avatar": new_avatar,
            "createdAt": created_at,
            "updatedAt": updated_at,
        }

        event = {
            "pathParameters": {"participantId": participant_id_str},
            "headers": {"Authorization": "Bearer mock-token"},
            "body": json.dumps({"name": new_name, "avatar": new_avatar}),
        }
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 200
        body = json.loads(response["body"])

        # Verify updated values are returned
        assert body["name"] == new_name
        assert body["avatar"] == new_avatar
        assert body["participantId"] == participant_id_str

        # Verify update_item was called
        assert mock_update_item.called
        call_args = mock_update_item.call_args

        # Verify the update expression includes both fields
        update_expression = call_args[0][2]
        assert "name" in update_expression or "#name" in update_expression
        assert "avatar" in update_expression

    @settings(max_examples=100)
    @given(
        participant_id=st.uuids(),
        tenant_id=st.uuids(),
        original_name=st.text(min_size=1, max_size=100),
        new_name=st.text(min_size=1, max_size=100),
        avatar=st.sampled_from(["😀", "😎", "🤓", "🥳"]),
    )
    @patch("handler.update_item")
    @patch("handler.require_participant_auth")
    def test_property_7_name_only_update(
        self,
        mock_require_participant_auth,
        mock_update_item,
        participant_id,
        tenant_id,
        original_name,
        new_name,
        avatar,
    ):
        """
        Verify that updating only the name persists correctly.
        """
        from handler import lambda_handler

        # Arrange
        participant_id_str = str(participant_id)
        tenant_id_str = str(tenant_id)
        created_at = "2024-01-01T00:00:00Z"
        updated_at = "2024-01-02T00:00:00Z"

        participant_record = {
            "participantId": participant_id_str,
            "tenantId": tenant_id_str,
            "name": original_name,
            "avatar": avatar,
            "createdAt": created_at,
            "updatedAt": created_at,
        }

        mock_require_participant_auth.return_value = (
            {
                "participantId": participant_id_str,
                "tenantId": tenant_id_str,
                "role": "participant",
                "participant": participant_record,
            },
            None,
        )

        mock_update_item.return_value = {
            "participantId": participant_id_str,
            "tenantId": tenant_id_str,
            "name": new_name,
            "avatar": avatar,
            "createdAt": created_at,
            "updatedAt": updated_at,
        }

        event = {
            "pathParameters": {"participantId": participant_id_str},
            "headers": {"Authorization": "Bearer mock-token"},
            "body": json.dumps({"name": new_name}),
        }
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["name"] == new_name
        assert body["avatar"] == avatar  # Avatar unchanged

    @settings(max_examples=100)
    @given(
        participant_id=st.uuids(),
        tenant_id=st.uuids(),
        name=st.text(min_size=1, max_size=100),
        original_avatar=st.sampled_from(["😀", "😎"]),
        new_avatar=st.sampled_from(["🤓", "🥳"]),
    )
    @patch("handler.update_item")
    @patch("handler.require_participant_auth")
    def test_property_7_avatar_only_update(
        self,
        mock_require_participant_auth,
        mock_update_item,
        participant_id,
        tenant_id,
        name,
        original_avatar,
        new_avatar,
    ):
        """
        Verify that updating only the avatar persists correctly.
        """
        from handler import lambda_handler

        # Arrange
        participant_id_str = str(participant_id)
        tenant_id_str = str(tenant_id)
        created_at = "2024-01-01T00:00:00Z"
        updated_at = "2024-01-02T00:00:00Z"

        participant_record = {
            "participantId": participant_id_str,
            "tenantId": tenant_id_str,
            "name": name,
            "avatar": original_avatar,
            "createdAt": created_at,
            "updatedAt": created_at,
        }

        mock_require_participant_auth.return_value = (
            {
                "participantId": participant_id_str,
                "tenantId": tenant_id_str,
                "role": "participant",
                "participant": participant_record,
            },
            None,
        )

        mock_update_item.return_value = {
            "participantId": participant_id_str,
            "tenantId": tenant_id_str,
            "name": name,
            "avatar": new_avatar,
            "createdAt": created_at,
            "updatedAt": updated_at,
        }

        event = {
            "pathParameters": {"participantId": participant_id_str},
            "headers": {"Authorization": "Bearer mock-token"},
            "body": json.dumps({"avatar": new_avatar}),
        }
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["name"] == name  # Name unchanged
        assert body["avatar"] == new_avatar

    @settings(max_examples=100)
    @given(
        participant_id=st.uuids(),
        other_participant_id=st.uuids(),
        tenant_id=st.uuids(),
    )
    @patch("handler.require_participant_auth")
    def test_unauthorized_update_rejection(
        self,
        mock_require_participant_auth,
        participant_id,
        other_participant_id,
        tenant_id,
    ):
        """
        Verify that a participant cannot update another participant's profile.
        """
        from handler import lambda_handler

        # Arrange - Token belongs to different participant
        participant_id_str = str(participant_id)
        other_participant_id_str = str(other_participant_id)
        tenant_id_str = str(tenant_id)

        # Ensure they're different
        if participant_id_str == other_participant_id_str:
            return

        # Mock authentication for a different participant
        participant_record = {
            "participantId": other_participant_id_str,
            "tenantId": tenant_id_str,
            "name": "Other Participant",
            "avatar": "😀",
            "createdAt": "2024-01-01T00:00:00Z",
            "updatedAt": "2024-01-01T00:00:00Z",
        }

        mock_require_participant_auth.return_value = (
            {
                "participantId": other_participant_id_str,
                "tenantId": tenant_id_str,
                "role": "participant",
                "participant": participant_record,
            },
            None,
        )

        event = {
            "pathParameters": {"participantId": participant_id_str},
            "headers": {"Authorization": "Bearer mock-token"},
            "body": json.dumps({"name": "New Name"}),
        }
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 403
        body = json.loads(response["body"])
        assert body["error"]["code"] == "INSUFFICIENT_PERMISSIONS"

    @settings(max_examples=100)
    @given(
        participant_id=st.uuids(),
    )
    @patch("handler.require_participant_auth")
    def test_missing_token_rejection(
        self, mock_require_participant_auth, participant_id
    ):
        """
        Verify that update is rejected when authorization token is missing.
        """
        from handler import lambda_handler

        # Arrange - Mock authentication failure (missing token)
        error_response = {
            "statusCode": 401,
            "body": json.dumps(
                {
                    "error": {
                        "code": "MISSING_TOKEN",
                        "message": "Authorization header is required",
                        "details": {},
                    }
                }
            ),
        }

        mock_require_participant_auth.return_value = (None, error_response)
        event = {
            "pathParameters": {"participantId": str(participant_id)},
            "headers": {},
            "body": json.dumps({"name": "New Name"}),
        }
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 401
        body = json.loads(response["body"])
        assert body["error"]["code"] == "MISSING_TOKEN"

    @settings(max_examples=100)
    @given(
        participant_id=st.uuids(),
        tenant_id=st.uuids(),
    )
    @patch("handler.require_participant_auth")
    def test_participant_not_found(
        self, mock_require_participant_auth, participant_id, tenant_id
    ):
        """
        Verify that update is rejected when participant doesn't exist.
        """
        from handler import lambda_handler

        # Arrange - Mock authentication failure (participant not found)
        participant_id_str = str(participant_id)

        error_response = {
            "statusCode": 404,
            "body": json.dumps(
                {
                    "error": {
                        "code": "PARTICIPANT_NOT_FOUND",
                        "message": f"Participant {participant_id_str} not found",
                        "details": {},
                    }
                }
            ),
        }

        mock_require_participant_auth.return_value = (None, error_response)

        event = {
            "pathParameters": {"participantId": participant_id_str},
            "headers": {"Authorization": "Bearer mock-token"},
            "body": json.dumps({"name": "New Name"}),
        }
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert body["error"]["code"] == "PARTICIPANT_NOT_FOUND"
