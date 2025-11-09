"""
Get Audio Lambda Handler

This Lambda function generates presigned URLs for audio files stored in S3.

Endpoint: GET /audio/{audioKey}
"""
import json
import os
import sys

# Add common utilities to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))

from cors import add_cors_headers
from errors import error_response
import boto3
from botocore.exceptions import ClientError


# Environment variables
AUDIO_BUCKET = os.environ.get("AUDIO_BUCKET", "music-quiz-audio")

# Initialize S3 client
s3_client = boto3.client("s3")


def lambda_handler(event, context):
    """
    Handle get audio requests.

    Expected path parameters:
        audioKey: S3 object key (URL encoded)

    Returns:
        Success (200):
            {
                "url": "presigned_s3_url"
            }

        Or redirect (302) to presigned URL

        Error (400): Missing audio key
        Error (404): Audio file not found
        Error (500): Internal server error
    """
    try:
        # Extract audio key from path parameters
        path_parameters = event.get("pathParameters", {})
        audio_key = path_parameters.get("audioKey")

        if not audio_key:
            return error_response(
                400, "MISSING_AUDIO_KEY", "Audio key is required in path"
            )

        # Check if object exists in S3
        try:
            s3_client.head_object(Bucket=AUDIO_BUCKET, Key=audio_key)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "404" or error_code == "NoSuchKey":
                return error_response(
                    404, "AUDIO_NOT_FOUND", f"Audio file {audio_key} not found"
                )
            print(f"S3 head_object error: {str(e)}")
            return error_response(
                500, "STORAGE_ERROR", "Failed to check audio file existence"
            )

        # Generate presigned URL (valid for 1 hour)
        try:
            presigned_url = s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": AUDIO_BUCKET, "Key": audio_key},
                ExpiresIn=3600,
            )
        except ClientError as e:
            print(f"Presigned URL generation error: {str(e)}")
            return error_response(
                500, "URL_GENERATION_ERROR", "Failed to generate audio URL"
            )

        # Return redirect response
        response = {
            "statusCode": 302,
            "headers": {"Location": presigned_url},
            "body": json.dumps({"url": presigned_url}),
        }

        return add_cors_headers(response)

    except Exception as e:
        # Log unexpected errors
        print(f"Unexpected error in get audio: {str(e)}")
        import traceback

        traceback.print_exc()

        return error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")
