"""
Bulk OpenSearch Service - Idempotent Bulk Operations with Retry Logic

Implements the expert recommendations:
- OpenSearch _id = sha256(repo_id + commit + path + start + end + content_hash)
- Bulk API batches: 5-15MB per batch
- Exponential backoff with partial-fail retry
- Circuit breaker for persistent failures
"""

import asyncio
import logging
import json
import hashlib
import time
import math
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime
from itertools import chain

from opensearchpy import OpenSearch
from opensearchpy.exceptions import OpenSearchException, ConnectionError, RequestError
from prometheus_client import Counter, Histogram, Gauge

from app.core.opensearch_setup import get_opensearch_client, is_opensearch_available
from app.core.config import settings

logger = logging.getLogger(__name__)

# Prometheus metrics
BULK_OPERATIONS = Counter('docxp_opensearch_bulk_operations_total', 'Total bulk operations', ['status'])
BULK_LATENCY = Histogram('docxp_opensearch_bulk_duration_seconds', 'Bulk operation duration')
BULK_BATCH_SIZE = Histogram('docxp_opensearch_bulk_batch_size_mb', 'Bulk batch size in MB')
CIRCUIT_BREAKER_STATE = Gauge('docxp_opensearch_circuit_breaker_open', 'Circuit breaker state (1=open, 0=closed)')

class CircuitBreakerState:
    """Simple circuit breaker for OpenSearch operations"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.is_open = False
    
    def record_success(self):
        """Record successful operation"""
        self.failure_count = 0
        self.is_open = False
        CIRCUIT_BREAKER_STATE.set(0)
    
    def record_failure(self):
        """Record failed operation"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.is_open = True
            CIRCUIT_BREAKER_STATE.set(1)
            logger.warning(f"🔴 OpenSearch circuit breaker OPEN after {self.failure_count} failures")
    
    def can_execute(self) -> bool:
        """Check if operation can be executed"""
        if not self.is_open:
            return True
        
        # Check if recovery timeout has passed
        if time.time() - self.last_failure_time > self.recovery_timeout:
            self.is_open = False
            self.failure_count = 0
            CIRCUIT_BREAKER_STATE.set(0)
            logger.info("🟢 OpenSearch circuit breaker CLOSED - attempting recovery")
            return True
        
        return False

class BulkOpenSearchService:
    """
    Enterprise-grade bulk OpenSearch operations with fault tolerance
    """
    
    def __init__(self):
        self.client = get_opensearch_client()
        self.circuit_breaker = CircuitBreakerState()
        
        # Configuration
        self.max_batch_size_mb = getattr(settings, 'OPENSEARCH_MAX_BATCH_SIZE_MB', 15)
        self.min_batch_size_mb = getattr(settings, 'OPENSEARCH_MIN_BATCH_SIZE_MB', 5)
        self.max_retries = getattr(settings, 'OPENSEARCH_MAX_RETRIES', 5)
        self.base_delay = getattr(settings, 'OPENSEARCH_BASE_DELAY_SECONDS', 1)
        
        # Index configuration
        self.default_index = getattr(settings, 'OPENSEARCH_DEFAULT_INDEX', 'docxp_entities')
        
        logger.info("✅ BulkOpenSearchService initialized with circuit breaker protection")
    
    def generate_document_id(self, repo_id: str, commit: str, path: str, 
                           start_line: int, end_line: int, content_hash: str) -> str:
        """
        Generate idempotent document ID as recommended
        
        Format: sha256(repo_id + commit + path + start + end + content_hash)
        """
        id_string = f"{repo_id}|{commit}|{path}|{start_line}|{end_line}|{content_hash}"
        return hashlib.sha256(id_string.encode('utf-8')).hexdigest()
    
    async def bulk_index_entities(self, job_id: str, entities: List[Dict[str, Any]], 
                                 index_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Bulk index entities with intelligent batching and retry logic
        """
        if not entities:
            return {"success": True, "indexed": 0, "failed": 0, "batches": 0}
        
        index_name = index_name or self.default_index
        
        logger.info(f"📚 Starting bulk index for {len(entities)} entities in job {job_id}")
        
        try:
            # Check circuit breaker
            if not self.circuit_breaker.can_execute():
                raise RuntimeError("OpenSearch circuit breaker is OPEN - skipping bulk operation")
            
            # Prepare documents with idempotent IDs
            documents = self._prepare_documents(entities, index_name)
            
            # Split into batches by size
            batches = self._create_batches(documents)
            
            # Process batches with retry logic
            total_indexed = 0
            total_failed = 0
            
            for batch_num, batch in enumerate(batches):
                logger.debug(f"📦 Processing batch {batch_num + 1}/{len(batches)} ({len(batch)} docs)")
                
                result = await self._process_batch_with_retry(batch, index_name)
                total_indexed += result['indexed']
                total_failed += result['failed']
                
                # Small delay between batches to be nice to OpenSearch
                if batch_num < len(batches) - 1:
                    await asyncio.sleep(0.1)
            
            self.circuit_breaker.record_success()
            BULK_OPERATIONS.labels(status='success').inc()
            
            logger.info(f"✅ Bulk index complete for job {job_id}: {total_indexed} indexed, {total_failed} failed")
            
            return {
                "success": True,
                "indexed": total_indexed,
                "failed": total_failed,
                "batches": len(batches),
                "job_id": job_id
            }
            
        except Exception as e:
            self.circuit_breaker.record_failure()
            BULK_OPERATIONS.labels(status='failed').inc()
            logger.error(f"❌ Bulk index failed for job {job_id}: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "indexed": 0,
                "failed": len(entities),
                "job_id": job_id
            }
    
    def _prepare_documents(self, entities: List[Dict[str, Any]], index_name: str) -> List[Dict[str, Any]]:
        """
        Prepare documents for bulk indexing with idempotent IDs
        """
        documents = []
        
        for entity in entities:
            # Generate idempotent ID
            doc_id = self.generate_document_id(
                repo_id=entity.get('repository_path', ''),
                commit=entity.get('commit_hash', ''),
                path=entity.get('file_path', ''),
                start_line=entity.get('start_line', 0),
                end_line=entity.get('end_line', 0),
                content_hash=entity.get('content_hash', '')
            )
            
            # Prepare document for indexing
            doc = {
                "_id": doc_id,
                "_index": index_name,
                "_source": {
                    "entity_id": entity.get('entity_id'),
                    "name": entity.get('name'),
                    "entity_type": entity.get('entity_type'),
                    "file_path": entity.get('file_path'),
                    "repository_path": entity.get('repository_path'),
                    "start_line": entity.get('start_line'),
                    "end_line": entity.get('end_line'),
                    "content": entity.get('content'),
                    "content_hash": entity.get('content_hash'),
                    "embedding": entity.get('embedding'),
                    "keywords": entity.get('keywords', []),
                    "entity_metadata": entity.get('entity_metadata', {}),
                    "quality_score": entity.get('quality_score', 0.0),
                    "relevance_score": entity.get('relevance_score', 0.0),
                    "business_rule_indicator": entity.get('business_rule_indicator', False),
                    "commit_hash": entity.get('commit_hash'),
                    "language": entity.get('language'),
                    "framework": entity.get('framework'),
                    "indexed_at": datetime.utcnow().isoformat(),
                    "indexed_by_job": entity.get('indexed_by_job')
                }
            }
            
            documents.append(doc)
        
        return documents
    
    def _create_batches(self, documents: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        Create batches based on size limits (5-15MB per batch)
        """
        batches = []
        current_batch = []
        current_size_bytes = 0
        
        max_size_bytes = self.max_batch_size_mb * 1024 * 1024
        
        for doc in documents:
            # Estimate document size (JSON serialization + metadata)
            doc_size = len(json.dumps(doc).encode('utf-8'))
            
            # Check if adding this doc would exceed batch size
            if current_batch and (current_size_bytes + doc_size) > max_size_bytes:
                # Finalize current batch
                batches.append(current_batch)
                current_batch = [doc]
                current_size_bytes = doc_size
            else:
                # Add to current batch
                current_batch.append(doc)
                current_size_bytes += doc_size
        
        # Add final batch if not empty
        if current_batch:
            batches.append(current_batch)
        
        logger.debug(f"📦 Created {len(batches)} batches from {len(documents)} documents")
        return batches
    
    async def _process_batch_with_retry(self, batch: List[Dict[str, Any]], 
                                      index_name: str) -> Dict[str, int]:
        """
        Process a single batch with exponential backoff retry
        """
        retry_count = 0
        current_batch = batch.copy()
        
        while retry_count < self.max_retries and current_batch:
            try:
                with BULK_LATENCY.time():
                    # Record batch size metrics
                    batch_size_mb = self._calculate_batch_size_mb(current_batch)
                    BULK_BATCH_SIZE.observe(batch_size_mb)
                    
                    # Execute bulk operation
                    response = await self._execute_bulk_operation(current_batch)
                    
                    # Process response and extract failed items
                    failed_items = self._extract_failed_items(response, current_batch)
                    successful_count = len(current_batch) - len(failed_items)
                    
                    if not failed_items:
                        # All successful
                        return {"indexed": successful_count, "failed": 0}
                    
                    # Some failures - prepare for retry
                    logger.warning(f"⚠️  Batch partial failure: {len(failed_items)}/{len(current_batch)} failed, retrying...")
                    current_batch = failed_items
                    retry_count += 1
                    
                    # Exponential backoff
                    delay = min(self.base_delay * (2 ** retry_count), 30)
                    await asyncio.sleep(delay)
                    
                    # Return partial success
                    if retry_count >= self.max_retries:
                        return {"indexed": successful_count, "failed": len(failed_items)}
                
            except Exception as e:
                retry_count += 1
                logger.error(f"❌ Batch execution failed (attempt {retry_count}): {e}")
                
                if retry_count >= self.max_retries:
                    return {"indexed": 0, "failed": len(current_batch)}
                
                # Exponential backoff
                delay = min(self.base_delay * (2 ** retry_count), 30)
                await asyncio.sleep(delay)
        
        return {"indexed": 0, "failed": len(batch)}
    
    async def _execute_bulk_operation(self, batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute the actual bulk operation against OpenSearch
        """
        # Convert to OpenSearch bulk format
        bulk_body = []
        for doc in batch:
            # Index action
            bulk_body.append({
                "index": {
                    "_index": doc["_index"],
                    "_id": doc["_id"]
                }
            })
            # Document source
            bulk_body.append(doc["_source"])
        
        # Execute bulk request
        response = self.client.bulk(
            body=bulk_body,
            refresh=False,  # Don't refresh immediately for performance
            timeout='60s'
        )
        
        return response
    
    def _extract_failed_items(self, response: Dict[str, Any], 
                            original_batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract failed items from bulk response for retry
        """
        if not response.get("errors"):
            return []
        
        failed_items = []
        items = response.get("items", [])
        
        for i, item in enumerate(items):
            if "index" in item and item["index"].get("error"):
                error = item["index"]["error"]
                doc_id = item["index"]["_id"]
                
                # Log the specific error
                logger.warning(f"⚠️  Document {doc_id} failed: {error.get('type', 'unknown')} - {error.get('reason', 'no reason')}")
                
                # Check if this is a retryable error
                error_type = error.get("type", "").lower()
                if self._is_retryable_error(error_type):
                    if i < len(original_batch):
                        failed_items.append(original_batch[i])
                else:
                    logger.error(f"❌ Non-retryable error for document {doc_id}: {error}")
        
        return failed_items
    
    def _is_retryable_error(self, error_type: str) -> bool:
        """
        Determine if an error type is retryable
        """
        retryable_errors = {
            "cluster_block_exception",
            "es_rejected_execution_exception", 
            "timeout_exception",
            "too_many_requests_exception",
            "service_unavailable_exception"
        }
        
        return error_type in retryable_errors
    
    def _calculate_batch_size_mb(self, batch: List[Dict[str, Any]]) -> float:
        """
        Calculate batch size in MB for metrics
        """
        total_bytes = sum(
            len(json.dumps(doc).encode('utf-8'))
            for doc in batch
        )
        return total_bytes / (1024 * 1024)
    
    async def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of the bulk indexing service
        """
        try:
            # Test OpenSearch connectivity
            cluster_health = self.client.cluster.health()
            
            return {
                "service": "BulkOpenSearchService",
                "status": "healthy" if cluster_health["status"] in ["green", "yellow"] else "unhealthy",
                "opensearch_status": cluster_health["status"],
                "circuit_breaker": {
                    "is_open": self.circuit_breaker.is_open,
                    "failure_count": self.circuit_breaker.failure_count
                },
                "configuration": {
                    "max_batch_size_mb": self.max_batch_size_mb,
                    "min_batch_size_mb": self.min_batch_size_mb,
                    "max_retries": self.max_retries
                }
            }
            
        except Exception as e:
            return {
                "service": "BulkOpenSearchService", 
                "status": "unhealthy",
                "error": str(e),
                "circuit_breaker": {
                    "is_open": True,
                    "failure_count": self.circuit_breaker.failure_count
                }
            }

# Global service instance
_bulk_opensearch_service: Optional[BulkOpenSearchService] = None

def get_bulk_opensearch_service() -> BulkOpenSearchService:
    """Get or create the global bulk OpenSearch service instance"""
    global _bulk_opensearch_service
    if _bulk_opensearch_service is None:
        _bulk_opensearch_service = BulkOpenSearchService()
    return _bulk_opensearch_service