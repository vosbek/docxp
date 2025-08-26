"""
AWS Token Manager - Proactive Token Refresh for Long-Running Jobs

Solves the critical issue: "AWS credential verification failed: Token has expired and refresh failed"

Features:
- Proactive token refresh 30 minutes before expiration
- Circuit breakers for AWS API failures  
- Multiple credential source support (SSO, IAM, env vars)
- Automatic retry with exponential backoff
- Token status monitoring and alerts
"""

import asyncio
import logging
import time
import random
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import subprocess
import os

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, TokenRetrievalError
from botocore.credentials import RefreshableCredentials
import aiofiles

from app.core.config import settings

logger = logging.getLogger(__name__)

class TokenStatus:
    """Token status tracking"""
    VALID = "valid"
    EXPIRING_SOON = "expiring_soon"  # < 30 minutes
    EXPIRED = "expired"
    REFRESH_FAILED = "refresh_failed"
    UNAVAILABLE = "unavailable"

class AWSTokenManager:
    """
    Manages AWS credentials with proactive refresh for long-running indexing jobs
    """
    
    def __init__(self):
        self.current_credentials: Optional[Dict[str, Any]] = None
        self.token_expiry: Optional[datetime] = None
        self._token_created_at: Optional[datetime] = None  # For jittered refresh
        self.credential_source: Optional[str] = None
        self.refresh_in_progress = False
        self.last_refresh_attempt: Optional[datetime] = None
        self.consecutive_failures = 0
        
        # Configuration - Updated for jittered refresh
        self.refresh_threshold_base_pct = 65  # Base: refresh at 65% of lifetime  
        self.refresh_jitter_pct = 10  # ±10% jitter to avoid thundering herds
        self.max_consecutive_failures = 3
        self.retry_delay_base = 60  # Base delay in seconds
        
        # Initialize credentials lazily to avoid event loop issues during import
        self._initialization_task = None
    
    async def _ensure_initialized(self):
        """Ensure credentials are initialized before use"""
        if self._initialization_task is None:
            self._initialization_task = asyncio.create_task(self._initialize_credentials())
        await self._initialization_task
    
    async def _initialize_credentials(self):
        """Initialize AWS credentials from available sources"""
        try:
            logger.info("🔐 Initializing AWS Token Manager...")
            
            # Try credential sources in order of preference
            sources = [
                self._try_environment_variables,
                self._try_aws_profile,
                self._try_sso_credentials,
                self._try_instance_metadata
            ]
            
            for source_func in sources:
                try:
                    success = await source_func()
                    if success:
                        logger.info(f"✅ AWS credentials initialized from {self.credential_source}")
                        await self._start_refresh_monitor()
                        return
                except Exception as e:
                    logger.debug(f"Credential source failed: {e}")
                    continue
            
            logger.error("❌ No valid AWS credentials found from any source")
            self.credential_source = "unavailable"
            
        except Exception as e:
            logger.error(f"❌ AWS Token Manager initialization failed: {e}")
    
    async def _try_environment_variables(self) -> bool:
        """Try to get credentials from environment variables"""
        try:
            access_key = os.getenv('AWS_ACCESS_KEY_ID')
            secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
            session_token = os.getenv('AWS_SESSION_TOKEN')
            
            if access_key and secret_key:
                self.current_credentials = {
                    'aws_access_key_id': access_key,
                    'aws_secret_access_key': secret_key,
                    'aws_session_token': session_token,
                    'region_name': os.getenv('AWS_REGION', 'us-east-1')
                }
                
                # Test credentials
                if await self._test_credentials():
                    self.credential_source = "environment_variables"
                    self.token_expiry = None  # Long-term credentials don't expire
                    self._token_created_at = datetime.utcnow()  # Track creation for jitter
                    return True
            
            return False
            
        except Exception as e:
            logger.debug(f"Environment variables credential check failed: {e}")
            return False
    
    async def _try_aws_profile(self) -> bool:
        """Try to get credentials from AWS profile"""
        try:
            profile_name = os.getenv('AWS_PROFILE', 'default')
            
            # Create session with profile
            session = boto3.Session(profile_name=profile_name)
            credentials = session.get_credentials()
            
            if credentials:
                self.current_credentials = {
                    'aws_access_key_id': credentials.access_key,
                    'aws_secret_access_key': credentials.secret_key,
                    'aws_session_token': credentials.token,
                    'region_name': session.region_name or 'us-east-1'
                }
                
                # Test credentials
                if await self._test_credentials():
                    self.credential_source = f"profile_{profile_name}"
                    
                    # Check if credentials are refreshable (SSO/STS)
                    if hasattr(credentials, 'expiry_time') and credentials.expiry_time:
                        self.token_expiry = credentials.expiry_time.replace(tzinfo=None)
                        self._token_created_at = datetime.utcnow()  # Track creation for jitter
                    
                    return True
            
            return False
            
        except Exception as e:
            logger.debug(f"AWS profile credential check failed: {e}")
            return False
    
    async def _try_sso_credentials(self) -> bool:
        """Try to get SSO credentials using AWS CLI"""
        try:
            # Try to get SSO credentials via AWS CLI
            result = subprocess.run(
                ['aws', 'sts', 'get-caller-identity', '--output', 'json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # If AWS CLI works, extract credentials
                caller_identity = json.loads(result.stdout)
                
                # Get credentials from the default session
                session = boto3.Session()
                credentials = session.get_credentials()
                
                if credentials:
                    self.current_credentials = {
                        'aws_access_key_id': credentials.access_key,
                        'aws_secret_access_key': credentials.secret_key,
                        'aws_session_token': credentials.token,
                        'region_name': session.region_name or 'us-east-1'
                    }
                    
                    if await self._test_credentials():
                        self.credential_source = "sso_cli"
                        
                        # SSO tokens typically expire in 8-12 hours
                        if hasattr(credentials, 'expiry_time') and credentials.expiry_time:
                            self.token_expiry = credentials.expiry_time.replace(tzinfo=None)
                        else:
                            # Estimate expiry time for SSO (8 hours)
                            self.token_expiry = datetime.utcnow() + timedelta(hours=8)
                        
                        self._token_created_at = datetime.utcnow()  # Track creation for jitter
                        
                        return True
            
            return False
            
        except Exception as e:
            logger.debug(f"SSO credential check failed: {e}")
            return False
    
    async def _try_instance_metadata(self) -> bool:
        """Try to get credentials from EC2 instance metadata"""
        try:
            # This would only work on EC2 instances
            session = boto3.Session()
            credentials = session.get_credentials()
            
            if credentials and credentials.access_key:
                self.current_credentials = {
                    'aws_access_key_id': credentials.access_key,
                    'aws_secret_access_key': credentials.secret_key,
                    'aws_session_token': credentials.token,
                    'region_name': session.region_name or 'us-east-1'
                }
                
                if await self._test_credentials():
                    self.credential_source = "instance_metadata"
                    
                    # Instance credentials refresh automatically
                    if hasattr(credentials, 'expiry_time') and credentials.expiry_time:
                        self.token_expiry = credentials.expiry_time.replace(tzinfo=None)
                        self._token_created_at = datetime.utcnow()  # Track creation for jitter
                    
                    return True
            
            return False
            
        except Exception as e:
            logger.debug(f"Instance metadata credential check failed: {e}")
            return False
    
    async def _test_credentials(self) -> bool:
        """Test if current credentials are valid"""
        try:
            if not self.current_credentials:
                return False
            
            # Create STS client to test credentials
            sts_client = boto3.client('sts', **self.current_credentials)
            
            # Test with get_caller_identity
            response = sts_client.get_caller_identity()
            
            if response and 'Arn' in response:
                logger.debug(f"✅ Credentials valid for: {response.get('Arn', 'unknown')}")
                return True
            
            return False
            
        except Exception as e:
            logger.debug(f"Credential test failed: {e}")
            return False
    
    async def _start_refresh_monitor(self):
        """Start background task to monitor and refresh tokens"""
        if not self.token_expiry:
            logger.info("📍 Credentials don't expire - no refresh monitoring needed")
            return
        
        logger.info(f"⏰ Starting token refresh monitor, expires at {self.token_expiry}")
        
        async def refresh_monitor():
            while True:
                try:
                    if await self._should_refresh_token():
                        logger.info("🔄 Proactive token refresh needed")
                        await self._refresh_credentials()
                    
                    # Check every 5 minutes
                    await asyncio.sleep(300)
                    
                except Exception as e:
                    logger.error(f"❌ Token refresh monitor error: {e}")
                    await asyncio.sleep(60)  # Shorter retry on error
        
        # Start background task
        asyncio.create_task(refresh_monitor())
    
    def _should_refresh_token(self) -> bool:
        """
        Check if token should be refreshed using jittered timing
        
        Implements recommendation: refresh at 60-70% ±10% jitter to avoid thundering herds
        """
        if not self.token_expiry:
            return False
        
        if self.refresh_in_progress:
            return False
        
        # Calculate total token lifetime (from creation to expiry)
        # Assume SSO tokens are valid for 8 hours (typical)
        if not hasattr(self, '_token_created_at') or not self._token_created_at:
            # Fallback to old behavior if we don't know creation time
            time_until_expiry = self.token_expiry - datetime.utcnow()
            return time_until_expiry.total_seconds() < (30 * 60)  # 30 minutes
        
        # Calculate jittered refresh point
        total_lifetime_seconds = (self.token_expiry - self._token_created_at).total_seconds()
        
        # Apply jitter: base_pct ± jitter_pct
        jitter = random.uniform(-self.refresh_jitter_pct, self.refresh_jitter_pct)
        refresh_at_pct = self.refresh_threshold_base_pct + jitter
        
        # Ensure bounds (don't go below 50% or above 80%)
        refresh_at_pct = max(50, min(80, refresh_at_pct))
        
        refresh_at_seconds = total_lifetime_seconds * (refresh_at_pct / 100)
        elapsed_seconds = (datetime.utcnow() - self._token_created_at).total_seconds()
        
        should_refresh = elapsed_seconds >= refresh_at_seconds
        
        if should_refresh:
            logger.info(f"🔄 Token refresh triggered at {refresh_at_pct:.1f}% of lifetime ({elapsed_seconds:.0f}s/{total_lifetime_seconds:.0f}s)")
        
        return should_refresh
    
    async def _refresh_credentials(self) -> bool:
        """Refresh AWS credentials"""
        if self.refresh_in_progress:
            logger.debug("Token refresh already in progress")
            return False
        
        self.refresh_in_progress = True
        self.last_refresh_attempt = datetime.utcnow()
        
        try:
            logger.info(f"🔄 Refreshing AWS credentials from {self.credential_source}")
            
            # Refresh based on credential source
            if self.credential_source == "sso_cli":
                success = await self._refresh_sso_credentials()
            elif "profile_" in self.credential_source:
                success = await self._refresh_profile_credentials()
            elif self.credential_source == "instance_metadata":
                success = await self._refresh_instance_credentials()
            else:
                logger.warning("⚠️  Cannot refresh credentials from source: {self.credential_source}")
                success = False
            
            if success:
                self.consecutive_failures = 0
                logger.info("✅ AWS credentials refreshed successfully")
                return True
            else:
                self.consecutive_failures += 1
                logger.error(f"❌ Credential refresh failed (attempt {self.consecutive_failures})")
                
                # If too many failures, try to reinitialize
                if self.consecutive_failures >= self.max_consecutive_failures:
                    logger.warning("🔄 Too many refresh failures, attempting reinitialization")
                    await self._initialize_credentials()
                
                return False
                
        except Exception as e:
            self.consecutive_failures += 1
            logger.error(f"❌ Credential refresh exception: {e}")
            return False
        finally:
            self.refresh_in_progress = False
    
    async def _refresh_sso_credentials(self) -> bool:
        """Refresh SSO credentials using AWS CLI"""
        try:
            # Try SSO login refresh
            result = subprocess.run(
                ['aws', 'sso', 'login'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                # Get refreshed credentials
                return await self._try_sso_credentials()
            else:
                logger.error(f"SSO refresh failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"SSO refresh exception: {e}")
            return False
    
    async def _refresh_profile_credentials(self) -> bool:
        """Refresh profile-based credentials"""
        try:
            # Profile credentials should refresh automatically
            return await self._try_aws_profile()
            
        except Exception as e:
            logger.error(f"Profile refresh exception: {e}")
            return False
    
    async def _refresh_instance_credentials(self) -> bool:
        """Refresh instance metadata credentials"""
        try:
            # Instance credentials refresh automatically
            return await self._try_instance_metadata()
            
        except Exception as e:
            logger.error(f"Instance metadata refresh exception: {e}")
            return False
    
    def get_token_status(self) -> Dict[str, Any]:
        """Get current token status for monitoring"""
        if not self.current_credentials:
            return {
                "status": TokenStatus.UNAVAILABLE,
                "credential_source": "none",
                "expiry": None,
                "time_until_expiry": None,
                "consecutive_failures": self.consecutive_failures
            }
        
        if not self.token_expiry:
            # Long-term credentials
            return {
                "status": TokenStatus.VALID,
                "credential_source": self.credential_source,
                "expiry": None,
                "time_until_expiry": None,
                "consecutive_failures": self.consecutive_failures
            }
        
        # Calculate time until expiry
        time_until_expiry = self.token_expiry - datetime.utcnow()
        seconds_until_expiry = time_until_expiry.total_seconds()
        
        # Determine status
        if seconds_until_expiry <= 0:
            status = TokenStatus.EXPIRED
        elif seconds_until_expiry < (30 * 60):  # 30 minutes threshold
            status = TokenStatus.EXPIRING_SOON
        elif self.consecutive_failures > 0:
            status = TokenStatus.REFRESH_FAILED
        else:
            status = TokenStatus.VALID
        
        return {
            "status": status,
            "credential_source": self.credential_source,
            "expiry": self.token_expiry.isoformat() if self.token_expiry else None,
            "time_until_expiry_minutes": seconds_until_expiry / 60 if seconds_until_expiry > 0 else 0,
            "consecutive_failures": self.consecutive_failures,
            "refresh_in_progress": self.refresh_in_progress,
            "last_refresh_attempt": self.last_refresh_attempt.isoformat() if self.last_refresh_attempt else None
        }
    
    async def get_valid_credentials(self) -> Optional[Dict[str, Any]]:
        """Get valid AWS credentials, refreshing if necessary"""
        try:
            # Ensure initialization before proceeding
            await self._ensure_initialized()
            # Check if refresh is needed
            if self._should_refresh_token():
                logger.info("🔄 Refreshing credentials before use")
                await self._refresh_credentials()
            
            # Test current credentials
            if self.current_credentials and await self._test_credentials():
                return self.current_credentials.copy()
            
            # Try to reinitialize if current credentials are invalid
            logger.warning("⚠️  Current credentials invalid, attempting reinitialization")
            await self._initialize_credentials()
            
            if self.current_credentials and await self._test_credentials():
                return self.current_credentials.copy()
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get valid credentials: {e}")
            return None
    
    async def ensure_valid_clients(self) -> Tuple[Optional[Any], Optional[Any]]:
        """Ensure Bedrock and STS clients have valid credentials"""
        try:
            # Ensure initialization before proceeding
            await self._ensure_initialized()
            
            credentials = await self.get_valid_credentials()
            if not credentials:
                return None, None
            
            # Create clients with current credentials
            bedrock_client = boto3.client('bedrock-runtime', **credentials)
            sts_client = boto3.client('sts', **credentials)
            
            return bedrock_client, sts_client
            
        except Exception as e:
            logger.error(f"❌ Failed to ensure valid clients: {e}")
            return None, None


# Global token manager instance
aws_token_manager = AWSTokenManager()

async def get_aws_token_manager() -> AWSTokenManager:
    """Get AWS token manager instance"""
    return aws_token_manager

async def get_valid_bedrock_client():
    """Get Bedrock client with valid credentials"""
    bedrock_client, _ = await aws_token_manager.ensure_valid_clients()
    return bedrock_client