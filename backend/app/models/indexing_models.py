"""
V1 Indexing Database Models - Enterprise-Grade Job Tracking and Persistence

Fixes the critical issue: "'CodeEntityData' object has no attribute 'entity_metadata'"

Features:
- Job tracking with checkpoints and resume capability
- File-level processing status and error tracking
- Repository metadata and indexing statistics
- Embedding cache for cost optimization
- Enhanced CodeEntityData with entity_metadata attribute
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base

# Enums for type safety
class JobType(str, Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    SELECTIVE = "selective"

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class FileStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class ProcessingError(str, Enum):
    PARSE_ERROR = "parse_error"
    EMBEDDING_ERROR = "embedding_error"
    INDEX_ERROR = "index_error"
    AWS_ERROR = "aws_error"
    TIMEOUT_ERROR = "timeout_error"
    UNKNOWN_ERROR = "unknown_error"

class ProcessingStage(str, Enum):
    INGEST = "ingest"
    EMBED = "embed"
    INDEX = "index"

class IndexingJob(Base):
    """
    Main indexing job tracking with checkpoints and resume capability
    
    Supports full, incremental, and selective indexing with fault tolerance
    """
    __tablename__ = "indexing_jobs"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Job configuration
    repository_path = Column(String(1000), nullable=False, index=True)
    job_type = Column(String(20), nullable=False, default=JobType.FULL.value)
    status = Column(String(20), nullable=False, default=JobStatus.PENDING.value, index=True)
    
    # File filtering
    file_patterns = Column(JSON, nullable=True)  # ["*.java", "*.jsp"]
    exclude_patterns = Column(JSON, nullable=True)  # ["**/test/**"]
    force_reindex = Column(Boolean, default=False)
    
    # Progress tracking
    total_files = Column(Integer, default=0)
    processed_files = Column(Integer, default=0)
    failed_files = Column(Integer, default=0)
    skipped_files = Column(Integer, default=0)
    progress_percentage = Column(Float, default=0.0)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Performance metrics
    success_rate = Column(Float, nullable=True)
    average_processing_time_per_file = Column(Float, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Checkpoint data for resume capability
    checkpoint_data = Column(JSON, nullable=True)
    last_processed_file = Column(String(1000), nullable=True)
    processing_order = Column(JSON, nullable=True)  # For deterministic resume
    
    # Relationships
    file_records = relationship("FileProcessingRecord", back_populates="job", cascade="all, delete-orphan")
    repository_snapshots = relationship("RepositorySnapshot", back_populates="job")
    
    __table_args__ = (
        Index('idx_job_status_created', 'status', 'created_at'),
        Index('idx_job_repo_type', 'repository_path', 'job_type'),
    )

class FileProcessingRecord(Base):
    """
    File-level processing status and error tracking
    
    Tracks individual file processing for error isolation and progress monitoring
    """
    __tablename__ = "file_processing_records"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    job_id = Column(UUID(as_uuid=True), ForeignKey('indexing_jobs.id'), nullable=False, index=True)
    
    # File identification
    repository_path = Column(String(1000), nullable=False, index=True)
    file_path = Column(String(2000), nullable=False, index=True)
    file_hash = Column(String(64), nullable=True)  # SHA-256 for change detection
    
    # Processing status
    status = Column(String(20), nullable=False, default=FileStatus.PENDING.value, index=True)
    
    # Processing results
    entities_extracted = Column(Integer, default=0)
    embeddings_generated = Column(Integer, default=0)
    processing_duration = Column(Float, nullable=True)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    error_type = Column(String(50), nullable=True)
    retry_count = Column(Integer, default=0)
    skip_reason = Column(String(200), nullable=True)
    
    # Relationships
    job = relationship("IndexingJob", back_populates="file_records")
    
    __table_args__ = (
        Index('idx_file_job_status', 'job_id', 'status'),
        Index('idx_file_repo_path', 'repository_path', 'file_path'),
    )

class RepositorySnapshot(Base):
    """
    Repository metadata and indexing statistics
    
    Captures repository state at job completion for historical tracking
    """
    __tablename__ = "repository_snapshots"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    job_id = Column(UUID(as_uuid=True), ForeignKey('indexing_jobs.id'), nullable=False, index=True)
    
    # Repository information
    repository_path = Column(String(1000), nullable=False, index=True)
    completion_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # File statistics
    total_files = Column(Integer, default=0)
    processed_files = Column(Integer, default=0)
    failed_files = Column(Integer, default=0)
    skipped_files = Column(Integer, default=0)
    
    # Content statistics
    total_lines_of_code = Column(Integer, default=0)
    total_entities_extracted = Column(Integer, default=0)
    language_distribution = Column(JSON, nullable=True)  # {"java": 150, "jsp": 30}
    
    # Performance metrics
    processing_duration_seconds = Column(Float, nullable=False)
    success_rate = Column(Float, nullable=False)
    average_processing_time_per_file = Column(Float, nullable=False)
    
    # Quality metrics
    error_rate = Column(Float, default=0.0)
    common_error_types = Column(JSON, nullable=True)
    
    # Cost tracking
    estimated_embedding_cost_usd = Column(Float, default=0.0)
    embeddings_cached_count = Column(Integer, default=0)
    cost_savings_usd = Column(Float, default=0.0)
    
    # Relationships
    job = relationship("IndexingJob", back_populates="repository_snapshots")
    
    __table_args__ = (
        Index('idx_snapshot_repo_time', 'repository_path', 'completion_time'),
    )

class EmbeddingCache(Base):
    """
    Embedding cache for cost optimization
    
    Content-based caching using SHA-256 hashes for 50%+ cost reduction
    """
    __tablename__ = "embedding_cache"

    # Primary key - content hash
    content_hash = Column(String(64), primary_key=True)  # SHA-256
    
    # Embedding data
    embedding = Column(JSON, nullable=False)  # List of floats
    model = Column(String(100), nullable=False, index=True)
    dimensions = Column(Integer, nullable=False)
    
    # Usage tracking
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_accessed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    hit_count = Column(Integer, default=0)
    
    # Cost tracking
    estimated_generation_cost_usd = Column(Float, default=0.0001)
    total_savings_usd = Column(Float, default=0.0)
    
    __table_args__ = (
        Index('idx_embedding_model_access', 'model', 'last_accessed_at'),
        Index('idx_embedding_created', 'created_at'),
    )

class CodeEntityData(Base):
    """
    Enhanced code entity data with entity_metadata attribute
    
    FIXES: "'CodeEntityData' object has no attribute 'entity_metadata'"
    """
    __tablename__ = "code_entity_data"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Entity identification
    entity_id = Column(String(100), nullable=False, index=True)
    name = Column(String(500), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)
    
    # File location
    file_path = Column(String(2000), nullable=False, index=True)
    repository_path = Column(String(1000), nullable=False, index=True)
    start_line = Column(Integer, nullable=True)
    end_line = Column(Integer, nullable=True)
    
    # Content
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False, index=True)
    
    # Embeddings for hybrid search
    embedding = Column(JSON, nullable=True)  # Vector embedding
    keywords = Column(ARRAY(String), nullable=True)  # Keywords for BM25
    
    # CRITICAL: Fixed missing attribute
    entity_metadata = Column(JSON, nullable=True)  # Additional metadata
    
    # Quality and relevance
    quality_score = Column(Float, default=0.0)
    relevance_score = Column(Float, default=0.0)
    business_rule_indicator = Column(Boolean, default=False)
    
    # Version tracking
    commit_hash = Column(String(40), nullable=True)
    language = Column(String(20), nullable=True, index=True)
    framework = Column(String(50), nullable=True)
    
    # Indexing metadata
    indexed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    indexed_by_job = Column(UUID(as_uuid=True), nullable=True)
    
    __table_args__ = (
        Index('idx_entity_file_type', 'file_path', 'entity_type'),
        Index('idx_entity_repo_commit', 'repository_path', 'commit_hash'),
        Index('idx_entity_content_hash', 'content_hash'),
    )

class IndexingHealthMetrics(Base):
    """
    System health monitoring and metrics
    
    Tracks performance, cost, and error rates for monitoring
    """
    __tablename__ = "indexing_health_metrics"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Time period
    metric_date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    time_bucket = Column(String(20), nullable=False)  # 'hourly', 'daily', 'weekly'
    
    # Performance metrics
    total_jobs = Column(Integer, default=0)
    successful_jobs = Column(Integer, default=0)
    failed_jobs = Column(Integer, default=0)
    average_job_duration_seconds = Column(Float, default=0.0)
    
    # Processing metrics
    total_files_processed = Column(Integer, default=0)
    total_entities_extracted = Column(Integer, default=0)
    average_processing_time_per_file = Column(Float, default=0.0)
    
    # Error metrics
    error_rate_percentage = Column(Float, default=0.0)
    common_error_types = Column(JSON, nullable=True)
    
    # Cost metrics
    total_embedding_requests = Column(Integer, default=0)
    cache_hit_rate_percentage = Column(Float, default=0.0)
    estimated_cost_savings_usd = Column(Float, default=0.0)
    
    # Repository metrics
    unique_repositories = Column(Integer, default=0)
    repositories_processed = Column(JSON, nullable=True)  # List of repo paths
    
    __table_args__ = (
        Index('idx_health_date_bucket', 'metric_date', 'time_bucket'),
    )

# Database views for common queries
def create_indexing_views():
    """
    Create helpful database views for common indexing queries
    """
    views = [
        # Active jobs view
        """
        CREATE OR REPLACE VIEW active_indexing_jobs AS
        SELECT 
            id,
            repository_path,
            job_type,
            status,
            progress_percentage,
            started_at,
            (processed_files + failed_files + skipped_files) as total_processed,
            total_files,
            CASE 
                WHEN total_files > 0 THEN 
                    ROUND((processed_files::float / total_files * 100)::numeric, 2)
                ELSE 0 
            END as completion_percentage
        FROM indexing_jobs 
        WHERE status IN ('pending', 'running', 'paused');
        """,
        
        # Job performance summary
        """
        CREATE OR REPLACE VIEW job_performance_summary AS
        SELECT 
            j.id,
            j.repository_path,
            j.status,
            j.duration_seconds,
            j.success_rate,
            COUNT(f.id) as total_file_records,
            COUNT(CASE WHEN f.status = 'completed' THEN 1 END) as completed_files,
            COUNT(CASE WHEN f.status = 'failed' THEN 1 END) as failed_files,
            AVG(f.processing_duration) as avg_file_processing_time
        FROM indexing_jobs j
        LEFT JOIN file_processing_records f ON j.id = f.job_id
        GROUP BY j.id, j.repository_path, j.status, j.duration_seconds, j.success_rate;
        """,
        
        # Repository indexing history
        """
        CREATE OR REPLACE VIEW repository_indexing_history AS
        SELECT 
            rs.repository_path,
            COUNT(rs.id) as total_indexing_runs,
            MAX(rs.completion_time) as last_indexed,
            AVG(rs.success_rate) as average_success_rate,
            SUM(rs.processed_files) as total_files_ever_processed,
            SUM(rs.cost_savings_usd) as total_cost_savings
        FROM repository_snapshots rs
        GROUP BY rs.repository_path
        ORDER BY last_indexed DESC;
        """
    ]
    
    return views

class JobFileState(Base):
    """
    Relational checkpoint tracking for deterministic resume capability
    
    Replaces JSON-based checkpoint data with proper relational structure
    as recommended for 10k+ file scalability
    """
    __tablename__ = "job_file_state"

    # Primary key - composite key for uniqueness
    job_id = Column(UUID(as_uuid=True), ForeignKey('indexing_jobs.id'), primary_key=True)
    path = Column(String(2000), primary_key=True)
    commit = Column(String(40), primary_key=True)
    
    # Processing state
    status = Column(String(20), nullable=False, default=FileStatus.PENDING.value, index=True)
    last_stage = Column(String(20), nullable=True)  # ingest, embed, index
    last_offset = Column(Integer, default=0)  # For resuming within large files
    
    # Error tracking
    error = Column(Text, nullable=True)
    error_class = Column(String(100), nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Processing metadata
    entities_extracted = Column(Integer, default=0)
    embeddings_generated = Column(Integer, default=0)
    indexed_entities = Column(Integer, default=0)
    processing_duration = Column(Float, nullable=True)
    
    # File metadata for deduplication
    file_size = Column(Integer, nullable=True)
    file_hash = Column(String(64), nullable=True)  # For content-based deduplication
    
    # Relationships
    job = relationship("IndexingJob", back_populates="file_states")
    
    __table_args__ = (
        Index('idx_job_file_status', 'job_id', 'status'),
        Index('idx_job_file_stage', 'job_id', 'last_stage'),
        Index('idx_file_hash_dedup', 'file_hash', 'commit'),
    )

class DeadLetterQueue(Base):
    """
    Dead Letter Queue for hard failures after max retries
    
    Stores files that cannot be processed for analysis and manual intervention
    """
    __tablename__ = "dead_letter_queue"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Job context
    job_id = Column(UUID(as_uuid=True), ForeignKey('indexing_jobs.id'), nullable=False, index=True)
    path = Column(String(2000), nullable=False)
    commit = Column(String(40), nullable=False)
    
    # Failure context
    stage = Column(String(20), nullable=False, index=True)  # ingest, embed, index
    error_class = Column(String(100), nullable=False, index=True)
    error = Column(Text, nullable=False)
    
    # Retry history
    retry_count = Column(Integer, default=0)
    first_failure_at = Column(DateTime, nullable=False)
    last_retry_at = Column(DateTime, nullable=True)
    
    # Created timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Manual resolution tracking
    resolved = Column(Boolean, default=False, index=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(100), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Relationships
    job = relationship("IndexingJob")
    
    __table_args__ = (
        Index('idx_dlq_job_stage', 'job_id', 'stage'),
        Index('idx_dlq_error_class', 'error_class', 'created_at'),
        Index('idx_dlq_unresolved', 'resolved', 'created_at'),
    )

# Add relationship to IndexingJob
IndexingJob.file_states = relationship("JobFileState", back_populates="job", cascade="all, delete-orphan")

# =============================================================================
# jQAssistant Architecture Analysis Models
# =============================================================================

class ArchitecturalAnalysisJob(Base):
    """
    jQAssistant architectural analysis job tracking
    
    Extends the V1 indexing system with architectural analysis capabilities
    """
    __tablename__ = "architectural_analysis_jobs"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Link to main indexing job
    indexing_job_id = Column(UUID(as_uuid=True), ForeignKey('indexing_jobs.id'), nullable=True, index=True)
    
    # Repository information
    repository_path = Column(String(1000), nullable=False, index=True)
    repository_id = Column(String(200), nullable=False, index=True)
    commit_hash = Column(String(40), nullable=False, index=True)
    
    # Analysis configuration
    include_test_code = Column(Boolean, default=False)
    custom_layers = Column(JSON, nullable=True)  # Custom architectural layer definitions
    custom_constraints = Column(JSON, nullable=True)  # Additional constraint rules
    
    # Analysis status
    status = Column(String(20), nullable=False, default=JobStatus.PENDING.value, index=True)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    analysis_duration_seconds = Column(Float, nullable=True)
    
    # Results summary
    total_packages = Column(Integer, default=0)
    total_classes = Column(Integer, default=0)
    total_methods = Column(Integer, default=0)
    total_dependencies = Column(Integer, default=0)
    cyclic_dependencies_count = Column(Integer, default=0)
    architectural_violations_count = Column(Integer, default=0)
    
    # Quality scores
    overall_quality_score = Column(Float, default=0.0)
    layer_compliance_score = Column(Float, default=0.0)
    architectural_debt_score = Column(Float, default=0.0)
    
    # Neo4j statistics
    neo4j_nodes_created = Column(Integer, default=0)
    neo4j_relationships_created = Column(Integer, default=0)
    
    # Configuration used
    rules_applied = Column(JSON, nullable=True)
    constraints_checked = Column(JSON, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    
    # Relationships
    indexing_job = relationship("IndexingJob", backref="architectural_analysis")
    package_dependencies = relationship("PackageDependency", back_populates="analysis_job", cascade="all, delete-orphan")
    architectural_violations = relationship("ArchitecturalViolation", back_populates="analysis_job", cascade="all, delete-orphan")
    design_patterns = relationship("DesignPattern", back_populates="analysis_job", cascade="all, delete-orphan")
    dead_code_elements = relationship("DeadCodeElement", back_populates="analysis_job", cascade="all, delete-orphan")
    code_metrics = relationship("CodeMetrics", back_populates="analysis_job", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_arch_repo_commit', 'repository_id', 'commit_hash'),
        Index('idx_arch_status_created', 'status', 'created_at'),
    )

class PackageDependency(Base):
    """
    Package dependency relationships extracted by jQAssistant
    
    Represents dependencies between Java packages for visualization and analysis
    """
    __tablename__ = "package_dependencies"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key to analysis job
    analysis_job_id = Column(UUID(as_uuid=True), ForeignKey('architectural_analysis_jobs.id'), nullable=False, index=True)
    
    # Dependency information
    source_package = Column(String(500), nullable=False, index=True)
    target_package = Column(String(500), nullable=False, index=True)
    dependency_type = Column(String(50), nullable=False, default='DEPENDS_ON')
    
    # Dependency metrics
    weight = Column(Integer, default=1)  # Number of dependencies
    files_involved = Column(JSON, nullable=True)  # List of files creating the dependency
    
    # Dependency analysis
    is_cyclic = Column(Boolean, default=False, index=True)
    violation_type = Column(String(100), nullable=True)  # Type of architectural violation
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    analysis_job = relationship("ArchitecturalAnalysisJob", back_populates="package_dependencies")
    
    __table_args__ = (
        Index('idx_pkg_dep_source_target', 'source_package', 'target_package'),
        Index('idx_pkg_dep_cyclic', 'is_cyclic', 'analysis_job_id'),
        Index('idx_pkg_dep_violation', 'violation_type', 'analysis_job_id'),
    )

class ArchitecturalViolation(Base):
    """
    Architectural constraint violations detected by jQAssistant
    
    Stores violations of architectural rules and design constraints
    """
    __tablename__ = "architectural_violations"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key to analysis job
    analysis_job_id = Column(UUID(as_uuid=True), ForeignKey('architectural_analysis_jobs.id'), nullable=False, index=True)
    
    # Violation details
    violation_type = Column(String(100), nullable=False, index=True)  # 'LAYER_VIOLATION', 'CYCLIC_DEPENDENCY', etc.
    severity = Column(String(20), nullable=False, index=True)  # 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    
    # Elements involved
    source_element = Column(String(1000), nullable=False)
    target_element = Column(String(1000), nullable=False)
    
    # Constraint information
    constraint_violated = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    fix_suggestion = Column(Text, nullable=True)
    
    # Location information
    file_path = Column(String(2000), nullable=True)
    line_number = Column(Integer, nullable=True)
    
    # Resolution tracking
    is_resolved = Column(Boolean, default=False, index=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(100), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    analysis_job = relationship("ArchitecturalAnalysisJob", back_populates="architectural_violations")
    
    __table_args__ = (
        Index('idx_violation_type_severity', 'violation_type', 'severity'),
        Index('idx_violation_resolved', 'is_resolved', 'analysis_job_id'),
        Index('idx_violation_constraint', 'constraint_violated', 'analysis_job_id'),
    )

class DesignPattern(Base):
    """
    Design patterns detected by jQAssistant analysis
    
    Stores information about identified design patterns in the codebase
    """
    __tablename__ = "design_patterns"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key to analysis job
    analysis_job_id = Column(UUID(as_uuid=True), ForeignKey('architectural_analysis_jobs.id'), nullable=False, index=True)
    
    # Pattern information
    pattern_name = Column(String(100), nullable=False, index=True)
    pattern_type = Column(String(50), nullable=False, index=True)  # 'CREATIONAL', 'STRUCTURAL', 'BEHAVIORAL'
    confidence = Column(Float, nullable=False)  # 0.0 - 1.0
    
    # Pattern details
    participants = Column(JSON, nullable=False)  # List of classes/interfaces involved
    description = Column(Text, nullable=False)
    benefits = Column(JSON, nullable=True)  # List of benefits
    location = Column(String(500), nullable=False)  # Package or module location
    
    # Quality assessment
    implementation_quality = Column(String(20), nullable=True)  # 'EXCELLENT', 'GOOD', 'FAIR', 'POOR'
    improvement_suggestions = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    analysis_job = relationship("ArchitecturalAnalysisJob", back_populates="design_patterns")
    
    __table_args__ = (
        Index('idx_pattern_name_type', 'pattern_name', 'pattern_type'),
        Index('idx_pattern_confidence', 'confidence', 'analysis_job_id'),
    )

class DeadCodeElement(Base):
    """
    Dead/unused code elements identified by jQAssistant
    
    Tracks unused classes, methods, and fields for cleanup recommendations
    """
    __tablename__ = "dead_code_elements"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key to analysis job
    analysis_job_id = Column(UUID(as_uuid=True), ForeignKey('architectural_analysis_jobs.id'), nullable=False, index=True)
    
    # Element information
    element_type = Column(String(50), nullable=False, index=True)  # 'CLASS', 'METHOD', 'FIELD', 'INTERFACE'
    element_name = Column(String(1000), nullable=False, index=True)
    fully_qualified_name = Column(String(2000), nullable=False)
    
    # Location information
    file_path = Column(String(2000), nullable=False)
    line_number = Column(Integer, nullable=True)
    
    # Analysis results
    reason = Column(Text, nullable=False)  # Why it's considered dead
    potential_impact = Column(String(20), nullable=False, index=True)  # 'LOW', 'MEDIUM', 'HIGH'
    removal_suggestion = Column(Text, nullable=False)
    
    # Verification status
    is_verified_dead = Column(Boolean, default=False, index=True)
    verification_notes = Column(Text, nullable=True)
    
    # Cleanup status
    is_removed = Column(Boolean, default=False, index=True)
    removed_at = Column(DateTime, nullable=True)
    removed_by = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    analysis_job = relationship("ArchitecturalAnalysisJob", back_populates="dead_code_elements")
    
    __table_args__ = (
        Index('idx_dead_code_type_impact', 'element_type', 'potential_impact'),
        Index('idx_dead_code_verified', 'is_verified_dead', 'analysis_job_id'),
        Index('idx_dead_code_removed', 'is_removed', 'analysis_job_id'),
    )

class CodeMetrics(Base):
    """
    Code quality metrics calculated by jQAssistant
    
    Stores comprehensive metrics for packages, classes, and methods
    """
    __tablename__ = "code_metrics"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key to analysis job
    analysis_job_id = Column(UUID(as_uuid=True), ForeignKey('architectural_analysis_jobs.id'), nullable=False, index=True)
    
    # Scope of metrics
    scope_type = Column(String(20), nullable=False, index=True)  # 'REPOSITORY', 'PACKAGE', 'CLASS', 'METHOD'
    scope_name = Column(String(1000), nullable=False, index=True)
    
    # Complexity metrics
    cyclomatic_complexity = Column(Float, nullable=True)
    cognitive_complexity = Column(Float, nullable=True)
    npath_complexity = Column(Float, nullable=True)
    
    # Size metrics
    lines_of_code = Column(Integer, nullable=True)
    lines_of_comments = Column(Integer, nullable=True)
    number_of_methods = Column(Integer, nullable=True)
    number_of_fields = Column(Integer, nullable=True)
    number_of_classes = Column(Integer, nullable=True)
    
    # Coupling metrics
    afferent_coupling = Column(Integer, nullable=True)  # Incoming dependencies
    efferent_coupling = Column(Integer, nullable=True)  # Outgoing dependencies
    instability = Column(Float, nullable=True)  # I = Ce / (Ca + Ce)
    
    # Cohesion metrics
    lack_of_cohesion = Column(Float, nullable=True)
    cohesion_among_methods = Column(Float, nullable=True)
    
    # Inheritance metrics
    depth_of_inheritance = Column(Integer, nullable=True)
    number_of_children = Column(Integer, nullable=True)
    
    # Quality scores
    maintainability_index = Column(Float, nullable=True)
    technical_debt_ratio = Column(Float, nullable=True)
    code_smells_count = Column(Integer, default=0)
    
    # Thresholds and ratings
    complexity_rating = Column(String(10), nullable=True)  # 'A', 'B', 'C', 'D', 'E'
    maintainability_rating = Column(String(10), nullable=True)
    testability_rating = Column(String(10), nullable=True)
    
    # Additional metrics as JSON for flexibility
    additional_metrics = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    analysis_job = relationship("ArchitecturalAnalysisJob", back_populates="code_metrics")
    
    __table_args__ = (
        Index('idx_metrics_scope_type', 'scope_type', 'analysis_job_id'),
        Index('idx_metrics_complexity', 'cyclomatic_complexity', 'scope_type'),
        Index('idx_metrics_rating', 'complexity_rating', 'maintainability_rating'),
    )

class ArchitecturalLayer(Base):
    """
    Architectural layer definitions and compliance tracking
    
    Defines layers and tracks compliance for architectural governance
    """
    __tablename__ = "architectural_layers"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Layer definition
    name = Column(String(100), nullable=False, index=True)
    pattern = Column(String(500), nullable=False)  # Regex pattern for package matching
    description = Column(Text, nullable=False)
    
    # Dependency rules
    allowed_dependencies = Column(JSON, nullable=True)  # List of allowed dependency layers
    forbidden_dependencies = Column(JSON, nullable=True)  # List of forbidden dependency layers
    
    # Configuration
    is_active = Column(Boolean, default=True, index=True)
    severity_level = Column(String(20), default='HIGH')  # Violation severity
    
    # Usage tracking
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(String(100), nullable=True)
    last_modified_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_modified_by = Column(String(100), nullable=True)
    
    __table_args__ = (
        Index('idx_layer_name_active', 'name', 'is_active'),
    )

class CyclicDependency(Base):
    """
    Cyclic dependencies detected by jQAssistant
    
    Tracks dependency cycles for architectural debt management
    """
    __tablename__ = "cyclic_dependencies"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key to analysis job
    analysis_job_id = Column(UUID(as_uuid=True), ForeignKey('architectural_analysis_jobs.id'), nullable=False, index=True)
    
    # Cycle information
    cycle_elements = Column(JSON, nullable=False)  # Ordered list of packages/classes in cycle
    cycle_length = Column(Integer, nullable=False, index=True)
    cycle_type = Column(String(20), nullable=False, index=True)  # 'PACKAGE', 'CLASS', 'METHOD'
    
    # Impact assessment
    severity = Column(String(20), nullable=False, index=True)  # 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    impact_description = Column(Text, nullable=True)
    estimated_effort_to_fix = Column(String(20), nullable=True)  # 'LOW', 'MEDIUM', 'HIGH'
    
    # Resolution tracking
    is_resolved = Column(Boolean, default=False, index=True)
    resolution_strategy = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    analysis_job = relationship("ArchitecturalAnalysisJob", backref="cyclic_dependencies")
    
    __table_args__ = (
        Index('idx_cycle_length_type', 'cycle_length', 'cycle_type'),
        Index('idx_cycle_severity_resolved', 'severity', 'is_resolved'),
    )

class ArchitecturalInsight(Base):
    """
    High-level architectural insights and recommendations
    
    Stores aggregated insights and recommendations from jQAssistant analysis
    """
    __tablename__ = "indexing_architectural_insights"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key to analysis job
    analysis_job_id = Column(UUID(as_uuid=True), ForeignKey('architectural_analysis_jobs.id'), nullable=False, index=True)
    
    # Insight information
    insight_type = Column(String(100), nullable=False, index=True)  # 'RECOMMENDATION', 'WARNING', 'OBSERVATION'
    category = Column(String(50), nullable=False, index=True)  # 'STRUCTURE', 'QUALITY', 'SECURITY', 'PERFORMANCE'
    priority = Column(String(20), nullable=False, index=True)  # 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    
    # Content
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=True)
    
    # Supporting data
    evidence = Column(JSON, nullable=True)  # Supporting metrics and data
    affected_elements = Column(JSON, nullable=True)  # List of affected packages/classes
    
    # Business impact
    business_impact = Column(Text, nullable=True)
    technical_impact = Column(Text, nullable=True)
    estimated_effort = Column(String(20), nullable=True)  # 'LOW', 'MEDIUM', 'HIGH'
    
    # Action tracking
    is_acknowledged = Column(Boolean, default=False, index=True)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String(100), nullable=True)
    action_taken = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    analysis_job = relationship("ArchitecturalAnalysisJob", backref="insights")
    
    __table_args__ = (
        Index('idx_insight_type_priority', 'insight_type', 'priority'),
        Index('idx_insight_category_ack', 'category', 'is_acknowledged'),
    )