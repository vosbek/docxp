"""
Graph Migration Service for DocXP Knowledge Graph
Handles schema initialization, migrations, and version management for Neo4j
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json

from app.services.knowledge_graph_service import KnowledgeGraphService, get_knowledge_graph_service
from app.models.graph_entities import GraphNodeType, GraphRelationshipType

logger = logging.getLogger(__name__)

@dataclass
class MigrationStep:
    """Represents a single migration step"""
    version: str
    description: str
    cypher_query: str
    rollback_query: Optional[str] = None
    validation_query: Optional[str] = None

@dataclass
class MigrationResult:
    """Result of a migration operation"""
    version: str
    success: bool
    message: str
    execution_time_seconds: float
    records_affected: int = 0

class GraphMigrationService:
    """
    Service for managing Neo4j schema migrations and constraints
    
    Provides:
    - Schema initialization with constraints and indexes
    - Version-controlled migrations
    - Rollback capabilities
    - Validation of schema state
    """
    
    def __init__(self):
        self.kg_service: Optional[KnowledgeGraphService] = None
        self.migration_history: List[MigrationResult] = []
        
    async def initialize(self):
        """Initialize the migration service with knowledge graph connection"""
        self.kg_service = await get_knowledge_graph_service()
        
    async def setup_initial_schema(self) -> bool:
        """
        Setup initial schema with constraints and indexes for DocXP knowledge graph
        """
        if not self.kg_service:
            await self.initialize()
        
        logger.info("Setting up initial Neo4j schema for DocXP knowledge graph")
        
        try:
            # Create constraints
            constraint_results = await self._create_constraints()
            
            # Create indexes  
            index_results = await self._create_indexes()
            
            # Create initial nodes for technology components
            tech_results = await self._create_technology_nodes()
            
            # Record migration
            migration_result = MigrationResult(
                version="1.0.0",
                success=True,
                message="Initial schema setup completed successfully",
                execution_time_seconds=0.0,
                records_affected=len(constraint_results) + len(index_results) + len(tech_results)
            )
            
            await self._record_migration(migration_result)
            
            logger.info("Initial schema setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup initial schema: {e}")
            migration_result = MigrationResult(
                version="1.0.0",
                success=False,
                message=f"Initial schema setup failed: {e}",
                execution_time_seconds=0.0
            )
            await self._record_migration(migration_result)
            return False
    
    async def _create_constraints(self) -> List[str]:
        """Create uniqueness constraints for graph nodes"""
        constraints = [
            # Node uniqueness constraints
            "CREATE CONSTRAINT entity_id_unique IF NOT EXISTS FOR (n:CodeEntity) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT repository_id_unique IF NOT EXISTS FOR (n:Repository) REQUIRE n.id IS UNIQUE", 
            "CREATE CONSTRAINT project_id_unique IF NOT EXISTS FOR (n:Project) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT business_rule_id_unique IF NOT EXISTS FOR (n:BusinessRule) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT technology_name_unique IF NOT EXISTS FOR (n:TechnologyComponent) REQUIRE n.name IS UNIQUE",
            "CREATE CONSTRAINT file_path_unique IF NOT EXISTS FOR (n:File) REQUIRE (n.path, n.repository_id) IS UNIQUE",
            "CREATE CONSTRAINT class_fqn_unique IF NOT EXISTS FOR (n:Class) REQUIRE (n.fully_qualified_name, n.repository_id) IS UNIQUE",
            "CREATE CONSTRAINT method_signature_unique IF NOT EXISTS FOR (n:Method) REQUIRE (n.signature, n.repository_id) IS UNIQUE",
            "CREATE CONSTRAINT jsp_path_unique IF NOT EXISTS FOR (n:JSPPage) REQUIRE (n.path, n.repository_id) IS UNIQUE",
            "CREATE CONSTRAINT struts_action_path_unique IF NOT EXISTS FOR (n:StrutsAction) REQUIRE (n.action_path, n.repository_id) IS UNIQUE",
            "CREATE CONSTRAINT database_table_unique IF NOT EXISTS FOR (n:DatabaseTable) REQUIRE (n.name, n.schema_name) IS UNIQUE",
            
            # Property existence constraints
            "CREATE CONSTRAINT entity_name_exists IF NOT EXISTS FOR (n:CodeEntity) REQUIRE n.name IS NOT NULL",
            "CREATE CONSTRAINT repository_name_exists IF NOT EXISTS FOR (n:Repository) REQUIRE n.name IS NOT NULL",
            "CREATE CONSTRAINT business_rule_description_exists IF NOT EXISTS FOR (n:BusinessRule) REQUIRE n.description IS NOT NULL"
        ]
        
        results = []
        
        def create_constraints_tx(tx):
            tx_results = []
            for constraint in constraints:
                try:
                    result = tx.run(constraint)
                    tx_results.append(f"Created: {constraint}")
                    logger.debug(f"Created constraint: {constraint}")
                except Exception as e:
                    tx_results.append(f"Failed: {constraint} - {e}")
                    logger.warning(f"Constraint creation failed: {constraint} - {e}")
            return tx_results
        
        with self.kg_service.driver.session(database=self.kg_service.neo4j_database) as session:
            results = session.execute_write(create_constraints_tx)
        
        logger.info(f"Constraint creation completed: {len(results)} constraints processed")
        return results
    
    async def _create_indexes(self) -> List[str]:
        """Create performance indexes for common queries"""
        indexes = [
            # Primary entity indexes
            "CREATE INDEX entity_type_index IF NOT EXISTS FOR (n:CodeEntity) ON (n.type)",
            "CREATE INDEX entity_repository_index IF NOT EXISTS FOR (n:CodeEntity) ON (n.repository_id)",
            "CREATE INDEX entity_project_index IF NOT EXISTS FOR (n:CodeEntity) ON (n.project_id)",
            "CREATE INDEX entity_file_index IF NOT EXISTS FOR (n:CodeEntity) ON (n.source_file)",
            
            # Business rule indexes
            "CREATE INDEX business_rule_category_index IF NOT EXISTS FOR (n:BusinessRule) ON (n.category)",
            "CREATE INDEX business_rule_domain_index IF NOT EXISTS FOR (n:BusinessRule) ON (n.business_domain)",
            "CREATE INDEX business_rule_priority_index IF NOT EXISTS FOR (n:BusinessRule) ON (n.priority)",
            
            # Repository and project indexes
            "CREATE INDEX repository_type_index IF NOT EXISTS FOR (n:Repository) ON (n.type)",
            "CREATE INDEX repository_status_index IF NOT EXISTS FOR (n:Repository) ON (n.status)",
            "CREATE INDEX project_status_index IF NOT EXISTS FOR (n:Project) ON (n.status)",
            
            # Technology component indexes
            "CREATE INDEX technology_category_index IF NOT EXISTS FOR (n:TechnologyComponent) ON (n.category)",
            "CREATE INDEX technology_version_index IF NOT EXISTS FOR (n:TechnologyComponent) ON (n.version)",
            "CREATE INDEX technology_deprecation_index IF NOT EXISTS FOR (n:TechnologyComponent) ON (n.deprecation_status)",
            
            # File and source code indexes
            "CREATE INDEX file_extension_index IF NOT EXISTS FOR (n:File) ON (n.extension)",
            "CREATE INDEX file_language_index IF NOT EXISTS FOR (n:File) ON (n.language)",
            "CREATE INDEX class_visibility_index IF NOT EXISTS FOR (n:Class) ON (n.visibility)",
            "CREATE INDEX method_visibility_index IF NOT EXISTS FOR (n:Method) ON (n.visibility)",
            
            # Struts-specific indexes
            "CREATE INDEX struts_action_class_index IF NOT EXISTS FOR (n:StrutsAction) ON (n.action_class)",
            "CREATE INDEX struts_action_method_index IF NOT EXISTS FOR (n:StrutsAction) ON (n.method_name)",
            "CREATE INDEX jsp_page_type_index IF NOT EXISTS FOR (n:JSPPage) ON (n.page_type)",
            
            # Database indexes
            "CREATE INDEX database_table_schema_index IF NOT EXISTS FOR (n:DatabaseTable) ON (n.schema_name)",
            "CREATE INDEX database_table_type_index IF NOT EXISTS FOR (n:DatabaseTable) ON (n.table_type)",
            
            # Temporal indexes
            "CREATE INDEX entity_created_index IF NOT EXISTS FOR (n:CodeEntity) ON (n.created_at)",
            "CREATE INDEX entity_updated_index IF NOT EXISTS FOR (n:CodeEntity) ON (n.updated_at)",
            
            # Composite indexes for common query patterns
            "CREATE INDEX entity_repo_type_index IF NOT EXISTS FOR (n:CodeEntity) ON (n.repository_id, n.type)",
            "CREATE INDEX business_rule_domain_priority_index IF NOT EXISTS FOR (n:BusinessRule) ON (n.business_domain, n.priority)",
            "CREATE INDEX file_repo_lang_index IF NOT EXISTS FOR (n:File) ON (n.repository_id, n.language)"
        ]
        
        results = []
        
        def create_indexes_tx(tx):
            tx_results = []
            for index in indexes:
                try:
                    result = tx.run(index)
                    tx_results.append(f"Created: {index}")
                    logger.debug(f"Created index: {index}")
                except Exception as e:
                    tx_results.append(f"Failed: {index} - {e}")
                    logger.warning(f"Index creation failed: {index} - {e}")
            return tx_results
        
        with self.kg_service.driver.session(database=self.kg_service.neo4j_database) as session:
            results = session.execute_write(create_indexes_tx)
        
        logger.info(f"Index creation completed: {len(results)} indexes processed")
        return results
    
    async def _create_technology_nodes(self) -> List[str]:
        """Create initial technology component nodes"""
        technology_components = [
            {
                "name": "JSP",
                "type": "presentation_technology",
                "category": "web_ui",
                "description": "JavaServer Pages - server-side Java technology",
                "deprecation_status": "legacy",
                "security_risk_level": "medium",
                "migration_complexity": "high",
                "replacement_options": ["React", "Angular", "Vue.js", "Thymeleaf"]
            },
            {
                "name": "Struts",
                "type": "mvc_framework", 
                "category": "web_framework",
                "description": "Apache Struts MVC framework",
                "deprecation_status": "legacy",
                "security_risk_level": "high",
                "migration_complexity": "high",
                "replacement_options": ["Spring Boot", "Spring MVC", "Jakarta EE"]
            },
            {
                "name": "Java",
                "type": "programming_language",
                "category": "backend_language",
                "description": "Java programming language",
                "deprecation_status": "active",
                "security_risk_level": "low",
                "migration_complexity": "low",
                "replacement_options": ["Java (newer version)", "Kotlin", "Scala"]
            },
            {
                "name": "CORBA",
                "type": "middleware",
                "category": "communication",
                "description": "Common Object Request Broker Architecture",
                "deprecation_status": "deprecated",
                "security_risk_level": "high",
                "migration_complexity": "very_high",
                "replacement_options": ["REST API", "gRPC", "GraphQL", "Message Queues"]
            },
            {
                "name": "Oracle Database",
                "type": "database",
                "category": "rdbms",
                "description": "Oracle relational database management system",
                "deprecation_status": "active",
                "security_risk_level": "low",
                "migration_complexity": "medium",
                "replacement_options": ["PostgreSQL", "MySQL", "MongoDB"]
            },
            {
                "name": "Spring Boot",
                "type": "application_framework",
                "category": "modern_framework",
                "description": "Modern Spring-based application framework",
                "deprecation_status": "active",
                "security_risk_level": "low",
                "migration_complexity": "low",
                "replacement_options": []
            },
            {
                "name": "REST API",
                "type": "api_protocol",
                "category": "modern_communication",
                "description": "Representational State Transfer API",
                "deprecation_status": "active",
                "security_risk_level": "low",
                "migration_complexity": "low",
                "replacement_options": ["GraphQL", "gRPC"]
            },
            {
                "name": "React",
                "type": "frontend_framework",
                "category": "modern_ui",
                "description": "React JavaScript library for building user interfaces",
                "deprecation_status": "active",
                "security_risk_level": "low",
                "migration_complexity": "medium",
                "replacement_options": ["Angular", "Vue.js", "Svelte"]
            }
        ]
        
        results = []
        
        def create_tech_nodes_tx(tx):
            tx_results = []
            for tech in technology_components:
                try:
                    query = """
                    MERGE (t:TechnologyComponent {name: $name})
                    SET t += $properties
                    SET t.created_at = datetime()
                    SET t.updated_at = datetime()
                    RETURN t.name as name
                    """
                    
                    result = tx.run(query, {
                        "name": tech["name"],
                        "properties": tech
                    })
                    
                    record = result.single()
                    if record:
                        tx_results.append(f"Created technology node: {record['name']}")
                        logger.debug(f"Created technology node: {record['name']}")
                    
                except Exception as e:
                    tx_results.append(f"Failed to create technology node {tech['name']}: {e}")
                    logger.warning(f"Technology node creation failed: {tech['name']} - {e}")
            
            return tx_results
        
        with self.kg_service.driver.session(database=self.kg_service.neo4j_database) as session:
            results = session.execute_write(create_tech_nodes_tx)
        
        # Create technology flow relationships
        await self._create_technology_flows()
        
        logger.info(f"Technology node creation completed: {len(results)} nodes processed")
        return results
    
    async def _create_technology_flows(self):
        """Create technology flow relationships for common migration paths"""
        technology_flows = [
            ("JSP", "React", "UI_MODERNIZATION"),
            ("JSP", "Angular", "UI_MODERNIZATION"),
            ("Struts", "Spring Boot", "FRAMEWORK_MODERNIZATION"),
            ("CORBA", "REST API", "API_MODERNIZATION"),
            ("CORBA", "gRPC", "API_MODERNIZATION"),
            ("Oracle Database", "PostgreSQL", "DATABASE_MIGRATION")
        ]
        
        def create_tech_flows_tx(tx):
            for source_tech, target_tech, flow_type in technology_flows:
                try:
                    query = """
                    MATCH (source:TechnologyComponent {name: $source_name})
                    MATCH (target:TechnologyComponent {name: $target_name})
                    MERGE (source)-[r:CAN_MIGRATE_TO]->(target)
                    SET r.migration_type = $flow_type
                    SET r.created_at = datetime()
                    RETURN source.name, target.name
                    """
                    
                    result = tx.run(query, {
                        "source_name": source_tech,
                        "target_name": target_tech,
                        "flow_type": flow_type
                    })
                    
                    logger.debug(f"Created migration flow: {source_tech} -> {target_tech}")
                    
                except Exception as e:
                    logger.warning(f"Failed to create migration flow {source_tech} -> {target_tech}: {e}")
        
        with self.kg_service.driver.session(database=self.kg_service.neo4j_database) as session:
            session.execute_write(create_tech_flows_tx)
    
    async def apply_migration(self, migration: MigrationStep) -> MigrationResult:
        """Apply a specific migration step"""
        if not self.kg_service:
            await self.initialize()
        
        start_time = datetime.utcnow()
        
        try:
            def apply_migration_tx(tx):
                result = tx.run(migration.cypher_query)
                records_affected = result.consume().counters.nodes_created + result.consume().counters.relationships_created
                return records_affected
            
            with self.kg_service.driver.session(database=self.kg_service.neo4j_database) as session:
                records_affected = session.execute_write(apply_migration_tx)
            
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds()
            
            # Validate migration if validation query provided
            validation_success = True
            if migration.validation_query:
                validation_success = await self._validate_migration(migration.validation_query)
            
            result = MigrationResult(
                version=migration.version,
                success=validation_success,
                message=f"Migration {migration.version} applied successfully" if validation_success else f"Migration {migration.version} failed validation",
                execution_time_seconds=execution_time,
                records_affected=records_affected
            )
            
            await self._record_migration(result)
            
            logger.info(f"Migration {migration.version} applied successfully")
            return result
            
        except Exception as e:
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds()
            
            result = MigrationResult(
                version=migration.version,
                success=False,
                message=f"Migration {migration.version} failed: {e}",
                execution_time_seconds=execution_time
            )
            
            await self._record_migration(result)
            
            logger.error(f"Migration {migration.version} failed: {e}")
            return result
    
    async def _validate_migration(self, validation_query: str) -> bool:
        """Validate that a migration was applied successfully"""
        try:
            def validate_tx(tx):
                result = tx.run(validation_query)
                return result.single()
            
            with self.kg_service.driver.session(database=self.kg_service.neo4j_database) as session:
                result = session.execute_read(validate_tx)
                
            return result is not None
            
        except Exception as e:
            logger.error(f"Migration validation failed: {e}")
            return False
    
    async def _record_migration(self, result: MigrationResult):
        """Record migration result in the history"""
        self.migration_history.append(result)
        
        # Also record in Neo4j for persistence
        try:
            def record_migration_tx(tx):
                query = """
                MERGE (m:MigrationHistory {version: $version})
                SET m.success = $success
                SET m.message = $message
                SET m.execution_time_seconds = $execution_time
                SET m.records_affected = $records_affected
                SET m.applied_at = datetime()
                RETURN m
                """
                
                tx.run(query, {
                    "version": result.version,
                    "success": result.success,
                    "message": result.message,
                    "execution_time": result.execution_time_seconds,
                    "records_affected": result.records_affected
                })
            
            with self.kg_service.driver.session(database=self.kg_service.neo4j_database) as session:
                session.execute_write(record_migration_tx)
                
        except Exception as e:
            logger.warning(f"Failed to record migration history: {e}")
    
    async def get_schema_info(self) -> Dict[str, Any]:
        """Get information about the current schema state"""
        if not self.kg_service:
            await self.initialize()
        
        try:
            def get_schema_info_tx(tx):
                # Get constraints
                constraints_result = tx.run("SHOW CONSTRAINTS")
                constraints = [record["name"] for record in constraints_result]
                
                # Get indexes
                indexes_result = tx.run("SHOW INDEXES")
                indexes = [record["name"] for record in indexes_result]
                
                # Get node labels
                labels_result = tx.run("CALL db.labels()")
                labels = [record["label"] for record in labels_result]
                
                # Get relationship types
                rel_types_result = tx.run("CALL db.relationshipTypes()")
                relationship_types = [record["relationshipType"] for record in rel_types_result]
                
                # Get migration history
                migration_result = tx.run("""
                    MATCH (m:MigrationHistory)
                    RETURN m.version as version, m.success as success, m.applied_at as applied_at
                    ORDER BY m.applied_at DESC
                """)
                migrations = [{
                    "version": record["version"],
                    "success": record["success"],
                    "applied_at": record["applied_at"]
                } for record in migration_result]
                
                return {
                    "constraints": constraints,
                    "indexes": indexes,
                    "node_labels": labels,
                    "relationship_types": relationship_types,
                    "migration_history": migrations
                }
            
            with self.kg_service.driver.session(database=self.kg_service.neo4j_database) as session:
                schema_info = session.execute_read(get_schema_info_tx)
                
            logger.info("Retrieved schema information successfully")
            return schema_info
            
        except Exception as e:
            logger.error(f"Failed to get schema information: {e}")
            return {}
    
    async def rollback_migration(self, version: str) -> bool:
        """Rollback a specific migration version (if rollback query available)"""
        # Find migration in history
        migration_to_rollback = None
        for migration in self.migration_history:
            if migration.version == version:
                migration_to_rollback = migration
                break
        
        if not migration_to_rollback:
            logger.error(f"Migration version {version} not found in history")
            return False
        
        # For now, rollback is manual - in future versions we could store rollback queries
        logger.warning(f"Rollback for migration {version} requires manual intervention")
        return False
    
    async def validate_schema_integrity(self) -> Dict[str, Any]:
        """Validate the integrity of the knowledge graph schema"""
        if not self.kg_service:
            await self.initialize()
        
        validation_results = {
            "orphaned_nodes": [],
            "missing_constraints": [],
            "missing_indexes": [],
            "data_integrity_issues": []
        }
        
        try:
            def validate_integrity_tx(tx):
                # Check for orphaned nodes (nodes with no relationships)
                orphaned_result = tx.run("""
                    MATCH (n)
                    WHERE NOT (n)--()
                    AND NOT n:MigrationHistory
                    AND NOT n:TechnologyComponent
                    RETURN labels(n) as labels, count(n) as count
                """)
                
                orphaned_nodes = [{
                    "labels": record["labels"],
                    "count": record["count"]
                } for record in orphaned_result]
                
                # Check for nodes missing required properties
                missing_props_result = tx.run("""
                    MATCH (n:CodeEntity)
                    WHERE n.name IS NULL OR n.type IS NULL
                    RETURN count(n) as count
                """)
                
                missing_props = missing_props_result.single()["count"]
                
                # Check for duplicate relationships
                duplicate_rels_result = tx.run("""
                    MATCH (a)-[r]->(b)
                    WITH a, b, type(r) as rel_type, count(r) as rel_count
                    WHERE rel_count > 1
                    RETURN rel_type, rel_count, count(*) as occurrences
                """)
                
                duplicate_rels = [{
                    "relationship_type": record["rel_type"],
                    "duplicate_count": record["rel_count"],
                    "occurrences": record["occurrences"]
                } for record in duplicate_rels_result]
                
                return {
                    "orphaned_nodes": orphaned_nodes,
                    "missing_required_properties": missing_props,
                    "duplicate_relationships": duplicate_rels
                }
            
            with self.kg_service.driver.session(database=self.kg_service.neo4j_database) as session:
                integrity_results = session.execute_read(validate_integrity_tx)
                
            validation_results.update(integrity_results)
            
            logger.info("Schema integrity validation completed")
            return validation_results
            
        except Exception as e:
            logger.error(f"Schema integrity validation failed: {e}")
            validation_results["validation_error"] = str(e)
            return validation_results

# Global migration service instance
graph_migration_service = GraphMigrationService()

async def get_graph_migration_service() -> GraphMigrationService:
    """Get graph migration service instance"""
    if not graph_migration_service.kg_service:
        await graph_migration_service.initialize()
    return graph_migration_service