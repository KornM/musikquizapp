"""
Property-Based Tests for Join Session Lambda Handler

Tests cover:
- Property 9: Auto-creation of session participation
- Property 10: Participation record linkage
- Property 11: Initial score is zero
- Property 12: Join timestamp recording
- Property 35: Cross-tenant session join denial

These tests use Hypothesis for property-based testing to verify universal properties
across many randomly generated inputs.

Validates: Requirements 3.1, 3.2, 3.3, 3.4, 11.2, 11.3
"""

import json
import pytest
from hypothesis import given, settings, strategies as st
from unittest.mock import patch, MagicMock
import sys
import os
from datetime import datetime

# Add lambda directories to path
lambda_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "lambda")
)
sys.path.insert(0, os.path.join(lambda_path, "join_session"))
sys.path.insert(0, os.path.join(lambda_path, "common"))


class TestJoinSessionProperties:
    """Property-based tests for session joining"""

    @settings(max_examples=100, deadline=None)
    @given(
        participant_id=st.uuids(),
        session_id=st.uuids(),
        tenant_id=st.uuids(),
        name=st.text(min_size=1, max_size=100),
    )
    @patch("handler.put_item")
    @patch("handler.query")
    @patch("handler.get_item")
    @patch("handler.require_participant_auth")
    def test_property_9_auto_creation_of_session_participation(
        self,
        mock_require_auth,
        mock_get_item,
        mock_query,
        mock_put_item,
        participant_id,
        session_id,
        tenant_id,
        name,
    ):
        """
        Feature: global-participant-registration, Property 9: Auto-creation of session participation

        For any global participant joining any session, the system should automatically create
        a session participation record linking the participant ID and session ID.

        Validates: Requirements 3.1
        """
        from handler import lambda_handler

        # Arrange
        participant_id_str = str(participant_id)
        session_id_str = str(session_id)
        tenant_id_str = str(tenant_id)

        # Mock participant authentication
        mock_require_auth.return_value = (
            {
                "participantId": participant_id_str,
                "tenantId": tenant_id_str,
                "role": "participant",
                "participant": {
                    "participantId": participant_id_str,
                    "tenantId": tenant_id_str,
                    "name": name,
                },
            },
            None,
        )

        # Mock session exists with matching tenant
        mock_get_item.return_value = {
            "sessionId": session_id_str,
            "tenantId": tenant_id_str,
            "status": "active",
        }

        # Mock no existing participation
        mock_query.return_value = []

        mock_put_item.return_value = {}

        event = {"pathParameters": {"sessionId": session_id_str}}
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 201
        body = json.loads(response["body"])

        # Verify participation record was created
        assert mock_put_item.called
        call_args = mock_put_item.call_args
        stored_participation = call_args[0][1]  # Second argument is the item

        # Verify it's a SessionParticipation record
        assert "participationId" in stored_participation
        assert "participantId" in stored_participation
        assert "sessionId" in stored_participation

    @settings(max_examples=100, deadline=None)
    @given(
        participant_id=st.uuids(),
        session_id=st.uuids(),
        tenant_id=st.uuids(),
        name=st.text(min_size=1, max_size=100),
    )
    @patch("handler.put_item")
    @patch("handler.query")
    @patch("handler.get_item")
    @patch("handler.require_participant_auth")
    def test_property_10_participation_record_linkage(
        self,
        mock_require_auth,
        mock_get_item,
        mock_query,
        mock_put_item,
        participant_id,
        session_id,
        tenant_id,
        name,
    ):
        """
        Feature: global-participant-registration, Property 10: Participation record linkage

        For any session participation record, it should contain both a valid participantId
        (referencing GlobalParticipants) and a valid sessionId (referencing QuizSessions).

        Validates: Requirements 3.2
        """
        from handler import lambda_handler

        # Arrange
        participant_id_str = str(participant_id)
        session_id_str = str(session_id)
        tenant_id_str = str(tenant_id)

        mock_require_auth.return_value = (
            {
                "participantId": participant_id_str,
                "tenantId": tenant_id_str,
                "role": "participant",
                "participant": {
                    "participantId": participant_id_str,
                    "tenantId": tenant_id_str,
                    "name": name,
                },
            },
            None,
        )

        mock_get_item.return_value = {
            "sessionId": session_id_str,
            "tenantId": tenant_id_str,
            "status": "active",
        }

        mock_query.return_value = []
        mock_put_item.return_value = {}

        event = {"pathParameters": {"sessionId": session_id_str}}
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 201
        body = json.loads(response["body"])

        # Verify participation record contains both IDs
        assert "participantId" in body
        assert "sessionId" in body
        assert body["participantId"] == participant_id_str
        assert body["sessionId"] == session_id_str

        # Verify put_item was called with correct linkage
        assert mock_put_item.called
        call_args = mock_put_item.call_args
        stored_participation = call_args[0][1]

        assert stored_participation["participantId"] == participant_id_str
        assert stored_participation["sessionId"] == session_id_str

    @settings(max_examples=100, deadline=None)
    @given(
        participant_id=st.uuids(),
        session_id=st.uuids(),
        tenant_id=st.uuids(),
        name=st.text(min_size=1, max_size=100),
    )
    @patch("handler.put_item")
    @patch("handler.query")
    @patch("handler.get_item")
    @patch("handler.require_participant_auth")
    def test_property_11_initial_score_is_zero(
        self,
        mock_require_auth,
        mock_get_item,
        mock_query,
        mock_put_item,
        participant_id,
        session_id,
        tenant_id,
        name,
    ):
        """
        Feature: global-participant-registration, Property 11: Initial score is zero

        For any new session participation created, the totalPoints field should be initialized to 0.

        Validates: Requirements 3.3
        """
        from handler import lambda_handler

        # Arrange
        participant_id_str = str(participant_id)
        session_id_str = str(session_id)
        tenant_id_str = str(tenant_id)

        mock_require_auth.return_value = (
            {
                "participantId": participant_id_str,
                "tenantId": tenant_id_str,
                "role": "participant",
                "participant": {
                    "participantId": participant_id_str,
                    "tenantId": tenant_id_str,
                    "name": name,
                },
            },
            None,
        )

        mock_get_item.return_value = {
            "sessionId": session_id_str,
            "tenantId": tenant_id_str,
            "status": "active",
        }

        mock_query.return_value = []
        mock_put_item.return_value = {}

        event = {"pathParameters": {"sessionId": session_id_str}}
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 201
        body = json.loads(response["body"])

        # Verify totalPoints is 0
        assert "totalPoints" in body
        assert body["totalPoints"] == 0

        # Verify correctAnswers is also 0
        assert "correctAnswers" in body
        assert body["correctAnswers"] == 0

        # Verify put_item was called with totalPoints=0
        assert mock_put_item.called
        call_args = mock_put_item.call_args
        stored_participation = call_args[0][1]

        assert stored_participation["totalPoints"] == 0
        assert stored_participation["correctAnswers"] == 0

    @settings(max_examples=100, deadline=None)
    @given(
        participant_id=st.uuids(),
        session_id=st.uuids(),
        tenant_id=st.uuids(),
        name=st.text(min_size=1, max_size=100),
    )
    @patch("handler.put_item")
    @patch("handler.query")
    @patch("handler.get_item")
    @patch("handler.require_participant_auth")
    def test_property_12_join_timestamp_recording(
        self,
        mock_require_auth,
        mock_get_item,
        mock_query,
        mock_put_item,
        participant_id,
        session_id,
        tenant_id,
        name,
    ):
        """
        Feature: global-participant-registration, Property 12: Join timestamp recording

        For any session participation created, the joinedAt field should contain a valid
        timestamp representing when the participant joined.

        Validates: Requirements 3.4
        """
        from handler import lambda_handler

        # Arrange
        participant_id_str = str(participant_id)
        session_id_str = str(session_id)
        tenant_id_str = str(tenant_id)

        mock_require_auth.return_value = (
            {
                "participantId": participant_id_str,
                "tenantId": tenant_id_str,
                "role": "participant",
                "participant": {
                    "participantId": participant_id_str,
                    "tenantId": tenant_id_str,
                    "name": name,
                },
            },
            None,
        )

        mock_get_item.return_value = {
            "sessionId": session_id_str,
            "tenantId": tenant_id_str,
            "status": "active",
        }

        mock_query.return_value = []
        mock_put_item.return_value = {}

        event = {"pathParameters": {"sessionId": session_id_str}}
        context = {}

        # Act
        before_join = datetime.utcnow()
        response = lambda_handler(event, context)
        after_join = datetime.utcnow()

        # Assert
        assert response["statusCode"] == 201
        body = json.loads(response["body"])

        # Verify joinedAt is present
        assert "joinedAt" in body
        assert body["joinedAt"] is not None

        # Verify joinedAt is a valid ISO timestamp
        try:
            joined_at = datetime.fromisoformat(body["joinedAt"].replace("Z", "+00:00"))
        except ValueError:
            pytest.fail(f"joinedAt '{body['joinedAt']}' is not a valid ISO timestamp")

        # Verify timestamp is reasonable (between before and after the call)
        # Allow some tolerance for test execution time
        assert (
            before_join <= joined_at <= after_join
            or (after_join - joined_at).total_seconds() < 1
        )

        # Verify put_item was called with joinedAt
        assert mock_put_item.called
        call_args = mock_put_item.call_args
        stored_participation = call_args[0][1]

        assert "joinedAt" in stored_participation
        assert stored_participation["joinedAt"] is not None

    @settings(max_examples=100, deadline=None)
    @given(
        participant_id=st.uuids(),
        session_id=st.uuids(),
        participant_tenant_id=st.uuids(),
        session_tenant_id=st.uuids(),
        name=st.text(min_size=1, max_size=100),
    )
    @patch("handler.get_item")
    @patch("handler.require_participant_auth")
    def test_property_35_cross_tenant_session_join_denial(
        self,
        mock_require_auth,
        mock_get_item,
        participant_id,
        session_id,
        participant_tenant_id,
        session_tenant_id,
        name,
    ):
        """
        Feature: global-participant-registration, Property 35: Cross-tenant session join denial

        For any participant attempting to join a session where the session's tenantId differs
        from the participant's tenantId, the system should deny access.

        Validates: Requirements 11.2, 11.3
        """
        from handler import lambda_handler

        # Arrange - Ensure tenant IDs are different
        participant_tenant_id_str = str(participant_tenant_id)
        session_tenant_id_str = str(session_tenant_id)

        # Skip test if UUIDs happen to be the same
        if participant_tenant_id_str == session_tenant_id_str:
            return

        participant_id_str = str(participant_id)
        session_id_str = str(session_id)

        # Mock participant authentication with one tenant
        mock_require_auth.return_value = (
            {
                "participantId": participant_id_str,
                "tenantId": participant_tenant_id_str,
                "role": "participant",
                "participant": {
                    "participantId": participant_id_str,
                    "tenantId": participant_tenant_id_str,
                    "name": name,
                },
            },
            None,
        )

        # Mock session exists with different tenant
        mock_get_item.return_value = {
            "sessionId": session_id_str,
            "tenantId": session_tenant_id_str,
            "status": "active",
        }

        event = {"pathParameters": {"sessionId": session_id_str}}
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert - Should be denied with 403 Forbidden
        assert response["statusCode"] == 403
        body = json.loads(response["body"])
        assert body["error"]["code"] == "CROSS_TENANT_ACCESS"

    @settings(max_examples=100, deadline=None)
    @given(
        participant_id=st.uuids(),
        session_id=st.uuids(),
        tenant_id=st.uuids(),
        name=st.text(min_size=1, max_size=100),
    )
    @patch("handler.query")
    @patch("handler.get_item")
    @patch("handler.require_participant_auth")
    def test_idempotent_join_returns_existing_participation(
        self,
        mock_require_auth,
        mock_get_item,
        mock_query,
        participant_id,
        session_id,
        tenant_id,
        name,
    ):
        """
        Verify that joining a session multiple times returns the existing participation
        record (idempotent operation).
        """
        from handler import lambda_handler

        # Arrange
        participant_id_str = str(participant_id)
        session_id_str = str(session_id)
        tenant_id_str = str(tenant_id)
        participation_id_str = str(st.uuids().example())

        mock_require_auth.return_value = (
            {
                "participantId": participant_id_str,
                "tenantId": tenant_id_str,
                "role": "participant",
                "participant": {
                    "participantId": participant_id_str,
                    "tenantId": tenant_id_str,
                    "name": name,
                },
            },
            None,
        )

        mock_get_item.return_value = {
            "sessionId": session_id_str,
            "tenantId": tenant_id_str,
            "status": "active",
        }

        # Mock existing participation
        existing_participation = {
            "participationId": participation_id_str,
            "participantId": participant_id_str,
            "sessionId": session_id_str,
            "tenantId": tenant_id_str,
            "joinedAt": "2024-01-01T00:00:00Z",
            "totalPoints": 0,
            "correctAnswers": 0,
        }
        mock_query.return_value = [existing_participation]

        event = {"pathParameters": {"sessionId": session_id_str}}
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert - Should return 200 (not 201) with existing participation
        assert response["statusCode"] == 200
        body = json.loads(response["body"])

        # Verify it returns the existing participation
        assert body["participationId"] == participation_id_str
        assert body["participantId"] == participant_id_str
        assert body["sessionId"] == session_id_str

    @settings(max_examples=100, deadline=None)
    @given(
        participant_id=st.uuids(),
        session_id=st.uuids(),
        tenant_id=st.uuids(),
        name=st.text(min_size=1, max_size=100),
    )
    @patch("handler.get_item")
    @patch("handler.require_participant_auth")
    def test_session_not_found_rejection(
        self,
        mock_require_auth,
        mock_get_item,
        participant_id,
        session_id,
        tenant_id,
        name,
    ):
        """
        Verify that joining a non-existent session is rejected.
        """
        from handler import lambda_handler

        # Arrange
        participant_id_str = str(participant_id)
        session_id_str = str(session_id)
        tenant_id_str = str(tenant_id)

        mock_require_auth.return_value = (
            {
                "participantId": participant_id_str,
                "tenantId": tenant_id_str,
                "role": "participant",
                "participant": {
                    "participantId": participant_id_str,
                    "tenantId": tenant_id_str,
                    "name": name,
                },
            },
            None,
        )

        # Mock session doesn't exist
        mock_get_item.return_value = None

        event = {"pathParameters": {"sessionId": session_id_str}}
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
        Verify that joining without authentication is rejected.
        """
        from handler import lambda_handler

        # Arrange
        session_id_str = str(session_id)

        # Mock authentication failure
        with patch("handler.require_participant_auth") as mock_require_auth:
            mock_require_auth.return_value = (
                None,
                {
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
                },
            )

            event = {"pathParameters": {"sessionId": session_id_str}}
            context = {}

            # Act
            response = lambda_handler(event, context)

            # Assert
            assert response["statusCode"] == 401
            body = json.loads(response["body"])
            assert body["error"]["code"] == "MISSING_TOKEN"
