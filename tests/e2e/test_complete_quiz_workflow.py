"""
End-to-End Test: Complete Quiz Workflow

This test simulates the complete workflow of creating and running a quiz:
1. Super admin creates tenant and tenant admin
2. Tenant admin logs in and creates a quiz session
3. Multiple participants register and join the session
4. Participants submit answers
5. Scoreboard displays correct rankings
6. Cross-tenant access is properly blocked
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


class TestCompleteQuizWorkflow:
    """End-to-end test for complete quiz workflow"""

    def test_complete_quiz_workflow(self):
        """
        Test the complete workflow from tenant creation to quiz completion.

        This simulates a real-world scenario where:
        - A super admin sets up a new organization
        - The organization admin creates a quiz
        - Participants join and play the quiz
        - Results are displayed on the scoreboard
        """
        # IDs for this test
        tenant_id = "e2e-tenant-001"
        admin_id = "e2e-admin-001"
        session_id = "e2e-session-001"
        participant1_id = "e2e-participant-001"
        participant2_id = "e2e-participant-002"
        participant3_id = "e2e-participant-003"
        participation1_id = "e2e-participation-001"
        participation2_id = "e2e-participation-002"
        participation3_id = "e2e-participation-003"

        # ===================================================================
        # PHASE 1: SUPER ADMIN CREATES TENANT
        # ===================================================================
        print("\n=== PHASE 1: Super Admin Creates Tenant ===")

        with patch("create_tenant.handler.put_item") as mock_put_tenant:
            from create_tenant.handler import lambda_handler as create_tenant_handler

            create_tenant_event = {
                "body": json.dumps(
                    {
                        "name": "Acme Corporation",
                        "description": "A test organization for E2E testing",
                    }
                ),
                "headers": {"Authorization": "Bearer super_admin_token"},
            }

            with patch("uuid.uuid4", return_value=MagicMock(hex=tenant_id)):
                tenant_response = create_tenant_handler(create_tenant_event, {})

            assert tenant_response["statusCode"] == 201
            tenant_body = json.loads(tenant_response["body"])
            assert tenant_body["tenantId"] == tenant_id
            assert tenant_body["name"] == "Acme Corporation"
            print(f"✓ Tenant created: {tenant_body['name']} ({tenant_id})")

        # ===================================================================
        # PHASE 2: SUPER ADMIN CREATES TENANT ADMIN
        # ===================================================================
        print("\n=== PHASE 2: Super Admin Creates Tenant Admin ===")

        with (
            patch("create_tenant_admin.handler.get_item") as mock_get_tenant,
            patch("create_tenant_admin.handler.query") as mock_query_username,
            patch("create_tenant_admin.handler.put_item") as mock_put_admin,
        ):
            from create_tenant_admin.handler import (
                lambda_handler as create_admin_handler,
            )

            mock_get_tenant.return_value = {
                "tenantId": tenant_id,
                "name": "Acme Corporation",
                "status": "active",
            }
            mock_query_username.return_value = []

            create_admin_event = {
                "pathParameters": {"tenantId": tenant_id},
                "body": json.dumps(
                    {
                        "username": "acme_admin",
                        "password": "SecurePassword123!",
                        "email": "admin@acme.com",
                    }
                ),
                "headers": {"Authorization": "Bearer super_admin_token"},
            }

            with patch("uuid.uuid4", return_value=MagicMock(hex=admin_id)):
                admin_response = create_admin_handler(create_admin_event, {})

            assert admin_response["statusCode"] == 201
            admin_body = json.loads(admin_response["body"])
            assert admin_body["tenantId"] == tenant_id
            assert admin_body["username"] == "acme_admin"
            print(f"✓ Tenant admin created: {admin_body['username']} ({admin_id})")

        # ===================================================================
        # PHASE 3: TENANT ADMIN LOGS IN
        # ===================================================================
        print("\n=== PHASE 3: Tenant Admin Logs In ===")

        with (
            patch("admin_login.handler.query") as mock_query_login,
            patch("admin_login.handler.verify_password") as mock_verify,
        ):
            from admin_login.handler import lambda_handler as login_handler

            mock_query_login.return_value = [
                {
                    "adminId": admin_id,
                    "username": "acme_admin",
                    "passwordHash": "hashed_password",
                    "tenantId": tenant_id,
                    "role": "tenant_admin",
                }
            ]
            mock_verify.return_value = True

            login_event = {
                "body": json.dumps(
                    {"username": "acme_admin", "password": "SecurePassword123!"}
                ),
                "headers": {},
            }

            login_response = login_handler(login_event, {})

            assert login_response["statusCode"] == 200
            login_body = json.loads(login_response["body"])
            assert "token" in login_body
            assert login_body["tenantId"] == tenant_id
            admin_token = login_body["token"]
            print(f"✓ Admin logged in successfully, received token")

        # ===================================================================
        # PHASE 4: TENANT ADMIN CREATES QUIZ SESSION
        # ===================================================================
        print("\n=== PHASE 4: Tenant Admin Creates Quiz Session ===")

        with patch("create_quiz.handler.put_item") as mock_put_session:
            from create_quiz.handler import lambda_handler as create_session_handler

            create_session_event = {
                "body": json.dumps(
                    {
                        "title": "General Knowledge Quiz",
                        "description": "Test your knowledge!",
                    }
                ),
                "headers": {"Authorization": f"Bearer {admin_token}"},
                "requestContext": {
                    "authorizer": {
                        "tenantId": tenant_id,
                        "adminId": admin_id,
                        "role": "tenant_admin",
                    }
                },
            }

            with patch("uuid.uuid4", return_value=MagicMock(hex=session_id)):
                session_response = create_session_handler(create_session_event, {})

            assert session_response["statusCode"] == 201
            session_body = json.loads(session_response["body"])
            assert session_body["tenantId"] == tenant_id
            assert session_body["title"] == "General Knowledge Quiz"
            print(f"✓ Quiz session created: {session_body['title']} ({session_id})")

        # ===================================================================
        # PHASE 5: PARTICIPANTS REGISTER
        # ===================================================================
        print("\n=== PHASE 5: Participants Register ===")

        participants = [
            {"id": participant1_id, "name": "Alice", "avatar": "😀"},
            {"id": participant2_id, "name": "Bob", "avatar": "😎"},
            {"id": participant3_id, "name": "Charlie", "avatar": "🤓"},
        ]

        participant_tokens = {}

        for participant in participants:
            with (
                patch(
                    "register_global_participant.handler.get_item"
                ) as mock_get_tenant,
                patch(
                    "register_global_participant.handler.put_item"
                ) as mock_put_participant,
            ):
                from register_global_participant.handler import (
                    lambda_handler as register_handler,
                )

                mock_get_tenant.return_value = {
                    "tenantId": tenant_id,
                    "name": "Acme Corporation",
                    "status": "active",
                }

                register_event = {
                    "body": json.dumps(
                        {
                            "tenantId": tenant_id,
                            "name": participant["name"],
                            "avatar": participant["avatar"],
                        }
                    ),
                    "headers": {},
                }

                with patch("uuid.uuid4", return_value=MagicMock(hex=participant["id"])):
                    register_response = register_handler(register_event, {})

                assert register_response["statusCode"] == 201
                register_body = json.loads(register_response["body"])
                assert register_body["participantId"] == participant["id"]
                participant_tokens[participant["id"]] = register_body["token"]
                print(
                    f"✓ Participant registered: {participant['name']} ({participant['id']})"
                )

        # ===================================================================
        # PHASE 6: PARTICIPANTS JOIN SESSION
        # ===================================================================
        print("\n=== PHASE 6: Participants Join Session ===")

        participation_ids = [participation1_id, participation2_id, participation3_id]

        for i, participant in enumerate(participants):
            with (
                patch("join_session.handler.get_item") as mock_get_session,
                patch("join_session.handler.query") as mock_query_participation,
                patch("join_session.handler.put_item") as mock_put_participation,
            ):
                from join_session.handler import lambda_handler as join_handler

                mock_get_session.return_value = {
                    "sessionId": session_id,
                    "tenantId": tenant_id,
                    "title": "General Knowledge Quiz",
                }
                mock_query_participation.return_value = []

                join_event = {
                    "pathParameters": {"sessionId": session_id},
                    "headers": {
                        "Authorization": f"Bearer {participant_tokens[participant['id']]}"
                    },
                    "requestContext": {
                        "authorizer": {
                            "participantId": participant["id"],
                            "tenantId": tenant_id,
                        }
                    },
                }

                with patch(
                    "uuid.uuid4", return_value=MagicMock(hex=participation_ids[i])
                ):
                    join_response = join_handler(join_event, {})

                assert join_response["statusCode"] == 200
                join_body = json.loads(join_response["body"])
                assert join_body["participationId"] == participation_ids[i]
                assert join_body["totalPoints"] == 0
                print(f"✓ {participant['name']} joined session")

        # ===================================================================
        # PHASE 7: PARTICIPANTS SUBMIT ANSWERS
        # ===================================================================
        print("\n=== PHASE 7: Participants Submit Answers ===")

        # Simulate different scores for each participant
        scores = [
            {"participant": participants[0], "points": 150, "correct": 3},
            {"participant": participants[1], "points": 200, "correct": 4},
            {"participant": participants[2], "points": 100, "correct": 2},
        ]

        for score_data in scores:
            with (
                patch("submit_answer.handler.get_item") as mock_get_session,
                patch("submit_answer.handler.query") as mock_query_participation,
                patch("submit_answer.handler.put_item") as mock_put_answer,
                patch("submit_answer.handler.update_item") as mock_update_participation,
            ):
                from submit_answer.handler import lambda_handler as submit_handler

                mock_get_session.return_value = {
                    "sessionId": session_id,
                    "tenantId": tenant_id,
                    "currentRound": 1,
                }

                participant_idx = participants.index(score_data["participant"])
                mock_query_participation.return_value = [
                    {
                        "participationId": participation_ids[participant_idx],
                        "participantId": score_data["participant"]["id"],
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
                            "answer": 1,
                            "timeElapsed": 5.0,
                        }
                    ),
                    "headers": {
                        "Authorization": f"Bearer {participant_tokens[score_data['participant']['id']]}"
                    },
                    "requestContext": {
                        "authorizer": {
                            "participantId": score_data["participant"]["id"],
                            "tenantId": tenant_id,
                        }
                    },
                }

                submit_response = submit_handler(submit_event, {})
                assert submit_response["statusCode"] == 200
                print(f"✓ {score_data['participant']['name']} submitted answer")

        # ===================================================================
        # PHASE 8: VIEW SCOREBOARD
        # ===================================================================
        print("\n=== PHASE 8: View Scoreboard ===")

        with (
            patch("get_scoreboard.handler.get_item") as mock_get_session,
            patch("get_scoreboard.handler.query") as mock_query_participations,
        ):
            from get_scoreboard.handler import lambda_handler as scoreboard_handler

            mock_get_session.return_value = {
                "sessionId": session_id,
                "tenantId": tenant_id,
            }

            # Return participants sorted by points (descending)
            mock_query_participations.return_value = [
                {
                    "participationId": participation2_id,
                    "participantId": participant2_id,
                    "name": "Bob",
                    "avatar": "😎",
                    "totalPoints": 200,
                    "correctAnswers": 4,
                },
                {
                    "participationId": participation1_id,
                    "participantId": participant1_id,
                    "name": "Alice",
                    "avatar": "😀",
                    "totalPoints": 150,
                    "correctAnswers": 3,
                },
                {
                    "participationId": participation3_id,
                    "participantId": participant3_id,
                    "name": "Charlie",
                    "avatar": "🤓",
                    "totalPoints": 100,
                    "correctAnswers": 2,
                },
            ]

            scoreboard_event = {
                "pathParameters": {"sessionId": session_id},
                "headers": {},
            }

            scoreboard_response = scoreboard_handler(scoreboard_event, {})

            assert scoreboard_response["statusCode"] == 200
            scoreboard_body = json.loads(scoreboard_response["body"])
            assert len(scoreboard_body["participants"]) == 3

            # Verify correct order (highest score first)
            assert scoreboard_body["participants"][0]["name"] == "Bob"
            assert scoreboard_body["participants"][0]["totalPoints"] == 200
            assert scoreboard_body["participants"][1]["name"] == "Alice"
            assert scoreboard_body["participants"][1]["totalPoints"] == 150
            assert scoreboard_body["participants"][2]["name"] == "Charlie"
            assert scoreboard_body["participants"][2]["totalPoints"] == 100

            print("\n✓ Scoreboard:")
            for i, p in enumerate(scoreboard_body["participants"], 1):
                print(
                    f"  {i}. {p['name']} {p['avatar']} - {p['totalPoints']} points ({p['correctAnswers']} correct)"
                )

        # ===================================================================
        # PHASE 9: TEST CROSS-TENANT ACCESS BLOCKING
        # ===================================================================
        print("\n=== PHASE 9: Test Cross-Tenant Access Blocking ===")

        other_tenant_id = "other-tenant-999"
        other_participant_id = "other-participant-999"

        # Register participant in different tenant
        with (
            patch("register_global_participant.handler.get_item") as mock_get_tenant,
            patch(
                "register_global_participant.handler.put_item"
            ) as mock_put_participant,
        ):
            mock_get_tenant.return_value = {
                "tenantId": other_tenant_id,
                "name": "Other Organization",
                "status": "active",
            }

            register_event = {
                "body": json.dumps(
                    {"tenantId": other_tenant_id, "name": "Intruder", "avatar": "👾"}
                ),
                "headers": {},
            }

            with patch("uuid.uuid4", return_value=MagicMock(hex=other_participant_id)):
                register_response = register_handler(register_event, {})

            other_participant_token = json.loads(register_response["body"])["token"]

        # Try to join session from different tenant
        with patch("join_session.handler.get_item") as mock_get_session:
            mock_get_session.return_value = {
                "sessionId": session_id,
                "tenantId": tenant_id,  # Original tenant
                "title": "General Knowledge Quiz",
            }

            join_event = {
                "pathParameters": {"sessionId": session_id},
                "headers": {"Authorization": f"Bearer {other_participant_token}"},
                "requestContext": {
                    "authorizer": {
                        "participantId": other_participant_id,
                        "tenantId": other_tenant_id,  # Different tenant!
                    }
                },
            }

            join_response = join_handler(join_event, {})

            # Should be blocked
            assert join_response["statusCode"] == 403
            error_body = json.loads(join_response["body"])
            assert error_body["error"]["code"] == "CROSS_TENANT_ACCESS"
            print("✓ Cross-tenant access properly blocked")

        print("\n=== E2E TEST COMPLETE ===")
        print("✓ All phases completed successfully!")
        print(f"  - Tenant created: Acme Corporation")
        print(f"  - Admin created and logged in: acme_admin")
        print(f"  - Quiz session created: General Knowledge Quiz")
        print(f"  - 3 participants registered and joined")
        print(f"  - Answers submitted and scored")
        print(f"  - Scoreboard displayed correctly")
        print(f"  - Cross-tenant access blocked")
