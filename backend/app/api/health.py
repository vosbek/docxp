"""
Health check endpoints for monitoring system status
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime
from typing import Dict, Any
import psutil
import os

from app.core.database import get_session
from app.services.ai_service import AIService
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "DocXP Backend",
        "version": "1.0.0"
    }

@router.get("/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_session)):
    """Comprehensive health check of all services"""
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {},
        "metrics": {}
    }
    
    # API Service Check
    health_status["checks"]["api"] = "healthy"
    
    # Database Check
    try:
        await db.execute(text("SELECT 1"))
        await db.commit()
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # AI Service Check
    try:
        ai_service = AIService()
        # Just check if service initializes properly
        health_status["checks"]["ai_service"] = "healthy" if ai_service else "degraded"
    except Exception as e:
        logger.warning(f"AI service check failed: {e}")
        health_status["checks"]["ai_service"] = f"failed: {str(e)}"
    
    # System Resources
    try:
        # CPU Usage
        cpu_percent = psutil.cpu_percent(interval=1)
        health_status["metrics"]["cpu_usage_percent"] = cpu_percent
        
        # Memory Usage
        memory = psutil.virtual_memory()
        health_status["metrics"]["memory_usage_percent"] = memory.percent
        health_status["metrics"]["memory_available_gb"] = round(memory.available / (1024**3), 2)
        
        # Disk Usage
        disk = psutil.disk_usage('/')
        health_status["metrics"]["disk_usage_percent"] = disk.percent
        health_status["metrics"]["disk_free_gb"] = round(disk.free / (1024**3), 2)
        
        # Process Info
        process = psutil.Process(os.getpid())
        health_status["metrics"]["process_memory_mb"] = round(process.memory_info().rss / (1024**2), 2)
        health_status["metrics"]["process_threads"] = process.num_threads()
        
    except Exception as e:
        logger.error(f"System metrics collection failed: {e}")
        health_status["metrics"]["error"] = str(e)
    
    # Determine overall status
    unhealthy_checks = [k for k, v in health_status["checks"].items() if "unhealthy" in str(v)]
    if unhealthy_checks:
        health_status["status"] = "unhealthy"
    elif any("degraded" in str(v) for v in health_status["checks"].values()):
        health_status["status"] = "degraded"
    
    return health_status

@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_session)):
    """
    Check if application is ready to serve requests
    Used by load balancers and orchestrators
    """
    try:
        # Check database connectivity
        await db.execute(text("SELECT 1"))
        await db.commit()
        
        # Check if critical directories exist
        required_dirs = ["output", "temp", "logs"]
        for dir_name in required_dirs:
            if not os.path.exists(dir_name):
                return {
                    "ready": False,
                    "reason": f"Required directory {dir_name} not found"
                }
        
        return {"ready": True, "timestamp": datetime.utcnow().isoformat()}
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {
            "ready": False,
            "reason": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/live")
async def liveness_check():
    """
    Simple liveness check
    Used to detect if the application is still running
    """
    return {"alive": True, "timestamp": datetime.utcnow().isoformat()}
