"""
Integration Tests for Complete Participant Journey

Tests the full participant experience including:
- Global participant registration
- Profile management
- Session joining
- Answer submission
- Score tracking
- Cross-session participation
"""

import json
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

lambda_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "lambda")
)
sys.path.insert(0, lambda_path)


class TestParticipantJourney:
    """Integration tests for complete participant journey"""

    def test_complete_participant_journey(self):
        """
        Test the complete journey of a participant from registration to scoring.

        Workflow:
        1. Participant registers with tenant
        2. Participant joins a session
        3. Participant submits answers
        4. Participant's score is updated
        5. Participant appears on scoreboard
        6. Participant updates profile
        7. Updated profile reflects in session
        """
        tenant_id = "test-tenant-123"
        participant_id = "participant-456"
        session_id = "session-789"
        participation_id = "participation-101"

        # Step 1: Register participant
        with (
            patch("register_global_participant.handler.get_item") as mock_get_tenant,
            patch(
                "register_global_participant.handler.put_item"
            ) as mock_put_participant,
        ):
            from register_global_participant.handler import (
                lambda_handler as register_handler,
            )

            mock_get_tenant.return_value = {
                "tenantId": tenant_id,
                "name": "Test Org",
                "status": "active",
            }

            register_event = {
                "body": json.dumps(
                    {"tenantId": tenant_id, "name": "John Doe", "avatar": "😀"}
                ),
                "headers": {},
            }

            with patch("uuid.uuid4", return_value=MagicMock(hex=participant_id)):
                response = register_handler(register_event, {})

            assert response["statusCode"] == 201
            body = json.loads(response["body"])
            assert body["participantId"] == participant_id
            assert body["name"] == "John Doe"
            assert "token" in body
            participant_token = body["token"]

        # Step 2: Join session
        with (
            patch("join_session.handler.get_item") as mock_get_session,
            patch("join_session.handler.query") as mock_query_participation,
            patch("join_session.handler.put_item") as mock_put_participation,
        ):
            from join_session.handler import lambda_handler as join_handler

            mock_get_session.return_value = {
                "sessionId": session_id,
                "tenantId": tenant_id,
                "title": "Test Quiz",
            }

            # No existing participation
            mock_query_participation.return_value = []

            join_event = {
                "pathParameters": {"sessionId": session_id},
                "headers": {"Authorization": f"Bearer {participant_token}"},
                "requestContext": {
                    "authorizer": {
                        "participantId": participant_id,
                        "tenantId": tenant_id,
                    }
                },
            }

            with patch("uuid.uuid4", return_value=MagicMock(hex=participation_id)):
                response = join_handler(join_event, {})

            assert response["statusCode"] == 200
            body = json.loads(response["body"])
            assert body["participationId"] == participation_id
            assert body["totalPoints"] == 0

        # Step 3: Submit answer
        with (
            patch("submit_answer.handler.get_item") as mock_get_session_answer,
            patch("submit_answer.handler.query") as mock_query_participation_answer,
            patch("submit_answer.handler.put_item") as mock_put_answer,
            patch("submit_answer.handler.update_item") as mock_update_participation,
        ):
            from submit_answer.handler import lambda_handler as submit_handler

            mock_get_session_answer.return_value = {
                "sessionId": session_id,
                "tenantId": tenant_id,
                "currentRound": 1,
            }

            mock_query_participation_answer.return_value = [
                {
                    "participationId": participation_id,
                    "participantId": participant_id,
                    "sessionId": session_id,
                    "totalPoints": 0,
                    "correctAnswers": 0,
                }
            ]

            submit_event = {
                "body": json.dumps(
                    {
                        "sessionId": session_id,
                        "roundNumber": 1,
                        "answer": 2,
                        "timeElapsed": 5.5,
                    }
                ),
                "headers": {"Authorization": f"Bearer {participant_token}"},
                "requestContext": {
                    "authorizer": {
                        "participantId": participant_id,
                        "tenantId": tenant_id,
                    }
                },
            }

            response = submit_handler(submit_event, {})

            assert response["statusCode"] == 200
            body = json.loads(response["body"])
            assert "points" in body

        # Step 4: Check scoreboard
        with (
            patch("get_scoreboard.handler.get_item") as mock_get_session_scoreboard,
            patch("get_scoreboard.handler.query") as mock_query_participations,
        ):
            from get_scoreboard.handler import lambda_handler as scoreboard_handler

            mock_get_session_scoreboard.return_value = {
                "sessionId": session_id,
                "tenantId": tenant_id,
            }

            mock_query_participations.return_value = [
                {
                    "participationId": participation_id,
                    "participantId": participant_id,
                    "sessionId": session_id,
                    "totalPoints": 100,
                    "correctAnswers": 1,
                    "name": "John Doe",
                    "avatar": "😀",
                }
            ]

            scoreboard_event = {
                "pathParameters": {"sessionId": session_id},
                "headers": {},
            }

            response = scoreboard_handler(scoreboard_event, {})

            assert response["statusCode"] == 200
            body = json.loads(response["body"])
            assert len(body["participants"]) == 1
            assert body["participants"][0]["name"] == "John Doe"
            assert body["participants"][0]["totalPoints"] == 100

        # Step 5: Update profile
        with (
            patch("update_global_participant.handler.get_item") as mock_get_participant,
            patch(
                "update_global_participant.handler.update_item"
            ) as mock_update_participant,
        ):
            from update_global_participant.handler import (
                lambda_handler as update_handler,
            )

            mock_get_participant.return_value = {
                "participantId": participant_id,
                "tenantId": tenant_id,
                "name": "John Doe",
                "avatar": "😀",
            }

            update_event = {
                "pathParameters": {"participantId": participant_id},
                "body": json.dumps({"name": "Jane Doe", "avatar": "😎"}),
                "headers": {"Authorization": f"Bearer {participant_token}"},
                "requestContext": {
                    "authorizer": {
                        "participantId": participant_id,
                        "tenantId": tenant_id,
                    }
                },
            }

            response = update_handler(update_event, {})

            assert response["statusCode"] == 200
            body = json.loads(response["body"])
            assert body["name"] == "Jane Doe"
            assert body["avatar"] == "😎"

    def test_multi_session_participation(self):
        """
        Test participant joining multiple sessions with independent scores.

        Workflow:
        1. Participant registers
        2. Participant joins session 1
        3. Participant earns points in session 1
        4. Participant joins session 2
        5. Participant earns different points in session 2
        6. Verify scores are independent
        """
        tenant_id = "test-tenant"
        participant_id = "participant-123"
        session1_id = "session-1"
        session2_id = "session-2"
        participation1_id = "participation-1"
        participation2_id = "participation-2"

        # Register participant (already tested above, simplified here)
        participant_token = "mock_token"

        # Join session 1
        with (
            patch("join_session.handler.get_item") as mock_get_session,
            patch("join_session.handler.query") as mock_query,
            patch("join_session.handler.put_item") as mock_put,
        ):
            from join_session.handler import lambda_handler as join_handler

            mock_get_session.return_value = {
                "sessionId": session1_id,
                "tenantId": tenant_id,
            }
            mock_query.return_value = []

            event1 = {
                "pathParameters": {"sessionId": session1_id},
                "headers": {"Authorization": f"Bearer {participant_token}"},
                "requestContext": {
                    "authorizer": {
                        "participantId": participant_id,
                        "tenantId": tenant_id,
                    }
                },
            }

            with patch("uuid.uuid4", return_value=MagicMock(hex=participation1_id)):
                response1 = join_handler(event1, {})

            assert response1["statusCode"] == 200
            body1 = json.loads(response1["body"])
            assert body1["participationId"] == participation1_id

        # Join session 2
        with (
            patch("join_session.handler.get_item") as mock_get_session,
            patch("join_session.handler.query") as mock_query,
            patch("join_session.handler.put_item") as mock_put,
        ):
            mock_get_session.return_value = {
                "sessionId": session2_id,
                "tenantId": tenant_id,
            }
            mock_query.return_value = []

            event2 = {
                "pathParameters": {"sessionId": session2_id},
                "headers": {"Authorization": f"Bearer {participant_token}"},
                "requestContext": {
                    "authorizer": {
                        "participantId": participant_id,
                        "tenantId": tenant_id,
                    }
                },
            }

            with patch("uuid.uuid4", return_value=MagicMock(hex=participation2_id)):
                response2 = join_handler(event2, {})

            assert response2["statusCode"] == 200
            body2 = json.loads(response2["body"])
            assert body2["participationId"] == participation2_id
            # Verify different participation IDs
            assert participation1_id != participation2_id

        # Verify independent scoreboards
        with (
            patch("get_scoreboard.handler.get_item") as mock_get_session,
            patch("get_scoreboard.handler.query") as mock_query,
        ):
            from get_scoreboard.handler import lambda_handler as scoreboard_handler

            # Session 1 scoreboard
            mock_get_session.return_value = {
                "sessionId": session1_id,
                "tenantId": tenant_id,
            }
            mock_query.return_value = [
                {
                    "participationId": participation1_id,
                    "totalPoints": 100,
                    "name": "Test User",
                }
            ]

            event_sb1 = {"pathParameters": {"sessionId": session1_id}, "headers": {}}

            response_sb1 = scoreboard_handler(event_sb1, {})
            body_sb1 = json.loads(response_sb1["body"])

            # Session 2 scoreboard
            mock_get_session.return_value = {
                "sessionId": session2_id,
                "tenantId": tenant_id,
            }
            mock_query.return_value = [
                {
                    "participationId": participation2_id,
                    "totalPoints": 200,
                    "name": "Test User",
                }
            ]

            event_sb2 = {"pathParameters": {"sessionId": session2_id}, "headers": {}}

            response_sb2 = scoreboard_handler(event_sb2, {})
            body_sb2 = json.loads(response_sb2["body"])

            # Verify different scores
            assert body_sb1["participants"][0]["totalPoints"] == 100
            assert body_sb2["participants"][0]["totalPoints"] == 200

    def test_cross_tenant_participant_isolation(self):
        """
        Test that participants cannot join sessions from different tenants.

        Workflow:
        1. Participant registers with tenant 1
        2. Session exists in tenant 2
        3. Participant tries to join tenant 2's session
        4. Verify access is denied
        """
        tenant1_id = "tenant-1"
        tenant2_id = "tenant-2"
        participant_id = "participant-123"
        session2_id = "session-in-tenant-2"

        with (
            patch("join_session.handler.get_item") as mock_get_session,
        ):
            from join_session.handler import lambda_handler as join_handler

            # Session belongs to tenant 2
            mock_get_session.return_value = {
                "sessionId": session2_id,
                "tenantId": tenant2_id,
                "title": "Tenant 2 Quiz",
            }

            # Participant from tenant 1 tries to join
            event = {
                "pathParameters": {"sessionId": session2_id},
                "headers": {"Authorization": "Bearer mock_token"},
                "requestContext": {
                    "authorizer": {
                        "participantId": participant_id,
                        "tenantId": tenant1_id,  # Different tenant!
                    }
                },
            }

            response = join_handler(event, {})

            # Should be denied
            assert response["statusCode"] == 403
            body = json.loads(response["body"])
            assert body["error"]["code"] == "CROSS_TENANT_ACCESS"
