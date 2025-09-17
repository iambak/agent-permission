import json
import boto3
import os
from datetime import datetime
from typing import Dict, Any

# Configuration from environment variables
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'agent-permissions-data')
S3_FILE_KEY = os.environ.get('S3_FILE_KEY', 'permissions.json')
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'dev')
LOCAL_FILE_PATH = '/tmp/permissions.json'

# Check if running in SAM Local or AWS Lambda
IS_SAM_LOCAL = os.environ.get('AWS_SAM_LOCAL') == 'true'

def read_permissions_from_local() -> Dict[str, Any]:
    """Read permissions from local file (for SAM Local)"""
    try:
        if os.path.exists(LOCAL_FILE_PATH):
            with open(LOCAL_FILE_PATH, 'r') as f:
                return json.load(f)
        else:
            # Create default permissions with empty agent arrays
            default_data = {
                "last_updated": datetime.now().isoformat(),
                "permissions": {
                    "user_123": [],
                    "user_456": [],
                    "user_789": []
                }
            }
            write_permissions_to_local(default_data)
            return default_data
    except Exception as e:
        raise Exception(f"Unable to retrieve local permissions: {str(e)}")

def write_permissions_to_local(data: Dict[str, Any]) -> None:
    """Write permissions to local file (for SAM Local)"""
    try:
        data["last_updated"] = datetime.now().isoformat()
        with open(LOCAL_FILE_PATH, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        raise Exception(f"Unable to update local permissions: {str(e)}")

def read_permissions_from_s3() -> Dict[str, Any]:
    """Read permissions from S3 bucket"""
    # Initialize S3 client only when needed (for AWS)
    s3_client = boto3.client('s3')

    try:
        response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=S3_FILE_KEY)
        content = response['Body'].read().decode('utf-8')
        return json.loads(content)
    except s3_client.exceptions.NoSuchKey:
        # Create empty permissions file if it doesn't exist
        default_data = {
            "last_updated": datetime.now().isoformat(),
            "permissions": {}
        }
        write_permissions_to_s3(default_data)
        return default_data
    except Exception as e:
        raise Exception(f"Unable to retrieve permissions: {str(e)}")

def write_permissions_to_s3(data: Dict[str, Any]) -> None:
    """Write permissions to S3 bucket"""
    # Initialize S3 client only when needed (for AWS)
    s3_client = boto3.client('s3')

    try:
        data["last_updated"] = datetime.now().isoformat()
        content = json.dumps(data, indent=2)
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=S3_FILE_KEY,
            Body=content,
            ContentType='application/json'
        )
    except Exception as e:
        raise Exception(f"Unable to update permissions: {str(e)}")

# Environment-aware functions
def read_permissions() -> Dict[str, Any]:
    """Read permissions - auto-detects environment"""
    if IS_SAM_LOCAL:
        return read_permissions_from_local()
    else:
        return read_permissions_from_s3()

def write_permissions(data: Dict[str, Any]) -> None:
    """Write permissions - auto-detects environment"""
    if IS_SAM_LOCAL:
        write_permissions_to_local(data)
    else:
        write_permissions_to_s3(data)

def create_response(status_code: int, body: dict) -> dict:
    """Create proper API Gateway response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
        },
        'body': json.dumps(body)
    }

def handle_user_exists(user_id: str) -> dict:
    """Handle GET /users/{user_id}"""
    try:
        # Normalize user_id to lowercase
        user_id = user_id.lower()
        data = read_permissions()

        if user_id not in data["permissions"]:
            return create_response(404, {
                "status": "error",
                "error": {
                    "code": "USER_NOT_FOUND",
                    "message": "User was not found in the system",
                    "user_id": user_id
                }
            })

        return create_response(200, {
            "status": "success",
            "data": {
                "user_id": user_id,
                "exists": True
            },
            "message": "User exists in the system"
        })

    except Exception as e:
        return create_response(500, {
            "status": "error",
            "error": {
                "code": "SERVICE_UNAVAILABLE",
                "message": "Unable to retrieve permissions at this time"
            }
        })

def handle_get_permissions(user_id: str) -> dict:
    """Handle GET /permissions/{user_id}"""
    try:
        # Normalize user_id to lowercase for lookup
        user_id = user_id.lower()
        data = read_permissions()

        if user_id not in data["permissions"]:
            return create_response(404, {
                "status": "error",
                "error": {
                    "code": "USER_NOT_FOUND",
                    "message": "User was not found in the system",
                    "user_id": user_id
                }
            })

        return create_response(200, {
            "status": "success",
            "data": {
                "user_id": user_id,
                "permitted_agents": data["permissions"][user_id]
            }
        })

    except Exception as e:
        return create_response(500, {
            "status": "error",
            "error": {
                "code": "SERVICE_UNAVAILABLE",
                "message": "Unable to retrieve permissions at this time"
            }
        })

def handle_add_permission(user_id: str, body: str) -> dict:
    """Handle POST /permissions/{user_id}/agents"""
    try:
        # Parse request body
        request_data = json.loads(body)
        agent_name = request_data.get('agent_name')

        if not agent_name:
            return create_response(400, {
                "status": "error",
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "agent_name is required"
                }
            })

        # Normalize user_id to lowercase for lookup and storage
        user_id = user_id.lower()
        data = read_permissions()

        # Check if user exists
        if user_id in data["permissions"]:
            # User exists - check if agent already permitted
            if agent_name in data["permissions"][user_id]:
                return create_response(200, {
                    "status": "success",
                    "data": {
                        "user_id": user_id,
                        "agent_added": agent_name,
                        "permitted_agents": data["permissions"][user_id]
                    },
                    "message": "Permission already exists"
                })
            else:
                # Add agent to existing user
                data["permissions"][user_id].append(agent_name)
                write_permissions(data)
                return create_response(200, {
                    "status": "success",
                    "data": {
                        "user_id": user_id,
                        "agent_added": agent_name,
                        "permitted_agents": data["permissions"][user_id]
                    },
                    "message": "Permission added successfully"
                })
        else:
            # User doesn't exist - create new user with agent permission
            data["permissions"][user_id] = [agent_name]
            write_permissions(data)
            return create_response(200, {
                "status": "success",
                "data": {
                    "user_id": user_id,
                    "agent_added": agent_name,
                    "permitted_agents": data["permissions"][user_id]
                },
                "message": "User created and permission added successfully"
            })

    except json.JSONDecodeError:
        return create_response(400, {
            "status": "error",
            "error": {
                "code": "INVALID_REQUEST",
                "message": "Invalid JSON in request body"
            }
        })
    except Exception as e:
        return create_response(500, {
            "status": "error",
            "error": {
                "code": "SERVICE_UNAVAILABLE",
                "message": "Unable to update permissions at this time"
            }
        })

def handle_create_user(body: str) -> dict:
    """Handle POST /users"""
    try:
        # Parse request body
        request_data = json.loads(body)
        user_id = request_data.get('user_id')

        if not user_id:
            return create_response(400, {
                "status": "error",
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "user_id is required"
                }
            })

        # Store user_id as lowercase in JSON
        user_id_lower = user_id.lower()
        data = read_permissions()

        # Check if user already exists
        if user_id_lower in data["permissions"]:
            return create_response(409, {
                "status": "error",
                "error": {
                    "code": "USER_ALREADY_EXISTS",
                    "message": "User already exists in the system",
                    "user_id": user_id_lower
                }
            })

        # Create new user with empty permissions
        data["permissions"][user_id_lower] = []
        write_permissions(data)

        return create_response(201, {
            "status": "success",
            "data": {
                "user_id": user_id_lower,
                "permitted_agents": [],
                "created_at": datetime.now().isoformat()
            },
            "message": "User created successfully"
        })

    except json.JSONDecodeError:
        return create_response(400, {
            "status": "error",
            "error": {
                "code": "INVALID_REQUEST",
                "message": "Invalid JSON in request body"
            }
        })
    except Exception as e:
        return create_response(500, {
            "status": "error",
            "error": {
                "code": "SERVICE_UNAVAILABLE",
                "message": "Unable to create user at this time"
            }
        })

def handler(event, context):
    """Main Lambda handler"""

    # Handle CORS preflight requests
    if event.get('httpMethod') == 'OPTIONS':
        return create_response(200, {"message": "CORS preflight"})

    # Extract path and method
    path = event.get('path', '')
    method = event.get('httpMethod', '').upper()
    path_parameters = event.get('pathParameters') or {}
    user_id = path_parameters.get('user_id')

    # Route requests
    if method == 'GET' and path.startswith('/users/'):
        return handle_user_exists(user_id)

    elif method == 'POST' and path == '/users':
        body = event.get('body', '{}')
        return handle_create_user(body)

    elif method == 'GET' and path.startswith('/permissions/'):
        return handle_get_permissions(user_id)

    elif method == 'POST' and path.startswith('/permissions/') and path.endswith('/agents'):
        body = event.get('body', '{}')
        return handle_add_permission(user_id, body)

    else:
        return create_response(404, {
            "status": "error",
            "error": {
                "code": "NOT_FOUND",
                "message": "Endpoint not found"
            }
        })