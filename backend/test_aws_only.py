#!/usr/bin/env python3
"""
Standalone AWS credentials test
"""

import os
import sys
from pathlib import Path

def test_aws_credentials():
    """Test AWS credentials directly"""
    print("🔍 Testing AWS credentials...")
    
    # Check environment variables
    aws_profile = os.getenv('AWS_PROFILE')
    aws_region = os.getenv('AWS_REGION')
    
    print(f"  AWS_PROFILE from env: {aws_profile}")
    print(f"  AWS_REGION from env: {aws_region}")
    
    # Try to create AWS session
    try:
        import boto3
        
        if aws_profile:
            print(f"  Creating session with profile: {aws_profile}")
            session = boto3.Session(profile_name=aws_profile, region_name=aws_region)
        else:
            print("  Creating session with default credentials")
            session = boto3.Session(region_name=aws_region or 'us-east-1')
            
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        
        print(f"✅ AWS credentials working!")
        print(f"  Account: {identity.get('Account')}")
        print(f"  User/Role: {identity.get('Arn')}")
        
        # Test Bedrock access
        bedrock = session.client('bedrock', region_name=aws_region or 'us-east-1')
        models = bedrock.list_foundation_models()
        print(f"✅ Bedrock access confirmed: {len(models['modelSummaries'])} models available")
        
        return True
        
    except Exception as e:
        print(f"❌ AWS credentials failed: {e}")
        return False

if __name__ == "__main__":
    # Load environment first
    env_file = Path(__file__).parent / ".env.enterprise"
    if env_file.exists():
        print(f"📁 Loading environment from {env_file}")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
    
    print("=" * 60)
    print("  AWS Credentials Test")
    print("=" * 60)
    
    if test_aws_credentials():
        print("🎉 AWS credentials are working!")
        sys.exit(0)
    else:
        print("❌ AWS credentials failed!")
        sys.exit(1)