"""
Repository Processing API endpoints for multi-repository parallel processing
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from pydantic import BaseModel, Field
from datetime import datetime

from app.services.repository_processor import (
    get_repository_processor, 
    RepositoryProcessor, 
    RepositoryInfo, 
    ProcessingResult, 
    ProcessingStatus
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/processing", tags=["Repository Processing"])

# Request/Response Models
class RepositorySourceRequest(BaseModel):
    id: str = Field(..., description="Unique repository identifier")
    name: str = Field(..., description="Repository name")
    source_type: str = Field(..., description="Source type: git, zip, tar, directory")
    source_path: str = Field(..., description="Source path (URL, file path, or directory)")
    branch: str = Field(default="main", description="Git branch (for git repositories)")
    priority: int = Field(default=1, ge=1, le=5, description="Processing priority (1=highest)")
    processing_options: Dict[str, Any] = Field(default_factory=dict, description="Processing options")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class BatchProcessingRequest(BaseModel):
    repositories: List[RepositorySourceRequest] = Field(..., description="List of repositories to process")
    batch_options: Dict[str, Any] = Field(default_factory=dict, description="Batch processing options")
    
    class Config:
        schema_extra = {
            "example": {
                "repositories": [
                    {
                        "id": "legacy-customer-service",
                        "name": "Customer Service (Legacy)",
                        "source_type": "git",
                        "source_path": "https://github.com/company/customer-service-legacy.git",
                        "branch": "main",
                        "priority": 1,
                        "processing_options": {
                            "deep_analysis": True,
                            "extract_business_rules": True
                        },
                        "metadata": {
                            "team": "customer-experience",
                            "migration_target": "spring-boot"
                        }
                    },
                    {
                        "id": "billing-system",
                        "name": "Billing System",
                        "source_type": "directory",
                        "source_path": "/path/to/billing-system",
                        "priority": 2
                    }
                ],
                "batch_options": {
                    "parallel_processing": True,
                    "generate_migration_plan": True
                }
            }
        }

class ProcessingStatusResponse(BaseModel):
    repository_id: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    entities_extracted: int = 0
    business_rules_found: int = 0
    files_processed: int = 0
    errors: List[str] = []
    warnings: List[str] = []
    processing_stats: Dict[str, Any] = {}

class BatchStatusResponse(BaseModel):
    active_jobs: int
    completed_jobs: int
    failed_jobs: int
    total_processed: int
    current_jobs: List[str]

@router.post("/batch")
async def start_batch_processing(
    request: BatchProcessingRequest,
    background_tasks: BackgroundTasks,
    processor: RepositoryProcessor = Depends(get_repository_processor)
):
    """
    Start batch processing of multiple repositories
    """
    try:
        # Convert request to RepositoryInfo objects
        repository_infos = []
        for repo_req in request.repositories:
            repo_info = RepositoryInfo(
                id=repo_req.id,
                name=repo_req.name,
                source_type=repo_req.source_type,
                source_path=repo_req.source_path,
                branch=repo_req.branch,
                priority=repo_req.priority,
                processing_options=repo_req.processing_options,
                metadata=repo_req.metadata
            )
            repository_infos.append(repo_info)
        
        # Validate repository IDs are unique
        repo_ids = [repo.id for repo in repository_infos]
        if len(repo_ids) != len(set(repo_ids)):
            raise HTTPException(
                status_code=400, 
                detail="Repository IDs must be unique within the batch"
            )
        
        # Add batch processing options
        batch_options = {
            **request.batch_options,
            "batch_id": f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "submitted_at": datetime.utcnow().isoformat()
        }
        
        # Start background processing
        background_tasks.add_task(
            processor.process_repositories_batch,
            repository_infos,
            batch_options
        )
        
        logger.info(f"Started batch processing for {len(repository_infos)} repositories")
        
        return {
            "success": True,
            "message": f"Batch processing started for {len(repository_infos)} repositories",
            "batch_id": batch_options["batch_id"],
            "repository_ids": repo_ids,
            "estimated_completion": "Processing time varies by repository size and complexity"
        }
        
    except Exception as e:
        logger.error(f"Batch processing start failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start batch processing: {str(e)}")

@router.post("/single")
async def start_single_repository_processing(
    request: RepositorySourceRequest,
    background_tasks: BackgroundTasks,
    processor: RepositoryProcessor = Depends(get_repository_processor)
):
    """
    Start processing a single repository
    """
    try:
        repo_info = RepositoryInfo(
            id=request.id,
            name=request.name,
            source_type=request.source_type,
            source_path=request.source_path,
            branch=request.branch,
            priority=request.priority,
            processing_options=request.processing_options,
            metadata=request.metadata
        )
        
        # Start background processing
        background_tasks.add_task(processor.process_single_repository, repo_info)
        
        logger.info(f"Started processing for repository {request.name}")
        
        return {
            "success": True,
            "message": f"Processing started for repository: {request.name}",
            "repository_id": request.id,
            "status": "processing_started"
        }
        
    except Exception as e:
        logger.error(f"Single repository processing start failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start processing: {str(e)}")

@router.get("/status/{repository_id}")
async def get_repository_status(
    repository_id: str,
    processor: RepositoryProcessor = Depends(get_repository_processor)
) -> ProcessingStatusResponse:
    """
    Get processing status for a specific repository
    """
    try:
        result = await processor.get_processing_status(repository_id)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Repository {repository_id} not found")
        
        return ProcessingStatusResponse(
            repository_id=result.repository_id,
            status=result.status.value,
            start_time=result.start_time,
            end_time=result.end_time,
            entities_extracted=result.entities_extracted,
            business_rules_found=result.business_rules_found,
            files_processed=result.files_processed,
            errors=result.errors,
            warnings=result.warnings,
            processing_stats=result.processing_stats
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

@router.get("/batch-status")
async def get_batch_status(
    processor: RepositoryProcessor = Depends(get_repository_processor)
) -> BatchStatusResponse:
    """
    Get overall batch processing status
    """
    try:
        status = await processor.get_batch_status()
        
        return BatchStatusResponse(
            active_jobs=status["active_jobs"],
            completed_jobs=status["completed_jobs"],
            failed_jobs=status["failed_jobs"],
            total_processed=status["total_processed"],
            current_jobs=status["current_jobs"]
        )
        
    except Exception as e:
        logger.error(f"Batch status retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get batch status: {str(e)}")

@router.post("/cancel/{repository_id}")
async def cancel_repository_processing(
    repository_id: str,
    processor: RepositoryProcessor = Depends(get_repository_processor)
):
    """
    Cancel processing for a specific repository
    """
    try:
        success = await processor.cancel_processing(repository_id)
        
        if success:
            return {
                "success": True,
                "message": f"Processing cancelled for repository: {repository_id}"
            }
        else:
            raise HTTPException(
                status_code=404, 
                detail=f"Repository {repository_id} not found or not currently processing"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Processing cancellation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel processing: {str(e)}")

@router.get("/history")
async def get_processing_history(
    limit: int = Query(default=50, ge=1, le=200, description="Maximum number of results"),
    status_filter: Optional[str] = Query(default=None, description="Filter by status"),
    processor: RepositoryProcessor = Depends(get_repository_processor)
):
    """
    Get processing history with optional filtering
    """
    try:
        # Get job history
        history = processor.job_history
        
        # Apply status filter if provided
        if status_filter:
            try:
                status_enum = ProcessingStatus(status_filter)
                history = [job for job in history if job.status == status_enum]
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status filter: {status_filter}")
        
        # Sort by start time (newest first) and limit
        history = sorted(history, key=lambda x: x.start_time, reverse=True)[:limit]
        
        # Convert to response format
        history_responses = []
        for result in history:
            history_responses.append(ProcessingStatusResponse(
                repository_id=result.repository_id,
                status=result.status.value,
                start_time=result.start_time,
                end_time=result.end_time,
                entities_extracted=result.entities_extracted,
                business_rules_found=result.business_rules_found,
                files_processed=result.files_processed,
                errors=result.errors,
                warnings=result.warnings,
                processing_stats=result.processing_stats
            ))
        
        return {
            "success": True,
            "total_results": len(history_responses),
            "results": history_responses,
            "filters_applied": {
                "status": status_filter,
                "limit": limit
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"History retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get processing history: {str(e)}")

@router.get("/supported-sources")
async def get_supported_source_types():
    """
    Get list of supported repository source types and their requirements
    """
    return {
        "success": True,
        "supported_sources": {
            "git": {
                "description": "Git repositories (GitHub, GitLab, Bitbucket, etc.)",
                "source_path_format": "https://github.com/user/repo.git",
                "additional_fields": ["branch"],
                "examples": [
                    "https://github.com/apache/struts.git",
                    "git@github.com:company/legacy-app.git"
                ]
            },
            "zip": {
                "description": "ZIP archive files",
                "source_path_format": "/path/to/archive.zip",
                "additional_fields": [],
                "examples": [
                    "/uploads/legacy-codebase.zip",
                    "C:\\Downloads\\project-archive.zip"
                ]
            },
            "tar": {
                "description": "TAR archive files (including .tar.gz, .tar.bz2)",
                "source_path_format": "/path/to/archive.tar.gz",
                "additional_fields": [],
                "examples": [
                    "/backups/codebase.tar.gz",
                    "/tmp/export.tar.bz2"
                ]
            },
            "directory": {
                "description": "Local file system directories",
                "source_path_format": "/path/to/directory",
                "additional_fields": [],
                "examples": [
                    "/home/user/projects/legacy-app",
                    "C:\\Development\\OldProjects\\CustomerService"
                ]
            }
        },
        "processing_options": {
            "deep_analysis": {
                "type": "boolean",
                "description": "Perform detailed code analysis including complexity metrics",
                "default": False
            },
            "extract_business_rules": {
                "type": "boolean", 
                "description": "Extract business rules from comments and documentation",
                "default": True
            },
            "include_tests": {
                "type": "boolean",
                "description": "Include test files in analysis",
                "default": True
            },
            "parallel_file_processing": {
                "type": "boolean",
                "description": "Process files in parallel for faster analysis",
                "default": True
            }
        }
    }

@router.get("/health")
async def repository_processing_health(
    processor: RepositoryProcessor = Depends(get_repository_processor)
):
    """
    Health check for repository processing service
    """
    try:
        # Get current status
        status = await processor.get_batch_status()
        
        # Check if services are available
        services_status = {
            "vector_service": processor.vector_service is not None,
            "semantic_ai_service": processor.semantic_ai_service is not None,
            "ai_service": processor.ai_service is not None
        }
        
        all_services_healthy = all(services_status.values())
        
        return {
            "success": True,
            "status": "healthy" if all_services_healthy else "degraded",
            "services": services_status,
            "current_load": {
                "active_jobs": status["active_jobs"],
                "max_concurrent": processor.max_concurrent_repos,
                "utilization_percentage": (status["active_jobs"] / processor.max_concurrent_repos) * 100
            },
            "configuration": {
                "max_concurrent_repos": processor.max_concurrent_repos,
                "batch_size": processor.batch_size,
                "processing_timeout": processor.processing_timeout
            },
            "statistics": {
                "total_processed": status["total_processed"],
                "completed_jobs": status["completed_jobs"],
                "failed_jobs": status["failed_jobs"],
                "success_rate": (status["completed_jobs"] / status["total_processed"] * 100) 
                              if status["total_processed"] > 0 else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Repository processing health check failed: {e}")
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e)
        }