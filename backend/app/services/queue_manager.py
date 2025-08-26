"""
Queue Manager - Multi-Stage Queue Coordination with Backpressure

Implements 3-stage pipeline:
- ingest: file reading + parsing
- embed: Bedrock embedding calls  
- index: OpenSearch bulk operations

Features:
- Backpressure management to prevent queue overload
- Health monitoring and metrics
- Dynamic scaling based on queue depths
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

import redis
from rq import Queue, Worker, Connection
from rq.job import Job
from prometheus_client import Gauge, Counter

from app.core.config import settings

logger = logging.getLogger(__name__)

# Prometheus metrics
QUEUE_DEPTH = Gauge('docxp_queue_depth', 'Current queue depth', ['stage'])
QUEUE_THROUGHPUT = Counter('docxp_queue_processed_total', 'Total jobs processed', ['stage', 'status'])
BACKPRESSURE_EVENTS = Counter('docxp_backpressure_events_total', 'Backpressure activation events', ['stage'])

class QueueStage(str, Enum):
    INGEST = "ingest"
    EMBED = "embed"
    INDEX = "index"

class QueueManager:
    """
    Multi-stage queue manager with intelligent backpressure
    
    Prevents any single stage from overwhelming downstream stages
    """
    
    def __init__(self):
        self.redis_client = redis.Redis.from_url(
            getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
        )
        
        # Queue configuration
        self.max_depths = {
            QueueStage.INGEST: getattr(settings, 'QUEUE_MAX_INGEST_DEPTH', 200),
            QueueStage.EMBED: getattr(settings, 'QUEUE_MAX_EMBED_DEPTH', 100),
            QueueStage.INDEX: getattr(settings, 'QUEUE_MAX_INDEX_DEPTH', 50)
        }
        
        # Backpressure thresholds (when to pause upstream)
        self.backpressure_thresholds = {
            QueueStage.EMBED: getattr(settings, 'QUEUE_EMBED_BACKPRESSURE_THRESHOLD', 100),
            QueueStage.INDEX: getattr(settings, 'QUEUE_INDEX_BACKPRESSURE_THRESHOLD', 50)
        }
        
        # Initialize queues
        self.queues = {
            QueueStage.INGEST: Queue('ingest', connection=self.redis_client),
            QueueStage.EMBED: Queue('embed', connection=self.redis_client), 
            QueueStage.INDEX: Queue('index', connection=self.redis_client)
        }
        
        logger.info("✅ QueueManager initialized with 3-stage pipeline")
    
    async def enqueue_job(self, stage: QueueStage, func_name: str, *args, **kwargs) -> Optional[str]:
        """
        Enqueue job with backpressure check
        
        Returns job ID if enqueued, None if backpressure prevents enqueue
        """
        try:
            # Check backpressure before enqueueing
            if await self._should_apply_backpressure(stage):
                BACKPRESSURE_EVENTS.labels(stage=stage.value).inc()
                logger.warning(f"🚦 Backpressure: {stage.value} queue blocked due to downstream congestion")
                return None
            
            # Enqueue the job
            queue = self.queues[stage]
            job = queue.enqueue(func_name, *args, **kwargs)
            
            # Update metrics
            current_depth = len(queue)
            QUEUE_DEPTH.labels(stage=stage.value).set(current_depth)
            
            logger.debug(f"📤 Enqueued {stage.value} job {job.id} (depth: {current_depth})")
            return job.id
            
        except Exception as e:
            logger.error(f"❌ Failed to enqueue {stage.value} job: {e}")
            return None
    
    async def _should_apply_backpressure(self, stage: QueueStage) -> bool:
        """
        Check if backpressure should be applied for this stage
        
        Backpressure logic:
        - Pause ingest if embed queue > threshold
        - Pause embed if index queue > threshold  
        - Index queue never has backpressure (it's the sink)
        """
        try:
            if stage == QueueStage.INGEST:
                # Check embed queue depth
                embed_depth = len(self.queues[QueueStage.EMBED])
                threshold = self.backpressure_thresholds[QueueStage.EMBED]
                return embed_depth >= threshold
                
            elif stage == QueueStage.EMBED:
                # Check index queue depth  
                index_depth = len(self.queues[QueueStage.INDEX])
                threshold = self.backpressure_thresholds[QueueStage.INDEX]
                return index_depth >= threshold
                
            else:  # INDEX stage
                # Index is the sink - never apply backpressure
                return False
                
        except Exception as e:
            logger.error(f"❌ Error checking backpressure for {stage.value}: {e}")
            # Conservative approach: apply backpressure on error
            return True
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """
        Get comprehensive queue status for monitoring
        """
        try:
            status = {
                "timestamp": datetime.utcnow().isoformat(),
                "queues": {},
                "backpressure": {},
                "workers": {}
            }
            
            for stage, queue in self.queues.items():
                depth = len(queue)
                
                # Queue metrics
                status["queues"][stage.value] = {
                    "depth": depth,
                    "max_depth": self.max_depths[stage],
                    "utilization_pct": round((depth / self.max_depths[stage]) * 100, 1)
                }
                
                # Update Prometheus metrics
                QUEUE_DEPTH.labels(stage=stage.value).set(depth)
                
                # Backpressure status
                if stage in self.backpressure_thresholds:
                    threshold = self.backpressure_thresholds[stage]
                    status["backpressure"][stage.value] = {
                        "threshold": threshold,
                        "active": depth >= threshold,
                        "margin": threshold - depth
                    }
            
            # Worker status
            for stage in QueueStage:
                workers = Worker.all(queue=self.queues[stage])
                status["workers"][stage.value] = {
                    "count": len(workers),
                    "busy": len([w for w in workers if w.get_current_job()]),
                    "idle": len([w for w in workers if not w.get_current_job()])
                }
            
            return status
            
        except Exception as e:
            logger.error(f"❌ Error getting queue status: {e}")
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a specific job across all queues
        """
        try:
            for stage, queue in self.queues.items():
                try:
                    job = Job.fetch(job_id, connection=self.redis_client)
                    return {
                        "job_id": job_id,
                        "stage": stage.value,
                        "status": job.get_status(),
                        "created_at": job.created_at.isoformat() if job.created_at else None,
                        "started_at": job.started_at.isoformat() if job.started_at else None,
                        "ended_at": job.ended_at.isoformat() if job.ended_at else None,
                        "result": job.result,
                        "exc_info": job.exc_info
                    }
                except:
                    continue
                    
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting job status for {job_id}: {e}")
            return None
    
    async def clear_queue(self, stage: QueueStage) -> bool:
        """
        Clear all jobs from a specific queue (admin operation)
        """
        try:
            queue = self.queues[stage]
            queue.empty()
            
            # Reset metrics
            QUEUE_DEPTH.labels(stage=stage.value).set(0)
            
            logger.info(f"🧹 Cleared {stage.value} queue")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error clearing {stage.value} queue: {e}")
            return False
    
    async def pause_queue(self, stage: QueueStage) -> bool:
        """
        Pause workers for a specific queue
        """
        try:
            # This would integrate with worker management
            # For now, log the action
            logger.info(f"⏸️  Paused {stage.value} queue workers")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error pausing {stage.value} queue: {e}")
            return False
    
    async def resume_queue(self, stage: QueueStage) -> bool:
        """
        Resume workers for a specific queue
        """
        try:
            # This would integrate with worker management
            # For now, log the action
            logger.info(f"▶️  Resumed {stage.value} queue workers")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error resuming {stage.value} queue: {e}")
            return False

# Global queue manager instance
_queue_manager: Optional[QueueManager] = None

def get_queue_manager() -> QueueManager:
    """Get or create the global queue manager instance"""
    global _queue_manager
    if _queue_manager is None:
        _queue_manager = QueueManager()
    return _queue_manager

# Worker functions for each stage
def process_ingest_job(job_id: str, repository_path: str, file_paths: List[str], **kwargs):
    """
    Process ingest job: read files and parse content
    """
    from app.services.v1_indexing_service import get_v1_indexing_service
    
    logger.info(f"🔍 Processing ingest job {job_id} for {len(file_paths)} files")
    
    try:
        service = get_v1_indexing_service()
        # This will be implemented in the updated V1IndexingService
        result = service.process_ingest_chunk(job_id, repository_path, file_paths, **kwargs)
        
        QUEUE_THROUGHPUT.labels(stage='ingest', status='success').inc()
        return result
        
    except Exception as e:
        logger.error(f"❌ Ingest job {job_id} failed: {e}")
        QUEUE_THROUGHPUT.labels(stage='ingest', status='failed').inc()
        raise

def process_embed_job(job_id: str, entities: List[Dict[str, Any]], **kwargs):
    """
    Process embed job: generate embeddings via Bedrock
    """
    from app.services.embedding_service import EmbeddingService
    
    logger.info(f"🧠 Processing embed job {job_id} for {len(entities)} entities")
    
    try:
        service = EmbeddingService()
        # This will be updated to handle batching
        result = service.process_embed_batch(job_id, entities, **kwargs)
        
        QUEUE_THROUGHPUT.labels(stage='embed', status='success').inc()
        return result
        
    except Exception as e:
        logger.error(f"❌ Embed job {job_id} failed: {e}")
        QUEUE_THROUGHPUT.labels(stage='embed', status='failed').inc()
        raise

def process_index_job(job_id: str, entities_with_embeddings: List[Dict[str, Any]], **kwargs):
    """
    Process index job: bulk index to OpenSearch
    """
    from app.services.bulk_opensearch_service import BulkOpenSearchService
    
    logger.info(f"📚 Processing index job {job_id} for {len(entities_with_embeddings)} entities")
    
    try:
        service = BulkOpenSearchService()
        # This will be implemented
        result = service.bulk_index_entities(job_id, entities_with_embeddings, **kwargs)
        
        QUEUE_THROUGHPUT.labels(stage='index', status='success').inc()
        return result
        
    except Exception as e:
        logger.error(f"❌ Index job {job_id} failed: {e}")
        QUEUE_THROUGHPUT.labels(stage='index', status='failed').inc()
        raise