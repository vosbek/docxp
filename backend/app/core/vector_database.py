"""
Enterprise Vector Database Abstraction Layer
Supports ChromaDB and PostgreSQL pgvector backends
"""

import asyncio
import logging
import hashlib
import json
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from enum import Enum

import numpy as np
from sqlalchemy import Column, String, DateTime, Text, Integer, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, and_, text
import asyncpg

# Vector extension import (requires pgvector)
try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False
    Vector = None

from app.core.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

class VectorDatabaseType(str, Enum):
    CHROMADB = "chromadb"
    POSTGRESQL_PGVECTOR = "postgresql_pgvector"


class DocumentEmbedding(Base):
    """PostgreSQL table for storing document embeddings with pgvector"""
    __tablename__ = "document_embeddings"
    
    id = Column(String, primary_key=True)
    content_hash = Column(String(64), unique=True, index=True)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1024), nullable=False) if PGVECTOR_AVAILABLE else Column(Text)  # Fallback to JSON
    metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_accessed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    access_count = Column(Integer, default=1)
    
    # Add vector similarity search indexes
    # Note: These are created manually via SQL due to SQLAlchemy limitations


class VectorDatabaseInterface(ABC):
    """Abstract interface for vector database operations"""
    
    @abstractmethod
    async def add_embedding(self, id: str, content: str, embedding: List[float], metadata: Dict[str, Any] = None) -> bool:
        """Add a document embedding to the vector database"""
        pass
    
    @abstractmethod
    async def search_similar(self, query_embedding: List[float], limit: int = 10, metadata_filter: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search for similar embeddings"""
        pass
    
    @abstractmethod
    async def get_embedding(self, id: str) -> Optional[Dict[str, Any]]:
        """Get a specific embedding by ID"""
        pass
    
    @abstractmethod
    async def delete_embedding(self, id: str) -> bool:
        """Delete an embedding by ID"""
        pass
    
    @abstractmethod
    async def update_embedding(self, id: str, content: str, embedding: List[float], metadata: Dict[str, Any] = None) -> bool:
        """Update an existing embedding"""
        pass
    
    @abstractmethod
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        pass


class PostgreSQLVectorDatabase(VectorDatabaseInterface):
    """PostgreSQL with pgvector extension implementation"""
    
    def __init__(self):
        if not PGVECTOR_AVAILABLE:
            raise ImportError("pgvector not available. Install with: pip install pgvector")
        
        self.engine = None
        self.session_factory = None
        self._initialized = False
    
    async def _initialize(self):
        """Initialize PostgreSQL connection and create tables"""
        if self._initialized:
            return
        
        if not settings.POSTGRESQL_VECTOR_URL:
            raise ValueError("POSTGRESQL_VECTOR_URL not configured")
        
        # Create async engine
        self.engine = create_async_engine(
            settings.POSTGRESQL_VECTOR_URL,
            echo=settings.DEBUG,
            pool_size=10,
            max_overflow=20
        )
        
        # Create session factory
        self.session_factory = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        
        # Create tables and vector extension
        await self._create_tables_and_indexes()
        self._initialized = True
        logger.info("PostgreSQL vector database initialized")
    
    async def _create_tables_and_indexes(self):
        """Create tables and vector indexes"""
        async with self.engine.begin() as conn:
            # Create vector extension
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            
            # Create tables
            await conn.run_sync(Base.metadata.create_all)
            
            # Create vector indexes for similarity search
            try:
                # HNSW index for high performance (requires sufficient data)
                await conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_embedding_hnsw 
                    ON document_embeddings USING hnsw (embedding vector_cosine_ops)
                    WITH (m = 16, ef_construction = 64)
                """))
            except Exception as e:
                logger.warning(f"Could not create HNSW index (needs more data): {e}")
                # Fallback to IVFFlat index
                await conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_embedding_ivfflat 
                    ON document_embeddings USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100)
                """))
            
            # Create metadata index for filtering
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_embedding_metadata 
                ON document_embeddings USING gin (metadata)
            """))
    
    async def add_embedding(self, id: str, content: str, embedding: List[float], metadata: Dict[str, Any] = None) -> bool:
        """Add a document embedding to PostgreSQL"""
        await self._initialize()
        
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        
        async with self.session_factory() as session:
            try:
                # Check if embedding already exists
                existing = await session.execute(
                    select(DocumentEmbedding).where(DocumentEmbedding.id == id)
                )
                if existing.scalar_one_or_none():
                    return await self.update_embedding(id, content, embedding, metadata)
                
                # Create new embedding
                doc_embedding = DocumentEmbedding(
                    id=id,
                    content_hash=content_hash,
                    content=content,
                    embedding=embedding,
                    metadata=metadata or {},
                    created_at=datetime.utcnow(),
                    last_accessed_at=datetime.utcnow(),
                    access_count=1
                )
                
                session.add(doc_embedding)
                await session.commit()
                return True
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Error adding embedding {id}: {e}")
                return False
    
    async def search_similar(self, query_embedding: List[float], limit: int = 10, metadata_filter: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search for similar embeddings using vector similarity"""
        await self._initialize()
        
        async with self.session_factory() as session:
            try:
                # Build similarity query
                query = select(
                    DocumentEmbedding.id,
                    DocumentEmbedding.content,
                    DocumentEmbedding.metadata,
                    DocumentEmbedding.created_at,
                    (DocumentEmbedding.embedding.cosine_distance(query_embedding)).label('distance')
                )
                
                # Add metadata filter if provided
                if metadata_filter:
                    for key, value in metadata_filter.items():
                        query = query.where(DocumentEmbedding.metadata[key].astext == str(value))
                
                # Order by similarity and limit results
                query = query.order_by('distance').limit(limit)
                
                result = await session.execute(query)
                rows = result.fetchall()
                
                # Format results
                results = []
                for row in rows:
                    results.append({
                        'id': row.id,
                        'content': row.content,
                        'metadata': row.metadata or {},
                        'similarity': 1.0 - row.distance,  # Convert distance to similarity
                        'created_at': row.created_at.isoformat()
                    })
                
                return results
                
            except Exception as e:
                logger.error(f"Error searching embeddings: {e}")
                return []
    
    async def get_embedding(self, id: str) -> Optional[Dict[str, Any]]:
        """Get a specific embedding by ID"""
        await self._initialize()
        
        async with self.session_factory() as session:
            try:
                result = await session.execute(
                    select(DocumentEmbedding).where(DocumentEmbedding.id == id)
                )
                doc = result.scalar_one_or_none()
                
                if not doc:
                    return None
                
                # Update access tracking
                doc.last_accessed_at = datetime.utcnow()
                doc.access_count += 1
                await session.commit()
                
                return {
                    'id': doc.id,
                    'content': doc.content,
                    'embedding': doc.embedding,
                    'metadata': doc.metadata or {},
                    'created_at': doc.created_at.isoformat(),
                    'access_count': doc.access_count
                }
                
            except Exception as e:
                logger.error(f"Error getting embedding {id}: {e}")
                return None
    
    async def delete_embedding(self, id: str) -> bool:
        """Delete an embedding by ID"""
        await self._initialize()
        
        async with self.session_factory() as session:
            try:
                result = await session.execute(
                    select(DocumentEmbedding).where(DocumentEmbedding.id == id)
                )
                doc = result.scalar_one_or_none()
                
                if not doc:
                    return False
                
                await session.delete(doc)
                await session.commit()
                return True
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Error deleting embedding {id}: {e}")
                return False
    
    async def update_embedding(self, id: str, content: str, embedding: List[float], metadata: Dict[str, Any] = None) -> bool:
        """Update an existing embedding"""
        await self._initialize()
        
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        
        async with self.session_factory() as session:
            try:
                result = await session.execute(
                    select(DocumentEmbedding).where(DocumentEmbedding.id == id)
                )
                doc = result.scalar_one_or_none()
                
                if not doc:
                    return await self.add_embedding(id, content, embedding, metadata)
                
                # Update fields
                doc.content_hash = content_hash
                doc.content = content
                doc.embedding = embedding
                doc.metadata = metadata or {}
                doc.last_accessed_at = datetime.utcnow()
                doc.access_count += 1
                
                await session.commit()
                return True
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Error updating embedding {id}: {e}")
                return False
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get PostgreSQL vector database statistics"""
        await self._initialize()
        
        async with self.session_factory() as session:
            try:
                # Count total documents
                total_docs = await session.execute(
                    text("SELECT COUNT(*) FROM document_embeddings")
                )
                total_count = total_docs.scalar()
                
                # Get database size
                db_size = await session.execute(
                    text("SELECT pg_size_pretty(pg_database_size(current_database()))")
                )
                database_size = db_size.scalar()
                
                # Get table size
                table_size = await session.execute(
                    text("SELECT pg_size_pretty(pg_total_relation_size('document_embeddings'))")
                )
                embeddings_table_size = table_size.scalar()
                
                return {
                    'database_type': 'PostgreSQL pgvector',
                    'total_documents': total_count,
                    'database_size': database_size,
                    'embeddings_table_size': embeddings_table_size,
                    'vector_dimensions': settings.BEDROCK_EMBEDDING_DIMENSIONS,
                    'pgvector_available': PGVECTOR_AVAILABLE
                }
                
            except Exception as e:
                logger.error(f"Error getting database stats: {e}")
                return {
                    'database_type': 'PostgreSQL pgvector',
                    'error': str(e)
                }


class ChromaDBVectorDatabase(VectorDatabaseInterface):
    """ChromaDB implementation (existing functionality)"""
    
    def __init__(self):
        # Import here to avoid dependency issues
        import chromadb
        from chromadb.utils import embedding_functions
        
        self.client = chromadb.PersistentClient(
            path=str(settings.BASE_DIR / "data" / "vector_db")
        )
        
        # Use sentence transformers for embeddings
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.EMBEDDING_MODEL
        )
        
        self.collection = self.client.get_or_create_collection(
            name="code_entities",
            embedding_function=self.embedding_function
        )
    
    async def add_embedding(self, id: str, content: str, embedding: List[float], metadata: Dict[str, Any] = None) -> bool:
        """Add embedding to ChromaDB"""
        try:
            self.collection.upsert(
                ids=[id],
                documents=[content],
                embeddings=[embedding],
                metadatas=[metadata or {}]
            )
            return True
        except Exception as e:
            logger.error(f"Error adding to ChromaDB: {e}")
            return False
    
    async def search_similar(self, query_embedding: List[float], limit: int = 10, metadata_filter: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search ChromaDB for similar embeddings"""
        try:
            where_clause = metadata_filter if metadata_filter else None
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_clause
            )
            
            # Format results
            formatted_results = []
            if results['ids']:
                for i, doc_id in enumerate(results['ids'][0]):
                    formatted_results.append({
                        'id': doc_id,
                        'content': results['documents'][0][i] if results['documents'] else '',
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'similarity': 1.0 - results['distances'][0][i] if results['distances'] else 0.0
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching ChromaDB: {e}")
            return []
    
    async def get_embedding(self, id: str) -> Optional[Dict[str, Any]]:
        """Get embedding from ChromaDB"""
        try:
            result = self.collection.get(ids=[id], include=['documents', 'metadatas', 'embeddings'])
            if result['ids']:
                return {
                    'id': result['ids'][0],
                    'content': result['documents'][0] if result['documents'] else '',
                    'metadata': result['metadatas'][0] if result['metadatas'] else {},
                    'embedding': result['embeddings'][0] if result['embeddings'] else []
                }
            return None
        except Exception as e:
            logger.error(f"Error getting from ChromaDB: {e}")
            return None
    
    async def delete_embedding(self, id: str) -> bool:
        """Delete from ChromaDB"""
        try:
            self.collection.delete(ids=[id])
            return True
        except Exception as e:
            logger.error(f"Error deleting from ChromaDB: {e}")
            return False
    
    async def update_embedding(self, id: str, content: str, embedding: List[float], metadata: Dict[str, Any] = None) -> bool:
        """Update ChromaDB embedding"""
        return await self.add_embedding(id, content, embedding, metadata)
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get ChromaDB statistics"""
        try:
            count = self.collection.count()
            return {
                'database_type': 'ChromaDB',
                'total_documents': count,
                'collection_name': self.collection.name,
                'embedding_model': settings.EMBEDDING_MODEL
            }
        except Exception as e:
            logger.error(f"Error getting ChromaDB stats: {e}")
            return {'database_type': 'ChromaDB', 'error': str(e)}


class VectorDatabaseFactory:
    """Factory for creating vector database instances"""
    
    @staticmethod
    def create_database(db_type: VectorDatabaseType = None) -> VectorDatabaseInterface:
        """Create a vector database instance based on configuration"""
        if db_type is None:
            db_type = VectorDatabaseType(settings.VECTOR_DB_TYPE)
        
        if db_type == VectorDatabaseType.POSTGRESQL_PGVECTOR:
            if not PGVECTOR_AVAILABLE:
                logger.warning("pgvector not available, falling back to ChromaDB")
                return ChromaDBVectorDatabase()
            return PostgreSQLVectorDatabase()
        elif db_type == VectorDatabaseType.CHROMADB:
            return ChromaDBVectorDatabase()
        else:
            raise ValueError(f"Unsupported vector database type: {db_type}")


# Global instance
_vector_db_instance = None

def get_vector_database() -> VectorDatabaseInterface:
    """Get the configured vector database instance"""
    global _vector_db_instance
    if _vector_db_instance is None:
        _vector_db_instance = VectorDatabaseFactory.create_database()
    return _vector_db_instance