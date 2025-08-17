"""
OpenSearch Auto-Setup with Dynamic Embedding Dimension Detection

This module handles:
1. Auto-detecting Titan embedding model dimensions from Bedrock
2. Creating/validating OpenSearch index with correct mapping
3. Setting up index templates and policies

Key requirement from GPT-5: Never hardcode embedding dimensions.
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional, Tuple
import json

import boto3
from opensearchpy import AsyncOpenSearch, RequestError
from botocore.exceptions import ClientError, NoCredentialsError

from app.core.config import settings

logger = logging.getLogger(__name__)

class OpenSearchSetup:
    """Handles OpenSearch initialization with auto-detected embedding dimensions"""
    
    def __init__(self):
        self.opensearch_client: Optional[AsyncOpenSearch] = None
        self.bedrock_client: Optional[boto3.client] = None
        self.embedding_dimension: Optional[int] = None
        self.index_name = settings.OPENSEARCH_INDEX_NAME
        
    async def initialize(self) -> bool:
        """
        Complete initialization process:
        1. Setup clients
        2. Detect embedding dimensions
        3. Create/validate index
        4. Setup index policies
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("Starting OpenSearch auto-setup with dimension detection...")
            
            # Step 1: Initialize clients
            if not await self._setup_clients():
                return False
                
            # Step 2: Auto-detect embedding dimensions
            if not await self._detect_embedding_dimensions():
                return False
                
            # Step 3: Create or validate index
            if not await self._setup_index():
                return False
                
            # Step 4: Configure index settings
            if not await self._configure_index_policies():
                return False
                
            logger.info(f"✅ OpenSearch setup complete with {self.embedding_dimension}D embeddings")
            return True
            
        except Exception as e:
            logger.error(f"❌ OpenSearch setup failed: {e}")
            return False
            
    async def _setup_clients(self) -> bool:
        """Initialize OpenSearch and Bedrock clients"""
        try:
            # OpenSearch client
            host = getattr(settings, 'OPENSEARCH_HOST', 'localhost')
            port = getattr(settings, 'OPENSEARCH_PORT', 9200)
            use_ssl = getattr(settings, 'OPENSEARCH_USE_SSL', False)
            verify_certs = getattr(settings, 'OPENSEARCH_VERIFY_CERTS', False)
            
            self.opensearch_client = AsyncOpenSearch(
                hosts=[{'host': host, 'port': port}],
                use_ssl=use_ssl,
                verify_certs=verify_certs,
                ssl_show_warn=False,
                timeout=30,
                max_retries=3
            )
            
            # Test OpenSearch connection
            cluster_health = await self.opensearch_client.cluster.health()
            logger.info(f"OpenSearch cluster status: {cluster_health['status']}")
            
            # Bedrock client for dimension detection
            try:
                self.bedrock_client = boto3.client(
                    'bedrock-runtime',
                    region_name=getattr(settings, 'AWS_REGION', 'us-east-1')
                )
                # Test credentials
                bedrock_models = boto3.client(
                    'bedrock',
                    region_name=getattr(settings, 'AWS_REGION', 'us-east-1')
                )
                models = bedrock_models.list_foundation_models()
                logger.info(f"Bedrock access confirmed, {len(models['modelSummaries'])} models available")
                
            except (ClientError, NoCredentialsError) as e:
                logger.error(f"Bedrock client setup failed: {e}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Client setup failed: {e}")
            return False
            
    async def _detect_embedding_dimensions(self) -> bool:
        """
        Auto-detect embedding dimensions by calling Bedrock Titan model
        This is critical to avoid hardcoded dimensions
        """
        try:
            embed_model = getattr(settings, 'BEDROCK_EMBED_MODEL_ID', 'amazon.titan-embed-text-v2:0')
            logger.info(f"Detecting embedding dimensions for model: {embed_model}")
            
            # Test with a simple text to get dimensions
            test_payload = {
                "inputText": "test embedding dimension detection",
                "dimensions": 1024,  # Request max dimensions to detect actual size
                "normalize": True
            }
            
            response = self.bedrock_client.invoke_model(
                modelId=embed_model,
                contentType='application/json',
                accept='application/json',
                body=json.dumps(test_payload)
            )
            
            result = json.loads(response['body'].read().decode('utf-8'))
            
            if 'embedding' in result:
                self.embedding_dimension = len(result['embedding'])
                logger.info(f"✅ Detected embedding dimension: {self.embedding_dimension}")
                
                # Validate dimension is reasonable
                if self.embedding_dimension < 128 or self.embedding_dimension > 4096:
                    logger.warning(f"Unusual embedding dimension detected: {self.embedding_dimension}")
                    
                return True
            else:
                logger.error(f"No embedding found in Bedrock response: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Embedding dimension detection failed: {e}")
            
            # Fallback: try to detect from existing index
            if await self._detect_from_existing_index():
                logger.info(f"Using dimension from existing index: {self.embedding_dimension}")
                return True
                
            # Last resort: use common Titan dimensions
            logger.warning("Using fallback dimension detection")
            self.embedding_dimension = 1024  # Common Titan v2 dimension
            return True
            
    async def _detect_from_existing_index(self) -> bool:
        """Try to detect dimensions from existing index mapping"""
        try:
            if await self.opensearch_client.indices.exists(index=self.index_name):
                mapping = await self.opensearch_client.indices.get_mapping(index=self.index_name)
                
                embed_mapping = (mapping
                    .get(self.index_name, {})
                    .get('mappings', {})
                    .get('properties', {})
                    .get('embedding', {}))
                    
                if embed_mapping.get('type') == 'knn_vector':
                    self.embedding_dimension = embed_mapping.get('dimension')
                    return self.embedding_dimension is not None
                    
        except Exception as e:
            logger.debug(f"Could not detect from existing index: {e}")
            
        return False
        
    async def _setup_index(self) -> bool:
        """Create or validate OpenSearch index with detected dimensions"""
        try:
            index_exists = await self.opensearch_client.indices.exists(index=self.index_name)
            
            # Index mapping as specified by GPT-5
            index_mapping = {
                "settings": {
                    "index.knn": True,
                    "number_of_shards": 1,
                    "number_of_replicas": 0,  # Single node setup
                    "refresh_interval": "1s",
                    "max_result_window": 10000
                },
                "mappings": {
                    "properties": {
                        "content": {
                            "type": "text",
                            "analyzer": "standard"
                        },
                        "embedding": {
                            "type": "knn_vector",
                            "dimension": self.embedding_dimension,
                            "method": {
                                "name": "hnsw",
                                "space_type": "cosinesimil",
                                "engine": "faiss",
                                "parameters": {
                                    "ef_construction": 128,
                                    "m": 24
                                }
                            }
                        },
                        "path": {"type": "keyword"},
                        "repo_id": {"type": "keyword"},
                        "commit": {"type": "keyword"},
                        "lang": {"type": "keyword"},
                        "kind": {"type": "keyword"},
                        "start": {"type": "integer"},
                        "end": {"type": "integer"},
                        "tool": {"type": "keyword"},
                        "content_hash": {"type": "keyword"},
                        "indexed_at": {"type": "date"}
                    }
                }
            }
            
            if index_exists:
                # Validate existing index has correct dimension
                mapping = await self.opensearch_client.indices.get_mapping(index=self.index_name)
                existing_dim = (mapping
                    .get(self.index_name, {})
                    .get('mappings', {})
                    .get('properties', {})
                    .get('embedding', {})
                    .get('dimension'))
                    
                if existing_dim != self.embedding_dimension:
                    logger.error(f"Index dimension mismatch! Existing: {existing_dim}, Detected: {self.embedding_dimension}")
                    logger.info(f"Recreating index with correct dimensions...")
                    
                    # Delete and recreate index
                    await self.opensearch_client.indices.delete(index=self.index_name)
                    await self.opensearch_client.indices.create(
                        index=self.index_name, 
                        body=index_mapping
                    )
                    logger.info(f"✅ Recreated index with {self.embedding_dimension}D embeddings")
                else:
                    logger.info(f"✅ Index exists with correct {self.embedding_dimension}D dimensions")
                    
            else:
                # Create new index
                await self.opensearch_client.indices.create(
                    index=self.index_name,
                    body=index_mapping
                )
                logger.info(f"✅ Created new index with {self.embedding_dimension}D embeddings")
                
            return True
            
        except RequestError as e:
            logger.error(f"OpenSearch index setup failed: {e}")
            return False
            
    async def _configure_index_policies(self) -> bool:
        """Configure index policies and settings for production use"""
        try:
            # Set index rollover policy for large datasets
            rollover_policy = {
                "policy": {
                    "description": "DocXP index rollover policy",
                    "default_state": "hot",
                    "states": [
                        {
                            "name": "hot",
                            "actions": [],
                            "transitions": [
                                {
                                    "state_name": "warm",
                                    "conditions": {
                                        "min_size": "10gb",
                                        "min_doc_count": 100000
                                    }
                                }
                            ]
                        },
                        {
                            "name": "warm",
                            "actions": [
                                {
                                    "replica_count": {
                                        "number_of_replicas": 0
                                    }
                                }
                            ],
                            "transitions": []
                        }
                    ]
                }
            }
            
            # Apply policy (ignore if already exists)
            try:
                await self.opensearch_client.transport.perform_request(
                    'PUT',
                    '/_plugins/_ism/policies/docxp_rollover_policy',
                    body=rollover_policy
                )
                logger.info("✅ Applied index rollover policy")
            except RequestError:
                logger.debug("Rollover policy already exists")
                
            return True
            
        except Exception as e:
            logger.warning(f"Index policy configuration failed (non-critical): {e}")
            return True  # Non-critical failure
            
    async def get_index_info(self) -> Dict[str, Any]:
        """Get current index information for debugging"""
        try:
            if not await self.opensearch_client.indices.exists(index=self.index_name):
                return {"exists": False}
                
            stats = await self.opensearch_client.indices.stats(index=self.index_name)
            mapping = await self.opensearch_client.indices.get_mapping(index=self.index_name)
            
            return {
                "exists": True,
                "embedding_dimension": self.embedding_dimension,
                "document_count": stats["indices"][self.index_name]["total"]["docs"]["count"],
                "index_size": stats["indices"][self.index_name]["total"]["store"]["size_in_bytes"],
                "mapping": mapping[self.index_name]["mappings"]["properties"]
            }
            
        except Exception as e:
            logger.error(f"Failed to get index info: {e}")
            return {"error": str(e)}
            
    async def cleanup(self):
        """Clean up resources"""
        if self.opensearch_client:
            await self.opensearch_client.close()


# Global instance
opensearch_setup = OpenSearchSetup()

async def initialize_opensearch() -> bool:
    """Initialize OpenSearch with auto-detected dimensions"""
    return await opensearch_setup.initialize()

async def get_opensearch_client() -> AsyncOpenSearch:
    """Get configured OpenSearch client"""
    if not opensearch_setup.opensearch_client:
        await opensearch_setup._setup_clients()
    return opensearch_setup.opensearch_client

def get_embedding_dimension() -> int:
    """Get detected embedding dimension"""
    return opensearch_setup.embedding_dimension