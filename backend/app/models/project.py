"""
Project Models for DocXP Enterprise
Multi-repository project coordination and management for enterprise modernization initiatives
"""

from typing import List, Optional, Dict, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import uuid

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

from app.models.base import Base

class ProjectStatus(Enum):
    """Status of enterprise modernization project"""
    PLANNING = "planning"               # Initial planning phase
    ANALYSIS = "analysis"              # Code analysis in progress
    DISCOVERY = "discovery"            # Business rule discovery phase
    ASSESSMENT = "assessment"          # Risk and complexity assessment
    DESIGN = "design"                  # Modernization design phase
    IMPLEMENTATION = "implementation"   # Modernization implementation
    TESTING = "testing"                # Testing and validation
    DEPLOYMENT = "deployment"          # Production deployment
    COMPLETED = "completed"            # Project completed
    ON_HOLD = "on_hold"               # Temporarily suspended
    CANCELLED = "cancelled"            # Project cancelled

class ProjectPriority(Enum):
    """Project priority levels"""
    CRITICAL = "critical"              # Business critical
    HIGH = "high"                     # High priority
    MEDIUM = "medium"                 # Normal priority  
    LOW = "low"                       # Low priority
    MAINTENANCE = "maintenance"        # Maintenance/support

class RepositoryRole(Enum):
    """Role of repository within project"""
    PRIMARY = "primary"                # Main application
    DEPENDENCY = "dependency"          # Shared library/component
    INTEGRATION = "integration"        # Integration/middleware
    CONFIGURATION = "configuration"    # Configuration repository
    DOCUMENTATION = "documentation"    # Documentation repository
    TESTING = "testing"               # Test repository

# SQLAlchemy Models

class Project(Base):
    """
    Enterprise modernization project containing multiple repositories
    """
    __tablename__ = "projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Basic information
    name = Column(String(500), nullable=False)
    description = Column(Text)
    business_purpose = Column(Text)  # Business rationale for modernization
    
    # Project metadata
    status = Column(String(50), default="planning")  # ProjectStatus enum
    priority = Column(String(50), default="medium")  # ProjectPriority enum
    complexity_score = Column(Float, default=0.0)  # Overall complexity (0-10)
    risk_level = Column(String(50), default="medium")  # low, medium, high, critical
    
    # Business context
    business_domains = Column(ARRAY(String))  # Primary business domains
    stakeholders = Column(JSON)  # Key stakeholders and contacts
    business_sponsor = Column(String(200))  # Executive sponsor
    technical_lead = Column(String(200))  # Technical lead
    
    # Modernization strategy
    modernization_goals = Column(JSON)  # Specific modernization objectives
    target_architecture = Column(JSON)  # Target technology stack
    modernization_approach = Column(String(100))  # big_bang, phased, strangler_fig
    estimated_duration_months = Column(Integer)  # Estimated project duration
    
    # Timeline
    planned_start_date = Column(DateTime)
    planned_end_date = Column(DateTime)
    actual_start_date = Column(DateTime)
    actual_end_date = Column(DateTime)
    
    # Budget and resources
    estimated_effort_hours = Column(Integer)
    allocated_budget = Column(Float)  # Budget in USD
    team_size = Column(Integer)
    
    # Progress tracking
    progress_percentage = Column(Float, default=0.0)  # 0-100%
    repositories_analyzed = Column(Integer, default=0)
    business_rules_discovered = Column(Integer, default=0)
    insights_generated = Column(Integer, default=0)
    
    # Quality metrics
    analysis_completeness = Column(Float, default=0.0)  # 0-100%
    rule_extraction_confidence = Column(Float, default=0.0)  # Average confidence
    coverage_percentage = Column(Float, default=0.0)  # Code coverage analyzed
    
    # Relationships  
    repository_assignments = relationship("ProjectRepository", back_populates="project", cascade="all, delete-orphan")
    project_phases = relationship("ProjectPhase", back_populates="project", cascade="all, delete-orphan")
    project_dependencies = relationship("ProjectDependency", foreign_keys="ProjectDependency.project_id", back_populates="project")
    
    # Metadata
    tags = Column(ARRAY(String))  # Searchable tags
    meta_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))

class ProjectRepository(Base):
    """
    Association between projects and repositories with role and metadata
    """
    __tablename__ = "project_repositories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    
    # Repository role in project
    repository_role = Column(String(50), default="primary")  # RepositoryRole enum
    priority = Column(Integer, default=100)  # Processing priority (lower = higher)
    is_critical_path = Column(Boolean, default=False)  # On critical path
    
    # Analysis status
    analysis_status = Column(String(50), default="pending")  # pending, in_progress, completed, failed
    analysis_progress = Column(Float, default=0.0)  # 0-100%
    last_analyzed = Column(DateTime)
    analysis_duration_minutes = Column(Integer)
    
    # Repository metadata within project context
    technology_stack = Column(JSON)  # Technologies used in this repository
    business_domains = Column(ARRAY(String))  # Business domains covered
    complexity_factors = Column(JSON)  # Factors contributing to complexity
    
    # Dependencies
    depends_on_repositories = Column(ARRAY(String))  # Repository IDs this depends on
    dependency_strength = Column(Float, default=0.0)  # 0-1 coupling strength
    shared_components = Column(JSON)  # Shared libraries/components
    
    # Modernization context
    modernization_priority = Column(Integer, default=50)  # 1-100
    modernization_complexity = Column(String(50), default="medium")  # low, medium, high
    legacy_risk_factors = Column(JSON)  # Risks in modernizing this repo
    modernization_notes = Column(Text)
    
    # Relationships
    project = relationship("Project", back_populates="repository_assignments")
    # Note: Repository relationship would be added when repositories table is available
    
    # Metadata
    meta_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ProjectPhase(Base):
    """
    Project phases for managing complex modernization initiatives
    """
    __tablename__ = "project_phases"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    
    # Phase information
    phase_name = Column(String(200), nullable=False)
    phase_type = Column(String(50))  # discovery, analysis, design, implementation
    phase_order = Column(Integer, nullable=False)  # Sequential order
    
    # Status and progress
    status = Column(String(50), default="not_started")  # not_started, in_progress, completed, blocked
    progress_percentage = Column(Float, default=0.0)
    
    # Timeline
    planned_start_date = Column(DateTime)
    planned_end_date = Column(DateTime)
    actual_start_date = Column(DateTime)
    actual_end_date = Column(DateTime)
    
    # Scope
    repositories_in_scope = Column(ARRAY(String))  # Repository IDs for this phase
    deliverables = Column(JSON)  # Expected deliverables
    success_criteria = Column(JSON)  # Success criteria
    
    # Resources
    estimated_effort_hours = Column(Integer)
    team_assignments = Column(JSON)  # Team member assignments
    
    # Dependencies
    depends_on_phases = Column(ARRAY(String))  # Phase IDs this depends on
    blocking_issues = Column(JSON)  # Current blocking issues
    
    # Relationships
    project = relationship("Project", back_populates="project_phases")
    
    # Metadata
    description = Column(Text)
    notes = Column(Text)
    meta_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ProjectDependency(Base):
    """
    Dependencies between projects for enterprise portfolio management
    """
    __tablename__ = "project_dependencies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    depends_on_project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    
    # Dependency metadata
    dependency_type = Column(String(50), nullable=False)  # technical, business, resource, timeline
    dependency_strength = Column(String(50), default="medium")  # weak, medium, strong, critical
    description = Column(Text)
    
    # Impact analysis
    impact_on_timeline = Column(String(50))  # none, minor, moderate, major
    impact_on_budget = Column(String(50))  # none, minor, moderate, major
    risk_level = Column(String(50), default="medium")  # low, medium, high
    
    # Management
    mitigation_strategy = Column(Text)
    is_blocking = Column(Boolean, default=False)
    resolution_status = Column(String(50), default="open")  # open, mitigated, resolved
    
    # Relationships
    project = relationship("Project", foreign_keys=[project_id], back_populates="project_dependencies")
    depends_on_project = relationship("Project", foreign_keys=[depends_on_project_id])
    
    # Metadata
    meta_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))

# Pydantic Schemas

class ProjectRepositorySchema(BaseModel):
    """Pydantic schema for ProjectRepository"""
    repository_id: str
    repository_role: RepositoryRole = RepositoryRole.PRIMARY
    priority: Optional[int] = 100
    is_critical_path: Optional[bool] = False
    analysis_status: Optional[str] = "pending"
    analysis_progress: Optional[float] = 0.0
    technology_stack: Optional[Dict[str, Any]] = {}
    business_domains: Optional[List[str]] = []
    complexity_factors: Optional[Dict[str, Any]] = {}
    depends_on_repositories: Optional[List[str]] = []
    dependency_strength: Optional[float] = 0.0
    shared_components: Optional[Dict[str, Any]] = {}
    modernization_priority: Optional[int] = 50
    modernization_complexity: Optional[str] = "medium"
    legacy_risk_factors: Optional[Dict[str, Any]] = {}
    modernization_notes: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = {}

    class Config:
        use_enum_values = True

class ProjectPhaseSchema(BaseModel):
    """Pydantic schema for ProjectPhase"""
    phase_name: str
    phase_type: Optional[str] = None
    phase_order: int
    status: Optional[str] = "not_started"
    progress_percentage: Optional[float] = 0.0
    planned_start_date: Optional[datetime] = None
    planned_end_date: Optional[datetime] = None
    repositories_in_scope: Optional[List[str]] = []
    deliverables: Optional[Dict[str, Any]] = {}
    success_criteria: Optional[Dict[str, Any]] = {}
    estimated_effort_hours: Optional[int] = None
    team_assignments: Optional[Dict[str, Any]] = {}
    depends_on_phases: Optional[List[str]] = []
    blocking_issues: Optional[Dict[str, Any]] = {}
    description: Optional[str] = None
    notes: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = {}

class ProjectSchema(BaseModel):
    """Pydantic schema for Project"""
    project_id: str
    name: str
    description: Optional[str] = None
    business_purpose: Optional[str] = None
    status: ProjectStatus = ProjectStatus.PLANNING
    priority: ProjectPriority = ProjectPriority.MEDIUM
    complexity_score: Optional[float] = 0.0
    risk_level: Optional[str] = "medium"
    business_domains: Optional[List[str]] = []
    stakeholders: Optional[Dict[str, Any]] = {}
    business_sponsor: Optional[str] = None
    technical_lead: Optional[str] = None
    modernization_goals: Optional[Dict[str, Any]] = {}
    target_architecture: Optional[Dict[str, Any]] = {}
    modernization_approach: Optional[str] = None
    estimated_duration_months: Optional[int] = None
    planned_start_date: Optional[datetime] = None
    planned_end_date: Optional[datetime] = None
    estimated_effort_hours: Optional[int] = None
    allocated_budget: Optional[float] = None
    team_size: Optional[int] = None
    repository_assignments: Optional[List[ProjectRepositorySchema]] = []
    project_phases: Optional[List[ProjectPhaseSchema]] = []
    tags: Optional[List[str]] = []
    meta_data: Optional[Dict[str, Any]] = {}
    created_by: Optional[str] = None

    class Config:
        use_enum_values = True

# Utility Functions

def generate_project_id(name: str, organization: str = "docxp") -> str:
    """Generate unique project ID from name"""
    # Sanitize name
    sanitized = "".join(c.lower() if c.isalnum() else "_" for c in name)
    sanitized = sanitized.strip("_")[:20]
    
    # Add timestamp for uniqueness
    timestamp = datetime.utcnow().strftime("%Y%m%d")
    
    return f"{organization}_{sanitized}_{timestamp}"

def calculate_project_complexity(repositories: List[ProjectRepositorySchema]) -> float:
    """Calculate overall project complexity score"""
    if not repositories:
        return 0.0
    
    # Factors contributing to complexity
    repo_count = len(repositories)
    technology_diversity = len(set(
        tech for repo in repositories
        for tech in repo.technology_stack.get("languages", [])
    ))
    
    # Dependency complexity
    total_dependencies = sum(len(repo.depends_on_repositories) for repo in repositories)
    avg_dependency_strength = sum(repo.dependency_strength for repo in repositories) / len(repositories)
    
    # Business domain complexity
    domain_count = len(set(
        domain for repo in repositories
        for domain in repo.business_domains
    ))
    
    # Complexity calculation (0-10 scale)
    complexity = (
        min(repo_count / 5, 2.0) * 0.25 +          # Repository count impact
        min(technology_diversity / 10, 2.0) * 0.25 + # Technology diversity
        min(total_dependencies / 20, 2.0) * 0.2 +    # Dependency complexity
        avg_dependency_strength * 2.0 * 0.15 +       # Coupling strength
        min(domain_count / 5, 2.0) * 0.15            # Domain complexity
    ) * 2.5  # Scale to 0-10
    
    return min(complexity, 10.0)

def estimate_project_duration(
    repositories: List[ProjectRepositorySchema],
    team_size: int = 4,
    modernization_approach: str = "phased"
) -> int:
    """Estimate project duration in months"""
    if not repositories:
        return 0
    
    # Base analysis time per repository (weeks)
    base_weeks_per_repo = {
        "small": 2,
        "medium": 4,
        "large": 8,
        "xl": 12
    }
    
    # Calculate total analysis effort
    total_weeks = 0
    for repo in repositories:
        repo_size = repo.modernization_complexity
        weeks = base_weeks_per_repo.get(repo_size, 4)
        
        # Adjust for priority and criticality
        if repo.is_critical_path:
            weeks *= 1.3
        if repo.modernization_priority > 80:
            weeks *= 1.2
        
        total_weeks += weeks
    
    # Adjust for modernization approach
    approach_multipliers = {
        "big_bang": 0.8,      # Parallel approach
        "phased": 1.0,        # Sequential phases
        "strangler_fig": 1.5  # Gradual replacement
    }
    
    multiplier = approach_multipliers.get(modernization_approach, 1.0)
    total_weeks *= multiplier
    
    # Adjust for team size (parallel work)
    parallel_weeks = total_weeks / max(team_size / 2, 1)
    
    # Add project overhead (20%)
    total_weeks_with_overhead = parallel_weeks * 1.2
    
    # Convert to months (4.3 weeks per month)
    months = max(int(total_weeks_with_overhead / 4.3), 1)
    
    return months

def create_default_phases(project_approach: str = "phased") -> List[Dict[str, Any]]:
    """Create default project phases based on approach"""
    if project_approach == "big_bang":
        return [
            {
                "phase_name": "Discovery & Analysis",
                "phase_type": "analysis",
                "phase_order": 1,
                "deliverables": {
                    "business_rules": "Complete business rule extraction",
                    "architecture_assessment": "Current state architecture analysis",
                    "risk_analysis": "Technical and business risk assessment"
                }
            },
            {
                "phase_name": "Modernization Design",
                "phase_type": "design", 
                "phase_order": 2,
                "deliverables": {
                    "target_architecture": "Future state architecture design",
                    "migration_plan": "Detailed migration strategy",
                    "test_strategy": "Testing and validation approach"
                }
            },
            {
                "phase_name": "Implementation & Deployment",
                "phase_type": "implementation",
                "phase_order": 3,
                "deliverables": {
                    "modernized_system": "Fully modernized application",
                    "documentation": "Updated system documentation",
                    "training": "Team training and knowledge transfer"
                }
            }
        ]
    
    elif project_approach == "strangler_fig":
        return [
            {
                "phase_name": "Foundation Setup",
                "phase_type": "setup",
                "phase_order": 1,
                "deliverables": {
                    "facade_layer": "API facade implementation",
                    "monitoring": "Legacy system monitoring",
                    "routing_logic": "Request routing infrastructure"
                }
            },
            {
                "phase_name": "Incremental Migration - Core",
                "phase_type": "implementation",
                "phase_order": 2,
                "deliverables": {
                    "core_services": "Core business services migrated",
                    "data_migration": "Core data migrated",
                    "integration_testing": "Core functionality validated"
                }
            },
            {
                "phase_name": "Incremental Migration - Supporting",
                "phase_type": "implementation", 
                "phase_order": 3,
                "deliverables": {
                    "supporting_services": "Supporting services migrated",
                    "ui_migration": "User interfaces updated",
                    "performance_testing": "Performance validated"
                }
            },
            {
                "phase_name": "Legacy Decommission",
                "phase_type": "cleanup",
                "phase_order": 4,
                "deliverables": {
                    "legacy_shutdown": "Legacy system decommissioned", 
                    "cleanup": "Infrastructure cleanup",
                    "documentation": "Final documentation and handover"
                }
            }
        ]
    
    else:  # phased approach
        return [
            {
                "phase_name": "Phase 1: Discovery",
                "phase_type": "discovery",
                "phase_order": 1,
                "deliverables": {
                    "inventory": "Complete system inventory",
                    "business_rules": "Business rule extraction",
                    "dependencies": "Inter-system dependencies mapped"
                }
            },
            {
                "phase_name": "Phase 2: Assessment",
                "phase_type": "assessment",
                "phase_order": 2,
                "deliverables": {
                    "complexity_analysis": "Complexity and risk assessment",
                    "modernization_plan": "Detailed modernization roadmap",
                    "resource_plan": "Resource and timeline planning"
                }
            },
            {
                "phase_name": "Phase 3: Foundation",
                "phase_type": "implementation",
                "phase_order": 3,
                "deliverables": {
                    "infrastructure": "Modern infrastructure setup",
                    "core_framework": "Application framework migration",
                    "data_layer": "Data access layer modernization"
                }
            },
            {
                "phase_name": "Phase 4: Business Logic",
                "phase_type": "implementation",
                "phase_order": 4,
                "deliverables": {
                    "business_services": "Business logic migration",
                    "integration_points": "External integrations updated",
                    "testing": "Comprehensive testing completed"
                }
            },
            {
                "phase_name": "Phase 5: User Interface",
                "phase_type": "implementation",
                "phase_order": 5,
                "deliverables": {
                    "modern_ui": "Modern user interface",
                    "user_training": "User training and documentation",
                    "go_live": "Production deployment"
                }
            }
        ]