#!/usr/bin/env python3
"""
Setup Default Tenant Script

This script creates a default tenant for backward compatibility with single-tenant deployments.
Run this during deployment if no tenants exist.

Usage:
    python scripts/setup_default_tenant.py
    python scripts/setup_default_tenant.py --table-name Tenants
"""

import argparse
import sys
import os
from datetime import datetime

# Add lambda common directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lambda", "common"))

import boto3
from botocore.exceptions import ClientError

# Well-known UUID for default tenant
DEFAULT_TENANT_ID = "00000000-0000-0000-0000-000000000001"
DEFAULT_TENANT_NAME = "Default Organization"


def check_tenants_exist(table_name="Tenants"):
    """
    Check if any tenants already exist in the database.

    Args:
        table_name (str): DynamoDB table name

    Returns:
        bool: True if tenants exist, False otherwise
    """
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)

    try:
        response = table.scan(Limit=1)
        return len(response.get("Items", [])) > 0
    except ClientError as e:
        print(f"Error checking for existing tenants: {str(e)}")
        return False


def create_default_tenant(table_name="Tenants"):
    """
    Create the default tenant in DynamoDB.

    Args:
        table_name (str): DynamoDB table name

    Returns:
        dict: Created tenant data or None if failed
    """
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)

    # Check if default tenant already exists
    try:
        response = table.get_item(Key={"tenantId": DEFAULT_TENANT_ID})
        if "Item" in response:
            print(f"Default tenant already exists with ID: {DEFAULT_TENANT_ID}")
            return response["Item"]
    except ClientError as e:
        print(f"Error checking for default tenant: {str(e)}")
        return None

    # Create default tenant
    created_at = datetime.utcnow().isoformat()
    tenant_item = {
        "tenantId": DEFAULT_TENANT_ID,
        "name": DEFAULT_TENANT_NAME,
        "description": "Default tenant for backward compatibility",
        "status": "active",
        "createdAt": created_at,
        "updatedAt": created_at,
        "settings": {},
    }

    try:
        table.put_item(Item=tenant_item)
        print(f"Successfully created default tenant: {DEFAULT_TENANT_NAME}")
        print(f"Tenant ID: {DEFAULT_TENANT_ID}")
        return tenant_item
    except ClientError as e:
        print(f"Error creating default tenant: {str(e)}")
        return None


def main():
    """Main function to parse arguments and create default tenant."""
    parser = argparse.ArgumentParser(
        description="Create default tenant for backward compatibility"
    )
    parser.add_argument(
        "--table-name",
        default="Tenants",
        help="DynamoDB table name (default: Tenants)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Create default tenant even if other tenants exist",
    )

    args = parser.parse_args()

    # Check if tenants already exist
    if not args.force and check_tenants_exist(args.table_name):
        print("Tenants already exist. Skipping default tenant creation.")
        print("Use --force to create default tenant anyway.")
        sys.exit(0)

    # Create default tenant
    result = create_default_tenant(args.table_name)

    if result:
        print("\nDefault tenant created successfully!")
        print("This tenant can be used for backward compatibility with existing data.")
        sys.exit(0)
    else:
        print("\nFailed to create default tenant.")
        sys.exit(1)


if __name__ == "__main__":
    main()
