"""
Lambda function to delete a round from a quiz session.
"""
import json
import os
import boto3
from botocore.exceptions import ClientError
from common.cors import cors_response
from common.auth import require_admin_auth
from common.errors import handle_error

dynamodb = boto3.resource("dynamodb")
s3 = boto3.client("s3")

SESSIONS_TABLE = os.environ["QUIZ_SESSIONS_TABLE"]
ROUNDS_TABLE = os.environ["QUIZ_ROUNDS_TABLE"]
AUDIO_BUCKET = os.environ["AUDIO_BUCKET"]


@require_admin_auth
def handler(event, context):
    """
    Delete a round from a quiz session.

    DELETE /admin/quiz-sessions/{sessionId}/rounds/{roundNumber}
    """
    try:
        session_id = event["pathParameters"]["sessionId"]
        round_number = int(event["pathParameters"]["roundNumber"])

        sessions_table = dynamodb.Table(SESSIONS_TABLE)
        rounds_table = dynamodb.Table(ROUNDS_TABLE)

        # Get the round to find the audio key
        round_response = rounds_table.get_item(
            Key={"sessionId": session_id, "roundNumber": round_number}
        )

        if "Item" not in round_response:
            return cors_response(404, {"error": {"message": "Round not found"}})

        round_item = round_response["Item"]

        # Delete audio file from S3 if it exists
        if "audioKey" in round_item:
            try:
                s3.delete_object(Bucket=AUDIO_BUCKET, Key=round_item["audioKey"])
            except ClientError as e:
                print(f"Error deleting audio file: {e}")
                # Continue with deletion even if S3 delete fails

        # Delete the round from DynamoDB
        rounds_table.delete_item(
            Key={"sessionId": session_id, "roundNumber": round_number}
        )

        # Update session's round count
        # Get all remaining rounds for this session
        remaining_rounds = rounds_table.query(
            KeyConditionExpression="sessionId = :sid",
            ExpressionAttributeValues={":sid": session_id},
        )

        new_round_count = remaining_rounds["Count"]

        # Update session
        sessions_table.update_item(
            Key={"sessionId": session_id},
            UpdateExpression="SET roundCount = :count",
            ExpressionAttributeValues={":count": new_round_count},
        )

        return cors_response(200, {"message": "Round deleted successfully"})

    except ValueError:
        return cors_response(400, {"error": {"message": "Invalid round number"}})
    except Exception as e:
        return handle_error(e)
