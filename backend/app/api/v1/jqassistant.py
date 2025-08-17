"""
jQAssistant Architecture Analysis API Endpoints

REST API for integrating jQAssistant architectural analysis with DocXP:
- Repository architectural analysis endpoints
- Package dependency visualization
- Architectural compliance reporting
- Code quality metrics and insights
- Design pattern detection
- Dead code identification
- Integration with V1 indexing pipeline
"""

import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from pydantic import BaseModel, Field

from app.services.jqassistant_service import get_jqassistant_service
from app.services.jqassistant_batch_service import get_jqassistant_batch_service
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/jqassistant", tags=["Architecture Analysis"])

# Request Models
class AnalyzeRepositoryRequest(BaseModel):
    repository_path: str = Field(..., description="Path to Java repository")
    repository_id: str = Field(..., description="Repository identifier")
    commit_hash: str = Field(..., description="Git commit hash")
    indexing_job_id: Optional[str] = Field(None, description="Link to V1 indexing job")
    custom_layers: Optional[List[Dict[str, Any]]] = Field(None, description="Custom architectural layer definitions")
    custom_constraints: Optional[List[str]] = Field(None, description="Additional constraint rules")
    include_test_code: bool = Field(False, description="Include test code in analysis")

class ArchitecturalLayerRequest(BaseModel):
    name: str = Field(..., description="Layer name")
    pattern: str = Field(..., description="Regex pattern for package matching")
    description: str = Field(..., description="Layer description")
    allowed_dependencies: List[str] = Field(default_factory=list, description="Allowed dependency layers")
    forbidden_dependencies: List[str] = Field(default_factory=list, description="Forbidden dependency layers")
    severity_level: str = Field("HIGH", description="Violation severity level")

class ArchitecturalInsightRequest(BaseModel):
    repository_id: str = Field(..., description="Repository identifier")
    insight_types: Optional[List[str]] = Field(None, description="Filter by insight types")
    categories: Optional[List[str]] = Field(None, description="Filter by categories")
    priorities: Optional[List[str]] = Field(None, description="Filter by priorities")

# Response Models
class PackageDependencyResponse(BaseModel):
    source_package: str
    target_package: str
    dependency_type: str
    weight: int
    files_involved: List[str]
    is_cyclic: bool
    violation_type: Optional[str]

class ArchitecturalViolationResponse(BaseModel):
    violation_type: str
    severity: str
    source_element: str
    target_element: str
    constraint_violated: str
    description: str
    fix_suggestion: Optional[str]
    file_path: Optional[str]
    line_number: Optional[int]

class DesignPatternResponse(BaseModel):
    pattern_name: str
    pattern_type: str
    confidence: float
    participants: List[str]
    description: str
    benefits: List[str]
    location: str

class DeadCodeElementResponse(BaseModel):
    element_type: str
    element_name: str
    file_path: str
    line_number: Optional[int]
    reason: str
    potential_impact: str
    removal_suggestion: str

class CodeMetricsResponse(BaseModel):
    complexity_metrics: Dict[str, float]
    coupling_metrics: Dict[str, float]
    cohesion_metrics: Dict[str, float]
    size_metrics: Dict[str, int]
    inheritance_metrics: Dict[str, float]
    quality_score: float

class CyclicDependencyResponse(BaseModel):
    cycle_elements: List[str]
    cycle_length: int
    cycle_type: str
    severity: str
    impact_description: Optional[str]
    estimated_effort_to_fix: Optional[str]

class ArchitecturalInsightResponse(BaseModel):
    insight_type: str
    category: str
    priority: str
    title: str
    description: str
    recommendation: Optional[str]
    evidence: Optional[Dict[str, Any]]
    affected_elements: Optional[List[str]]
    business_impact: Optional[str]
    technical_impact: Optional[str]
    estimated_effort: Optional[str]

class AnalysisResultResponse(BaseModel):
    job_id: str
    repository_id: str
    commit_hash: str
    status: str
    
    # Analysis summary
    total_packages: int
    total_classes: int
    total_methods: int
    total_dependencies: int
    cyclic_dependencies_count: int
    architectural_violations_count: int
    
    # Quality scores
    overall_quality_score: float
    layer_compliance_score: float
    architectural_debt_score: float
    
    # Analysis timing
    analysis_duration_seconds: Optional[float]
    
    # Results (limited for API response)
    package_dependencies: List[PackageDependencyResponse]
    architectural_violations: List[ArchitecturalViolationResponse]
    design_patterns: List[DesignPatternResponse]
    dead_code_elements: List[DeadCodeElementResponse]
    code_metrics: CodeMetricsResponse
    cyclic_dependencies: List[CyclicDependencyResponse]

class DependencyGraphResponse(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class AnalysisJobStatusResponse(BaseModel):
    job_id: str
    status: str
    repository_id: str
    repository_path: str
    commit_hash: str
    progress: Dict[str, Any]
    quality_scores: Dict[str, Any]
    timing: Dict[str, Any]
    neo4j_stats: Dict[str, Any]
    configuration: Dict[str, Any]
    linked_indexing_job: Optional[str]
    error_message: Optional[str]

class ValidationResponse(BaseModel):
    jqassistant_installed: bool
    version: Optional[str]
    neo4j_available: bool
    config_valid: bool
    errors: List[str]

# Global service instances
jqassistant_service = None
jqassistant_batch_service = None

async def get_services():
    """Get service instances"""
    global jqassistant_service, jqassistant_batch_service
    if not jqassistant_service:
        jqassistant_service = await get_jqassistant_service()
    if not jqassistant_batch_service:
        jqassistant_batch_service = await get_jqassistant_batch_service()
    return jqassistant_service, jqassistant_batch_service

@router.get("/health", response_model=ValidationResponse)
async def get_jqassistant_health():
    """
    Check jQAssistant installation and configuration status
    
    Returns validation information about jQAssistant setup
    """
    try:
        jqa_service, _ = await get_services()
        validation = await jqa_service.validate_installation()
        return ValidationResponse(**validation)
    except Exception as e:
        logger.error(f"jQAssistant health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.post("/analyze/repository", response_model=Dict[str, str])
async def analyze_repository(
    request: AnalyzeRepositoryRequest,
    background_tasks: BackgroundTasks
):
    """
    Start comprehensive architectural analysis of a Java repository
    
    Analyzes repository structure, dependencies, architectural compliance,
    and code quality metrics using jQAssistant
    """
    try:
        repo_path = Path(request.repository_path)
        if not repo_path.exists():
            raise HTTPException(status_code=404, detail=f"Repository path not found: {request.repository_path}")
        
        logger.info(f"🏗️ Starting jQAssistant analysis for repository: {request.repository_id}")
        
        _, batch_service = await get_services()
        
        # Start architectural analysis
        job_id = await batch_service.start_architectural_analysis(
            repository_path=request.repository_path,
            repository_id=request.repository_id,
            commit_hash=request.commit_hash,
            indexing_job_id=request.indexing_job_id,
            custom_layers=request.custom_layers,
            custom_constraints=request.custom_constraints,
            include_test_code=request.include_test_code
        )
        
        return {
            "job_id": job_id,
            "status": "started",
            "message": f"Architectural analysis started for {request.repository_id}"
        }
        
    except Exception as e:
        logger.error(f"Repository analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/analyze/status/{job_id}", response_model=AnalysisJobStatusResponse)
async def get_analysis_status(job_id: str):
    """
    Get status and progress of architectural analysis job
    
    Returns comprehensive status information including progress,
    quality scores, and timing details
    """
    try:
        _, batch_service = await get_services()
        
        status = await batch_service.get_analysis_job_status(job_id)
        
        if not status:
            raise HTTPException(status_code=404, detail=f"Analysis job {job_id} not found")
        
        return AnalysisJobStatusResponse(**status)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analysis status: {e}")
        raise HTTPException(status_code=500, detail=f"Status retrieval failed: {str(e)}")

@router.get("/analyze/results/{job_id}", response_model=AnalysisResultResponse)
async def get_analysis_results(
    job_id: str,
    include_dependencies: bool = Query(True, description="Include package dependencies"),
    include_violations: bool = Query(True, description="Include architectural violations"),
    include_patterns: bool = Query(True, description="Include design patterns"),
    include_dead_code: bool = Query(True, description="Include dead code elements"),
    limit_results: int = Query(100, description="Limit number of results per category")
):
    """
    Get detailed results of completed architectural analysis
    
    Returns comprehensive analysis results including dependencies,
    violations, patterns, metrics, and insights
    """
    try:
        _, batch_service = await get_services()
        
        # Get job status first
        status = await batch_service.get_analysis_job_status(job_id)
        
        if not status:
            raise HTTPException(status_code=404, detail=f"Analysis job {job_id} not found")
        
        if status['status'] != 'completed':
            raise HTTPException(
                status_code=400, 
                detail=f"Analysis job {job_id} is not completed (status: {status['status']})"
            )
        
        # This would retrieve detailed results from the database
        # For now, return a structured response based on the status
        
        results = AnalysisResultResponse(
            job_id=job_id,
            repository_id=status['repository_id'],
            commit_hash=status['commit_hash'],
            status=status['status'],
            total_packages=status['progress']['total_packages'],
            total_classes=status['progress']['total_classes'],
            total_methods=status['progress']['total_methods'],
            total_dependencies=status['progress']['total_dependencies'],
            cyclic_dependencies_count=status['progress']['cyclic_dependencies_count'],
            architectural_violations_count=status['progress']['architectural_violations_count'],
            overall_quality_score=status['quality_scores']['overall_quality_score'],
            layer_compliance_score=status['quality_scores']['layer_compliance_score'],
            architectural_debt_score=status['quality_scores']['architectural_debt_score'],
            analysis_duration_seconds=status['timing']['analysis_duration_seconds'],
            package_dependencies=[],  # Would be populated from database
            architectural_violations=[],  # Would be populated from database
            design_patterns=[],  # Would be populated from database
            dead_code_elements=[],  # Would be populated from database
            code_metrics=CodeMetricsResponse(
                complexity_metrics={},
                coupling_metrics={},
                cohesion_metrics={},
                size_metrics={},
                inheritance_metrics={},
                quality_score=status['quality_scores']['overall_quality_score']
            ),
            cyclic_dependencies=[]  # Would be populated from database
        )
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analysis results: {e}")
        raise HTTPException(status_code=500, detail=f"Results retrieval failed: {str(e)}")

@router.get("/dependencies/graph/{job_id}", response_model=DependencyGraphResponse)
async def get_dependency_graph(
    job_id: str,
    format: str = Query("json", description="Graph format (json, cytoscape, d3)"),
    include_cycles: bool = Query(True, description="Highlight cyclic dependencies"),
    package_filter: Optional[str] = Query(None, description="Filter packages by pattern")
):
    """
    Get package dependency graph for visualization
    
    Returns graph data in various formats suitable for visualization
    libraries like D3.js, Cytoscape.js, etc.
    """
    try:
        # This would retrieve and format the dependency graph from the database
        # For now, return a placeholder structure
        
        return DependencyGraphResponse(
            nodes=[
                {"id": "com.example.controller", "label": "Controller", "type": "package", "layer": "presentation"},
                {"id": "com.example.service", "label": "Service", "type": "package", "layer": "business"},
                {"id": "com.example.repository", "label": "Repository", "type": "package", "layer": "data"}
            ],
            edges=[
                {"source": "com.example.controller", "target": "com.example.service", "weight": 5, "type": "depends_on"},
                {"source": "com.example.service", "target": "com.example.repository", "weight": 3, "type": "depends_on"}
            ],
            metadata={
                "job_id": job_id,
                "format": format,
                "total_nodes": 3,
                "total_edges": 2,
                "cyclic_dependencies": 0,
                "generated_at": "2024-01-01T00:00:00Z"
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get dependency graph: {e}")
        raise HTTPException(status_code=500, detail=f"Graph retrieval failed: {str(e)}")

@router.get("/violations/{job_id}")
async def get_architectural_violations(
    job_id: str,
    violation_type: Optional[str] = Query(None, description="Filter by violation type"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    resolved: Optional[bool] = Query(None, description="Filter by resolution status"),
    limit: int = Query(50, description="Maximum number of violations")
):
    """
    Get architectural violations with filtering options
    
    Returns violations found during analysis with detailed
    descriptions and fix suggestions
    """
    try:
        # This would query the database for violations
        # For now, return a placeholder response
        
        violations = [
            {
                "violation_type": "LAYER_VIOLATION",
                "severity": "HIGH",
                "source_element": "com.example.controller.UserController",
                "target_element": "com.example.repository.UserRepository",
                "constraint_violated": "architecture:LayerViolation",
                "description": "Presentation layer should not directly depend on Repository layer",
                "fix_suggestion": "Introduce service layer to mediate between controller and repository",
                "file_path": "/src/main/java/com/example/controller/UserController.java",
                "line_number": 25,
                "is_resolved": False
            }
        ]
        
        return {
            "job_id": job_id,
            "total_violations": len(violations),
            "filters": {
                "violation_type": violation_type,
                "severity": severity,
                "resolved": resolved
            },
            "violations": violations
        }
        
    except Exception as e:
        logger.error(f"Failed to get violations: {e}")
        raise HTTPException(status_code=500, detail=f"Violations retrieval failed: {str(e)}")

@router.get("/metrics/{job_id}")
async def get_code_metrics(
    job_id: str,
    scope_type: str = Query("REPOSITORY", description="Metrics scope (REPOSITORY, PACKAGE, CLASS)"),
    scope_name: Optional[str] = Query(None, description="Specific scope name")
):
    """
    Get code quality metrics for repository, packages, or classes
    
    Returns comprehensive metrics including complexity, coupling,
    cohesion, and quality scores
    """
    try:
        # This would query the database for metrics
        # For now, return a placeholder response
        
        metrics = {
            "job_id": job_id,
            "scope_type": scope_type,
            "scope_name": scope_name or "entire_repository",
            "complexity_metrics": {
                "average_cyclomatic_complexity": 3.2,
                "maximum_cyclomatic_complexity": 15,
                "total_methods": 245
            },
            "coupling_metrics": {
                "average_efferent_coupling": 4.1,
                "average_afferent_coupling": 2.8,
                "average_instability": 0.59
            },
            "size_metrics": {
                "total_lines_of_code": 12450,
                "total_classes": 45,
                "total_methods": 245,
                "total_fields": 128
            },
            "quality_scores": {
                "maintainability_index": 72.5,
                "technical_debt_ratio": 0.15,
                "overall_quality_score": 78.2
            }
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics retrieval failed: {str(e)}")

@router.get("/patterns/{job_id}")
async def get_design_patterns(
    job_id: str,
    pattern_type: Optional[str] = Query(None, description="Filter by pattern type"),
    confidence_threshold: float = Query(0.5, description="Minimum confidence threshold")
):
    """
    Get design patterns detected in the codebase
    
    Returns identified design patterns with confidence scores
    and implementation details
    """
    try:
        # This would query the database for design patterns
        # For now, return a placeholder response
        
        patterns = [
            {
                "pattern_name": "Singleton",
                "pattern_type": "CREATIONAL",
                "confidence": 0.85,
                "participants": ["com.example.config.DatabaseConfig"],
                "description": "Ensures a class has only one instance",
                "benefits": ["Global access point", "Controlled instantiation"],
                "location": "com.example.config",
                "implementation_quality": "GOOD"
            },
            {
                "pattern_name": "Factory",
                "pattern_type": "CREATIONAL",
                "confidence": 0.75,
                "participants": ["com.example.factory.UserFactory", "com.example.model.User"],
                "description": "Creates objects without specifying exact classes",
                "benefits": ["Loose coupling", "Flexible object creation"],
                "location": "com.example.factory",
                "implementation_quality": "EXCELLENT"
            }
        ]
        
        return {
            "job_id": job_id,
            "total_patterns": len(patterns),
            "filters": {
                "pattern_type": pattern_type,
                "confidence_threshold": confidence_threshold
            },
            "patterns": patterns
        }
        
    except Exception as e:
        logger.error(f"Failed to get design patterns: {e}")
        raise HTTPException(status_code=500, detail=f"Patterns retrieval failed: {str(e)}")

@router.get("/dead-code/{job_id}")
async def get_dead_code(
    job_id: str,
    element_type: Optional[str] = Query(None, description="Filter by element type"),
    potential_impact: Optional[str] = Query(None, description="Filter by potential impact"),
    verified_only: bool = Query(False, description="Only return verified dead code")
):
    """
    Get dead/unused code elements identified by analysis
    
    Returns potentially unused code elements with removal
    suggestions and impact assessment
    """
    try:
        # This would query the database for dead code elements
        # For now, return a placeholder response
        
        dead_code = [
            {
                "element_type": "CLASS",
                "element_name": "com.example.util.LegacyUtil",
                "file_path": "/src/main/java/com/example/util/LegacyUtil.java",
                "line_number": 1,
                "reason": "No incoming dependencies detected",
                "potential_impact": "LOW",
                "removal_suggestion": "Verify not used via reflection, then consider removal",
                "is_verified_dead": False
            },
            {
                "element_type": "METHOD",
                "element_name": "com.example.service.UserService.validateLegacyFormat",
                "file_path": "/src/main/java/com/example/service/UserService.java",
                "line_number": 156,
                "reason": "Private method with no invocations",
                "potential_impact": "MEDIUM",
                "removal_suggestion": "Safe to remove if not accessed via reflection",
                "is_verified_dead": False
            }
        ]
        
        return {
            "job_id": job_id,
            "total_dead_code_elements": len(dead_code),
            "filters": {
                "element_type": element_type,
                "potential_impact": potential_impact,
                "verified_only": verified_only
            },
            "dead_code_elements": dead_code
        }
        
    except Exception as e:
        logger.error(f"Failed to get dead code: {e}")
        raise HTTPException(status_code=500, detail=f"Dead code retrieval failed: {str(e)}")

@router.get("/insights/{job_id}")
async def get_architectural_insights(
    job_id: str,
    insight_type: Optional[str] = Query(None, description="Filter by insight type"),
    category: Optional[str] = Query(None, description="Filter by category"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    acknowledged: Optional[bool] = Query(None, description="Filter by acknowledgment status")
):
    """
    Get high-level architectural insights and recommendations
    
    Returns aggregated insights with business and technical
    impact assessment and recommended actions
    """
    try:
        # This would query the database for insights
        # For now, return a placeholder response
        
        insights = [
            {
                "insight_type": "WARNING",
                "category": "QUALITY",
                "priority": "HIGH",
                "title": "Low Overall Code Quality",
                "description": "Overall quality score is 65.2/100",
                "recommendation": "Focus on reducing complexity and improving architectural compliance",
                "evidence": {"quality_score": 65.2},
                "business_impact": "Increased maintenance costs and development velocity reduction",
                "technical_impact": "Higher bug rates and difficult refactoring",
                "estimated_effort": "HIGH",
                "is_acknowledged": False
            },
            {
                "insight_type": "RECOMMENDATION",
                "category": "STRUCTURE",
                "priority": "MEDIUM",
                "title": "Design Patterns Well Implemented",
                "description": "Identified 5 well-implemented design patterns",
                "recommendation": "Document and maintain these patterns for consistency",
                "evidence": {"patterns": ["Singleton", "Factory", "Observer"]},
                "business_impact": "Good foundation for maintainable code",
                "technical_impact": "Consistent design approach",
                "estimated_effort": "LOW",
                "is_acknowledged": False
            }
        ]
        
        return {
            "job_id": job_id,
            "total_insights": len(insights),
            "filters": {
                "insight_type": insight_type,
                "category": category,
                "priority": priority,
                "acknowledged": acknowledged
            },
            "insights": insights
        }
        
    except Exception as e:
        logger.error(f"Failed to get insights: {e}")
        raise HTTPException(status_code=500, detail=f"Insights retrieval failed: {str(e)}")

@router.get("/dashboard/{repository_id}")
async def get_architecture_dashboard(
    repository_id: str,
    time_range: str = Query("30d", description="Time range for trends (7d, 30d, 90d)")
):
    """
    Get comprehensive architecture dashboard data
    
    Returns metrics, trends, and insights for architectural
    governance and technical debt management
    """
    try:
        # This would aggregate data across multiple analysis jobs
        # For now, return a structured dashboard response
        
        dashboard_data = {
            "repository_id": repository_id,
            "time_range": time_range,
            "latest_analysis": {
                "job_id": "latest-job-id",
                "commit_hash": "abc123",
                "analysis_date": "2024-01-01T00:00:00Z",
                "overall_quality_score": 72.5
            },
            "trends": {
                "quality_score_trend": [70.2, 71.1, 72.5],  # 30-day trend
                "architectural_debt_trend": [25.3, 24.8, 23.1],  # 30-day trend
                "violations_trend": [15, 12, 8]  # 30-day trend
            },
            "current_state": {
                "total_packages": 25,
                "total_classes": 156,
                "cyclic_dependencies": 2,
                "architectural_violations": 8,
                "design_patterns": 5,
                "dead_code_elements": 12
            },
            "top_issues": {
                "critical_violations": [
                    "Layer violation in UserController",
                    "Cyclic dependency in service layer"
                ],
                "high_complexity_classes": [
                    "com.example.service.OrderProcessor",
                    "com.example.util.DataTransformer"
                ],
                "largest_cycles": [
                    ["com.example.service", "com.example.util", "com.example.service"]
                ]
            },
            "recommendations": [
                "Break cyclic dependencies in service layer",
                "Introduce service layer to reduce controller-repository coupling",
                "Refactor high-complexity classes using Extract Method pattern",
                "Remove identified dead code to improve maintainability"
            ]
        }
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Dashboard generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Dashboard generation failed: {str(e)}")

@router.get("/jobs/recent")
async def list_recent_analysis_jobs(
    limit: int = Query(10, description="Maximum number of jobs to return")
):
    """
    List recent architectural analysis jobs
    
    Returns summary information about recent analysis jobs
    for monitoring and historical tracking
    """
    try:
        _, batch_service = await get_services()
        
        jobs = await batch_service.list_recent_analysis_jobs(limit)
        
        return {
            "total_jobs": len(jobs),
            "jobs": jobs
        }
        
    except Exception as e:
        logger.error(f"Failed to list recent jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Job listing failed: {str(e)}")

@router.post("/layers/validate")
async def validate_architectural_layers(layers: List[ArchitecturalLayerRequest]):
    """
    Validate custom architectural layer definitions
    
    Checks layer definitions for consistency and conflicts
    before using them in analysis
    """
    try:
        # Validate layer definitions
        validation_results = []
        
        for layer in layers:
            result = {
                "layer_name": layer.name,
                "valid": True,
                "errors": [],
                "warnings": []
            }
            
            # Basic validation
            if not layer.pattern:
                result["valid"] = False
                result["errors"].append("Pattern cannot be empty")
            
            if not layer.description:
                result["warnings"].append("Description is empty")
            
            # Check for circular dependencies in layer definitions
            if layer.name in layer.allowed_dependencies:
                result["valid"] = False
                result["errors"].append("Layer cannot depend on itself")
            
            validation_results.append(result)
        
        overall_valid = all(result["valid"] for result in validation_results)
        
        return {
            "overall_valid": overall_valid,
            "layer_count": len(layers),
            "validation_results": validation_results
        }
        
    except Exception as e:
        logger.error(f"Layer validation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@router.get("/config/default-layers")
async def get_default_architectural_layers():
    """
    Get default architectural layer definitions
    
    Returns pre-configured layer definitions for common
    Java application architectures
    """
    try:
        jqa_service, _ = await get_services()
        
        default_layers = [
            {
                "name": "Presentation",
                "pattern": r".*\.(controller|web|ui|view)\..*",
                "description": "Web controllers and UI components",
                "allowed_dependencies": ["Service", "DTO"],
                "forbidden_dependencies": ["Repository", "Entity"],
                "severity_level": "HIGH"
            },
            {
                "name": "Service",
                "pattern": r".*\.(service|business|logic)\..*",
                "description": "Business logic and service layer",
                "allowed_dependencies": ["Repository", "DTO", "Entity"],
                "forbidden_dependencies": ["Controller"],
                "severity_level": "HIGH"
            },
            {
                "name": "Repository",
                "pattern": r".*\.(repository|dao|persistence)\..*",
                "description": "Data access layer",
                "allowed_dependencies": ["Entity"],
                "forbidden_dependencies": ["Controller", "Service"],
                "severity_level": "HIGH"
            },
            {
                "name": "Entity",
                "pattern": r".*\.(entity|model|domain)\..*",
                "description": "Domain entities and data models",
                "allowed_dependencies": [],
                "forbidden_dependencies": ["Controller", "Service", "Repository"],
                "severity_level": "CRITICAL"
            },
            {
                "name": "DTO",
                "pattern": r".*\.(dto|transfer|api)\..*",
                "description": "Data transfer objects",
                "allowed_dependencies": ["Entity"],
                "forbidden_dependencies": ["Repository"],
                "severity_level": "MEDIUM"
            }
        ]
        
        return {
            "architecture_type": "Layered Architecture",
            "description": "Standard enterprise Java layered architecture",
            "layers": default_layers
        }
        
    except Exception as e:
        logger.error(f"Failed to get default layers: {e}")
        raise HTTPException(status_code=500, detail=f"Default layers retrieval failed: {str(e)}")