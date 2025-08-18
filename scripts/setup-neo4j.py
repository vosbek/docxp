#!/usr/bin/env python3
"""
Neo4j Setup Script for DocXP
Initializes Neo4j database with constraints, indexes, and sample data
"""

import asyncio
import logging
import sys
from pathlib import Path
import time

# Add the backend directory to the path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.services.knowledge_graph_service import KnowledgeGraphService
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def wait_for_neo4j(max_attempts=30, delay=2):
    """Wait for Neo4j to be ready"""
    kg_service = KnowledgeGraphService()
    
    for attempt in range(max_attempts):
        try:
            logger.info(f"Attempt {attempt + 1}/{max_attempts}: Connecting to Neo4j...")
            success = await kg_service.connect()
            if success:
                logger.info("✅ Neo4j is ready!")
                await kg_service.disconnect()
                return True
        except Exception as e:
            logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
        
        if attempt < max_attempts - 1:
            logger.info(f"Waiting {delay} seconds before next attempt...")
            time.sleep(delay)
    
    logger.error("❌ Neo4j is not ready after maximum attempts")
    return False

async def run_cypher_file(kg_service, cypher_file_path):
    """Run a Cypher script file"""
    try:
        with open(cypher_file_path, 'r') as f:
            cypher_content = f.read()
        
        # Split into individual statements (basic splitting on semicolons)
        statements = [stmt.strip() for stmt in cypher_content.split(';') if stmt.strip()]
        
        logger.info(f"Executing {len(statements)} Cypher statements...")
        
        def execute_cypher_tx(tx, statement):
            try:
                result = tx.run(statement)
                return result.consume()
            except Exception as e:
                logger.warning(f"Statement execution warning: {e}")
                return None
        
        executed = 0
        for i, statement in enumerate(statements):
            # Skip comments and empty statements
            if statement.startswith('//') or not statement:
                continue
                
            try:
                with kg_service.driver.session(database=kg_service.neo4j_database) as session:
                    result = session.execute_write(execute_cypher_tx, statement)
                    executed += 1
                    logger.debug(f"Executed statement {i+1}: {statement[:50]}...")
            except Exception as e:
                logger.warning(f"Failed to execute statement {i+1}: {e}")
        
        logger.info(f"✅ Successfully executed {executed} Cypher statements")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to run Cypher file {cypher_file_path}: {e}")
        return False

async def setup_neo4j():
    """Main setup function"""
    logger.info("Starting Neo4j setup for DocXP...")
    
    # Wait for Neo4j to be ready
    if not await wait_for_neo4j():
        logger.error("Cannot proceed - Neo4j is not available")
        return False
    
    # Connect to Neo4j
    kg_service = KnowledgeGraphService()
    try:
        success = await kg_service.connect()
        if not success:
            logger.error("Failed to connect to Neo4j for setup")
            return False
        
        logger.info(f"Connected to Neo4j at {settings.NEO4J_URI}")
        
        # Run initialization script
        cypher_file = Path(__file__).parent / "init-neo4j.cypher"
        if cypher_file.exists():
            logger.info(f"Running initialization script: {cypher_file}")
            await run_cypher_file(kg_service, cypher_file)
        else:
            logger.warning(f"Initialization script not found: {cypher_file}")
        
        # Create indexes using the service
        logger.info("Creating optimized indexes...")
        await kg_service.create_indexes()
        
        # Get initial statistics
        logger.info("Getting initial graph statistics...")
        stats = await kg_service.get_graph_statistics()
        logger.info(f"Graph Statistics: {stats}")
        
        logger.info("✅ Neo4j setup completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Neo4j setup failed: {e}")
        return False
    finally:
        if kg_service.is_connected:
            await kg_service.disconnect()

async def main():
    """Main entry point"""
    try:
        success = await setup_neo4j()
        if success:
            logger.info("\n🎉 DocXP Neo4j database is ready!")
            logger.info("You can now:")
            logger.info("  - Access Neo4j Browser at http://localhost:7474")
            logger.info("  - Run the integration tests")
            logger.info("  - Start the DocXP backend service")
            return 0
        else:
            logger.error("\n💥 Setup failed - check logs for details")
            return 1
    except Exception as e:
        logger.error(f"💥 Setup script failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)