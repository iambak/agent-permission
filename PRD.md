# Agent Permission API - Product Requirements Document

## Overview
**Project**: Agent Permission API
**Type**: Mock API for agent access control
**Purpose**: Allow general agents to check if users have access to specialized agents before invoking them

## Goals
- Provide permission checking for specialized agent invocation
- Enable general agents to verify user access before delegating tasks
- Simple lookup system using S3 as mock database
- Deploy on AWS for reliable access

## API Endpoints

### User Management
- `GET /users/{user_id}` - Check if user exists
- `POST /users` - Create new user with empty permissions

### Permission Management
- `GET /permissions/{user_id}` - Get all agents a user has access to
- `POST /permissions/{user_id}/agents` - Add agent permission to user

## Data Models

### Permission Response
```json
{
  "user_id": "user_123",
  "permitted_agents": [
    "code-reviewer",
    "data-analyst",
    "image-generator",
    "pdf-processor"
  ]
}
```

### S3 JSON Structure (permissions.json)
```json
{
  "last_updated": "2024-01-01T00:00:00Z",
  "permissions": {
    "user_123": ["code-reviewer", "data-analyst", "image-generator"],
    "user_456": ["code-reviewer"],
    "user_789": ["data-analyst", "pdf-processor"]
  }
}
```

## Response Formats

### Success Response
```json
{
  "status": "success",
  "data": {
    "user_id": "user_123",
    "permitted_agents": ["code-reviewer", "data-analyst"]
  }
}
```

### Error Response - User Not Found
```json
{
  "status": "error",
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "User was not found in the system",
    "user_id": "invalid_user_123"
  }
}
```

### Error Response - Service Error
```json
{
  "status": "error",
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "Unable to retrieve permissions at this time"
  }
}
```

## Sample Requests/Responses

### GET /permissions/user_123
**Response (Success):**
```json
{
  "status": "success",
  "data": {
    "user_id": "user_123",
    "permitted_agents": ["code-reviewer", "data-analyst", "image-generator"]
  }
}
```

### GET /permissions/invalid_user
**Response (User Not Found):**
```json
{
  "status": "error",
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "User was not found in the system",
    "user_id": "invalid_user"
  }
}
```

### POST /permissions/user_123/agents
**Request:**
```json
{
  "agent_name": "code-reviewer"
}
```

**Response (Existing User - Permission Added):**
```json
{
  "status": "success",
  "data": {
    "user_id": "user_123",
    "agent_added": "code-reviewer",
    "permitted_agents": ["data-analyst", "image-generator", "code-reviewer"]
  },
  "message": "Permission added successfully"
}
```

**Response (New User - User Created):**
```json
{
  "status": "success",
  "data": {
    "user_id": "new_user_456",
    "agent_added": "code-reviewer",
    "permitted_agents": ["code-reviewer"]
  },
  "message": "User created and permission added successfully"
}
```

**Response (Permission Already Exists):**
```json
{
  "status": "success",
  "data": {
    "user_id": "user_123",
    "agent_added": "code-reviewer",
    "permitted_agents": ["code-reviewer", "data-analyst"]
  },
  "message": "Permission already exists"
}
```

## Error Handling

### Error Codes
- **USER_NOT_FOUND**: User ID doesn't exist in permissions data
- **SERVICE_UNAVAILABLE**: S3 connection issues or API service problems
- **INVALID_REQUEST**: Malformed user_id or request format

### Error Response Strategy
- Descriptive error messages for agents to relay to users
- Clear error codes for programmatic handling
- Include relevant context (user_id, timestamp) when appropriate

## AWS Deployment

### Architecture
- **API Gateway**: REST API endpoints with CORS enabled
- **Lambda Function**: Python function to handle permission checks
- **S3 Bucket**: JSON file storage for permissions data
- **IAM Role**: Lambda execution role with S3 read permissions

### S3 Setup
- Bucket: `agent-permissions-data`
- File: `permissions.json`
- Public read access not required (Lambda access only)

### Lambda Function Requirements
- Runtime: Python 3.11 or later
- Memory: 128 MB (sufficient for JSON parsing)
- Timeout: 15 seconds (increased for S3 write operations)
- Environment variables: `S3_BUCKET_NAME`, `S3_FILE_KEY`
- Dependencies: boto3 (AWS SDK for Python)
- IAM Permissions: S3 read/write access to permissions bucket

### API Gateway Configuration
- REST API (not HTTP API for simplicity)
- Resources:
  - `/permissions/{user_id}` - GET method
  - `/permissions/{user_id}/agents` - POST method
- CORS enabled for cross-origin requests
- No authentication required (public endpoints for now)

## Usage Flow

### Permission Checking Flow
1. General agent receives user request requiring specialized agent
2. General agent calls `GET /permissions/{user_id}`
3. API checks S3 JSON for user permissions
4. If user found: returns list of permitted agents
5. If user not found: returns descriptive error
6. General agent uses response to either:
   - Invoke specialized agent if permitted
   - Return error message to user if not permitted

### Permission Adding Flow
1. General agent determines user needs access to specific agent
2. General agent calls `POST /permissions/{user_id}/agents` with agent name
3. API logic:
   - Reads current S3 JSON file
   - If user exists: adds agent to their permission list (if not already there)
   - If user doesn't exist: creates new user entry with the agent permission
   - Updates S3 JSON file with new permissions
4. Returns success response with updated permission list

## Local Testing

### AWS SAM Local Testing
The application uses AWS SAM Local for local development and testing:

**Prerequisites:**
- Install AWS SAM CLI: `brew install aws-sam-cli`
- Docker (for Lambda container simulation)

**Development Workflow:**
```bash
# Build the application
sam build

# Start local API Gateway + Lambda
sam local start-api --port 3000 --env-vars env.json

# Test endpoints
curl http://localhost:3000/users/user_123
```

**Key Features:**
- **Environment Detection**: Automatically uses local file storage in SAM Local, S3 in AWS
- **Lambda Simulation**: Exact same code runs locally and in production
- **API Gateway**: Full REST API simulation with CORS support

## Sample Implementation Notes
- Lambda fetches S3 file on each request (no caching for simplicity)
- JSON structure allows easy manual updates via S3 console
- Consider adding CloudWatch logging for debugging
- Future: Add DynamoDB for better performance at scale