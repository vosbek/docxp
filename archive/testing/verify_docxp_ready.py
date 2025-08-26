#!/usr/bin/env python3
"""
DocXP Readiness Verification Script
Quickly checks if all components are properly configured and ready
"""

import sys
from pathlib import Path
import importlib.util

def check_imports():
    """Check if all required modules can be imported"""
    print("🔍 Checking Python imports...")
    
    required_modules = [
        ('fastapi', 'FastAPI framework'),
        ('neo4j', 'Neo4j Python driver'),
        ('pydantic', 'Pydantic for data validation'),
        ('sqlalchemy', 'SQLAlchemy for database ORM'),
        ('boto3', 'AWS SDK for Python'),
        ('opensearch_py', 'OpenSearch client')
    ]
    
    failed_imports = []
    
    for module_name, description in required_modules:
        try:
            spec = importlib.util.find_spec(module_name)
            if spec is None:
                failed_imports.append(f"❌ {module_name} ({description})")
            else:
                print(f"✅ {module_name} ({description})")
        except Exception as e:
            failed_imports.append(f"❌ {module_name} ({description}) - Error: {e}")
    
    if failed_imports:
        print("\n⚠️  Failed imports:")
        for failed in failed_imports:
            print(f"   {failed}")
        return False
    
    print("✅ All required modules are available")
    return True

def check_docxp_imports():
    """Check if DocXP specific modules can be imported"""
    print("\n🔍 Checking DocXP module imports...")
    
    try:
        # Add backend to path
        backend_dir = Path(__file__).parent
        sys.path.insert(0, str(backend_dir))
        
        # Test core imports
        from app.core.config import settings
        print("✅ Core configuration loaded")
        
        from app.services.knowledge_graph_service import KnowledgeGraphService
        print("✅ KnowledgeGraphService imported")
        
        from app.models.graph_entities import GraphNodeType, GraphRelationshipType
        print("✅ Graph entity models imported")
        
        from app.services.graph_migration_service import GraphMigrationService
        print("✅ Graph migration service imported")
        
        from app.services.graph_sync_service import GraphSyncService
        print("✅ Graph sync service imported")
        
        return True
        
    except ImportError as e:
        print(f"❌ DocXP import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error importing DocXP modules: {e}")
        return False

def check_configuration():
    """Check configuration settings"""
    print("\n🔍 Checking configuration...")
    
    try:
        from app.core.config import settings
        
        # Check Neo4j configuration
        print(f"📊 Neo4j URI: {settings.NEO4J_URI}")
        print(f"📊 Neo4j Database: {settings.NEO4J_DATABASE}")
        print(f"📊 Neo4j Enabled: {settings.NEO4J_ENABLED}")
        
        # Check database configuration
        print(f"📊 Database URL: {settings.DATABASE_URL}")
        
        # Check vector database configuration
        print(f"📊 Vector DB Type: {settings.VECTOR_DB_TYPE}")
        print(f"📊 Vector DB Enabled: {settings.VECTOR_DB_ENABLED}")
        
        # Check embedding configuration
        print(f"📊 Embedding Provider: {settings.EMBEDDING_PROVIDER}")
        
        print("✅ Configuration loaded successfully")
        return True
        
    except Exception as e:
        print(f"❌ Configuration check failed: {e}")
        return False

def check_file_structure():
    """Check if key files exist"""
    print("\n🔍 Checking file structure...")
    
    base_dir = Path(__file__).parent.parent
    
    required_files = [
        'docker-compose.yml',
        'backend/app/core/config.py',
        'backend/app/services/knowledge_graph_service.py',
        'backend/app/models/graph_entities.py',
        'backend/requirements.txt',
        'scripts/init-neo4j.cypher',
        'scripts/setup-neo4j.py'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        full_path = base_dir / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            missing_files.append(f"❌ {file_path}")
    
    if missing_files:
        print("\n⚠️  Missing files:")
        for missing in missing_files:
            print(f"   {missing}")
        return False
    
    print("✅ All required files are present")
    return True

def main():
    """Main verification function"""
    print("DocXP Readiness Verification")
    print("=" * 40)
    
    checks = [
        ("File Structure", check_file_structure),
        ("Python Imports", check_imports),
        ("DocXP Modules", check_docxp_imports),
        ("Configuration", check_configuration)
    ]
    
    passed = 0
    failed = 0
    
    for check_name, check_func in checks:
        print(f"\n{'-' * 20}")
        print(f"Running: {check_name}")
        print(f"{'-' * 20}")
        
        try:
            if check_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {check_name} failed with exception: {e}")
            failed += 1
    
    print(f"\n{'=' * 40}")
    print("VERIFICATION SUMMARY")
    print(f"{'=' * 40}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total:  {passed + failed}")
    
    if failed == 0:
        print("\n🎉 DocXP is ready for deployment!")
        print("\nNext steps:")
        print("1. Run: docker-compose up -d neo4j")
        print("2. Run: python scripts/setup-neo4j.py")
        print("3. Run: python test_knowledge_graph_integration.py")
        print("4. Run: docker-compose up -d")
        return 0
    else:
        print(f"\n⚠️  {failed} checks failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)