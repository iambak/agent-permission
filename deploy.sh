#!/bin/bash

# AWS SAM deployment script for Agent Permission API

set -e

# Configuration
STACK_NAME="agent-permission-api"
REGION="us-east-1"
ENVIRONMENT="dev"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Deploying Agent Permission API to AWS${NC}"
echo "Stack: $STACK_NAME"
echo "Region: $REGION"
echo "Environment: $ENVIRONMENT"
echo ""

# Check if SAM CLI is installed
if ! command -v sam &> /dev/null; then
    echo -e "${RED}❌ AWS SAM CLI is not installed. Please install it first.${NC}"
    echo "Install guide: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html"
    exit 1
fi

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not configured. Please run 'aws configure' first.${NC}"
    exit 1
fi

echo -e "${YELLOW}🔨 Building SAM application...${NC}"
sam build

echo -e "${YELLOW}📦 Deploying to AWS...${NC}"
sam deploy \
    --stack-name $STACK_NAME \
    --region $REGION \
    --parameter-overrides Environment=$ENVIRONMENT \
    --capabilities CAPABILITY_IAM \
    --confirm-changeset \
    --resolve-s3

echo ""
echo -e "${GREEN}✅ Deployment complete!${NC}"

# Get the API endpoint
API_URL=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`AgentPermissionApi`].OutputValue' \
    --output text)

echo ""
echo -e "${GREEN}🌐 Your API is live at:${NC}"
echo "   $API_URL"
echo ""
echo -e "${YELLOW}📋 Test your API:${NC}"
echo "   curl $API_URL/users/user_123"
echo ""
echo -e "${YELLOW}🗑️  To delete the stack:${NC}"
echo "   aws cloudformation delete-stack --stack-name $STACK_NAME --region $REGION"