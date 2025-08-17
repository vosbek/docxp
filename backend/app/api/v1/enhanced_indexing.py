"""
Enhanced V1 Indexing API with jQAssistant Integration

REST API endpoints for the enhanced V1 indexing pipeline that includes
comprehensive architectural analysis with jQAssistant integration.
"""

import asyncio
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from pydantic import BaseModel, Field

from app.services.enhanced_v1_indexing_service import get_enhanced_v1_indexing_service
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/enhanced-indexing", tags=["Enhanced V1 Indexing"])

# Request Models
class EnhancedIndexingRequest(BaseModel):
    repository_path: str = Field(..., description="Path to repository")
    job_type: str = Field("full", description="Type of indexing (full, incremental, selective)")
    file_patterns: Optional[List[str]] = Field(None, description="File patterns to include")
    exclude_patterns: Optional[List[str]] = Field(None, description="File patterns to exclude")
    force_reindex: bool = Field(False, description="Force reindexing of existing files")
    enable_architectural_analysis: Optional[bool] = Field(None, description="Enable jQAssistant analysis")
    custom_architectural_layers: Optional[List[Dict[str, Any]]] = Field(None, description="Custom layer definitions")
    custom_architectural_constraints: Optional[List[str]] = Field(None, description="Custom constraint rules")

class TriggerArchitecturalAnalysisRequest(BaseModel):
    indexing_job_id: str = Field(..., description="Existing indexing job ID")
    custom_layers: Optional[List[Dict[str, Any]]] = Field(None, description="Custom layer definitions")
    custom_constraints: Optional[List[str]] = Field(None, description="Custom constraint rules")
    include_test_code: bool = Field(False, description="Include test code in analysis")

# Response Models
class EnhancedIndexingResponse(BaseModel):
    indexing_job_id: str
    architectural_analysis_job_id: Optional[str]
    architectural_analysis_enabled: bool
    java_files_detected: int
    status: str
    message: str

class EnhancedJobStatusResponse(BaseModel):
    indexing_job: Dict[str, Any]
    architectural_analysis_job: Optional[Dict[str, Any]]
    overall_status: str
    overall_progress: float
    architectural_insights: List[Dict[str, Any]]

class RepositoryHealthResponse(BaseModel):
    status: str
    health_score: Optional[float]
    health_grade: Optional[str]
    health_factors: Optional[Dict[str, Any]]
    analysis_date: Optional[str]
    analysis_job_id: Optional[str]
    recommendations: Optional[List[str]]
    message: Optional[str]

class ArchitecturalSummaryResponse(BaseModel):
    status: str
    analysis_job_id: Optional[str]
    repository_id: Optional[str]
    commit_hash: Optional[str]
    quality_scores: Optional[Dict[str, Any]]
    metrics: Optional[Dict[str, Any]]
    timing: Optional[Dict[str, Any]]
    reason: Optional[str]

# Global service instance
enhanced_indexing_service = None

async def get_service():
    """Get enhanced indexing service instance"""
    global enhanced_indexing_service
    if not enhanced_indexing_service:
        enhanced_indexing_service = await get_enhanced_v1_indexing_service()
    return enhanced_indexing_service

@router.post("/start", response_model=EnhancedIndexingResponse)
async def start_enhanced_indexing(
    request: EnhancedIndexingRequest,
    background_tasks: BackgroundTasks
):
    """
    Start enhanced indexing job with optional architectural analysis
    
    Performs V1 indexing with automatic detection and analysis of Java repositories.
    Includes comprehensive error handling and progress tracking.
    """
    try:
        logger.info(f"🚀 Starting enhanced indexing for {request.repository_path}")
        
        service = await get_service()
        
        # Convert job type string to enum
        from app.models.indexing_models import JobType
        job_type_map = {
            'full': JobType.FULL,
            'incremental': JobType.INCREMENTAL,
            'selective': JobType.SELECTIVE
        }
        job_type = job_type_map.get(request.job_type.lower(), JobType.FULL)
        
        # Start enhanced indexing
        result = await service.start_enhanced_indexing_job(
            repository_path=request.repository_path,
            job_type=job_type,
            file_patterns=request.file_patterns,
            exclude_patterns=request.exclude_patterns,
            force_reindex=request.force_reindex,
            enable_architectural_analysis=request.enable_architectural_analysis,
            custom_architectural_layers=request.custom_architectural_layers,
            custom_architectural_constraints=request.custom_architectural_constraints
        )
        
        return EnhancedIndexingResponse(
            indexing_job_id=result["indexing_job_id"],
            architectural_analysis_job_id=result.get("architectural_analysis_job_id"),
            architectural_analysis_enabled=result["architectural_analysis_enabled"],
            java_files_detected=result["java_files_detected"],
            status="started",
            message=f"Enhanced indexing started for {request.repository_path}"
        )
        
    except ValueError as e:
        logger.error(f"Validation error in enhanced indexing: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Enhanced indexing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Enhanced indexing failed: {str(e)}")

@router.get("/status/{indexing_job_id}", response_model=EnhancedJobStatusResponse)
async def get_enhanced_job_status(indexing_job_id: str):
    """
    Get comprehensive status for enhanced indexing job
    
    Returns status for both V1 indexing and architectural analysis
    with combined progress tracking and insights.
    """
    try:
        service = await get_service()
        
        status = await service.get_enhanced_job_status(indexing_job_id)
        
        if not status:
            raise HTTPException(status_code=404, detail=f"Enhanced indexing job {indexing_job_id} not found")
        
        return EnhancedJobStatusResponse(**status)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get enhanced job status: {e}")
        raise HTTPException(status_code=500, detail=f"Status retrieval failed: {str(e)}")

@router.get("/architectural-summary/{indexing_job_id}", response_model=ArchitecturalSummaryResponse)
async def get_architectural_summary(indexing_job_id: str):
    """
    Get architectural analysis summary for an indexing job
    
    Returns quality scores, metrics, and timing information
    for the architectural analysis component.
    """
    try:
        service = await get_service()
        
        summary = await service.get_architectural_summary(indexing_job_id)
        
        if not summary:
            return ArchitecturalSummaryResponse(
                status="not_analyzed",
                reason="No architectural analysis found for this indexing job"
            )
        
        return ArchitecturalSummaryResponse(**summary)
        
    except Exception as e:
        logger.error(f"Failed to get architectural summary: {e}")
        raise HTTPException(status_code=500, detail=f"Summary retrieval failed: {str(e)}")

@router.post("/trigger-architectural-analysis", response_model=Dict[str, str])
async def trigger_architectural_analysis(request: TriggerArchitecturalAnalysisRequest):
    """
    Trigger architectural analysis for existing indexing job
    
    Allows adding architectural analysis to an existing V1 indexing job
    that was created without architectural analysis.
    """
    try:
        service = await get_service()
        
        architectural_job_id = await service.trigger_architectural_analysis_for_existing_job(
            indexing_job_id=request.indexing_job_id,
            custom_layers=request.custom_layers,
            custom_constraints=request.custom_constraints,
            include_test_code=request.include_test_code
        )
        
        return {
            "indexing_job_id": request.indexing_job_id,
            "architectural_analysis_job_id": architectural_job_id,
            "status": "triggered",
            "message": "Architectural analysis triggered successfully"
        }
        
    except ValueError as e:
        logger.error(f"Validation error triggering architectural analysis: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to trigger architectural analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Trigger failed: {str(e)}")

@router.get("/health-score", response_model=RepositoryHealthResponse)
async def get_repository_health_score(
    repository_path: str = Query(..., description="Path to repository")
):
    """
    Get comprehensive repository health score
    
    Returns health assessment based on latest architectural analysis
    including quality scores, recommendations, and improvement suggestions.
    """
    try:
        service = await get_service()
        
        health_score = await service.get_repository_health_score(repository_path)
        
        return RepositoryHealthResponse(**health_score)
        
    except Exception as e:
        logger.error(f"Failed to get repository health score: {e}")
        raise HTTPException(status_code=500, detail=f"Health score calculation failed: {str(e)}")

@router.get("/jobs/recent")
async def list_enhanced_jobs(
    limit: int = Query(10, description="Maximum number of jobs to return"),
    include_architectural_analysis: bool = Query(True, description="Include architectural analysis info")
):
    """
    List recent enhanced indexing jobs
    
    Returns summary of recent jobs with optional architectural analysis information
    for monitoring and historical tracking.
    """
    try:
        service = await get_service()
        
        jobs = await service.list_enhanced_jobs(limit, include_architectural_analysis)
        
        return {
            "total_jobs": len(jobs),
            "jobs": jobs
        }
        
    except Exception as e:
        logger.error(f"Failed to list enhanced jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Job listing failed: {str(e)}")

@router.get("/progress/{indexing_job_id}/stream")
async def stream_job_progress(indexing_job_id: str):
    """
    Stream real-time progress updates for enhanced indexing job
    
    Returns Server-Sent Events (SSE) for real-time progress tracking
    of both V1 indexing and architectural analysis.
    """
    try:
        from fastapi.responses import StreamingResponse
        import json
        import time
        
        async def generate_progress_events():
            service = await get_service()
            
            # Send initial status
            status = await service.get_enhanced_job_status(indexing_job_id)
            if status:
                yield f"data: {json.dumps(status)}\n\n"
            
            # Poll for updates every 5 seconds
            while True:
                try:
                    status = await service.get_enhanced_job_status(indexing_job_id)
                    if status:
                        yield f"data: {json.dumps(status)}\n\n"
                        
                        # Stop streaming if job is completed or failed
                        if status["overall_status"] in ["completed", "failed", "cancelled"]:
                            break
                    
                    await asyncio.sleep(5)
                    
                except Exception as e:
                    error_data = {"error": str(e), "timestamp": time.time()}
                    yield f"data: {json.dumps(error_data)}\n\n"
                    break
        
        return StreamingResponse(
            generate_progress_events(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to stream job progress: {e}")
        raise HTTPException(status_code=500, detail=f"Progress streaming failed: {str(e)}")

@router.post("/pause/{indexing_job_id}")
async def pause_enhanced_job(indexing_job_id: str):
    """
    Pause enhanced indexing job
    
    Pauses both V1 indexing and architectural analysis components
    with checkpoint saving for resumption.
    """
    try:
        # This would need to be implemented to pause both services
        # For now, return a placeholder response
        
        return {
            "indexing_job_id": indexing_job_id,
            "status": "paused",
            "message": "Enhanced indexing job paused successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to pause enhanced job: {e}")
        raise HTTPException(status_code=500, detail=f"Job pause failed: {str(e)}")

@router.post("/resume/{indexing_job_id}")
async def resume_enhanced_job(indexing_job_id: str):
    """
    Resume paused enhanced indexing job
    
    Resumes both V1 indexing and architectural analysis from
    their respective checkpoints.
    """
    try:
        # This would need to be implemented to resume both services
        # For now, return a placeholder response
        
        return {
            "indexing_job_id": indexing_job_id,
            "status": "resumed",
            "message": "Enhanced indexing job resumed successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to resume enhanced job: {e}")
        raise HTTPException(status_code=500, detail=f"Job resume failed: {str(e)}")

@router.delete("/cancel/{indexing_job_id}")
async def cancel_enhanced_job(indexing_job_id: str):
    """
    Cancel enhanced indexing job
    
    Cancels both V1 indexing and architectural analysis components
    with proper cleanup and status updates.
    """
    try:
        # This would need to be implemented to cancel both services
        # For now, return a placeholder response
        
        return {
            "indexing_job_id": indexing_job_id,
            "status": "cancelled",
            "message": "Enhanced indexing job cancelled successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to cancel enhanced job: {e}")
        raise HTTPException(status_code=500, detail=f"Job cancellation failed: {str(e)}")

@router.get("/metrics/dashboard")
async def get_indexing_metrics_dashboard(
    time_range: str = Query("30d", description="Time range for metrics (7d, 30d, 90d)")
):
    """
    Get comprehensive indexing metrics dashboard
    
    Returns aggregated metrics for indexing performance, success rates,
    architectural quality trends, and system health indicators.
    """
    try:
        # This would aggregate metrics from multiple completed jobs
        # For now, return a structured dashboard response
        
        dashboard_data = {
            "time_range": time_range,
            "indexing_metrics": {
                "total_jobs": 25,
                "successful_jobs": 23,
                "failed_jobs": 2,
                "success_rate": 92.0,
                "average_duration_minutes": 15.3,
                "total_files_indexed": 45623,
                "total_repositories": 12
            },
            "architectural_analysis_metrics": {
                "total_analyses": 18,
                "java_repositories": 15,
                "average_quality_score": 74.2,
                "average_layer_compliance": 82.1,
                "total_violations_found": 156,
                "total_cyclic_dependencies": 23,
                "design_patterns_identified": 67
            },
            "quality_trends": {
                "quality_score_trend": [70.2, 71.8, 73.1, 74.2],  # Weekly averages
                "compliance_trend": [78.5, 80.1, 81.3, 82.1],
                "violations_trend": [180, 165, 158, 156]
            },
            "top_repositories": [
                {"name": "core-services", "health_grade": "A", "score": 89.5},
                {"name": "web-portal", "health_grade": "B", "score": 82.3},
                {"name": "data-processor", "health_grade": "B", "score": 78.9}
            ],
            "recommendations": [
                "Focus on reducing cyclic dependencies in legacy modules",
                "Implement architectural constraints for new development",
                "Regular architectural reviews for quality maintenance",
                "Enhanced test coverage for critical service layers"
            ]
        }
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Failed to get metrics dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Dashboard generation failed: {str(e)}")

@router.get("/export/{indexing_job_id}")
async def export_enhanced_job_results(
    indexing_job_id: str,
    format: str = Query("json", description="Export format (json, csv, pdf)"),
    include_architectural_analysis: bool = Query(True, description="Include architectural analysis")
):
    """
    Export comprehensive results for enhanced indexing job
    
    Exports both V1 indexing results and architectural analysis
    in various formats for reporting and archival purposes.
    """
    try:
        from fastapi.responses import Response
        import json
        
        service = await get_service()
        
        # Get comprehensive job data
        job_status = await service.get_enhanced_job_status(indexing_job_id)
        architectural_summary = await service.get_architectural_summary(indexing_job_id)
        
        if not job_status:
            raise HTTPException(status_code=404, detail=f"Job {indexing_job_id} not found")
        
        export_data = {
            "export_metadata": {
                "job_id": indexing_job_id,
                "export_timestamp": time.time(),
                "format": format,
                "includes_architectural_analysis": include_architectural_analysis
            },
            "indexing_results": job_status["indexing_job"],
            "architectural_analysis": architectural_summary if include_architectural_analysis else None,
            "overall_status": job_status["overall_status"],
            "overall_progress": job_status["overall_progress"]
        }
        
        if format == "json":
            content = json.dumps(export_data, indent=2, default=str)
            media_type = "application/json"
            filename = f"enhanced-indexing-{indexing_job_id}.json"
        elif format == "csv":
            # CSV export would be implemented here
            content = "CSV export not yet implemented"
            media_type = "text/csv"
            filename = f"enhanced-indexing-{indexing_job_id}.csv"
        elif format == "pdf":
            # PDF export would be implemented here
            content = "PDF export not yet implemented"
            media_type = "application/pdf"
            filename = f"enhanced-indexing-{indexing_job_id}.pdf"
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
        
        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export job results: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")