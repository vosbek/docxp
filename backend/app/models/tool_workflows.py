"""
Tool Workflow Models for Enhanced Single-Agent Tool Integration

Defines tool sequences and workflows for common enterprise analysis patterns.
Part of Week 5 implementation.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid

from sqlalchemy import Column, String, Text, DateTime, Integer, Float, Boolean
from sqlalchemy.dialects.postgresql import JSON
from app.models.base import Base


class ToolExecutionStatus(Enum):
    """Status of tool execution in a workflow"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowStatus(Enum):
    """Overall workflow execution status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ToolStep:
    """Represents a single tool execution step in a workflow"""
    tool_name: str
    tool_function: str
    parameters: Dict[str, Any]
    depends_on: List[str] = field(default_factory=list)  # Tool names this step depends on
    timeout_seconds: int = 300
    retry_count: int = 3
    required: bool = True
    condition: Optional[str] = None  # Python expression for conditional execution
    
    def __post_init__(self):
        self.step_id = str(uuid.uuid4())
        self.status = ToolExecutionStatus.PENDING
        self.result: Optional[Dict[str, Any]] = None
        self.error_message: Optional[str] = None
        self.execution_time: float = 0.0
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None


@dataclass
class ToolSequence:
    """Defines a sequence of tool executions for common analysis patterns"""
    sequence_id: str
    name: str
    description: str
    tools: List[ToolStep]
    success_criteria: List[str]
    timeout_minutes: int = 30
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        self.status = WorkflowStatus.NOT_STARTED
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.results: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}


class WorkflowExecution(Base):
    """Database model for tracking workflow executions"""
    __tablename__ = "workflow_executions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, nullable=False)
    sequence_id = Column(String, nullable=False)
    sequence_name = Column(String, nullable=False)
    status = Column(String, nullable=False, default=WorkflowStatus.NOT_STARTED.value)
    
    # Execution tracking
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    total_duration_seconds = Column(Float, nullable=True)
    
    # Results and metadata
    results = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)
    
    # Tool execution details
    tool_executions = Column(JSON, nullable=True)  # List of tool execution details
    success_rate = Column(Float, nullable=True)  # Percentage of successful tool executions
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PredefinedWorkflows:
    """Factory class for creating predefined tool sequence workflows"""
    
    @staticmethod
    def legacy_modernization_analysis() -> ToolSequence:
        """Workflow for comprehensive legacy modernization analysis"""
        return ToolSequence(
            sequence_id="legacy_modernization_analysis",
            name="Legacy Modernization Analysis",
            description="Comprehensive analysis of legacy system for modernization planning",
            category="modernization",
            tags=["legacy", "migration", "analysis", "spring-boot", "struts"],
            tools=[
                ToolStep(
                    tool_name="repository_analyzer",
                    tool_function="analyze_repository", 
                    parameters={"include_dependencies": True, "analyze_patterns": True}
                ),
                ToolStep(
                    tool_name="flow_tracer",
                    tool_function="trace_business_rules",
                    parameters={"max_traces": 10, "priority": "high"},
                    depends_on=["repository_analyzer"]
                ),
                ToolStep(
                    tool_name="flow_validator", 
                    tool_function="validate_flows",
                    parameters={"validation_level": "comprehensive"},
                    depends_on=["flow_tracer"]
                ),
                ToolStep(
                    tool_name="risk_assessor",
                    tool_function="assess_migration_risks",
                    parameters={"risk_categories": ["technical", "business", "timeline"]},
                    depends_on=["flow_validator"]
                ),
                ToolStep(
                    tool_name="modernization_planner",
                    tool_function="generate_migration_plan", 
                    parameters={"target_framework": "spring-boot", "approach": "phased"},
                    depends_on=["risk_assessor"]
                )
            ],
            success_criteria=[
                "Repository analysis completed with >90% coverage",
                "At least 5 business rule flows traced and validated",
                "Migration risks identified and categorized",
                "Modernization plan generated with timeline"
            ],
            timeout_minutes=45
        )
    
    @staticmethod
    def cross_repository_impact_analysis() -> ToolSequence:
        """Workflow for analyzing impact across multiple repositories"""
        return ToolSequence(
            sequence_id="cross_repo_impact_analysis",
            name="Cross-Repository Impact Analysis",
            description="Analyze the impact of changes across multiple repositories",
            category="impact_analysis",
            tags=["cross-repo", "impact", "dependencies", "portfolio"],
            tools=[
                ToolStep(
                    tool_name="cross_repo_discovery",
                    tool_function="discover_shared_components",
                    parameters={"analysis_depth": "deep", "include_transitive": True}
                ),
                ToolStep(
                    tool_name="dependency_mapper",
                    tool_function="map_dependencies",
                    parameters={"scope": "portfolio", "include_external": True},
                    depends_on=["cross_repo_discovery"]
                ),
                ToolStep(
                    tool_name="flow_tracer",
                    tool_function="trace_cross_repo_flows",
                    parameters={"max_depth": 3, "follow_api_calls": True},
                    depends_on=["dependency_mapper"]
                ),
                ToolStep(
                    tool_name="impact_analyzer",
                    tool_function="analyze_change_impact",
                    parameters={"change_scope": "component", "ripple_analysis": True},
                    depends_on=["flow_tracer"]
                )
            ],
            success_criteria=[
                "Shared components identified across repositories",
                "Cross-repository dependencies mapped",
                "Impact analysis completed with confidence scores",
                "Change recommendations provided"
            ],
            timeout_minutes=30
        )
    
    @staticmethod
    def business_rule_extraction() -> ToolSequence:
        """Workflow for extracting and documenting business rules"""
        return ToolSequence(
            sequence_id="business_rule_extraction", 
            name="Business Rule Extraction",
            description="Extract and document business rules from legacy code",
            category="documentation",
            tags=["business-rules", "documentation", "extraction", "analysis"],
            tools=[
                ToolStep(
                    tool_name="repository_analyzer",
                    tool_function="identify_business_logic_components",
                    parameters={"focus": "business_rules", "confidence_threshold": 0.7}
                ),
                ToolStep(
                    tool_name="flow_tracer",
                    tool_function="trace_business_rule_flows",
                    parameters={"trace_type": "business_logic", "include_data_flow": True},
                    depends_on=["repository_analyzer"]
                ),
                ToolStep(
                    tool_name="business_rule_extractor",
                    tool_function="extract_rules_from_traces",
                    parameters={"extraction_method": "ai_powered", "validate_rules": True},
                    depends_on=["flow_tracer"]
                ),
                ToolStep(
                    tool_name="rule_documenter",
                    tool_function="generate_rule_documentation",
                    parameters={"format": "structured", "include_examples": True},
                    depends_on=["business_rule_extractor"]
                )
            ],
            success_criteria=[
                "Business logic components identified",
                "Business rule flows traced with high confidence",
                "Rules extracted and validated",
                "Documentation generated in structured format"
            ],
            timeout_minutes=25
        )
    
    @staticmethod
    def architecture_health_check() -> ToolSequence:
        """Workflow for comprehensive architecture health assessment"""
        return ToolSequence(
            sequence_id="architecture_health_check",
            name="Architecture Health Check", 
            description="Comprehensive assessment of system architecture health",
            category="assessment",
            tags=["architecture", "health", "assessment", "quality", "technical-debt"],
            tools=[
                ToolStep(
                    tool_name="repository_analyzer",
                    tool_function="analyze_code_quality",
                    parameters={"metrics": ["complexity", "coupling", "cohesion"], "detailed": True}
                ),
                ToolStep(
                    tool_name="pattern_detector",
                    tool_function="detect_architectural_patterns",
                    parameters={"pattern_types": ["design_patterns", "anti_patterns"], "confidence_threshold": 0.8},
                    depends_on=["repository_analyzer"]
                ),
                ToolStep(
                    tool_name="dependency_analyzer", 
                    tool_function="analyze_dependency_health",
                    parameters={"check_circular": True, "analyze_coupling": True},
                    depends_on=["repository_analyzer"]
                ),
                ToolStep(
                    tool_name="technical_debt_assessor",
                    tool_function="calculate_technical_debt",
                    parameters={"debt_categories": ["code", "architecture", "documentation"]},
                    depends_on=["pattern_detector", "dependency_analyzer"]
                )
            ],
            success_criteria=[
                "Code quality metrics calculated",
                "Architectural patterns identified",
                "Dependency health assessed",
                "Technical debt quantified with recommendations"
            ],
            timeout_minutes=20
        )
    
    @classmethod
    def get_all_predefined_workflows(cls) -> List[ToolSequence]:
        """Get all predefined workflows"""
        return [
            cls.legacy_modernization_analysis(),
            cls.cross_repository_impact_analysis(),
            cls.business_rule_extraction(),
            cls.architecture_health_check()
        ]
    
    @classmethod
    def get_workflow_by_id(cls, sequence_id: str) -> Optional[ToolSequence]:
        """Get a specific workflow by its sequence_id"""
        workflows = {
            "legacy_modernization_analysis": cls.legacy_modernization_analysis,
            "cross_repo_impact_analysis": cls.cross_repository_impact_analysis,
            "business_rule_extraction": cls.business_rule_extraction,
            "architecture_health_check": cls.architecture_health_check
        }
        
        workflow_factory = workflows.get(sequence_id)
        return workflow_factory() if workflow_factory else None
    
    @classmethod
    def get_workflows_by_category(cls, category: str) -> List[ToolSequence]:
        """Get workflows by category"""
        all_workflows = cls.get_all_predefined_workflows()
        return [wf for wf in all_workflows if wf.category == category]
    
    @classmethod
    def get_workflows_by_tags(cls, tags: List[str]) -> List[ToolSequence]:
        """Get workflows that contain any of the specified tags"""
        all_workflows = cls.get_all_predefined_workflows()
        return [wf for wf in all_workflows if any(tag in wf.tags for tag in tags)]


# Workflow recommendation system
class WorkflowRecommender:
    """Recommends appropriate workflows based on user queries and context"""
    
    @staticmethod
    def recommend_workflows(query: str, context: Dict[str, Any] = None) -> List[ToolSequence]:
        """Recommend workflows based on query and context"""
        context = context or {}
        recommendations = []
        
        query_lower = query.lower()
        
        # Legacy modernization keywords
        if any(keyword in query_lower for keyword in [
            "modernize", "migrate", "legacy", "struts", "spring boot", 
            "upgrade", "transformation", "migration"
        ]):
            recommendations.append(PredefinedWorkflows.legacy_modernization_analysis())
        
        # Impact analysis keywords  
        if any(keyword in query_lower for keyword in [
            "impact", "change", "affect", "dependency", "ripple", 
            "cross repository", "shared component"
        ]):
            recommendations.append(PredefinedWorkflows.cross_repository_impact_analysis())
        
        # Business rule extraction keywords
        if any(keyword in query_lower for keyword in [
            "business rule", "extract", "document", "business logic",
            "workflow", "process", "rule"
        ]):
            recommendations.append(PredefinedWorkflows.business_rule_extraction())
        
        # Architecture assessment keywords
        if any(keyword in query_lower for keyword in [
            "architecture", "health", "assessment", "quality", "debt",
            "pattern", "anti-pattern", "coupling", "complexity"
        ]):
            recommendations.append(PredefinedWorkflows.architecture_health_check())
        
        # Default to modernization analysis if no specific workflow identified
        if not recommendations:
            recommendations.append(PredefinedWorkflows.legacy_modernization_analysis())
        
        return recommendations[:3]  # Return top 3 recommendations