# Agent Permission API

A serverless API for managing user permissions to access specialized AI agents. This API allows general-purpose AI agents to check user permissions before invoking specialized agents.

## 🚀 Live API

**Base URL**: `https://kpfnbcvnfb.execute-api.us-east-1.amazonaws.com/dev/`

## 📋 Quick Start for AI Agents

### Basic Permission Check
```bash
# Check if user has permissions
curl "https://kpfnbcvnfb.execute-api.us-east-1.amazonaws.com/dev/permissions/abhinav"

# Response: List of permitted agents
{
  "status": "success",
  "data": {
    "user_id": "abhinav",
    "permitted_agents": []
  }
}
```

### User Profile Management
```bash
# Get user profile
curl "https://kpfnbcvnfb.execute-api.us-east-1.amazonaws.com/dev/profiles/abhinav"

# Response: User profile details
{
  "status": "success",
  "data": {
    "user_id": "abhinav",
    "profile": {
      "email": "abhinav.thunderbolt@example.com",
      "first_name": "Abhinav",
      "last_name": "Thunderbolt",
      "role": "Day Trading Superhero",
      "bio": "Strikes the market like lightning with quick trades.",
      "created_at": "2025-09-15T09:00:00.000000"
    }
  }
}

# Create new profile (auto-generates user_id from first_name)
curl -X POST "https://kpfnbcvnfb.execute-api.us-east-1.amazonaws.com/dev/profiles" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com"
  }'
```

### Grant New Permission
```bash
# Add agent permission to user
curl -X POST "https://kpfnbcvnfb.execute-api.us-east-1.amazonaws.com/dev/permissions/abhinav/agents" \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "image-generator"}'

# Response: Updated permissions
{
  "status": "success",
  "data": {
    "user_id": "abhinav",
    "agent_added": "image-generator",
    "permitted_agents": ["image-generator"]
  },
  "message": "Permission added successfully"
}
```

## 🤖 AI Agent Integration Guide

### Permission Check Workflow

1. **Check User Permissions**
   ```python
   import requests

   def check_user_permission(user_id, agent_name):
       base_url = "https://kpfnbcvnfb.execute-api.us-east-1.amazonaws.com/dev"
       response = requests.get(f"{base_url}/permissions/{user_id}")

       if response.status_code == 200:
           data = response.json()
           return agent_name in data["data"]["permitted_agents"]
       elif response.status_code == 404:
           return False  # User not found
       else:
           raise Exception("Permission check failed")

   # Usage
   if check_user_permission("user_123", "code-reviewer"):
       # User has access - invoke specialized agent
       result = invoke_code_reviewer_agent(code)
   else:
       # User lacks permission
       return "You don't have access to the code-reviewer agent"
   ```

2. **Grant Permission (when needed)**
   ```python
   def grant_permission(user_id, agent_name):
       base_url = "https://kpfnbcvnfb.execute-api.us-east-1.amazonaws.com/dev"
       response = requests.post(
           f"{base_url}/permissions/{user_id}/agents",
           json={"agent_name": agent_name}
       )
       return response.status_code == 200
   ```

### Error Handling
```python
def safe_permission_check(user_id, agent_name):
    try:
        response = requests.get(f"{base_url}/permissions/{user_id}")

        if response.status_code == 200:
            data = response.json()
            return agent_name in data["data"]["permitted_agents"]
        elif response.status_code == 404:
            # User doesn't exist - optionally create them
            return False
        else:
            # Service error
            error_data = response.json()
            print(f"Error: {error_data['error']['message']}")
            return False

    except requests.RequestException:
        # Network error - fail gracefully
        print("Unable to check permissions at this time")
        return False
```

## 📖 API Documentation

### Complete API Contract

See [`api-contract.yaml`](./api-contract.yaml) for the complete OpenAPI 3.0 specification with:
- Detailed endpoint documentation
- Request/response schemas
- Example payloads
- Error codes and handling
- AI agent integration instructions

### Endpoints Overview

| Method | Endpoint | Purpose | AI Agent Use Case |
|--------|----------|---------|-------------------|
| `GET` | `/users/{user_id}` | Check if user exists | Validate user before operations |
| `POST` | `/users` | Create new user | Initialize new users |
| `GET` | `/permissions/{user_id}` | Get user's agent permissions | **Main endpoint**: Check before agent invocation |
| `POST` | `/permissions/{user_id}/agents` | Grant agent permission | Add new permissions when needed |
| `GET` | `/profiles` | List all user profiles | Get overview of all users |
| `GET` | `/profiles/{user_id}` | Get user profile details | Get detailed user information |
| `POST` | `/profiles` | Create user profile | Create profile with auto user_id generation |
| `PUT` | `/profiles/{user_id}` | Update user profile | Modify existing profile information |
| `DELETE` | `/profiles/{user_id}` | Delete user profile | Remove user profile |

### Response Format

All responses follow a consistent structure:

**Success Response:**
```json
{
  "status": "success",
  "data": { /* endpoint-specific data */ },
  "message": "Human-readable success message"
}
```

**Error Response:**
```json
{
  "status": "error",
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "user_id": "context_when_applicable"
  }
}
```

### Error Codes for AI Agents

| Code | Meaning | AI Agent Action |
|------|---------|----------------|
| `USER_NOT_FOUND` | User doesn't exist | Create user or inform them |
| `INVALID_REQUEST` | Malformed request | Fix request format |
| `SERVICE_UNAVAILABLE` | API is down | Retry later or fail gracefully |
| `USER_ALREADY_EXISTS` | User creation conflict | Continue with existing user |

## 🛠️ Local Development

### Prerequisites
- AWS SAM CLI: `brew install aws-sam-cli`
- Docker (for Lambda simulation)
- Python 3.9+

### Quick Start
```bash
# Clone and enter directory
git clone <repository-url>
cd agent-permission

# Build and start local API
sam build
sam local start-api --port 3000 --env-vars env.json

# Test locally
curl http://localhost:3000/permissions/user_123
```

### Environment Variables for Local Testing
Create `env.json`:
```json
{
  "Parameters": {
    "S3_BUCKET_NAME": "local-permissions",
    "S3_FILE_KEY": "permissions.json",
    "ENVIRONMENT": "local"
  }
}
```

## 🚀 Deployment

### Deploy to AWS
```bash
# Deploy using the provided script
./deploy.sh

# Or manually with SAM
sam build
sam deploy --guided
```

### Production Configuration
- **Region**: us-east-1
- **Stack Name**: agent-permission-api
- **S3 Bucket**: Auto-generated with versioning
- **Lambda**: Python 3.9, 128MB memory, 15s timeout

## 📊 Data Storage

### S3 Structure

**Permissions File (`permissions.json`)**
```json
{
  "last_updated": "2025-09-17T09:00:00.000000",
  "permissions": {
    "abhinav": [],
    "quang": [],
    "raghav": [],
    "venkat": [],
    "bak": []
  }
}
```

**User Profiles File (`user_profiles.json`)**
```json
{
  "last_updated": "2025-09-17T10:30:00.000000",
  "profiles": {
    "abhinav": {
      "email": "abhinav.thunderbolt@example.com",
      "first_name": "Abhinav",
      "last_name": "Thunderbolt",
      "phone": "",
      "company": "",
      "role": "Day Trading Superhero",
      "bio": "Strikes the market like lightning with quick trades. Known for electrifying gains and shocking comebacks.",
      "created_at": "2025-09-15T09:00:00.000000",
      "updated_at": "2025-09-15T09:00:00.000000"
    }
  }
}
```

### Data Management
- User IDs are stored in lowercase for consistency
- Agent names should be descriptive (e.g., "code-reviewer", not "cr")
- Files are automatically created if they don't exist
- Profile creation auto-generates user_id from first_name (lowercase)
- Supports both local file storage (SAM Local) and S3 (AWS)

## 🔒 Security Considerations

- **No Authentication**: Public endpoints for simplicity
- **CORS Enabled**: Allows cross-origin requests
- **S3 Private**: Bucket is not publicly accessible
- **IAM Minimal**: Lambda has only necessary S3 permissions

## 🤝 Contributing

1. Test locally with SAM Local
2. Follow existing code patterns
3. Update API documentation if adding endpoints
4. Test deployment script before submitting

## 📜 License

MIT License - see LICENSE file for details.

## 🆘 Support

For issues or questions:
1. Check the [API contract](./api-contract.yaml) for detailed specifications
2. Test endpoints with the provided curl examples
3. Review error responses for debugging information
4. Use SAM Local for development and testing