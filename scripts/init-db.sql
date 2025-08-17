-- DocXP Database Initialization Script
-- This script sets up the basic schema for the V1 local-first architecture

-- Create database if it doesn't exist (handled by POSTGRES_DB env var)
-- CREATE DATABASE IF NOT EXISTS docxp;

-- Use the docxp database
\c docxp;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Drop tables if they exist (for development)
DROP TABLE IF EXISTS citation_metadata CASCADE;
DROP TABLE IF EXISTS job_results CASCADE;
DROP TABLE IF EXISTS repository_jobs CASCADE;
DROP TABLE IF EXISTS repositories CASCADE;
DROP TABLE IF EXISTS golden_questions CASCADE;
DROP TABLE IF EXISTS golden_question_results CASCADE;

-- Repositories table
CREATE TABLE repositories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    local_path TEXT,
    commit_hash VARCHAR(64),
    branch VARCHAR(255) DEFAULT 'main',
    language_stats JSONB,
    total_files INTEGER DEFAULT 0,
    total_lines INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',
    metadata JSONB
);

-- Repository jobs table for tracking processing
CREATE TABLE repository_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    repository_id UUID REFERENCES repositories(id) ON DELETE CASCADE,
    job_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    progress INTEGER DEFAULT 0,
    total_steps INTEGER DEFAULT 100,
    error_message TEXT,
    result_data JSONB,
    rq_job_id VARCHAR(255),
    created_by VARCHAR(255),
    metadata JSONB
);

-- Job results for storing analysis outputs
CREATE TABLE job_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES repository_jobs(id) ON DELETE CASCADE,
    repository_id UUID REFERENCES repositories(id) ON DELETE CASCADE,
    result_type VARCHAR(100) NOT NULL, -- 'documentation', 'diagram', 'business_rule', etc.
    file_path TEXT NOT NULL,
    s3_key TEXT, -- MinIO/S3 storage key
    content_hash VARCHAR(64),
    file_size BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Citation metadata for grounded responses
CREATE TABLE citation_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    repository_id UUID REFERENCES repositories(id) ON DELETE CASCADE,
    commit_hash VARCHAR(64) NOT NULL,
    file_path TEXT NOT NULL,
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    content_type VARCHAR(100), -- 'code', 'documentation', 'config', etc.
    language VARCHAR(50),
    kind VARCHAR(100), -- 'function', 'class', 'jsp', 'sql', etc.
    tool VARCHAR(100) NOT NULL, -- 'tree-sitter', 'semgrep', 'jsp-parser', etc.
    model VARCHAR(100), -- 'claude-3-5-sonnet', 'titan-embed-v2', etc.
    content_hash VARCHAR(64),
    indexed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    opensearch_doc_id VARCHAR(255), -- Reference to OpenSearch document
    metadata JSONB
);

-- Golden questions for regression testing
CREATE TABLE golden_questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id VARCHAR(255) UNIQUE NOT NULL,
    query TEXT NOT NULL,
    expected_results JSONB NOT NULL, -- Array of expected citations/results
    tags TEXT[], -- ['db', 'jsp', 'struts', etc.]
    priority INTEGER DEFAULT 1,
    repository_filter VARCHAR(255), -- Optional repository constraint
    commit_filter VARCHAR(64), -- Optional commit constraint
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB
);

-- Golden question test results
CREATE TABLE golden_question_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id UUID REFERENCES golden_questions(id) ON DELETE CASCADE,
    test_run_id VARCHAR(255) NOT NULL, -- Groups results from same test run
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    query_latency_ms INTEGER,
    top_k_results JSONB, -- Array of returned results
    hit_at_k JSONB, -- Which positions had correct results
    precision_at_3 DECIMAL(5,4),
    precision_at_5 DECIMAL(5,4),
    passed BOOLEAN,
    error_message TEXT,
    bedrock_tokens_used INTEGER,
    bedrock_cost_usd DECIMAL(10,6),
    metadata JSONB
);

-- Create indexes for performance
CREATE INDEX idx_repositories_status ON repositories(status);
CREATE INDEX idx_repositories_commit ON repositories(commit_hash);
CREATE INDEX idx_repository_jobs_status ON repository_jobs(status);
CREATE INDEX idx_repository_jobs_repo ON repository_jobs(repository_id);
CREATE INDEX idx_repository_jobs_rq_id ON repository_jobs(rq_job_id);
CREATE INDEX idx_job_results_job ON job_results(job_id);
CREATE INDEX idx_job_results_repo ON job_results(repository_id);
CREATE INDEX idx_job_results_type ON job_results(result_type);
CREATE INDEX idx_citation_repo_commit ON citation_metadata(repository_id, commit_hash);
CREATE INDEX idx_citation_file_path ON citation_metadata(file_path);
CREATE INDEX idx_citation_lines ON citation_metadata(start_line, end_line);
CREATE INDEX idx_citation_opensearch ON citation_metadata(opensearch_doc_id);
CREATE INDEX idx_golden_questions_active ON golden_questions(is_active);
CREATE INDEX idx_golden_results_run ON golden_question_results(test_run_id);
CREATE INDEX idx_golden_results_question ON golden_question_results(question_id);

-- Insert sample golden questions for V1 demo
INSERT INTO golden_questions (question_id, query, expected_results, tags, priority) VALUES
(
    'specified-amount-trace',
    'Where does Specified Amount come from in the summary action?',
    '[
        {
            "path": "sql/seeds/agreement_values.sql",
            "contains": "DEATH BENEFIT AMOUNT",
            "min_similarity": 0.8
        },
        {
            "path": "web/jsp/summary.jsp",
            "contains": "contractOptions.specifiedAmount",
            "min_similarity": 0.8
        },
        {
            "path": "struts-config.xml",
            "contains": "summary.action",
            "min_similarity": 0.7
        }
    ]'::jsonb,
    ARRAY['db', 'jsp', 'struts', 'mapping'],
    1
),
(
    'contract-options-flow',
    'How does contractOptions data flow from database to JSP?',
    '[
        {
            "path": "src/actions/SummaryAction.java",
            "contains": "contractOptions",
            "min_similarity": 0.7
        },
        {
            "path": "web/jsp/loadedHeader.jsp",
            "contains": "contractOptions",
            "min_similarity": 0.7
        }
    ]'::jsonb,
    ARRAY['java', 'jsp', 'data-flow'],
    2
),
(
    'ssc-table-usage',
    'Which tables are used for SSC calculations?',
    '[
        {
            "path": "sql/schema/ssc_tables.sql",
            "contains": "ssc_",
            "min_similarity": 0.8
        },
        {
            "path": "sql/migration/items_migration.sql",
            "contains": "ssc_item_info",
            "min_similarity": 0.8
        }
    ]'::jsonb,
    ARRAY['db', 'ssc', 'calculations'],
    1
);

-- Update timestamps trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers for updated_at columns
CREATE TRIGGER update_repositories_updated_at 
    BEFORE UPDATE ON repositories 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_golden_questions_updated_at 
    BEFORE UPDATE ON golden_questions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions (adjust as needed for production)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO docxp_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO docxp_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO docxp_user;

-- Log successful initialization
INSERT INTO repositories (name, url, status, metadata) VALUES 
('_system_init', 'internal://system', 'initialized', '{"init_time": "' || CURRENT_TIMESTAMP || '", "version": "v1.0"}');

-- Show tables created
\dt