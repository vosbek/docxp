"""
Enhanced V1 Indexing Service with jQAssistant Integration

Extends the V1 indexing pipeline to include comprehensive architectural analysis:
- Automatic jQAssistant analysis for Java repositories
- Integration of architectural insights with code entities
- Enhanced search metadata with architectural information
- Unified progress tracking for both indexing and architectural analysis
- Smart analysis triggering based on repository characteristics
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import re

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.v1_indexing_service import V1IndexingService, get_v1_indexing_service
from app.services.jqassistant_batch_service import get_jqassistant_batch_service
from app.models.indexing_models import IndexingJob, JobStatus, JobType
from app.core.database import get_async_session
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class EnhancedV1IndexingService:
    """
    Enhanced V1 indexing service with integrated architectural analysis
    
    Provides comprehensive repository analysis by combining:
    - V1 indexing for semantic search and embeddings
    - jQAssistant for architectural analysis and compliance
    - Unified progress tracking and error handling
    - Smart analysis triggering based on repository characteristics
    """
    
    def __init__(self):
        self.v1_service = None
        self.jqassistant_service = None
        
        # Configuration for analysis triggering
        self.java_file_threshold = 10  # Minimum Java files to trigger architectural analysis
        self.java_file_patterns = [
            r'.*\.java$',
            r'.*\.jsp$',
            r'.*\.xml$',  # For Spring/Maven configurations
            r'.*pom\.xml$',
            r'.*build\.gradle$'
        ]
        
        # Initialize services
        asyncio.create_task(self._initialize_services())
    
    async def _initialize_services(self):
        """Initialize required services"""
        try:
            self.v1_service = await get_v1_indexing_service()
            self.jqassistant_service = await get_jqassistant_batch_service()
            logger.info("✅ Enhanced V1 Indexing Service initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Enhanced V1 Indexing Service: {e}")
            raise
    
    async def start_enhanced_indexing_job(
        self,
        repository_path: str,
        job_type: JobType = JobType.FULL,
        file_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        force_reindex: bool = False,
        enable_architectural_analysis: Optional[bool] = None,
        custom_architectural_layers: Optional[List[Dict[str, Any]]] = None,
        custom_architectural_constraints: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """
        Start enhanced indexing job with optional architectural analysis
        
        Args:
            repository_path: Path to repository to index
            job_type: Type of indexing (full, incremental, selective)
            file_patterns: Patterns to include (e.g., ['*.java', '*.jsp'])
            exclude_patterns: Patterns to exclude (e.g., ['**/test/**'])
            force_reindex: Reindex files even if already processed
            enable_architectural_analysis: Enable jQAssistant analysis (auto-detected if None)
            custom_architectural_layers: Custom architectural layer definitions
            custom_architectural_constraints: Additional constraint rules
            
        Returns:
            Dictionary with job IDs and status information
        """
        try:
            repo_path = Path(repository_path)
            if not repo_path.exists():
                raise ValueError(f"Repository path does not exist: {repository_path}")
            
            logger.info(f"🚀 Starting enhanced indexing for {repository_path}")
            
            # Start V1 indexing job
            indexing_job_id = await self.v1_service.start_indexing_job(
                repository_path=repository_path,
                job_type=job_type,
                file_patterns=file_patterns,
                exclude_patterns=exclude_patterns,
                force_reindex=force_reindex
            )
            
            result = {
                "indexing_job_id": indexing_job_id,
                "architectural_analysis_job_id": None,
                "architectural_analysis_enabled": False,
                "java_files_detected": 0
            }
            
            # Determine if architectural analysis should be enabled
            if enable_architectural_analysis is None:
                enable_architectural_analysis = await self._should_enable_architectural_analysis(repo_path)
            
            if enable_architectural_analysis:
                # Detect Java files and repository characteristics
                java_info = await self._analyze_java_repository(repo_path)
                result["java_files_detected"] = java_info["java_file_count"]
                
                if java_info["java_file_count"] >= self.java_file_threshold:
                    # Start architectural analysis
                    architectural_job_id = await self.jqassistant_service.start_architectural_analysis(
                        repository_path=repository_path,
                        repository_id=self._extract_repository_id(repository_path),
                        commit_hash=await self._get_current_commit_hash(repo_path),
                        indexing_job_id=indexing_job_id,
                        custom_layers=custom_architectural_layers,
                        custom_constraints=custom_architectural_constraints,
                        include_test_code=False  # Default to production code only
                    )
                    
                    result["architectural_analysis_job_id"] = architectural_job_id
                    result["architectural_analysis_enabled"] = True
                    
                    logger.info(f"✅ Started architectural analysis job {architectural_job_id} "
                              f"for {java_info['java_file_count']} Java files")
                else:
                    logger.info(f"📊 Java files detected ({java_info['java_file_count']}) below threshold "
                              f"({self.java_file_threshold}), skipping architectural analysis")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Enhanced indexing job failed: {e}")
            raise
    
    async def _should_enable_architectural_analysis(self, repo_path: Path) -> bool:
        """Determine if architectural analysis should be enabled for repository"""
        try:
            java_info = await self._analyze_java_repository(repo_path)
            
            # Enable if sufficient Java files and Java project indicators
            has_sufficient_files = java_info["java_file_count"] >= self.java_file_threshold
            has_java_project_files = java_info["has_maven"] or java_info["has_gradle"] or java_info["has_spring"]
            
            return has_sufficient_files and has_java_project_files
            
        except Exception as e:
            logger.warning(f"Failed to determine architectural analysis eligibility: {e}")
            return False
    
    async def _analyze_java_repository(self, repo_path: Path) -> Dict[str, Any]:
        """Analyze repository to determine Java project characteristics"""
        try:
            java_info = {
                "java_file_count": 0,
                "has_maven": False,
                "has_gradle": False,
                "has_spring": False,
                "java_packages": set(),
                "source_directories": []
            }
            
            # Count Java files and analyze structure
            for file_path in repo_path.rglob('*'):
                if file_path.is_file():
                    file_str = str(file_path)
                    
                    # Count Java files
                    if any(re.match(pattern, file_str) for pattern in self.java_file_patterns):
                        if file_path.suffix == '.java':
                            java_info["java_file_count"] += 1
                            
                            # Extract package information
                            package = self._extract_package_from_java_file(file_path)
                            if package:
                                java_info["java_packages"].add(package)
                        
                        # Detect source directories
                        if '/src/main/java/' in file_str or '\\src\\main\\java\\' in file_str:
                            src_dir = str(file_path.parent)
                            if src_dir not in java_info["source_directories"]:
                                java_info["source_directories"].append(src_dir)
                    
                    # Detect project types
                    if file_path.name == 'pom.xml':
                        java_info["has_maven"] = True
                    elif file_path.name in ['build.gradle', 'build.gradle.kts']:
                        java_info["has_gradle"] = True
                    elif 'spring' in file_str.lower() or file_path.name == 'application.properties':
                        java_info["has_spring"] = True
            
            java_info["java_packages"] = list(java_info["java_packages"])
            
            logger.debug(f"Java repository analysis: {java_info['java_file_count']} files, "
                        f"{len(java_info['java_packages'])} packages")
            
            return java_info
            
        except Exception as e:
            logger.error(f"Failed to analyze Java repository: {e}")
            return {"java_file_count": 0, "has_maven": False, "has_gradle": False, "has_spring": False}
    
    def _extract_package_from_java_file(self, file_path: Path) -> Optional[str]:
        """Extract package declaration from Java file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('package ') and line.endswith(';'):
                        package = line[8:-1].strip()  # Remove 'package ' and ';'
                        return package
                    elif line.startswith('import ') or line.startswith('public class'):
                        # Stop looking if we hit imports or class declaration
                        break
            return None
        except Exception:
            return None
    
    def _extract_repository_id(self, repository_path: str) -> str:
        """Extract repository identifier from path"""
        return Path(repository_path).name
    
    async def _get_current_commit_hash(self, repo_path: Path) -> str:
        """Get current Git commit hash"""
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                # Fallback to current timestamp if not a git repository
                return f"snapshot-{int(datetime.now().timestamp())}"
        except Exception:
            return f"snapshot-{int(datetime.now().timestamp())}"
    
    async def get_enhanced_job_status(self, indexing_job_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive status for enhanced indexing job"""
        try:
            # Get V1 indexing job status
            indexing_status = await self.v1_service.get_job_status(indexing_job_id)
            
            if not indexing_status:
                return None
            
            enhanced_status = {
                "indexing_job": indexing_status,
                "architectural_analysis_job": None,
                "overall_status": indexing_status["status"],
                "overall_progress": indexing_status["progress"]["progress_percentage"],
                "architectural_insights": []
            }
            
            # Check for linked architectural analysis job
            async with get_async_session() as session:
                result = await session.execute(
                    select(IndexingJob).where(IndexingJob.id == indexing_job_id)
                )
                indexing_job = result.scalar_one_or_none()
                
                if indexing_job and hasattr(indexing_job, 'architectural_analysis') and indexing_job.architectural_analysis:
                    arch_analysis = indexing_job.architectural_analysis[0]  # Assume one analysis per job
                    
                    # Get architectural analysis status
                    arch_status = await self.jqassistant_service.get_analysis_job_status(str(arch_analysis.id))
                    enhanced_status["architectural_analysis_job"] = arch_status
                    
                    # Calculate overall progress (weighted average)
                    if arch_status:
                        indexing_weight = 0.7  # 70% of overall progress
                        arch_weight = 0.3      # 30% of overall progress
                        
                        indexing_progress = indexing_status["progress"]["progress_percentage"]
                        arch_progress = 100.0 if arch_status["status"] == "completed" else 0.0
                        
                        enhanced_status["overall_progress"] = (
                            indexing_progress * indexing_weight + arch_progress * arch_weight
                        )
                        
                        # Determine overall status
                        if indexing_status["status"] == "completed" and arch_status["status"] == "completed":
                            enhanced_status["overall_status"] = "completed"
                        elif indexing_status["status"] == "failed" or arch_status["status"] == "failed":
                            enhanced_status["overall_status"] = "failed"
                        else:
                            enhanced_status["overall_status"] = "running"
            
            return enhanced_status
            
        except Exception as e:
            logger.error(f"Failed to get enhanced job status: {e}")
            return None
    
    async def get_architectural_summary(self, indexing_job_id: str) -> Optional[Dict[str, Any]]:
        """Get architectural analysis summary for an indexing job"""
        try:
            async with get_async_session() as session:
                result = await session.execute(
                    select(IndexingJob).where(IndexingJob.id == indexing_job_id)
                )
                indexing_job = result.scalar_one_or_none()
                
                if not indexing_job or not hasattr(indexing_job, 'architectural_analysis'):
                    return None
                
                if not indexing_job.architectural_analysis:
                    return {"status": "not_analyzed", "reason": "No architectural analysis performed"}
                
                arch_job = indexing_job.architectural_analysis[0]
                
                summary = {
                    "status": arch_job.status.value,
                    "analysis_job_id": str(arch_job.id),
                    "repository_id": arch_job.repository_id,
                    "commit_hash": arch_job.commit_hash,
                    "quality_scores": {
                        "overall_quality_score": arch_job.overall_quality_score,
                        "layer_compliance_score": arch_job.layer_compliance_score,
                        "architectural_debt_score": arch_job.architectural_debt_score
                    },
                    "metrics": {
                        "total_packages": arch_job.total_packages,
                        "total_classes": arch_job.total_classes,
                        "total_methods": arch_job.total_methods,
                        "total_dependencies": arch_job.total_dependencies,
                        "cyclic_dependencies_count": arch_job.cyclic_dependencies_count,
                        "architectural_violations_count": arch_job.architectural_violations_count
                    },
                    "timing": {
                        "created_at": arch_job.created_at.isoformat() if arch_job.created_at else None,
                        "started_at": arch_job.started_at.isoformat() if arch_job.started_at else None,
                        "completed_at": arch_job.completed_at.isoformat() if arch_job.completed_at else None,
                        "analysis_duration_seconds": arch_job.analysis_duration_seconds
                    }
                }
                
                return summary
                
        except Exception as e:
            logger.error(f"Failed to get architectural summary: {e}")
            return None
    
    async def trigger_architectural_analysis_for_existing_job(
        self,
        indexing_job_id: str,
        custom_layers: Optional[List[Dict[str, Any]]] = None,
        custom_constraints: Optional[List[str]] = None,
        include_test_code: bool = False
    ) -> Optional[str]:
        """Trigger architectural analysis for an existing indexing job"""
        try:
            async with get_async_session() as session:
                result = await session.execute(
                    select(IndexingJob).where(IndexingJob.id == indexing_job_id)
                )
                indexing_job = result.scalar_one_or_none()
                
                if not indexing_job:
                    raise ValueError(f"Indexing job {indexing_job_id} not found")
                
                # Check if architectural analysis already exists
                if hasattr(indexing_job, 'architectural_analysis') and indexing_job.architectural_analysis:
                    raise ValueError(f"Architectural analysis already exists for job {indexing_job_id}")
                
                # Start architectural analysis
                architectural_job_id = await self.jqassistant_service.start_architectural_analysis(
                    repository_path=indexing_job.repository_path,
                    repository_id=self._extract_repository_id(indexing_job.repository_path),
                    commit_hash=await self._get_current_commit_hash(Path(indexing_job.repository_path)),
                    indexing_job_id=indexing_job_id,
                    custom_layers=custom_layers,
                    custom_constraints=custom_constraints,
                    include_test_code=include_test_code
                )
                
                logger.info(f"✅ Triggered architectural analysis {architectural_job_id} "
                          f"for existing indexing job {indexing_job_id}")
                
                return architectural_job_id
                
        except Exception as e:
            logger.error(f"Failed to trigger architectural analysis: {e}")
            raise
    
    async def list_enhanced_jobs(
        self, 
        limit: int = 10,
        include_architectural_analysis: bool = True
    ) -> List[Dict[str, Any]]:
        """List recent enhanced indexing jobs with architectural analysis information"""
        try:
            # Get recent V1 indexing jobs
            indexing_jobs = await self.v1_service.list_recent_jobs(limit)
            
            enhanced_jobs = []
            
            for job in indexing_jobs:
                enhanced_job = dict(job)
                enhanced_job["architectural_analysis"] = None
                
                if include_architectural_analysis:
                    # Get architectural analysis summary
                    arch_summary = await self.get_architectural_summary(job["job_id"])
                    if arch_summary:
                        enhanced_job["architectural_analysis"] = arch_summary
                
                enhanced_jobs.append(enhanced_job)
            
            return enhanced_jobs
            
        except Exception as e:
            logger.error(f"Failed to list enhanced jobs: {e}")
            return []
    
    async def get_repository_health_score(self, repository_path: str) -> Dict[str, Any]:
        """Calculate comprehensive repository health score"""
        try:
            repo_path = Path(repository_path)
            if not repo_path.exists():
                raise ValueError(f"Repository path does not exist: {repository_path}")
            
            # Get the latest completed analysis for this repository
            async with get_async_session() as session:
                from app.models.indexing_models import ArchitecturalAnalysisJob
                
                result = await session.execute(
                    select(ArchitecturalAnalysisJob)
                    .where(
                        ArchitecturalAnalysisJob.repository_path == str(repo_path.absolute()),
                        ArchitecturalAnalysisJob.status == JobStatus.COMPLETED
                    )
                    .order_by(ArchitecturalAnalysisJob.completed_at.desc())
                    .limit(1)
                )
                latest_analysis = result.scalar_one_or_none()
                
                if not latest_analysis:
                    return {
                        "status": "no_analysis",
                        "message": "No completed architectural analysis found",
                        "health_score": None
                    }
                
                # Calculate health score based on multiple factors
                health_factors = {
                    "code_quality": latest_analysis.overall_quality_score,
                    "architectural_compliance": latest_analysis.layer_compliance_score,
                    "architectural_debt": 100 - latest_analysis.architectural_debt_score,  # Invert debt score
                    "cyclic_dependencies": max(0, 100 - (latest_analysis.cyclic_dependencies_count * 10)),
                    "violations": max(0, 100 - (latest_analysis.architectural_violations_count * 5))
                }
                
                # Weighted average of health factors
                weights = {
                    "code_quality": 0.3,
                    "architectural_compliance": 0.25,
                    "architectural_debt": 0.2,
                    "cyclic_dependencies": 0.15,
                    "violations": 0.1
                }
                
                health_score = sum(
                    health_factors[factor] * weights[factor]
                    for factor in health_factors
                    if health_factors[factor] is not None
                )
                
                # Determine health grade
                if health_score >= 90:
                    grade = "A"
                elif health_score >= 80:
                    grade = "B"
                elif health_score >= 70:
                    grade = "C"
                elif health_score >= 60:
                    grade = "D"
                else:
                    grade = "F"
                
                return {
                    "status": "analyzed",
                    "health_score": round(health_score, 2),
                    "health_grade": grade,
                    "health_factors": health_factors,
                    "analysis_date": latest_analysis.completed_at.isoformat(),
                    "analysis_job_id": str(latest_analysis.id),
                    "recommendations": self._generate_health_recommendations(health_factors, latest_analysis)
                }
                
        except Exception as e:
            logger.error(f"Failed to calculate repository health score: {e}")
            return {"status": "error", "message": str(e), "health_score": None}
    
    def _generate_health_recommendations(
        self, 
        health_factors: Dict[str, float], 
        analysis: Any
    ) -> List[str]:
        """Generate health improvement recommendations"""
        recommendations = []
        
        if health_factors["code_quality"] < 70:
            recommendations.append("Reduce code complexity and improve maintainability")
        
        if health_factors["architectural_compliance"] < 80:
            recommendations.append("Review and enforce architectural layer constraints")
        
        if health_factors["cyclic_dependencies"] < 80:
            recommendations.append("Break cyclic dependencies by introducing abstractions")
        
        if health_factors["violations"] < 90:
            recommendations.append("Address architectural violations with highest severity first")
        
        if analysis.cyclic_dependencies_count > 5:
            recommendations.append("Implement dependency injection to reduce tight coupling")
        
        if not recommendations:
            recommendations.append("Maintain current architectural quality standards")
        
        return recommendations

# Global service instance
enhanced_v1_indexing_service = EnhancedV1IndexingService()

async def get_enhanced_v1_indexing_service() -> EnhancedV1IndexingService:
    """Get enhanced V1 indexing service instance"""
    return enhanced_v1_indexing_service