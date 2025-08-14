"""
Pydantic schemas for API request/response models
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class DocumentationDepth(str, Enum):
    """Documentation depth levels"""
    MINIMAL = "minimal"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"
    EXHAUSTIVE = "exhaustive"

class DocumentationRequest(BaseModel):
    """Request model for documentation generation"""
    repository_path: str = Field(..., description="Path to repository")
    output_path: Optional[str] = Field(default="./output", description="Output directory")
    
    # Documentation options
    depth: DocumentationDepth = Field(default=DocumentationDepth.STANDARD)
    include_diagrams: bool = Field(default=True)
    include_business_rules: bool = Field(default=True)
    include_api_docs: bool = Field(default=True)
    incremental_update: bool = Field(default=False)
    
    # Focus areas
    focus_classes: bool = Field(default=True)
    focus_functions: bool = Field(default=True)
    focus_apis: bool = Field(default=True)
    focus_database: bool = Field(default=True)
    focus_security: bool = Field(default=True)
    focus_config: bool = Field(default=True)
    
    # Filters
    keywords: Optional[List[str]] = Field(default_factory=list)
    exclude_patterns: Optional[List[str]] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "repository_path": "/path/to/repo",
                "depth": "comprehensive",
                "include_diagrams": True,
                "keywords": ["payment", "validation"]
            }
        }

class DocumentationResponse(BaseModel):
    """Response model for documentation generation"""
    job_id: str
    status: str
    message: str

class JobStatusResponse(BaseModel):
    """Response model for job status"""
    job_id: str
    status: str
    repository_path: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    entities_count: int
    business_rules_count: int
    files_processed: int
    output_path: Optional[str]
    error_message: Optional[str]
    processing_time_seconds: Optional[float]

class RepositoryInfo(BaseModel):
    """Repository information model"""
    path: str
    name: str
    total_files: int
    total_lines: int
    languages: Dict[str, int]
    is_git: bool
    last_commit: Optional[str]
    size_mb: float

class AnalyticsData(BaseModel):
    """Analytics data model"""
    total_jobs: int
    successful_jobs: int
    failed_jobs: int
    average_processing_time: float
    total_entities: int
    total_business_rules: int
    repositories_analyzed: int

class ConfigurationTemplate(BaseModel):
    """Configuration template model"""
    name: str
    description: Optional[str]
    config: Dict[str, Any]
    is_default: bool = False
    
class BusinessRule(BaseModel):
    """Business rule model"""
    id: str
    description: str
    confidence_score: float
    category: str
    code_reference: str
    validation_logic: Optional[str]
    related_entities: List[str]
