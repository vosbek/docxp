"""
Database configuration and initialization
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, Boolean, Text
from datetime import datetime
import json

from app.core.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True
)

# Create async session
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Create base class for models
Base = declarative_base()

# Database models
class DocumentationJob(Base):
    """Documentation generation job with enhanced progress tracking"""
    __tablename__ = "documentation_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, unique=True, index=True)
    repository_path = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Configuration
    config = Column(JSON, nullable=False)
    
    # Enhanced Progress Tracking
    progress_percentage = Column(Integer, default=0)  # 0-100
    current_step = Column(String, nullable=True)  # Current step key
    step_description = Column(String, nullable=True)  # Human-readable step description
    progress_data = Column(JSON, nullable=True)  # Detailed progress information
    
    # Results
    entities_count = Column(Integer, default=0)
    business_rules_count = Column(Integer, default=0)
    files_processed = Column(Integer, default=0)
    output_path = Column(String, nullable=True)
    
    # Metrics
    processing_time_seconds = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)

class Repository(Base):
    """Repository information"""
    __tablename__ = "repositories"
    
    id = Column(Integer, primary_key=True, index=True)
    path = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    last_analyzed = Column(DateTime, nullable=True)
    
    # Statistics
    total_files = Column(Integer, default=0)
    total_lines = Column(Integer, default=0)
    languages = Column(JSON, default=list)
    
    # Metadata
    git_remote = Column(String, nullable=True)
    last_commit = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class ConfigurationTemplate(Base):
    """Saved configuration templates"""
    __tablename__ = "configuration_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=True)
    config = Column(JSON, nullable=False)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

# Database initialization
async def init_db():
    """Initialize database"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_session() -> AsyncSession:
    """Get database session"""
    async with AsyncSessionLocal() as session:
        yield session
