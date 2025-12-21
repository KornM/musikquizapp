#!/usr/bin/env python3
"""
Migrate Answers to Multi-Tenant Script

This script migrates existing answers to the multi-tenant model by adding
tenantId and participationId fields. It looks up the session's tenantId and
the participant's participationId from SessionParticipations.

Usage:
    python scripts/migrate_answers.py
    python scripts/migrate_answers.py --dry-run
"""

import argparse
import sys
import os
from datetime import datetime

# Add lambda common directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lambda", "common"))

import boto3
from botocore.exceptions import ClientError

# Default tenant ID (must match setup_default_tenant.py)
DEFAULT_TENANT_ID = "00000000-0000-0000-0000-000000000001"


def get_answers_without_tenant(table_name="Answers"):
    """
    Query all answers that don't have a tenantId field.

    Args:
        table_name (str): DynamoDB table name

    Returns:
        list: List of answer items without tenantId
    """
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)

    try:
        # Scan for all answers
        response = table.scan()
        items = response.get("Items", [])

        # Handle pagination
        while "LastEvaluatedKey" in response:
            response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
            items.extend(response.get("Items", []))

        # Filter answers without tenantId
        answers_without_tenant = [
            answer
            for answer in items
            if "tenantId" not in answer or answer.get("tenantId") is None
        ]

        return answers_without_tenant
    except ClientError as e:
        print(f"Error querying answers: {str(e)}")
        return []


def get_session_tenant_id(session_id):
    """
    Look up the tenantId for a session.

    Args:
        session_id (str): Session ID

    Returns:
        str: Tenant ID or DEFAULT_TENANT_ID if not found
    """
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("QuizSessions")

    try:
        response = table.get_item(Key={"sessionId": session_id})
        if "Item" in response:
            return response["Item"].get("tenantId", DEFAULT_TENANT_ID)
        return DEFAULT_TENANT_ID
    except ClientError:
        return DEFAULT_TENANT_ID


def get_participation_id(participant_id, session_id):
    """
    Look up the participationId from SessionParticipations.

    Args:
        participant_id (str): Participant ID
        session_id (str): Session ID

    Returns:
        str: Participation ID or None if not found
    """
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("SessionParticipations")

    try:
        # Query by ParticipantIndex
        response = table.query(
            IndexName="ParticipantIndex",
            KeyConditionExpression="participantId = :pid",
            ExpressionAttributeValues={":pid": participant_id},
        )

        # Find the participation for this session
        for participation in response.get("Items", []):
            if participation.get("sessionId") == session_id:
                return participation.get("participationId")

        return None
    except ClientError as e:
        print(f"      Error looking up participation: {str(e)}")
        return None


def migrate_answer(answer, dry_run=False):
    """
    Migrate a single answer to the multi-tenant model.

    Args:
        answer (dict): Answer item to migrate
        dry_run (bool): If True, don't actually update the database

    Returns:
        bool: True if successful, False otherwise
    """
    answer_id = answer.get("answerId")
    participant_id = answer.get("participantId")
    session_id = answer.get("sessionId")

    print(f"  Migrating answer {answer_id}")

    # Look up session's tenantId
    tenant_id = get_session_tenant_id(session_id)
    print(f"    Session tenant: {tenant_id}")

    # Look up participationId
    participation_id = get_participation_id(participant_id, session_id)
    if not participation_id:
        print(
            f"    Warning: Could not find participationId for participant {participant_id} in session {session_id}"
        )
        print(f"    Skipping this answer")
        return False

    print(f"    Participation ID: {participation_id}")

    if dry_run:
        print(
            f"    [DRY RUN] Would set tenantId={tenant_id}, participationId={participation_id}"
        )
        return True

    # Update the answer record
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("Answers")

    try:
        table.update_item(
            Key={"answerId": answer_id},
            UpdateExpression="SET tenantId = :tenant_id, participationId = :participation_id",
            ExpressionAttributeValues={
                ":tenant_id": tenant_id,
                ":participation_id": participation_id,
            },
        )

        print(f"    Successfully migrated answer")
        return True
    except ClientError as e:
        print(f"    Error migrating answer: {str(e)}")
        return False


def main():
    """Main function to parse arguments and migrate answers."""
    parser = argparse.ArgumentParser(
        description="Migrate existing answers to multi-tenant model"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )

    args = parser.parse_args()

    print("Starting answer migration...")
    if args.dry_run:
        print("[DRY RUN MODE - No changes will be made]\n")

    # Get answers without tenant
    answers = get_answers_without_tenant()

    if not answers:
        print("No answers found that need migration.")
        sys.exit(0)

    print(f"Found {len(answers)} answer(s) to migrate:\n")

    # Migrate each answer
    success_count = 0
    skipped_count = 0
    for answer in answers:
        result = migrate_answer(answer, args.dry_run)
        if result:
            success_count += 1
        else:
            skipped_count += 1

    print(
        f"\nMigration complete: {success_count}/{len(answers)} answers migrated successfully"
    )
    if skipped_count > 0:
        print(f"Skipped {skipped_count} answers due to missing participation records")

    if args.dry_run:
        print("\nThis was a dry run. Run without --dry-run to apply changes.")
        sys.exit(0)

    if success_count == len(answers):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
