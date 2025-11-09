#!/bin/bash

# Script to remove the bucket policy so CDK can manage it

set -e

BUCKET_NAME="musicquizstack-frontendfrontendbucket428b8c09-ezs9huecyrmo"

echo "Bucket: $BUCKET_NAME"
echo ""

# Check current bucket policy
echo "Current bucket policy:"
aws s3api get-bucket-policy --bucket "$BUCKET_NAME" --query Policy --output text | jq . || echo "No policy found"
echo ""

# Delete the bucket policy
echo "Deleting bucket policy..."
aws s3api delete-bucket-policy --bucket "$BUCKET_NAME"

echo ""
echo "Bucket policy deleted successfully!"
echo ""
echo "Now redeploy the CDK stack to let it create the correct OAI-based policy:"
echo "  cd cdk && cdk deploy"
