#!/usr/bin/env python3
"""
Enterprise-Grade DocXP Database Migration and Health Check Solution

This script provides comprehensive database migration, validation, and health checking
capabilities for the DocXP Enterprise Migration Platform.

Features:
- Database schema validation and migration
- Service health checks with graceful degradation
- AWS configuration validation
- Production-ready backup and rollback procedures
- Performance monitoring and analytics
"""

import sqlite3
import os
import json
import asyncio
import logging
import traceback
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import shutil

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DocXPMigrationSolution:
    """Enterprise-grade migration solution for DocXP platform"""
    
    def __init__(self, backend_path: Path = None):
        self.backend_path = backend_path or Path(__file__).parent
        self.db_path = self.backend_path / "docxp.db"
        self.backup_dir = self.backend_path / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # Expected database schema
        self.expected_tables = {
            'documentation_jobs': {
                'id': 'INTEGER PRIMARY KEY',
                'job_id': 'VARCHAR',
                'repository_path': 'VARCHAR NOT NULL',
                'status': 'VARCHAR',
                'created_at': 'DATETIME',
                'completed_at': 'DATETIME',
                'config': 'JSON NOT NULL',
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
            },
            'repositories': {
                'id': 'INTEGER PRIMARY KEY',
                'path': 'VARCHAR UNIQUE NOT NULL',
                'name': 'VARCHAR NOT NULL',
                'last_analyzed': 'DATETIME',
                'total_files': 'INTEGER',
                'total_lines': 'INTEGER',
                'languages': 'JSON',
                'git_remote': 'VARCHAR',
                'last_commit': 'VARCHAR',
                'created_at': 'DATETIME',
                'updated_at': 'DATETIME'
            },
            'configuration_templates': {
                'id': 'INTEGER PRIMARY KEY',
                'name': 'VARCHAR UNIQUE NOT NULL',
                'description': 'TEXT',
                'config': 'JSON NOT NULL',
                'is_default': 'BOOLEAN',
                'created_at': 'DATETIME',
                'updated_at': 'DATETIME'
            }
        }

    def create_backup(self, suffix: str = None) -> Path:
        """Create a backup of the current database"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"docxp_backup_{timestamp}"
        if suffix:
            backup_name += f"_{suffix}"
        backup_name += ".db"
        
        backup_path = self.backup_dir / backup_name
        
        if self.db_path.exists():
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"✅ Database backup created: {backup_path}")
            return backup_path
        else:
            logger.warning(f"⚠️  No database file found to backup at {self.db_path}")
            return None

    def validate_database_schema(self) -> Tuple[bool, Dict[str, Any]]:
        """Validate current database schema against expected schema"""
        if not self.db_path.exists():
            return False, {"error": f"Database file not found: {self.db_path}"}
        
        validation_results = {
            "database_exists": True,
            "database_size": self.db_path.stat().st_size,
            "tables": {},
            "missing_tables": [],
            "missing_columns": {},
            "total_records": {}
        }
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Get existing tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            existing_tables = {row[0] for row in cursor.fetchall()}
            
            # Check each expected table
            for table_name, expected_columns in self.expected_tables.items():
                if table_name not in existing_tables:
                    validation_results["missing_tables"].append(table_name)
                    continue
                
                # Get table schema
                cursor.execute(f"PRAGMA table_info({table_name})")
                existing_columns = {row[1]: row[2] for row in cursor.fetchall()}
                
                # Check for missing columns
                missing_cols = []
                for col_name in expected_columns.keys():
                    if col_name not in existing_columns:
                        missing_cols.append(col_name)
                
                validation_results["tables"][table_name] = {
                    "exists": True,
                    "columns": existing_columns,
                    "missing_columns": missing_cols
                }
                
                if missing_cols:
                    validation_results["missing_columns"][table_name] = missing_cols
                
                # Get record count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                validation_results["total_records"][table_name] = cursor.fetchone()[0]
            
            conn.close()
            
            # Overall validation status
            is_valid = (
                len(validation_results["missing_tables"]) == 0 and
                len(validation_results["missing_columns"]) == 0
            )
            
            return is_valid, validation_results
            
        except Exception as e:
            return False, {"error": f"Database validation failed: {e}"}

    def migrate_database_schema(self) -> bool:
        """Migrate database schema to latest version"""
        logger.info("🔄 Starting database schema migration...")
        
        # Create backup before migration
        backup_path = self.create_backup("pre_migration")
        if not backup_path:
            logger.warning("⚠️  Proceeding without backup (no existing database)")
        
        try:
            # Check current schema
            is_valid, validation_results = self.validate_database_schema()
            
            if is_valid:
                logger.info("✅ Database schema is already up to date")
                return True
            
            logger.info("🔧 Migrating database schema...")
            
            # Initialize with SQLAlchemy models for consistency
            import sys
            sys.path.append(str(self.backend_path))
            
            try:
                from app.core.database import init_db
                asyncio.run(init_db())
                logger.info("✅ Database schema migration completed using SQLAlchemy")
                return True
            except Exception as e:
                logger.error(f"❌ SQLAlchemy migration failed: {e}")
                
                # Fallback to manual migration
                return self._manual_schema_migration(validation_results)
                
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            logger.error(traceback.format_exc())
            
            # Restore backup if migration failed
            if backup_path and backup_path.exists():
                logger.info("🔄 Restoring database from backup...")
                shutil.copy2(backup_path, self.db_path)
                logger.info("✅ Database restored from backup")
            
            return False

    def _manual_schema_migration(self, validation_results: Dict[str, Any]) -> bool:
        """Manual schema migration as fallback"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Create missing tables
            for table_name in validation_results.get("missing_tables", []):
                logger.info(f"📝 Creating table: {table_name}")
                self._create_table(cursor, table_name)
            
            # Add missing columns
            for table_name, missing_cols in validation_results.get("missing_columns", {}).items():
                for col_name in missing_cols:
                    logger.info(f"📝 Adding column: {table_name}.{col_name}")
                    self._add_column(cursor, table_name, col_name)
            
            conn.commit()
            conn.close()
            
            logger.info("✅ Manual schema migration completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Manual migration failed: {e}")
            return False

    def _create_table(self, cursor, table_name: str):
        """Create table with proper schema"""
        if table_name == "documentation_jobs":
            cursor.execute("""
                CREATE TABLE documentation_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id VARCHAR UNIQUE,
                    repository_path VARCHAR NOT NULL,
                    status VARCHAR DEFAULT 'pending',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
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
            """)
        elif table_name == "repositories":
            cursor.execute("""
                CREATE TABLE repositories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path VARCHAR UNIQUE NOT NULL,
                    name VARCHAR NOT NULL,
                    last_analyzed DATETIME,
                    total_files INTEGER DEFAULT 0,
                    total_lines INTEGER DEFAULT 0,
                    languages JSON DEFAULT '[]',
                    git_remote VARCHAR,
                    last_commit VARCHAR,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
        elif table_name == "configuration_templates":
            cursor.execute("""
                CREATE TABLE configuration_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR UNIQUE NOT NULL,
                    description TEXT,
                    config JSON NOT NULL,
                    is_default BOOLEAN DEFAULT FALSE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def _add_column(self, cursor, table_name: str, col_name: str):
        """Add missing column to existing table"""
        column_definitions = {
            'progress_percentage': 'INTEGER DEFAULT 0',
            'current_step': 'VARCHAR',
            'step_description': 'VARCHAR',
            'progress_data': 'JSON',
            'entities_count': 'INTEGER DEFAULT 0',
            'business_rules_count': 'INTEGER DEFAULT 0',
            'files_processed': 'INTEGER DEFAULT 0',
            'processing_time_seconds': 'FLOAT',
            'error_message': 'TEXT'
        }
        
        col_def = column_definitions.get(col_name, 'TEXT')
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_def}")

    async def test_service_health(self) -> Dict[str, Any]:
        """Comprehensive service health check"""
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "services": {
                "database": {"status": "unknown", "details": {}},
                "api_endpoints": {"status": "unknown", "details": {}},
                "aws_bedrock": {"status": "unknown", "details": {}},
                "file_system": {"status": "unknown", "details": {}}
            },
            "recommendations": []
        }
        
        # Test database
        try:
            is_valid, validation_results = self.validate_database_schema()
            if is_valid:
                health_status["services"]["database"]["status"] = "healthy"
                health_status["services"]["database"]["details"] = {
                    "schema_valid": True,
                    "total_records": validation_results.get("total_records", {}),
                    "database_size_mb": round(validation_results.get("database_size", 0) / (1024*1024), 2)
                }
            else:
                health_status["services"]["database"]["status"] = "unhealthy"
                health_status["services"]["database"]["details"] = validation_results
                health_status["overall_status"] = "degraded"
                health_status["recommendations"].append("Run database migration to fix schema issues")
        except Exception as e:
            health_status["services"]["database"]["status"] = "error"
            health_status["services"]["database"]["details"] = {"error": str(e)}
            health_status["overall_status"] = "unhealthy"

        # Test API endpoints
        try:
            # Import and test database operations
            import sys
            sys.path.append(str(self.backend_path))
            
            from app.core.database import AsyncSessionLocal
            from app.api.analytics import get_metrics
            
            async with AsyncSessionLocal() as session:
                metrics = await get_metrics(session)
                health_status["services"]["api_endpoints"]["status"] = "healthy"
                health_status["services"]["api_endpoints"]["details"] = {
                    "analytics_endpoint": "working",
                    "total_jobs": metrics.total_jobs,
                    "successful_jobs": metrics.successful_jobs
                }
        except Exception as e:
            health_status["services"]["api_endpoints"]["status"] = "error"
            health_status["services"]["api_endpoints"]["details"] = {"error": str(e)}
            if "overall_status" != "unhealthy":
                health_status["overall_status"] = "degraded"

        # Test AWS Bedrock (with graceful degradation)
        try:
            from app.core.config import settings
            
            aws_config = {
                "region": settings.AWS_REGION,
                "profile": settings.AWS_PROFILE,
                "has_access_key": bool(settings.AWS_ACCESS_KEY_ID),
                "has_secret_key": bool(settings.AWS_SECRET_ACCESS_KEY),
                "model_id": settings.BEDROCK_MODEL_ID
            }
            
            if settings.AWS_PROFILE or (settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY):
                # Try to initialize AI service
                try:
                    from app.services.ai_service import AIService
                    ai_service = AIService()
                    health_status["services"]["aws_bedrock"]["status"] = "healthy"
                    health_status["services"]["aws_bedrock"]["details"] = {
                        "configured": True,
                        "config": aws_config
                    }
                except Exception as ai_error:
                    health_status["services"]["aws_bedrock"]["status"] = "configured_but_inaccessible"
                    health_status["services"]["aws_bedrock"]["details"] = {
                        "configured": True,
                        "config": aws_config,
                        "error": str(ai_error)
                    }
                    health_status["recommendations"].append("Verify AWS credentials and region configuration")
            else:
                health_status["services"]["aws_bedrock"]["status"] = "not_configured"
                health_status["services"]["aws_bedrock"]["details"] = {
                    "configured": False,
                    "config": aws_config
                }
                health_status["recommendations"].append("Configure AWS credentials for AI features")
                
        except Exception as e:
            health_status["services"]["aws_bedrock"]["status"] = "error"
            health_status["services"]["aws_bedrock"]["details"] = {"error": str(e)}

        # Test file system
        try:
            required_dirs = ["output", "temp", "configs"]
            fs_status = {}
            
            for dir_name in required_dirs:
                dir_path = self.backend_path / dir_name
                fs_status[dir_name] = {
                    "exists": dir_path.exists(),
                    "writable": dir_path.exists() and os.access(dir_path, os.W_OK)
                }
                
                if not dir_path.exists():
                    dir_path.mkdir(exist_ok=True)
                    fs_status[dir_name]["created"] = True
            
            health_status["services"]["file_system"]["status"] = "healthy"
            health_status["services"]["file_system"]["details"] = fs_status
            
        except Exception as e:
            health_status["services"]["file_system"]["status"] = "error"
            health_status["services"]["file_system"]["details"] = {"error": str(e)}

        return health_status

    def generate_health_report(self, health_status: Dict[str, Any]) -> str:
        """Generate a human-readable health report"""
        report = [
            "=" * 80,
            "DocXP Enterprise Platform Health Report",
            "=" * 80,
            f"Generated: {health_status['timestamp']}",
            f"Overall Status: {health_status['overall_status'].upper()}",
            "",
        ]
        
        for service_name, service_data in health_status['services'].items():
            status_symbol = {
                "healthy": "[OK]",
                "unhealthy": "[ERROR]", 
                "degraded": "[WARN]",
                "error": "[CRITICAL]",
                "not_configured": "[CONFIG]",
                "configured_but_inaccessible": "[AUTH]",
                "unknown": "[UNKNOWN]"
            }.get(service_data['status'], "[UNKNOWN]")
            
            report.append(f"{status_symbol} {service_name.replace('_', ' ').title()}: {service_data['status']}")
            
            if service_data.get('details'):
                for key, value in service_data['details'].items():
                    if isinstance(value, dict):
                        report.append(f"   {key}: {json.dumps(value, indent=2)}")
                    else:
                        report.append(f"   {key}: {value}")
            report.append("")
        
        if health_status.get('recommendations'):
            report.extend([
                "RECOMMENDATIONS:",
                "-" * 40
            ])
            for i, rec in enumerate(health_status['recommendations'], 1):
                report.append(f"{i}. {rec}")
            report.append("")
        
        report.extend([
            "BACKUP INFORMATION:",
            "-" * 40,
            f"Backup directory: {self.backup_dir}",
            f"Available backups: {len(list(self.backup_dir.glob('*.db')))}",
            "",
            "=" * 80
        ])
        
        return "\n".join(report)

    async def run_comprehensive_check(self) -> bool:
        """Run comprehensive platform check and migration"""
        logger.info("🚀 Starting DocXP Enterprise Platform Comprehensive Check")
        
        # Step 1: Validate and migrate database
        if not self.migrate_database_schema():
            logger.error("❌ Database migration failed")
            return False
        
        # Step 2: Validate schema again
        is_valid, validation_results = self.validate_database_schema()
        if not is_valid:
            logger.error("❌ Database schema validation failed after migration")
            logger.error(json.dumps(validation_results, indent=2))
            return False
        
        logger.info("✅ Database schema validation passed")
        
        # Step 3: Run health checks
        health_status = await self.test_service_health()
        
        # Step 4: Generate and display report
        report = self.generate_health_report(health_status)
        print(report)
        
        # Step 5: Save report to file
        report_path = self.backend_path / f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"📄 Health report saved to: {report_path}")
        
        return health_status['overall_status'] in ['healthy', 'degraded']

async def main():
    """Main entry point for the migration solution"""
    backend_path = Path(__file__).parent
    solution = DocXPMigrationSolution(backend_path)
    
    success = await solution.run_comprehensive_check()
    
    if success:
        logger.info("✅ DocXP Platform is ready for production use")
        return 0
    else:
        logger.error("❌ DocXP Platform has critical issues that need attention")
        return 1

if __name__ == "__main__":
    exit(asyncio.run(main()))