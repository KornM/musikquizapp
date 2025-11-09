#!/bin/bash

# Script to check and fix S3 bucket policy for CloudFront access

set -e

BUCKET_NAME="musicquizstack-frontendfrontendbucket428b8c09-ezs9huecyrmo"

# Get the distribution ID
DISTRIBUTION_ID=$(aws cloudformation describe-stacks \
    --stack-name MusicQuizStack \
    --query "Stacks[0].Outputs[?OutputKey=='FrontendDistributionId'].OutputValue" \
    --output text)

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "Bucket: $BUCKET_NAME"
echo "Distribution ID: $DISTRIBUTION_ID"
echo "Account ID: $ACCOUNT_ID"
echo ""

# Check current bucket policy
echo "Current bucket policy:"
aws s3api get-bucket-policy --bucket "$BUCKET_NAME" --query Policy --output text | jq . || echo "No policy found"
echo ""

# Create the correct bucket policy
cat > /tmp/bucket-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowCloudFrontServicePrincipalReadOnly",
      "Effect": "Allow",
      "Principal": {
        "Service": "cloudfront.amazonaws.com"
      },
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::${BUCKET_NAME}/*",
      "Condition": {
        "StringEquals": {
          "AWS:SourceArn": "arn:aws:cloudfront::${ACCOUNT_ID}:distribution/${DISTRIBUTION_ID}"
        }
      }
    }
  ]
}
EOF

echo "Applying new bucket policy..."
aws s3api put-bucket-policy --bucket "$BUCKET_NAME" --policy file:///tmp/bucket-policy.json

echo ""
echo "New bucket policy applied successfully!"
echo ""

# Verify the policy
echo "Verifying new policy:"
aws s3api get-bucket-policy --bucket "$BUCKET_NAME" --query Policy --output text | jq .

# List files in bucket
echo ""
echo "Files in bucket:"
aws s3 ls "s3://$BUCKET_NAME/" --recursive

echo ""
echo "Done! Try accessing the CloudFront distribution now."
