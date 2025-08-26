#!/usr/bin/env python3
"""
Startup validation script for DocXP
Tests that all imports and configurations work without runtime errors
"""

import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_config_import():
    """Test that configuration loads without errors"""
    try:
        from app.core.config import settings
        logger.info("✅ Configuration loaded successfully")
        
        # Test critical fields
        critical_fields = [
            'OPENSEARCH_INDEX_NAME', 'OPENSEARCH_URL', 'OPENSEARCH_HOST',
            'NEO4J_URI', 'REDIS_URL', 'DATABASE_URL'
        ]
        
        for field in critical_fields:
            if hasattr(settings, field):
                logger.info(f"✅ {field}: {getattr(settings, field)}")
            else:
                logger.error(f"❌ Missing field: {field}")
                return False
        
        return True
    except Exception as e:
        logger.error(f"❌ Configuration import failed: {e}")
        return False

def test_service_imports():
    """Test that all service imports work"""
    services_to_test = [
        'app.services.strands_agent_service',
        'app.services.knowledge_graph_service', 
        'app.services.project_coordinator_service',
        'app.core.opensearch_setup'
    ]
    
    for service in services_to_test:
        try:
            __import__(service)
            logger.info(f"✅ {service} imported successfully")
        except Exception as e:
            logger.error(f"❌ {service} import failed: {e}")
            return False
    
    return True

def test_api_imports():
    """Test that API modules import without errors"""
    try:
        from app.api import (
            documentation, repositories, analytics, configuration, 
            health, aws_configuration, semantic_search, 
            repository_processing, strands_agents, hybrid_search, v1_indexing
        )
        logger.info("✅ All API modules imported successfully")
        return True
    except Exception as e:
        logger.error(f"❌ API import failed: {e}")
        return False

def main():
    """Run all startup validation tests"""
    logger.info("🚀 DocXP Startup Validation")
    logger.info("=" * 50)
    
    tests = [
        ("Configuration", test_config_import),
        ("Service Imports", test_service_imports), 
        ("API Imports", test_api_imports)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Testing {test_name}...")
        result = test_func()
        results.append((test_name, result))
    
    logger.info("\n" + "=" * 50)
    logger.info("📊 VALIDATION RESULTS")
    logger.info("=" * 50)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        logger.info("\n🎉 ALL TESTS PASSED - DocXP should start successfully!")
        return 0
    else:
        logger.error("\n💥 VALIDATION FAILED - Fix errors before starting DocXP")
        return 1

if __name__ == "__main__":
    sys.exit(main())