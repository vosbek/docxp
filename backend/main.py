"""
DocXP - AI-Powered Documentation Generation System
Main FastAPI Application
"""

# CRITICAL: Load environment BEFORE any other imports
import os
from pathlib import Path

def _load_env_enterprise_immediately():
    """Load .env.enterprise file IMMEDIATELY before any other imports"""
    env_file = Path(__file__).parent / ".env.enterprise"
    
    if env_file.exists():
        print(f"MAIN.PY: Loading environment from {env_file}")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or line.startswith('REM'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    # Handle Windows path variables
                    if '%USERNAME%' in value:
                        username = os.getenv('USERNAME', os.getenv('USER', 'hairsm2'))
                        value = value.replace('%USERNAME%', username)
                    os.environ[key] = value
        
        # Verify critical variables loaded
        aws_profile = os.getenv('AWS_PROFILE')
        aws_region = os.getenv('AWS_REGION')
        database_url = os.getenv('DATABASE_URL')
        print(f"MAIN.PY: Environment loaded - AWS_PROFILE={aws_profile}, AWS_REGION={aws_region}")
        print(f"MAIN.PY: DATABASE_URL starts with: {database_url[:50] if database_url else 'None'}...")
    else:
        print(f"MAIN.PY: ERROR - .env.enterprise not found at {env_file}")

# Load environment FIRST - before any other imports
_load_env_enterprise_immediately()

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from pathlib import Path
import time
import uuid

from app.api import documentation, repositories, analytics, configuration, health, aws_configuration, semantic_search, repository_processing, strands_agents, hybrid_search, v1_indexing
from app.api.v1 import enhanced_indexing, jqassistant, semgrep
from app.core.config import settings
from app.core.startup import application_lifespan, get_application_state
from app.core.logging_config import setup_logging, get_logger
from app.core.error_handlers import register_exception_handlers

# Setup enhanced logging
setup_logging(
    log_level=settings.LOG_LEVEL if hasattr(settings, 'LOG_LEVEL') else "INFO",
    log_file="logs/docxp.log"
)
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    async with application_lifespan() as app_state:
        # Store application state in app for access in endpoints
        app.state.docxp_state = app_state
        yield

# Create FastAPI application
app = FastAPI(
    title="DocXP API",
    description="AI-Powered Documentation Generation System",
    version="1.0.0",
    lifespan=lifespan
)

# Register exception handlers
register_exception_handlers(app)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:4201", "http://localhost:80", "http://localhost"],  # Angular dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request tracking middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID to all requests for tracking"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Log request
    logger.info(
        f"Request started: {request.method} {request.url.path}",
        extra={"request_id": request_id}
    )
    
    # Time the request
    start_time = time.time()
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Add headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        
        # Log response
        logger.info(
            f"Request completed: {response.status_code}",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "duration": process_time
            }
        )
        
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"Request failed: {str(e)}",
            extra={
                "request_id": request_id,
                "duration": process_time
            },
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "request_id": request_id,
                "message": "An unexpected error occurred"
            }
        )

# Include API routers
app.include_router(
    health.router,
    prefix="/health",
    tags=["Health"]
)

app.include_router(
    documentation.router,
    prefix="/api/documentation",
    tags=["Documentation"]
)

app.include_router(
    repositories.router,
    prefix="/api/repositories",
    tags=["Repositories"]
)

app.include_router(
    analytics.router,
    prefix="/api/analytics",
    tags=["Analytics"]
)

app.include_router(
    configuration.router,
    prefix="/api/configuration",
    tags=["Configuration"]
)

app.include_router(
    aws_configuration.router,
    prefix="/api/configuration/aws",
    tags=["AWS Configuration"]
)

# Semantic Search API
app.include_router(
    semantic_search.router,
    prefix="/api/semantic",
    tags=["Semantic Search & AI"]
)

# Repository Processing API
app.include_router(
    repository_processing.router,
    prefix="/api/repositories",
    tags=["Repository Processing"]
)

# Strands Agents API
app.include_router(
    strands_agents.router,
    prefix="/api/strands",
    tags=["Strands Agents"]
)

# V1 Hybrid Search API (RRF BM25 + k-NN)
app.include_router(
    hybrid_search.router,
    prefix="/api",
    tags=["V1 Hybrid Search"]
)

# V1 Indexing API (Enterprise-Grade Fault-Tolerant)
app.include_router(
    v1_indexing.router,
    prefix="/api",
    tags=["V1 Indexing"]
)

# V1 Enhanced Indexing API (with jQAssistant Integration)
app.include_router(
    enhanced_indexing.router,
    prefix="/api/v1",
    tags=["Enhanced V1 Indexing"]
)

# V1 jQAssistant Architecture Analysis API
app.include_router(
    jqassistant.router,
    prefix="/api/v1",
    tags=["Architecture Analysis"]
)

# V1 Semgrep Static Analysis API
app.include_router(
    semgrep.router,
    prefix="/api/v1",
    tags=["Static Analysis"]
)

# Serve static files (generated documentation)
app.mount("/output", StaticFiles(directory="output"), name="output")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "application": "DocXP",
        "version": "1.0.0",
        "status": "operational",
        "description": "AI-Powered Documentation Generation System"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=False,  # Disable reload to prevent watchfiles spam
        reload_dirs=[],  # Explicitly disable directory watching
        use_colors=False,  # Reduce log noise
        log_level="info"
    )
