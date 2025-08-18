"""
Architectural Insight Models for DocXP Enterprise
Captures and manages architectural insights, recommendations, and knowledge for enterprise modernization
"""

from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

from app.models.base import Base

class InsightType(Enum):
    """Types of architectural insights"""
    RISK = "risk"                           # Technical or business risk identification
    RECOMMENDATION = "recommendation"        # Modernization or improvement recommendation
    PATTERN = "pattern"                     # Architectural pattern detection
    ANTI_PATTERN = "anti_pattern"          # Anti-pattern identification
    DEPENDENCY = "dependency"               # Dependency analysis insight
    PERFORMANCE = "performance"             # Performance-related insight
    SECURITY = "security"                   # Security concern or recommendation
    MAINTAINABILITY = "maintainability"     # Code maintainability insight
    BUSINESS_RULE = "business_rule"         # Business rule extraction/analysis
    MODERNIZATION = "modernization"         # Specific modernization guidance
    COMPLIANCE = "compliance"               # Regulatory compliance insight
    TECHNICAL_DEBT = "technical_debt"       # Technical debt identification

class InsightSeverity(Enum):
    """Severity levels for insights"""
    CRITICAL = "critical"       # Requires immediate attention
    HIGH = "high"              # Important but not blocking
    MEDIUM = "medium"          # Should be addressed
    LOW = "low"               # Nice to have
    INFO = "info"             # Informational only

class ModernizationImpact(Enum):
    """Impact of modernization on the insight"""
    BREAKING_CHANGE = "breaking_change"     # Requires significant refactoring
    MODERATE_CHANGE = "moderate_change"     # Requires some refactoring
    MINOR_CHANGE = "minor_change"          # Minimal changes required
    NO_CHANGE = "no_change"                # No changes required
    BENEFICIAL = "beneficial"               # Modernization improves this area
    UNKNOWN = "unknown"                    # Impact not yet determined

class InsightStatus(Enum):
    """Status of insight handling"""
    NEW = "new"                     # Newly discovered
    ACKNOWLEDGED = "acknowledged"    # Reviewed but not acted upon
    IN_PROGRESS = "in_progress"     # Being addressed
    RESOLVED = "resolved"           # Successfully addressed
    DEFERRED = "deferred"          # Postponed to later phase
    REJECTED = "rejected"          # Determined not to be valid/important
    SUPERSEDED = "superseded"      # Replaced by newer insight

# SQLAlchemy Models

class ArchitecturalInsight(Base):
    """
    Core architectural insight capturing business and technical knowledge
    """
    __tablename__ = "enterprise_architectural_insights"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    insight_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Classification
    insight_type = Column(String(50), nullable=False)  # InsightType enum
    severity = Column(String(50), default="medium")    # InsightSeverity enum
    category = Column(String(100))  # Custom categorization
    tags = Column(ARRAY(String))   # Searchable tags
    
    # Core content
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    business_context = Column(Text)  # Business relevance and context
    technical_details = Column(Text)  # Technical specifics
    
    # Relationships to code
    business_rules = Column(ARRAY(String))  # Related business rule IDs
    affected_components = Column(JSON)  # Components impacted by this insight
    file_references = Column(JSON)  # Specific file/line references
    
    # Modernization guidance
    modernization_impact = Column(String(50), default="unknown")  # ModernizationImpact enum
    modernization_priority = Column(Integer, default=50)  # 1-100 priority score
    modernization_effort = Column(String(50))  # small, medium, large, xl
    modernization_approach = Column(Text)  # Recommended approach
    
    # Architect knowledge
    architect_notes = Column(Text)  # Human architect insights
    recommendations = Column(JSON)  # Specific recommendations list
    alternatives = Column(JSON)  # Alternative approaches
    risks = Column(JSON)  # Associated risks
    benefits = Column(JSON)  # Expected benefits
    
    # Quality metrics
    confidence_score = Column(Float, default=0.0)  # 0.0 to 1.0
    evidence_strength = Column(String(50), default="medium")  # weak, medium, strong
    validation_status = Column(String(50), default="unvalidated")  # validated, unvalidated, disputed
    
    # Lifecycle management
    status = Column(String(50), default="new")  # InsightStatus enum
    assigned_to = Column(String(100))  # Architect or team responsible
    target_phase = Column(String(100))  # Which modernization phase to address
    estimated_effort_hours = Column(Integer)  # Effort estimate
    
    # Traceability
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    commit_hash = Column(String(64), nullable=False)
    discovered_by = Column(String(100))  # AI model, tool, or human
    discovery_method = Column(String(100))  # Method used to discover insight
    
    # Relationships
    dependencies = relationship("InsightDependency", foreign_keys="InsightDependency.source_insight_id", back_populates="source_insight")
    dependents = relationship("InsightDependency", foreign_keys="InsightDependency.target_insight_id", back_populates="target_insight")
    
    # Metadata
    meta_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    reviewed_at = Column(DateTime)
    reviewed_by = Column(String(100))

class InsightDependency(Base):
    """
    Captures dependencies between architectural insights
    """
    __tablename__ = "insight_dependencies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Dependency relationship
    source_insight_id = Column(UUID(as_uuid=True), ForeignKey("enterprise_architectural_insights.id"), nullable=False)
    target_insight_id = Column(UUID(as_uuid=True), ForeignKey("enterprise_architectural_insights.id"), nullable=False)
    dependency_type = Column(String(50), nullable=False)  # blocks, related_to, builds_on, conflicts_with
    dependency_strength = Column(String(50), default="medium")  # weak, medium, strong
    
    # Context
    description = Column(Text)
    business_rationale = Column(Text)
    technical_rationale = Column(Text)
    
    # Relationships
    source_insight = relationship("ArchitecturalInsight", foreign_keys=[source_insight_id], back_populates="dependencies")
    target_insight = relationship("ArchitecturalInsight", foreign_keys=[target_insight_id], back_populates="dependents")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))

class InsightEvolution(Base):
    """
    Tracks how insights evolve over time as code changes
    """
    __tablename__ = "insight_evolution"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    insight_id = Column(UUID(as_uuid=True), ForeignKey("enterprise_architectural_insights.id"), nullable=False)
    
    # Evolution tracking
    version = Column(Integer, nullable=False)
    change_type = Column(String(50), nullable=False)  # created, updated, resolved, invalidated
    change_description = Column(Text)
    
    # State snapshot
    previous_state = Column(JSON)  # Previous insight state
    new_state = Column(JSON)  # New insight state
    
    # Context
    trigger = Column(String(100))  # code_change, manual_update, ai_analysis
    commit_hash = Column(String(64))
    changed_by = Column(String(100))
    
    # Relationships
    insight = relationship("ArchitecturalInsight")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

class KnowledgeArticle(Base):
    """
    Reusable knowledge articles extracted from insights
    """
    __tablename__ = "knowledge_articles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id = Column(String(255), unique=True, nullable=False)
    
    # Content
    title = Column(String(500), nullable=False)
    summary = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(100))
    
    # Knowledge metadata
    knowledge_type = Column(String(50))  # pattern, anti_pattern, best_practice, pitfall
    applicability = Column(JSON)  # When this knowledge applies
    technology_stack = Column(ARRAY(String))  # Relevant technologies
    business_domains = Column(ARRAY(String))  # Applicable business domains
    
    # Quality
    confidence_level = Column(String(50), default="medium")  # low, medium, high
    evidence_count = Column(Integer, default=0)  # Number of supporting insights
    usage_count = Column(Integer, default=0)  # How often referenced
    
    # Lifecycle
    status = Column(String(50), default="draft")  # draft, published, deprecated
    authored_by = Column(String(100))
    reviewed_by = Column(String(100))
    
    # Metadata
    meta_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Pydantic Schemas

class ArchitecturalInsightSchema(BaseModel):
    """Pydantic schema for ArchitecturalInsight"""
    insight_id: str
    insight_type: InsightType
    severity: InsightSeverity = InsightSeverity.MEDIUM
    category: Optional[str] = None
    tags: Optional[List[str]] = []
    title: str
    description: str
    business_context: Optional[str] = None
    technical_details: Optional[str] = None
    business_rules: Optional[List[str]] = []
    affected_components: Optional[Dict[str, Any]] = {}
    file_references: Optional[Dict[str, Any]] = {}
    modernization_impact: ModernizationImpact = ModernizationImpact.UNKNOWN
    modernization_priority: Optional[int] = 50
    modernization_effort: Optional[str] = None
    modernization_approach: Optional[str] = None
    architect_notes: Optional[str] = None
    recommendations: Optional[List[Dict[str, Any]]] = []
    alternatives: Optional[List[Dict[str, Any]]] = []
    risks: Optional[List[Dict[str, Any]]] = []
    benefits: Optional[List[Dict[str, Any]]] = []
    confidence_score: Optional[float] = 0.0
    evidence_strength: Optional[str] = "medium"
    validation_status: Optional[str] = "unvalidated"
    status: InsightStatus = InsightStatus.NEW
    assigned_to: Optional[str] = None
    target_phase: Optional[str] = None
    estimated_effort_hours: Optional[int] = None
    repository_id: str
    commit_hash: str
    discovered_by: Optional[str] = None
    discovery_method: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = {}

    class Config:
        use_enum_values = True

class InsightDependencySchema(BaseModel):
    """Pydantic schema for InsightDependency"""
    source_insight_id: str
    target_insight_id: str
    dependency_type: str
    dependency_strength: Optional[str] = "medium"
    description: Optional[str] = None
    business_rationale: Optional[str] = None
    technical_rationale: Optional[str] = None
    created_by: Optional[str] = None

class KnowledgeArticleSchema(BaseModel):
    """Pydantic schema for KnowledgeArticle"""
    article_id: str
    title: str
    summary: str
    content: str
    category: Optional[str] = None
    knowledge_type: Optional[str] = None
    applicability: Optional[Dict[str, Any]] = {}
    technology_stack: Optional[List[str]] = []
    business_domains: Optional[List[str]] = []
    confidence_level: Optional[str] = "medium"
    evidence_count: Optional[int] = 0
    usage_count: Optional[int] = 0
    status: Optional[str] = "draft"
    authored_by: Optional[str] = None
    reviewed_by: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = {}

# Utility Functions

def create_insight_id(repository_id: str, component_name: str, insight_type: str) -> str:
    """Generate unique insight ID"""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"{repository_id[:8]}_{component_name[:20]}_{insight_type}_{timestamp}"

def calculate_modernization_priority(
    severity: InsightSeverity,
    business_impact: str,
    technical_complexity: str,
    dependencies: int
) -> int:
    """Calculate modernization priority score (1-100)"""
    
    # Base score from severity
    severity_scores = {
        InsightSeverity.CRITICAL: 90,
        InsightSeverity.HIGH: 70,
        InsightSeverity.MEDIUM: 50,
        InsightSeverity.LOW: 30,
        InsightSeverity.INFO: 10
    }
    
    base_score = severity_scores.get(severity, 50)
    
    # Adjust for business impact
    business_adjustments = {
        "high": 20,
        "medium": 0,
        "low": -10,
        "none": -20
    }
    
    business_adj = business_adjustments.get(business_impact.lower(), 0)
    
    # Adjust for technical complexity (inverse - simpler = higher priority)
    complexity_adjustments = {
        "low": 10,
        "medium": 0,
        "high": -10,
        "very_high": -20
    }
    
    complexity_adj = complexity_adjustments.get(technical_complexity.lower(), 0)
    
    # Adjust for dependencies (more dependencies = higher priority)
    dependency_adj = min(dependencies * 5, 20)
    
    # Calculate final score
    final_score = base_score + business_adj + complexity_adj + dependency_adj
    
    # Clamp to 1-100 range
    return max(1, min(100, final_score))

def categorize_modernization_effort(
    affected_components: Dict[str, Any],
    complexity_score: float,
    dependency_count: int
) -> str:
    """Categorize effort required for modernization"""
    
    component_count = len(affected_components.get("files", []))
    
    # Calculate effort score
    effort_score = (
        component_count * 0.3 +
        complexity_score * 0.4 +
        dependency_count * 0.3
    )
    
    if effort_score < 2:
        return "small"
    elif effort_score < 5:
        return "medium"
    elif effort_score < 10:
        return "large"
    else:
        return "xl"

def extract_evidence_from_code(
    file_content: str,
    line_start: int,
    line_end: int,
    context_lines: int = 3
) -> Dict[str, Any]:
    """Extract code evidence for insight"""
    lines = file_content.split('\n')
    
    # Get context around the relevant lines
    start_idx = max(0, line_start - context_lines - 1)
    end_idx = min(len(lines), line_end + context_lines)
    
    evidence = {
        "line_start": line_start,
        "line_end": line_end,
        "context_start": start_idx + 1,
        "context_end": end_idx,
        "code_snippet": '\n'.join(lines[start_idx:end_idx]),
        "relevant_lines": '\n'.join(lines[line_start-1:line_end])
    }
    
    return evidence

def generate_insight_summary(insights: List[ArchitecturalInsight]) -> Dict[str, Any]:
    """Generate summary statistics from a list of insights"""
    if not insights:
        return {}
    
    summary = {
        "total_count": len(insights),
        "by_type": {},
        "by_severity": {},
        "by_status": {},
        "avg_confidence": 0.0,
        "high_priority_count": 0,
        "unresolved_count": 0
    }
    
    total_confidence = 0.0
    
    for insight in insights:
        # Count by type
        insight_type = insight.insight_type
        summary["by_type"][insight_type] = summary["by_type"].get(insight_type, 0) + 1
        
        # Count by severity
        severity = insight.severity
        summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1
        
        # Count by status
        status = insight.status
        summary["by_status"][status] = summary["by_status"].get(status, 0) + 1
        
        # Accumulate confidence
        total_confidence += insight.confidence_score or 0.0
        
        # Count high priority and unresolved
        if insight.modernization_priority and insight.modernization_priority > 70:
            summary["high_priority_count"] += 1
        
        if insight.status in ["new", "acknowledged", "in_progress"]:
            summary["unresolved_count"] += 1
    
    summary["avg_confidence"] = total_confidence / len(insights)
    
    return summary