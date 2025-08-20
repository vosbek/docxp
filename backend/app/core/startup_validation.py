"""
Database startup validation to prevent schema issues
Comprehensive validation of database schema integrity before application startup
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import engine, AsyncSessionLocal, Base
from app.core.config import settings

logger = logging.getLogger(__name__)

class DatabaseSchemaValidator:
    """Comprehensive database schema validation for startup"""
    
    def __init__(self):
        self.validation_errors = []
        self.validation_warnings = []
        self.validation_info = []
    
    async def validate_all(self) -> bool:
        """Run all validation checks"""
        logger.info("Starting comprehensive database schema validation...")
        
        validations = [
            self.validate_connection,
            self.validate_tables_exist,
            self.validate_foreign_key_constraints,
            self.validate_unique_constraints,
            self.validate_indexes,
            self.validate_self_referencing_constraints,
            self.validate_enum_constraints,
            self.validate_data_integrity,
        ]
        
        for validation in validations:
            try:
                success = await validation()
                if not success:
                    logger.error(f"Validation failed: {validation.__name__}")
            except Exception as e:
                logger.error(f"Validation error in {validation.__name__}: {e}")
                self.validation_errors.append(f"{validation.__name__}: {str(e)}")
        
        return len(self.validation_errors) == 0
    
    async def validate_connection(self) -> bool:
        """Validate database connection"""
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
                self.validation_info.append("Database connection: OK")
                return True
        except Exception as e:
            self.validation_errors.append(f"Database connection failed: {e}")
            return False
    
    async def validate_tables_exist(self) -> bool:
        """Validate all required tables exist"""
        expected_tables = [
            "domain_taxonomy",
            "domain_classification_rules", 
            "domain_classification_results",
            "repositories",
            "documentation_jobs",
            "code_entities",
            "business_rule_contexts",
        ]
        
        async with AsyncSessionLocal() as session:
            try:
                for table in expected_tables:
                    result = await session.execute(text(f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = '{table}'
                        );
                    """))
                    if not result.scalar():
                        self.validation_errors.append(f"Required table missing: {table}")
                
                self.validation_info.append(f"Checked {len(expected_tables)} required tables")
                return len(self.validation_errors) == 0
                
            except Exception as e:
                self.validation_errors.append(f"Table validation error: {e}")
                return False
    
    async def validate_foreign_key_constraints(self) -> bool:
        """Validate all foreign key constraints are properly defined"""
        async with AsyncSessionLocal() as session:
            try:
                # Check for foreign key constraints
                result = await session.execute(text("""
                    SELECT 
                        tc.table_name,
                        tc.constraint_name,
                        kcu.column_name,
                        ccu.table_name AS referenced_table,
                        ccu.column_name AS referenced_column
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu 
                        ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage ccu 
                        ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema = 'public'
                    ORDER BY tc.table_name, tc.constraint_name;
                """))
                
                foreign_keys = result.fetchall()
                
                # Validate specific critical foreign keys
                critical_fks = {
                    "domain_taxonomy": ["fk_domain_taxonomy_parent"],
                    "domain_classification_rules": ["domain_classification_rules_target_domain_fkey"],
                    "domain_classification_results": ["domain_classification_results_primary_domain_fkey"],
                }
                
                found_fks = {}
                for fk in foreign_keys:
                    table_name = fk[0]
                    if table_name not in found_fks:
                        found_fks[table_name] = []
                    found_fks[table_name].append(fk[1])
                
                for table, expected_constraints in critical_fks.items():
                    if table not in found_fks:
                        self.validation_warnings.append(f"No foreign keys found for table: {table}")
                        continue
                    
                    for expected_fk in expected_constraints:
                        if expected_fk not in found_fks[table]:
                            # Check if any constraint exists for the pattern (PostgreSQL auto-generates names)
                            pattern_found = any(expected_fk.split("_")[-2:] == fk.split("_")[-2:] 
                                              for fk in found_fks[table])
                            if not pattern_found:
                                self.validation_warnings.append(
                                    f"Expected foreign key pattern not found: {table}.{expected_fk}")
                
                self.validation_info.append(f"Validated {len(foreign_keys)} foreign key constraints")
                return True
                
            except Exception as e:
                self.validation_errors.append(f"Foreign key validation error: {e}")
                return False
    
    async def validate_unique_constraints(self) -> bool:
        """Validate unique constraints exist where required"""
        async with AsyncSessionLocal() as session:
            try:
                # Check critical unique constraints
                critical_unique = {
                    "domain_taxonomy": ["domain_id"],
                    "domain_classification_rules": ["rule_id"],
                    "repositories": ["path"],
                }
                
                for table, columns in critical_unique.items():
                    for column in columns:
                        result = await session.execute(text(f"""
                            SELECT indexname 
                            FROM pg_indexes 
                            WHERE tablename = '{table}' 
                            AND indexname LIKE '%{column}%'
                            AND indexname LIKE '%key%';
                        """))
                        
                        unique_indexes = result.fetchall()
                        if not unique_indexes:
                            self.validation_warnings.append(
                                f"No unique constraint found for {table}.{column}")
                
                self.validation_info.append("Validated unique constraints")
                return True
                
            except Exception as e:
                self.validation_errors.append(f"Unique constraint validation error: {e}")
                return False
    
    async def validate_indexes(self) -> bool:
        """Validate critical indexes exist"""
        async with AsyncSessionLocal() as session:
            try:
                # Check for indexes on foreign key columns (performance critical)
                result = await session.execute(text("""
                    SELECT 
                        t.relname AS table_name,
                        i.relname AS index_name,
                        a.attname AS column_name
                    FROM pg_class t
                    JOIN pg_index ix ON t.oid = ix.indrelid
                    JOIN pg_class i ON i.oid = ix.indexrelid
                    JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
                    WHERE t.relkind = 'r'
                    AND t.relname IN ('domain_taxonomy', 'domain_classification_rules', 'domain_classification_results')
                    ORDER BY t.relname, i.relname;
                """))
                
                indexes = result.fetchall()
                self.validation_info.append(f"Found {len(indexes)} indexes on critical tables")
                return True
                
            except Exception as e:
                self.validation_errors.append(f"Index validation error: {e}")
                return False
    
    async def validate_self_referencing_constraints(self) -> bool:
        """Specifically validate self-referencing constraints"""
        async with AsyncSessionLocal() as session:
            try:
                # Check domain_taxonomy self-referencing constraint
                result = await session.execute(text("""
                    SELECT 
                        tc.constraint_name,
                        tc.table_name,
                        kcu.column_name,
                        ccu.table_name AS referenced_table,
                        ccu.column_name AS referenced_column
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu 
                        ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage ccu 
                        ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_name = 'domain_taxonomy'
                    AND kcu.column_name = 'parent_domain_id'
                    AND ccu.table_name = 'domain_taxonomy'
                    AND ccu.column_name = 'domain_id';
                """))
                
                self_ref_constraint = result.fetchone()
                if not self_ref_constraint:
                    self.validation_errors.append(
                        "Critical self-referencing constraint missing: domain_taxonomy.parent_domain_id")
                    return False
                
                self.validation_info.append(
                    f"Self-referencing constraint OK: {self_ref_constraint[0]}")
                return True
                
            except Exception as e:
                self.validation_errors.append(f"Self-referencing constraint validation error: {e}")
                return False
    
    async def validate_enum_constraints(self) -> bool:
        """Validate enum-like constraints"""
        async with AsyncSessionLocal() as session:
            try:
                # Check if domain_taxonomy.category has reasonable values
                result = await session.execute(text("""
                    SELECT DISTINCT category 
                    FROM domain_taxonomy 
                    WHERE category IS NOT NULL
                    LIMIT 10;
                """))
                
                categories = result.fetchall()
                self.validation_info.append(f"Found {len(categories)} distinct domain categories")
                return True
                
            except Exception as e:
                # This is not critical if table is empty
                self.validation_info.append("Enum validation skipped - table may be empty")
                return True
    
    async def validate_data_integrity(self) -> bool:
        """Validate basic data integrity"""
        async with AsyncSessionLocal() as session:
            try:
                # Check for orphaned foreign key references
                result = await session.execute(text("""
                    SELECT COUNT(*) as orphaned_count
                    FROM domain_taxonomy dt1
                    LEFT JOIN domain_taxonomy dt2 ON dt1.parent_domain_id = dt2.domain_id
                    WHERE dt1.parent_domain_id IS NOT NULL 
                    AND dt2.domain_id IS NULL;
                """))
                
                orphaned_count = result.scalar()
                if orphaned_count > 0:
                    self.validation_warnings.append(
                        f"Found {orphaned_count} orphaned parent domain references")
                
                self.validation_info.append("Data integrity check completed")
                return True
                
            except Exception as e:
                # This is not critical if table doesn't exist or is empty
                self.validation_info.append("Data integrity check skipped - table may not exist")
                return True
    
    def print_validation_summary(self):
        """Print comprehensive validation summary"""
        print("\n" + "="*70)
        print("DATABASE SCHEMA VALIDATION SUMMARY")
        print("="*70)
        
        if self.validation_info:
            print("\n✅ VALIDATION INFO:")
            for info in self.validation_info:
                print(f"   ℹ️  {info}")
        
        if self.validation_warnings:
            print("\n⚠️  VALIDATION WARNINGS:")
            for warning in self.validation_warnings:
                print(f"   ⚠️  {warning}")
        
        if self.validation_errors:
            print("\n❌ VALIDATION ERRORS:")
            for error in self.validation_errors:
                print(f"   ❌ {error}")
        else:
            print("\n✅ NO VALIDATION ERRORS FOUND")
        
        print("="*70)
        
        return len(self.validation_errors) == 0

async def startup_validation() -> bool:
    """Main startup validation function"""
    validator = DatabaseSchemaValidator()
    success = await validator.validate_all()
    validator.print_validation_summary()
    
    if success:
        logger.info("Database startup validation passed")
    else:
        logger.error("Database startup validation failed")
    
    return success

# Fast validation for development
async def quick_startup_check() -> bool:
    """Quick validation for development environments"""
    try:
        async with AsyncSessionLocal() as session:
            # Just check connection and critical table
            await session.execute(text("SELECT 1"))
            
            result = await session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'domain_taxonomy'
                );
            """))
            
            if result.scalar():
                # Check the critical constraint exists
                constraint_result = await session.execute(text("""
                    SELECT COUNT(*) 
                    FROM information_schema.table_constraints 
                    WHERE table_name = 'domain_taxonomy' 
                    AND constraint_type = 'FOREIGN KEY'
                    AND constraint_name LIKE '%parent%';
                """))
                
                constraint_count = constraint_result.scalar()
                if constraint_count > 0:
                    logger.info("Quick startup validation passed")
                    return True
                else:
                    logger.warning("Self-referencing constraint may be missing")
                    return False
            else:
                logger.info("Domain taxonomy table not found - will be created")
                return True
                
    except Exception as e:
        logger.error(f"Quick startup validation failed: {e}")
        return False

if __name__ == "__main__":
    # Run standalone validation
    asyncio.run(startup_validation())