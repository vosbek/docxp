#!/usr/bin/env python3
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