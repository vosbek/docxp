"""
DocXP - AI-Powered Documentation Generation System
Main FastAPI Application
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
from pathlib import Path

from app.api import documentation, repositories, analytics, configuration
from app.core.config import settings
from app.core.database import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info("Starting DocXP Backend...")
    await init_db()
    logger.info("Database initialized")
    
    # Create necessary directories
    Path(settings.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.TEMP_DIR).mkdir(parents=True, exist_ok=True)
    
    yield
    
    # Shutdown
    logger.info("Shutting down DocXP Backend...")

# Create FastAPI application
app = FastAPI(
    title="DocXP API",
    description="AI-Powered Documentation Generation System",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # Angular dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
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
        port=8000,
        reload=True,
        log_level="info"
    )
