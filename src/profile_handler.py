import json
import boto3
import os
import random
from datetime import datetime
from typing import Dict, Any, Optional

# Configuration from environment variables
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'agent-permissions-data')
S3_PROFILES_FILE_KEY = os.environ.get('S3_PROFILES_FILE_KEY', 'user_profiles.json')
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'dev')
LOCAL_PROFILES_FILE_PATH = '/tmp/user_profiles.json'

# Check if running in SAM Local or AWS Lambda
IS_SAM_LOCAL = os.environ.get('AWS_SAM_LOCAL') == 'true'

# Funny superhero last names
SUPERHERO_LAST_NAMES = [
    "Thunderbolt", "Stormwind", "Fireburst", "Shadowbane", "Lightspeed",
    "Iceheart", "Starfist", "Nightwing", "Ironclad", "Blazefire",
    "Frostbite", "Quickstrike", "Darkblade", "Goldeneye", "Silverwing",
    "Thunderstorm", "Flameheart", "Crystalclaw", "Moonbeam", "Sunburst",
    "Steelstorm", "Crimsonbolt", "Emeraldfire", "Diamondshield", "Rubystrike",
    "Sapphirewing", "Platinumfist", "Titanforge", "Voidwalker", "Starstrike"
]

def read_profiles_from_local() -> Dict[str, Any]:
    """Read user profiles from local file (for SAM Local)"""
    try:
        if os.path.exists(LOCAL_PROFILES_FILE_PATH):
            with open(LOCAL_PROFILES_FILE_PATH, 'r') as f:
                return json.load(f)
        else:
            # Create default profiles structure
            default_data = {
                "last_updated": datetime.now().isoformat(),
                "profiles": {}
            }
            write_profiles_to_local(default_data)
            return default_data
    except Exception as e:
        raise Exception(f"Unable to retrieve local profiles: {str(e)}")

def write_profiles_to_local(data: Dict[str, Any]) -> None:
    """Write user profiles to local file (for SAM Local)"""
    try:
        data["last_updated"] = datetime.now().isoformat()
        with open(LOCAL_PROFILES_FILE_PATH, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        raise Exception(f"Unable to update local profiles: {str(e)}")

def read_profiles_from_s3() -> Dict[str, Any]:
    """Read user profiles from S3 bucket"""
    s3_client = boto3.client('s3')

    try:
        response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=S3_PROFILES_FILE_KEY)
        content = response['Body'].read().decode('utf-8')
        return json.loads(content)
    except s3_client.exceptions.NoSuchKey:
        # Create empty profiles file if it doesn't exist
        default_data = {
            "last_updated": datetime.now().isoformat(),
            "profiles": {}
        }
        write_profiles_to_s3(default_data)
        return default_data
    except Exception as e:
        raise Exception(f"Unable to retrieve profiles: {str(e)}")

def write_profiles_to_s3(data: Dict[str, Any]) -> None:
    """Write user profiles to S3 bucket"""
    s3_client = boto3.client('s3')

    try:
        data["last_updated"] = datetime.now().isoformat()
        content = json.dumps(data, indent=2)
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=S3_PROFILES_FILE_KEY,
            Body=content,
            ContentType='application/json'
        )
    except Exception as e:
        raise Exception(f"Unable to update profiles: {str(e)}")

# Environment-aware functions
def read_profiles() -> Dict[str, Any]:
    """Read profiles - auto-detects environment"""
    if IS_SAM_LOCAL:
        return read_profiles_from_local()
    else:
        return read_profiles_from_s3()

def write_profiles(data: Dict[str, Any]) -> None:
    """Write profiles - auto-detects environment"""
    if IS_SAM_LOCAL:
        write_profiles_to_local(data)
    else:
        write_profiles_to_s3(data)

def create_response(status_code: int, body: dict) -> dict:
    """Create proper API Gateway response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
        },
        'body': json.dumps(body)
    }

def validate_profile_data(profile_data: Dict[str, Any]) -> Optional[str]:
    """Validate profile data and return error message if invalid"""
    required_fields = ['email', 'first_name', 'last_name']

    for field in required_fields:
        if field not in profile_data or not profile_data[field]:
            return f"{field} is required"

    # Basic email validation
    email = profile_data.get('email', '')
    if '@' not in email or '.' not in email.split('@')[-1]:
        return "Invalid email format"

    # Validate first_name for use as user_id (no spaces, special chars)
    first_name = profile_data.get('first_name', '')
    if not first_name.replace('_', '').replace('-', '').isalnum():
        return "first_name can only contain letters, numbers, hyphens, and underscores (will be used as user ID)"

    return None

def handle_get_profile(user_id: str) -> dict:
    """Handle GET /profiles/{user_id}"""
    try:
        user_id = user_id.lower()
        data = read_profiles()

        if user_id not in data["profiles"]:
            return create_response(404, {
                "status": "error",
                "error": {
                    "code": "PROFILE_NOT_FOUND",
                    "message": "User profile was not found",
                    "user_id": user_id
                }
            })

        return create_response(200, {
            "status": "success",
            "data": {
                "user_id": user_id,
                "profile": data["profiles"][user_id]
            }
        })

    except Exception as e:
        return create_response(500, {
            "status": "error",
            "error": {
                "code": "SERVICE_UNAVAILABLE",
                "message": "Unable to retrieve profile at this time"
            }
        })

def handle_create_profile(body: str) -> dict:
    """Handle POST /profiles"""
    try:
        request_data = json.loads(body)

        # Extract profile data first to get first_name
        profile_data = {
            "email": request_data.get('email'),
            "first_name": request_data.get('first_name'),
            "last_name": request_data.get('last_name'),
            "phone": request_data.get('phone', ''),
            "company": request_data.get('company', ''),
            "role": request_data.get('role', ''),
            "bio": request_data.get('bio', ''),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        # Validate profile data
        validation_error = validate_profile_data(profile_data)
        if validation_error:
            return create_response(400, {
                "status": "error",
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": validation_error
                }
            })

        # Auto-generate user_id from first_name (convert to lowercase)
        user_id = profile_data['first_name'].lower()
        data = read_profiles()

        # Check if profile already exists
        if user_id in data["profiles"]:
            return create_response(409, {
                "status": "error",
                "error": {
                    "code": "PROFILE_ALREADY_EXISTS",
                    "message": "User profile already exists",
                    "user_id": user_id
                }
            })

        # Create new profile
        data["profiles"][user_id] = profile_data
        write_profiles(data)

        return create_response(201, {
            "status": "success",
            "data": {
                "user_id": user_id,
                "profile": profile_data
            },
            "message": "Profile created successfully"
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
                "message": "Unable to create profile at this time"
            }
        })

def handle_update_profile(user_id: str, body: str) -> dict:
    """Handle PUT /profiles/{user_id}"""
    try:
        request_data = json.loads(body)
        user_id = user_id.lower()
        data = read_profiles()

        if user_id not in data["profiles"]:
            return create_response(404, {
                "status": "error",
                "error": {
                    "code": "PROFILE_NOT_FOUND",
                    "message": "User profile was not found",
                    "user_id": user_id
                }
            })

        # Update profile data
        current_profile = data["profiles"][user_id]
        updated_profile = {
            "email": request_data.get('email', current_profile.get('email')),
            "first_name": request_data.get('first_name', current_profile.get('first_name')),
            "last_name": request_data.get('last_name', current_profile.get('last_name')),
            "phone": request_data.get('phone', current_profile.get('phone', '')),
            "company": request_data.get('company', current_profile.get('company', '')),
            "role": request_data.get('role', current_profile.get('role', '')),
            "bio": request_data.get('bio', current_profile.get('bio', '')),
            "created_at": current_profile.get('created_at'),
            "updated_at": datetime.now().isoformat()
        }

        # Validate updated profile data
        validation_error = validate_profile_data(updated_profile)
        if validation_error:
            return create_response(400, {
                "status": "error",
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": validation_error
                }
            })

        # Save updated profile
        data["profiles"][user_id] = updated_profile
        write_profiles(data)

        return create_response(200, {
            "status": "success",
            "data": {
                "user_id": user_id,
                "profile": updated_profile
            },
            "message": "Profile updated successfully"
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
                "message": "Unable to update profile at this time"
            }
        })

def handle_delete_profile(user_id: str) -> dict:
    """Handle DELETE /profiles/{user_id}"""
    try:
        user_id = user_id.lower()
        data = read_profiles()

        if user_id not in data["profiles"]:
            return create_response(404, {
                "status": "error",
                "error": {
                    "code": "PROFILE_NOT_FOUND",
                    "message": "User profile was not found",
                    "user_id": user_id
                }
            })

        # Delete profile
        del data["profiles"][user_id]
        write_profiles(data)

        return create_response(200, {
            "status": "success",
            "data": {
                "user_id": user_id
            },
            "message": "Profile deleted successfully"
        })

    except Exception as e:
        return create_response(500, {
            "status": "error",
            "error": {
                "code": "SERVICE_UNAVAILABLE",
                "message": "Unable to delete profile at this time"
            }
        })

def handle_list_profiles() -> dict:
    """Handle GET /profiles - list all profiles"""
    try:
        data = read_profiles()

        # Return list of profiles with basic info only
        profile_list = []
        for user_id, profile in data["profiles"].items():
            profile_list.append({
                "user_id": user_id,
                "email": profile.get("email"),
                "first_name": profile.get("first_name"),
                "last_name": profile.get("last_name"),
                "company": profile.get("company"),
                "created_at": profile.get("created_at")
            })

        return create_response(200, {
            "status": "success",
            "data": {
                "profiles": profile_list,
                "total_count": len(profile_list)
            }
        })

    except Exception as e:
        return create_response(500, {
            "status": "error",
            "error": {
                "code": "SERVICE_UNAVAILABLE",
                "message": "Unable to retrieve profiles at this time"
            }
        })

def handler(event, context):
    """Main Lambda handler for user profiles"""

    # Handle CORS preflight requests
    if event.get('httpMethod') == 'OPTIONS':
        return create_response(200, {"message": "CORS preflight"})

    # Extract path and method
    path = event.get('path', '')
    method = event.get('httpMethod', '').upper()
    path_parameters = event.get('pathParameters') or {}
    user_id = path_parameters.get('user_id')

    # Route requests
    if method == 'GET' and path == '/profiles':
        return handle_list_profiles()

    elif method == 'GET' and path.startswith('/profiles/'):
        return handle_get_profile(user_id)

    elif method == 'POST' and path == '/profiles':
        body = event.get('body', '{}')
        return handle_create_profile(body)

    elif method == 'PUT' and path.startswith('/profiles/'):
        body = event.get('body', '{}')
        return handle_update_profile(user_id, body)

    elif method == 'DELETE' and path.startswith('/profiles/'):
        return handle_delete_profile(user_id)

    else:
        return create_response(404, {
            "status": "error",
            "error": {
                "code": "NOT_FOUND",
                "message": "Endpoint not found"
            }
        })