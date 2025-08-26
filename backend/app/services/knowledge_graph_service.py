"""
Knowledge Graph Service for DocXP Enterprise
Provides unified relationship mapping across all technologies and repositories using Neo4j
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime

from neo4j import GraphDatabase, Driver
from neo4j.exceptions import ServiceUnavailable, TransientError

from app.core.config import settings

logger = logging.getLogger(__name__)

class NodeType(Enum):
    """Graph node types for code entities"""
    CODE_ENTITY = "CodeEntity"
    BUSINESS_RULE = "BusinessRule"
    TECHNOLOGY_COMPONENT = "TechnologyComponent"
    REPOSITORY = "Repository"
    PROJECT = "Project"
    FILE = "File"
    METHOD = "Method"
    CLASS = "Class"
    INTERFACE = "Interface"
    JSP_PAGE = "JSPPage"
    STRUTS_ACTION = "StrutsAction"
    DATABASE_TABLE = "DatabaseTable"
    API_ENDPOINT = "APIEndpoint"

class RelationshipType(Enum):
    """Graph relationship types"""
    CALLS = "CALLS"
    IMPLEMENTS = "IMPLEMENTS"
    EXTENDS = "EXTENDS"
    DEPENDS_ON = "DEPENDS_ON"
    CONTAINS = "CONTAINS"
    FLOWS_TO = "FLOWS_TO"
    REFERENCES = "REFERENCES"
    BELONGS_TO = "BELONGS_TO"
    USES = "USES"
    DEFINES = "DEFINES"
    FORWARDS_TO = "FORWARDS_TO"
    INHERITS_FROM = "INHERITS_FROM"
    COMMUNICATES_WITH = "COMMUNICATES_WITH"

@dataclass
class GraphNode:
    """Represents a graph node"""
    id: str
    node_type: NodeType
    properties: Dict[str, Any]
    labels: List[str] = None

@dataclass
class GraphRelationship:
    """Represents a graph relationship"""
    source_id: str
    target_id: str
    relationship_type: RelationshipType
    properties: Dict[str, Any] = None

class KnowledgeGraphService:
    """
    Advanced Neo4j knowledge graph service for enterprise code analysis
    
    Provides:
    - Cross-technology relationship mapping
    - Business rule flow tracing
    - Architectural pattern detection
    - Multi-repository dependency analysis
    """
    
    def __init__(self):
        self.driver: Optional[Driver] = None
        self.is_connected = False
        
        # Configuration from settings
        self.neo4j_uri = settings.NEO4J_URI
        self.neo4j_username = settings.NEO4J_USERNAME
        self.neo4j_password = settings.NEO4J_PASSWORD
        self.neo4j_database = settings.NEO4J_DATABASE
        
        # Connection pool settings from config
        self.max_connection_lifetime = settings.NEO4J_MAX_CONNECTION_LIFETIME
        self.max_connection_pool_size = settings.NEO4J_MAX_CONNECTION_POOL_SIZE
        self.connection_acquisition_timeout = settings.NEO4J_CONNECTION_ACQUISITION_TIMEOUT
        
    async def connect(self) -> bool:
        """Establish connection to Neo4j database"""
        try:
            self.driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_username, self.neo4j_password),
                max_connection_lifetime=self.max_connection_lifetime,
                max_connection_pool_size=self.max_connection_pool_size,
                connection_acquisition_timeout=self.connection_acquisition_timeout
            )
            
            # Test connection
            await self._test_connection()
            self.is_connected = True
            
            logger.info("Successfully connected to Neo4j knowledge graph")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            self.is_connected = False
            logger.info("Disconnected from Neo4j knowledge graph")
    
    async def _test_connection(self):
        """Test Neo4j connection"""
        def test_query(tx):
            result = tx.run("RETURN 1 as test")
            return result.single()["test"]
        
        with self.driver.session(database=self.neo4j_database) as session:
            result = session.execute_read(test_query)
            if result != 1:
                raise Exception("Connection test failed")
    
    async def create_node(self, node: GraphNode) -> bool:
        """Create a node in the knowledge graph"""
        if not self.is_connected:
            await self.connect()
        
        try:
            def create_node_tx(tx, node_data):
                # Build labels string
                labels = ":".join([node_data["node_type"]] + (node_data.get("labels") or []))
                
                # Create Cypher query
                query = f"""
                MERGE (n:{labels} {{id: $id}})
                SET n += $properties
                SET n.created_at = datetime()
                SET n.updated_at = datetime()
                RETURN n
                """
                
                result = tx.run(query, {
                    "id": node_data["id"],
                    "properties": node_data["properties"]
                })
                return result.single()
            
            node_data = {
                "id": node.id,
                "node_type": node.node_type.value,
                "labels": node.labels,
                "properties": node.properties
            }
            
            with self.driver.session(database=self.neo4j_database) as session:
                result = session.execute_write(create_node_tx, node_data)
                
            logger.debug(f"Created node: {node.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create node {node.id}: {e}")
            return False
    
    async def create_relationship(self, relationship: GraphRelationship) -> bool:
        """Create a relationship in the knowledge graph"""
        if not self.is_connected:
            await self.connect()
        
        try:
            def create_relationship_tx(tx, rel_data):
                query = f"""
                MATCH (a {{id: $source_id}})
                MATCH (b {{id: $target_id}})
                MERGE (a)-[r:{rel_data["relationship_type"]}]->(b)
                SET r += $properties
                SET r.created_at = datetime()
                SET r.updated_at = datetime()
                RETURN r
                """
                
                result = tx.run(query, {
                    "source_id": rel_data["source_id"],
                    "target_id": rel_data["target_id"],
                    "properties": rel_data["properties"] or {}
                })
                return result.single()
            
            rel_data = {
                "source_id": relationship.source_id,
                "target_id": relationship.target_id,
                "relationship_type": relationship.relationship_type.value,
                "properties": relationship.properties
            }
            
            with self.driver.session(database=self.neo4j_database) as session:
                result = session.execute_write(create_relationship_tx, rel_data)
                
            logger.debug(f"Created relationship: {relationship.source_id} -> {relationship.target_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create relationship {relationship.source_id} -> {relationship.target_id}: {e}")
            return False
    
    async def find_business_rule_path(self, entry_point: str, max_depth: int = 10) -> List[Dict[str, Any]]:
        """
        Find complete business rule path from UI entry point to data layer
        
        Traces JSP -> Struts Action -> Java Service -> Database flow
        """
        if not self.is_connected:
            await self.connect()
        
        try:
            def find_path_tx(tx):
                query = """
                MATCH path = (start {id: $entry_point})-[*1..$max_depth]->(end)
                WHERE start:JSPPage OR start:StrutsAction
                AND (end:DatabaseTable OR end:APIEndpoint)
                RETURN path,
                       length(path) as path_length,
                       [n in nodes(path) | {id: n.id, type: labels(n), properties: properties(n)}] as nodes,
                       [r in relationships(path) | {type: type(r), properties: properties(r)}] as relationships
                ORDER BY path_length ASC
                LIMIT 10
                """
                
                result = tx.run(query, {
                    "entry_point": entry_point,
                    "max_depth": max_depth
                })
                
                paths = []
                for record in result:
                    paths.append({
                        "path_length": record["path_length"],
                        "nodes": record["nodes"],
                        "relationships": record["relationships"]
                    })
                
                return paths
            
            with self.driver.session(database=self.neo4j_database) as session:
                paths = session.execute_read(find_path_tx)
                
            logger.info(f"Found {len(paths)} business rule paths from {entry_point}")
            return paths
            
        except Exception as e:
            logger.error(f"Failed to find business rule path from {entry_point}: {e}")
            return []
    
    async def find_similar_patterns(self, pattern_type: str, repository_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Find architecturally similar code patterns across repositories"""
        if not self.is_connected:
            await self.connect()
        
        try:
            def find_patterns_tx(tx):
                # Base query for pattern matching
                base_query = """
                MATCH (n:CodeEntity)
                WHERE n.pattern_type = $pattern_type
                """
                
                # Add repository filter if specified
                if repository_id:
                    base_query += """
                    AND EXISTS {
                        MATCH (n)-[:BELONGS_TO]->(r:Repository {id: $repository_id})
                    }
                    """
                
                query = base_query + """
                OPTIONAL MATCH (n)-[r]-(related)
                RETURN n,
                       collect(DISTINCT {
                           relationship: type(r),
                           related_node: {
                               id: related.id,
                               type: labels(related),
                               properties: properties(related)
                           }
                       }) as related_entities
                LIMIT 50
                """
                
                params = {"pattern_type": pattern_type}
                if repository_id:
                    params["repository_id"] = repository_id
                
                result = tx.run(query, params)
                
                patterns = []
                for record in result:
                    patterns.append({
                        "node": {
                            "id": record["n"]["id"],
                            "type": list(record["n"].labels),
                            "properties": dict(record["n"])
                        },
                        "related_entities": record["related_entities"]
                    })
                
                return patterns
            
            with self.driver.session(database=self.neo4j_database) as session:
                patterns = session.execute_read(find_patterns_tx)
                
            logger.info(f"Found {len(patterns)} similar patterns of type {pattern_type}")
            return patterns
            
        except Exception as e:
            logger.error(f"Failed to find similar patterns: {e}")
            return []
    
    async def get_cross_repository_dependencies(self, repository_ids: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Find dependencies between multiple repositories"""
        if not self.is_connected:
            await self.connect()
        
        try:
            def find_dependencies_tx(tx):
                query = """
                MATCH (source)-[:BELONGS_TO]->(repo1:Repository)
                MATCH (target)-[:BELONGS_TO]->(repo2:Repository)
                MATCH (source)-[r:DEPENDS_ON|CALLS|USES]->(target)
                WHERE repo1.id IN $repository_ids
                AND repo2.id IN $repository_ids
                AND repo1.id <> repo2.id
                RETURN repo1.id as source_repo,
                       repo2.id as target_repo,
                       source.id as source_entity,
                       target.id as target_entity,
                       type(r) as relationship_type,
                       properties(r) as relationship_properties
                """
                
                result = tx.run(query, {"repository_ids": repository_ids})
                
                dependencies = {}
                for record in result:
                    source_repo = record["source_repo"]
                    if source_repo not in dependencies:
                        dependencies[source_repo] = []
                    
                    dependencies[source_repo].append({
                        "target_repository": record["target_repo"],
                        "source_entity": record["source_entity"],
                        "target_entity": record["target_entity"],
                        "relationship_type": record["relationship_type"],
                        "properties": record["relationship_properties"]
                    })
                
                return dependencies
            
            with self.driver.session(database=self.neo4j_database) as session:
                dependencies = session.execute_read(find_dependencies_tx)
                
            logger.info(f"Found cross-repository dependencies for {len(repository_ids)} repositories")
            return dependencies
            
        except Exception as e:
            logger.error(f"Failed to find cross-repository dependencies: {e}")
            return {}
    
    async def get_technology_flow_chain(self, start_technology: str, end_technology: str) -> List[Dict[str, Any]]:
        """
        Get complete technology flow chain (e.g., JSP -> Struts -> Java -> CORBA -> Database)
        """
        if not self.is_connected:
            await self.connect()
        
        try:
            def find_flow_chain_tx(tx):
                query = """
                MATCH path = (start:TechnologyComponent {name: $start_technology})
                            -[:FLOWS_TO*1..10]->
                            (end:TechnologyComponent {name: $end_technology})
                RETURN path,
                       [n in nodes(path) | {
                           name: n.name,
                           type: n.type,
                           properties: properties(n)
                       }] as technology_chain,
                       [r in relationships(path) | {
                           type: type(r),
                           properties: properties(r)
                       }] as flow_relationships
                ORDER BY length(path) ASC
                LIMIT 5
                """
                
                result = tx.run(query, {
                    "start_technology": start_technology,
                    "end_technology": end_technology
                })
                
                chains = []
                for record in result:
                    chains.append({
                        "technology_chain": record["technology_chain"],
                        "flow_relationships": record["flow_relationships"],
                        "chain_length": len(record["technology_chain"])
                    })
                
                return chains
            
            with self.driver.session(database=self.neo4j_database) as session:
                chains = session.execute_read(find_flow_chain_tx)
                
            logger.info(f"Found {len(chains)} technology flow chains from {start_technology} to {end_technology}")
            return chains
            
        except Exception as e:
            logger.error(f"Failed to find technology flow chain: {e}")
            return []
    
    async def analyze_impact_of_change(self, entity_id: str, change_type: str) -> Dict[str, Any]:
        """
        Analyze the impact of changing a specific entity
        Returns affected entities and risk assessment
        """
        if not self.is_connected:
            await self.connect()
        
        try:
            def analyze_impact_tx(tx):
                # Find all entities that depend on this entity
                query = """
                MATCH (target {id: $entity_id})
                OPTIONAL MATCH (affected)-[r:DEPENDS_ON|CALLS|USES]->(target)
                OPTIONAL MATCH (affected)-[:BELONGS_TO]->(repo:Repository)
                RETURN target,
                       collect(DISTINCT {
                           entity: {
                               id: affected.id,
                               type: labels(affected),
                               properties: properties(affected)
                           },
                           relationship: type(r),
                           repository: repo.id
                       }) as affected_entities,
                       count(DISTINCT affected) as impact_count
                """
                
                result = tx.run(query, {"entity_id": entity_id})
                record = result.single()
                
                if not record:
                    return None
                
                return {
                    "target_entity": {
                        "id": record["target"]["id"],
                        "type": list(record["target"].labels),
                        "properties": dict(record["target"])
                    },
                    "affected_entities": record["affected_entities"],
                    "impact_count": record["impact_count"],
                    "change_type": change_type,
                    "risk_level": "high" if record["impact_count"] > 10 else "medium" if record["impact_count"] > 5 else "low"
                }
            
            with self.driver.session(database=self.neo4j_database) as session:
                impact_analysis = session.execute_read(analyze_impact_tx)
                
            if impact_analysis:
                logger.info(f"Impact analysis for {entity_id}: {impact_analysis['impact_count']} affected entities")
                return impact_analysis
            else:
                logger.warning(f"Entity {entity_id} not found for impact analysis")
                return {}
            
        except Exception as e:
            logger.error(f"Failed to analyze impact for entity {entity_id}: {e}")
            return {}
    
    async def create_indexes(self):
        """Create optimized indexes for common queries"""
        if not self.is_connected:
            await self.connect()
        
        indexes = [
            "CREATE INDEX entity_id_index IF NOT EXISTS FOR (n:CodeEntity) ON (n.id)",
            "CREATE INDEX repository_id_index IF NOT EXISTS FOR (n:Repository) ON (n.id)",
            "CREATE INDEX business_rule_id_index IF NOT EXISTS FOR (n:BusinessRule) ON (n.id)",
            "CREATE INDEX technology_component_name_index IF NOT EXISTS FOR (n:TechnologyComponent) ON (n.name)",
            "CREATE INDEX file_path_index IF NOT EXISTS FOR (n:File) ON (n.path)",
            "CREATE INDEX class_name_index IF NOT EXISTS FOR (n:Class) ON (n.name)",
            "CREATE INDEX method_name_index IF NOT EXISTS FOR (n:Method) ON (n.name)"
        ]
        
        try:
            def create_indexes_tx(tx):
                results = []
                for index_query in indexes:
                    try:
                        result = tx.run(index_query)
                        results.append(f"Created: {index_query}")
                    except Exception as e:
                        results.append(f"Failed: {index_query} - {e}")
                return results
            
            with self.driver.session(database=self.neo4j_database) as session:
                results = session.execute_write(create_indexes_tx)
                
            logger.info(f"Index creation results: {results}")
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
    
    async def get_graph_statistics(self) -> Dict[str, Any]:
        """Get knowledge graph statistics"""
        if not self.is_connected:
            await self.connect()
        
        try:
            def get_stats_tx(tx):
                queries = {
                    "total_nodes": "MATCH (n) RETURN count(n) as count",
                    "total_relationships": "MATCH ()-[r]->() RETURN count(r) as count",
                    "node_types": "MATCH (n) RETURN labels(n) as labels, count(n) as count",
                    "relationship_types": "MATCH ()-[r]->() RETURN type(r) as type, count(r) as count",
                    "repositories": "MATCH (r:Repository) RETURN count(r) as count",
                    "business_rules": "MATCH (br:BusinessRule) RETURN count(br) as count"
                }
                
                stats = {}
                
                # Get simple counts
                for stat_name, query in queries.items():
                    if stat_name in ["node_types", "relationship_types"]:
                        continue
                    result = tx.run(query)
                    stats[stat_name] = result.single()["count"]
                
                # Get node type distribution
                result = tx.run(queries["node_types"])
                stats["node_types"] = {}
                for record in result:
                    label = record["labels"][0] if record["labels"] else "Unknown"
                    stats["node_types"][label] = record["count"]
                
                # Get relationship type distribution
                result = tx.run(queries["relationship_types"])
                stats["relationship_types"] = {}
                for record in result:
                    stats["relationship_types"][record["type"]] = record["count"]
                
                return stats
            
            with self.driver.session(database=self.neo4j_database) as session:
                stats = session.execute_read(get_stats_tx)
                
            logger.info(f"Knowledge graph statistics: {json.dumps(stats, indent=2)}")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get graph statistics: {e}")
            return {}

# Global knowledge graph service instance
knowledge_graph_service = KnowledgeGraphService()

async def get_knowledge_graph_service() -> KnowledgeGraphService:
    """Get knowledge graph service instance"""
    if not knowledge_graph_service.is_connected:
        await knowledge_graph_service.connect()
    return knowledge_graph_service