#!/usr/bin/env python3
"""
Test script to verify that our integration_analyzer dataclass fixes work
and that all imports are correctly resolved.
"""

def test_dataclass_imports():
    """Test that dataclasses can be imported without errors"""
    try:
        from app.services.integration_analyzer import HTTPCall, RESTEndpoint, StrutsAction, JSPComponent, IntegrationFlow
        print("✅ Successfully imported all dataclasses from integration_analyzer")
        
        # Test that we can create instances
        http_call = HTTPCall(
            source_file="test.js",
            line_number=10,
            method="GET",
            url_pattern="/api/test",
            parameters=["param1", "param2"]
        )
        print(f"✅ Successfully created HTTPCall instance: {http_call}")
        
        rest_endpoint = RESTEndpoint(
            source_file="test.java",
            line_number=20,
            method="GET",
            path="/api/test",
            handler_function="handleTest",
            parameters=["id", "name"]
        )
        print(f"✅ Successfully created RESTEndpoint instance: {rest_endpoint}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error importing dataclasses: {e}")
        return False

def test_service_imports():
    """Test that our main services can be imported"""
    try:
        from app.services.integration_analyzer import integration_analyzer
        print("✅ Successfully imported integration_analyzer singleton")
        
        from app.services.migration_dashboard import migration_dashboard
        print("✅ Successfully imported migration_dashboard singleton")
        
        from app.services.diagram_service import DiagramService
        print("✅ Successfully imported DiagramService class")
        
        return True
        
    except Exception as e:
        print(f"❌ Error importing services: {e}")
        return False

def test_documentation_service_import():
    """Test that DocumentationService can be imported (this was causing the original error)"""
    try:
        from app.services.documentation_service import DocumentationService
        print("✅ Successfully imported DocumentationService")
        return True
        
    except Exception as e:
        print(f"❌ Error importing DocumentationService: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Testing DocXP Integration Fixes...")
    print("=" * 50)
    
    # Test in order of dependency
    dataclass_ok = test_dataclass_imports()
    print()
    
    service_ok = test_service_imports()
    print()
    
    doc_service_ok = test_documentation_service_import()
    print()
    
    if all([dataclass_ok, service_ok, doc_service_ok]):
        print("🎉 All tests passed! The dataclass error should be resolved.")
        print("✅ Integration fixes are working correctly.")
    else:
        print("❌ Some tests failed. Check the error messages above.")
        
    print("=" * 50)