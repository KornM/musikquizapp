#!/usr/bin/env python3
"""
Create Super Admin User Script

This script creates a super admin user in the DynamoDB Admins table.
Super admins have full system access and can manage tenants and tenant admins.

Usage:
    python scripts/create_super_admin.py --username superadmin --password yourpassword
    python scripts/create_super_admin.py --username superadmin --password yourpassword --email admin@example.com
"""

import argparse
import sys
import os
import uuid
from datetime import datetime

# Add lambda common directory to path for auth utilities
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lambda", "common"))

import boto3
from botocore.exceptions import ClientError
from auth import hash_password


def create_super_admin(username, password, email=None, table_name="Admins"):
    """
    Create a super admin user in DynamoDB.

    Args:
        username (str): Admin username
        password (str): Admin password (will be hashed)
        email (str, optional): Admin email address
        table_name (str): DynamoDB table name

    Returns:
        dict: Created admin user data
    """
    # Initialize DynamoDB client
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)

    # Check if username already exists
    try:
        response = table.query(
            IndexName="UsernameIndex",
            KeyConditionExpression="username = :username",
            ExpressionAttributeValues={":username": username},
        )

        if response.get("Items"):
            print(f"Error: Admin user '{username}' already exists")
            return None
    except ClientError as e:
        print(f"Error checking existing user: {str(e)}")
        return None

    # Generate admin ID and hash password
    admin_id = str(uuid.uuid4())
    password_hash = hash_password(password)
    created_at = datetime.utcnow().isoformat() + "Z"

    # Create admin item
    admin_item = {
        "adminId": admin_id,
        "username": username,
        "passwordHash": password_hash,
        "role": "super_admin",  # Super admin role
        # tenantId is intentionally omitted for super admins
        "createdAt": created_at,
        "updatedAt": created_at,
    }

    # Add email if provided
    if email:
        admin_item["email"] = email

    # Store in DynamoDB
    try:
        table.put_item(Item=admin_item)
        print(f"✓ Successfully created super admin user: {username}")
        print(f"✓ Admin ID: {admin_id}")
        print(f"✓ Role: super_admin")
        if email:
            print(f"✓ Email: {email}")
        return admin_item
    except ClientError as e:
        print(f"✗ Error creating super admin user: {str(e)}")
        return None


def main():
    """Main function to parse arguments and create super admin user."""
    parser = argparse.ArgumentParser(
        description="Create a super admin user in DynamoDB"
    )
    parser.add_argument("--username", required=True, help="Super admin username")
    parser.add_argument("--password", required=True, help="Super admin password")
    parser.add_argument("--email", help="Super admin email address (optional)")
    parser.add_argument(
        "--table-name",
        default="Admins",
        help="DynamoDB table name (default: Admins)",
    )

    args = parser.parse_args()

    # Validate inputs
    if len(args.username) < 3:
        print("✗ Error: Username must be at least 3 characters")
        sys.exit(1)

    if len(args.password) < 8:
        print("✗ Error: Password must be at least 8 characters")
        sys.exit(1)

    if args.email and "@" not in args.email:
        print("✗ Error: Invalid email address")
        sys.exit(1)

    print(f"\nCreating super admin user...")
    print(f"Username: {args.username}")
    if args.email:
        print(f"Email: {args.email}")
    print(f"Table: {args.table_name}")
    print()

    # Create super admin user
    result = create_super_admin(
        args.username, args.password, args.email, args.table_name
    )

    if result:
        print("\n" + "=" * 60)
        print("Super admin user created successfully!")
        print("=" * 60)
        print("\nYou can now:")
        print("1. Login with these credentials")
        print("2. Create tenants via the super admin UI")
        print("3. Create tenant admins for each tenant")
        print("\nKeep these credentials secure!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n✗ Failed to create super admin user.")
        sys.exit(1)


if __name__ == "__main__":
    main()
