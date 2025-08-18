#!/usr/bin/env python3
"""
Validate Critical Breaking Changes Fixes
Tests all the critical fixes identified by Gemini CLI review
"""

import sys
import traceback

def test_base_model_import():
    """Test Base model import"""
    try:
        from app.models.base import Base
        print("OK - Base model import: PASSED")
        return True
    except Exception as e:
        print(f"FAIL - Base model import: {e}")
        return False

def test_repository_model_import():
    """Test Repository model import"""
    try:
        from app.core.database import Repository
        from app.models import Repository as ImportedRepository
        print("OK - Repository model import: PASSED")
        return True
    except Exception as e:
        print(f"FAIL - Repository model import: {e}")
        return False

def test_business_rule_trace_import():
    """Test BusinessRuleTrace model import"""
    try:
        from app.models.business_rule_trace import BusinessRuleTrace, FlowStep
        print("OK - BusinessRuleTrace model import: PASSED")
        return True
    except Exception as e:
        print(f"FAIL - BusinessRuleTrace model import: {e}")
        return False

def test_project_model_import():
    """Test Project model import"""
    try:
        from app.models.project import Project, ProjectRepository, ProjectPhase
        print("OK - Project model import: PASSED")
        return True
    except Exception as e:
        print(f"FAIL - Project model import: {e}")
        return False

def test_architectural_insight_import():
    """Test ArchitecturalInsight model import"""
    try:
        from app.models.architectural_insight import ArchitecturalInsight, InsightDependency
        print("OK - ArchitecturalInsight model import: PASSED")
        return True
    except Exception as e:
        print(f"FAIL - ArchitecturalInsight model import: {e}")
        return False

def test_domain_models_import():
    """Test Domain models import"""
    try:
        from app.models.business_domains import DomainTaxonomy, DomainClassificationRule
        print("OK - Domain models import: PASSED")
        return True
    except Exception as e:
        print(f"FAIL - Domain models import: {e}")
        return False

def test_models_init_import():
    """Test models __init__.py import"""
    try:
        from app.models import (
            Base, Repository, BusinessRuleTrace, Project, 
            ArchitecturalInsight, DomainTaxonomy
        )
        print("OK - Models __init__.py import: PASSED")
        return True
    except Exception as e:
        print(f"FAIL - Models __init__.py import: {e}")
        return False

def test_service_imports():
    """Test critical service imports"""
    try:
        from app.services.knowledge_graph_service import KnowledgeGraphService
        from app.services.domain_classifier_service import DomainClassifierService  
        from app.services.project_coordinator_service import ProjectCoordinatorService
        print("OK - Service imports: PASSED")
        return True
    except Exception as e:
        print(f"FAIL - Service imports: {e}")
        return False

def test_database_import():
    """Test database import"""
    try:
        from app.core.database import get_async_session, Base
        print("OK - Database import: PASSED")
        return True
    except Exception as e:
        print(f"FAIL - Database import: {e}")
        return False

def main():
    """Run all validation tests"""
    print("Validating Critical Breaking Changes Fixes...")
    print("=" * 60)
    
    tests = [
        test_base_model_import,
        test_repository_model_import,
        test_business_rule_trace_import,
        test_project_model_import,
        test_architectural_insight_import,
        test_domain_models_import,
        test_models_init_import,
        test_service_imports,
        test_database_import,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: EXCEPTION - {e}")
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("SUCCESS: ALL CRITICAL FIXES VALIDATED!")
        return True
    else:
        print("CRITICAL ISSUES STILL EXIST!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)