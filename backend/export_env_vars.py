#!/usr/bin/env python3
"""
Export environment variables from .env.enterprise in Windows batch format
"""

import os
from pathlib import Path

def export_env_vars():
    """Export environment variables in Windows batch format"""
    env_file = Path(__file__).parent / ".env.enterprise"
    
    if not env_file.exists():
        print(f"echo ❌ .env.enterprise not found at {env_file}")
        return False
    
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
                
                # Output as Windows SET command
                print(f"set {key}={value}")
    
    return True

if __name__ == "__main__":
    export_env_vars()