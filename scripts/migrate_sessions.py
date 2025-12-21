#!/usr/bin/env python3
"""
Migrate Sessions to Multi-Tenant Script

This script migrates existing quiz sessions to the multi-tenant model by adding
the tenantId field. All sessions are associated with the default tenant.

Usage:
    python scripts/migrate_sessions.py
    python scripts/migrate_sessions.py --table-name QuizSessions --dry-run
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


def get_sessions_without_tenant(table_name="QuizSessions"):
    """
    Query all sessions that don't have a tenantId field.

    Args:
        table_name (str): DynamoDB table name

    Returns:
        list: List of session items without tenantId
    """
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)

    try:
        # Scan for all sessions
        response = table.scan()
        items = response.get("Items", [])

        # Handle pagination
        while "LastEvaluatedKey" in response:
            response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
            items.extend(response.get("Items", []))

        # Filter sessions without tenantId
        sessions_without_tenant = [
            session
            for session in items
            if "tenantId" not in session or session.get("tenantId") is None
        ]

        return sessions_without_tenant
    except ClientError as e:
        print(f"Error querying sessions: {str(e)}")
        return []


def migrate_session(session, table_name="QuizSessions", dry_run=False):
    """
    Migrate a single session to the multi-tenant model.

    Args:
        session (dict): Session item to migrate
        table_name (str): DynamoDB table name
        dry_run (bool): If True, don't actually update the database

    Returns:
        bool: True if successful, False otherwise
    """
    session_id = session.get("sessionId")
    title = session.get("title", "Untitled")

    print(f"  Migrating session '{title}' (ID: {session_id})")

    if dry_run:
        print(f"    [DRY RUN] Would set tenantId={DEFAULT_TENANT_ID}")
        return True

    # Update the session record
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)

    try:
        table.update_item(
            Key={"sessionId": session_id},
            UpdateExpression="SET tenantId = :tenant_id, updatedAt = :updated_at",
            ExpressionAttributeValues={
                ":tenant_id": DEFAULT_TENANT_ID,
                ":updated_at": datetime.utcnow().isoformat(),
            },
        )

        print(f"    Successfully migrated session '{title}'")
        return True
    except ClientError as e:
        print(f"    Error migrating session '{title}': {str(e)}")
        return False


def main():
    """Main function to parse arguments and migrate sessions."""
    parser = argparse.ArgumentParser(
        description="Migrate existing sessions to multi-tenant model"
    )
    parser.add_argument(
        "--table-name",
        default="QuizSessions",
        help="DynamoDB table name (default: QuizSessions)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )

    args = parser.parse_args()

    print("Starting session migration...")
    if args.dry_run:
        print("[DRY RUN MODE - No changes will be made]\n")

    # Get sessions without tenant
    sessions = get_sessions_without_tenant(args.table_name)

    if not sessions:
        print("No sessions found that need migration.")
        sys.exit(0)

    print(f"Found {len(sessions)} session(s) to migrate:\n")

    # Migrate each session
    success_count = 0
    for session in sessions:
        if migrate_session(session, args.table_name, args.dry_run):
            success_count += 1

    print(
        f"\nMigration complete: {success_count}/{len(sessions)} sessions migrated successfully"
    )

    if args.dry_run:
        print("\nThis was a dry run. Run without --dry-run to apply changes.")
        sys.exit(0)

    if success_count == len(sessions):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
