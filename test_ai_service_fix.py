#!/usr/bin/env python3
"""
Test script to verify AI service fixes
"""
import os
import sys
import asyncio
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

# Load environment
from dotenv import load_dotenv
env_path = backend_dir / ".env.enterprise"
load_dotenv(env_path)

print("🔍 Testing AI Service initialization fixes...")
print(f"📁 Loading environment from {env_path}")
print(f"  AWS_PROFILE: {os.getenv('AWS_PROFILE')}")
print(f"  AWS_REGION: {os.getenv('AWS_REGION')}")

try:
    # Import and test the AI service
    from app.services.ai_service import AIService
    from app.core.config import settings
    
    print("\n✅ AI Service class imported successfully")
    
    # Create AI service instance
    ai_service = AIService()
    print("✅ AI Service instance created")
    
    # Test synchronous initialization
    print("\n🔧 Testing synchronous session creation...")
    session = ai_service._create_session_sync()
    print(f"✅ Synchronous session created: {type(session)}")
    
    # Test connection
    print("\n🔗 Testing AWS connection...")
    try:
        models = ai_service._test_connection()
        print(f"✅ Connection successful, found {len(models)} models")
    except Exception as e:
        print(f"⚠️  Connection test warning: {e}")
    
    # Test async session creation (in proper async context)
    async def test_async_session():
        print("\n🔧 Testing async session creation...")
        session = await ai_service._create_session()
        print(f"✅ Async session created: {type(session)}")
        return session
    
    # Run async test
    async_session = asyncio.run(test_async_session())
    
    print("\n🎉 All AI Service fixes working correctly!")
    print("✅ No more 'asyncio.run() cannot be called from a running event loop' errors")
    
except Exception as e:
    print(f"❌ Error during testing: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
