#!/usr/bin/env python3
"""
Comprehensive Import Testing Script for DocXP Backend
Tests all import chains and identifies missing classes/modules
"""

import sys
import traceback
import importlib
from pathlib import Path

def test_import(module_name, item_name=None):
    """Test importing a module or specific item from module"""
    try:
        if item_name:
            module = importlib.import_module(module_name)
            if not hasattr(module, item_name):
                return False, f"Module {module_name} exists but missing {item_name}"
            return True, f"OK {module_name}.{item_name}"
        else:
            importlib.import_module(module_name)
            return True, f"OK {module_name}"
    except ImportError as e:
        return False, f"FAIL {module_name}: {e}"
    except Exception as e:
        return False, f"FAIL {module_name}: {type(e).__name__}: {e}"

def test_backend_imports():
    """Test all critical backend imports"""
    print("=" * 60)
    print("COMPREHENSIVE BACKEND IMPORT TEST")
    print("=" * 60)
    
    # Test main application imports first
    print("\n1. MAIN APPLICATION IMPORTS:")
    main_imports = [
        "app.core.config",
        "app.core.database", 
        "app.models.indexing_models",
        "app.api.v1",
    ]
    
    for module in main_imports:
        success, msg = test_import(module)
        print(f"   {msg}")
        if not success:
            print(f"      CRITICAL: Main app cannot start without {module}")
    
    # Test API route imports
    print("\n2. API ROUTE IMPORTS:")
    api_imports = [
        ("app.api.v1.enhanced_indexing", None),
        ("app.api.v1.jqassistant", None),
        ("app.api.v1.semgrep", None),
    ]
    
    for module, item in api_imports:
        success, msg = test_import(module, item)
        print(f"   {msg}")
    
    # Test service imports (critical chain)
    print("\n3. SERVICE IMPORTS:")
    service_imports = [
        ("app.services.enhanced_v1_indexing_service", "get_enhanced_v1_indexing_service"),
        ("app.services.jqassistant_batch_service", "get_jqassistant_batch_service"),
        ("app.services.jqassistant_service", "JQAssistantService"),
        ("app.services.jqassistant_service", "JQAssistantAnalysisResult"),
        ("app.services.jqassistant_service", "get_jqassistant_service"),
        ("app.services.v1_indexing_service", "get_v1_indexing_service"),
        ("app.services.strands_agent_service", "get_strands_agent_service"),
        ("app.services.semantic_ai_service", "get_semantic_ai_service"),
        ("app.services.ai_service", "AIService"),
        ("app.services.embedding_service", "get_embedding_service"),
        ("app.services.hybrid_search_service", "get_hybrid_search_service"),
    ]
    
    for module, item in service_imports:
        success, msg = test_import(module, item)
        print(f"   {msg}")
    
    # Test model imports
    print("\n4. MODEL IMPORTS:")
    model_imports = [
        ("app.models.indexing_models", "IndexingJob"),
        ("app.models.indexing_models", "JobType"), 
        ("app.models.indexing_models", "JobStatus"),
        ("app.models.indexing_models", "FileProcessingRecord"),
        ("app.models.indexing_models", "RepositorySnapshot"),
    ]
    
    for module, item in model_imports:
        success, msg = test_import(module, item)
        print(f"   {msg}")
    
    # Test parser imports
    print("\n5. PARSER IMPORTS:")
    parser_imports = [
        ("app.parsers.parser_factory", "get_parser_for_file"),
        ("app.parsers.base_parser", "BaseParser"),
        ("app.parsers.python_parser", "PythonParser"),
        ("app.parsers.angular_parser", "AngularParser"),
    ]
    
    for module, item in parser_imports:
        success, msg = test_import(module, item)
        print(f"   {msg}")
    
    # Test core imports
    print("\n6. CORE IMPORTS:")
    core_imports = [
        ("app.core.opensearch_setup", "get_opensearch_client"),
        ("app.core.opensearch_setup", "is_opensearch_available"),
        ("app.core.vector_database", None),
    ]
    
    for module, item in core_imports:
        success, msg = test_import(module, item)
        print(f"   {msg}")

def simulate_startup_imports():
    """Simulate the exact import chain that happens during startup"""
    print("\n" + "=" * 60)
    print("STARTUP SIMULATION TEST")
    print("=" * 60)
    
    startup_chain = [
        "main",
        "app.api.v1.enhanced_indexing",
        "app.services.enhanced_v1_indexing_service", 
        "app.services.jqassistant_batch_service",
        "app.services.jqassistant_service",
    ]
    
    print("\nTesting startup import chain:")
    for i, module in enumerate(startup_chain):
        print(f"{i+1}. Importing {module}...")
        success, msg = test_import(module)
        print(f"   {msg}")
        if not success:
            print(f"   BLOCKED: STARTUP BLOCKED at step {i+1}")
            return False
    
    print("\nOK Startup import chain complete!")
    return True

def identify_missing_classes():
    """Identify specific missing classes that need to be created"""
    print("\n" + "=" * 60)
    print("MISSING CLASSES ANALYSIS")
    print("=" * 60)
    
    # Check each service file for missing classes
    missing_classes = []
    
    # JQAssistant service missing classes
    try:
        from app.services.jqassistant_service import JQAssistantService
        print("OK JQAssistantService found")
    except ImportError:
        missing_classes.append("JQAssistantService in app.services.jqassistant_service")
    
    try:
        from app.services.jqassistant_service import JQAssistantAnalysisResult
        print("OK JQAssistantAnalysisResult found") 
    except ImportError:
        missing_classes.append("JQAssistantAnalysisResult in app.services.jqassistant_service")
        print("FAIL JQAssistantAnalysisResult missing - needs to be created")
    
    # Check for other missing service classes
    service_classes = [
        ("app.services.enhanced_v1_indexing_service", "EnhancedV1IndexingService"),
        ("app.services.embedding_service", "EmbeddingService"),
        ("app.services.hybrid_search_service", "HybridSearchService"),
    ]
    
    for module, class_name in service_classes:
        try:
            mod = importlib.import_module(module)
            if hasattr(mod, class_name):
                print(f"OK {class_name} found in {module}")
            else:
                missing_classes.append(f"{class_name} in {module}")
                print(f"FAIL {class_name} missing from {module}")
        except ImportError as e:
            missing_classes.append(f"{module} (entire module)")
            print(f"FAIL Cannot import {module}: {e}")
    
    if missing_classes:
        print(f"\nMISSING CLASSES TO CREATE ({len(missing_classes)}):")
        for i, missing in enumerate(missing_classes, 1):
            print(f"   {i}. {missing}")
    else:
        print("\nOK All required classes found!")
    
    return missing_classes

def main():
    """Run comprehensive import testing"""
    print("Starting comprehensive backend import analysis...")
    
    # Test all imports
    test_backend_imports()
    
    # Test startup simulation
    startup_success = simulate_startup_imports()
    
    # Identify missing classes
    missing_classes = identify_missing_classes()
    
    # Summary
    print("\n" + "=" * 60)
    print("ANALYSIS SUMMARY")
    print("=" * 60)
    
    if startup_success:
        print("OK Startup import chain works")
    else:
        print("FAIL Startup import chain blocked")
    
    if missing_classes:
        print(f"FAIL {len(missing_classes)} missing classes need to be created")
        print("\nPRIORITY FIXES NEEDED:")
        for i, missing in enumerate(missing_classes[:5], 1):
            print(f"   {i}. Create {missing}")
    else:
        print("OK All required classes present")
    
    print(f"\nRun this script on the target machine to identify issues:")
    print(f"python comprehensive_import_test.py")

if __name__ == "__main__":
    main()