#!/bin/bash

# Script to build and deploy the frontend to S3 and invalidate CloudFront cache

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting frontend deployment...${NC}"

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Change to frontend directory
cd "$PROJECT_ROOT/frontend"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    npm install
fi

# Build the frontend
echo -e "${YELLOW}Building frontend...${NC}"
npm run build

# Get the S3 bucket name and CloudFront distribution ID from CDK outputs
cd "$PROJECT_ROOT/cdk"

echo -e "${YELLOW}Getting CDK stack outputs...${NC}"
BUCKET_NAME=$(aws cloudformation describe-stacks \
    --stack-name MusicQuizStack \
    --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" \
    --output text)

DISTRIBUTION_ID=$(aws cloudformation describe-stacks \
    --stack-name MusicQuizStack \
    --query "Stacks[0].Outputs[?OutputKey=='FrontendDistributionId'].OutputValue" \
    --output text)

if [ -z "$BUCKET_NAME" ]; then
    echo -e "${RED}Error: Could not find FrontendBucketName in stack outputs${NC}"
    exit 1
fi

if [ -z "$DISTRIBUTION_ID" ]; then
    echo -e "${RED}Error: Could not find FrontendDistributionId in stack outputs${NC}"
    exit 1
fi

echo -e "${GREEN}Bucket: $BUCKET_NAME${NC}"
echo -e "${GREEN}Distribution: $DISTRIBUTION_ID${NC}"

# Upload to S3
echo -e "${YELLOW}Uploading files to S3...${NC}"
aws s3 sync "$PROJECT_ROOT/frontend/dist" "s3://$BUCKET_NAME" \
    --delete \
    --cache-control "public, max-age=31536000, immutable" \
    --exclude "index.html"

# Upload index.html with no-cache
echo -e "${YELLOW}Uploading index.html with no-cache...${NC}"
aws s3 cp "$PROJECT_ROOT/frontend/dist/index.html" "s3://$BUCKET_NAME/index.html" \
    --cache-control "public, max-age=0, must-revalidate"

# Invalidate CloudFront cache
echo -e "${YELLOW}Invalidating CloudFront cache...${NC}"
INVALIDATION_ID=$(aws cloudfront create-invalidation \
    --distribution-id "$DISTRIBUTION_ID" \
    --paths "/*" \
    --query "Invalidation.Id" \
    --output text)

echo -e "${GREEN}CloudFront invalidation created: $INVALIDATION_ID${NC}"
echo -e "${GREEN}Frontend deployment complete!${NC}"
echo -e "${GREEN}URL: https://katrins-music-quiz.kornis.bayern${NC}"
