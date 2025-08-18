#!/usr/bin/env python3
"""
DocXP Service Connectivity Test
Test all core services and validate the setup
"""

import asyncio
import sys
import os
import logging
from typing import Dict, Any

# Add backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_neo4j_connection():
    """Test Neo4j connection and basic functionality"""
    try:
        from app.services.knowledge_graph_service import KnowledgeGraphService, GraphNode, NodeType
        
        logger.info("Testing Neo4j connection...")
        
        # Create service instance
        kg_service = KnowledgeGraphService()
        
        # Test connection
        connected = await kg_service.connect()
        if not connected:
            return {"status": "failed", "error": "Could not connect to Neo4j"}
        
        # Test basic node creation
        test_node = GraphNode(
            id="test_node_1",
            node_type=NodeType.CODE_ENTITY,
            properties={"name": "test", "type": "test_entity", "created_by": "connectivity_test"}
        )
        
        created = await kg_service.create_node(test_node)
        if not created:
            return {"status": "failed", "error": "Could not create test node"}
        
        # Get statistics
        stats = await kg_service.get_graph_statistics()
        
        await kg_service.disconnect()
        
        return {
            "status": "success", 
            "message": "Neo4j connection successful",
            "stats": stats
        }
        
    except Exception as e:
        return {"status": "failed", "error": str(e)}

async def test_redis_connection():
    """Test Redis connection"""
    try:
        import redis
        
        logger.info("Testing Redis connection...")
        
        r = redis.Redis(host='localhost', port=6379, db=0)
        
        # Test basic operations
        r.set('test_key', 'test_value')
        value = r.get('test_key')
        
        if value.decode() != 'test_value':
            return {"status": "failed", "error": "Redis read/write test failed"}
        
        # Clean up
        r.delete('test_key')
        
        return {"status": "success", "message": "Redis connection successful"}
        
    except Exception as e:
        return {"status": "failed", "error": str(e)}

async def test_opensearch_connection():
    """Test OpenSearch connection"""
    try:
        from opensearchpy import OpenSearch
        
        logger.info("Testing OpenSearch connection...")
        
        client = OpenSearch(
            hosts=[{'host': 'localhost', 'port': 9200}],
            http_compress=True,
            use_ssl=False,
            verify_certs=False,
            ssl_assert_hostname=False,
            ssl_show_warn=False,
        )
        
        # Test cluster health
        health = client.cluster.health()
        
        if health['status'] not in ['green', 'yellow']:
            return {"status": "failed", "error": f"OpenSearch cluster status: {health['status']}"}
        
        return {
            "status": "success", 
            "message": "OpenSearch connection successful",
            "cluster_status": health['status']
        }
        
    except Exception as e:
        return {"status": "failed", "error": str(e)}

async def test_postgres_connection():
    """Test PostgreSQL connection"""
    try:
        import asyncpg
        
        logger.info("Testing PostgreSQL connection...")
        
        conn = await asyncpg.connect(
            "postgresql://docxp_user:docxp_local_dev_2024@localhost:5432/docxp"
        )
        
        # Test basic query
        result = await conn.fetchval("SELECT 1")
        
        if result != 1:
            return {"status": "failed", "error": "PostgreSQL query test failed"}
        
        await conn.close()
        
        return {"status": "success", "message": "PostgreSQL connection successful"}
        
    except Exception as e:
        return {"status": "failed", "error": str(e)}

async def run_all_tests():
    """Run all service connectivity tests"""
    logger.info("🚀 Starting DocXP Service Connectivity Tests")
    logger.info("=" * 60)
    
    tests = [
        ("Neo4j Knowledge Graph", test_neo4j_connection),
        ("Redis Cache & Queue", test_redis_connection), 
        ("OpenSearch Hybrid Search", test_opensearch_connection),
        ("PostgreSQL Database", test_postgres_connection),
    ]
    
    results = {}
    all_passed = True
    
    for test_name, test_func in tests:
        logger.info(f"\n🔍 Testing {test_name}...")
        
        try:
            result = await test_func()
            results[test_name] = result
            
            if result["status"] == "success":
                logger.info(f"✅ {test_name}: {result['message']}")
                if 'stats' in result:
                    logger.info(f"   Stats: {result['stats']}")
                if 'cluster_status' in result:
                    logger.info(f"   Cluster Status: {result['cluster_status']}")
            else:
                logger.error(f"❌ {test_name}: {result['error']}")
                all_passed = False
                
        except Exception as e:
            logger.error(f"❌ {test_name}: Unexpected error - {e}")
            results[test_name] = {"status": "failed", "error": str(e)}
            all_passed = False
    
    logger.info("\n" + "=" * 60)
    if all_passed:
        logger.info("🎉 ALL TESTS PASSED! DocXP infrastructure is ready.")
        logger.info("\nNext steps:")
        logger.info("1. Start backend: cd backend && python -m uvicorn app.main:app --reload")
        logger.info("2. Access Neo4j Browser: http://localhost:7474 (neo4j/docxp-neo4j-2024)")
        logger.info("3. Access OpenSearch: http://localhost:9200")
        logger.info("4. Run graph migration to initialize schema")
    else:
        logger.error("❌ Some tests failed. Check the errors above.")
        
    return results, all_passed

if __name__ == "__main__":
    asyncio.run(run_all_tests())