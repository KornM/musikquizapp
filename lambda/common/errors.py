"""
Error handling utility module for consistent error responses across Lambda functions.
"""
import json
import sys
import os

# Add common directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from cors import add_cors_headers


def error_response(status_code, error_code, message, details=None):
    """
    Create a standardized error response with CORS headers.

    This function generates a consistent JSON error response format that includes
    appropriate HTTP status codes and CORS headers.

    Args:
        status_code (int): HTTP status code (e.g., 400, 401, 404, 500)
        error_code (str): Application-specific error code (e.g., 'INVALID_TOKEN')
        message (str): Human-readable error message
        details (dict, optional): Additional error details

    Returns:
        dict: Lambda response dictionary with error body and CORS headers
    """
    response = {
        "statusCode": status_code,
        "body": json.dumps(
            {
                "error": {
                    "code": error_code,
                    "message": message,
                    "details": details or {},
                }
            }
        ),
    }

    return add_cors_headers(response)
