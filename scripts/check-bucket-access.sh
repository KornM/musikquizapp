#!/bin/bash

# Script to check S3 bucket access and policy

set -e

# Get bucket name from CDK outputs
BUCKET_NAME=$(aws cloudformation describe-stacks \
    --stack-name MusicQuizStack \
    --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" \
    --output text)

echo "Bucket Name: $BUCKET_NAME"
echo ""

# Check if bucket exists
echo "Checking if bucket exists..."
aws s3 ls "s3://$BUCKET_NAME" || echo "Bucket is empty or doesn't exist"
echo ""

# Get bucket policy
echo "Current bucket policy:"
aws s3api get-bucket-policy --bucket "$BUCKET_NAME" --query Policy --output text | jq . || echo "No bucket policy found"
echo ""

# List files in bucket
echo "Files in bucket:"
aws s3 ls "s3://$BUCKET_NAME" --recursive || echo "No files found"
