#!/usr/bin/env python3
"""
Pre-flight check script to validate environment before starting DocXP
Run this before starting the application to ensure everything is configured correctly.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent))

from app.core.validator import EnvironmentValidator

def print_banner():
    """Print a nice banner for the validation script"""
    banner = """
    ╔══════════════════════════════════════════════════════╗
    ║          DocXP Environment Validation Check           ║
    ╚══════════════════════════════════════════════════════╝
    """
    print(banner)

def print_section(title: str):
    """Print a section header"""
    print(f"\n{'='*50}")
    print(f"  {title}")
    print('='*50)

def main():
    """Run the validation checks"""
    print_banner()
    print("\nValidating DocXP environment and dependencies...\n")
    
    # Create validator instance
    validator = EnvironmentValidator()
    
    # Run all validations
    is_valid, results = validator.validate_all()
    
    # Print results by category
    if results['info']:
        print_section("✅ VALIDATED COMPONENTS")
        for info in results['info']:
            print(f"  ✓ {info}")
    
    if results['warnings']:
        print_section("⚠️  WARNINGS")
        for warning in results['warnings']:
            print(f"  ⚠ {warning}")
    
    if results['errors']:
        print_section("❌ ERRORS - MUST FIX")
        for error in results['errors']:
            print(f"  ✗ {error}")
    
    # Print summary
    print("\n" + "="*50)
    if is_valid:
        print("✅ VALIDATION PASSED - DocXP is ready to start!")
        print("="*50)
        print("\nYou can now run:")
        print("  • Windows: start.bat")
        print("  • Linux/Mac: ./start.sh")
        print("  • Or manually: python main.py")
        
        # Create validation marker file
        Path(".validated").touch()
        
        # Return success
        sys.exit(0)
    else:
        print("❌ VALIDATION FAILED")
        print("="*50)
        print(f"\nFound {len(results['errors'])} error(s) that must be fixed.")
        print("Please address the issues above and run this script again.")
        
        # Remove validation marker if it exists
        validation_marker = Path(".validated")
        if validation_marker.exists():
            validation_marker.unlink()
        
        # Return failure
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nValidation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error during validation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
