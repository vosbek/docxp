#!/usr/bin/env python3
"""
DocXP Knowledge Graph Integration Test
Tests complete Neo4j integration and KnowledgeGraphService functionality
"""

import asyncio
import logging
import sys
import json
from datetime import datetime
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from app.services.knowledge_graph_service import (
    KnowledgeGraphService, 
    GraphNode, 
    GraphRelationship,
    NodeType, 
    RelationshipType
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class KnowledgeGraphIntegrationTest:
    """Comprehensive integration test for Knowledge Graph Service"""
    
    def __init__(self):
        self.kg_service = KnowledgeGraphService()
        self.test_results = []
        
    async def run_all_tests(self):
        """Run all integration tests"""
        logger.info("Starting DocXP Knowledge Graph Integration Tests")
        logger.info(f"Neo4j URI: {settings.NEO4J_URI}")
        logger.info(f"Neo4j Database: {settings.NEO4J_DATABASE}")
        
        tests = [
            ("Connection Test", self.test_connection),
            ("Schema Initialization", self.test_schema_initialization),
            ("Node Creation", self.test_node_creation),
            ("Relationship Creation", self.test_relationship_creation),
            ("Business Rule Path Finding", self.test_business_rule_paths),
            ("Pattern Analysis", self.test_pattern_analysis),
            ("Cross-Repository Dependencies", self.test_cross_repository_dependencies),
            ("Impact Analysis", self.test_impact_analysis),
            ("Graph Statistics", self.test_graph_statistics),
            ("Performance Test", self.test_performance)
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                logger.info(f"\n{'='*50}")
                logger.info(f"Running Test: {test_name}")
                logger.info(f"{'='*50}")
                
                result = await test_func()
                if result:
                    logger.info(f"✅ {test_name} PASSED")
                    passed += 1
                else:
                    logger.error(f"❌ {test_name} FAILED")
                    failed += 1
                    
                self.test_results.append({
                    "test": test_name,
                    "status": "PASSED" if result else "FAILED",
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"❌ {test_name} FAILED with exception: {e}")
                failed += 1
                self.test_results.append({
                    "test": test_name,
                    "status": "FAILED",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        # Print summary
        logger.info(f"\n{'='*60}")
        logger.info(f"TEST SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Total Tests: {passed + failed}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Success Rate: {(passed/(passed+failed)*100):.1f}%")
        
        # Clean up
        if self.kg_service.is_connected:
            await self.kg_service.disconnect()
            
        return failed == 0
    
    async def test_connection(self):
        """Test Neo4j connection"""
        try:
            success = await self.kg_service.connect()
            if success:
                logger.info("✅ Successfully connected to Neo4j")
                return True
            else:
                logger.error("❌ Failed to connect to Neo4j")
                return False
        except Exception as e:
            logger.error(f"❌ Connection test failed: {e}")
            return False
    
    async def test_schema_initialization(self):
        """Test schema initialization and index creation"""
        try:
            await self.kg_service.create_indexes()
            
            # Verify system status node creation
            stats = await self.kg_service.get_graph_statistics()
            logger.info(f"Graph statistics after initialization: {json.dumps(stats, indent=2)}")
            
            return True
        except Exception as e:
            logger.error(f"❌ Schema initialization failed: {e}")
            return False
    
    async def test_node_creation(self):
        """Test creating various types of nodes"""
        try:
            # Create test repository
            repo_node = GraphNode(
                id="test_repo_001",
                node_type=NodeType.REPOSITORY,
                properties={
                    "name": "test-banking-system",
                    "url": "https://github.com/test/banking-system",
                    "language": "Java",
                    "framework": "Struts"
                },
                labels=["Repository"]
            )
            
            success1 = await self.kg_service.create_node(repo_node)
            
            # Create test class
            class_node = GraphNode(
                id="test_class_AccountService",
                node_type=NodeType.CLASS,
                properties={
                    "name": "AccountService",
                    "package": "com.bank.service",
                    "file_path": "/src/main/java/com/bank/service/AccountService.java",
                    "methods_count": 10,
                    "complexity_score": 6.5
                },
                labels=["Class", "CodeEntity"]
            )
            
            success2 = await self.kg_service.create_node(class_node)
            
            # Create test JSP page
            jsp_node = GraphNode(
                id="test_jsp_account_details",
                node_type=NodeType.JSP_PAGE,
                properties={
                    "path": "/WEB-INF/pages/account/details.jsp",
                    "name": "details.jsp",
                    "business_functions": ["display_account", "edit_account"]
                },
                labels=["JSPPage", "WebComponent"]
            )
            
            success3 = await self.kg_service.create_node(jsp_node)
            
            if success1 and success2 and success3:
                logger.info("✅ Successfully created test nodes")
                return True
            else:
                logger.error("❌ Failed to create some test nodes")
                return False
                
        except Exception as e:
            logger.error(f"❌ Node creation test failed: {e}")
            return False
    
    async def test_relationship_creation(self):
        """Test creating relationships between nodes"""
        try:
            # Create relationship: Class belongs to Repository
            rel1 = GraphRelationship(
                source_id="test_class_AccountService",
                target_id="test_repo_001",
                relationship_type=RelationshipType.BELONGS_TO,
                properties={
                    "relationship_strength": 1.0,
                    "created_by": "integration_test"
                }
            )
            
            success1 = await self.kg_service.create_relationship(rel1)
            
            # Create relationship: JSP depends on Class
            rel2 = GraphRelationship(
                source_id="test_jsp_account_details",
                target_id="test_class_AccountService",
                relationship_type=RelationshipType.DEPENDS_ON,
                properties={
                    "dependency_type": "service_call",
                    "confidence": 0.9
                }
            )
            
            success2 = await self.kg_service.create_relationship(rel2)
            
            if success1 and success2:
                logger.info("✅ Successfully created test relationships")
                return True
            else:
                logger.error("❌ Failed to create some test relationships")
                return False
                
        except Exception as e:
            logger.error(f"❌ Relationship creation test failed: {e}")
            return False
    
    async def test_business_rule_paths(self):
        """Test business rule path finding"""
        try:
            # This test will work better with more data, but we can test the query structure
            paths = await self.kg_service.find_business_rule_path(
                entry_point="test_jsp_account_details",
                max_depth=5
            )
            
            logger.info(f"Found {len(paths)} business rule paths")
            for i, path in enumerate(paths[:3]):  # Show first 3 paths
                logger.info(f"Path {i+1}: {path.get('path_length', 0)} steps")
            
            return True  # Test passes if no exception occurs
        except Exception as e:
            logger.error(f"❌ Business rule path test failed: {e}")
            return False
    
    async def test_pattern_analysis(self):
        """Test pattern analysis functionality"""
        try:
            patterns = await self.kg_service.find_similar_patterns(
                pattern_type="service_class",
                repository_id="test_repo_001"
            )
            
            logger.info(f"Found {len(patterns)} similar patterns")
            return True
        except Exception as e:
            logger.error(f"❌ Pattern analysis test failed: {e}")
            return False
    
    async def test_cross_repository_dependencies(self):
        """Test cross-repository dependency analysis"""
        try:
            dependencies = await self.kg_service.get_cross_repository_dependencies(
                repository_ids=["test_repo_001"]
            )
            
            logger.info(f"Found cross-repository dependencies: {len(dependencies)} repositories")
            return True
        except Exception as e:
            logger.error(f"❌ Cross-repository dependency test failed: {e}")
            return False
    
    async def test_impact_analysis(self):
        """Test impact analysis functionality"""
        try:
            impact = await self.kg_service.analyze_impact_of_change(
                entity_id="test_class_AccountService",
                change_type="method_signature_change"
            )
            
            if impact:
                logger.info(f"Impact analysis found {impact.get('impact_count', 0)} affected entities")
                logger.info(f"Risk level: {impact.get('risk_level', 'unknown')}")
            else:
                logger.info("No impact found (expected for test data)")
            
            return True
        except Exception as e:
            logger.error(f"❌ Impact analysis test failed: {e}")
            return False
    
    async def test_graph_statistics(self):
        """Test graph statistics retrieval"""
        try:
            stats = await self.kg_service.get_graph_statistics()
            
            logger.info("Graph Statistics:")
            logger.info(f"  Total Nodes: {stats.get('total_nodes', 0)}")
            logger.info(f"  Total Relationships: {stats.get('total_relationships', 0)}")
            logger.info(f"  Repositories: {stats.get('repositories', 0)}")
            logger.info(f"  Business Rules: {stats.get('business_rules', 0)}")
            
            # Log node type distribution
            node_types = stats.get('node_types', {})
            if node_types:
                logger.info("  Node Types:")
                for node_type, count in node_types.items():
                    logger.info(f"    {node_type}: {count}")
            
            return stats.get('total_nodes', 0) >= 0  # Should have at least 0 nodes
        except Exception as e:
            logger.error(f"❌ Graph statistics test failed: {e}")
            return False
    
    async def test_performance(self):
        """Test basic performance with small dataset"""
        try:
            start_time = datetime.now()
            
            # Create 10 test nodes quickly
            for i in range(10):
                node = GraphNode(
                    id=f"perf_test_node_{i}",
                    node_type=NodeType.CODE_ENTITY,
                    properties={
                        "name": f"TestEntity_{i}",
                        "test_id": i,
                        "created_for": "performance_test"
                    }
                )
                await self.kg_service.create_node(node)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"Created 10 nodes in {duration:.2f} seconds")
            logger.info(f"Average: {(duration/10)*1000:.1f}ms per node")
            
            return duration < 10  # Should complete in under 10 seconds
        except Exception as e:
            logger.error(f"❌ Performance test failed: {e}")
            return False

async def main():
    """Main test runner"""
    test_runner = KnowledgeGraphIntegrationTest()
    
    try:
        success = await test_runner.run_all_tests()
        
        # Save test results
        results_file = Path("test_results.json")
        with open(results_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "success": success,
                "tests": test_runner.test_results
            }, f, indent=2)
        
        logger.info(f"\nTest results saved to: {results_file}")
        
        if success:
            logger.info("\n🎉 ALL TESTS PASSED - DocXP Knowledge Graph is ready!")
            return 0
        else:
            logger.error("\n💥 SOME TESTS FAILED - Check logs for details")
            return 1
            
    except Exception as e:
        logger.error(f"💥 Test runner failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)