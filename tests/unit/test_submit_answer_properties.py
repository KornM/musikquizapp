"""
Property-Based Tests for Submit Answer Lambda Handler

Tests cover:
- Property 16: Answer linked to participation
- Property 17: Score isolation per session
- Property 18: Independent participation records

These tests use Hypothesis for property-based testing to verify universal properties
across many randomly generated inputs.

Validates: Requirements 5.1, 5.2, 5.3
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
sys.path.insert(0, os.path.join(lambda_path, "submit_answer"))
sys.path.insert(0, os.path.join(lambda_path, "common"))


class TestSubmitAnswerProperties:
    """Property-based tests for answer submission"""

    @settings(max_examples=100, deadline=None)
    @given(
        participant_id=st.uuids(),
        session_id=st.uuids(),
        tenant_id=st.uuids(),
        participation_id=st.uuids(),
        round_number=st.integers(min_value=1, max_value=10),
        answer=st.integers(min_value=0, max_value=3),
        correct_answer=st.integers(min_value=0, max_value=3),
    )
    @patch("handler.update_item")
    @patch("handler.put_item")
    @patch("handler.get_item")
    @patch("handler.query")
    def test_property_16_answer_linked_to_participation(
        self,
        mock_query,
        mock_get_item,
        mock_put_item,
        mock_update_item,
        participant_id,
        session_id,
        tenant_id,
        participation_id,
        round_number,
        answer,
        correct_answer,
    ):
        """
        Feature: global-participant-registration, Property 16: Answer linked to participation

        For any answer submitted by a participant, the answer record should reference
        the correct participationId from SessionParticipations.

        Validates: Requirements 5.1
        """
        from handler import lambda_handler

        # Arrange
        participant_id_str = str(participant_id)
        session_id_str = str(session_id)
        tenant_id_str = str(tenant_id)
        participation_id_str = str(participation_id)

        # Mock SessionParticipation lookup
        mock_query.return_value = [
            {
                "participationId": participation_id_str,
                "participantId": participant_id_str,
                "sessionId": session_id_str,
                "tenantId": tenant_id_str,
                "totalPoints": 0,
                "correctAnswers": 0,
            }
        ]

        # Mock round exists
        mock_get_item.side_effect = lambda table, key: {
            "sessionId": session_id_str,
            "roundNumber": round_number,
            "correctAnswer": correct_answer,
        }

        mock_put_item.return_value = {}
        mock_update_item.return_value = {}

        event = {
            "body": json.dumps(
                {
                    "participantId": participant_id_str,
                    "sessionId": session_id_str,
                    "roundNumber": round_number,
                    "answer": answer,
                }
            )
        }
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 201

        # Verify answer was stored with participationId
        assert mock_put_item.called
        call_args = mock_put_item.call_args
        stored_answer = call_args[0][1]  # Second argument is the item

        # Verify participationId is present and correct
        assert "participationId" in stored_answer
        assert stored_answer["participationId"] == participation_id_str

    @settings(max_examples=100, deadline=None)
    @given(
        participant_id=st.uuids(),
        session1_id=st.uuids(),
        session2_id=st.uuids(),
        tenant_id=st.uuids(),
        participation1_id=st.uuids(),
        participation2_id=st.uuids(),
        round_number=st.integers(min_value=1, max_value=10),
        answer=st.integers(min_value=0, max_value=3),
        correct_answer=st.integers(min_value=0, max_value=3),
        initial_points_session1=st.integers(min_value=0, max_value=100),
        initial_points_session2=st.integers(min_value=0, max_value=100),
    )
    @patch("handler.update_item")
    @patch("handler.put_item")
    @patch("handler.get_item")
    @patch("handler.query")
    def test_property_17_score_isolation_per_session(
        self,
        mock_query,
        mock_get_item,
        mock_put_item,
        mock_update_item,
        participant_id,
        session1_id,
        session2_id,
        tenant_id,
        participation1_id,
        participation2_id,
        round_number,
        answer,
        correct_answer,
        initial_points_session1,
        initial_points_session2,
    ):
        """
        Feature: global-participant-registration, Property 17: Score isolation per session

        For any participant who joins multiple sessions and earns points in each,
        the totalPoints in each SessionParticipation record should be independent
        and reflect only that session's score.

        Validates: Requirements 5.2
        """
        from handler import lambda_handler

        # Arrange - Ensure sessions are different
        session1_id_str = str(session1_id)
        session2_id_str = str(session2_id)

        if session1_id_str == session2_id_str:
            return  # Skip if sessions happen to be the same

        participant_id_str = str(participant_id)
        tenant_id_str = str(tenant_id)
        participation1_id_str = str(participation1_id)
        participation2_id_str = str(participation2_id)

        # Mock SessionParticipation lookup for session 1
        mock_query.return_value = [
            {
                "participationId": participation1_id_str,
                "participantId": participant_id_str,
                "sessionId": session1_id_str,
                "tenantId": tenant_id_str,
                "totalPoints": initial_points_session1,
                "correctAnswers": 0,
            }
        ]

        # Mock round exists
        mock_get_item.side_effect = lambda table, key: {
            "sessionId": session1_id_str,
            "roundNumber": round_number,
            "correctAnswer": correct_answer,
        }

        mock_put_item.return_value = {}
        mock_update_item.return_value = {}

        event = {
            "body": json.dumps(
                {
                    "participantId": participant_id_str,
                    "sessionId": session1_id_str,
                    "roundNumber": round_number,
                    "answer": answer,
                }
            )
        }
        context = {}

        # Act - Submit answer for session 1
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 201

        # Verify update_item was called to update session 1 participation
        assert mock_update_item.called
        call_args = mock_update_item.call_args

        # Verify the correct participation was updated
        updated_key = call_args[0][1]  # Second argument is the key
        assert updated_key["participationId"] == participation1_id_str

        # Verify the update expression updates totalPoints
        update_expression = call_args[0][2]  # Third argument is update expression
        assert "totalPoints" in update_expression

        # The key point: session 2's participation should not be affected
        # This is verified by checking that only participation1_id was updated
        for call in mock_update_item.call_args_list:
            updated_key = call[0][1]
            assert updated_key["participationId"] == participation1_id_str
            # Should never update participation2_id
            assert updated_key["participationId"] != participation2_id_str

    @settings(max_examples=100, deadline=None)
    @given(
        participant_id=st.uuids(),
        session1_id=st.uuids(),
        session2_id=st.uuids(),
        session3_id=st.uuids(),
        tenant_id=st.uuids(),
        participation1_id=st.uuids(),
        participation2_id=st.uuids(),
        participation3_id=st.uuids(),
    )
    def test_property_18_independent_participation_records(
        self,
        participant_id,
        session1_id,
        session2_id,
        session3_id,
        tenant_id,
        participation1_id,
        participation2_id,
        participation3_id,
    ):
        """
        Feature: global-participant-registration, Property 18: Independent participation records

        For any participant joining N sessions, the system should create N distinct
        SessionParticipation records, each with a unique participationId.

        Validates: Requirements 5.3
        """
        # This property is primarily tested through the join_session handler
        # Here we verify that answer submission respects the independence by
        # ensuring each answer references the correct participation for its session

        from handler import lambda_handler

        # Arrange
        participant_id_str = str(participant_id)
        session1_id_str = str(session1_id)
        session2_id_str = str(session2_id)
        session3_id_str = str(session3_id)
        tenant_id_str = str(tenant_id)
        participation1_id_str = str(participation1_id)
        participation2_id_str = str(participation2_id)
        participation3_id_str = str(participation3_id)

        # Ensure all sessions are different
        session_ids = {session1_id_str, session2_id_str, session3_id_str}
        if len(session_ids) < 3:
            return  # Skip if any sessions are the same

        # Ensure participation IDs are unique
        participation_ids = {
            participation1_id_str,
            participation2_id_str,
            participation3_id_str,
        }
        if len(participation_ids) < 3:
            return  # Skip if any participation IDs are the same

        # Mock participations for all three sessions
        all_participations = [
            {
                "participationId": participation1_id_str,
                "participantId": participant_id_str,
                "sessionId": session1_id_str,
                "tenantId": tenant_id_str,
                "totalPoints": 0,
                "correctAnswers": 0,
            },
            {
                "participationId": participation2_id_str,
                "participantId": participant_id_str,
                "sessionId": session2_id_str,
                "tenantId": tenant_id_str,
                "totalPoints": 0,
                "correctAnswers": 0,
            },
            {
                "participationId": participation3_id_str,
                "participantId": participant_id_str,
                "sessionId": session3_id_str,
                "tenantId": tenant_id_str,
                "totalPoints": 0,
                "correctAnswers": 0,
            },
        ]

        # Test submitting answers to each session
        for session_id_str, expected_participation_id in [
            (session1_id_str, participation1_id_str),
            (session2_id_str, participation2_id_str),
            (session3_id_str, participation3_id_str),
        ]:
            with (
                patch("handler.query") as mock_query,
                patch("handler.get_item") as mock_get_item,
                patch("handler.put_item") as mock_put_item,
                patch("handler.update_item") as mock_update_item,
            ):
                # Mock query returns all participations, handler filters by sessionId
                mock_query.return_value = all_participations

                # Mock round exists
                mock_get_item.return_value = {
                    "sessionId": session_id_str,
                    "roundNumber": 1,
                    "correctAnswer": 0,
                }

                mock_put_item.return_value = {}
                mock_update_item.return_value = {}

                event = {
                    "body": json.dumps(
                        {
                            "participantId": participant_id_str,
                            "sessionId": session_id_str,
                            "roundNumber": 1,
                            "answer": 0,
                        }
                    )
                }
                context = {}

                # Act
                response = lambda_handler(event, context)

                # Assert
                assert response["statusCode"] == 201

                # Verify the answer was linked to the correct participation
                assert mock_put_item.called
                call_args = mock_put_item.call_args
                stored_answer = call_args[0][1]

                assert stored_answer["participationId"] == expected_participation_id
                assert stored_answer["sessionId"] == session_id_str
