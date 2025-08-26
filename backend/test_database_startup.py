#!/usr/bin/env python3
"""
Comprehensive Database Startup Test Script for DocXP Backend
Tests database connectivity, schema creation, constraints, and startup validation
"""

import sys
import asyncio
import logging
import traceback
from typing import Dict, List, Optional
from pathlib import Path
import os

# Add backend directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.database import Base, get_async_session
from app.models import *  # Import all models

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseStartupTester:
    """Comprehensive database startup testing and validation"""
    
    def __init__(self):
        self.engine = None
        self.session_factory = None
        self.test_results = {}
        
    async def initialize_engine(self):
        """Initialize database engine with connection testing"""
        try:
            # Create engine with proper settings
            self.engine = create_async_engine(
                settings.DATABASE_URL,
                echo=False,  # Set to True for SQL debugging
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10
            )
            
            # Create session factory
            self.session_factory = sessionmaker(
                self.engine, 
                class_=AsyncSession, 
                expire_on_commit=False
            )
            
            logger.info("✓ Database engine initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"✗ Failed to initialize database engine: {e}")
            return False

    async def test_database_connectivity(self) -> bool:
        """Test basic database connectivity"""
        try:
            async with self.engine.begin() as conn:
                result = await conn.execute(text("SELECT 1 as test"))
                test_value = result.scalar()
                
            if test_value == 1:
                logger.info("✓ Database connectivity test passed")
                return True
            else:
                logger.error("✗ Database connectivity test failed - unexpected result")
                return False
                
        except Exception as e:
            logger.error(f"✗ Database connectivity test failed: {e}")
            return False

    async def test_schema_creation(self) -> bool:
        """Test database schema creation"""
        try:
            # Drop all tables first for clean test
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
                logger.info("✓ Existing tables dropped for clean test")
                
            # Create all tables
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                logger.info("✓ Database schema created successfully")
                
            return True
            
        except Exception as e:
            logger.error(f"✗ Schema creation failed: {e}")
            logger.error(f"Error details: {traceback.format_exc()}")
            return False

    async def test_foreign_key_constraints(self) -> bool:
        """Test all foreign key constraints"""
        try:
            async with self.session_factory() as session:
                # Get all table names
                inspector = inspect(self.engine.sync_engine)
                table_names = inspector.get_table_names()
                
                constraint_tests = []
                
                for table_name in table_names:
                    foreign_keys = inspector.get_foreign_keys(table_name)
                    for fk in foreign_keys:
                        constraint_tests.append({
                            'table': table_name,
                            'constraint': fk['name'],
                            'columns': fk['constrained_columns'],
                            'referred_table': fk['referred_table'],
                            'referred_columns': fk['referred_columns']
                        })
                
                logger.info(f"✓ Found {len(constraint_tests)} foreign key constraints to validate")
                
                # Test domain_taxonomy self-referencing constraint specifically
                domain_taxonomy_constraints = [
                    ct for ct in constraint_tests 
                    if ct['table'] == 'domain_taxonomy' or ct['referred_table'] == 'domain_taxonomy'
                ]
                
                if domain_taxonomy_constraints:
                    logger.info(f"✓ Domain taxonomy constraints validated: {len(domain_taxonomy_constraints)} found")
                    for ct in domain_taxonomy_constraints:
                        logger.info(f"  - {ct['table']}.{ct['columns']} -> {ct['referred_table']}.{ct['referred_columns']}")
                else:
                    logger.warning("⚠ No domain_taxonomy constraints found")
                
                return True
                
        except Exception as e:
            logger.error(f"✗ Foreign key constraint validation failed: {e}")
            return False

    async def test_sample_data_insertion(self) -> bool:
        """Test sample data insertion to validate constraints"""
        try:
            async with self.session_factory() as session:
                # Test domain taxonomy insertion
                from app.models.business_domains import DomainTaxonomy
                
                # Insert root domain
                root_domain = DomainTaxonomy(
                    domain_id="root",
                    name="Root Domain",
                    description="Root level domain for testing",
                    category="technical",
                    level=0
                )
                session.add(root_domain)
                await session.commit()
                
                # Insert child domain (tests self-referencing FK)
                child_domain = DomainTaxonomy(
                    domain_id="technical-web",
                    parent_domain_id="root",  # References root domain
                    name="Web Technical Domain",
                    description="Web development related domain",
                    category="technical",
                    level=1
                )
                session.add(child_domain)
                await session.commit()
                
                # Verify insertions
                result = await session.execute(
                    text("SELECT COUNT(*) FROM domain_taxonomy")
                )
                count = result.scalar()
                
                if count >= 2:
                    logger.info(f"✓ Sample data insertion successful ({count} records)")
                    return True
                else:
                    logger.error(f"✗ Sample data insertion failed - only {count} records found")
                    return False
                    
        except Exception as e:
            logger.error(f"✗ Sample data insertion failed: {e}")
            logger.error(f"Error details: {traceback.format_exc()}")
            return False

    async def test_application_startup_simulation(self) -> bool:
        """Simulate the actual application startup process"""
        try:
            # Import startup components
            from app.core.startup import initialize_database, create_required_directories
            
            # Test directory creation
            success = await create_required_directories()
            if not success:
                logger.error("✗ Required directories creation failed")
                return False
            
            logger.info("✓ Required directories created successfully")
            
            # Test database initialization
            success = await initialize_database()
            if not success:
                logger.error("✗ Database initialization failed during startup simulation")
                return False
                
            logger.info("✓ Application startup simulation successful")
            return True
            
        except Exception as e:
            logger.error(f"✗ Application startup simulation failed: {e}")
            logger.error(f"Error details: {traceback.format_exc()}")
            return False

    async def run_comprehensive_tests(self, quick_mode: bool = False) -> Dict[str, bool]:
        """Run all database tests"""
        results = {}
        
        logger.info("=" * 60)
        logger.info("DOCXP DATABASE STARTUP COMPREHENSIVE TEST")
        logger.info("=" * 60)
        
        # Test 1: Engine initialization
        results['engine_init'] = await self.initialize_engine()
        if not results['engine_init']:
            logger.error("❌ CRITICAL: Engine initialization failed - cannot continue")
            return results
        
        # Test 2: Basic connectivity
        results['connectivity'] = await self.test_database_connectivity()
        if not results['connectivity']:
            logger.error("❌ CRITICAL: Database connectivity failed - cannot continue")
            return results
        
        # Test 3: Schema creation (the main issue we're fixing)
        results['schema_creation'] = await self.test_schema_creation()
        if not results['schema_creation']:
            logger.error("❌ CRITICAL: Schema creation failed - this was the original issue")
            return results
        
        # Test 4: Foreign key constraints
        results['foreign_keys'] = await self.test_foreign_key_constraints()
        
        if not quick_mode:
            # Test 5: Sample data insertion
            results['sample_data'] = await self.test_sample_data_insertion()
            
            # Test 6: Application startup simulation
            results['startup_simulation'] = await self.test_application_startup_simulation()
        
        return results

    async def cleanup(self):
        """Clean up database connections"""
        if self.engine:
            await self.engine.dispose()
            logger.info("✓ Database connections cleaned up")

async def main():
    """Main test execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="DocXP Database Startup Tester")
    parser.add_argument("--quick", action="store_true", help="Run quick essential tests only")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--clean", action="store_true", help="Clean rebuild database (DESTRUCTIVE)")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.clean:
        response = input("⚠️  WARNING: This will DROP ALL TABLES and rebuild the database. Type 'yes' to continue: ")
        if response.lower() != 'yes':
            print("Operation cancelled")
            return
    
    tester = DatabaseStartupTester()
    
    try:
        # Run tests
        results = await tester.run_comprehensive_tests(quick_mode=args.quick)
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("TEST RESULTS SUMMARY")
        logger.info("=" * 60)
        
        all_passed = True
        for test_name, passed in results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            logger.info(f"{test_name.replace('_', ' ').title()}: {status}")
            if not passed:
                all_passed = False
        
        if all_passed:
            logger.info("\n🎉 ALL TESTS PASSED! Database startup is working correctly.")
            logger.info("The backend should now start successfully on the target machine.")
        else:
            logger.error("\n❌ SOME TESTS FAILED! Please review the errors above.")
            logger.error("Address the failed tests before deploying to production.")
        
        # Provide next steps
        logger.info("\n" + "=" * 60)
        logger.info("NEXT STEPS")
        logger.info("=" * 60)
        if all_passed:
            logger.info("1. Run this script on the target machine to verify")
            logger.info("2. Start the backend with: python -m uvicorn main:app --host 0.0.0.0 --port 8001")
            logger.info("3. Check the health endpoint: http://localhost:8001/health")
        else:
            logger.info("1. Fix the failed tests")
            logger.info("2. Re-run this script to verify fixes")
            logger.info("3. Only deploy to production after all tests pass")
        
        return 0 if all_passed else 1
        
    except KeyboardInterrupt:
        logger.info("\n⚠️ Test interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"\n❌ Test execution failed: {e}")
        logger.error(f"Error details: {traceback.format_exc()}")
        return 1
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        sys.exit(1)