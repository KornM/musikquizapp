#!/usr/bin/env python3
"""
Create Initial Admin User Script

This script creates an initial admin user in the DynamoDB Admins table.
Run this after CDK deployment to bootstrap admin access.

Usage:
    python scripts/create_admin.py --username admin --password yourpassword
    python scripts/create_admin.py --username admin --password yourpassword --table-name Admins
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


def create_admin_user(username, password, table_name="Admins"):
    """
    Create an admin user in DynamoDB.

    Args:
        username (str): Admin username
        password (str): Admin password (will be hashed)
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
    created_at = str(int(datetime.utcnow().timestamp()))

    # Create admin item
    admin_item = {
        "adminId": admin_id,
        "username": username,
        "passwordHash": password_hash,
        "createdAt": created_at,
    }

    # Store in DynamoDB
    try:
        table.put_item(Item=admin_item)
        print(f"Successfully created admin user: {username}")
        print(f"Admin ID: {admin_id}")
        return admin_item
    except ClientError as e:
        print(f"Error creating admin user: {str(e)}")
        return None


def main():
    """Main function to parse arguments and create admin user."""
    parser = argparse.ArgumentParser(
        description="Create an initial admin user in DynamoDB"
    )
    parser.add_argument("--username", required=True, help="Admin username")
    parser.add_argument("--password", required=True, help="Admin password")
    parser.add_argument(
        "--table-name",
        default="Admins",
        help="DynamoDB table name (default: Admins)",
    )

    args = parser.parse_args()

    # Validate inputs
    if len(args.username) < 3:
        print("Error: Username must be at least 3 characters")
        sys.exit(1)

    if len(args.password) < 8:
        print("Error: Password must be at least 8 characters")
        sys.exit(1)

    # Create admin user
    result = create_admin_user(args.username, args.password, args.table_name)

    if result:
        print("\nAdmin user created successfully!")
        print("You can now login with these credentials.")
        sys.exit(0)
    else:
        print("\nFailed to create admin user.")
        sys.exit(1)


if __name__ == "__main__":
    main()
