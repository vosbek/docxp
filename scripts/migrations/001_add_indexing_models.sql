-- Migration: Add V1 Indexing Models
-- Version: 1.1
-- Date: 2025-08-16
-- Description: Add database tables for V1 indexing system with job tracking, 
--              file processing status, repository snapshots, embedding cache, 
--              and health metrics

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create enum types for indexing
CREATE TYPE indexing_job_status AS ENUM (
    'pending', 'running', 'paused', 'completed', 'failed', 'cancelled'
);

CREATE TYPE file_processing_status AS ENUM (
    'pending', 'processing', 'completed', 'failed', 'skipped'
);

CREATE TYPE indexing_job_type AS ENUM (
    'full', 'incremental', 'selective'
);

-- Indexing Jobs Table
CREATE TABLE indexing_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    repository_id UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    job_type VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    
    -- Job configuration
    target_commit VARCHAR(40),
    file_patterns JSONB,
    config JSONB,
    
    -- Progress tracking
    total_files INTEGER DEFAULT 0,
    processed_files INTEGER DEFAULT 0,
    failed_files INTEGER DEFAULT 0,
    skipped_files INTEGER DEFAULT 0,
    
    -- Checkpoint data for resume capability
    last_processed_file VARCHAR(500),
    checkpoint_data JSONB,
    
    -- Error tracking
    error_message TEXT,
    error_details JSONB,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    
    -- Timing
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    estimated_completion TIMESTAMPTZ,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(100)
);

-- File Processing Records Table
CREATE TABLE file_processing_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    indexing_job_id UUID NOT NULL REFERENCES indexing_jobs(id) ON DELETE CASCADE,
    
    -- File identification
    file_path VARCHAR(1000) NOT NULL,
    file_hash VARCHAR(64),
    file_size INTEGER,
    file_type VARCHAR(50),
    
    -- Processing status
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    processing_order INTEGER,
    
    -- Processing results
    entities_extracted INTEGER DEFAULT 0,
    embeddings_generated INTEGER DEFAULT 0,
    processing_duration FLOAT,
    
    -- Error tracking
    error_message TEXT,
    error_type VARCHAR(100),
    error_details JSONB,
    retry_count INTEGER DEFAULT 0,
    
    -- Timing
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(indexing_job_id, file_path)
);

-- Repository Snapshots Table
CREATE TABLE repository_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    repository_id UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    indexing_job_id UUID NOT NULL REFERENCES indexing_jobs(id) ON DELETE CASCADE,
    
    -- Repository state
    commit_hash VARCHAR(40) NOT NULL,
    branch_name VARCHAR(200),
    commit_message TEXT,
    commit_author VARCHAR(200),
    commit_date TIMESTAMPTZ,
    
    -- File statistics
    total_files INTEGER NOT NULL DEFAULT 0,
    indexed_files INTEGER NOT NULL DEFAULT 0,
    failed_files INTEGER NOT NULL DEFAULT 0,
    skipped_files INTEGER NOT NULL DEFAULT 0,
    
    -- Content statistics
    total_entities INTEGER NOT NULL DEFAULT 0,
    total_embeddings INTEGER NOT NULL DEFAULT 0,
    total_size_bytes INTEGER NOT NULL DEFAULT 0,
    
    -- File type breakdown
    file_type_stats JSONB,
    
    -- Performance metrics
    indexing_duration FLOAT,
    avg_file_processing_time FLOAT,
    embeddings_cost FLOAT,
    
    -- Quality metrics
    error_rate FLOAT,
    success_rate FLOAT,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB,
    
    -- Constraints
    UNIQUE(indexing_job_id)
);

-- Embedding Cache Table
CREATE TABLE embedding_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Content identification
    content_hash VARCHAR(64) NOT NULL UNIQUE,
    content_type VARCHAR(50) NOT NULL,
    
    -- Embedding data
    embedding_model VARCHAR(100) NOT NULL,
    embedding_vector JSONB NOT NULL,
    embedding_dimension INTEGER NOT NULL,
    
    -- Usage tracking
    hit_count INTEGER DEFAULT 1,
    cost_saved FLOAT DEFAULT 0.0,
    
    -- Content metadata
    sample_content TEXT,
    file_extension VARCHAR(10),
    content_length INTEGER,
    
    -- Timing
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enhanced Code Entity Data Table (addresses missing entity_metadata)
-- Note: This assumes the existing code_entity_data table needs to be enhanced
-- If it doesn't exist, uncomment the CREATE TABLE below

-- ALTER TABLE code_entity_data ADD COLUMN IF NOT EXISTS entity_metadata JSONB;
-- ALTER TABLE code_entity_data ADD COLUMN IF NOT EXISTS indexing_job_id UUID REFERENCES indexing_jobs(id);
-- ALTER TABLE code_entity_data ADD COLUMN IF NOT EXISTS content_hash VARCHAR(64);
-- ALTER TABLE code_entity_data ADD COLUMN IF NOT EXISTS embedding_vector JSONB;
-- ALTER TABLE code_entity_data ADD COLUMN IF NOT EXISTS content_summary TEXT;
-- ALTER TABLE code_entity_data ADD COLUMN IF NOT EXISTS keywords JSONB;
-- ALTER TABLE code_entity_data ADD COLUMN IF NOT EXISTS complexity_score FLOAT;
-- ALTER TABLE code_entity_data ADD COLUMN IF NOT EXISTS importance_score FLOAT;
-- ALTER TABLE code_entity_data ADD COLUMN IF NOT EXISTS extraction_method VARCHAR(50);
-- ALTER TABLE code_entity_data ADD COLUMN IF NOT EXISTS embedding_model VARCHAR(100);

-- If code_entity_data table doesn't exist, create it:
CREATE TABLE IF NOT EXISTS code_entity_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    repository_id UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    indexing_job_id UUID REFERENCES indexing_jobs(id),
    
    -- Entity identification
    entity_type VARCHAR(50) NOT NULL,
    entity_name VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000) NOT NULL,
    
    -- Source location
    start_line INTEGER,
    end_line INTEGER,
    start_column INTEGER,
    end_column INTEGER,
    
    -- Content and embeddings
    content TEXT NOT NULL,
    content_hash VARCHAR(64),
    embedding_vector JSONB,
    
    -- Enhanced metadata (addresses missing entity_metadata)
    entity_metadata JSONB,
    metadata JSONB,
    
    -- Search optimization
    content_summary TEXT,
    keywords JSONB,
    
    -- Quality and relevance
    complexity_score FLOAT,
    importance_score FLOAT,
    
    -- Processing info
    extraction_method VARCHAR(50),
    embedding_model VARCHAR(100),
    
    -- Timing
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexing Health Metrics Table
CREATE TABLE indexing_health_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Metric identification
    metric_type VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    
    -- Metric data
    metric_value FLOAT NOT NULL,
    metric_unit VARCHAR(20),
    
    -- Context
    repository_id UUID REFERENCES repositories(id),
    indexing_job_id UUID REFERENCES indexing_jobs(id),
    
    -- Aggregation
    time_bucket VARCHAR(20),
    sample_count INTEGER DEFAULT 1,
    
    -- Additional context
    metadata JSONB,
    
    -- Timing
    recorded_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for optimal performance

-- Indexing Jobs indexes
CREATE INDEX idx_indexing_jobs_repository_id ON indexing_jobs(repository_id);
CREATE INDEX idx_indexing_jobs_status ON indexing_jobs(status);
CREATE INDEX idx_indexing_jobs_created_at ON indexing_jobs(created_at);
CREATE INDEX idx_indexing_jobs_repo_status ON indexing_jobs(repository_id, status);

-- File Processing Records indexes
CREATE INDEX idx_file_processing_job_id ON file_processing_records(indexing_job_id);
CREATE INDEX idx_file_processing_status ON file_processing_records(status);
CREATE INDEX idx_file_processing_file_path ON file_processing_records(file_path);
CREATE INDEX idx_file_processing_job_order ON file_processing_records(indexing_job_id, processing_order);

-- Repository Snapshots indexes
CREATE INDEX idx_repo_snapshots_repository_id ON repository_snapshots(repository_id);
CREATE INDEX idx_repo_snapshots_commit_hash ON repository_snapshots(commit_hash);
CREATE INDEX idx_repo_snapshots_created_at ON repository_snapshots(created_at);
CREATE INDEX idx_repo_snapshots_repo_commit ON repository_snapshots(repository_id, commit_hash);

-- Embedding Cache indexes
CREATE INDEX idx_embedding_cache_content_hash ON embedding_cache(content_hash);
CREATE INDEX idx_embedding_cache_model ON embedding_cache(embedding_model);
CREATE INDEX idx_embedding_cache_type ON embedding_cache(content_type);
CREATE INDEX idx_embedding_cache_last_used ON embedding_cache(last_used_at);
CREATE INDEX idx_embedding_cache_model_type ON embedding_cache(embedding_model, content_type);

-- Code Entity Data indexes
CREATE INDEX IF NOT EXISTS idx_code_entity_repository_id ON code_entity_data(repository_id);
CREATE INDEX IF NOT EXISTS idx_code_entity_entity_type ON code_entity_data(entity_type);
CREATE INDEX IF NOT EXISTS idx_code_entity_entity_name ON code_entity_data(entity_name);
CREATE INDEX IF NOT EXISTS idx_code_entity_file_path ON code_entity_data(file_path);
CREATE INDEX IF NOT EXISTS idx_code_entity_content_hash ON code_entity_data(content_hash);
CREATE INDEX IF NOT EXISTS idx_code_entity_repo_type ON code_entity_data(repository_id, entity_type);
CREATE INDEX IF NOT EXISTS idx_code_entity_repo_file ON code_entity_data(repository_id, file_path);
CREATE INDEX IF NOT EXISTS idx_code_entity_job_id ON code_entity_data(indexing_job_id);

-- Health Metrics indexes
CREATE INDEX idx_health_metrics_type ON indexing_health_metrics(metric_type);
CREATE INDEX idx_health_metrics_name ON indexing_health_metrics(metric_name);
CREATE INDEX idx_health_metrics_recorded_at ON indexing_health_metrics(recorded_at);
CREATE INDEX idx_health_metrics_repository_id ON indexing_health_metrics(repository_id);
CREATE INDEX idx_health_metrics_job_id ON indexing_health_metrics(indexing_job_id);
CREATE INDEX idx_health_metrics_type_name ON indexing_health_metrics(metric_type, metric_name);
CREATE INDEX idx_health_metrics_type_time ON indexing_health_metrics(metric_type, recorded_at);

-- Create triggers for automatic updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_indexing_jobs_updated_at 
    BEFORE UPDATE ON indexing_jobs 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_file_processing_records_updated_at 
    BEFORE UPDATE ON file_processing_records 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_code_entity_data_updated_at 
    BEFORE UPDATE ON code_entity_data 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add helpful views for common queries

-- View for active jobs with progress
CREATE VIEW active_indexing_jobs AS
SELECT 
    j.*,
    CASE 
        WHEN j.total_files > 0 THEN (j.processed_files::float / j.total_files::float * 100)
        ELSE 0 
    END as progress_percentage,
    r.name as repository_name,
    r.url as repository_url
FROM indexing_jobs j
JOIN repositories r ON j.repository_id = r.id
WHERE j.status IN ('pending', 'running', 'paused');

-- View for job performance metrics
CREATE VIEW indexing_job_performance AS
SELECT 
    j.id,
    j.repository_id,
    j.job_type,
    j.status,
    j.total_files,
    j.processed_files,
    j.failed_files,
    EXTRACT(EPOCH FROM (j.completed_at - j.started_at)) as duration_seconds,
    CASE 
        WHEN j.processed_files > 0 AND j.started_at IS NOT NULL AND j.completed_at IS NOT NULL 
        THEN EXTRACT(EPOCH FROM (j.completed_at - j.started_at)) / j.processed_files
        ELSE NULL 
    END as avg_seconds_per_file,
    CASE 
        WHEN j.total_files > 0 THEN (j.failed_files::float / j.total_files::float * 100)
        ELSE 0 
    END as error_rate_percentage
FROM indexing_jobs j
WHERE j.status = 'completed';

-- View for repository indexing health
CREATE VIEW repository_indexing_health AS
SELECT 
    r.id as repository_id,
    r.name as repository_name,
    COUNT(j.id) as total_jobs,
    COUNT(CASE WHEN j.status = 'completed' THEN 1 END) as completed_jobs,
    COUNT(CASE WHEN j.status = 'failed' THEN 1 END) as failed_jobs,
    MAX(j.completed_at) as last_successful_index,
    AVG(CASE WHEN j.status = 'completed' AND j.started_at IS NOT NULL AND j.completed_at IS NOT NULL 
        THEN EXTRACT(EPOCH FROM (j.completed_at - j.started_at)) END) as avg_job_duration
FROM repositories r
LEFT JOIN indexing_jobs j ON r.id = j.repository_id
GROUP BY r.id, r.name;

COMMENT ON TABLE indexing_jobs IS 'Tracks indexing jobs with checkpoint and resume capability';
COMMENT ON TABLE file_processing_records IS 'File-level processing status and error tracking';
COMMENT ON TABLE repository_snapshots IS 'Repository metadata and indexing statistics snapshots';
COMMENT ON TABLE embedding_cache IS 'Embedding cache for cost optimization';
COMMENT ON TABLE code_entity_data IS 'Enhanced code entities with metadata for hybrid search';
COMMENT ON TABLE indexing_health_metrics IS 'System health metrics for monitoring';

-- End of migration
-- Version: 1.1
-- Last updated: 2025-08-16