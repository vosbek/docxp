"""
ChromaDB Vector Database Service for Semantic Search and Code Analysis
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import hashlib

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)

class VectorService:
    """
    ChromaDB-based vector database service for semantic search and code analysis.
    Provides embedding storage and retrieval for legacy migration analysis.
    """
    
    def __init__(self):
        self.client = None
        self.collections = {}
        self.embedding_function = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize ChromaDB client and embedding function"""
        try:
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=str(settings.BASE_DIR / "data" / "vector_db"),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Initialize embedding function
            # Using sentence-transformers for code embeddings
            self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="microsoft/codebert-base"  # Optimized for code understanding
            )
            
            # Initialize collections
            self._initialize_collections()
            
            logger.info("ChromaDB vector service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    def _initialize_collections(self):
        """Initialize ChromaDB collections for different data types"""
        try:
            # Code entities collection
            self.collections['code_entities'] = self.client.get_or_create_collection(
                name="code_entities",
                embedding_function=self.embedding_function,
                metadata={
                    "description": "Code entities (classes, methods, functions) with semantic embeddings",
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            
            # Business rules collection
            self.collections['business_rules'] = self.client.get_or_create_collection(
                name="business_rules",
                embedding_function=self.embedding_function,
                metadata={
                    "description": "Business rules and logic with semantic embeddings",
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            
            # Documentation collection
            self.collections['documentation'] = self.client.get_or_create_collection(
                name="documentation",
                embedding_function=self.embedding_function,
                metadata={
                    "description": "Documentation and comments with semantic embeddings",
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            
            # Migration patterns collection
            self.collections['migration_patterns'] = self.client.get_or_create_collection(
                name="migration_patterns",
                embedding_function=self.embedding_function,
                metadata={
                    "description": "Legacy to modern migration patterns and examples",
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Initialized {len(self.collections)} ChromaDB collections")
            
        except Exception as e:
            logger.error(f"Failed to initialize collections: {e}")
            raise
    
    async def add_code_entity(
        self, 
        entity_id: str,
        name: str,
        code_content: str,
        entity_type: str,
        file_path: str,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """Add code entity to vector database"""
        try:
            # Create searchable text content
            searchable_content = f"""
            Entity Name: {name}
            Type: {entity_type}
            File: {file_path}
            Code:
            {code_content}
            """
            
            # Prepare metadata
            entity_metadata = {
                "entity_id": entity_id,
                "name": name,
                "type": entity_type,
                "file_path": file_path,
                "indexed_at": datetime.utcnow().isoformat(),
                **(metadata or {})
            }
            
            # Add to collection
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.collections['code_entities'].add(
                    documents=[searchable_content],
                    metadatas=[entity_metadata],
                    ids=[entity_id]
                )
            )
            
            logger.debug(f"Added code entity {entity_id} to vector database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add code entity {entity_id}: {e}")
            return False
    
    async def add_business_rule(
        self,
        rule_id: str,
        description: str,
        plain_english: str,
        context: str,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """Add business rule to vector database"""
        try:
            # Create searchable content for business rule
            searchable_content = f"""
            Business Rule: {description}
            Plain English: {plain_english}
            Context: {context}
            """
            
            # Prepare metadata
            rule_metadata = {
                "rule_id": rule_id,
                "description": description,
                "plain_english": plain_english,
                "indexed_at": datetime.utcnow().isoformat(),
                **(metadata or {})
            }
            
            # Add to collection
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.collections['business_rules'].add(
                    documents=[searchable_content],
                    metadatas=[rule_metadata],
                    ids=[rule_id]
                )
            )
            
            logger.debug(f"Added business rule {rule_id} to vector database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add business rule {rule_id}: {e}")
            return False
    
    async def semantic_search(
        self,
        query: str,
        collection_name: str = "code_entities",
        n_results: int = 10,
        filter_metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Perform semantic search across code entities and business rules"""
        try:
            if collection_name not in self.collections:
                raise ValueError(f"Collection {collection_name} not found")
            
            collection = self.collections[collection_name]
            
            # Perform semantic search
            results = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: collection.query(
                    query_texts=[query],
                    n_results=n_results,
                    where=filter_metadata,
                    include=['documents', 'metadatas', 'distances']
                )
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    result = {
                        'id': results['ids'][0][i] if results['ids'] else None,
                        'content': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'similarity_score': 1 - results['distances'][0][i] if results['distances'] else 0,
                        'collection': collection_name
                    }
                    formatted_results.append(result)
            
            logger.debug(f"Semantic search for '{query}' returned {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []
    
    async def find_similar_code(
        self,
        code_content: str,
        entity_type: str = None,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Find similar code entities based on semantic similarity"""
        try:
            # Build filter for entity type if specified
            filter_metadata = {"type": entity_type} if entity_type else None
            
            # Search for similar code
            results = await self.semantic_search(
                query=code_content,
                collection_name="code_entities",
                n_results=n_results,
                filter_metadata=filter_metadata
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to find similar code: {e}")
            return []
    
    async def find_migration_patterns(
        self,
        legacy_pattern: str,
        technology_stack: str = None,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Find relevant migration patterns for legacy code"""
        try:
            # Build search query
            search_query = f"Legacy pattern: {legacy_pattern}"
            if technology_stack:
                search_query += f" Technology: {technology_stack}"
            
            # Build filter
            filter_metadata = {}
            if technology_stack:
                filter_metadata["source_technology"] = technology_stack
            
            # Search migration patterns
            results = await self.semantic_search(
                query=search_query,
                collection_name="migration_patterns",
                n_results=n_results,
                filter_metadata=filter_metadata if filter_metadata else None
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to find migration patterns: {e}")
            return []
    
    async def add_migration_pattern(
        self,
        pattern_id: str,
        legacy_pattern: str,
        modern_equivalent: str,
        source_technology: str,
        target_technology: str,
        complexity_score: float,
        description: str,
        example_code: str = None
    ) -> bool:
        """Add migration pattern to knowledge base"""
        try:
            # Create searchable content
            searchable_content = f"""
            Legacy Pattern: {legacy_pattern}
            Modern Equivalent: {modern_equivalent}
            Source: {source_technology}
            Target: {target_technology}
            Description: {description}
            """
            
            if example_code:
                searchable_content += f"\nExample Code:\n{example_code}"
            
            # Prepare metadata
            pattern_metadata = {
                "pattern_id": pattern_id,
                "legacy_pattern": legacy_pattern,
                "modern_equivalent": modern_equivalent,
                "source_technology": source_technology,
                "target_technology": target_technology,
                "complexity_score": complexity_score,
                "description": description,
                "indexed_at": datetime.utcnow().isoformat()
            }
            
            # Add to collection
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.collections['migration_patterns'].add(
                    documents=[searchable_content],
                    metadatas=[pattern_metadata],
                    ids=[pattern_id]
                )
            )
            
            logger.debug(f"Added migration pattern {pattern_id} to vector database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add migration pattern {pattern_id}: {e}")
            return False
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about vector database collections"""
        try:
            stats = {}
            
            for name, collection in self.collections.items():
                try:
                    count = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: collection.count()
                    )
                    stats[name] = {
                        "document_count": count,
                        "collection_metadata": collection.metadata
                    }
                except Exception as e:
                    logger.warning(f"Failed to get stats for collection {name}: {e}")
                    stats[name] = {"error": str(e)}
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {}
    
    async def bulk_add_entities(
        self,
        entities: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Bulk add multiple entities to improve performance"""
        try:
            results = {"success": 0, "failed": 0}
            
            # Group entities by collection type
            entity_groups = {
                "code_entities": [],
                "business_rules": [],
                "documentation": []
            }
            
            for entity in entities:
                entity_type = entity.get("collection_type", "code_entities")
                if entity_type in entity_groups:
                    entity_groups[entity_type].append(entity)
            
            # Process each group
            for collection_name, group_entities in entity_groups.items():
                if not group_entities:
                    continue
                
                try:
                    # Prepare batch data
                    documents = []
                    metadatas = []
                    ids = []
                    
                    for entity in group_entities:
                        documents.append(entity["content"])
                        metadatas.append(entity["metadata"])
                        ids.append(entity["id"])
                    
                    # Bulk add to collection
                    await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: self.collections[collection_name].add(
                            documents=documents,
                            metadatas=metadatas,
                            ids=ids
                        )
                    )
                    
                    results["success"] += len(group_entities)
                    logger.info(f"Bulk added {len(group_entities)} entities to {collection_name}")
                    
                except Exception as e:
                    logger.error(f"Bulk add failed for {collection_name}: {e}")
                    results["failed"] += len(group_entities)
            
            return results
            
        except Exception as e:
            logger.error(f"Bulk add entities failed: {e}")
            return {"success": 0, "failed": len(entities)}
    
    async def clear_collection(self, collection_name: str) -> bool:
        """Clear all documents from a collection"""
        try:
            if collection_name not in self.collections:
                raise ValueError(f"Collection {collection_name} not found")
            
            # Delete the collection and recreate it
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.delete_collection(collection_name)
            )
            
            # Recreate the collection
            self.collections[collection_name] = self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            
            logger.info(f"Cleared collection {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear collection {collection_name}: {e}")
            return False

# Global vector service instance
vector_service = VectorService()

async def get_vector_service() -> VectorService:
    """Get vector service instance"""
    return vector_service