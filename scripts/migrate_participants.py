#!/usr/bin/env python3
"""
Migrate Participants to Global Participants Script

This script migrates existing session-specific participants to the global participant model.
It creates GlobalParticipants records and SessionParticipations records, preserving all
existing participant data including scores and answers.

Usage:
    python scripts/migrate_participants.py
    python scripts/migrate_participants.py --dry-run
"""

import argparse
import sys
import os
import uuid
from datetime import datetime

# Add lambda common directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lambda", "common"))

import boto3
from botocore.exceptions import ClientError

# Default tenant ID (must match setup_default_tenant.py)
DEFAULT_TENANT_ID = "00000000-0000-0000-0000-000000000001"


def get_legacy_participants(table_name="Participants"):
    """
    Query all participants from the legacy Participants table.

    Args:
        table_name (str): DynamoDB table name

    Returns:
        list: List of legacy participant items
    """
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)

    try:
        # Scan for all participants
        response = table.scan()
        items = response.get("Items", [])

        # Handle pagination
        while "LastEvaluatedKey" in response:
            response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
            items.extend(response.get("Items", []))

        return items
    except ClientError as e:
        print(f"Error querying legacy participants: {str(e)}")
        return []


def check_global_participant_exists(participant_id, table_name="GlobalParticipants"):
    """
    Check if a global participant already exists.

    Args:
        participant_id (str): Participant ID to check
        table_name (str): DynamoDB table name

    Returns:
        bool: True if exists, False otherwise
    """
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)

    try:
        response = table.get_item(Key={"participantId": participant_id})
        return "Item" in response
    except ClientError:
        return False


def create_global_participant(participant, dry_run=False):
    """
    Create a GlobalParticipants record from a legacy participant.

    Args:
        participant (dict): Legacy participant item
        dry_run (bool): If True, don't actually update the database

    Returns:
        bool: True if successful, False otherwise
    """
    participant_id = participant.get("participantId")
    name = participant.get("name", "Unknown")
    avatar = participant.get("avatar", "😀")

    # Check if already migrated
    if check_global_participant_exists(participant_id):
        print(
            f"    Global participant already exists for {name} (ID: {participant_id})"
        )
        return True

    print(f"    Creating global participant for {name} (ID: {participant_id})")

    if dry_run:
        print(f"      [DRY RUN] Would create GlobalParticipants record")
        return True

    # Create global participant record
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("GlobalParticipants")

    global_participant = {
        "participantId": participant_id,
        "tenantId": DEFAULT_TENANT_ID,
        "name": name,
        "avatar": avatar,
        "createdAt": participant.get("registeredAt", datetime.utcnow().isoformat()),
        "updatedAt": datetime.utcnow().isoformat(),
    }

    # Add token if it exists
    if "token" in participant:
        global_participant["token"] = participant["token"]

    try:
        table.put_item(Item=global_participant)
        print(f"      Successfully created global participant")
        return True
    except ClientError as e:
        print(f"      Error creating global participant: {str(e)}")
        return False


def create_session_participation(participant, dry_run=False):
    """
    Create a SessionParticipations record from a legacy participant.

    Args:
        participant (dict): Legacy participant item
        dry_run (bool): If True, don't actually update the database

    Returns:
        bool: True if successful, False otherwise
    """
    participant_id = participant.get("participantId")
    session_id = participant.get("sessionId")
    name = participant.get("name", "Unknown")

    print(f"    Creating session participation for {name} in session {session_id}")

    if dry_run:
        print(f"      [DRY RUN] Would create SessionParticipations record")
        return True

    # Create session participation record
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("SessionParticipations")

    participation_id = str(uuid.uuid4())
    participation = {
        "participationId": participation_id,
        "participantId": participant_id,
        "sessionId": session_id,
        "tenantId": DEFAULT_TENANT_ID,
        "joinedAt": participant.get("registeredAt", datetime.utcnow().isoformat()),
        "totalPoints": participant.get("totalPoints", 0),
        "correctAnswers": participant.get("correctAnswers", 0),
    }

    try:
        table.put_item(Item=participation)
        print(
            f"      Successfully created session participation (ID: {participation_id})"
        )
        return True
    except ClientError as e:
        print(f"      Error creating session participation: {str(e)}")
        return False


def migrate_participant(participant, dry_run=False):
    """
    Migrate a single participant to the global participant model.

    Args:
        participant (dict): Legacy participant item to migrate
        dry_run (bool): If True, don't actually update the database

    Returns:
        bool: True if successful, False otherwise
    """
    participant_id = participant.get("participantId")
    name = participant.get("name", "Unknown")
    session_id = participant.get("sessionId", "unknown")

    print(
        f"  Migrating participant '{name}' (ID: {participant_id}, Session: {session_id})"
    )

    # Create global participant (if not already exists)
    if not create_global_participant(participant, dry_run):
        return False

    # Create session participation
    if not create_session_participation(participant, dry_run):
        return False

    print(f"    Successfully migrated participant '{name}'")
    return True


def main():
    """Main function to parse arguments and migrate participants."""
    parser = argparse.ArgumentParser(
        description="Migrate legacy participants to global participant model"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )

    args = parser.parse_args()

    print("Starting participant migration...")
    if args.dry_run:
        print("[DRY RUN MODE - No changes will be made]\n")

    # Get legacy participants
    participants = get_legacy_participants()

    if not participants:
        print("No legacy participants found that need migration.")
        sys.exit(0)

    print(f"Found {len(participants)} legacy participant(s) to migrate:\n")

    # Migrate each participant
    success_count = 0
    for participant in participants:
        if migrate_participant(participant, args.dry_run):
            success_count += 1

    print(
        f"\nMigration complete: {success_count}/{len(participants)} participants migrated successfully"
    )

    if args.dry_run:
        print("\nThis was a dry run. Run without --dry-run to apply changes.")
        sys.exit(0)

    if success_count == len(participants):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
