-- Migration: Add Enterprise Models (Week 1-3)
-- Version: 2.0
-- Date: 2025-08-18
-- Description: Add all Week 1-3 enterprise models for SQLite
--              Business Rule Traces, Domain Classification, Architectural Insights, Projects

-- =============================================================================
-- Week 2: Enhanced Business Rule Models (Task 2.1-2.3)
-- =============================================================================

-- Business Rule Traces Table
CREATE TABLE IF NOT EXISTS business_rule_traces (
    id TEXT PRIMARY KEY,
    trace_id TEXT UNIQUE NOT NULL,
    rule_name TEXT NOT NULL,
    business_domain TEXT NOT NULL,
    
    -- Technology stack involved (JSON array)
    technology_stack TEXT NOT NULL, -- JSON: ["JSP", "Struts", "Java", "CORBA"]
    
    -- Flow metadata
    entry_point TEXT NOT NULL,
    exit_point TEXT,
    flow_complexity REAL DEFAULT 0.0,
    extraction_confidence REAL DEFAULT 0.0,
    
    -- Business context
    business_description TEXT,
    impact_level TEXT DEFAULT 'medium',
    regulatory_relevance BOOLEAN DEFAULT 0,
    
    -- Traceability
    repository_id INTEGER NOT NULL REFERENCES repositories(id),
    commit_hash TEXT NOT NULL,
    extracted_by TEXT,
    extracted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Metadata
    meta_data TEXT, -- JSON
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Flow Steps Table
CREATE TABLE IF NOT EXISTS flow_steps (
    id TEXT PRIMARY KEY,
    trace_id TEXT NOT NULL REFERENCES business_rule_traces(id),
    
    -- Step identification
    step_order INTEGER NOT NULL,
    step_type TEXT NOT NULL, -- FlowStepType enum
    technology TEXT NOT NULL, -- TechnologyType enum
    
    -- Component details
    component_name TEXT NOT NULL,
    component_type TEXT, -- "class", "method", "jsp", "action"
    file_path TEXT NOT NULL,
    line_start INTEGER,
    line_end INTEGER,
    
    -- Business logic
    business_logic TEXT,
    business_rules TEXT, -- JSON array
    data_elements TEXT, -- JSON array
    
    -- Dependencies and relationships
    input_parameters TEXT, -- JSON
    output_parameters TEXT, -- JSON
    dependencies TEXT, -- JSON array
    database_tables TEXT, -- JSON array
    
    -- Code analysis
    complexity_score REAL DEFAULT 0.0,
    risk_indicators TEXT, -- JSON array
    modernization_notes TEXT,
    
    -- Metadata
    meta_data TEXT, -- JSON
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Cross Technology Mapping Table
CREATE TABLE IF NOT EXISTS cross_technology_mappings (
    id TEXT PRIMARY KEY,
    
    -- Source and target components
    source_component TEXT NOT NULL,
    source_technology TEXT NOT NULL,
    source_file_path TEXT NOT NULL,
    
    target_component TEXT NOT NULL,
    target_technology TEXT NOT NULL,
    target_file_path TEXT NOT NULL,
    
    -- Relationship details
    relationship_type TEXT NOT NULL,
    relationship_strength REAL DEFAULT 1.0,
    coupling_type TEXT,
    
    -- Context
    business_context TEXT,
    modernization_impact TEXT,
    
    -- Traceability
    repository_id INTEGER NOT NULL REFERENCES repositories(id),
    discovered_by TEXT,
    confidence_score REAL DEFAULT 0.0,
    
    -- Metadata
    meta_data TEXT, -- JSON
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- Week 2: Domain Classification (Task 2.2)
-- =============================================================================

-- Domain Taxonomy Table
CREATE TABLE IF NOT EXISTS domain_taxonomy (
    id TEXT PRIMARY KEY,
    domain_id TEXT UNIQUE NOT NULL,
    
    -- Hierarchy
    parent_domain_id TEXT REFERENCES domain_taxonomy(domain_id),
    category TEXT NOT NULL, -- DomainCategory enum
    subdomain TEXT, -- BusinessSubdomain enum
    level INTEGER DEFAULT 0,
    
    -- Domain details
    name TEXT NOT NULL,
    description TEXT,
    business_purpose TEXT,
    typical_components TEXT, -- JSON array
    key_stakeholders TEXT, -- JSON array
    
    -- Classification metadata
    keywords TEXT, -- JSON array
    patterns TEXT, -- JSON array
    regulatory_scope TEXT, -- JSON array
    
    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Domain Classification Rules Table
CREATE TABLE IF NOT EXISTS domain_classification_rules (
    id TEXT PRIMARY KEY,
    rule_id TEXT UNIQUE NOT NULL,
    
    -- Rule definition
    rule_name TEXT NOT NULL,
    rule_type TEXT NOT NULL, -- keyword, pattern, ml_model
    target_domain TEXT NOT NULL REFERENCES domain_taxonomy(domain_id),
    
    -- Rule logic
    keywords TEXT, -- JSON array
    file_patterns TEXT, -- JSON array
    code_patterns TEXT, -- JSON array
    ml_model_path TEXT,
    
    -- Rule metadata
    confidence_weight REAL DEFAULT 1.0,
    priority INTEGER DEFAULT 100,
    is_active BOOLEAN DEFAULT 1,
    validation_accuracy REAL,
    
    -- Context
    created_by TEXT,
    description TEXT,
    
    -- Metadata
    meta_data TEXT, -- JSON
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Domain Classification Results Table  
CREATE TABLE IF NOT EXISTS domain_classification_results (
    id TEXT PRIMARY KEY,
    
    -- Component being classified
    repository_id INTEGER NOT NULL REFERENCES repositories(id),
    file_path TEXT NOT NULL,
    component_name TEXT,
    component_type TEXT,
    
    -- Classification results
    primary_domain TEXT NOT NULL REFERENCES domain_taxonomy(domain_id),
    confidence_score REAL NOT NULL,
    secondary_domains TEXT, -- JSON
    
    -- Classification metadata
    classification_method TEXT,
    rules_applied TEXT, -- JSON array
    model_version TEXT,
    
    -- Manual override
    manual_override BOOLEAN DEFAULT 0,
    override_reason TEXT,
    reviewed_by TEXT,
    reviewed_at DATETIME,
    
    -- Metadata
    meta_data TEXT, -- JSON
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- Week 2: Architectural Insights (Task 2.3)
-- =============================================================================

-- Enterprise Architectural Insights Table
CREATE TABLE IF NOT EXISTS enterprise_architectural_insights (
    id TEXT PRIMARY KEY,
    insight_id TEXT UNIQUE NOT NULL,
    
    -- Classification
    insight_type TEXT NOT NULL, -- InsightType enum
    severity TEXT DEFAULT 'medium', -- InsightSeverity enum
    category TEXT,
    tags TEXT, -- JSON array
    
    -- Core content
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    business_context TEXT,
    technical_details TEXT,
    
    -- Relationships to code
    business_rules TEXT, -- JSON array of rule IDs
    affected_components TEXT, -- JSON
    file_references TEXT, -- JSON
    
    -- Modernization guidance
    modernization_impact TEXT DEFAULT 'unknown',
    modernization_priority INTEGER DEFAULT 50,
    modernization_effort TEXT,
    modernization_approach TEXT,
    
    -- Architect knowledge
    architect_notes TEXT,
    recommendations TEXT, -- JSON
    alternatives TEXT, -- JSON
    risks TEXT, -- JSON
    benefits TEXT, -- JSON
    
    -- Quality metrics
    confidence_score REAL DEFAULT 0.0,
    evidence_strength TEXT DEFAULT 'medium',
    validation_status TEXT DEFAULT 'unvalidated',
    
    -- Lifecycle management
    status TEXT DEFAULT 'new',
    assigned_to TEXT,
    target_phase TEXT,
    estimated_effort_hours INTEGER,
    
    -- Traceability
    repository_id INTEGER NOT NULL REFERENCES repositories(id),
    commit_hash TEXT NOT NULL,
    discovered_by TEXT,
    discovery_method TEXT,
    
    -- Metadata
    meta_data TEXT, -- JSON
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    reviewed_at DATETIME,
    reviewed_by TEXT
);

-- Insight Dependencies Table
CREATE TABLE IF NOT EXISTS insight_dependencies (
    id TEXT PRIMARY KEY,
    
    -- Dependency relationship
    source_insight_id TEXT NOT NULL REFERENCES enterprise_architectural_insights(id),
    target_insight_id TEXT NOT NULL REFERENCES enterprise_architectural_insights(id),
    dependency_type TEXT NOT NULL,
    dependency_strength TEXT DEFAULT 'medium',
    
    -- Context
    description TEXT,
    business_rationale TEXT,
    technical_rationale TEXT,
    
    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT
);

-- Insight Evolution Table
CREATE TABLE IF NOT EXISTS insight_evolution (
    id TEXT PRIMARY KEY,
    insight_id TEXT NOT NULL REFERENCES enterprise_architectural_insights(id),
    
    -- Evolution tracking
    version INTEGER NOT NULL,
    change_type TEXT NOT NULL,
    change_description TEXT,
    
    -- State snapshot
    previous_state TEXT, -- JSON
    new_state TEXT, -- JSON
    
    -- Context
    trigger TEXT,
    commit_hash TEXT,
    changed_by TEXT,
    
    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Knowledge Articles Table
CREATE TABLE IF NOT EXISTS knowledge_articles (
    id TEXT PRIMARY KEY,
    article_id TEXT UNIQUE NOT NULL,
    
    -- Content
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    content TEXT NOT NULL,
    category TEXT,
    
    -- Knowledge metadata
    knowledge_type TEXT,
    applicability TEXT, -- JSON
    technology_stack TEXT, -- JSON array
    business_domains TEXT, -- JSON array
    
    -- Quality
    confidence_level TEXT DEFAULT 'medium',
    evidence_count INTEGER DEFAULT 0,
    usage_count INTEGER DEFAULT 0,
    
    -- Lifecycle
    status TEXT DEFAULT 'draft',
    authored_by TEXT,
    reviewed_by TEXT,
    
    -- Metadata
    meta_data TEXT, -- JSON
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- Week 3: Multi-Repository Project Coordination (Task 3.1)
-- =============================================================================

-- Projects Table
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    project_id TEXT UNIQUE NOT NULL,
    
    -- Basic information
    name TEXT NOT NULL,
    description TEXT,
    business_purpose TEXT,
    
    -- Project metadata
    status TEXT DEFAULT 'planning',
    priority TEXT DEFAULT 'medium',
    complexity_score REAL DEFAULT 0.0,
    risk_level TEXT DEFAULT 'medium',
    
    -- Business context
    business_domains TEXT, -- JSON array
    stakeholders TEXT, -- JSON
    business_sponsor TEXT,
    technical_lead TEXT,
    
    -- Modernization strategy
    modernization_goals TEXT, -- JSON
    target_architecture TEXT, -- JSON
    modernization_approach TEXT,
    estimated_duration_months INTEGER,
    
    -- Timeline
    planned_start_date DATETIME,
    planned_end_date DATETIME,
    actual_start_date DATETIME,
    actual_end_date DATETIME,
    
    -- Budget and resources
    estimated_effort_hours INTEGER,
    allocated_budget REAL,
    team_size INTEGER,
    
    -- Progress tracking
    progress_percentage REAL DEFAULT 0.0,
    repositories_analyzed INTEGER DEFAULT 0,
    business_rules_discovered INTEGER DEFAULT 0,
    insights_generated INTEGER DEFAULT 0,
    
    -- Quality metrics
    analysis_completeness REAL DEFAULT 0.0,
    rule_extraction_confidence REAL DEFAULT 0.0,
    coverage_percentage REAL DEFAULT 0.0,
    
    -- Metadata
    tags TEXT, -- JSON array
    meta_data TEXT, -- JSON
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT
);

-- Project Repositories Table
CREATE TABLE IF NOT EXISTS project_repositories (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    repository_id INTEGER NOT NULL REFERENCES repositories(id),
    
    -- Repository role in project
    repository_role TEXT DEFAULT 'primary',
    priority INTEGER DEFAULT 100,
    is_critical_path BOOLEAN DEFAULT 0,
    
    -- Analysis status
    analysis_status TEXT DEFAULT 'pending',
    analysis_progress REAL DEFAULT 0.0,
    last_analyzed DATETIME,
    analysis_duration_minutes INTEGER,
    
    -- Repository metadata within project context
    technology_stack TEXT, -- JSON
    business_domains TEXT, -- JSON array
    complexity_factors TEXT, -- JSON
    
    -- Dependencies
    depends_on_repositories TEXT, -- JSON array
    dependency_strength REAL DEFAULT 0.0,
    shared_components TEXT, -- JSON
    
    -- Modernization context
    modernization_priority INTEGER DEFAULT 50,
    modernization_complexity TEXT DEFAULT 'medium',
    legacy_risk_factors TEXT, -- JSON
    modernization_notes TEXT,
    
    -- Metadata
    meta_data TEXT, -- JSON
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Project Phases Table
CREATE TABLE IF NOT EXISTS project_phases (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    
    -- Phase information
    phase_name TEXT NOT NULL,
    phase_type TEXT,
    phase_order INTEGER NOT NULL,
    
    -- Status and progress
    status TEXT DEFAULT 'not_started',
    progress_percentage REAL DEFAULT 0.0,
    
    -- Timeline
    planned_start_date DATETIME,
    planned_end_date DATETIME,
    actual_start_date DATETIME,
    actual_end_date DATETIME,
    
    -- Scope
    repositories_in_scope TEXT, -- JSON array
    deliverables TEXT, -- JSON
    success_criteria TEXT, -- JSON
    
    -- Resources
    estimated_effort_hours INTEGER,
    team_assignments TEXT, -- JSON
    
    -- Dependencies
    depends_on_phases TEXT, -- JSON array
    blocking_issues TEXT, -- JSON
    
    -- Metadata
    description TEXT,
    notes TEXT,
    meta_data TEXT, -- JSON
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Project Dependencies Table
CREATE TABLE IF NOT EXISTS project_dependencies (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    depends_on_project_id TEXT NOT NULL REFERENCES projects(id),
    
    -- Dependency metadata
    dependency_type TEXT NOT NULL,
    dependency_strength TEXT DEFAULT 'medium',
    description TEXT,
    
    -- Impact analysis
    impact_on_timeline TEXT,
    impact_on_budget TEXT,
    risk_level TEXT DEFAULT 'medium',
    
    -- Management
    mitigation_strategy TEXT,
    is_blocking BOOLEAN DEFAULT 0,
    resolution_status TEXT DEFAULT 'open',
    
    -- Metadata
    meta_data TEXT, -- JSON
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT
);

-- =============================================================================
-- Graph Entity Metadata Tables
-- =============================================================================

-- Graph Node Metadata Table
CREATE TABLE IF NOT EXISTS graph_node_metadata (
    id TEXT PRIMARY KEY,
    node_type TEXT NOT NULL,
    name TEXT NOT NULL,
    repository_id TEXT,
    project_id TEXT,
    source_file TEXT,
    line_number INTEGER,
    properties TEXT, -- JSON
    labels TEXT, -- JSON
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

-- Graph Relationship Metadata Table
CREATE TABLE IF NOT EXISTS graph_relationship_metadata (
    id TEXT PRIMARY KEY,
    source_node_id TEXT NOT NULL,
    target_node_id TEXT NOT NULL,
    relationship_type TEXT NOT NULL,
    properties TEXT, -- JSON
    strength INTEGER DEFAULT 1,
    frequency INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

-- Graph Business Rule Traces Table (separate from main business rule traces)
CREATE TABLE IF NOT EXISTS graph_business_rule_traces (
    id TEXT PRIMARY KEY,
    rule_name TEXT NOT NULL,
    description TEXT,
    business_domain TEXT,
    technology_stack TEXT, -- JSON
    flow_steps TEXT, -- JSON
    complexity_score INTEGER,
    extraction_confidence INTEGER,
    validation_status TEXT DEFAULT 'pending',
    created_by TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Graph Architectural Insights Table (separate from enterprise insights)
CREATE TABLE IF NOT EXISTS graph_architectural_insights (
    id TEXT PRIMARY KEY,
    insight_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    business_rules TEXT, -- JSON
    affected_components TEXT, -- JSON
    modernization_impact TEXT,
    implementation_effort TEXT,
    roi_estimate TEXT,
    architect_notes TEXT,
    confidence_score INTEGER,
    validation_status TEXT DEFAULT 'pending',
    priority TEXT DEFAULT 'medium',
    created_by TEXT,
    reviewed_by TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- Create Indexes for Optimal Performance
-- =============================================================================

-- Business Rule Traces indexes
CREATE INDEX IF NOT EXISTS idx_business_rule_traces_repository_id ON business_rule_traces(repository_id);
CREATE INDEX IF NOT EXISTS idx_business_rule_traces_trace_id ON business_rule_traces(trace_id);
CREATE INDEX IF NOT EXISTS idx_business_rule_traces_domain ON business_rule_traces(business_domain);

-- Flow Steps indexes
CREATE INDEX IF NOT EXISTS idx_flow_steps_trace_id ON flow_steps(trace_id);
CREATE INDEX IF NOT EXISTS idx_flow_steps_step_order ON flow_steps(trace_id, step_order);
CREATE INDEX IF NOT EXISTS idx_flow_steps_technology ON flow_steps(technology);

-- Cross Technology Mappings indexes
CREATE INDEX IF NOT EXISTS idx_cross_tech_mappings_repository_id ON cross_technology_mappings(repository_id);
CREATE INDEX IF NOT EXISTS idx_cross_tech_mappings_source ON cross_technology_mappings(source_technology, source_component);
CREATE INDEX IF NOT EXISTS idx_cross_tech_mappings_target ON cross_technology_mappings(target_technology, target_component);

-- Domain Taxonomy indexes
CREATE INDEX IF NOT EXISTS idx_domain_taxonomy_domain_id ON domain_taxonomy(domain_id);
CREATE INDEX IF NOT EXISTS idx_domain_taxonomy_parent ON domain_taxonomy(parent_domain_id);
CREATE INDEX IF NOT EXISTS idx_domain_taxonomy_category ON domain_taxonomy(category);

-- Domain Classification Results indexes
CREATE INDEX IF NOT EXISTS idx_domain_results_repository_id ON domain_classification_results(repository_id);
CREATE INDEX IF NOT EXISTS idx_domain_results_primary_domain ON domain_classification_results(primary_domain);
CREATE INDEX IF NOT EXISTS idx_domain_results_file_path ON domain_classification_results(file_path);

-- Architectural Insights indexes
CREATE INDEX IF NOT EXISTS idx_enterprise_insights_repository_id ON enterprise_architectural_insights(repository_id);
CREATE INDEX IF NOT EXISTS idx_enterprise_insights_insight_id ON enterprise_architectural_insights(insight_id);
CREATE INDEX IF NOT EXISTS idx_enterprise_insights_type ON enterprise_architectural_insights(insight_type);
CREATE INDEX IF NOT EXISTS idx_enterprise_insights_priority ON enterprise_architectural_insights(modernization_priority);

-- Project indexes
CREATE INDEX IF NOT EXISTS idx_projects_project_id ON projects(project_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_created_at ON projects(created_at);

-- Project Repositories indexes
CREATE INDEX IF NOT EXISTS idx_project_repositories_project_id ON project_repositories(project_id);
CREATE INDEX IF NOT EXISTS idx_project_repositories_repository_id ON project_repositories(repository_id);
CREATE INDEX IF NOT EXISTS idx_project_repositories_role ON project_repositories(repository_role);

-- Graph indexes
CREATE INDEX IF NOT EXISTS idx_graph_nodes_type ON graph_node_metadata(node_type);
CREATE INDEX IF NOT EXISTS idx_graph_nodes_repository ON graph_node_metadata(repository_id);
CREATE INDEX IF NOT EXISTS idx_graph_relationships_type ON graph_relationship_metadata(relationship_type);
CREATE INDEX IF NOT EXISTS idx_graph_relationships_source ON graph_relationship_metadata(source_node_id);
CREATE INDEX IF NOT EXISTS idx_graph_relationships_target ON graph_relationship_metadata(target_node_id);

-- Add helpful views for common queries

-- View for project progress
CREATE VIEW IF NOT EXISTS project_progress_view AS
SELECT 
    p.*,
    COUNT(pr.id) as total_repositories,
    COUNT(CASE WHEN pr.analysis_status = 'completed' THEN 1 END) as completed_repositories,
    AVG(pr.analysis_progress) as avg_repository_progress
FROM projects p
LEFT JOIN project_repositories pr ON p.id = pr.project_id
GROUP BY p.id;

-- View for business rule trace summary
CREATE VIEW IF NOT EXISTS business_rule_summary AS
SELECT 
    brt.business_domain,
    COUNT(brt.id) as total_traces,
    COUNT(fs.id) as total_flow_steps,
    AVG(brt.flow_complexity) as avg_complexity,
    AVG(brt.extraction_confidence) as avg_confidence
FROM business_rule_traces brt
LEFT JOIN flow_steps fs ON brt.id = fs.trace_id
GROUP BY brt.business_domain;

-- Comments on tables for documentation
-- (SQLite doesn't support COMMENT ON TABLE, but we can add them as SQL comments)

-- End of migration
-- Version: 2.0
-- Tables created: 20 new enterprise tables
-- Views created: 2 summary views  
-- Indexes created: 25+ performance indexes
-- Last updated: 2025-08-18