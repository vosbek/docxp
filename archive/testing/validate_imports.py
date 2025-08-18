#!/usr/bin/env python3
"""
Import Validation Script for DocXP
Validates all imports work before deployment to prevent runtime errors
"""

import sys
import importlib
import traceback
from pathlib import Path

def test_import(module_name):
    """Test importing a module"""
    try:
        importlib.import_module(module_name)
        print(f"OK {module_name}")
        return True
    except Exception as e:
        print(f"FAIL {module_name}: {e}")
        return False

def validate_core_imports():
    """Validate all core application imports"""
    print("=" * 60)
    print("DocXP Import Validation")
    print("=" * 60)
    
    success_count = 0
    total_count = 0
    
    # Core modules to test
    modules_to_test = [
        # Core modules
        "app.core.config",
        "app.core.database", 
        "app.core.logging_config",
        "app.core.validator",
        
        # Models
        "app.models.indexing_models",
        "app.models.schemas",
        "app.models",
        
        # Services
        "app.services.v1_indexing_service",
        "app.services.enhanced_v1_indexing_service", 
        "app.services.embedding_service",
        "app.services.jqassistant_service",
        "app.services.semgrep_service",
        
        # API modules
        "app.api.health",
        "app.api.v1_indexing",
        "app.api.v1.enhanced_indexing",
        "app.api.v1.jqassistant",
        "app.api.v1.semgrep",
    ]
    
    print("\nTesting core modules:")
    print("-" * 40)
    
    for module in modules_to_test:
        total_count += 1
        if test_import(module):
            success_count += 1
    
    print(f"\nResults: {success_count}/{total_count} imports successful")
    
    if success_count == total_count:
        print("SUCCESS: ALL IMPORTS SUCCESSFUL!")
        return True
    else:
        print("ERROR: IMPORT FAILURES DETECTED")
        return False

def test_specific_imports():
    """Test specific imports that were problematic"""
    print("\nTesting specific problem imports:")
    print("-" * 40)
    
    tests = [
        # Models imports
        ("IndexingJob", "from app.models import IndexingJob"),
        ("JobStatus", "from app.models.indexing_models import JobStatus"),
        ("FileStatus", "from app.models.indexing_models import FileStatus"),
        ("get_async_session", "from app.core.database import get_async_session"),
        
        # Service imports  
        ("V1IndexingService", "from app.services.v1_indexing_service import V1IndexingService"),
        ("EmbeddingService", "from app.services.embedding_service import EmbeddingService"),
    ]
    
    success_count = 0
    for name, import_stmt in tests:
        try:
            exec(import_stmt)
            print(f"OK {name}")
            success_count += 1
        except Exception as e:
            print(f"FAIL {name}: {e}")
    
    print(f"\nSpecific imports: {success_count}/{len(tests)} successful")
    return success_count == len(tests)

def test_database_functions():
    """Test database function usage patterns"""
    print("\nTesting database function usage:")
    print("-" * 40)
    
    try:
        from app.core.database import get_async_session
        
        # Test that it returns something that can be used as a context manager
        async_session = get_async_session()
        if hasattr(async_session, '__aenter__') and hasattr(async_session, '__aexit__'):
            print("OK get_async_session returns async context manager")
            return True
        else:
            print("FAIL get_async_session does not return async context manager")
            return False
            
    except Exception as e:
        print(f"FAIL Database function test failed: {e}")
        return False

def main():
    """Run all validation tests"""
    print("Starting DocXP import validation...\n")
    
    # Change to the correct directory
    script_dir = Path(__file__).parent
    sys.path.insert(0, str(script_dir))
    
    results = []
    
    # Run tests
    results.append(validate_core_imports())
    results.append(test_specific_imports()) 
    results.append(test_database_functions())
    
    # Final summary
    print("\n" + "=" * 60)
    if all(results):
        print("SUCCESS: ALL VALIDATION TESTS PASSED!")
        print("OK Application should start without import errors")
        sys.exit(0)
    else:
        print("ERROR: VALIDATION FAILED!")
        print("FAIL Fix import errors before starting application")
        sys.exit(1)

if __name__ == "__main__":
    main()