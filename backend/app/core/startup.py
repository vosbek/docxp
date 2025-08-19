"""
Application Startup and Lifecycle Management

This module provides a comprehensive startup sequence that:
1. Eliminates import-time initialization issues
2. Provides proper error handling and graceful degradation
3. Ensures services are initialized in the correct order
4. Creates required directories and resources
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db
from app.core.opensearch_setup import initialize_opensearch, cleanup_opensearch
from app.core.logging_config import setup_logging, get_logger, force_sqlalchemy_silence

logger = get_logger(__name__)

class ApplicationState:
    """Manages application state and service availability"""
    
    def __init__(self):
        self.database_available: bool = False
        self.opensearch_available: bool = False
        self.directories_created: bool = False
        self.services_initialized: bool = False
        self.startup_errors: list = []
        
    def add_error(self, service: str, error: Exception):
        """Add a startup error for tracking"""
        self.startup_errors.append({
            "service": service,
            "error": str(error),
            "type": type(error).__name__
        })
        logger.error(f"Service {service} failed to initialize: {error}")
        
    def is_healthy(self) -> bool:
        """Check if application is in a healthy state"""
        # Application is healthy if core services are available
        return self.database_available and self.directories_created
        
    def get_status(self) -> Dict[str, Any]:
        """Get detailed application status"""
        return {
            "healthy": self.is_healthy(),
            "database_available": self.database_available,
            "opensearch_available": self.opensearch_available,
            "directories_created": self.directories_created,
            "services_initialized": self.services_initialized,
            "startup_errors": self.startup_errors
        }

# Global application state
app_state = ApplicationState()

def create_required_directories() -> bool:
    """Create required application directories"""
    try:
        directories = [
            settings.OUTPUT_DIR,
            settings.TEMP_DIR,
            settings.CONFIGS_DIR,
            "logs"  # For log files
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logger.debug(f"Directory ensured: {directory}")
            
        app_state.directories_created = True
        logger.info("✅ Required directories created")
        return True
        
    except Exception as e:
        app_state.add_error("directories", e)
        return False

async def initialize_database() -> bool:
    """Initialize database with proper error handling"""
    try:
        await init_db()
        app_state.database_available = True
        logger.info("✅ Database initialized")
        return True
        
    except Exception as e:
        app_state.add_error("database", e)
        return False

async def initialize_search_engine() -> bool:
    """Initialize OpenSearch with graceful degradation"""
    try:
        success = await initialize_opensearch()
        if success:
            app_state.opensearch_available = True
            logger.info("✅ OpenSearch search engine initialized")
        else:
            logger.warning("⚠️  OpenSearch initialization failed - search functionality will be limited")
        return success
        
    except Exception as e:
        app_state.add_error("opensearch", e)
        logger.warning(f"⚠️  OpenSearch error: {e} - search functionality will be limited")
        return False

async def initialize_optional_services() -> bool:
    """Initialize optional services that can fail gracefully"""
    success_count = 0
    total_services = 1  # OpenSearch is currently the only optional service
    
    # OpenSearch initialization
    if await initialize_search_engine():
        success_count += 1
    
    # Future: Add other optional services here (Redis, Neo4j, etc.)
    
    return success_count > 0  # At least some optional services should work

async def startup_sequence() -> bool:
    """Complete application startup sequence"""
    logger.info("🚀 Starting DocXP Backend initialization...")
    
    # Step 1: Create required directories (critical)
    if not create_required_directories():
        logger.error("❌ Failed to create required directories - startup aborted")
        return False
    
    # Step 2: Initialize database (critical)
    if not await initialize_database():
        logger.error("❌ Database initialization failed - startup aborted")
        return False
    
    # Step 3: Force SQLAlchemy to be quiet after database initialization
    force_sqlalchemy_silence()
    
    # Step 4: Initialize optional services (non-critical)
    await initialize_optional_services()
    
    # Mark services as initialized
    app_state.services_initialized = True
    
    # Log final status
    status = app_state.get_status()
    if status["healthy"]:
        logger.info("✅ DocXP Backend startup completed successfully")
        if status["startup_errors"]:
            logger.warning(f"⚠️  {len(status['startup_errors'])} non-critical services failed to initialize")
    else:
        logger.error("❌ DocXP Backend startup completed with critical errors")
    
    return status["healthy"]

async def shutdown_sequence():
    """Clean shutdown sequence"""
    logger.info("🛑 Starting DocXP Backend shutdown...")
    
    try:
        # Cleanup OpenSearch
        await cleanup_opensearch()
        logger.info("✅ OpenSearch resources cleaned up")
        
        # Future: Add cleanup for other services here
        
        logger.info("✅ DocXP Backend shutdown completed")
        
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")

@asynccontextmanager
async def application_lifespan():
    """Application lifespan context manager for FastAPI"""
    try:
        # Startup
        startup_success = await startup_sequence()
        if not startup_success:
            logger.error("Application startup failed - some functionality may be limited")
        
        yield app_state
        
    finally:
        # Shutdown
        await shutdown_sequence()

def get_application_state() -> ApplicationState:
    """Get current application state"""
    return app_state

def require_service(service_name: str) -> bool:
    """Check if a service is available, log warning if not"""
    status = app_state.get_status()
    
    service_map = {
        "database": status["database_available"],
        "opensearch": status["opensearch_available"],
        "search": status["opensearch_available"]  # Alias
    }
    
    if service_name in service_map:
        if not service_map[service_name]:
            logger.warning(f"Service '{service_name}' is not available")
        return service_map[service_name]
    
    logger.error(f"Unknown service '{service_name}' requested")
    return False