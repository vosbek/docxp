"""
Business Rule Trace Models for DocXP Enterprise
Tracks business logic flows across multiple technologies (JSP → Struts → Java → CORBA → Database)
"""

from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

from app.models.base import Base

class TechnologyType(Enum):
    """Technology types in enterprise stack"""
    JSP = "JSP"
    STRUTS = "Struts"
    STRUTS2 = "Struts2"
    JAVA = "Java"
    CORBA = "CORBA"
    SPRING = "Spring"
    HIBERNATE = "Hibernate"
    DATABASE = "Database"
    SQL = "SQL"
    JAVASCRIPT = "JavaScript"
    ANGULAR = "Angular"
    XML_CONFIG = "XMLConfig"
    PROPERTIES = "Properties"
    WEB_XML = "WebXML"

class FlowStepType(Enum):
    """Types of flow steps in business rule execution"""
    UI_PRESENTATION = "ui_presentation"      # JSP display logic
    ACTION_MAPPING = "action_mapping"        # Struts action mapping
    BUSINESS_LOGIC = "business_logic"        # Java service methods
    DATA_ACCESS = "data_access"              # DAO/Repository methods
    DATABASE_QUERY = "database_query"        # SQL operations
    REMOTE_CALL = "remote_call"              # CORBA/RMI calls
    VALIDATION = "validation"                # Input validation
    TRANSFORMATION = "transformation"        # Data transformation
    CONFIGURATION = "configuration"          # XML/Properties config
    FLOW_CONTROL = "flow_control"           # Conditional logic

class BusinessDomain(Enum):
    """Business domains for enterprise applications"""
    CLAIMS_PROCESSING = "claims_processing"
    POLICY_MANAGEMENT = "policy_management"
    PAYMENT_PROCESSING = "payment_processing"
    CUSTOMER_MANAGEMENT = "customer_management"
    UNDERWRITING = "underwriting"
    BILLING = "billing"
    REPORTING = "reporting"
    AUTHENTICATION = "authentication"
    WORKFLOW_MANAGEMENT = "workflow_management"
    COMPLIANCE = "compliance"
    DOCUMENT_MANAGEMENT = "document_management"
    NOTIFICATION = "notification"
    INTEGRATION = "integration"
    ADMINISTRATION = "administration"

# SQLAlchemy Models

class BusinessRuleTrace(Base):
    """
    Complete business rule trace across technology stack
    Maps end-to-end business process flow
    """
    __tablename__ = "business_rule_traces"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trace_id = Column(String(255), unique=True, nullable=False, index=True)
    rule_name = Column(String(500), nullable=False)
    business_domain = Column(String(100), nullable=False)  # BusinessDomain enum value
    
    # Technology stack involved
    technology_stack = Column(ARRAY(String), nullable=False)  # ["JSP", "Struts", "Java", "CORBA"]
    
    # Flow metadata
    entry_point = Column(String(500), nullable=False)  # Starting file/component
    exit_point = Column(String(500))  # Ending file/component
    flow_complexity = Column(Float, default=0.0)  # Calculated complexity score
    extraction_confidence = Column(Float, default=0.0)  # AI extraction confidence
    
    # Business context
    business_description = Column(Text)  # Human-readable description
    impact_level = Column(String(50), default="medium")  # low, medium, high, critical
    regulatory_relevance = Column(Boolean, default=False)  # SOX, GDPR, etc.
    
    # Traceability
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    commit_hash = Column(String(64), nullable=False)
    extracted_by = Column(String(100))  # AI model or tool used
    extracted_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    flow_steps = relationship("FlowStep", back_populates="business_rule_trace", cascade="all, delete-orphan")
    
    # Metadata
    meta_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class FlowStep(Base):
    """
    Individual step in business rule flow
    Represents one technology transition or logical operation
    """
    __tablename__ = "flow_steps"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trace_id = Column(UUID(as_uuid=True), ForeignKey("business_rule_traces.id"), nullable=False)
    
    # Step identification
    step_order = Column(Integer, nullable=False)  # Sequence in flow
    step_type = Column(String(50), nullable=False)  # FlowStepType enum value
    technology = Column(String(50), nullable=False)  # TechnologyType enum value
    
    # Component details
    component_name = Column(String(500), nullable=False)  # Class, JSP, Action name
    component_type = Column(String(100))  # "class", "method", "jsp", "action", "table"
    file_path = Column(String(1000), nullable=False)
    line_start = Column(Integer)
    line_end = Column(Integer)
    
    # Business logic
    business_logic = Column(Text)  # Extracted business logic description
    business_rules = Column(ARRAY(String))  # List of specific business rules
    data_elements = Column(ARRAY(String))  # Data fields involved
    
    # Dependencies and relationships
    input_parameters = Column(JSON)  # Parameters received
    output_parameters = Column(JSON)  # Parameters produced
    dependencies = Column(ARRAY(String))  # Other components this depends on
    database_tables = Column(ARRAY(String))  # Tables accessed
    
    # Code analysis
    complexity_score = Column(Float, default=0.0)  # Cyclomatic complexity
    risk_indicators = Column(ARRAY(String))  # Security, performance risks
    modernization_notes = Column(Text)  # Suggestions for modernization
    
    # Relationships
    business_rule_trace = relationship("BusinessRuleTrace", back_populates="flow_steps")
    
    # Metadata
    meta_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class CrossTechnologyMapping(Base):
    """
    Maps relationships between different technology components
    Used for impact analysis and modernization planning
    """
    __tablename__ = "cross_technology_mappings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Source and target components
    source_component = Column(String(500), nullable=False)
    source_technology = Column(String(50), nullable=False)
    source_file_path = Column(String(1000), nullable=False)
    
    target_component = Column(String(500), nullable=False)
    target_technology = Column(String(50), nullable=False)
    target_file_path = Column(String(1000), nullable=False)
    
    # Relationship details
    relationship_type = Column(String(100), nullable=False)  # calls, includes, configures, etc.
    relationship_strength = Column(Float, default=1.0)  # 0.0 to 1.0
    coupling_type = Column(String(50))  # tight, loose, none
    
    # Context
    business_context = Column(Text)  # Why this relationship exists
    modernization_impact = Column(Text)  # Impact of changing this relationship
    
    # Traceability
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    discovered_by = Column(String(100))  # Tool or analysis method
    confidence_score = Column(Float, default=0.0)
    
    # Metadata
    meta_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

# Pydantic Schemas for API

class FlowStepSchema(BaseModel):
    """Pydantic schema for FlowStep"""
    step_order: int
    step_type: FlowStepType
    technology: TechnologyType
    component_name: str
    component_type: Optional[str] = None
    file_path: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    business_logic: Optional[str] = None
    business_rules: Optional[List[str]] = []
    data_elements: Optional[List[str]] = []
    input_parameters: Optional[Dict[str, Any]] = {}
    output_parameters: Optional[Dict[str, Any]] = {}
    dependencies: Optional[List[str]] = []
    database_tables: Optional[List[str]] = []
    complexity_score: Optional[float] = 0.0
    risk_indicators: Optional[List[str]] = []
    modernization_notes: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = {}

    class Config:
        use_enum_values = True

class BusinessRuleTraceSchema(BaseModel):
    """Pydantic schema for BusinessRuleTrace"""
    trace_id: str
    rule_name: str
    business_domain: BusinessDomain
    technology_stack: List[TechnologyType]
    entry_point: str
    exit_point: Optional[str] = None
    flow_complexity: Optional[float] = 0.0
    extraction_confidence: Optional[float] = 0.0
    business_description: Optional[str] = None
    impact_level: Optional[str] = "medium"
    regulatory_relevance: Optional[bool] = False
    repository_id: str
    commit_hash: str
    extracted_by: Optional[str] = None
    flow_steps: List[FlowStepSchema] = []
    meta_data: Optional[Dict[str, Any]] = {}

    class Config:
        use_enum_values = True

class CrossTechnologyMappingSchema(BaseModel):
    """Pydantic schema for CrossTechnologyMapping"""
    source_component: str
    source_technology: TechnologyType
    source_file_path: str
    target_component: str
    target_technology: TechnologyType
    target_file_path: str
    relationship_type: str
    relationship_strength: Optional[float] = 1.0
    coupling_type: Optional[str] = None
    business_context: Optional[str] = None
    modernization_impact: Optional[str] = None
    repository_id: str
    discovered_by: Optional[str] = None
    confidence_score: Optional[float] = 0.0
    meta_data: Optional[Dict[str, Any]] = {}

    class Config:
        use_enum_values = True

# Utility Functions

def calculate_flow_complexity(flow_steps: List[FlowStep]) -> float:
    """Calculate complexity score for business rule flow"""
    if not flow_steps:
        return 0.0
    
    # Factors contributing to complexity
    technology_diversity = len(set(step.technology for step in flow_steps))
    step_count = len(flow_steps)
    avg_step_complexity = sum(step.complexity_score or 0 for step in flow_steps) / len(flow_steps)
    database_interactions = sum(1 for step in flow_steps if step.database_tables)
    
    # Weighted complexity calculation
    complexity = (
        technology_diversity * 0.3 +
        (step_count / 10) * 0.2 +
        avg_step_complexity * 0.3 +
        database_interactions * 0.2
    )
    
    return min(complexity, 10.0)  # Cap at 10.0

def extract_technology_stack(flow_steps: List[FlowStep]) -> List[str]:
    """Extract unique technologies involved in flow"""
    technologies = []
    seen = set()
    
    for step in sorted(flow_steps, key=lambda x: x.step_order):
        if step.technology not in seen:
            technologies.append(step.technology)
            seen.add(step.technology)
    
    return technologies

def identify_business_domain(rule_name: str, flow_steps: List[FlowStep]) -> BusinessDomain:
    """Use heuristics to identify business domain from rule name and flow"""
    rule_lower = rule_name.lower()
    
    # Domain keyword mapping
    domain_keywords = {
        BusinessDomain.CLAIMS_PROCESSING: ["claim", "settlement", "adjudication", "coverage"],
        BusinessDomain.POLICY_MANAGEMENT: ["policy", "contract", "premium", "renewal"],
        BusinessDomain.PAYMENT_PROCESSING: ["payment", "billing", "invoice", "transaction"],
        BusinessDomain.CUSTOMER_MANAGEMENT: ["customer", "client", "member", "contact"],
        BusinessDomain.UNDERWRITING: ["underwrite", "risk", "assessment", "approval"],
        BusinessDomain.AUTHENTICATION: ["login", "auth", "security", "credential"],
        BusinessDomain.REPORTING: ["report", "analytics", "dashboard", "metrics"],
        BusinessDomain.WORKFLOW_MANAGEMENT: ["workflow", "approval", "routing", "queue"],
        BusinessDomain.COMPLIANCE: ["compliance", "audit", "regulatory", "sox"],
        BusinessDomain.DOCUMENT_MANAGEMENT: ["document", "upload", "attachment", "file"],
    }
    
    # Check rule name for domain keywords
    for domain, keywords in domain_keywords.items():
        if any(keyword in rule_lower for keyword in keywords):
            return domain
    
    # Check flow steps for domain indicators
    for step in flow_steps:
        step_text = f"{step.component_name} {step.business_logic or ''}".lower()
        for domain, keywords in domain_keywords.items():
            if any(keyword in step_text for keyword in keywords):
                return domain
    
    # Default to integration if unclear
    return BusinessDomain.INTEGRATION