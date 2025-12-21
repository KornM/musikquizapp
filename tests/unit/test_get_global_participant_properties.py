"""
Property-Based Tests for Get Global Participant Lambda Handler

Tests cover:
- Property 6: Profile retrieval

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
sys.path.insert(0, os.path.join(lambda_path, "get_global_participant"))
sys.path.insert(0, os.path.join(lambda_path, "common"))


class TestGetGlobalParticipantProperties:
    """Property-based tests for global participant profile retrieval"""

    @patch("handler.get_item")
    @settings(max_examples=100)
    @given(
        participant_id=st.uuids(),
        tenant_id=st.uuids(),
        name=st.text(min_size=1, max_size=100),
        avatar=st.sampled_from(["😀", "😎", "🤓", "🥳", "🎉", "🎵"]),
    )
    def test_property_6_profile_retrieval(
        self, mock_get_item, participant_id, tenant_id, name, avatar
    ):
        """
        Feature: global-participant-registration, Property 6: Profile retrieval

        For any existing global participant ID, querying the system should return
        the participant's profile with matching name and avatar.

        Validates: Requirements 2.1
        """
        from handler import lambda_handler

        # Arrange
        participant_id_str = str(participant_id)
        tenant_id_str = str(tenant_id)
        created_at = "2024-01-01T00:00:00Z"

        # Mock the database to return a participant
        mock_get_item.return_value = {
            "participantId": participant_id_str,
            "tenantId": tenant_id_str,
            "name": name,
            "avatar": avatar,
            "token": "some-jwt-token",  # Should not be returned
            "createdAt": created_at,
            "updatedAt": created_at,
        }

        event = {"pathParameters": {"participantId": participant_id_str}}
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 200
        body = json.loads(response["body"])

        # Verify profile contains correct data
        assert body["participantId"] == participant_id_str
        assert body["tenantId"] == tenant_id_str
        assert body["name"] == name
        assert body["avatar"] == avatar
        assert body["createdAt"] == created_at

        # Verify token is NOT included in response (security)
        assert "token" not in body

        # Verify get_item was called with correct key
        assert mock_get_item.called
        call_args = mock_get_item.call_args
        assert call_args[0][1] == {"participantId": participant_id_str}

    @patch("handler.get_item")
    @settings(max_examples=100)
    @given(
        participant_id=st.uuids(),
    )
    def test_participant_not_found(self, mock_get_item, participant_id):
        """
        Verify that retrieval returns 404 when participant doesn't exist.
        """
        from handler import lambda_handler

        # Arrange - Participant doesn't exist
        mock_get_item.return_value = None

        event = {"pathParameters": {"participantId": str(participant_id)}}
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert body["error"]["code"] == "PARTICIPANT_NOT_FOUND"

    def test_missing_participant_id(self):
        """
        Verify that retrieval returns 400 when participantId is missing.
        """
        from handler import lambda_handler

        # Arrange - No path parameters
        event = {"pathParameters": {}}
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"]["code"] == "MISSING_FIELDS"
