"""
Quick fix to ensure .env.enterprise is loaded properly
Run this before starting the main application
"""

import os
from pathlib import Path

def load_env_enterprise():
    """Load .env.enterprise file explicitly"""
    env_file = Path(__file__).parent / ".env.enterprise"
    
    if not env_file.exists():
        print(f"❌ .env.enterprise not found at {env_file}")
        return False
    
    print(f"📁 Loading environment from {env_file}")
    
    with open(env_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#') or line.startswith('REM'):
                continue
            
            # Parse key=value pairs
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Handle Windows path variables
                if '%USERNAME%' in value:
                    username = os.getenv('USERNAME', os.getenv('USER', 'hairsm2'))
                    value = value.replace('%USERNAME%', username)
                
                # Set environment variable
                os.environ[key] = value
                print(f"  ✅ {key}={value}")
    
    return True

def verify_aws_config():
    """Verify AWS configuration is properly loaded"""
    print("\n🔍 Verifying AWS configuration...")
    
    aws_profile = os.getenv('AWS_PROFILE')
    aws_region = os.getenv('AWS_REGION')
    
    if not aws_profile:
        print("❌ AWS_PROFILE not set")
        return False
    
    if not aws_region:
        print("❌ AWS_REGION not set")
        return False
    
    print(f"✅ AWS_PROFILE: {aws_profile}")
    print(f"✅ AWS_REGION: {aws_region}")
    
    # Test boto3 session creation
    try:
        import boto3
        session = boto3.Session(profile_name=aws_profile, region_name=aws_region)
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS Session verified: Account {identity.get('Account')}")
        return True
    except Exception as e:
        print(f"❌ AWS Session failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("  DocXP Environment Configuration Fix")
    print("=" * 80)
    
    # Load environment
    if load_env_enterprise():
        # Verify AWS
        if verify_aws_config():
            print("\n🎉 Environment configuration successful!")
            print("\nYou can now start the application with:")
            print("python main.py")
        else:
            print("\n❌ AWS configuration failed")
    else:
        print("\n❌ Environment loading failed")
    
    print("=" * 80)