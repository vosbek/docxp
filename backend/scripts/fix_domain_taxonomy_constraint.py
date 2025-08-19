#!/usr/bin/env python3
"""
Migration script to fix domain_taxonomy self-referencing foreign key constraint
This script handles the database schema fix for production environments

Usage:
    python scripts/fix_domain_taxonomy_constraint.py [--dry-run] [--force]

Options:
    --dry-run: Show what would be done without making changes
    --force: Force the migration even if validation fails
"""

import asyncio
import argparse
import logging
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import engine, AsyncSessionLocal
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DomainTaxonomyMigration:
    """Handle the domain_taxonomy table constraint migration"""
    
    def __init__(self, dry_run=False, force=False):
        self.dry_run = dry_run
        self.force = force
        self.migration_log = []
    
    async def check_table_exists(self, session):
        """Check if domain_taxonomy table exists"""
        try:
            result = await session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'domain_taxonomy'
                );
            """))
            return result.scalar()
        except Exception as e:
            logger.error(f"Error checking table existence: {e}")
            return False
    
    async def check_constraint_exists(self, session):
        """Check if the problematic constraint exists"""
        try:
            result = await session.execute(text("""
                SELECT constraint_name 
                FROM information_schema.table_constraints 
                WHERE table_name = 'domain_taxonomy' 
                AND constraint_type = 'FOREIGN KEY'
                AND constraint_name LIKE '%parent%';
            """))
            constraints = result.fetchall()
            return [row[0] for row in constraints]
        except Exception as e:
            logger.error(f"Error checking constraints: {e}")
            return []
    
    async def backup_data(self, session):
        """Backup domain_taxonomy data before migration"""
        try:
            result = await session.execute(text("SELECT COUNT(*) FROM domain_taxonomy;"))
            count = result.scalar()
            
            if count > 0:
                backup_table = f"domain_taxonomy_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                if not self.dry_run:
                    await session.execute(text(f"""
                        CREATE TABLE {backup_table} AS 
                        SELECT * FROM domain_taxonomy;
                    """))
                    await session.commit()
                
                logger.info(f"{'Would backup' if self.dry_run else 'Backed up'} {count} records to {backup_table}")
                self.migration_log.append(f"Backup created: {backup_table} with {count} records")
                return backup_table
            else:
                logger.info("No data to backup - table is empty")
                return None
                
        except Exception as e:
            logger.error(f"Error backing up data: {e}")
            raise
    
    async def drop_problematic_constraint(self, session):
        """Drop the existing problematic constraint"""
        try:
            constraints = await self.check_constraint_exists(session)
            
            for constraint_name in constraints:
                drop_sql = f"ALTER TABLE domain_taxonomy DROP CONSTRAINT IF EXISTS {constraint_name};"
                
                if not self.dry_run:
                    await session.execute(text(drop_sql))
                
                logger.info(f"{'Would drop' if self.dry_run else 'Dropped'} constraint: {constraint_name}")
                self.migration_log.append(f"Dropped constraint: {constraint_name}")
            
            if not self.dry_run and constraints:
                await session.commit()
                
        except Exception as e:
            logger.error(f"Error dropping constraints: {e}")
            raise
    
    async def create_fixed_constraint(self, session):
        """Create the corrected foreign key constraint with proper naming"""
        try:
            # Create the corrected constraint with explicit name
            constraint_sql = """
                ALTER TABLE domain_taxonomy 
                ADD CONSTRAINT fk_domain_taxonomy_parent 
                FOREIGN KEY (parent_domain_id) 
                REFERENCES domain_taxonomy (domain_id) 
                ON DELETE SET NULL;
            """
            
            if not self.dry_run:
                await session.execute(text(constraint_sql))
                await session.commit()
            
            logger.info(f"{'Would create' if self.dry_run else 'Created'} fixed constraint: fk_domain_taxonomy_parent")
            self.migration_log.append("Created fixed constraint: fk_domain_taxonomy_parent")
            
        except Exception as e:
            logger.error(f"Error creating fixed constraint: {e}")
            raise
    
    async def validate_migration(self, session):
        """Validate the migration was successful"""
        try:
            # Check constraint exists
            result = await session.execute(text("""
                SELECT constraint_name 
                FROM information_schema.table_constraints 
                WHERE table_name = 'domain_taxonomy' 
                AND constraint_type = 'FOREIGN KEY'
                AND constraint_name = 'fk_domain_taxonomy_parent';
            """))
            constraint_exists = result.fetchone() is not None
            
            if not constraint_exists:
                raise Exception("Fixed constraint was not created successfully")
            
            # Test constraint works
            await session.execute(text("""
                SELECT dt1.domain_id, dt2.domain_id as parent_domain_id
                FROM domain_taxonomy dt1 
                LEFT JOIN domain_taxonomy dt2 ON dt1.parent_domain_id = dt2.domain_id
                LIMIT 1;
            """))
            
            logger.info("Migration validation passed")
            self.migration_log.append("Migration validation: SUCCESS")
            return True
            
        except Exception as e:
            logger.error(f"Migration validation failed: {e}")
            self.migration_log.append(f"Migration validation: FAILED - {e}")
            return False
    
    async def run_migration(self):
        """Execute the complete migration process"""
        logger.info("Starting domain_taxonomy constraint migration")
        logger.info(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE MIGRATION'}")
        
        async with AsyncSessionLocal() as session:
            try:
                # Step 1: Check if table exists
                table_exists = await self.check_table_exists(session)
                if not table_exists:
                    logger.info("domain_taxonomy table does not exist - no migration needed")
                    return True
                
                # Step 2: Backup existing data
                backup_table = await self.backup_data(session)
                
                # Step 3: Drop problematic constraints
                await self.drop_problematic_constraint(session)
                
                # Step 4: Create fixed constraint
                await self.create_fixed_constraint(session)
                
                # Step 5: Validate migration (only in live mode)
                if not self.dry_run:
                    validation_success = await self.validate_migration(session)
                    if not validation_success and not self.force:
                        raise Exception("Migration validation failed - use --force to override")
                
                logger.info("Migration completed successfully")
                return True
                
            except Exception as e:
                logger.error(f"Migration failed: {e}")
                if not self.dry_run:
                    await session.rollback()
                return False
    
    def print_migration_summary(self):
        """Print summary of migration actions"""
        print("\n" + "="*60)
        print("DOMAIN TAXONOMY MIGRATION SUMMARY")
        print("="*60)
        for entry in self.migration_log:
            print(f"✓ {entry}")
        print("="*60)

async def main():
    """Main migration execution"""
    parser = argparse.ArgumentParser(description="Fix domain_taxonomy constraint migration")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show what would be done without making changes")
    parser.add_argument("--force", action="store_true",
                       help="Force migration even if validation fails")
    
    args = parser.parse_args()
    
    migration = DomainTaxonomyMigration(dry_run=args.dry_run, force=args.force)
    
    try:
        success = await migration.run_migration()
        migration.print_migration_summary()
        
        if success:
            print(f"\n✅ Migration {'simulation' if args.dry_run else 'execution'} completed successfully")
            return 0
        else:
            print(f"\n❌ Migration {'simulation' if args.dry_run else 'execution'} failed")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️  Migration interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\n💥 Migration failed with unexpected error: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))