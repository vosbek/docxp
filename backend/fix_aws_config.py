#!/usr/bin/env python3
"""
Fix AWS Configuration for Development Mode

This script provides a solution to disable AWS Bedrock integration 
for development and testing when AWS credentials are not available.
"""

import os
import sys
from pathlib import Path

def create_dev_env_file():
    """Create a development .env file with AWS disabled"""
    backend_path = Path(__file__).parent
    env_path = backend_path / ".env"
    
    # Development environment configuration
    dev_config = """
# DocXP Development Configuration
# This file disables AWS Bedrock for development when credentials are not available

# Application
DEBUG=true

# Database
DATABASE_URL=sqlite+aiosqlite:///./docxp.db

# AWS Configuration - Leave empty to disable
AWS_REGION=us-east-1
AWS_PROFILE=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_SESSION_TOKEN=

# Bedrock Model (only used when AWS is configured)
BEDROCK_MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0

# Feature Flags
ENABLE_DB_ANALYSIS=true
"""
    
    if env_path.exists():
        print(f"[INFO] Backing up existing .env file to .env.backup")
        backup_path = backend_path / ".env.backup"
        with open(env_path, 'r') as src, open(backup_path, 'w') as dst:
            dst.write(src.read())
    
    with open(env_path, 'w') as f:
        f.write(dev_config.strip())
    
    print(f"[OK] Development .env file created at: {env_path}")
    print("[INFO] AWS Bedrock is now disabled for development mode")
    
    return env_path

def modify_ai_service_for_graceful_degradation():
    """Modify AI service to handle missing credentials gracefully"""
    backend_path = Path(__file__).parent
    ai_service_path = backend_path / "app" / "services" / "ai_service.py"
    
    if not ai_service_path.exists():
        print(f"[ERROR] AI service file not found: {ai_service_path}")
        return False
    
    # Read current content
    with open(ai_service_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if already modified
    if "# GRACEFUL_DEGRADATION_MODE" in content:
        print("[INFO] AI service already configured for graceful degradation")
        return True
    
    # Add graceful degradation code
    graceful_init = '''
    def __init__(self):
        if not self._initialized:
            self.client = None
            self._graceful_mode = False  # GRACEFUL_DEGRADATION_MODE
            try:
                self._initialize_client()
            except Exception as e:
                logger.warning(f"AI Service starting in graceful degradation mode: {e}")
                self._graceful_mode = True
                self.client = None
            self._initialized = True
'''
    
    # Replace the __init__ method
    import re
    pattern = r'def __init__\(self\):(.*?)self\._initialized = True'
    
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, graceful_init.strip(), content, flags=re.DOTALL)
        
        # Add graceful methods
        graceful_methods = '''
    
    def _is_available(self) -> bool:
        """Check if AI service is available"""
        return not getattr(self, '_graceful_mode', False) and self.client is not None
    
    def _require_ai_service(self):
        """Raise exception if AI service is not available"""
        if not self._is_available():
            raise RuntimeError("AI Service not available - AWS Bedrock not configured")
'''
        
        # Add methods before the last class definition ends
        content = content.replace('\nai_service_instance = AIService()', graceful_methods + '\nai_service_instance = AIService()')
        
        # Backup original file
        backup_path = ai_service_path.with_suffix('.py.backup')
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[INFO] AI service backed up to: {backup_path}")
        
        # Write modified content
        with open(ai_service_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("[OK] AI service modified for graceful degradation")
        return True
    else:
        print("[ERROR] Could not find __init__ method to modify")
        return False

def create_development_mode_script():
    """Create a script to run the platform in development mode"""
    backend_path = Path(__file__).parent
    dev_script_path = backend_path / "run_dev_mode.py"
    
    dev_script = '''#!/usr/bin/env python3
"""
DocXP Development Mode Runner

This script runs DocXP in development mode with AI features disabled
when AWS credentials are not available.
"""

import os
import sys
import uvicorn
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

def main():
    """Run DocXP in development mode"""
    print("[START] Starting DocXP in Development Mode")
    print("[INFO] AI features may be disabled if AWS is not configured")
    
    # Set development environment
    os.environ["DEBUG"] = "true"
    
    try:
        # Import main app
        from main import app
        
        # Run with uvicorn
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="info"
        )
    except Exception as e:
        print(f"[ERROR] Failed to start development server: {e}")
        print("[TIP] Try running the health check first: python enterprise_migration_solution.py")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
'''
    
    with open(dev_script_path, 'w', encoding='utf-8') as f:
        f.write(dev_script.strip())
    
    print(f"[OK] Development mode script created: {dev_script_path}")
    return dev_script_path

def main():
    """Main function to set up development environment"""
    print("[SETUP] Setting up DocXP Development Environment")
    print("=" * 60)
    
    # Step 1: Create development .env file
    env_path = create_dev_env_file()
    
    # Step 2: Modify AI service for graceful degradation
    # modify_ai_service_for_graceful_degradation()
    
    # Step 3: Create development mode script
    dev_script_path = create_development_mode_script()
    
    print("\n[OK] Development environment setup complete!")
    print("\nNext steps:")
    print(f"1. Run health check: python enterprise_migration_solution.py")
    print(f"2. Start development server: python run_dev_mode.py")
    print(f"3. Access web interface: http://localhost:8000")
    print("\n[NOTES]:")
    print("- AI features will be disabled until AWS credentials are configured")
    print("- All database operations will work normally")
    print("- API endpoints will function except those requiring AI processing")
    
    return 0

if __name__ == "__main__":
    exit(main())