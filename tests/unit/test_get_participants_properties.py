"""
Property-Based Tests for Get Participants Lambda Handler

Tests cover:
- Property 13: Complete participant list for session
- Property 14: Participant list contains required fields
- Property 15: Participant list reflects current profile
- Property 36: Participant list tenant filtering

These tests use Hypothesis for property-based testing to verify universal properties
across many randomly generated inputs.

Validates: Requirements 4.1, 4.2, 4.3, 4.5, 11.4
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
sys.path.insert(0, os.path.join(lambda_path, "get_participants"))
sys.path.insert(0, os.path.join(lambda_path, "common"))


class TestGetParticipantsProperties:
    """Property-based tests for getting session participants"""

    @settings(max_examples=100, deadline=None)
    @given(
        session_id=st.uuids(),
        tenant_id=st.uuids(),
        num_participants=st.integers(min_value=1, max_value=10),
    )
    @patch("handler.get_item")
    @patch("handler.query")
    @patch("handler.validate_token")
    def test_property_13_complete_participant_list_for_session(
        self,
        mock_validate_token,
        mock_query,
        mock_get_item,
        session_id,
        tenant_id,
        num_participants,
    ):
        """
        Feature: global-participant-registration, Property 13: Complete participant list for session

        For any session, querying the participant list should return all participants who have
        joined that session (all SessionParticipations records for that sessionId).

        Validates: Requirements 4.1
        """
        from handler import lambda_handler

        # Arrange
        session_id_str = str(session_id)
        tenant_id_str = str(tenant_id)

        # Mock admin authentication
        mock_validate_token.return_value = {
            "sub": "admin-id",
            "role": "tenant_admin",
            "tenantId": tenant_id_str,
        }

        # Mock session exists
        mock_get_item.side_effect = (
            lambda table, key: {
                "sessionId": session_id_str,
                "tenantId": tenant_id_str,
                "status": "active",
            }
            if key.get("sessionId") == session_id_str
            else {
                "participantId": key.get("participantId"),
                "tenantId": tenant_id_str,
                "name": f"Participant {key.get('participantId')[:8]}",
                "avatar": "😀",
            }
        )

        # Create mock participations
        participations = []
        for i in range(num_participants):
            participant_id = f"participant-{i}"
            participations.append(
                {
                    "participationId": f"participation-{i}",
                    "participantId": participant_id,
                    "sessionId": session_id_str,
                    "tenantId": tenant_id_str,
                    "joinedAt": f"2024-01-01T00:00:{i:02d}Z",
                    "totalPoints": i * 10,
                    "correctAnswers": i,
                }
            )

        mock_query.return_value = participations

        event = {
            "headers": {"Authorization": "Bearer valid-token"},
            "pathParameters": {"sessionId": session_id_str},
        }
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 200
        body = json.loads(response["body"])

        # Verify all participants are returned
        assert "participants" in body
        assert len(body["participants"]) == num_participants

        # Verify query was called with correct sessionId
        assert mock_query.called
        call_args = mock_query.call_args
        assert session_id_str in str(call_args)

    @settings(max_examples=100, deadline=None)
    @given(
        session_id=st.uuids(),
        tenant_id=st.uuids(),
        participant_id=st.uuids(),
        name=st.text(min_size=1, max_size=100),
        avatar=st.sampled_from(["😀", "😎", "🤓", "🥳"]),
        total_points=st.integers(min_value=0, max_value=1000),
        correct_answers=st.integers(min_value=0, max_value=50),
    )
    @patch("handler.get_item")
    @patch("handler.query")
    @patch("handler.validate_token")
    def test_property_14_participant_list_contains_required_fields(
        self,
        mock_validate_token,
        mock_query,
        mock_get_item,
        session_id,
        tenant_id,
        participant_id,
        name,
        avatar,
        total_points,
        correct_answers,
    ):
        """
        Feature: global-participant-registration, Property 14: Participant list contains required fields

        For any participant in a session participant list, the response should include the
        participant's name, avatar, and current score (totalPoints).

        Validates: Requirements 4.2
        """
        from handler import lambda_handler

        # Arrange
        session_id_str = str(session_id)
        tenant_id_str = str(tenant_id)
        participant_id_str = str(participant_id)

        mock_validate_token.return_value = {
            "sub": "admin-id",
            "role": "tenant_admin",
            "tenantId": tenant_id_str,
        }

        # Mock session exists
        def mock_get_item_func(table, key):
            if key.get("sessionId") == session_id_str:
                return {
                    "sessionId": session_id_str,
                    "tenantId": tenant_id_str,
                    "status": "active",
                }
            elif key.get("participantId") == participant_id_str:
                return {
                    "participantId": participant_id_str,
                    "tenantId": tenant_id_str,
                    "name": name,
                    "avatar": avatar,
                }
            return None

        mock_get_item.side_effect = mock_get_item_func

        # Mock participation
        participations = [
            {
                "participationId": "participation-1",
                "participantId": participant_id_str,
                "sessionId": session_id_str,
                "tenantId": tenant_id_str,
                "joinedAt": "2024-01-01T00:00:00Z",
                "totalPoints": total_points,
                "correctAnswers": correct_answers,
            }
        ]

        mock_query.return_value = participations

        event = {
            "headers": {"Authorization": "Bearer valid-token"},
            "pathParameters": {"sessionId": session_id_str},
        }
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 200
        body = json.loads(response["body"])

        # Verify participant has all required fields
        assert len(body["participants"]) == 1
        participant = body["participants"][0]

        assert "name" in participant
        assert participant["name"] == name

        assert "avatar" in participant
        assert participant["avatar"] == avatar

        assert "totalPoints" in participant
        assert participant["totalPoints"] == total_points

        assert "correctAnswers" in participant
        assert participant["correctAnswers"] == correct_answers

        assert "participantId" in participant
        assert participant["participantId"] == participant_id_str

    @settings(max_examples=100, deadline=None)
    @given(
        session_id=st.uuids(),
        tenant_id=st.uuids(),
        participant_id=st.uuids(),
        original_name=st.text(min_size=1, max_size=100),
        updated_name=st.text(min_size=1, max_size=100),
        original_avatar=st.sampled_from(["😀", "😎"]),
        updated_avatar=st.sampled_from(["🤓", "🥳"]),
    )
    @patch("handler.get_item")
    @patch("handler.query")
    @patch("handler.validate_token")
    def test_property_15_participant_list_reflects_current_profile(
        self,
        mock_validate_token,
        mock_query,
        mock_get_item,
        session_id,
        tenant_id,
        participant_id,
        original_name,
        updated_name,
        original_avatar,
        updated_avatar,
    ):
        """
        Feature: global-participant-registration, Property 15: Participant list reflects current profile

        For any participant who updates their global profile, subsequent queries to session
        participant lists should show the updated name and avatar.

        Validates: Requirements 4.3, 4.5
        """
        from handler import lambda_handler

        # Arrange
        session_id_str = str(session_id)
        tenant_id_str = str(tenant_id)
        participant_id_str = str(participant_id)

        mock_validate_token.return_value = {
            "sub": "admin-id",
            "role": "tenant_admin",
            "tenantId": tenant_id_str,
        }

        # Mock participation (doesn't change)
        participations = [
            {
                "participationId": "participation-1",
                "participantId": participant_id_str,
                "sessionId": session_id_str,
                "tenantId": tenant_id_str,
                "joinedAt": "2024-01-01T00:00:00Z",
                "totalPoints": 50,
                "correctAnswers": 5,
            }
        ]

        mock_query.return_value = participations

        # First call - original profile
        def mock_get_item_original(table, key):
            if key.get("sessionId") == session_id_str:
                return {
                    "sessionId": session_id_str,
                    "tenantId": tenant_id_str,
                    "status": "active",
                }
            elif key.get("participantId") == participant_id_str:
                return {
                    "participantId": participant_id_str,
                    "tenantId": tenant_id_str,
                    "name": original_name,
                    "avatar": original_avatar,
                }
            return None

        mock_get_item.side_effect = mock_get_item_original

        event = {
            "headers": {"Authorization": "Bearer valid-token"},
            "pathParameters": {"sessionId": session_id_str},
        }
        context = {}

        # Act - First call with original profile
        response1 = lambda_handler(event, context)

        # Assert - Original profile
        assert response1["statusCode"] == 200
        body1 = json.loads(response1["body"])
        participant1 = body1["participants"][0]
        assert participant1["name"] == original_name
        assert participant1["avatar"] == original_avatar

        # Simulate profile update - change mock to return updated profile
        def mock_get_item_updated(table, key):
            if key.get("sessionId") == session_id_str:
                return {
                    "sessionId": session_id_str,
                    "tenantId": tenant_id_str,
                    "status": "active",
                }
            elif key.get("participantId") == participant_id_str:
                return {
                    "participantId": participant_id_str,
                    "tenantId": tenant_id_str,
                    "name": updated_name,
                    "avatar": updated_avatar,
                }
            return None

        mock_get_item.side_effect = mock_get_item_updated

        # Act - Second call with updated profile
        response2 = lambda_handler(event, context)

        # Assert - Updated profile is reflected
        assert response2["statusCode"] == 200
        body2 = json.loads(response2["body"])
        participant2 = body2["participants"][0]
        assert participant2["name"] == updated_name
        assert participant2["avatar"] == updated_avatar

    @settings(max_examples=100, deadline=None)
    @given(
        session_id=st.uuids(),
        session_tenant_id=st.uuids(),
        admin_tenant_id=st.uuids(),
    )
    @patch("handler.get_item")
    @patch("handler.validate_token")
    def test_property_36_participant_list_tenant_filtering(
        self,
        mock_validate_token,
        mock_get_item,
        session_id,
        session_tenant_id,
        admin_tenant_id,
    ):
        """
        Feature: global-participant-registration, Property 36: Participant list tenant filtering

        For any session participant list, all participants should have the same tenantId as the session.

        Validates: Requirements 11.4
        """
        from handler import lambda_handler

        # Arrange - Ensure tenant IDs are different
        session_tenant_id_str = str(session_tenant_id)
        admin_tenant_id_str = str(admin_tenant_id)

        # Skip test if UUIDs happen to be the same
        if session_tenant_id_str == admin_tenant_id_str:
            return

        session_id_str = str(session_id)

        # Mock admin authentication with different tenant
        mock_validate_token.return_value = {
            "sub": "admin-id",
            "role": "tenant_admin",
            "tenantId": admin_tenant_id_str,
        }

        # Mock session exists with different tenant
        mock_get_item.return_value = {
            "sessionId": session_id_str,
            "tenantId": session_tenant_id_str,
            "status": "active",
        }

        event = {
            "headers": {"Authorization": "Bearer valid-token"},
            "pathParameters": {"sessionId": session_id_str},
        }
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert - Should be denied with 403 Forbidden
        assert response["statusCode"] == 403
        body = json.loads(response["body"])
        assert body["error"]["code"] == "CROSS_TENANT_ACCESS"

    @settings(max_examples=100, deadline=None)
    @given(
        session_id=st.uuids(),
        tenant_id=st.uuids(),
    )
    @patch("handler.get_item")
    @patch("handler.validate_token")
    def test_session_not_found_rejection(
        self,
        mock_validate_token,
        mock_get_item,
        session_id,
        tenant_id,
    ):
        """
        Verify that getting participants for a non-existent session is rejected.
        """
        from handler import lambda_handler

        # Arrange
        session_id_str = str(session_id)
        tenant_id_str = str(tenant_id)

        mock_validate_token.return_value = {
            "sub": "admin-id",
            "role": "tenant_admin",
            "tenantId": tenant_id_str,
        }

        # Mock session doesn't exist
        mock_get_item.return_value = None

        event = {
            "headers": {"Authorization": "Bearer valid-token"},
            "pathParameters": {"sessionId": session_id_str},
        }
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert body["error"]["code"] == "SESSION_NOT_FOUND"

    @settings(max_examples=100, deadline=None)
    @given(
        session_id=st.uuids(),
    )
    def test_missing_authentication_rejection(self, session_id):
        """
        Verify that getting participants without authentication is rejected.
        """
        from handler import lambda_handler

        # Arrange
        session_id_str = str(session_id)

        event = {
            "headers": {},  # No Authorization header
            "pathParameters": {"sessionId": session_id_str},
        }
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 401
        body = json.loads(response["body"])
        assert body["error"]["code"] == "MISSING_TOKEN"

    @settings(max_examples=100, deadline=None)
    @given(
        session_id=st.uuids(),
    )
    @patch("handler.validate_token")
    def test_insufficient_permissions_rejection(self, mock_validate_token, session_id):
        """
        Verify that getting participants with non-admin role is rejected.
        """
        from handler import lambda_handler

        # Arrange
        session_id_str = str(session_id)

        # Mock participant authentication (not admin)
        mock_validate_token.return_value = {
            "sub": "participant-id",
            "role": "participant",
            "tenantId": "tenant-id",
        }

        event = {
            "headers": {"Authorization": "Bearer valid-token"},
            "pathParameters": {"sessionId": session_id_str},
        }
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 403
        body = json.loads(response["body"])
        assert body["error"]["code"] == "INSUFFICIENT_PERMISSIONS"
