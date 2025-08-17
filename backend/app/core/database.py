"""
Database configuration and initialization
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import json

from app.core.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True
)

# Create async session
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Create base class for models
Base = declarative_base()

# Database models
class DocumentationJob(Base):
    """Documentation generation job with enhanced progress tracking"""
    __tablename__ = "documentation_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, unique=True, index=True)
    repository_path = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Configuration
    config = Column(JSON, nullable=False)
    
    # Enhanced Progress Tracking
    progress_percentage = Column(Integer, default=0)  # 0-100
    current_step = Column(String, nullable=True)  # Current step key
    step_description = Column(String, nullable=True)  # Human-readable step description
    progress_data = Column(JSON, nullable=True)  # Detailed progress information
    
    # Results
    entities_count = Column(Integer, default=0)
    business_rules_count = Column(Integer, default=0)
    files_processed = Column(Integer, default=0)
    output_path = Column(String, nullable=True)
    
    # Metrics
    processing_time_seconds = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)

class Repository(Base):
    """Repository information"""
    __tablename__ = "repositories"
    
    id = Column(Integer, primary_key=True, index=True)
    path = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    last_analyzed = Column(DateTime, nullable=True)
    
    # Statistics
    total_files = Column(Integer, default=0)
    total_lines = Column(Integer, default=0)
    languages = Column(JSON, default=list)
    
    # Metadata
    git_remote = Column(String, nullable=True)
    last_commit = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class ConfigurationTemplate(Base):
    """Saved configuration templates"""
    __tablename__ = "configuration_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=True)
    config = Column(JSON, nullable=False)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

# Enhanced Code Intelligence Tables
class CodeEntity(Base):
    """Code entities with hierarchical relationships"""
    __tablename__ = "code_entities"
    
    id = Column(String, primary_key=True)  # Stable entity ID from intelligence graph
    name = Column(String, nullable=False, index=True)
    type = Column(String, nullable=False, index=True)  # module, class, method, function, etc.
    file_path = Column(String, nullable=False, index=True)
    line_number = Column(Integer, nullable=True)
    
    # Hierarchy
    parent_id = Column(String, ForeignKey('code_entities.id'), nullable=True, index=True)
    module_path = Column(String, nullable=False, index=True)
    
    # Content
    docstring = Column(Text, nullable=True)
    parameters = Column(JSON, default=list)  # Function/method parameters
    complexity = Column(Integer, default=0)
    
    # Metadata
    language = Column(String, nullable=True)
    visibility = Column(String, default='public')  # public, private, protected
    is_abstract = Column(Boolean, default=False)
    design_patterns = Column(JSON, default=list)
    entity_metadata = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    children = relationship("CodeEntity", back_populates="parent", cascade="all, delete-orphan")
    parent = relationship("CodeEntity", back_populates="children", remote_side=[id])
    business_rules = relationship("BusinessRuleContext", back_populates="code_entity")
    outgoing_relationships = relationship("CodeRelationship", 
                                         foreign_keys="CodeRelationship.source_id",
                                         back_populates="source_entity")
    incoming_relationships = relationship("CodeRelationship", 
                                         foreign_keys="CodeRelationship.target_id",
                                         back_populates="target_entity")

class CodeRelationship(Base):
    """Relationships between code entities"""
    __tablename__ = "code_relationships"
    
    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(String, ForeignKey('code_entities.id'), nullable=False, index=True)
    target_id = Column(String, ForeignKey('code_entities.id'), nullable=False, index=True)
    relationship_type = Column(String, nullable=False, index=True)  # calls, inherits, implements, uses, depends_on
    
    # Context
    file_path = Column(String, nullable=False)
    line_number = Column(Integer, nullable=True)
    context = Column(Text, nullable=True)  # Additional context about the relationship
    
    # Metadata
    strength = Column(Float, default=1.0)  # Relationship strength (for weighted analysis)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    source_entity = relationship("CodeEntity", foreign_keys=[source_id], back_populates="outgoing_relationships")
    target_entity = relationship("CodeEntity", foreign_keys=[target_id], back_populates="incoming_relationships")

class BusinessRuleContext(Base):
    """Enhanced business rules with hierarchical context"""
    __tablename__ = "business_rule_contexts"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)
    plain_english = Column(Text, nullable=True)  # Natural language explanation
    confidence_score = Column(Float, nullable=False)
    category = Column(String, nullable=False, index=True)
    
    # Hierarchy Context
    code_entity_id = Column(String, ForeignKey('code_entities.id'), nullable=False, index=True)
    module_path = Column(String, nullable=False, index=True)
    class_context = Column(String, nullable=True, index=True)
    method_context = Column(String, nullable=True, index=True)
    
    # Business Context
    business_impact = Column(Text, nullable=True)
    implementation_details = Column(Text, nullable=True)
    related_rules = Column(JSON, default=list)  # List of related rule IDs
    
    # Enhanced Code Traceability
    method_call_chain = Column(Text, nullable=True)  # Complete execution path
    boundary_spans = Column(JSON, default=list)  # ["controller→service", "service→data"]
    file_locations = Column(JSON, default=list)  # Specific file:line references
    integration_points = Column(Text, nullable=True)  # External system connections
    business_process = Column(Text, nullable=True)  # Business workflow mapping
    failure_impact = Column(Text, nullable=True)  # Business failure handling
    compliance_requirements = Column(Text, nullable=True)  # Regulatory enforcement details
    
    # Metadata
    keywords = Column(JSON, default=list)
    priority = Column(String, default='medium')  # low, medium, high, critical
    validated = Column(Boolean, default=False)  # Human validation flag
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    code_entity = relationship("CodeEntity", back_populates="business_rules")

class EntityHierarchy(Base):
    """Materialized view for fast hierarchy queries"""
    __tablename__ = "entity_hierarchies"
    
    id = Column(Integer, primary_key=True, index=True)
    ancestor_id = Column(String, ForeignKey('code_entities.id'), nullable=False, index=True)
    descendant_id = Column(String, ForeignKey('code_entities.id'), nullable=False, index=True)
    depth = Column(Integer, nullable=False, index=True)  # Distance between ancestor and descendant
    
    # Path information
    path = Column(String, nullable=False)  # Dot-separated path from ancestor to descendant
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    ancestor = relationship("CodeEntity", foreign_keys=[ancestor_id])
    descendant = relationship("CodeEntity", foreign_keys=[descendant_id])

class CallGraph(Base):
    """Optimized call graph for fast traversal"""
    __tablename__ = "call_graphs"
    
    id = Column(Integer, primary_key=True, index=True)
    caller_id = Column(String, ForeignKey('code_entities.id'), nullable=False, index=True)
    callee_id = Column(String, ForeignKey('code_entities.id'), nullable=False, index=True)
    call_count = Column(Integer, default=1)  # How many times this call occurs
    
    # Context
    file_path = Column(String, nullable=False)
    line_numbers = Column(JSON, default=list)  # All line numbers where this call occurs
    
    # Analysis
    is_recursive = Column(Boolean, default=False)
    is_critical_path = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    caller = relationship("CodeEntity", foreign_keys=[caller_id])
    callee = relationship("CodeEntity", foreign_keys=[callee_id])

class SearchIndex(Base):
    """Full-text search index for code entities and business rules"""
    __tablename__ = "search_indexes"
    
    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(String, ForeignKey('code_entities.id'), nullable=True, index=True)
    rule_id = Column(String, ForeignKey('business_rule_contexts.rule_id'), nullable=True, index=True)
    
    # Search content
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    keywords = Column(JSON, default=list)
    category = Column(String, nullable=False, index=True)  # entity, business_rule, documentation
    
    # Hierarchy context for result ranking
    module_path = Column(String, nullable=False, index=True)
    hierarchy_depth = Column(Integer, default=0)
    
    # Search metadata
    language = Column(String, nullable=True, index=True)
    file_path = Column(String, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

# Database initialization
async def init_db():
    """Initialize database"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_session() -> AsyncSession:
    """Get database session"""
    async with AsyncSessionLocal() as session:
        yield session

def get_async_session():
    """Get async database session - returns context manager"""
    return AsyncSessionLocal()
