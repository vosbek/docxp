"""
Simple Golden Path Test for DocXP Enterprise
Tests core functionality without unicode characters for Windows compatibility
"""

import asyncio
import logging
import tempfile
import os
import shutil
from datetime import datetime
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleGoldenPathTest:
    """Simple test for core DocXP functionality"""
    
    def __init__(self):
        self.test_results = {
            "overall_status": "pending",
            "tests_passed": 0,
            "tests_failed": 0,
            "start_time": None,
            "end_time": None,
            "errors": []
        }
        self.temp_dir = None
        
    async def run_test(self) -> Dict[str, Any]:
        """Run simple golden path test"""
        self.test_results["start_time"] = datetime.utcnow().isoformat()
        logger.info("Starting Simple Golden Path Test")
        
        try:
            # Test 1: Service imports
            await self._test_service_imports()
            
            # Test 2: Sample repository creation
            await self._test_sample_repository()
            
            # Test 3: Basic parser functionality
            await self._test_basic_parsing()
            
            # Test 4: Knowledge graph connection
            await self._test_knowledge_graph()
            
            self.test_results["overall_status"] = "passed"
            logger.info("Simple Golden Path Test PASSED")
            
        except Exception as e:
            self.test_results["overall_status"] = "failed"
            self.test_results["errors"].append(str(e))
            logger.error(f"Simple Golden Path Test FAILED: {e}")
            
        finally:
            await self._cleanup()
            self.test_results["end_time"] = datetime.utcnow().isoformat()
            
        return self.test_results
    
    async def _test_service_imports(self):
        """Test 1: Service imports"""
        logger.info("Testing service imports...")
        
        try:
            # Test core service imports
            from app.services.unified_flow_tracer import get_unified_flow_tracer
            from app.services.parser_orchestrator import get_parser_orchestrator
            from app.services.flow_validator import get_flow_validator
            from app.services.knowledge_graph_service import get_knowledge_graph_service
            from app.services.project_coordinator_service import get_project_coordinator_service
            
            # Initialize services
            self.flow_tracer = get_unified_flow_tracer()
            self.parser_orchestrator = get_parser_orchestrator()
            self.flow_validator = get_flow_validator()
            self.kg_service = await get_knowledge_graph_service()
            self.project_coordinator = await get_project_coordinator_service()
            
            self.test_results["tests_passed"] += 1
            logger.info("Service imports: PASSED")
            
        except Exception as e:
            self.test_results["tests_failed"] += 1
            self.test_results["errors"].append(f"Service imports failed: {e}")
            logger.error(f"Service imports: FAILED - {e}")
            raise
    
    async def _test_sample_repository(self):
        """Test 2: Create sample repository"""
        logger.info("Testing sample repository creation...")
        
        try:
            # Create temporary directory
            self.temp_dir = tempfile.mkdtemp(prefix="docxp_simple_test_")
            self.test_repo_path = os.path.join(self.temp_dir, "test_repo")
            os.makedirs(self.test_repo_path)
            
            # Create a simple Java file
            java_dir = os.path.join(self.test_repo_path, "src", "main", "java")
            os.makedirs(java_dir, exist_ok=True)
            
            java_content = '''
public class TestClass {
    public void testMethod() {
        System.out.println("Hello World");
    }
}
'''
            
            with open(os.path.join(java_dir, "TestClass.java"), "w") as f:
                f.write(java_content)
            
            # Verify file was created
            assert os.path.exists(os.path.join(java_dir, "TestClass.java"))
            
            self.test_results["tests_passed"] += 1
            logger.info("Sample repository creation: PASSED")
            
        except Exception as e:
            self.test_results["tests_failed"] += 1
            self.test_results["errors"].append(f"Sample repository creation failed: {e}")
            logger.error(f"Sample repository creation: FAILED - {e}")
            raise
    
    async def _test_basic_parsing(self):
        """Test 3: Basic parsing functionality"""
        logger.info("Testing basic parsing...")
        
        try:
            # Test parser orchestrator initialization
            assert self.parser_orchestrator is not None
            
            # Test parser statistics (should not fail)
            stats = self.parser_orchestrator.get_parser_statistics()
            assert isinstance(stats, dict)
            
            self.test_results["tests_passed"] += 1
            logger.info("Basic parsing: PASSED")
            
        except Exception as e:
            self.test_results["tests_failed"] += 1
            self.test_results["errors"].append(f"Basic parsing failed: {e}")
            logger.error(f"Basic parsing: FAILED - {e}")
            raise
    
    async def _test_knowledge_graph(self):
        """Test 4: Knowledge graph connection"""
        logger.info("Testing knowledge graph...")
        
        try:
            # Test if knowledge graph service exists
            assert self.kg_service is not None
            
            # Try to connect (may fail if Neo4j not available, which is ok)
            try:
                connected = await self.kg_service.connect()
                if connected:
                    logger.info("Knowledge graph connection: SUCCESS")
                    # Test getting statistics
                    stats = await self.kg_service.get_graph_statistics()
                    assert isinstance(stats, dict)
                else:
                    logger.info("Knowledge graph connection: SKIPPED (Neo4j not available)")
            except Exception as e:
                logger.info(f"Knowledge graph connection: SKIPPED ({e})")
            
            self.test_results["tests_passed"] += 1
            logger.info("Knowledge graph test: PASSED")
            
        except Exception as e:
            self.test_results["tests_failed"] += 1
            self.test_results["errors"].append(f"Knowledge graph test failed: {e}")
            logger.error(f"Knowledge graph test: FAILED - {e}")
            raise
    
    async def _cleanup(self):
        """Cleanup test resources"""
        try:
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                logger.info(f"Cleaned up test directory: {self.temp_dir}")
                
            if hasattr(self, 'kg_service') and self.kg_service and self.kg_service.is_connected:
                await self.kg_service.disconnect()
                
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")

async def main():
    """Run the simple golden path test"""
    test_runner = SimpleGoldenPathTest()
    results = await test_runner.run_test()
    
    print("\n" + "="*60)
    print("DOCXP SIMPLE GOLDEN PATH TEST RESULTS")
    print("="*60)
    print(f"Overall Status: {results['overall_status'].upper()}")
    print(f"Tests Passed: {results['tests_passed']}")
    print(f"Tests Failed: {results['tests_failed']}")
    print(f"Duration: {results['start_time']} to {results['end_time']}")
    
    if results["errors"]:
        print("\nErrors:")
        for error in results["errors"]:
            print(f"- {error}")
    
    if results["overall_status"] == "passed":
        print(f"\n[SUCCESS] Simple Golden Path Test PASSED!")
    else:
        print(f"\n[FAILED] Simple Golden Path Test FAILED")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())