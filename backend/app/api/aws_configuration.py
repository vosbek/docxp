"""
AWS Configuration API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import logging
import os
import tempfile

from app.core.database import get_session
from app.services.ai_service import ai_service_instance
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

class AWSCredentialsRequest(BaseModel):
    """AWS credentials configuration request"""
    auth_method: str  # "access_keys" or "sso_profile"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None
    aws_profile: Optional[str] = None
    aws_region: str = "us-east-1"

class ModelSelectionRequest(BaseModel):
    """Model selection request"""
    model_id: str

class AWSStatusResponse(BaseModel):
    """AWS connection status response"""
    connected: bool
    error: Optional[str] = None
    account_id: Optional[str] = None
    region: str
    auth_method: str
    model_count: int = 0

@router.get("/status")
async def get_aws_status():
    """Get current AWS connection status"""
    try:
        ai_service = ai_service_instance
        
        # Check if we have a working client
        if not ai_service.client:
            return AWSStatusResponse(
                connected=False,
                error="No AWS credentials configured",
                region=settings.AWS_REGION,
                auth_method="none",
                model_count=0
            )
        
        # Test the connection
        try:
            models = ai_service.get_available_models()
            
            # Try to get account info
            import boto3
            session_kwargs = {}
            if settings.AWS_PROFILE:
                session_kwargs['profile_name'] = settings.AWS_PROFILE
            elif settings.AWS_ACCESS_KEY_ID:
                session_kwargs['aws_access_key_id'] = settings.AWS_ACCESS_KEY_ID
                session_kwargs['aws_secret_access_key'] = settings.AWS_SECRET_ACCESS_KEY
                if settings.AWS_SESSION_TOKEN:
                    session_kwargs['aws_session_token'] = settings.AWS_SESSION_TOKEN
            
            session_kwargs['region_name'] = settings.AWS_REGION
            session = boto3.Session(**session_kwargs)
            sts = session.client('sts')
            identity = sts.get_caller_identity()
            
            auth_method = "sso_profile" if settings.AWS_PROFILE else "access_keys"
            
            return AWSStatusResponse(
                connected=True,
                account_id=identity.get('Account'),
                region=settings.AWS_REGION,
                auth_method=auth_method,
                model_count=len(models)
            )
            
        except Exception as e:
            return AWSStatusResponse(
                connected=False,
                error=str(e),
                region=settings.AWS_REGION,
                auth_method="unknown",
                model_count=0
            )
            
    except Exception as e:
        logger.error(f"Error checking AWS status: {e}")
        return AWSStatusResponse(
            connected=False,
            error=f"Internal error: {e}",
            region=settings.AWS_REGION,
            auth_method="unknown",
            model_count=0
        )

@router.post("/test-credentials")
async def test_aws_credentials(request: AWSCredentialsRequest):
    """Test AWS credentials without permanently storing them"""
    try:
        # Temporarily set environment variables for testing
        original_env = {}
        
        if request.auth_method == "access_keys":
            if not request.aws_access_key_id or not request.aws_secret_access_key:
                raise HTTPException(status_code=400, detail="Access key and secret key are required")
            
            # Store original values
            for key in ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_SESSION_TOKEN', 'AWS_PROFILE']:
                original_env[key] = os.environ.get(key)
            
            # Set test values
            os.environ['AWS_ACCESS_KEY_ID'] = request.aws_access_key_id
            os.environ['AWS_SECRET_ACCESS_KEY'] = request.aws_secret_access_key
            if request.aws_session_token:
                os.environ['AWS_SESSION_TOKEN'] = request.aws_session_token
            else:
                os.environ.pop('AWS_SESSION_TOKEN', None)
            os.environ.pop('AWS_PROFILE', None)
            
        elif request.auth_method == "sso_profile":
            if not request.aws_profile:
                raise HTTPException(status_code=400, detail="AWS profile name is required")
            
            # Store original values
            for key in ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_SESSION_TOKEN', 'AWS_PROFILE']:
                original_env[key] = os.environ.get(key)
            
            # Set test values
            for key in ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_SESSION_TOKEN']:
                os.environ.pop(key, None)
            os.environ['AWS_PROFILE'] = request.aws_profile
            
        else:
            raise HTTPException(status_code=400, detail="Invalid auth_method. Must be 'access_keys' or 'sso_profile'")
        
        os.environ['AWS_REGION'] = request.aws_region
        
        # Create a temporary AI service instance for testing
        test_ai_service = ai_service_instance
        
        # Test the connection
        models = test_ai_service.get_available_models()
        
        # Get account information
        import boto3
        if request.auth_method == "sso_profile":
            session = boto3.Session(profile_name=request.aws_profile, region_name=request.aws_region)
        else:
            session = boto3.Session(
                aws_access_key_id=request.aws_access_key_id,
                aws_secret_access_key=request.aws_secret_access_key,
                aws_session_token=request.aws_session_token,
                region_name=request.aws_region
            )
        
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        
        return {
            "success": True,
            "message": f"Successfully connected to AWS account {identity.get('Account')}",
            "account_id": identity.get('Account'),
            "region": request.aws_region,
            "model_count": len(models),
            "models": models[:5]  # Return first 5 models as preview
        }
        
    except Exception as e:
        logger.error(f"AWS credential test failed: {e}")
        return {
            "success": False,
            "message": f"Connection failed: {e}",
            "error": str(e)
        }
        
    finally:
        # Restore original environment variables
        for key, value in original_env.items():
            if value is not None:
                os.environ[key] = value
            else:
                os.environ.pop(key, None)

@router.post("/configure")
async def configure_aws_credentials(request: AWSCredentialsRequest):
    """Configure AWS credentials permanently"""
    try:
        # First test the credentials
        test_result = await test_aws_credentials(request)
        
        if not test_result.get("success"):
            raise HTTPException(status_code=400, detail=test_result.get("message", "Credential test failed"))
        
        # Update the settings
        if request.auth_method == "access_keys":
            settings.AWS_ACCESS_KEY_ID = request.aws_access_key_id
            settings.AWS_SECRET_ACCESS_KEY = request.aws_secret_access_key
            settings.AWS_SESSION_TOKEN = request.aws_session_token
            settings.AWS_PROFILE = None
        elif request.auth_method == "sso_profile":
            settings.AWS_PROFILE = request.aws_profile
            settings.AWS_ACCESS_KEY_ID = None
            settings.AWS_SECRET_ACCESS_KEY = None
            settings.AWS_SESSION_TOKEN = None
        
        settings.AWS_REGION = request.aws_region
        
        # Update environment variables for the current session
        if request.auth_method == "access_keys":
            os.environ['AWS_ACCESS_KEY_ID'] = request.aws_access_key_id
            os.environ['AWS_SECRET_ACCESS_KEY'] = request.aws_secret_access_key
            if request.aws_session_token:
                os.environ['AWS_SESSION_TOKEN'] = request.aws_session_token
            else:
                os.environ.pop('AWS_SESSION_TOKEN', None)
            os.environ.pop('AWS_PROFILE', None)
        else:
            for key in ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_SESSION_TOKEN']:
                os.environ.pop(key, None)
            os.environ['AWS_PROFILE'] = request.aws_profile
        
        os.environ['AWS_REGION'] = request.aws_region
        
        # Write to .env file for persistence
        env_path = ".env"
        env_lines = []
        
        # Read existing .env file if it exists
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                env_lines = [line.strip() for line in f.readlines()]
        
        # Remove existing AWS-related lines
        env_lines = [line for line in env_lines if not any(
            line.startswith(prefix) for prefix in [
                'AWS_ACCESS_KEY_ID=', 'AWS_SECRET_ACCESS_KEY=', 
                'AWS_SESSION_TOKEN=', 'AWS_PROFILE=', 'AWS_REGION='
            ]
        )]
        
        # Add new configuration
        if request.auth_method == "access_keys":
            env_lines.append(f"AWS_ACCESS_KEY_ID={request.aws_access_key_id}")
            env_lines.append(f"AWS_SECRET_ACCESS_KEY={request.aws_secret_access_key}")
            if request.aws_session_token:
                env_lines.append(f"AWS_SESSION_TOKEN={request.aws_session_token}")
        else:
            env_lines.append(f"AWS_PROFILE={request.aws_profile}")
        
        env_lines.append(f"AWS_REGION={request.aws_region}")
        env_lines.append("BEDROCK_MODEL_ID=anthropic.claude-v2")
        
        # Write updated .env file
        with open(env_path, 'w') as f:
            f.write('\n'.join(env_lines) + '\n')
        
        return {
            "success": True,
            "message": "AWS credentials configured successfully",
            "account_id": test_result.get("account_id"),
            "region": request.aws_region,
            "auth_method": request.auth_method
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error configuring AWS credentials: {e}")
        raise HTTPException(status_code=500, detail=f"Configuration failed: {e}")

@router.get("/models")
async def get_available_models():
    """Get list of available Bedrock models"""
    try:
        ai_service = ai_service_instance
        models = ai_service.get_available_models()
        
        return {
            "success": True,
            "models": models,
            "current_model": ai_service.get_current_model_id()
        }
        
    except Exception as e:
        logger.error(f"Error fetching models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch models: {e}")

@router.post("/set-model")
async def set_bedrock_model(request: ModelSelectionRequest):
    """Set the Bedrock model to use"""
    try:
        ai_service = ai_service_instance
        ai_service.set_model_id(request.model_id)
        
        # Update the .env file
        env_path = ".env"
        env_lines = []
        
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                env_lines = [line.strip() for line in f.readlines()]
        
        # Remove existing BEDROCK_MODEL_ID line
        env_lines = [line for line in env_lines if not line.startswith('BEDROCK_MODEL_ID=')]
        
        # Add new model ID
        env_lines.append(f"BEDROCK_MODEL_ID={request.model_id}")
        
        # Write updated .env file
        with open(env_path, 'w') as f:
            f.write('\n'.join(env_lines) + '\n')
        
        return {
            "success": True,
            "message": f"Model set to {request.model_id}",
            "model_id": request.model_id
        }
        
    except Exception as e:
        logger.error(f"Error setting model: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to set model: {e}")

@router.get("/profiles")
async def get_aws_profiles():
    """Get available AWS CLI profiles"""
    try:
        import configparser
        import os
        from pathlib import Path
        
        profiles = []
        
        # Check AWS credentials file
        aws_dir = Path.home() / ".aws"
        credentials_file = aws_dir / "credentials"
        config_file = aws_dir / "config"
        
        if credentials_file.exists():
            config = configparser.ConfigParser()
            config.read(credentials_file)
            for section in config.sections():
                profiles.append(section)
        
        if config_file.exists():
            config = configparser.ConfigParser()
            config.read(config_file)
            for section in config.sections():
                # Remove 'profile ' prefix if present
                profile_name = section.replace('profile ', '')
                if profile_name not in profiles:
                    profiles.append(profile_name)
        
        return {
            "success": True,
            "profiles": sorted(profiles),
            "message": f"Found {len(profiles)} AWS profiles"
        }
        
    except Exception as e:
        logger.error(f"Error reading AWS profiles: {e}")
        return {
            "success": False,
            "profiles": [],
            "message": f"Could not read AWS profiles: {e}"
        }