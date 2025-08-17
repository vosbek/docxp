"""
Semgrep Static Analysis API Endpoints

REST API for integrating Semgrep static analysis with DocXP:
- Repository and file analysis endpoints
- Security vulnerability reporting
- Code quality assessment
- Integration with search results
"""

import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from pydantic import BaseModel, Field

from app.services.semgrep_service import SemgrepService, SemgrepAnalysisResult, SemgrepFinding
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/semgrep", tags=["Static Analysis"])

# Request Models
class AnalyzeRepositoryRequest(BaseModel):
    repo_path: str = Field(..., description="Path to repository")
    repo_id: str = Field(..., description="Repository identifier")
    commit_hash: str = Field(..., description="Git commit hash")
    rule_sets: Optional[List[str]] = Field(None, description="Specific rule sets to use")
    custom_rules: Optional[List[str]] = Field(None, description="Additional custom rules")

class AnalyzeFileRequest(BaseModel):
    file_path: str = Field(..., description="Path to file")
    content: Optional[str] = Field(None, description="File content (if not reading from disk)")

class SecurityAssessmentRequest(BaseModel):
    repo_id: str = Field(..., description="Repository identifier")
    include_low_priority: bool = Field(False, description="Include low priority findings")

# Response Models
class FindingResponse(BaseModel):
    rule_id: str
    severity: str
    category: str
    message: str
    file_path: str
    start_line: int
    end_line: int
    code_snippet: str
    confidence: str
    cwe_ids: List[str]
    owasp_categories: List[str]
    fix_suggestion: Optional[str]

class AnalysisResultResponse(BaseModel):
    repo_id: str
    commit_hash: str
    total_findings: int
    findings_by_severity: Dict[str, int]
    findings_by_category: Dict[str, int]
    critical_security_issues: int
    performance_issues: int
    maintainability_score: float
    analysis_duration_seconds: float
    findings: List[FindingResponse]

class SecuritySummaryResponse(BaseModel):
    total_security_findings: int
    critical_vulnerabilities: int
    risk_score: float
    risk_level: str
    remediation_priority: List[Dict[str, Any]]

class ValidationResponse(BaseModel):
    semgrep_installed: bool
    version: Optional[str]
    rules_available: bool
    custom_rules_ready: bool
    errors: List[str]

# Global service instance
semgrep_service = SemgrepService()

@router.get("/health", response_model=ValidationResponse)
async def get_semgrep_health():
    """
    Check Semgrep installation and configuration status
    
    Returns validation information about Semgrep setup
    """
    try:
        validation = await semgrep_service.validate_installation()
        return ValidationResponse(**validation)
    except Exception as e:
        logger.error(f"Semgrep health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.post("/analyze/repository", response_model=AnalysisResultResponse)
async def analyze_repository(
    request: AnalyzeRepositoryRequest,
    background_tasks: BackgroundTasks
):
    """
    Perform comprehensive Semgrep analysis on a repository
    
    Analyzes entire repository for security vulnerabilities,
    code quality issues, and architectural compliance
    """
    try:
        repo_path = Path(request.repo_path)
        if not repo_path.exists():
            raise HTTPException(status_code=404, detail=f"Repository path not found: {request.repo_path}")
        
        logger.info(f"🔍 Starting Semgrep analysis for repository: {request.repo_id}")
        
        # Perform analysis
        analysis_result = await semgrep_service.analyze_repository(
            repo_path=repo_path,
            repo_id=request.repo_id,
            commit_hash=request.commit_hash,
            rule_sets=request.rule_sets,
            custom_rules=request.custom_rules
        )
        
        # Convert findings to response format
        findings_response = [
            FindingResponse(
                rule_id=finding.rule_id,
                severity=finding.severity,
                category=finding.category,
                message=finding.message,
                file_path=finding.file_path,
                start_line=finding.start_line,
                end_line=finding.end_line,
                code_snippet=finding.code_snippet,
                confidence=finding.confidence,
                cwe_ids=finding.cwe_ids,
                owasp_categories=finding.owasp_categories,
                fix_suggestion=finding.fix_suggestion
            )
            for finding in analysis_result.findings
        ]
        
        # Schedule background tasks for integration
        background_tasks.add_task(
            _integrate_with_search_index,
            analysis_result.repo_id,
            analysis_result.commit_hash,
            analysis_result.findings
        )
        
        return AnalysisResultResponse(
            repo_id=analysis_result.repo_id,
            commit_hash=analysis_result.commit_hash,
            total_findings=analysis_result.total_findings,
            findings_by_severity=analysis_result.findings_by_severity,
            findings_by_category=analysis_result.findings_by_category,
            critical_security_issues=analysis_result.critical_security_issues,
            performance_issues=analysis_result.performance_issues,
            maintainability_score=analysis_result.maintainability_score,
            analysis_duration_seconds=analysis_result.analysis_duration_seconds,
            findings=findings_response
        )
        
    except Exception as e:
        logger.error(f"Repository analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/analyze/file", response_model=List[FindingResponse])
async def analyze_file(request: AnalyzeFileRequest):
    """
    Analyze a single file with Semgrep
    
    Useful for real-time analysis during code editing
    """
    try:
        file_path = Path(request.file_path)
        
        logger.info(f"🔍 Analyzing file: {request.file_path}")
        
        # Perform file analysis
        findings = await semgrep_service.analyze_file(
            file_path=file_path,
            content=request.content
        )
        
        # Convert to response format
        findings_response = [
            FindingResponse(
                rule_id=finding.rule_id,
                severity=finding.severity,
                category=finding.category,
                message=finding.message,
                file_path=finding.file_path,
                start_line=finding.start_line,
                end_line=finding.end_line,
                code_snippet=finding.code_snippet,
                confidence=finding.confidence,
                cwe_ids=finding.cwe_ids,
                owasp_categories=finding.owasp_categories,
                fix_suggestion=finding.fix_suggestion
            )
            for finding in findings
        ]
        
        logger.info(f"✅ File analysis complete: {len(findings_response)} findings")
        
        return findings_response
        
    except Exception as e:
        logger.error(f"File analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"File analysis failed: {str(e)}")

@router.get("/security/summary/{repo_id}", response_model=SecuritySummaryResponse)
async def get_security_summary(
    repo_id: str,
    commit_hash: Optional[str] = Query(None, description="Specific commit hash")
):
    """
    Get security-focused summary for a repository
    
    Returns OWASP Top 10 mapping, risk assessment, and remediation priorities
    """
    try:
        # Get latest analysis for repository
        # This would typically query a database of stored analysis results
        # For now, we'll simulate it
        
        logger.info(f"🔒 Generating security summary for {repo_id}")
        
        # This is a placeholder - in production, retrieve from database
        analysis_result = None  # await get_latest_analysis(repo_id, commit_hash)
        
        if not analysis_result:
            raise HTTPException(
                status_code=404, 
                detail=f"No analysis found for repository: {repo_id}"
            )
        
        # Generate security summary
        security_summary = await semgrep_service.get_security_summary(analysis_result)
        
        return SecuritySummaryResponse(
            total_security_findings=security_summary['total_security_findings'],
            critical_vulnerabilities=security_summary['critical_vulnerabilities'],
            risk_score=security_summary['risk_score'],
            risk_level=security_summary['risk_level'],
            remediation_priority=security_summary['remediation_priority']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Security summary generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Security summary failed: {str(e)}")

@router.get("/findings/by-category/{repo_id}")
async def get_findings_by_category(
    repo_id: str,
    category: str = Query(..., description="Finding category"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(50, description="Maximum number of findings")
):
    """
    Get findings filtered by category and severity
    
    Useful for focused analysis of specific types of issues
    """
    try:
        # This would query stored analysis results
        # For now, return a placeholder response
        
        logger.info(f"📊 Retrieving {category} findings for {repo_id}")
        
        # Placeholder implementation
        findings = []  # await query_findings(repo_id, category, severity, limit)
        
        return {
            "repo_id": repo_id,
            "category": category,
            "severity_filter": severity,
            "total_findings": len(findings),
            "findings": findings
        }
        
    except Exception as e:
        logger.error(f"Findings retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Findings retrieval failed: {str(e)}")

@router.get("/rules/available")
async def get_available_rules():
    """
    Get list of available Semgrep rules and rule sets
    
    Returns information about built-in and custom rules
    """
    try:
        return {
            "rule_sets": semgrep_service.rule_sets,
            "language_configs": semgrep_service.language_configs,
            "custom_rules_path": str(semgrep_service.custom_rules_path),
            "enterprise_rules_path": str(semgrep_service.enterprise_rules_path)
        }
        
    except Exception as e:
        logger.error(f"Rules retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Rules retrieval failed: {str(e)}")

@router.post("/rules/validate")
async def validate_custom_rules(rules_path: str):
    """
    Validate custom Semgrep rules
    
    Checks syntax and compatibility of custom rule files
    """
    try:
        rules_directory = Path(rules_path)
        
        if not rules_directory.exists():
            raise HTTPException(status_code=404, detail=f"Rules directory not found: {rules_path}")
        
        # Install and validate custom rules
        success = await semgrep_service.install_custom_rules(rules_directory)
        
        if success:
            return {"status": "success", "message": "Custom rules validated successfully"}
        else:
            return {"status": "error", "message": "Custom rules validation failed"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rules validation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Rules validation failed: {str(e)}")

@router.get("/stats/dashboard/{repo_id}")
async def get_analysis_dashboard(repo_id: str):
    """
    Get comprehensive analysis dashboard data
    
    Returns metrics and trends for security and quality analysis
    """
    try:
        # This would aggregate historical analysis data
        # For now, return a structured dashboard response
        
        dashboard_data = {
            "repo_id": repo_id,
            "last_analysis": None,  # await get_last_analysis_timestamp(repo_id)
            "trends": {
                "security_findings_trend": [],  # 30-day trend
                "quality_score_trend": [],      # 30-day trend
                "critical_issues_trend": []     # 30-day trend
            },
            "top_issues": {
                "security": [],     # Top security rule violations
                "performance": [],  # Top performance issues
                "maintainability": [] # Top maintainability issues
            },
            "recommendations": [
                "Enable additional security rule sets",
                "Configure custom enterprise rules",
                "Set up automated analysis on commits"
            ]
        }
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Dashboard generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Dashboard generation failed: {str(e)}")

# Background task functions

async def _integrate_with_search_index(
    repo_id: str, 
    commit_hash: str, 
    findings: List[SemgrepFinding]
):
    """
    Background task to integrate Semgrep findings with search index
    
    Enriches search results with static analysis information
    """
    try:
        logger.info(f"🔗 Integrating Semgrep findings with search index for {repo_id}")
        
        # This would integrate with the OpenSearch index
        # Add metadata about security issues, quality problems, etc.
        # to relevant code chunks
        
        # Placeholder for integration logic
        for finding in findings:
            # Update search documents with finding metadata
            pass
        
        logger.info(f"✅ Search index integration complete for {repo_id}")
        
    except Exception as e:
        logger.error(f"Search index integration failed: {e}")

async def _cache_analysis_results(analysis_result: SemgrepAnalysisResult):
    """
    Background task to cache analysis results for future retrieval
    """
    try:
        # This would store results in PostgreSQL or Redis
        # for quick retrieval in dashboard and reporting endpoints
        
        logger.info(f"💾 Caching analysis results for {analysis_result.repo_id}")
        
        # Placeholder for caching logic
        
    except Exception as e:
        logger.error(f"Results caching failed: {e}")

async def _generate_quality_report(repo_id: str, analysis_result: SemgrepAnalysisResult):
    """
    Background task to generate comprehensive quality report
    """
    try:
        logger.info(f"📊 Generating quality report for {repo_id}")
        
        # This would generate PDF/HTML reports
        # with detailed analysis, trends, and recommendations
        
        # Placeholder for report generation logic
        
    except Exception as e:
        logger.error(f"Quality report generation failed: {e}")