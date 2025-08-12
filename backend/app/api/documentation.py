"""
Documentation generation API endpoints
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
from uuid import uuid4
from datetime import datetime
import logging

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
        entities_count=job.entities_count,
        business_rules_count=job.business_rules_count,
        files_processed=job.files_processed,
        output_path=job.output_path,
        error_message=job.error_message
    )

@router.get("/jobs")
async def list_jobs(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_session)
):
    """
    List all documentation generation jobs
    """
    from sqlalchemy import select
    
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

# Add import at top of file
from sqlalchemy import select
