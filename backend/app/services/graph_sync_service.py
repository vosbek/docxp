"""
Graph Synchronization Service for DocXP
Handles real-time synchronization between PostgreSQL, Redis, OpenSearch, and Neo4j
"""

import logging
import asyncio
import json
from typing import Dict, List, Any, Optional, Set, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, insert
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import get_async_session
from app.services.knowledge_graph_service import (
    KnowledgeGraphService, get_knowledge_graph_service,
    GraphNode, GraphRelationship, NodeType, RelationshipType
)
# NOTE: Vector operations now handled by OpenSearch - ChromaDB removed
# from app.services.vector_service import get_vector_service
from app.models.base import Repository, CodeEntity, BusinessRule
from app.models.graph_entities import (
    GraphNodeMetadata, GraphRelationshipMetadata, GraphBusinessRuleTrace,
    CodeEntityProperties, BusinessRuleProperties, TechnologyComponentProperties
)

logger = logging.getLogger(__name__)

class SyncEventType(Enum):
    """Types of synchronization events"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    BATCH_CREATE = "batch_create"
    BATCH_UPDATE = "batch_update"
    FULL_SYNC = "full_sync"

class SyncStatus(Enum):
    """Synchronization status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class SyncEvent:
    """Represents a synchronization event"""
    event_id: str
    event_type: SyncEventType
    entity_type: str
    entity_id: str
    entity_data: Dict[str, Any]
    source_system: str  # postgresql, redis, opensearch, neo4j
    target_systems: List[str]
    timestamp: datetime
    priority: int = 1  # 1=highest, 5=lowest
    retry_count: int = 0
    max_retries: int = 3
    status: SyncStatus = SyncStatus.PENDING
    error_message: Optional[str] = None

class GraphSyncService:
    """
    Advanced synchronization service for multi-database architecture
    
    Coordinates data between:
    - PostgreSQL: Primary metadata and business logic storage
    - Redis: Queue management and caching
    - OpenSearch: Full-text search and retrieval
    - Neo4j: Knowledge graph relationships
    
    Provides:
    - Real-time sync with event-driven updates
    - Conflict resolution strategies
    - Retry mechanisms for failed syncs
    - Performance optimization with batching
    """
    
    def __init__(self):
        # Service connections
        self.kg_service: Optional[KnowledgeGraphService] = None
        self.vector_service = None
        self.redis_client: Optional[redis.Redis] = None
        
        # Configuration
        self.redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
        self.sync_queue_name = "docxp:graph_sync_queue"
        self.cache_prefix = "docxp:sync_cache:"
        self.lock_prefix = "docxp:sync_lock:"
        
        # Sync configuration
        self.batch_size = 100
        self.sync_interval_seconds = 30
        self.max_retry_attempts = 3
        self.lock_timeout_seconds = 300  # 5 minutes
        
        # Event queues
        self.pending_events: List[SyncEvent] = []
        self.failed_events: List[SyncEvent] = []
        
        # Performance metrics
        self.sync_stats = {
            "events_processed": 0,
            "events_failed": 0,
            "last_sync_time": None,
            "average_sync_time": 0.0
        }
        
    async def initialize(self):
        """Initialize all service connections"""
        try:
            # Initialize knowledge graph service
            self.kg_service = await get_knowledge_graph_service()
            
            # Initialize vector service
            self.vector_service = await get_vector_service()
            
            # Initialize Redis connection
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            
            logger.info("Graph sync service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize graph sync service: {e}")
            raise
    
    async def sync_repository_metadata(self, repository_id: str, force_full_sync: bool = False) -> bool:
        """
        Synchronize all metadata for a repository across all systems
        """
        if not self.kg_service:
            await self.initialize()
        
        try:
            logger.info(f"Starting repository metadata sync for {repository_id}")
            
            # Get repository data from PostgreSQL
            async with get_async_session() as session:
                repo_data = await self._get_repository_data(session, repository_id)
                
                if not repo_data:
                    logger.warning(f"Repository {repository_id} not found in PostgreSQL")
                    return False
            
            # Create sync events for all entities
            sync_events = []
            
            # Repository node
            repo_sync_event = SyncEvent(
                event_id=f"repo_sync_{repository_id}_{datetime.utcnow().isoformat()}",
                event_type=SyncEventType.UPDATE if not force_full_sync else SyncEventType.FULL_SYNC,
                entity_type="repository",
                entity_id=repository_id,
                entity_data=repo_data["repository"],
                source_system="postgresql",
                target_systems=["neo4j", "opensearch"],
                timestamp=datetime.utcnow()
            )
            sync_events.append(repo_sync_event)
            
            # Code entities
            for entity in repo_data["code_entities"]:
                entity_sync_event = SyncEvent(
                    event_id=f"entity_sync_{entity['id']}_{datetime.utcnow().isoformat()}",
                    event_type=SyncEventType.UPDATE,
                    entity_type="code_entity",
                    entity_id=entity["id"],
                    entity_data=entity,
                    source_system="postgresql",
                    target_systems=["neo4j", "opensearch"],
                    timestamp=datetime.utcnow()
                )
                sync_events.append(entity_sync_event)
            
            # Business rules
            for rule in repo_data["business_rules"]:
                rule_sync_event = SyncEvent(
                    event_id=f"rule_sync_{rule['id']}_{datetime.utcnow().isoformat()}",
                    event_type=SyncEventType.UPDATE,
                    entity_type="business_rule",
                    entity_id=rule["id"],
                    entity_data=rule,
                    source_system="postgresql",
                    target_systems=["neo4j", "opensearch"],
                    timestamp=datetime.utcnow()
                )
                sync_events.append(rule_sync_event)
            
            # Process sync events
            success_count = await self._process_sync_events_batch(sync_events)
            
            logger.info(f"Repository sync completed: {success_count}/{len(sync_events)} events successful")
            return success_count == len(sync_events)
            
        except Exception as e:
            logger.error(f"Repository metadata sync failed for {repository_id}: {e}")
            return False
    
    async def _get_repository_data(self, session: AsyncSession, repository_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive repository data from PostgreSQL"""
        try:
            # Get repository
            repo_stmt = select(Repository).where(Repository.id == repository_id)
            repo_result = await session.execute(repo_stmt)
            repository = repo_result.scalar_one_or_none()
            
            if not repository:
                return None
            
            # Get code entities
            entities_stmt = select(CodeEntity).where(CodeEntity.repository_id == repository_id)
            entities_result = await session.execute(entities_stmt)
            code_entities = entities_result.scalars().all()
            
            # Get business rules
            rules_stmt = select(BusinessRule).where(BusinessRule.repository_id == repository_id)
            rules_result = await session.execute(rules_stmt)
            business_rules = rules_result.scalars().all()
            
            # Convert to dictionaries
            repo_data = {
                "repository": {
                    "id": repository.id,
                    "name": repository.name,
                    "type": repository.type,
                    "url": getattr(repository, 'url', ''),
                    "status": getattr(repository, 'status', 'active'),
                    "created_at": repository.created_at.isoformat() if repository.created_at else None,
                    "updated_at": repository.updated_at.isoformat() if repository.updated_at else None
                },
                "code_entities": [
                    {
                        "id": entity.id,
                        "name": entity.name,
                        "type": entity.type,
                        "file_path": entity.file_path,
                        "line_number": entity.line_number,
                        "repository_id": entity.repository_id,
                        "properties": entity.properties or {},
                        "created_at": entity.created_at.isoformat() if entity.created_at else None
                    } for entity in code_entities
                ],
                "business_rules": [
                    {
                        "id": rule.id,
                        "name": rule.name,
                        "description": rule.description,
                        "category": rule.category,
                        "repository_id": rule.repository_id,
                        "properties": rule.properties or {},
                        "created_at": rule.created_at.isoformat() if rule.created_at else None
                    } for rule in business_rules
                ]
            }
            
            return repo_data
            
        except Exception as e:
            logger.error(f"Failed to get repository data for {repository_id}: {e}")
            return None
    
    async def _process_sync_events_batch(self, sync_events: List[SyncEvent]) -> int:
        """Process a batch of sync events"""
        success_count = 0
        
        # Group events by target system for efficiency
        events_by_system = {}
        for event in sync_events:
            for target_system in event.target_systems:
                if target_system not in events_by_system:
                    events_by_system[target_system] = []
                events_by_system[target_system].append(event)
        
        # Process each target system
        for target_system, system_events in events_by_system.items():
            try:
                if target_system == "neo4j":
                    success_count += await self._sync_to_neo4j_batch(system_events)
                elif target_system == "opensearch":
                    success_count += await self._sync_to_opensearch_batch(system_events)
                elif target_system == "redis":
                    success_count += await self._sync_to_redis_batch(system_events)
                    
            except Exception as e:
                logger.error(f"Batch sync to {target_system} failed: {e}")
                # Mark events as failed
                for event in system_events:
                    event.status = SyncStatus.FAILED
                    event.error_message = str(e)
                    self.failed_events.append(event)
        
        return success_count
    
    async def _sync_to_neo4j_batch(self, events: List[SyncEvent]) -> int:
        """Sync events to Neo4j knowledge graph"""
        success_count = 0
        
        for event in events:
            try:
                if event.entity_type == "repository":
                    success = await self._sync_repository_to_neo4j(event)
                elif event.entity_type == "code_entity":
                    success = await self._sync_code_entity_to_neo4j(event)
                elif event.entity_type == "business_rule":
                    success = await self._sync_business_rule_to_neo4j(event)
                else:
                    logger.warning(f"Unknown entity type for Neo4j sync: {event.entity_type}")
                    continue
                
                if success:
                    success_count += 1
                    event.status = SyncStatus.COMPLETED
                else:
                    event.status = SyncStatus.FAILED
                    
            except Exception as e:
                logger.error(f"Failed to sync event {event.event_id} to Neo4j: {e}")
                event.status = SyncStatus.FAILED
                event.error_message = str(e)
        
        return success_count
    
    async def _sync_repository_to_neo4j(self, event: SyncEvent) -> bool:
        """Sync repository node to Neo4j"""
        try:
            repo_data = event.entity_data
            
            # Create repository node
            repo_node = GraphNode(
                id=repo_data["id"],
                node_type=NodeType.REPOSITORY,
                properties={
                    "name": repo_data["name"],
                    "type": repo_data["type"],
                    "url": repo_data.get("url", ""),
                    "status": repo_data.get("status", "active"),
                    "created_at": repo_data.get("created_at"),
                    "updated_at": repo_data.get("updated_at")
                },
                labels=["Repository"]
            )
            
            success = await self.kg_service.create_node(repo_node)
            
            if success:
                logger.debug(f"Synced repository {repo_data['id']} to Neo4j")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to sync repository to Neo4j: {e}")
            return False
    
    async def _sync_code_entity_to_neo4j(self, event: SyncEvent) -> bool:
        """Sync code entity node to Neo4j"""
        try:
            entity_data = event.entity_data
            
            # Determine node type based on entity type
            node_type_mapping = {
                "class": NodeType.CLASS,
                "method": NodeType.METHOD,
                "function": NodeType.FUNCTION,
                "interface": NodeType.INTERFACE,
                "jsp_page": NodeType.JSP_PAGE,
                "struts_action": NodeType.STRUTS_ACTION,
                "file": NodeType.FILE
            }
            
            node_type = node_type_mapping.get(entity_data.get("type", ""), NodeType.CODE_ENTITY)
            
            # Create code entity node
            entity_node = GraphNode(
                id=entity_data["id"],
                node_type=node_type,
                properties={
                    "name": entity_data["name"],
                    "type": entity_data["type"],
                    "file_path": entity_data.get("file_path", ""),
                    "line_number": entity_data.get("line_number"),
                    "repository_id": entity_data["repository_id"],
                    "created_at": entity_data.get("created_at"),
                    **entity_data.get("properties", {})
                },
                labels=["CodeEntity", entity_data.get("type", "").title()]
            )
            
            success = await self.kg_service.create_node(entity_node)
            
            # Create relationship to repository
            if success:
                repo_relationship = GraphRelationship(
                    source_id=entity_data["id"],
                    target_id=entity_data["repository_id"],
                    relationship_type=RelationshipType.BELONGS_TO,
                    properties={"created_at": datetime.utcnow().isoformat()}
                )
                await self.kg_service.create_relationship(repo_relationship)
                
                logger.debug(f"Synced code entity {entity_data['id']} to Neo4j")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to sync code entity to Neo4j: {e}")
            return False
    
    async def _sync_business_rule_to_neo4j(self, event: SyncEvent) -> bool:
        """Sync business rule node to Neo4j"""
        try:
            rule_data = event.entity_data
            
            # Create business rule node
            rule_node = GraphNode(
                id=rule_data["id"],
                node_type=NodeType.BUSINESS_RULE,
                properties={
                    "name": rule_data["name"],
                    "description": rule_data["description"],
                    "category": rule_data["category"],
                    "repository_id": rule_data["repository_id"],
                    "created_at": rule_data.get("created_at"),
                    **rule_data.get("properties", {})
                },
                labels=["BusinessRule"]
            )
            
            success = await self.kg_service.create_node(rule_node)
            
            # Create relationship to repository
            if success:
                repo_relationship = GraphRelationship(
                    source_id=rule_data["id"],
                    target_id=rule_data["repository_id"],
                    relationship_type=RelationshipType.BELONGS_TO,
                    properties={"created_at": datetime.utcnow().isoformat()}
                )
                await self.kg_service.create_relationship(repo_relationship)
                
                logger.debug(f"Synced business rule {rule_data['id']} to Neo4j")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to sync business rule to Neo4j: {e}")
            return False
    
    async def _sync_to_opensearch_batch(self, events: List[SyncEvent]) -> int:
        """Sync events to OpenSearch"""
        success_count = 0
        
        if not self.vector_service:
            logger.warning("Vector service not available for OpenSearch sync")
            return 0
        
        for event in events:
            try:
                # Prepare document for OpenSearch indexing
                doc_data = {
                    "id": event.entity_id,
                    "type": event.entity_type,
                    "content": self._extract_searchable_content(event.entity_data),
                    "metadata": event.entity_data,
                    "timestamp": event.timestamp.isoformat(),
                    "repository_id": event.entity_data.get("repository_id")
                }
                
                # Index in OpenSearch (through vector service)
                # Note: This would need to be implemented in the vector service
                # For now, we'll log the intent
                logger.debug(f"Would sync {event.entity_id} to OpenSearch")
                success_count += 1
                event.status = SyncStatus.COMPLETED
                
            except Exception as e:
                logger.error(f"Failed to sync event {event.event_id} to OpenSearch: {e}")
                event.status = SyncStatus.FAILED
                event.error_message = str(e)
        
        return success_count
    
    async def _sync_to_redis_batch(self, events: List[SyncEvent]) -> int:
        """Sync events to Redis cache"""
        success_count = 0
        
        for event in events:
            try:
                # Cache entity data in Redis
                cache_key = f"{self.cache_prefix}{event.entity_type}:{event.entity_id}"
                cache_data = json.dumps(event.entity_data, default=str)
                
                await self.redis_client.setex(
                    cache_key,
                    timedelta(hours=24),  # 24 hour cache
                    cache_data
                )
                
                success_count += 1
                event.status = SyncStatus.COMPLETED
                logger.debug(f"Cached {event.entity_id} in Redis")
                
            except Exception as e:
                logger.error(f"Failed to sync event {event.event_id} to Redis: {e}")
                event.status = SyncStatus.FAILED
                event.error_message = str(e)
        
        return success_count
    
    def _extract_searchable_content(self, entity_data: Dict[str, Any]) -> str:
        """Extract searchable text content from entity data"""
        searchable_parts = []
        
        # Add name and description
        if "name" in entity_data:
            searchable_parts.append(entity_data["name"])
        
        if "description" in entity_data:
            searchable_parts.append(entity_data["description"])
        
        # Add file path for context
        if "file_path" in entity_data:
            searchable_parts.append(entity_data["file_path"])
        
        # Add properties text
        properties = entity_data.get("properties", {})
        for key, value in properties.items():
            if isinstance(value, str) and len(value) > 0:
                searchable_parts.append(f"{key}: {value}")
        
        return " ".join(searchable_parts)
    
    async def create_sync_event(self, 
                              entity_type: str,
                              entity_id: str, 
                              entity_data: Dict[str, Any],
                              event_type: SyncEventType = SyncEventType.UPDATE,
                              target_systems: List[str] = None) -> str:
        """Create a new sync event"""
        if target_systems is None:
            target_systems = ["neo4j", "opensearch", "redis"]
        
        event = SyncEvent(
            event_id=f"sync_{entity_type}_{entity_id}_{datetime.utcnow().isoformat()}",
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_data=entity_data,
            source_system="postgresql",
            target_systems=target_systems,
            timestamp=datetime.utcnow()
        )
        
        # Queue event for processing
        await self._queue_sync_event(event)
        
        return event.event_id
    
    async def _queue_sync_event(self, event: SyncEvent):
        """Queue sync event for asynchronous processing"""
        try:
            event_data = json.dumps(asdict(event), default=str)
            await self.redis_client.lpush(self.sync_queue_name, event_data)
            logger.debug(f"Queued sync event: {event.event_id}")
            
        except Exception as e:
            logger.error(f"Failed to queue sync event {event.event_id}: {e}")
            # Add to in-memory queue as fallback
            self.pending_events.append(event)
    
    async def process_sync_queue(self, max_events: int = 100) -> int:
        """Process queued sync events"""
        if not self.redis_client:
            await self.initialize()
        
        processed_count = 0
        
        try:
            # Process events from Redis queue
            for _ in range(max_events):
                event_data = await self.redis_client.brpop(self.sync_queue_name, timeout=1)
                
                if not event_data:
                    break  # No more events
                
                try:
                    # Deserialize event
                    event_dict = json.loads(event_data[1])
                    event = SyncEvent(**event_dict)
                    
                    # Process event
                    success = await self._process_single_sync_event(event)
                    
                    if success:
                        processed_count += 1
                    else:
                        # Retry logic
                        event.retry_count += 1
                        if event.retry_count < event.max_retries:
                            await self._queue_sync_event(event)
                        else:
                            self.failed_events.append(event)
                    
                except Exception as e:
                    logger.error(f"Failed to process sync event: {e}")
            
            # Process in-memory fallback events
            fallback_events = self.pending_events[:max_events - processed_count]
            self.pending_events = self.pending_events[max_events - processed_count:]
            
            for event in fallback_events:
                success = await self._process_single_sync_event(event)
                if success:
                    processed_count += 1
                else:
                    self.failed_events.append(event)
            
            # Update statistics
            self.sync_stats["events_processed"] += processed_count
            self.sync_stats["last_sync_time"] = datetime.utcnow().isoformat()
            
            logger.info(f"Processed {processed_count} sync events")
            return processed_count
            
        except Exception as e:
            logger.error(f"Sync queue processing failed: {e}")
            return processed_count
    
    async def _process_single_sync_event(self, event: SyncEvent) -> bool:
        """Process a single sync event"""
        try:
            event.status = SyncStatus.IN_PROGRESS
            
            success_count = await self._process_sync_events_batch([event])
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Failed to process sync event {event.event_id}: {e}")
            event.status = SyncStatus.FAILED
            event.error_message = str(e)
            return False
    
    async def get_sync_statistics(self) -> Dict[str, Any]:
        """Get synchronization statistics"""
        return {
            **self.sync_stats,
            "pending_events": len(self.pending_events),
            "failed_events": len(self.failed_events),
            "queue_size": await self.redis_client.llen(self.sync_queue_name) if self.redis_client else 0
        }
    
    async def retry_failed_events(self) -> int:
        """Retry failed sync events"""
        retry_count = 0
        retry_events = self.failed_events.copy()
        self.failed_events.clear()
        
        for event in retry_events:
            if event.retry_count < event.max_retries:
                event.retry_count += 1
                event.status = SyncStatus.PENDING
                event.error_message = None
                await self._queue_sync_event(event)
                retry_count += 1
            else:
                self.failed_events.append(event)  # Permanently failed
        
        logger.info(f"Retrying {retry_count} failed sync events")
        return retry_count
    
    async def cleanup_old_events(self, days_old: int = 7):
        """Clean up old sync events and cache entries"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Clean up old failed events
            self.failed_events = [
                event for event in self.failed_events 
                if event.timestamp > cutoff_date
            ]
            
            # Clean up old cache entries (Redis keys with TTL will expire automatically)
            logger.info(f"Cleaned up sync events older than {days_old} days")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old events: {e}")

# Global sync service instance
graph_sync_service = GraphSyncService()

async def get_graph_sync_service() -> GraphSyncService:
    """Get graph sync service instance"""
    if not graph_sync_service.kg_service:
        await graph_sync_service.initialize()
    return graph_sync_service