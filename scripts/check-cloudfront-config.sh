#!/bin/bash

# Script to check CloudFront distribution configuration

set -e

# Get the distribution ID
DISTRIBUTION_ID=$(aws cloudformation describe-stacks \
    --stack-name MusicQuizStack \
    --query "Stacks[0].Outputs[?OutputKey=='FrontendDistributionId'].OutputValue" \
    --output text)

echo "Distribution ID: $DISTRIBUTION_ID"
echo ""

# Get distribution config
echo "CloudFront Origin Configuration:"
aws cloudfront get-distribution --id "$DISTRIBUTION_ID" \
    --query "Distribution.DistributionConfig.Origins.Items[0]" \
    --output json | jq .

echo ""
echo "Checking for Origin Access Identity (OAI):"
aws cloudfront get-distribution --id "$DISTRIBUTION_ID" \
    --query "Distribution.DistributionConfig.Origins.Items[0].S3OriginConfig.OriginAccessIdentity" \
    --output text

echo ""
echo "Checking for Origin Access Control (OAC):"
aws cloudfront get-distribution --id "$DISTRIBUTION_ID" \
    --query "Distribution.DistributionConfig.Origins.Items[0].OriginAccessControlId" \
    --output text
