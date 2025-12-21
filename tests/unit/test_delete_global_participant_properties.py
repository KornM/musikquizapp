"""
Property-Based Tests for Global Participant Deletion

Tests cover:
- Property 44: Participant deletion cascades

These tests use Hypothesis for property-based testing to verify universal properties
about global participant deletion and cascade behavior.
"""

import json
import os
from unittest.mock import MagicMock, patch
from hypothesis import given, settings, strategies as st
import pytest
import sys

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "lambda"))

from delete_global_participant.handler import lambda_handler


class TestProperty44ParticipantDeletionCascades:
    """
    Property 44: Participant deletion cascades

    For any global participant deletion, all associated SessionParticipation
    records should be deleted or marked as inactive.
    """

    @settings(max_examples=100)
    @given(
        participant_id=st.uuids(),
        tenant_id=st.uuids(),
        num_sessions=st.integers(min_value=1, max_value=10),
    )
    @patch.dict(
        os.environ,
        {
            "GLOBAL_PARTICIPANTS_TABLE": "TestGlobalParticipants",
            "SESSION_PARTICIPATIONS_TABLE": "TestSessionParticipations",
            "JWT_SECRET": "test-secret-key",
        },
    )
    def test_property_44_deletion_cascades_to_participations(
        self, participant_id, tenant_id, num_sessions
    ):
        """
        Feature: global-participant-registration, Property 44: Participant deletion cascades

        For any global participant deletion, all associated SessionParticipation
        records should be deleted.
        """
        from auth import generate_token

        participant_id_str = str(participant_id)
        tenant_id_str = str(tenant_id)

        # Generate a valid token for the participant
        token = generate_token(participant_id_str, "participant", tenant_id_str)

        participant_record = {
            "participantId": participant_id_str,
            "tenantId": tenant_id_str,
            "name": "Test Participant",
            "avatar": "😀",
            "createdAt": "2024-01-01T00:00:00Z",
        }

        # Create multiple session participation records
        participation_records = []
        for i in range(num_sessions):
            participation_records.append(
                {
                    "participationId": f"participation-{i}",
                    "participantId": participant_id_str,
                    "sessionId": f"session-{i}",
                    "tenantId": tenant_id_str,
                    "joinedAt": "2024-01-01T00:00:00Z",
                    "totalPoints": 0,
                    "correctAnswers": 0,
                }
            )

        with (
            patch("delete_global_participant.handler.get_item") as mock_get,
            patch("delete_global_participant.handler.query") as mock_query,
            patch("delete_global_participant.handler.delete_item") as mock_delete,
        ):
            # Participant exists
            mock_get.return_value = participant_record

            # Return all participation records
            mock_query.return_value = participation_records

            event = {
                "pathParameters": {"participantId": participant_id_str},
                "headers": {"Authorization": f"Bearer {token}"},
            }

            response = lambda_handler(event, {})

            # Verify deletion was successful
            assert response["statusCode"] == 200
            response_body = json.loads(response["body"])

            # Verify all participations were deleted
            assert response_body["deletedParticipations"] == num_sessions

            # Verify delete_item was called for each participation + the participant
            assert mock_delete.call_count == num_sessions + 1

            # Verify the participant itself was deleted
            participant_delete_calls = [
                call
                for call in mock_delete.call_args_list
                if call[0][1] == {"participantId": participant_id_str}
            ]
            assert len(participant_delete_calls) == 1

    @settings(max_examples=100)
    @given(
        participant_id=st.uuids(),
        tenant_id=st.uuids(),
    )
    @patch.dict(
        os.environ,
        {
            "GLOBAL_PARTICIPANTS_TABLE": "TestGlobalParticipants",
            "SESSION_PARTICIPATIONS_TABLE": "TestSessionParticipations",
            "JWT_SECRET": "test-secret-key",
        },
    )
    def test_property_44_deletion_with_no_participations(
        self, participant_id, tenant_id
    ):
        """
        Feature: global-participant-registration, Property 44: Participant deletion cascades

        For any global participant with no session participations, deletion
        should still succeed.
        """
        from auth import generate_token

        participant_id_str = str(participant_id)
        tenant_id_str = str(tenant_id)

        token = generate_token(participant_id_str, "participant", tenant_id_str)

        participant_record = {
            "participantId": participant_id_str,
            "tenantId": tenant_id_str,
            "name": "Test Participant",
            "avatar": "😀",
            "createdAt": "2024-01-01T00:00:00Z",
        }

        with (
            patch("delete_global_participant.handler.get_item") as mock_get,
            patch("delete_global_participant.handler.query") as mock_query,
            patch("delete_global_participant.handler.delete_item") as mock_delete,
        ):
            mock_get.return_value = participant_record
            mock_query.return_value = []  # No participations

            event = {
                "pathParameters": {"participantId": participant_id_str},
                "headers": {"Authorization": f"Bearer {token}"},
            }

            response = lambda_handler(event, {})

            # Verify deletion was successful
            assert response["statusCode"] == 200
            response_body = json.loads(response["body"])
            assert response_body["deletedParticipations"] == 0

            # Verify participant was still deleted
            mock_delete.assert_called_once_with(
                "TestGlobalParticipants", {"participantId": participant_id_str}
            )

    @settings(max_examples=100)
    @given(
        participant_id=st.uuids(),
        tenant_id=st.uuids(),
        other_participant_id=st.uuids(),
    )
    @patch.dict(
        os.environ,
        {
            "GLOBAL_PARTICIPANTS_TABLE": "TestGlobalParticipants",
            "SESSION_PARTICIPATIONS_TABLE": "TestSessionParticipations",
            "JWT_SECRET": "test-secret-key",
        },
    )
    def test_property_44_cannot_delete_other_participant(
        self, participant_id, tenant_id, other_participant_id
    ):
        """
        Feature: global-participant-registration, Property 44: Participant deletion cascades

        For any participant attempting to delete another participant's account,
        the system should deny access.
        """
        from auth import generate_token

        # Ensure the IDs are different
        if participant_id == other_participant_id:
            return

        participant_id_str = str(participant_id)
        other_participant_id_str = str(other_participant_id)
        tenant_id_str = str(tenant_id)

        # Token is for participant_id, but trying to delete other_participant_id
        token = generate_token(participant_id_str, "participant", tenant_id_str)

        event = {
            "pathParameters": {"participantId": other_participant_id_str},
            "headers": {"Authorization": f"Bearer {token}"},
        }

        response = lambda_handler(event, {})

        # Verify access is denied
        assert response["statusCode"] == 403
        response_body = json.loads(response["body"])
        assert response_body["error"]["code"] == "UNAUTHORIZED_ACCESS"

    @settings(max_examples=100)
    @given(
        participant_id=st.uuids(),
    )
    @patch.dict(
        os.environ,
        {
            "GLOBAL_PARTICIPANTS_TABLE": "TestGlobalParticipants",
            "SESSION_PARTICIPATIONS_TABLE": "TestSessionParticipations",
            "JWT_SECRET": "test-secret-key",
        },
    )
    def test_property_44_nonexistent_participant_deletion_fails(self, participant_id):
        """
        Feature: global-participant-registration, Property 44: Participant deletion cascades

        For any participant ID that doesn't exist, deletion attempts should
        fail with 404.
        """
        from auth import generate_token

        participant_id_str = str(participant_id)
        token = generate_token(participant_id_str, "participant", "tenant-123")

        with patch("delete_global_participant.handler.get_item") as mock_get:
            # Participant doesn't exist
            mock_get.return_value = None

            event = {
                "pathParameters": {"participantId": participant_id_str},
                "headers": {"Authorization": f"Bearer {token}"},
            }

            response = lambda_handler(event, {})

            # Verify deletion fails
            assert response["statusCode"] == 404
            response_body = json.loads(response["body"])
            assert response_body["error"]["code"] == "PARTICIPANT_NOT_FOUND"

    @settings(max_examples=100)
    @given(
        participant_id=st.uuids(),
        tenant_id=st.uuids(),
        num_sessions=st.integers(min_value=2, max_value=5),
    )
    @patch.dict(
        os.environ,
        {
            "GLOBAL_PARTICIPANTS_TABLE": "TestGlobalParticipants",
            "SESSION_PARTICIPATIONS_TABLE": "TestSessionParticipations",
            "JWT_SECRET": "test-secret-key",
        },
    )
    def test_property_44_all_participations_deleted(
        self, participant_id, tenant_id, num_sessions
    ):
        """
        Feature: global-participant-registration, Property 44: Participant deletion cascades

        For any global participant with multiple session participations,
        all participations should be deleted when the participant is deleted.
        """
        from auth import generate_token

        participant_id_str = str(participant_id)
        tenant_id_str = str(tenant_id)

        token = generate_token(participant_id_str, "participant", tenant_id_str)

        participant_record = {
            "participantId": participant_id_str,
            "tenantId": tenant_id_str,
            "name": "Test Participant",
            "avatar": "😀",
            "createdAt": "2024-01-01T00:00:00Z",
        }

        # Create participation records for different sessions
        participation_records = []
        participation_ids = set()
        for i in range(num_sessions):
            participation_id = f"participation-{participant_id_str}-{i}"
            participation_ids.add(participation_id)
            participation_records.append(
                {
                    "participationId": participation_id,
                    "participantId": participant_id_str,
                    "sessionId": f"session-{i}",
                    "tenantId": tenant_id_str,
                    "joinedAt": "2024-01-01T00:00:00Z",
                    "totalPoints": i * 10,
                    "correctAnswers": i,
                }
            )

        with (
            patch("delete_global_participant.handler.get_item") as mock_get,
            patch("delete_global_participant.handler.query") as mock_query,
            patch("delete_global_participant.handler.delete_item") as mock_delete,
        ):
            mock_get.return_value = participant_record
            mock_query.return_value = participation_records

            event = {
                "pathParameters": {"participantId": participant_id_str},
                "headers": {"Authorization": f"Bearer {token}"},
            }

            response = lambda_handler(event, {})

            # Verify success
            assert response["statusCode"] == 200
            response_body = json.loads(response["body"])
            assert response_body["deletedParticipations"] == num_sessions

            # Verify all participation IDs were deleted
            deleted_participation_ids = set()
            for call in mock_delete.call_args_list:
                if "participationId" in call[0][1]:
                    deleted_participation_ids.add(call[0][1]["participationId"])

            assert deleted_participation_ids == participation_ids

    @patch.dict(
        os.environ,
        {
            "GLOBAL_PARTICIPANTS_TABLE": "TestGlobalParticipants",
            "SESSION_PARTICIPATIONS_TABLE": "TestSessionParticipations",
            "JWT_SECRET": "test-secret-key",
        },
    )
    def test_property_44_missing_participant_id_in_path(self):
        """
        Feature: global-participant-registration, Property 44: Participant deletion cascades

        For any deletion request without a participant ID, the system should
        reject it.
        """
        from auth import generate_token

        token = generate_token("participant-123", "participant", "tenant-123")

        event = {"pathParameters": {}, "headers": {"Authorization": f"Bearer {token}"}}

        response = lambda_handler(event, {})

        assert response["statusCode"] == 400
        response_body = json.loads(response["body"])
        assert response_body["error"]["code"] == "MISSING_FIELDS"

    @patch.dict(
        os.environ,
        {
            "GLOBAL_PARTICIPANTS_TABLE": "TestGlobalParticipants",
            "SESSION_PARTICIPATIONS_TABLE": "TestSessionParticipations",
            "JWT_SECRET": "test-secret-key",
        },
    )
    def test_property_44_missing_authorization_token(self):
        """
        Feature: global-participant-registration, Property 44: Participant deletion cascades

        For any deletion request without an authorization token, the system
        should reject it.
        """
        event = {"pathParameters": {"participantId": "participant-123"}, "headers": {}}

        response = lambda_handler(event, {})

        assert response["statusCode"] == 401
        response_body = json.loads(response["body"])
        assert response_body["error"]["code"] == "MISSING_TOKEN"
