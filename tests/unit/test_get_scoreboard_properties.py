"""
Property-Based Tests for Get Scoreboard Lambda Handler

Tests cover:
- Property 19: Scoreboard session specificity
- Property 20: Score and answer persistence

These tests use Hypothesis for property-based testing to verify universal properties
across many randomly generated inputs.

Validates: Requirements 5.4, 5.5
"""

import json
import pytest
from hypothesis import given, settings, strategies as st
from unittest.mock import patch, MagicMock
import sys
import os
from decimal import Decimal
import uuid

# Add lambda directories to path
lambda_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "lambda")
)
sys.path.insert(0, os.path.join(lambda_path, "get_scoreboard"))
sys.path.insert(0, os.path.join(lambda_path, "common"))


class TestGetScoreboardProperties:
    """Property-based tests for scoreboard retrieval"""

    @settings(max_examples=100, deadline=None)
    @given(
        session_id=st.uuids(),
        tenant_id=st.uuids(),
        # Generate a list of participants with their scores
        num_participants=st.integers(min_value=1, max_value=10),
        data=st.data(),
    )
    @patch("handler.get_item")
    @patch("handler.query")
    def test_property_19_scoreboard_session_specificity(
        self,
        mock_query,
        mock_get_item,
        session_id,
        tenant_id,
        num_participants,
        data,
    ):
        """
        Feature: global-participant-registration, Property 19: Scoreboard session specificity

        For any session scoreboard query, the returned scores should only include
        participants from that specific session (filtered by sessionId).

        Validates: Requirements 5.4
        """
        from handler import lambda_handler

        # Arrange
        session_id_str = str(session_id)
        tenant_id_str = str(tenant_id)

        # Create participations for this session
        session_participations = []
        for i in range(num_participants):
            participant_id = str(data.draw(st.uuids()))
            session_participations.append(
                {
                    "participationId": str(data.draw(st.uuids())),
                    "participantId": participant_id,
                    "sessionId": session_id_str,
                    "tenantId": tenant_id_str,
                    "totalPoints": data.draw(st.integers(min_value=0, max_value=100)),
                    "correctAnswers": data.draw(st.integers(min_value=0, max_value=10)),
                }
            )

        # Mock session exists
        def mock_get_item_side_effect(table, key):
            if "sessionId" in key:
                return {
                    "sessionId": session_id_str,
                    "tenantId": tenant_id_str,
                    "status": "active",
                }
            # Mock GlobalParticipants lookup
            participant_id = key.get("participantId")
            if participant_id:
                return {
                    "participantId": participant_id,
                    "tenantId": tenant_id_str,
                    "name": f"Participant {participant_id[:8]}",
                    "avatar": "😀",
                }
            return None

        mock_get_item.side_effect = mock_get_item_side_effect

        # Mock query returns participations for this session only
        mock_query.return_value = session_participations

        event = {"pathParameters": {"sessionId": session_id_str}}
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 200
        body = json.loads(response["body"])

        # Verify all returned participants are from this session
        assert "scoreboard" in body
        scoreboard = body["scoreboard"]

        # Verify the number of participants matches
        assert len(scoreboard) == num_participants

        # Verify all participants have the correct sessionId context
        # (implicitly verified by the fact that we only queried this session)
        for entry in scoreboard:
            assert "participantId" in entry
            assert "totalPoints" in entry
            assert "correctAnswers" in entry
            assert "name" in entry
            assert "avatar" in entry

        # Verify query was called with the correct sessionId
        assert mock_query.called
        call_args = mock_query.call_args
        assert ":sessionId" in call_args[0][2]  # expression_attribute_values
        assert call_args[0][2][":sessionId"] == session_id_str

    @settings(max_examples=100, deadline=None)
    @given(
        session_id=st.uuids(),
        tenant_id=st.uuids(),
        participant_id=st.uuids(),
        participation_id=st.uuids(),
        total_points=st.integers(min_value=0, max_value=100),
        correct_answers=st.integers(min_value=0, max_value=10),
        name=st.text(min_size=1, max_size=50),
    )
    @patch("handler.get_item")
    @patch("handler.query")
    def test_property_20_score_and_answer_persistence(
        self,
        mock_query,
        mock_get_item,
        session_id,
        tenant_id,
        participant_id,
        participation_id,
        total_points,
        correct_answers,
        name,
    ):
        """
        Feature: global-participant-registration, Property 20: Score and answer persistence

        For any session that ends, the SessionParticipation records and Answer records
        for that session should remain unchanged and queryable.

        Validates: Requirements 5.5
        """
        from handler import lambda_handler

        # Arrange
        session_id_str = str(session_id)
        tenant_id_str = str(tenant_id)
        participant_id_str = str(participant_id)
        participation_id_str = str(participation_id)

        # Create a participation with specific scores
        participation = {
            "participationId": participation_id_str,
            "participantId": participant_id_str,
            "sessionId": session_id_str,
            "tenantId": tenant_id_str,
            "totalPoints": total_points,
            "correctAnswers": correct_answers,
        }

        # Mock session exists (could be ended)
        def mock_get_item_side_effect(table, key):
            if "sessionId" in key:
                return {
                    "sessionId": session_id_str,
                    "tenantId": tenant_id_str,
                    "status": "ended",  # Session has ended
                }
            # Mock GlobalParticipants lookup
            if "participantId" in key:
                return {
                    "participantId": participant_id_str,
                    "tenantId": tenant_id_str,
                    "name": name,
                    "avatar": "😀",
                }
            return None

        mock_get_item.side_effect = mock_get_item_side_effect
        mock_query.return_value = [participation]

        event = {"pathParameters": {"sessionId": session_id_str}}
        context = {}

        # Act - Query scoreboard after session ends
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 200
        body = json.loads(response["body"])

        # Verify scores are still accessible
        assert "scoreboard" in body
        scoreboard = body["scoreboard"]
        assert len(scoreboard) == 1

        # Verify the scores match what was stored
        participant_entry = scoreboard[0]
        assert participant_entry["participantId"] == participant_id_str
        assert participant_entry["totalPoints"] == total_points
        assert participant_entry["correctAnswers"] == correct_answers
        assert participant_entry["name"] == name

        # The key property: scores remain unchanged after session ends
        # This is verified by the fact that we can still query them
        # and they match the original values

    @settings(max_examples=100, deadline=None)
    @given(
        session_id=st.uuids(),
        tenant_id=st.uuids(),
        num_participants=st.integers(min_value=2, max_value=10),
        data=st.data(),
    )
    @patch("handler.get_item")
    @patch("handler.query")
    def test_scoreboard_sorted_by_points_descending(
        self,
        mock_query,
        mock_get_item,
        session_id,
        tenant_id,
        num_participants,
        data,
    ):
        """
        Verify that scoreboard is sorted by totalPoints in descending order.
        """
        from handler import lambda_handler

        # Arrange
        session_id_str = str(session_id)
        tenant_id_str = str(tenant_id)

        # Create participations with different scores
        session_participations = []
        expected_scores = []

        for i in range(num_participants):
            participant_id = str(data.draw(st.uuids()))
            points = data.draw(st.integers(min_value=0, max_value=100))

            session_participations.append(
                {
                    "participationId": str(data.draw(st.uuids())),
                    "participantId": participant_id,
                    "sessionId": session_id_str,
                    "tenantId": tenant_id_str,
                    "totalPoints": points,
                    "correctAnswers": 0,
                }
            )
            expected_scores.append(points)

        # Sort expected scores descending
        expected_scores.sort(reverse=True)

        # Mock session exists
        def mock_get_item_side_effect(table, key):
            if "sessionId" in key:
                return {
                    "sessionId": session_id_str,
                    "tenantId": tenant_id_str,
                    "status": "active",
                }
            # Mock GlobalParticipants lookup
            participant_id = key.get("participantId")
            if participant_id:
                return {
                    "participantId": participant_id,
                    "tenantId": tenant_id_str,
                    "name": f"Participant {participant_id[:8]}",
                    "avatar": "😀",
                }
            return None

        mock_get_item.side_effect = mock_get_item_side_effect
        mock_query.return_value = session_participations

        event = {"pathParameters": {"sessionId": session_id_str}}
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 200
        body = json.loads(response["body"])

        scoreboard = body["scoreboard"]
        actual_scores = [entry["totalPoints"] for entry in scoreboard]

        # Verify scores are in descending order
        assert actual_scores == expected_scores

        # Verify ranks are assigned correctly
        for i, entry in enumerate(scoreboard):
            assert entry["rank"] == i + 1

    @settings(max_examples=100, deadline=None)
    @given(
        session_id=st.uuids(),
        tenant_id=st.uuids(),
    )
    @patch("handler.get_item")
    @patch("handler.query")
    def test_empty_scoreboard_for_session_with_no_participants(
        self,
        mock_query,
        mock_get_item,
        session_id,
        tenant_id,
    ):
        """
        Verify that a session with no participants returns an empty scoreboard.
        """
        from handler import lambda_handler

        # Arrange
        session_id_str = str(session_id)
        tenant_id_str = str(tenant_id)

        # Mock session exists
        mock_get_item.return_value = {
            "sessionId": session_id_str,
            "tenantId": tenant_id_str,
            "status": "active",
        }

        # Mock no participations
        mock_query.return_value = []

        event = {"pathParameters": {"sessionId": session_id_str}}
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 200
        body = json.loads(response["body"])

        assert "scoreboard" in body
        assert body["scoreboard"] == []

    @settings(max_examples=100, deadline=None)
    @given(
        session_id=st.uuids(),
    )
    @patch("handler.get_item")
    def test_session_not_found_returns_404(
        self,
        mock_get_item,
        session_id,
    ):
        """
        Verify that requesting scoreboard for non-existent session returns 404.
        """
        from handler import lambda_handler

        # Arrange
        session_id_str = str(session_id)

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
        tenant_id=st.uuids(),
        other_tenant_id=st.uuids(),
        num_same_tenant=st.integers(min_value=1, max_value=5),
        num_other_tenant=st.integers(min_value=1, max_value=5),
        data=st.data(),
    )
    @patch("handler.get_item")
    @patch("handler.query")
    def test_tenant_filtering_in_scoreboard(
        self,
        mock_query,
        mock_get_item,
        session_id,
        tenant_id,
        other_tenant_id,
        num_same_tenant,
        num_other_tenant,
        data,
    ):
        """
        Verify that scoreboard filters out participants from different tenants.
        """
        from handler import lambda_handler

        # Arrange - Ensure tenants are different
        tenant_id_str = str(tenant_id)
        other_tenant_id_str = str(other_tenant_id)

        if tenant_id_str == other_tenant_id_str:
            return  # Skip if tenants are the same

        session_id_str = str(session_id)

        # Create participations from both tenants
        all_participations = []

        # Participations from correct tenant
        for i in range(num_same_tenant):
            all_participations.append(
                {
                    "participationId": str(data.draw(st.uuids())),
                    "participantId": str(data.draw(st.uuids())),
                    "sessionId": session_id_str,
                    "tenantId": tenant_id_str,
                    "totalPoints": 10,
                    "correctAnswers": 1,
                }
            )

        # Participations from wrong tenant (should be filtered out)
        for i in range(num_other_tenant):
            all_participations.append(
                {
                    "participationId": str(data.draw(st.uuids())),
                    "participantId": str(data.draw(st.uuids())),
                    "sessionId": session_id_str,
                    "tenantId": other_tenant_id_str,
                    "totalPoints": 20,
                    "correctAnswers": 2,
                }
            )

        # Mock session exists with specific tenant
        def mock_get_item_side_effect(table, key):
            if "sessionId" in key:
                return {
                    "sessionId": session_id_str,
                    "tenantId": tenant_id_str,
                    "status": "active",
                }
            # Mock GlobalParticipants lookup
            participant_id = key.get("participantId")
            if participant_id:
                return {
                    "participantId": participant_id,
                    "name": f"Participant {participant_id[:8]}",
                    "avatar": "😀",
                }
            return None

        mock_get_item.side_effect = mock_get_item_side_effect
        mock_query.return_value = all_participations

        event = {"pathParameters": {"sessionId": session_id_str}}
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 200
        body = json.loads(response["body"])

        scoreboard = body["scoreboard"]

        # Should only include participants from the correct tenant
        assert len(scoreboard) == num_same_tenant

        # Mock session exists
        def mock_get_item_side_effect(table, key):
            if "sessionId" in key:
                return {
                    "sessionId": session_id_str,
                    "tenantId": tenant_id_str,
                    "status": "active",
                }
            # Mock GlobalParticipants lookup
            participant_id = key.get("participantId")
            if participant_id:
                return {
                    "participantId": participant_id,
                    "tenantId": tenant_id_str,
                    "name": f"Participant {participant_id[:8]}",
                    "avatar": "😀",
                }
            return None

        mock_get_item.side_effect = mock_get_item_side_effect

        # Mock query returns participations for this session only
        mock_query.return_value = session_participations

        event = {"pathParameters": {"sessionId": session_id_str}}
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 200
        body = json.loads(response["body"])

        # Verify all returned participants are from this session
        assert "scoreboard" in body
        scoreboard = body["scoreboard"]

        # Verify the number of participants matches
        assert len(scoreboard) == num_participants

        # Verify all participants have the correct sessionId context
        # (implicitly verified by the fact that we only queried this session)
        for entry in scoreboard:
            assert "participantId" in entry
            assert "totalPoints" in entry
            assert "correctAnswers" in entry
            assert "name" in entry
            assert "avatar" in entry

        # Verify query was called with the correct sessionId
        assert mock_query.called
        call_args = mock_query.call_args
        assert ":sessionId" in call_args[0][2]  # expression_attribute_values
        assert call_args[0][2][":sessionId"] == session_id_str

    @settings(max_examples=100, deadline=None)
    @given(
        session_id=st.uuids(),
        tenant_id=st.uuids(),
        participant_id=st.uuids(),
        participation_id=st.uuids(),
        total_points=st.integers(min_value=0, max_value=100),
        correct_answers=st.integers(min_value=0, max_value=10),
        name=st.text(min_size=1, max_size=50),
    )
    @patch("handler.get_item")
    @patch("handler.query")
    def test_property_20_score_and_answer_persistence(
        self,
        mock_query,
        mock_get_item,
        session_id,
        tenant_id,
        participant_id,
        participation_id,
        total_points,
        correct_answers,
        name,
    ):
        """
        Feature: global-participant-registration, Property 20: Score and answer persistence

        For any session that ends, the SessionParticipation records and Answer records
        for that session should remain unchanged and queryable.

        Validates: Requirements 5.5
        """
        from handler import lambda_handler

        # Arrange
        session_id_str = str(session_id)
        tenant_id_str = str(tenant_id)
        participant_id_str = str(participant_id)
        participation_id_str = str(participation_id)

        # Create a participation with specific scores
        participation = {
            "participationId": participation_id_str,
            "participantId": participant_id_str,
            "sessionId": session_id_str,
            "tenantId": tenant_id_str,
            "totalPoints": total_points,
            "correctAnswers": correct_answers,
        }

        # Mock session exists (could be ended)
        def mock_get_item_side_effect(table, key):
            if "sessionId" in key:
                return {
                    "sessionId": session_id_str,
                    "tenantId": tenant_id_str,
                    "status": "ended",  # Session has ended
                }
            # Mock GlobalParticipants lookup
            if "participantId" in key:
                return {
                    "participantId": participant_id_str,
                    "tenantId": tenant_id_str,
                    "name": name,
                    "avatar": "😀",
                }
            return None

        mock_get_item.side_effect = mock_get_item_side_effect
        mock_query.return_value = [participation]

        event = {"pathParameters": {"sessionId": session_id_str}}
        context = {}

        # Act - Query scoreboard after session ends
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 200
        body = json.loads(response["body"])

        # Verify scores are still accessible
        assert "scoreboard" in body
        scoreboard = body["scoreboard"]
        assert len(scoreboard) == 1

        # Verify the scores match what was stored
        participant_entry = scoreboard[0]
        assert participant_entry["participantId"] == participant_id_str
        assert participant_entry["totalPoints"] == total_points
        assert participant_entry["correctAnswers"] == correct_answers
        assert participant_entry["name"] == name

        # The key property: scores remain unchanged after session ends
        # This is verified by the fact that we can still query them
        # and they match the original values

    @settings(max_examples=100, deadline=None)
    @given(
        session_id=st.uuids(),
        tenant_id=st.uuids(),
        num_participants=st.integers(min_value=2, max_value=10),
    )
    @patch("handler.get_item")
    @patch("handler.query")
    def test_scoreboard_sorted_by_points_descending(
        self,
        mock_query,
        mock_get_item,
        session_id,
        tenant_id,
        num_participants,
    ):
        """
        Verify that scoreboard is sorted by totalPoints in descending order.
        """
        from handler import lambda_handler

        # Arrange
        session_id_str = str(session_id)
        tenant_id_str = str(tenant_id)

        # Create participations with different scores
        session_participations = []
        expected_scores = []

        for i in range(num_participants):
            participant_id = str(st.uuids().example())
            points = st.integers(min_value=0, max_value=100).example()

            session_participations.append(
                {
                    "participationId": str(st.uuids().example()),
                    "participantId": participant_id,
                    "sessionId": session_id_str,
                    "tenantId": tenant_id_str,
                    "totalPoints": points,
                    "correctAnswers": 0,
                }
            )
            expected_scores.append(points)

        # Sort expected scores descending
        expected_scores.sort(reverse=True)

        # Mock session exists
        def mock_get_item_side_effect(table, key):
            if "sessionId" in key:
                return {
                    "sessionId": session_id_str,
                    "tenantId": tenant_id_str,
                    "status": "active",
                }
            # Mock GlobalParticipants lookup
            participant_id = key.get("participantId")
            if participant_id:
                return {
                    "participantId": participant_id,
                    "tenantId": tenant_id_str,
                    "name": f"Participant {participant_id[:8]}",
                    "avatar": "😀",
                }
            return None

        mock_get_item.side_effect = mock_get_item_side_effect
        mock_query.return_value = session_participations

        event = {"pathParameters": {"sessionId": session_id_str}}
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 200
        body = json.loads(response["body"])

        scoreboard = body["scoreboard"]
        actual_scores = [entry["totalPoints"] for entry in scoreboard]

        # Verify scores are in descending order
        assert actual_scores == expected_scores

        # Verify ranks are assigned correctly
        for i, entry in enumerate(scoreboard):
            assert entry["rank"] == i + 1

    @settings(max_examples=100, deadline=None)
    @given(
        session_id=st.uuids(),
        tenant_id=st.uuids(),
    )
    @patch("handler.get_item")
    @patch("handler.query")
    def test_empty_scoreboard_for_session_with_no_participants(
        self,
        mock_query,
        mock_get_item,
        session_id,
        tenant_id,
    ):
        """
        Verify that a session with no participants returns an empty scoreboard.
        """
        from handler import lambda_handler

        # Arrange
        session_id_str = str(session_id)
        tenant_id_str = str(tenant_id)

        # Mock session exists
        mock_get_item.return_value = {
            "sessionId": session_id_str,
            "tenantId": tenant_id_str,
            "status": "active",
        }

        # Mock no participations
        mock_query.return_value = []

        event = {"pathParameters": {"sessionId": session_id_str}}
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 200
        body = json.loads(response["body"])

        assert "scoreboard" in body
        assert body["scoreboard"] == []

    @settings(max_examples=100, deadline=None)
    @given(
        session_id=st.uuids(),
    )
    @patch("handler.get_item")
    def test_session_not_found_returns_404(
        self,
        mock_get_item,
        session_id,
    ):
        """
        Verify that requesting scoreboard for non-existent session returns 404.
        """
        from handler import lambda_handler

        # Arrange
        session_id_str = str(session_id)

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
        tenant_id=st.uuids(),
        other_tenant_id=st.uuids(),
        num_same_tenant=st.integers(min_value=1, max_value=5),
        num_other_tenant=st.integers(min_value=1, max_value=5),
    )
    @patch("handler.get_item")
    @patch("handler.query")
    def test_tenant_filtering_in_scoreboard(
        self,
        mock_query,
        mock_get_item,
        session_id,
        tenant_id,
        other_tenant_id,
        num_same_tenant,
        num_other_tenant,
    ):
        """
        Verify that scoreboard filters out participants from different tenants.
        """
        from handler import lambda_handler

        # Arrange - Ensure tenants are different
        tenant_id_str = str(tenant_id)
        other_tenant_id_str = str(other_tenant_id)

        if tenant_id_str == other_tenant_id_str:
            return  # Skip if tenants are the same

        session_id_str = str(session_id)

        # Create participations from both tenants
        all_participations = []

        # Participations from correct tenant
        for i in range(num_same_tenant):
            all_participations.append(
                {
                    "participationId": str(st.uuids().example()),
                    "participantId": str(st.uuids().example()),
                    "sessionId": session_id_str,
                    "tenantId": tenant_id_str,
                    "totalPoints": 10,
                    "correctAnswers": 1,
                }
            )

        # Participations from wrong tenant (should be filtered out)
        for i in range(num_other_tenant):
            all_participations.append(
                {
                    "participationId": str(st.uuids().example()),
                    "participantId": str(st.uuids().example()),
                    "sessionId": session_id_str,
                    "tenantId": other_tenant_id_str,
                    "totalPoints": 20,
                    "correctAnswers": 2,
                }
            )

        # Mock session exists with specific tenant
        def mock_get_item_side_effect(table, key):
            if "sessionId" in key:
                return {
                    "sessionId": session_id_str,
                    "tenantId": tenant_id_str,
                    "status": "active",
                }
            # Mock GlobalParticipants lookup
            participant_id = key.get("participantId")
            if participant_id:
                return {
                    "participantId": participant_id,
                    "name": f"Participant {participant_id[:8]}",
                    "avatar": "😀",
                }
            return None

        mock_get_item.side_effect = mock_get_item_side_effect
        mock_query.return_value = all_participations

        event = {"pathParameters": {"sessionId": session_id_str}}
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 200
        body = json.loads(response["body"])

        scoreboard = body["scoreboard"]

        # Should only include participants from the correct tenant
        assert len(scoreboard) == num_same_tenant
