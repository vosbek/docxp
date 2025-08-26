"""
Graph Entity Models for DocXP Knowledge Graph
Defines the data models for nodes and relationships in the Neo4j knowledge graph
"""

from typing import Dict, List, Any, Optional, Set, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, String, Text, Integer, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base

from app.models.base import Base

class GraphNodeType(str, Enum):
    """Types of nodes in the knowledge graph"""
    # Code Structure Entities
    CODE_ENTITY = "CodeEntity"
    CLASS = "Class"
    METHOD = "Method"
    FUNCTION = "Function"
    INTERFACE = "Interface"
    PACKAGE = "Package"
    MODULE = "Module"
    
    # Business Logic Entities  
    BUSINESS_RULE = "BusinessRule"
    BUSINESS_PROCESS = "BusinessProcess"
    BUSINESS_DOMAIN = "BusinessDomain"
    
    # Technology Entities
    TECHNOLOGY_COMPONENT = "TechnologyComponent"
    FRAMEWORK = "Framework"
    LIBRARY = "Library"
    DATABASE = "Database"
    DATABASE_TABLE = "DatabaseTable"
    DATABASE_COLUMN = "DatabaseColumn"
    
    # Web/UI Entities
    JSP_PAGE = "JSPPage"
    HTML_PAGE = "HTMLPage"
    JAVASCRIPT_COMPONENT = "JavaScriptComponent"
    CSS_STYLESHEET = "CSSStylesheet"
    
    # Struts Entities
    STRUTS_ACTION = "StrutsAction"
    STRUTS_FORM = "StrutsForm"
    STRUTS_CONFIG = "StrutsConfig"
    ACTION_MAPPING = "ActionMapping"
    
    # System Entities
    REPOSITORY = "Repository"
    PROJECT = "Project"
    FILE = "File"
    DIRECTORY = "Directory"
    
    # API/Service Entities
    API_ENDPOINT = "APIEndpoint"
    REST_SERVICE = "RESTService"
    SOAP_SERVICE = "SOAPService"
    CORBA_INTERFACE = "CORBAInterface"
    
    # Configuration Entities
    CONFIG_FILE = "ConfigFile"
    PROPERTY_FILE = "PropertyFile"
    XML_CONFIG = "XMLConfig"

class GraphRelationshipType(str, Enum):
    """Types of relationships in the knowledge graph"""
    # Code Structure Relationships
    CALLS = "CALLS"
    IMPLEMENTS = "IMPLEMENTS"  
    EXTENDS = "EXTENDS"
    OVERRIDES = "OVERRIDES"
    IMPORTS = "IMPORTS"
    DEPENDS_ON = "DEPENDS_ON"
    CONTAINS = "CONTAINS"
    DEFINES = "DEFINES"
    USES = "USES"
    REFERENCES = "REFERENCES"
    INHERITS_FROM = "INHERITS_FROM"
    
    # Business Flow Relationships
    FLOWS_TO = "FLOWS_TO"
    FORWARDS_TO = "FORWARDS_TO"
    REDIRECTS_TO = "REDIRECTS_TO"
    PROCESSES = "PROCESSES"
    VALIDATES = "VALIDATES"
    TRANSFORMS = "TRANSFORMS"
    
    # Organizational Relationships
    BELONGS_TO = "BELONGS_TO"
    PART_OF = "PART_OF"
    MANAGES = "MANAGES"
    OWNED_BY = "OWNED_BY"
    
    # Communication Relationships
    COMMUNICATES_WITH = "COMMUNICATES_WITH"
    SENDS_TO = "SENDS_TO"
    RECEIVES_FROM = "RECEIVES_FROM"
    PUBLISHES = "PUBLISHES"
    SUBSCRIBES_TO = "SUBSCRIBES_TO"
    
    # Data Relationships
    READS_FROM = "READS_FROM"
    WRITES_TO = "WRITES_TO"
    UPDATES = "UPDATES"
    DELETES = "DELETES"
    QUERIES = "QUERIES"

@dataclass
class GraphNodeProperties:
    """Base properties for all graph nodes"""
    name: str
    type: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    source_file: Optional[str] = None
    line_number: Optional[int] = None
    repository_id: Optional[str] = None
    project_id: Optional[str] = None
    technology_stack: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CodeEntityProperties(GraphNodeProperties):
    """Properties for code entities (classes, methods, etc.)"""
    fully_qualified_name: str = ""
    visibility: str = "public"  # public, private, protected
    is_abstract: bool = False
    is_static: bool = False
    is_final: bool = False
    parameters: List[Dict[str, str]] = field(default_factory=list)
    return_type: Optional[str] = None
    annotations: List[str] = field(default_factory=list)
    documentation: Optional[str] = None
    complexity_score: Optional[float] = None
    lines_of_code: Optional[int] = None
    cyclomatic_complexity: Optional[int] = None

@dataclass  
class BusinessRuleProperties(GraphNodeProperties):
    """Properties for business rules"""
    description: str = ""
    category: str = "general"
    priority: str = "medium"  # low, medium, high, critical
    confidence_score: float = 0.0
    validation_rules: List[str] = field(default_factory=list)
    business_domain: Optional[str] = None
    stakeholders: List[str] = field(default_factory=list)
    implementation_files: List[str] = field(default_factory=list)
    last_modified_by: Optional[str] = None
    change_frequency: str = "low"  # low, medium, high
    impact_level: str = "medium"  # low, medium, high

@dataclass
class TechnologyComponentProperties(GraphNodeProperties):
    """Properties for technology components"""
    version: Optional[str] = None
    vendor: Optional[str] = None
    category: str = "framework"  # framework, library, database, service
    license: Optional[str] = None
    documentation_url: Optional[str] = None
    deprecation_status: str = "active"  # active, deprecated, legacy
    security_risk_level: str = "low"  # low, medium, high
    migration_complexity: str = "medium"  # low, medium, high
    replacement_options: List[str] = field(default_factory=list)

@dataclass
class StrutsActionProperties(GraphNodeProperties):
    """Properties specific to Struts actions"""
    action_path: str = ""
    action_class: str = ""
    method_name: str = "execute"
    form_bean: Optional[str] = None
    scope: str = "request"  # request, session, application
    validation_enabled: bool = True
    input_page: Optional[str] = None
    success_forward: Optional[str] = None
    error_forward: Optional[str] = None
    exception_mappings: Dict[str, str] = field(default_factory=dict)
    interceptors: List[str] = field(default_factory=list)

@dataclass
class DatabaseTableProperties(GraphNodeProperties):
    """Properties for database tables"""
    schema_name: Optional[str] = None
    table_type: str = "table"  # table, view, procedure
    columns: List[Dict[str, Any]] = field(default_factory=list)
    primary_keys: List[str] = field(default_factory=list)
    foreign_keys: List[Dict[str, str]] = field(default_factory=list)
    indexes: List[Dict[str, Any]] = field(default_factory=list)
    row_count: Optional[int] = None
    size_mb: Optional[float] = None
    last_analyzed: Optional[datetime] = None

class GraphRelationshipProperties(BaseModel):
    """Base properties for graph relationships"""
    strength: float = Field(default=1.0, ge=0.0, le=1.0)
    frequency: int = Field(default=1, ge=1)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    source_location: Optional[str] = None
    target_location: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class FlowRelationshipProperties(GraphRelationshipProperties):
    """Properties for flow relationships (FLOWS_TO, FORWARDS_TO, etc.)"""
    flow_type: str = "direct"  # direct, conditional, exception
    condition: Optional[str] = None
    trigger_event: Optional[str] = None
    data_transferred: List[str] = Field(default_factory=list)
    validation_rules: List[str] = Field(default_factory=list)
    error_handling: Optional[str] = None

class DependencyRelationshipProperties(GraphRelationshipProperties):
    """Properties for dependency relationships"""
    dependency_type: str = "compile"  # compile, runtime, test
    is_optional: bool = False
    version_constraint: Optional[str] = None
    scope: str = "default"
    is_transitive: bool = False

# SQLAlchemy models for persistent storage of graph metadata

class GraphNodeMetadata(Base):
    """SQLAlchemy model for storing graph node metadata"""
    __tablename__ = "graph_node_metadata"
    
    id = Column(String, primary_key=True)
    node_type = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    repository_id = Column(String, index=True)
    project_id = Column(String, index=True)
    source_file = Column(String)
    line_number = Column(Integer)
    properties = Column(JSON)
    labels = Column(JSON)  # Additional Neo4j labels
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class GraphRelationshipMetadata(Base):
    """SQLAlchemy model for storing graph relationship metadata"""
    __tablename__ = "graph_relationship_metadata"
    
    id = Column(String, primary_key=True)
    source_node_id = Column(String, nullable=False, index=True)
    target_node_id = Column(String, nullable=False, index=True)
    relationship_type = Column(String, nullable=False, index=True)
    properties = Column(JSON)
    strength = Column(Integer, default=1)
    frequency = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class GraphBusinessRuleTrace(Base):
    """SQLAlchemy model for business rule traces across technologies"""
    __tablename__ = "graph_business_rule_traces"
    
    id = Column(String, primary_key=True)
    rule_name = Column(String, nullable=False, index=True)
    description = Column(Text)
    business_domain = Column(String, index=True)
    technology_stack = Column(JSON)  # ["JSP", "Struts", "Java", "CORBA"]
    flow_steps = Column(JSON)  # List of flow step dictionaries
    complexity_score = Column(Integer)
    extraction_confidence = Column(Integer)
    validation_status = Column(String, default="pending")  # pending, validated, rejected
    created_by = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class FlowStep(BaseModel):
    """Model for individual steps in a business rule flow"""
    step_order: int = Field(ge=1)
    technology: str
    component_name: str
    component_type: str
    file_path: str
    line_range: tuple[int, int] = Field(default=(0, 0))
    business_logic: str
    input_data: List[str] = Field(default_factory=list)
    output_data: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    validation_rules: List[str] = Field(default_factory=list)
    error_conditions: List[str] = Field(default_factory=list)

class GraphArchitecturalInsight(Base):
    """SQLAlchemy model for architectural insights and recommendations"""
    __tablename__ = "graph_architectural_insights"
    
    id = Column(String, primary_key=True)
    insight_type = Column(String, nullable=False, index=True)  # risk, recommendation, pattern
    title = Column(String, nullable=False)
    description = Column(Text)
    business_rules = Column(JSON)  # List of related business rule IDs
    affected_components = Column(JSON)  # List of component IDs
    modernization_impact = Column(String)  # low, medium, high
    implementation_effort = Column(String)  # low, medium, high
    roi_estimate = Column(String)  # low, medium, high
    architect_notes = Column(Text)
    confidence_score = Column(Integer)  # 1-100
    validation_status = Column(String, default="pending")
    priority = Column(String, default="medium")  # low, medium, high, critical
    created_by = Column(String)
    reviewed_by = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ProjectCoordination(Base):
    """SQLAlchemy model for multi-repository project coordination"""
    __tablename__ = "project_coordination"
    
    id = Column(String, primary_key=True)
    project_name = Column(String, nullable=False, index=True)
    description = Column(Text)
    repository_ids = Column(JSON)  # List of repository IDs
    business_domains = Column(JSON)  # List of business domains
    modernization_goals = Column(JSON)  # List of modernization objectives
    status = Column(String, default="planning")  # planning, active, completed, on_hold
    progress_percentage = Column(Integer, default=0)
    estimated_duration_weeks = Column(Integer)
    actual_duration_weeks = Column(Integer)
    budget_estimate = Column(Integer)
    actual_cost = Column(Integer)
    risk_level = Column(String, default="medium")
    stakeholders = Column(JSON)  # List of stakeholder information
    created_by = Column(String)
    project_manager = Column(String)
    technical_lead = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Utility functions for working with graph entities

def create_code_entity_id(repository_id: str, file_path: str, entity_name: str, entity_type: str) -> str:
    """Create a unique ID for code entities"""
    return f"{repository_id}:{file_path}:{entity_type}:{entity_name}"

def create_business_rule_id(repository_id: str, rule_name: str) -> str:
    """Create a unique ID for business rules"""
    return f"{repository_id}:rule:{rule_name}"

def create_flow_relationship_id(source_id: str, target_id: str, flow_type: str) -> str:
    """Create a unique ID for flow relationships"""
    return f"{source_id}:flows_to:{target_id}:{flow_type}"

def parse_entity_id(entity_id: str) -> Dict[str, str]:
    """Parse entity ID to extract components"""
    parts = entity_id.split(":")
    if len(parts) >= 4:
        return {
            "repository_id": parts[0],
            "file_path": parts[1], 
            "entity_type": parts[2],
            "entity_name": ":".join(parts[3:])  # Handle names with colons
        }
    return {}

def validate_graph_node_properties(node_type: GraphNodeType, properties: Dict[str, Any]) -> bool:
    """Validate that node properties match the expected schema for the node type"""
    required_fields = {
        GraphNodeType.CODE_ENTITY: ["name", "type"],
        GraphNodeType.BUSINESS_RULE: ["name", "description", "category"],
        GraphNodeType.STRUTS_ACTION: ["name", "action_path", "action_class"],
        GraphNodeType.DATABASE_TABLE: ["name", "schema_name"],
        GraphNodeType.REPOSITORY: ["name", "type"],
        GraphNodeType.PROJECT: ["name", "description"]
    }
    
    if node_type in required_fields:
        for field in required_fields[node_type]:
            if field not in properties:
                return False
    
    return True

def validate_graph_relationship(source_type: GraphNodeType, 
                              target_type: GraphNodeType, 
                              relationship_type: GraphRelationshipType) -> bool:
    """Validate that a relationship type is valid between two node types"""
    valid_relationships = {
        (GraphNodeType.JSP_PAGE, GraphNodeType.STRUTS_ACTION): [GraphRelationshipType.FLOWS_TO],
        (GraphNodeType.STRUTS_ACTION, GraphNodeType.CLASS): [GraphRelationshipType.IMPLEMENTS],
        (GraphNodeType.CLASS, GraphNodeType.METHOD): [GraphRelationshipType.CONTAINS],
        (GraphNodeType.METHOD, GraphNodeType.DATABASE_TABLE): [GraphRelationshipType.READS_FROM, GraphRelationshipType.WRITES_TO],
        (GraphNodeType.CLASS, GraphNodeType.CLASS): [GraphRelationshipType.EXTENDS, GraphRelationshipType.IMPLEMENTS],
        (GraphNodeType.FILE, GraphNodeType.REPOSITORY): [GraphRelationshipType.BELONGS_TO],
        (GraphNodeType.REPOSITORY, GraphNodeType.PROJECT): [GraphRelationshipType.PART_OF]
    }
    
    relationship_key = (source_type, target_type)
    if relationship_key in valid_relationships:
        return relationship_type in valid_relationships[relationship_key]
    
    # Allow generic relationships for any node type
    generic_relationships = [
        GraphRelationshipType.DEPENDS_ON,
        GraphRelationshipType.USES,
        GraphRelationshipType.REFERENCES,
        GraphRelationshipType.BELONGS_TO
    ]
    
    return relationship_type in generic_relationships