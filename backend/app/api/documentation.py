"""
Documentation generation API endpoints
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, Dict, Any
from uuid import uuid4
from datetime import datetime
import logging
import traceback
from pathlib import Path
import zipfile

from app.core.database import get_session, DocumentationJob
from app.models.schemas import (
    DocumentationRequest,
    DocumentationResponse,
    JobStatusResponse
)
from app.services.documentation_service import DocumentationService

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/generate", response_model=DocumentationResponse)
async def generate_documentation(
    request: DocumentationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session)
):
    """
    Generate documentation for a repository
    """
    try:
        # Create job ID
        job_id = str(uuid4())
        
        # Create job record
        job = DocumentationJob(
            job_id=job_id,
            repository_path=request.repository_path,
            status="pending",
            config=request.dict()
        )
        db.add(job)
        await db.commit()
        
        # Start generation in background
        doc_service = DocumentationService(db)
        background_tasks.add_task(
            doc_service.generate_documentation,
            job_id,
            request
        )
        
        return DocumentationResponse(
            job_id=job_id,
            status="processing",
            message="Documentation generation started"
        )
        
    except Exception as e:
        logger.error(f"Error starting documentation generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    db: AsyncSession = Depends(get_session)
):
    """
    Get status of a documentation generation job
    """
    try:
        query = await db.execute(
            select(DocumentationJob).where(DocumentationJob.job_id == job_id)
        )
        job = query.scalar_one_or_none()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return JobStatusResponse(
            job_id=job.job_id,
            status=job.status,
            created_at=job.created_at,
            completed_at=job.completed_at,
            entities_count=job.entities_count or 0,
            business_rules_count=job.business_rules_count or 0,
            files_processed=job.files_processed or 0,
            output_path=job.output_path,
            error_message=job.error_message,
            processing_time_seconds=job.processing_time_seconds or 0
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching job status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/jobs")
async def list_jobs(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_session)
):
    """
    List all documentation generation jobs
    """
    try:
        query = await db.execute(
            select(DocumentationJob)
            .order_by(DocumentationJob.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        jobs = query.scalars().all()
        
        return [
            {
                "job_id": job.job_id,
                "repository_path": job.repository_path,
                "status": job.status,
                "created_at": job.created_at,
                "completed_at": job.completed_at,
                "entities_count": job.entities_count,
                "business_rules_count": job.business_rules_count
            }
            for job in jobs
        ]
    except Exception as e:
        logger.error(f"Error listing jobs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list jobs")
@router.post("/sync")
async def sync_repository(
    repo_path: str,
    db: AsyncSession = Depends(get_session)
):
    """
    Sync repository for incremental updates
    """
    try:
        # Validate repository exists
        if not Path(repo_path).exists():
            raise HTTPException(status_code=404, detail="Repository not found")
        
        # Check for existing documentation
        query = await db.execute(
            select(DocumentationJob)
            .where(DocumentationJob.repository_path == repo_path)
            .order_by(DocumentationJob.created_at.desc())
            .limit(1)
        )
        last_job = query.scalar_one_or_none()
        
        if last_job and last_job.status == "completed":
            # Perform incremental update
            job_id = str(uuid4())
            new_job = DocumentationJob(
                job_id=job_id,
                repository_path=repo_path,
                status="pending",
                config={"incremental_update": True}
            )
            db.add(new_job)
            await db.commit()
            
            logger.info(f"Started incremental sync for {repo_path}, job_id: {job_id}")
            
            return {
                "message": "Incremental sync started",
                "job_id": job_id,
                "last_sync": last_job.completed_at.isoformat() if last_job.completed_at else None
            }
        else:
            return {
                "message": "No previous documentation found",
                "requires_full_generation": True
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sync failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{job_id}")
async def download_documentation(
    job_id: str,
    db: AsyncSession = Depends(get_session)
):
    """
    Download generated documentation as ZIP
    """
    try:
        # Get job details
        query = await db.execute(
            select(DocumentationJob).where(DocumentationJob.job_id == job_id)
        )
        job = query.scalar_one_or_none()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.status != "completed":
            raise HTTPException(
                status_code=400, 
                detail=f"Job is {job.status}, not completed"
            )
        
        # Check if output exists
        output_dir = Path(job.output_path) if job.output_path else Path(f"output/{job_id}")
        if not output_dir.exists():
            raise HTTPException(status_code=404, detail="Output not found")
        
        # Create ZIP file
        zip_path = Path(f"temp/{job_id}.zip")
        zip_path.parent.mkdir(exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in output_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(output_dir)
                    zipf.write(file_path, arcname)
        
        return FileResponse(
            path=str(zip_path),
            filename=f"documentation_{job_id}.zip",
            media_type="application/zip"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
