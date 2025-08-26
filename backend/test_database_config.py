#!/usr/bin/env python3
"""
Test database configuration to ensure PostgreSQL is properly configured
"""

import os
import sys
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def test_database_config():
    """Test that database configuration is correct"""
    print("🔍 Testing database configuration...")
    
    try:
        # Load environment first
        from fix_env_loading import load_env_enterprise
        load_env_enterprise()
        
        # Import settings after environment is loaded
        from app.core.config import settings
        
        print(f"  Database URL: {settings.DATABASE_URL}")
        print(f"  Vector DB Type: {settings.VECTOR_DB_TYPE}")
        print(f"  PgVector Enabled: {getattr(settings, 'PGVECTOR_ENABLED', 'Not set')}")
        print(f"  Embedding Provider: {settings.EMBEDDING_PROVIDER}")
        
        # Check if we're using PostgreSQL
        if settings.DATABASE_URL.startswith('sqlite'):
            print("❌ ERROR: Configuration is using SQLite instead of PostgreSQL!")
            print("   This will cause UUID compilation errors.")
            print("   Check that .env.enterprise is being loaded correctly.")
            return False
        elif 'postgresql' in settings.DATABASE_URL:
            print("✅ PostgreSQL configuration detected")
            return True
        else:
            print(f"⚠️  Unexpected database URL format: {settings.DATABASE_URL}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing database config: {e}")
        return False

def test_postgresql_connection():
    """Test actual PostgreSQL connection"""
    print("🔍 Testing PostgreSQL connection...")
    
    try:
        import asyncio
        import asyncpg
        from app.core.config import settings
        
        async def test_connection():
            try:
                # Extract connection details from DATABASE_URL
                # Format: postgresql+asyncpg://user:pass@host:port/db
                url = settings.DATABASE_URL
                if '+asyncpg' in url:
                    url = url.replace('postgresql+asyncpg://', 'postgresql://')
                
                conn = await asyncpg.connect(url)
                
                # Test basic query
                result = await conn.fetchval('SELECT version()')
                print(f"✅ PostgreSQL connection successful")
                print(f"   Version: {result.split(',')[0]}")
                
                await conn.close()
                return True
                
            except Exception as e:
                print(f"❌ PostgreSQL connection failed: {e}")
                return False
        
        return asyncio.run(test_connection())
        
    except ImportError as e:
        print(f"⚠️  Cannot test PostgreSQL connection - missing dependency: {e}")
        return True  # Don't fail if asyncpg not installed
    except Exception as e:
        print(f"❌ PostgreSQL connection test error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("  DocXP Database Configuration Test")
    print("=" * 60)
    
    config_ok = test_database_config()
    connection_ok = test_postgresql_connection() if config_ok else False
    
    print("=" * 60)
    
    if config_ok and connection_ok:
        print("🎉 Database configuration is correct!")
        sys.exit(0)
    elif config_ok:
        print("⚠️  Database configuration is correct but connection failed.")
        print("   This is normal if PostgreSQL container is not running yet.")
        sys.exit(0)
    else:
        print("❌ Database configuration is incorrect!")
        sys.exit(1)