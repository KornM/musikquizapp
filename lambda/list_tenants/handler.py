"""
List Tenants Lambda Handler

This Lambda function handles listing all tenants for the Music Quiz application.
It retrieves all tenants from the Tenants table with optional status filtering.

Endpoint: GET /super-admin/tenants
"""

import json
import os
import sys

# Add common utilities to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))

from cors import add_cors_headers
from errors import error_response
from db import scan, query


# Environment variables
TENANTS_TABLE = os.environ.get("TENANTS_TABLE", "Tenants")


def lambda_handler(event, context):
    """
    Handle tenant listing requests.

    Query Parameters:
        status (optional): Filter tenants by status (e.g., "active", "inactive")

    Returns:
        Success (200):
            {
                "tenants": [
                    {
                        "tenantId": "uuid",
                        "name": "Tenant Name",
                        "status": "active",
                        "createdAt": "2024-01-01T00:00:00.000Z"
                    },
                    ...
                ]
            }

        Error (500): Internal server error
    """
    try:
        # Get optional status filter from query parameters
        status_filter = None
        if event.get("queryStringParameters"):
            status_filter = event["queryStringParameters"].get("status")

        # Query tenants
        try:
            if status_filter:
                # Use StatusIndex GSI to filter by status
                tenants = query(
                    TENANTS_TABLE,
                    "#status = :status",
                    {":status": status_filter},
                    index_name="StatusIndex",
                    expression_attribute_names={"#status": "status"},
                )
            else:
                # Scan all tenants
                tenants = scan(TENANTS_TABLE)
        except Exception as e:
            print(f"DynamoDB query/scan error: {str(e)}")
            return error_response(500, "DATABASE_ERROR", "Failed to retrieve tenants")

        # Format response - include only necessary fields
        formatted_tenants = []
        for tenant in tenants:
            formatted_tenants.append(
                {
                    "tenantId": tenant.get("tenantId"),
                    "name": tenant.get("name"),
                    "description": tenant.get("description", ""),
                    "status": tenant.get("status"),
                    "createdAt": tenant.get("createdAt"),
                }
            )

        # Return success response
        response = {
            "statusCode": 200,
            "body": json.dumps({"tenants": formatted_tenants}),
        }

        return add_cors_headers(response)

    except Exception as e:
        # Log unexpected errors
        print(f"Unexpected error in list tenants: {str(e)}")
        import traceback

        traceback.print_exc()

        return error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")
