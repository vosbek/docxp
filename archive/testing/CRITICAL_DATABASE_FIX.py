#!/usr/bin/env python3
"""
CRITICAL DATABASE SCHEMA MIGRATION SCRIPT
DocXP Enterprise Platform - Production Ready Database Fix

This script DEFINITIVELY fixes the database schema mismatch issue.
Safe to run multiple times. Includes comprehensive error handling.
"""

import sqlite3
import os
import shutil
import json
from datetime import datetime
from pathlib import Path

class DatabaseSchemaFixer:
    def __init__(self):
        self.db_path = "docxp.db"
        self.backup_dir = "database_backups"
        self.log_messages = []
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.log_messages.append(log_entry)
        print(log_entry)
        
    def create_backup(self):
        """Create a backup of the current database"""
        try:
            if not os.path.exists(self.db_path):
                self.log("No existing database found. Will create new one.", "INFO")
                return True
                
            os.makedirs(self.backup_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(self.backup_dir, f"docxp_backup_{timestamp}.db")
            
            shutil.copy2(self.db_path, backup_path)
            self.log(f"✅ Database backup created: {backup_path}", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"❌ Failed to create backup: {e}", "ERROR")
            return False
    
    def check_current_schema(self):
        """Check what columns currently exist"""
        try:
            if not os.path.exists(self.db_path):
                self.log("Database file doesn't exist. Will create with correct schema.", "INFO")
                return {}, False
                
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get current table info
            cursor.execute("PRAGMA table_info(documentation_jobs)")
            columns = cursor.fetchall()
            
            current_columns = {col[1]: col[2] for col in columns}  # name: type
            
            self.log(f"Current columns in documentation_jobs: {list(current_columns.keys())}", "INFO")
            
            conn.close()
            return current_columns, True
            
        except Exception as e:
            self.log(f"❌ Error checking schema: {e}", "ERROR")
            return {}, False
    
    def get_required_schema(self):
        """Define the complete required schema"""
        return {
            'id': 'INTEGER',
            'job_id': 'VARCHAR',
            'repository_path': 'VARCHAR',
            'status': 'VARCHAR',
            'created_at': 'DATETIME',
            'completed_at': 'DATETIME',
            'config': 'JSON',
            'progress_percentage': 'INTEGER',
            'current_step': 'VARCHAR',
            'step_description': 'VARCHAR',
            'progress_data': 'JSON',
            'entities_count': 'INTEGER',
            'business_rules_count': 'INTEGER',
            'files_processed': 'INTEGER',
            'output_path': 'VARCHAR',
            'processing_time_seconds': 'FLOAT',
            'error_message': 'TEXT'
        }
    
    def add_missing_columns(self):
        """Add any missing columns to the database"""
        try:
            current_columns, exists = self.check_current_schema()
            required_columns = self.get_required_schema()
            
            if not exists:
                # Database doesn't exist, create it with full schema using SQLAlchemy
                self.log("Creating new database with complete schema...", "INFO")
                self.create_database_with_sqlalchemy()
                return True
            
            # Database exists, add missing columns
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            missing_columns = []
            for col_name, col_type in required_columns.items():
                if col_name not in current_columns:
                    missing_columns.append((col_name, col_type))
            
            if not missing_columns:
                self.log("✅ All required columns already exist!", "SUCCESS")
                conn.close()
                return True
            
            self.log(f"Missing columns to add: {[col[0] for col in missing_columns]}", "INFO")
            
            # Add missing columns
            for col_name, col_type in missing_columns:
                try:
                    default_value = self.get_default_value(col_name, col_type)
                    sql = f"ALTER TABLE documentation_jobs ADD COLUMN {col_name} {col_type}"
                    if default_value is not None:
                        sql += f" DEFAULT {default_value}"
                    
                    self.log(f"Executing: {sql}", "INFO")
                    cursor.execute(sql)
                    self.log(f"✅ Added column: {col_name}", "SUCCESS")
                    
                except sqlite3.OperationalError as e:
                    if "duplicate column" in str(e).lower():
                        self.log(f"⚠️  Column {col_name} already exists", "WARNING")
                    else:
                        raise
            
            conn.commit()
            conn.close()
            
            self.log("✅ Successfully added missing columns!", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"❌ Error adding missing columns: {e}", "ERROR")
            return False
    
    def get_default_value(self, col_name, col_type):
        """Get appropriate default value for a column"""
        if col_name == 'progress_percentage':
            return '0'
        elif col_type == 'INTEGER':
            return '0'
        elif col_type == 'FLOAT':
            return '0.0'
        else:
            return None  # NULL default
    
    def create_database_with_sqlalchemy(self):
        """Create database using SQLAlchemy to ensure proper schema"""
        try:
            import asyncio
            import sys
            
            # Add the app directory to Python path
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            
            from app.core.database import init_db
            
            async def create_db():
                await init_db()
            
            asyncio.run(create_db())
            self.log("✅ Created new database with SQLAlchemy", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"❌ Error creating database with SQLAlchemy: {e}", "ERROR")
            # Fallback to manual creation
            return self.create_database_manually()
    
    def create_database_manually(self):
        """Manually create database with correct schema"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create documentation_jobs table with full schema
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS documentation_jobs (
                id INTEGER PRIMARY KEY,
                job_id VARCHAR UNIQUE,
                repository_path VARCHAR NOT NULL,
                status VARCHAR DEFAULT 'pending',
                created_at DATETIME,
                completed_at DATETIME,
                config JSON NOT NULL,
                progress_percentage INTEGER DEFAULT 0,
                current_step VARCHAR,
                step_description VARCHAR,
                progress_data JSON,
                entities_count INTEGER DEFAULT 0,
                business_rules_count INTEGER DEFAULT 0,
                files_processed INTEGER DEFAULT 0,
                output_path VARCHAR,
                processing_time_seconds FLOAT,
                error_message TEXT
            )
            """
            
            cursor.execute(create_table_sql)
            
            # Create indexes
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_documentation_jobs_job_id ON documentation_jobs (job_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_documentation_jobs_id ON documentation_jobs (id)")
            
            # Create other tables
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS repositories (
                id INTEGER PRIMARY KEY,
                path VARCHAR UNIQUE NOT NULL,
                name VARCHAR NOT NULL,
                last_analyzed DATETIME,
                total_files INTEGER DEFAULT 0,
                total_lines INTEGER DEFAULT 0,
                languages JSON,
                git_remote VARCHAR,
                last_commit VARCHAR,
                created_at DATETIME,
                updated_at DATETIME
            )
            """)
            
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS configuration_templates (
                id INTEGER PRIMARY KEY,
                name VARCHAR UNIQUE NOT NULL,
                description TEXT,
                config JSON NOT NULL,
                is_default BOOLEAN DEFAULT 0,
                created_at DATETIME,
                updated_at DATETIME
            )
            """)
            
            conn.commit()
            conn.close()
            
            self.log("✅ Created database manually with correct schema", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"❌ Error creating database manually: {e}", "ERROR")
            return False
    
    def verify_schema(self):
        """Verify that all required columns exist"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("PRAGMA table_info(documentation_jobs)")
            columns = cursor.fetchall()
            current_columns = [col[1] for col in columns]
            
            required_columns = list(self.get_required_schema().keys())
            
            missing = [col for col in required_columns if col not in current_columns]
            
            if missing:
                self.log(f"❌ Still missing columns: {missing}", "ERROR")
                conn.close()
                return False
            
            self.log("✅ Schema verification PASSED - All columns present!", "SUCCESS")
            
            # Test a simple query
            cursor.execute("SELECT COUNT(*) FROM documentation_jobs")
            count = cursor.fetchone()[0]
            self.log(f"✅ Database query test PASSED - {count} jobs in database", "SUCCESS")
            
            conn.close()
            return True
            
        except Exception as e:
            self.log(f"❌ Schema verification FAILED: {e}", "ERROR")
            return False
    
    def save_log(self):
        """Save the migration log"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = f"migration_log_{timestamp}.txt"
            
            with open(log_file, 'w') as f:
                f.write("DocXP Database Migration Log\n")
                f.write("="*50 + "\n")
                for message in self.log_messages:
                    f.write(message + "\n")
            
            self.log(f"✅ Migration log saved: {log_file}", "SUCCESS")
            
        except Exception as e:
            self.log(f"❌ Failed to save log: {e}", "ERROR")
    
    def run_migration(self):
        """Run the complete migration process"""
        self.log("🚀 Starting CRITICAL DATABASE SCHEMA MIGRATION", "INFO")
        self.log("="*60, "INFO")
        
        # Step 1: Create backup
        if not self.create_backup():
            self.log("❌ MIGRATION ABORTED - Backup failed", "CRITICAL")
            return False
        
        # Step 2: Add missing columns
        if not self.add_missing_columns():
            self.log("❌ MIGRATION FAILED - Could not add missing columns", "CRITICAL")
            return False
        
        # Step 3: Verify schema
        if not self.verify_schema():
            self.log("❌ MIGRATION FAILED - Schema verification failed", "CRITICAL")
            return False
        
        self.log("="*60, "INFO")
        self.log("🎉 MIGRATION COMPLETED SUCCESSFULLY!", "SUCCESS")
        self.log("✅ Database is now ready for production use", "SUCCESS")
        self.log("="*60, "INFO")
        
        self.save_log()
        return True

def main():
    """Main entry point"""
    print("DocXP CRITICAL DATABASE SCHEMA MIGRATION")
    print("="*50)
    print("This script will fix the database schema mismatch issue.")
    print("It is safe to run multiple times.")
    print("")
    
    fixer = DatabaseSchemaFixer()
    
    try:
        success = fixer.run_migration()
        
        if success:
            print("\n🎉 SUCCESS! Your database is now fixed and ready to use.")
            print("\nNext steps:")
            print("1. Restart your DocXP application")
            print("2. Test the /api/documentation/jobs endpoint")
            print("3. All database-related errors should be resolved")
        else:
            print("\n❌ MIGRATION FAILED!")
            print("Please check the migration log for details.")
            print("Contact support if the issue persists.")
        
        return success
        
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {e}")
        print("Migration process encountered an unexpected error.")
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)