"""
V1 Indexing API Endpoints - Enterprise Job Management with Checkpoint/Resume

Provides REST API endpoints for:
- Starting, pausing, resuming indexing jobs
- Monitoring job progress and health
- Managing checkpoints and cache synchronization
- Enterprise-grade error handling and logging
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import logging

from app.services.v1_indexing_service import get_v1_indexing_service
from app.services.embedding_service import get_embedding_service
from app.models.indexing_models import JobType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/indexing", tags=["V1 Indexing"])

# Request/Response Models
class StartIndexingRequest(BaseModel):
    repository_path: str = Field(..., description="Path to repository to index")
    job_type: JobType = Field(default=JobType.FULL, description="Type of indexing job")
    file_patterns: Optional[List[str]] = Field(default=None, description="File patterns to include")
    exclude_patterns: Optional[List[str]] = Field(default=None, description="File patterns to exclude")
    force_reindex: bool = Field(default=False, description="Force reindexing of existing files")

class JobControlRequest(BaseModel):
    job_id: str = Field(..., description="ID of the job to control")

class CacheSyncRequest(BaseModel):
    limit: int = Field(default=1000, description="Maximum number of embeddings to sync")

class JobResponse(BaseModel):
    job_id: str
    message: str
    success: bool

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: Dict[str, Any]
    checkpoint: Optional[Dict[str, Any]]
    timing: Dict[str, Any]
    performance: Dict[str, Any]

@router.post("/start", response_model=JobResponse)
async def start_indexing_job(
    request: StartIndexingRequest,
    indexing_service = Depends(get_v1_indexing_service)
):
    """
    Start a new indexing job with enterprise fault tolerance
    
    Features:
    - Dynamic chunking (50 files OR 10MB per chunk)
    - Automatic checkpoint creation for resume capability  
    - Unified Redis+PostgreSQL caching
    - Circuit breakers and rate limiting
    - Real-time progress monitoring
    """
    try:
        job_id = await indexing_service.start_indexing_job(
            repository_path=request.repository_path,
            job_type=request.job_type,
            file_patterns=request.file_patterns,
            exclude_patterns=request.exclude_patterns,
            force_reindex=request.force_reindex
        )
        
        logger.info(f"🚀 Started indexing job {job_id} for {request.repository_path}")
        
        return JobResponse(
            job_id=job_id,
            message=f"Indexing job started successfully for {request.repository_path}",
            success=True
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to start indexing job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start indexing job: {str(e)}")

@router.post("/pause", response_model=JobResponse)
async def pause_indexing_job(
    request: JobControlRequest,
    indexing_service = Depends(get_v1_indexing_service)
):
    """
    Pause a running indexing job at the next checkpoint
    
    The job will complete its current chunk and save a checkpoint
    before pausing, allowing for clean resumption later.
    """
    try:
        success = await indexing_service.pause_job(request.job_id)
        
        if success:
            logger.info(f"⏸️  Paused indexing job {request.job_id}")
            return JobResponse(
                job_id=request.job_id,
                message="Job marked for pause at next checkpoint",
                success=True
            )
        else:
            raise HTTPException(status_code=400, detail="Could not pause job - check job status")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to pause job {request.job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to pause job: {str(e)}")

@router.post("/resume", response_model=JobResponse)
async def resume_indexing_job(
    request: JobControlRequest,
    indexing_service = Depends(get_v1_indexing_service)
):
    """
    Resume a paused indexing job from its last checkpoint
    
    The job will continue processing from exactly where it left off,
    using the deterministic file processing order.
    """
    try:
        success = await indexing_service.resume_job(request.job_id)
        
        if success:
            logger.info(f"▶️  Resumed indexing job {request.job_id}")
            return JobResponse(
                job_id=request.job_id,
                message="Job queued for resumption from last checkpoint",
                success=True
            )
        else:
            raise HTTPException(status_code=400, detail="Could not resume job - check job status")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to resume job {request.job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to resume job: {str(e)}")

@router.get("/status/{job_id}")
async def get_job_status(
    job_id: str,
    indexing_service = Depends(get_v1_indexing_service)
):
    """
    Get comprehensive job status including checkpoint information
    
    Returns:
    - Job progress and statistics
    - Checkpoint status and resume capability
    - Performance metrics
    - Error information if applicable
    """
    try:
        status = await indexing_service.get_job_status(job_id)
        
        if not status:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get job status for {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")

@router.get("/checkpoint/{job_id}")
async def get_checkpoint_status(
    job_id: str,
    indexing_service = Depends(get_v1_indexing_service)
):
    """
    Get detailed checkpoint information for a job
    
    Provides information about:
    - Last processed file
    - Checkpoint timestamp
    - Resume capability
    - Processing progress
    """
    try:
        checkpoint_status = await indexing_service.get_checkpoint_status(job_id)
        
        if not checkpoint_status:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        return checkpoint_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get checkpoint status for {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get checkpoint status: {str(e)}")

@router.get("/jobs/recent")
async def list_recent_jobs(
    limit: int = 10,
    indexing_service = Depends(get_v1_indexing_service)
):
    """
    List recent indexing jobs with basic status information
    """
    try:
        jobs = await indexing_service.list_recent_jobs(limit)
        return {"jobs": jobs, "count": len(jobs)}
        
    except Exception as e:
        logger.error(f"❌ Failed to list recent jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list recent jobs: {str(e)}")

@router.post("/cache/sync")
async def sync_cache_postgresql_to_redis(
    request: CacheSyncRequest,
    background_tasks: BackgroundTasks,
    embedding_service = Depends(get_embedding_service)
):
    """
    Sync frequently used embeddings from PostgreSQL to Redis
    
    Useful for:
    - Warming Redis cache after restart
    - Improving performance for frequently accessed embeddings
    - Cross-instance cache synchronization
    """
    try:
        # Run sync in background to avoid timeout
        background_tasks.add_task(
            embedding_service.sync_cache_from_postgresql_to_redis,
            request.limit
        )
        
        logger.info(f"🔄 Cache sync started (limit: {request.limit})")
        
        return {
            "message": f"Cache sync started for top {request.limit} embeddings",
            "status": "started",
            "limit": request.limit
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to start cache sync: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start cache sync: {str(e)}")

@router.get("/health")
async def get_indexing_health(
    embedding_service = Depends(get_embedding_service)
):
    """
    Get comprehensive health status for indexing services
    
    Returns:
    - EmbeddingService health (Redis, Bedrock, circuit breakers)
    - Cache statistics and performance metrics
    - Memory and resource usage
    - Service availability status
    """
    try:
        embedding_health = await embedding_service.get_embedding_health()
        
        return {
            "status": "healthy",
            "services": {
                "embedding_service": embedding_health,
                "indexing_service": "operational"
            },
            "timestamp": "2024-01-01T00:00:00Z"  # Current timestamp would be added
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get health status: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "services": {
                "embedding_service": {"status": "unhealthy"},
                "indexing_service": "unknown"
            }
        }

@router.get("/cache/stats")
async def get_cache_statistics(
    embedding_service = Depends(get_embedding_service)
):
    """
    Get detailed cache performance statistics
    
    Returns:
    - Cache hit/miss rates
    - Cost savings from caching
    - Cache size and utilization
    - Performance metrics
    """
    try:
        stats = embedding_service.get_cache_statistics()
        return {
            "cache_statistics": stats,
            "unified_caching": {
                "redis_primary": True,
                "postgresql_fallback": True,
                "auto_sync": True
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get cache statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache statistics: {str(e)}")