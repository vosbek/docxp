"""
Enterprise Database Service for DocXP
Handles complex database operations with enterprise-grade patterns
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, ProgrammingError
import logging
import asyncio
from datetime import datetime

from app.core.database import get_async_session, engine
from app.models.business_domains import DomainTaxonomy, DomainClassificationRule, DomainClassificationResult

logger = logging.getLogger(__name__)

class EnterpriseDatabaseService:
    """
    Enterprise-grade database service with advanced schema management,
    integrity validation, and performance optimization
    """
    
    def __init__(self):
        self.validation_errors: List[str] = []
        self.performance_warnings: List[str] = []
    
    async def validate_schema_integrity(self) -> Dict[str, Any]:
        """
        Comprehensive schema integrity validation for enterprise deployment
        
        Returns:
            Dict containing validation results, errors, and recommendations
        """
        validation_results = {
            "status": "pending",
            "foreign_key_issues": [],
            "constraint_violations": [],
            "performance_issues": [],
            "recommendations": [],
            "validated_at": datetime.utcnow().isoformat()
        }
        
        async with get_async_session() as session:
            try:
                # 1. Validate foreign key constraints
                fk_issues = await self._validate_foreign_key_constraints(session)
                validation_results["foreign_key_issues"] = fk_issues
                
                # 2. Check for constraint violations
                constraint_issues = await self._check_constraint_violations(session)
                validation_results["constraint_violations"] = constraint_issues
                
                # 3. Performance analysis
                performance_issues = await self._analyze_performance_issues(session)
                validation_results["performance_issues"] = performance_issues
                
                # 4. Generate recommendations
                recommendations = await self._generate_recommendations(
                    fk_issues, constraint_issues, performance_issues
                )
                validation_results["recommendations"] = recommendations
                
                # 5. Set overall status
                total_issues = len(fk_issues) + len(constraint_issues) + len(performance_issues)
                validation_results["status"] = "healthy" if total_issues == 0 else "issues_found"
                
            except Exception as e:
                logger.error(f"Schema validation failed: {e}")
                validation_results["status"] = "error"
                validation_results["error"] = str(e)
        
        return validation_results
    
    async def _validate_foreign_key_constraints(self, session: AsyncSession) -> List[Dict[str, str]]:
        """Validate all foreign key constraints"""
        issues = []
        
        # Check domain_taxonomy self-referencing FK
        result = await session.execute(text("""
            SELECT dt.domain_id, dt.parent_domain_id
            FROM domain_taxonomy dt
            WHERE dt.parent_domain_id IS NOT NULL
            AND dt.parent_domain_id NOT IN (
                SELECT domain_id FROM domain_taxonomy
            )
        """))
        
        orphaned_refs = result.fetchall()
        for row in orphaned_refs:
            issues.append({
                "table": "domain_taxonomy",
                "issue": "orphaned_reference",
                "domain_id": row.domain_id,
                "invalid_parent": row.parent_domain_id,
                "severity": "high"
            })
        
        # Check domain classification rules FK
        result = await session.execute(text("""
            SELECT rule_id, target_domain
            FROM domain_classification_rules
            WHERE target_domain NOT IN (
                SELECT domain_id FROM domain_taxonomy
            )
        """))
        
        invalid_targets = result.fetchall()
        for row in invalid_targets:
            issues.append({
                "table": "domain_classification_rules",
                "issue": "invalid_target_domain",
                "rule_id": row.rule_id,
                "invalid_target": row.target_domain,
                "severity": "medium"
            })
        
        return issues
    
    async def _check_constraint_violations(self, session: AsyncSession) -> List[Dict[str, str]]:
        """Check for business logic constraint violations"""
        violations = []
        
        # Check for circular references in domain taxonomy
        result = await session.execute(text("""
            WITH RECURSIVE hierarchy_check AS (
                SELECT domain_id, parent_domain_id, 1 as depth,
                       ARRAY[domain_id] as path
                FROM domain_taxonomy
                WHERE parent_domain_id IS NOT NULL
                
                UNION ALL
                
                SELECT hc.domain_id, dt.parent_domain_id, hc.depth + 1,
                       hc.path || dt.domain_id
                FROM hierarchy_check hc
                JOIN domain_taxonomy dt ON dt.domain_id = hc.parent_domain_id
                WHERE dt.domain_id != ALL(hc.path)
                AND hc.depth < 20
            )
            SELECT domain_id, path
            FROM hierarchy_check
            WHERE parent_domain_id = ANY(path)
        """))
        
        circular_refs = result.fetchall()
        for row in circular_refs:
            violations.append({
                "table": "domain_taxonomy",
                "violation": "circular_reference",
                "domain_id": row.domain_id,
                "path": " -> ".join(row.path),
                "severity": "critical"
            })
        
        # Check level consistency
        result = await session.execute(text("""
            WITH hierarchy_levels AS (
                SELECT dt.domain_id, dt.level,
                       CASE 
                           WHEN dt.parent_domain_id IS NULL THEN 0
                           ELSE COALESCE((
                               SELECT parent.level + 1 
                               FROM domain_taxonomy parent 
                               WHERE parent.domain_id = dt.parent_domain_id
                           ), 0)
                       END as calculated_level
                FROM domain_taxonomy dt
            )
            SELECT domain_id, level, calculated_level
            FROM hierarchy_levels
            WHERE level != calculated_level
        """))
        
        level_issues = result.fetchall()
        for row in level_issues:
            violations.append({
                "table": "domain_taxonomy",
                "violation": "level_inconsistency",
                "domain_id": row.domain_id,
                "current_level": row.level,
                "expected_level": row.calculated_level,
                "severity": "medium"
            })
        
        return violations
    
    async def _analyze_performance_issues(self, session: AsyncSession) -> List[Dict[str, str]]:
        """Analyze performance issues and missing indexes"""
        issues = []
        
        # Check for missing indexes on foreign key columns
        inspector = inspect(engine)
        
        # Get table information
        tables_to_check = [
            ("domain_taxonomy", "parent_domain_id"),
            ("domain_classification_rules", "target_domain"),
            ("domain_classification_results", "primary_domain"),
            ("domain_classification_results", "repository_id")
        ]
        
        for table_name, column_name in tables_to_check:
            # Check if index exists
            indexes = inspector.get_indexes(table_name)
            has_index = any(column_name in idx['column_names'] for idx in indexes)
            
            if not has_index:
                issues.append({
                    "type": "missing_index",
                    "table": table_name,
                    "column": column_name,
                    "impact": "query_performance",
                    "severity": "medium"
                })
        
        # Check table sizes for partitioning recommendations
        result = await session.execute(text("""
            SELECT schemaname, tablename, n_tup_ins + n_tup_upd + n_tup_del as total_operations
            FROM pg_stat_user_tables
            WHERE schemaname = 'public'
            AND tablename IN ('domain_classification_results', 'business_rule_traces')
            AND n_tup_ins + n_tup_upd + n_tup_del > 100000
        """))
        
        large_tables = result.fetchall()
        for row in large_tables:
            issues.append({
                "type": "large_table",
                "table": row.tablename,
                "operations": row.total_operations,
                "recommendation": "consider_partitioning",
                "severity": "low"
            })
        
        return issues
    
    async def _generate_recommendations(self, fk_issues: List, constraint_issues: List, perf_issues: List) -> List[Dict[str, str]]:
        """Generate actionable recommendations based on validation results"""
        recommendations = []
        
        # Foreign key recommendations
        if fk_issues:
            recommendations.append({
                "category": "data_integrity",
                "priority": "high",
                "action": "fix_foreign_key_violations",
                "description": "Run migration script to fix foreign key constraint violations",
                "sql": "UPDATE domain_taxonomy SET parent_domain_id = NULL WHERE parent_domain_id NOT IN (SELECT domain_id FROM domain_taxonomy);"
            })
        
        # Circular reference recommendations
        circular_refs = [issue for issue in constraint_issues if issue.get("violation") == "circular_reference"]
        if circular_refs:
            recommendations.append({
                "category": "business_logic",
                "priority": "critical",
                "action": "fix_circular_references",
                "description": "Manually review and fix circular references in domain taxonomy hierarchy",
                "affected_domains": [issue["domain_id"] for issue in circular_refs]
            })
        
        # Level consistency recommendations
        level_issues = [issue for issue in constraint_issues if issue.get("violation") == "level_inconsistency"]
        if level_issues:
            recommendations.append({
                "category": "data_quality",
                "priority": "medium",
                "action": "fix_hierarchy_levels",
                "description": "Recalculate hierarchy levels using the fix_domain_taxonomy_levels() function",
                "sql": "SELECT fix_domain_taxonomy_levels();"
            })
        
        # Performance recommendations
        missing_indexes = [issue for issue in perf_issues if issue.get("type") == "missing_index"]
        if missing_indexes:
            recommendations.append({
                "category": "performance",
                "priority": "medium",
                "action": "create_missing_indexes",
                "description": "Create indexes on foreign key columns for better query performance",
                "affected_columns": [(issue["table"], issue["column"]) for issue in missing_indexes]
            })
        
        # Enterprise monitoring recommendations
        recommendations.append({
            "category": "monitoring",
            "priority": "low",
            "action": "implement_health_checks",
            "description": "Set up automated health checks to monitor schema integrity",
            "frequency": "daily"
        })
        
        return recommendations
    
    async def fix_foreign_key_violations(self) -> Dict[str, Any]:
        """
        Automatically fix foreign key violations where possible
        
        Returns:
            Dict containing fix results and any manual actions needed
        """
        fix_results = {
            "status": "completed",
            "fixes_applied": [],
            "manual_actions_required": [],
            "fixed_at": datetime.utcnow().isoformat()
        }
        
        async with get_async_session() as session:
            try:
                # Fix orphaned parent references
                result = await session.execute(text("""
                    UPDATE domain_taxonomy 
                    SET parent_domain_id = NULL 
                    WHERE parent_domain_id IS NOT NULL 
                    AND parent_domain_id NOT IN (SELECT domain_id FROM domain_taxonomy)
                """))
                
                orphaned_fixed = result.rowcount
                if orphaned_fixed > 0:
                    fix_results["fixes_applied"].append({
                        "fix": "orphaned_parent_references",
                        "records_affected": orphaned_fixed,
                        "action": "Set parent_domain_id to NULL for orphaned references"
                    })
                
                # Fix level inconsistencies
                result = await session.execute(text("SELECT fix_domain_taxonomy_levels()"))
                levels_fixed = result.scalar()
                
                if levels_fixed > 0:
                    fix_results["fixes_applied"].append({
                        "fix": "hierarchy_levels",
                        "records_affected": levels_fixed,
                        "action": "Recalculated hierarchy levels based on parent relationships"
                    })
                
                await session.commit()
                
            except Exception as e:
                await session.rollback()
                fix_results["status"] = "error"
                fix_results["error"] = str(e)
                logger.error(f"Foreign key fix failed: {e}")
        
        return fix_results
    
    async def initialize_domain_taxonomy_seed_data(self) -> Dict[str, Any]:
        """
        Initialize domain taxonomy with enterprise seed data
        Safe for existing data - only adds missing entries
        """
        from app.models.business_domains import ENTERPRISE_DOMAIN_TAXONOMY
        
        initialization_results = {
            "status": "completed",
            "records_created": 0,
            "records_updated": 0,
            "errors": [],
            "initialized_at": datetime.utcnow().isoformat()
        }
        
        async with get_async_session() as session:
            try:
                # Flatten the taxonomy structure
                domains_to_create = []
                
                def flatten_taxonomy(data: Dict, parent_id: Optional[str] = None, level: int = 0):
                    for domain_id, domain_data in data.items():
                        domain_record = {
                            "domain_id": domain_id,
                            "parent_domain_id": parent_id,
                            "name": domain_data.get("name", domain_id),
                            "category": domain_data.get("category", "").value if hasattr(domain_data.get("category", ""), 'value') else str(domain_data.get("category", "")),
                            "subdomain": domain_data.get("subdomain", "").value if hasattr(domain_data.get("subdomain", ""), 'value') else str(domain_data.get("subdomain", "")) if domain_data.get("subdomain") else None,
                            "level": level,
                            "description": domain_data.get("description", ""),
                            "business_purpose": domain_data.get("business_purpose", ""),
                            "typical_components": domain_data.get("typical_components", []),
                            "key_stakeholders": domain_data.get("key_stakeholders", []),
                            "keywords": domain_data.get("keywords", []),
                            "patterns": domain_data.get("patterns", []),
                            "regulatory_scope": domain_data.get("regulatory_scope", [])
                        }
                        domains_to_create.append(domain_record)
                        
                        # Process children
                        if "children" in domain_data:
                            flatten_taxonomy(domain_data["children"], domain_id, level + 1)
                
                flatten_taxonomy(ENTERPRISE_DOMAIN_TAXONOMY)
                
                # Create domains in order (parents first)
                domains_to_create.sort(key=lambda x: x["level"])
                
                for domain_data in domains_to_create:
                    # Check if domain already exists
                    existing = await session.execute(
                        text("SELECT id FROM domain_taxonomy WHERE domain_id = :domain_id"),
                        {"domain_id": domain_data["domain_id"]}
                    )
                    
                    if existing.fetchone():
                        continue  # Skip existing domains
                    
                    # Create new domain
                    domain = DomainTaxonomy(**domain_data)
                    session.add(domain)
                    initialization_results["records_created"] += 1
                
                await session.commit()
                
            except Exception as e:
                await session.rollback()
                initialization_results["status"] = "error"
                initialization_results["errors"].append(str(e))
                logger.error(f"Domain taxonomy initialization failed: {e}")
        
        return initialization_results
    
    async def create_enterprise_health_check(self) -> Dict[str, Any]:
        """
        Comprehensive enterprise health check for the database
        """
        health_check = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database_connectivity": False,
            "schema_integrity": {},
            "performance_metrics": {},
            "recommendations": []
        }
        
        try:
            # Test database connectivity
            async with get_async_session() as session:
                await session.execute(text("SELECT 1"))
                health_check["database_connectivity"] = True
            
            # Run schema validation
            schema_results = await self.validate_schema_integrity()
            health_check["schema_integrity"] = schema_results
            
            # Performance metrics
            health_check["performance_metrics"] = await self._get_performance_metrics()
            
            # Determine overall health
            if (not health_check["database_connectivity"] or 
                schema_results["status"] == "error" or
                len(schema_results.get("foreign_key_issues", [])) > 0 or
                any(issue["severity"] == "critical" for issue in schema_results.get("constraint_violations", []))):
                health_check["status"] = "unhealthy"
            elif (len(schema_results.get("performance_issues", [])) > 0 or
                  any(issue["severity"] == "high" for issue in schema_results.get("foreign_key_issues", []))):
                health_check["status"] = "warning"
            
        except Exception as e:
            health_check["status"] = "error"
            health_check["error"] = str(e)
            logger.error(f"Health check failed: {e}")
        
        return health_check
    
    async def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get database performance metrics"""
        metrics = {}
        
        async with get_async_session() as session:
            # Table sizes
            result = await session.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                LIMIT 10
            """))
            
            metrics["table_sizes"] = [
                {
                    "table": row.tablename,
                    "size": row.size,
                    "size_bytes": row.size_bytes
                } for row in result.fetchall()
            ]
            
            # Index usage
            result = await session.execute(text("""
                SELECT 
                    indexname,
                    idx_tup_read,
                    idx_tup_fetch
                FROM pg_stat_user_indexes
                WHERE schemaname = 'public'
                ORDER BY idx_tup_read DESC
                LIMIT 10
            """))
            
            metrics["index_usage"] = [
                {
                    "index": row.indexname,
                    "reads": row.idx_tup_read,
                    "fetches": row.idx_tup_fetch
                } for row in result.fetchall()
            ]
        
        return metrics

# Global service instance
enterprise_db_service = EnterpriseDatabaseService()