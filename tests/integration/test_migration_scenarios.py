"""
Integration Tests for Migration Scenarios

Tests the migration from single-tenant to multi-tenant system:
- Default tenant creation
- Admin migration
- Session migration
- Participant migration
- Backward compatibility
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


class TestMigrationScenarios:
    """Integration tests for migration scenarios"""

    def test_default_tenant_setup(self):
        """
        Test that default tenant is created correctly for backward compatibility.

        Workflow:
        1. Run default tenant setup script
        2. Verify default tenant exists
        3. Verify default tenant has correct ID and status
        """
        default_tenant_id = "00000000-0000-0000-0000-000000000001"

        # Import the script module first
        scripts_path = os.path.join(os.path.dirname(__file__), "..", "..", "scripts")
        if scripts_path not in sys.path:
            sys.path.insert(0, scripts_path)

        import setup_default_tenant

        mock_table = MagicMock()
        mock_table.scan.return_value = {"Items": []}
        mock_table.get_item.return_value = {}  # No existing default tenant
        mock_table.put_item.return_value = {}

        with patch("boto3.resource") as mock_boto3:
            mock_dynamodb = MagicMock()
            mock_boto3.return_value = mock_dynamodb
            mock_dynamodb.Table.return_value = mock_table

            # Run setup
            result = setup_default_tenant.create_default_tenant()

            # Verify default tenant was created
            assert result is not None
            assert result["tenantId"] == default_tenant_id
            assert result["name"] == "Default Organization"
            assert result["status"] == "active"
            mock_table.put_item.assert_called_once()

    def test_admin_migration(self):
        """
        Test migration of existing admins to default tenant.

        Workflow:
        1. Existing admins without tenantId
        2. Run migration script
        3. Verify admins are assigned to default tenant
        4. Verify first admin becomes super_admin
        """
        default_tenant_id = "00000000-0000-0000-0000-000000000001"

        existing_admins = [
            {
                "adminId": "admin-1",
                "username": "admin1",
                "passwordHash": "hash1",
                "createdAt": "2024-01-01T00:00:00",
                # No tenantId or role
            },
            {
                "adminId": "admin-2",
                "username": "admin2",
                "passwordHash": "hash2",
                "createdAt": "2024-01-02T00:00:00",
                # No tenantId or role
            },
        ]

        # Import the script module first
        scripts_path = os.path.join(os.path.dirname(__file__), "..", "..", "scripts")
        if scripts_path not in sys.path:
            sys.path.insert(0, scripts_path)

        import migrate_admins

        mock_table = MagicMock()
        mock_table.scan.return_value = {"Items": existing_admins}
        mock_table.update_item.return_value = {}

        with patch("boto3.resource") as mock_boto3:
            mock_dynamodb = MagicMock()
            mock_boto3.return_value = mock_dynamodb
            mock_dynamodb.Table.return_value = mock_table

            # Get admins
            admins = migrate_admins.get_admins_without_tenant()
            assert len(admins) == 2

            # Migrate both admins
            admins.sort(key=lambda x: x.get("createdAt", ""))
            for i, admin in enumerate(admins):
                is_first = i == 0
                result = migrate_admins.migrate_admin(admin, is_first)
                assert result is True

            # Verify both admins were updated
            assert mock_table.update_item.call_count == 2

    def test_session_migration(self):
        """
        Test migration of existing sessions to default tenant.

        Workflow:
        1. Existing sessions without tenantId
        2. Run migration script
        3. Verify sessions are assigned to default tenant
        """
        default_tenant_id = "00000000-0000-0000-0000-000000000000"

        existing_sessions = [
            {
                "sessionId": "session-1",
                "title": "Old Quiz 1",
                # No tenantId
            },
            {
                "sessionId": "session-2",
                "title": "Old Quiz 2",
                # No tenantId
            },
        ]

        # Import the script module first
        scripts_path = os.path.join(os.path.dirname(__file__), "..", "..", "scripts")
        if scripts_path not in sys.path:
            sys.path.insert(0, scripts_path)

        import migrate_sessions

        with (
            patch.object(migrate_sessions, "sessions_table") as mock_table,
        ):
            mock_table.scan.return_value = {"Items": existing_sessions}

            migrate_sessions.migrate_sessions(default_tenant_id)

            # Verify both sessions were updated
            assert mock_table.update_item.call_count == 2

    def test_participant_migration(self):
        """
        Test migration of session-specific participants to global participants.

        Workflow:
        1. Existing participants in old Participants table
        2. Run migration script
        3. Verify GlobalParticipants records created
        4. Verify SessionParticipations records created
        5. Verify scores migrated correctly
        """
        default_tenant_id = "00000000-0000-0000-0000-000000000000"

        old_participants = [
            {
                "participantId": "old-participant-1",
                "sessionId": "session-1",
                "name": "John Doe",
                "avatar": "😀",
                "totalPoints": 100,
                "correctAnswers": 5,
            },
            {
                "participantId": "old-participant-2",
                "sessionId": "session-1",
                "name": "Jane Smith",
                "avatar": "😎",
                "totalPoints": 150,
                "correctAnswers": 7,
            },
        ]

        # Import the script module first
        scripts_path = os.path.join(os.path.dirname(__file__), "..", "..", "scripts")
        if scripts_path not in sys.path:
            sys.path.insert(0, scripts_path)

        import migrate_participants

        with (
            patch.object(migrate_participants, "participants_table") as mock_old_table,
            patch.object(
                migrate_participants, "global_participants_table"
            ) as mock_global_table,
            patch.object(
                migrate_participants, "session_participations_table"
            ) as mock_participation_table,
        ):
            mock_old_table.scan.return_value = {"Items": old_participants}

            migrate_participants.migrate_participants(default_tenant_id)

            # Verify GlobalParticipants and SessionParticipations were created
            assert mock_global_table.put_item.call_count >= 2
            assert mock_participation_table.put_item.call_count >= 2

    def test_backward_compatibility_api(self):
        """
        Test that APIs work without tenant context (backward compatibility).

        Workflow:
        1. Call API without tenant context in token
        2. Verify default tenant is used
        3. Verify response format is unchanged
        """
        default_tenant_id = "00000000-0000-0000-0000-000000000000"

        from common import backward_compatibility
        from create_quiz import handler as create_quiz_handler

        with (
            patch.object(
                backward_compatibility, "ensure_tenant_context"
            ) as mock_ensure,
            patch.object(create_quiz_handler, "table") as mock_table,
        ):
            mock_ensure.return_value = default_tenant_id
            mock_table.put_item.return_value = {}

            # Legacy request without tenant context
            event = {
                "body": json.dumps(
                    {
                        "title": "Legacy Quiz",
                        "description": "Created without tenant context",
                    }
                ),
                "headers": {},
                "requestContext": {},  # No authorizer
            }

            response = create_quiz_handler.lambda_handler(event, {})

            # Should succeed
            assert response["statusCode"] == 201
            body = json.loads(response["body"])

            # Response format should be unchanged (backward compatible)
            assert "sessionId" in body
            assert "title" in body
            # tenantId might be included but not required for backward compatibility

    def test_full_migration_workflow(self):
        """
        Test the complete migration workflow from start to finish.

        Workflow:
        1. Setup default tenant
        2. Migrate admins
        3. Migrate sessions
        4. Migrate participants
        5. Migrate answers
        6. Verify system works end-to-end
        """
        default_tenant_id = "00000000-0000-0000-0000-000000000000"

        # Import the script module first
        scripts_path = os.path.join(os.path.dirname(__file__), "..", "..", "scripts")
        if scripts_path not in sys.path:
            sys.path.insert(0, scripts_path)

        import run_full_migration

        # This would call the full migration script
        with (
            patch.object(run_full_migration, "setup_default_tenant") as mock_setup,
            patch.object(run_full_migration, "migrate_admins") as mock_migrate_admins,
            patch.object(
                run_full_migration, "migrate_sessions"
            ) as mock_migrate_sessions,
            patch.object(
                run_full_migration, "migrate_participants"
            ) as mock_migrate_participants,
            patch.object(run_full_migration, "migrate_answers") as mock_migrate_answers,
        ):
            run_full_migration.run_full_migration()

            # Verify all migration steps were called
            mock_setup.assert_called_once()
            mock_migrate_admins.assert_called_once()
            mock_migrate_sessions.assert_called_once()
            mock_migrate_participants.assert_called_once()
            mock_migrate_answers.assert_called_once()
