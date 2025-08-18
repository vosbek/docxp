# Models Package

# Import base model first
from .base import Base

# Import repository model from core database (existing model)
from app.core.database import Repository

# Import indexing models for V1 system
from .indexing_models import (
    IndexingJob,
    JobStatus as IndexingJobStatus,
    JobType as IndexingJobType,
    FileProcessingRecord,
    FileStatus as FileProcessingStatus,
    RepositorySnapshot,
    EmbeddingCache,
    CodeEntityData,
    IndexingHealthMetrics,
)

# Import business rule and domain models for Week 2
from .business_rule_trace import (
    BusinessRuleTrace,
    FlowStep,
    CrossTechnologyMapping,
    TechnologyType,
    FlowStepType,
    BusinessDomain,
)

from .business_domains import (
    DomainTaxonomy,
    DomainClassificationRule,
    DomainClassificationResult,
    DomainCategory,
    BusinessSubdomain,
)

from .architectural_insight import (
    ArchitecturalInsight,
    InsightDependency,
    InsightEvolution,
    KnowledgeArticle,
    InsightType,
    InsightSeverity,
    ModernizationImpact,
    InsightStatus,
)

# Import project models for Week 3
from .project import (
    Project,
    ProjectRepository,
    ProjectPhase,
    ProjectDependency,
    ProjectStatus,
    ProjectPriority,
    RepositoryRole,
)

# Import graph entities
from .graph_entities import (
    GraphNodeType,
    GraphRelationshipType,
    GraphNodeProperties,
    GraphRelationshipProperties,
)

__all__ = [
    # Base Model
    "Base",
    
    # Repository Model
    "Repository",
    
    # V1 Indexing Models
    "IndexingJob",
    "IndexingJobStatus", 
    "IndexingJobType",
    "FileProcessingRecord",
    "FileProcessingStatus",
    "RepositorySnapshot",
    "EmbeddingCache",
    "CodeEntityData",
    "IndexingHealthMetrics",
    
    # Week 2 Business Rule Models
    "BusinessRuleTrace",
    "FlowStep",
    "CrossTechnologyMapping",
    "TechnologyType",
    "FlowStepType",
    "BusinessDomain",
    
    # Domain Classification Models
    "DomainTaxonomy",
    "DomainClassificationRule",
    "DomainClassificationResult",
    "DomainCategory",
    "BusinessSubdomain",
    
    # Architectural Insight Models
    "ArchitecturalInsight",
    "InsightDependency",
    "InsightEvolution",
    "KnowledgeArticle",
    "InsightType",
    "InsightSeverity",
    "ModernizationImpact",
    "InsightStatus",
    
    # Project Models
    "Project",
    "ProjectRepository", 
    "ProjectPhase",
    "ProjectDependency",
    "ProjectStatus",
    "ProjectPriority",
    "RepositoryRole",
    
    # Graph Models
    "GraphNodeType",
    "GraphRelationshipType",
    "GraphNodeProperties",
    "GraphRelationshipProperties",
]
