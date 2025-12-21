#!/usr/bin/env python3
"""
Migrate Admins to Multi-Tenant Script

This script migrates existing admin users to the multi-tenant model by adding
tenantId and role fields. The first admin becomes a super_admin, and subsequent
admins become tenant_admins associated with the default tenant.

Usage:
    python scripts/migrate_admins.py
    python scripts/migrate_admins.py --table-name Admins --dry-run
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


def get_admins_without_tenant(table_name="Admins"):
    """
    Query all admins that don't have a tenantId field.

    Args:
        table_name (str): DynamoDB table name

    Returns:
        list: List of admin items without tenantId
    """
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)

    try:
        # Scan for all admins
        response = table.scan()
        items = response.get("Items", [])

        # Handle pagination
        while "LastEvaluatedKey" in response:
            response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
            items.extend(response.get("Items", []))

        # Filter admins without tenantId
        admins_without_tenant = [
            admin
            for admin in items
            if "tenantId" not in admin or admin.get("tenantId") is None
        ]

        return admins_without_tenant
    except ClientError as e:
        print(f"Error querying admins: {str(e)}")
        return []


def migrate_admin(admin, is_first_admin, table_name="Admins", dry_run=False):
    """
    Migrate a single admin to the multi-tenant model.

    Args:
        admin (dict): Admin item to migrate
        is_first_admin (bool): Whether this is the first admin (becomes super_admin)
        table_name (str): DynamoDB table name
        dry_run (bool): If True, don't actually update the database

    Returns:
        bool: True if successful, False otherwise
    """
    admin_id = admin.get("adminId")
    username = admin.get("username", "unknown")

    # Determine role and tenantId
    if is_first_admin:
        role = "super_admin"
        tenant_id = None  # Super admins don't have a tenant
        print(f"  Migrating {username} (ID: {admin_id}) as super_admin")
    else:
        role = "tenant_admin"
        tenant_id = DEFAULT_TENANT_ID
        print(
            f"  Migrating {username} (ID: {admin_id}) as tenant_admin for default tenant"
        )

    if dry_run:
        print(f"    [DRY RUN] Would set role={role}, tenantId={tenant_id}")
        return True

    # Update the admin record
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)

    try:
        # Use timezone-aware datetime
        from datetime import timezone

        updated_at = datetime.now(timezone.utc).isoformat()

        # Ensure createdAt is in string format for GSI compatibility
        created_at = admin.get("createdAt")
        if isinstance(created_at, (int, float)):
            # Convert Unix timestamp to ISO string
            created_at_dt = datetime.fromtimestamp(float(created_at), tz=timezone.utc)
            created_at = created_at_dt.isoformat()
        elif not isinstance(created_at, str):
            # Fallback to current time if createdAt is missing or invalid
            created_at = updated_at

        update_expression = (
            "SET #role = :role, updatedAt = :updated_at, createdAt = :created_at"
        )
        expression_attribute_values = {
            ":role": role,
            ":updated_at": updated_at,
            ":created_at": created_at,
        }
        expression_attribute_names = {"#role": "role"}

        # Add tenantId for tenant admins (but not for super admins)
        # Super admins should not have tenantId to avoid GSI issues
        if tenant_id is not None:
            update_expression += ", tenantId = :tenant_id"
            expression_attribute_values[":tenant_id"] = tenant_id

        table.update_item(
            Key={"adminId": admin_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ExpressionAttributeNames=expression_attribute_names,
        )
        print(f"    Successfully migrated {username}")
        return True
    except ClientError as e:
        print(f"    Error migrating {username}: {str(e)}")
        return False


def main():
    """Main function to parse arguments and migrate admins."""
    parser = argparse.ArgumentParser(
        description="Migrate existing admins to multi-tenant model"
    )
    parser.add_argument(
        "--table-name",
        default="Admins",
        help="DynamoDB table name (default: Admins)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )

    args = parser.parse_args()

    print("Starting admin migration...")
    if args.dry_run:
        print("[DRY RUN MODE - No changes will be made]\n")

    # Get admins without tenant
    admins = get_admins_without_tenant(args.table_name)

    if not admins:
        print("No admins found that need migration.")
        sys.exit(0)

    print(f"Found {len(admins)} admin(s) to migrate:\n")

    # Sort admins by createdAt to determine first admin
    # Handle both string (ISO format) and Decimal (Unix timestamp) formats
    def get_sort_key(admin):
        created_at = admin.get("createdAt", "")
        if isinstance(created_at, (int, float)):
            # Unix timestamp (Decimal or int)
            return float(created_at)
        elif isinstance(created_at, str):
            # ISO format string - convert to timestamp for sorting
            try:
                from datetime import datetime

                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                return dt.timestamp()
            except:
                return 0
        return 0

    admins.sort(key=get_sort_key)

    # Migrate each admin
    success_count = 0
    for i, admin in enumerate(admins):
        is_first = i == 0
        if migrate_admin(admin, is_first, args.table_name, args.dry_run):
            success_count += 1

    print(
        f"\nMigration complete: {success_count}/{len(admins)} admins migrated successfully"
    )

    if args.dry_run:
        print("\nThis was a dry run. Run without --dry-run to apply changes.")
        sys.exit(0)

    if success_count == len(admins):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
