#!/usr/bin/env python3
"""
Test configuration loading to ensure all settings are correct
"""

import os
import sys
from pathlib import Path

def test_config_loading():
    """Test that configuration loads correctly"""
    print("🔍 Testing configuration loading...")
    
    try:
        # Load environment first 
        from fix_env_loading import load_env_enterprise
        if not load_env_enterprise():
            print("❌ Failed to load .env.enterprise")
            return False
        
        print("\n🔍 Testing Settings import...")
        from app.core.config import settings
        
        print(f"✅ Settings imported successfully")
        print(f"  DATABASE_URL: {settings.DATABASE_URL}")
        print(f"  VECTOR_DB_TYPE: {settings.VECTOR_DB_TYPE}")
        print(f"  EMBEDDING_PROVIDER: {settings.EMBEDDING_PROVIDER}")
        print(f"  AWS_PROFILE: {settings.AWS_PROFILE}")
        print(f"  AWS_REGION: {settings.AWS_REGION}")
        print(f"  OPENSEARCH_HOST: {settings.OPENSEARCH_HOST}")
        print(f"  OPENSEARCH_INDEX_NAME: {settings.OPENSEARCH_INDEX_NAME}")
        
        # Validate database configuration
        if 'sqlite' in settings.DATABASE_URL.lower():
            print("❌ ERROR: Database is still configured for SQLite!")
            print(f"   DATABASE_URL={settings.DATABASE_URL}")
            return False
        elif 'postgresql' in settings.DATABASE_URL.lower():
            print("✅ Database correctly configured for PostgreSQL")
        else:
            print(f"⚠️  Unknown database configuration: {settings.DATABASE_URL}")
            
        # Validate other critical settings
        if settings.VECTOR_DB_TYPE != 'postgresql_pgvector':
            print(f"❌ ERROR: VECTOR_DB_TYPE should be 'postgresql_pgvector', got '{settings.VECTOR_DB_TYPE}'")
            return False
            
        if settings.EMBEDDING_PROVIDER != 'bedrock':
            print(f"❌ ERROR: EMBEDDING_PROVIDER should be 'bedrock', got '{settings.EMBEDDING_PROVIDER}'")
            return False
            
        if not settings.AWS_PROFILE:
            print("❌ ERROR: AWS_PROFILE not set")
            return False
            
        print("✅ All configuration validation passed!")
        return True
        
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("  DocXP Configuration Loading Test")
    print("=" * 60)
    
    if test_config_loading():
        print("\n🎉 Configuration is correct!")
        sys.exit(0)
    else:
        print("\n❌ Configuration has errors!")
        sys.exit(1)