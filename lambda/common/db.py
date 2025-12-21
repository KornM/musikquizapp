"""
Database utility module for DynamoDB operations.
"""

import boto3
from botocore.exceptions import ClientError


# Initialize DynamoDB client
dynamodb = boto3.resource("dynamodb")


def get_item(table_name, key):
    """
    Get a single item from a DynamoDB table.

    Args:
        table_name (str): Name of the DynamoDB table
        key (dict): Primary key of the item to retrieve

    Returns:
        dict: Item data if found, None otherwise

    Raises:
        ClientError: If DynamoDB operation fails
    """
    try:
        table = dynamodb.Table(table_name)
        response = table.get_item(Key=key)
        return response.get("Item")
    except ClientError as e:
        raise ClientError(error_response=e.response, operation_name="GetItem")


def put_item(table_name, item):
    """
    Put an item into a DynamoDB table.

    Args:
        table_name (str): Name of the DynamoDB table
        item (dict): Item data to store

    Returns:
        dict: Response from DynamoDB

    Raises:
        ClientError: If DynamoDB operation fails
    """
    try:
        table = dynamodb.Table(table_name)
        response = table.put_item(Item=item)
        return response
    except ClientError as e:
        raise ClientError(error_response=e.response, operation_name="PutItem")


def delete_item(table_name, key):
    """
    Delete an item from a DynamoDB table.

    Args:
        table_name (str): Name of the DynamoDB table
        key (dict): Primary key of the item to delete

    Returns:
        dict: Response from DynamoDB

    Raises:
        ClientError: If DynamoDB operation fails
    """
    try:
        table = dynamodb.Table(table_name)
        response = table.delete_item(Key=key)
        return response
    except ClientError as e:
        raise ClientError(error_response=e.response, operation_name="DeleteItem")


def query(
    table_name,
    key_condition_expression,
    expression_attribute_values,
    index_name=None,
    expression_attribute_names=None,
):
    """
    Query items from a DynamoDB table.

    Args:
        table_name (str): Name of the DynamoDB table
        key_condition_expression (str): Key condition expression for the query
        expression_attribute_values (dict): Values for the expression
        index_name (str, optional): Name of GSI to query
        expression_attribute_names (dict, optional): Attribute name mappings

    Returns:
        list: List of items matching the query

    Raises:
        ClientError: If DynamoDB operation fails
    """
    try:
        table = dynamodb.Table(table_name)

        query_params = {
            "KeyConditionExpression": key_condition_expression,
            "ExpressionAttributeValues": expression_attribute_values,
        }

        if index_name:
            query_params["IndexName"] = index_name

        if expression_attribute_names:
            query_params["ExpressionAttributeNames"] = expression_attribute_names

        response = table.query(**query_params)
        return response.get("Items", [])
    except ClientError as e:
        raise ClientError(error_response=e.response, operation_name="Query")


def scan(table_name, filter_expression=None, expression_attribute_values=None):
    """
    Scan all items from a DynamoDB table.

    Args:
        table_name (str): Name of the DynamoDB table
        filter_expression (str, optional): Filter expression for the scan
        expression_attribute_values (dict, optional): Values for the expression

    Returns:
        list: List of all items in the table

    Raises:
        ClientError: If DynamoDB operation fails
    """
    try:
        table = dynamodb.Table(table_name)

        scan_params = {}

        if filter_expression:
            scan_params["FilterExpression"] = filter_expression

        if expression_attribute_values:
            scan_params["ExpressionAttributeValues"] = expression_attribute_values

        response = table.scan(**scan_params)
        items = response.get("Items", [])

        # Handle pagination
        while "LastEvaluatedKey" in response:
            scan_params["ExclusiveStartKey"] = response["LastEvaluatedKey"]
            response = table.scan(**scan_params)
            items.extend(response.get("Items", []))

        return items
    except ClientError as e:
        raise ClientError(error_response=e.response, operation_name="Scan")


def update_item(
    table_name,
    key,
    update_expression,
    expression_attribute_values,
    expression_attribute_names=None,
):
    """
    Update an item in a DynamoDB table.

    Args:
        table_name (str): Name of the DynamoDB table
        key (dict): Primary key of the item to update
        update_expression (str): Update expression
        expression_attribute_values (dict): Values for the expression
        expression_attribute_names (dict, optional): Attribute name mappings

    Returns:
        dict: Updated item attributes

    Raises:
        ClientError: If DynamoDB operation fails
    """
    try:
        table = dynamodb.Table(table_name)

        update_params = {
            "Key": key,
            "UpdateExpression": update_expression,
            "ExpressionAttributeValues": expression_attribute_values,
            "ReturnValues": "ALL_NEW",
        }

        if expression_attribute_names:
            update_params["ExpressionAttributeNames"] = expression_attribute_names

        response = table.update_item(**update_params)
        return response.get("Attributes")
    except ClientError as e:
        raise ClientError(error_response=e.response, operation_name="UpdateItem")


def validate_tenant_access(resource_tenant_id, user_tenant_id, user_role):
    """
    Validate that a user has access to a resource based on tenant isolation.

    Args:
        resource_tenant_id (str): Tenant ID of the resource being accessed
        user_tenant_id (str): Tenant ID of the user making the request
        user_role (str): Role of the user (super_admin, tenant_admin, admin)

    Returns:
        bool: True if access is allowed, False otherwise
    """
    # Super admins can access all resources
    if user_role == "super_admin":
        return True

    # If resource has no tenant ID, allow access (backward compatibility)
    if not resource_tenant_id:
        return True

    # If user has no tenant ID, deny access to tenant-specific resources
    if not user_tenant_id:
        return False

    # Tenant admins can only access resources from their tenant
    return resource_tenant_id == user_tenant_id
