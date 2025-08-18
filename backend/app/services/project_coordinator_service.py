"""
Project Coordinator Service for DocXP Enterprise
Orchestrates multi-repository analysis and modernization projects
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid

from sqlalchemy import select, update, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import redis
from rq import Queue

from app.core.config import settings
from app.core.database import get_async_session
from app.models.project import (
    Project, ProjectRepository, ProjectPhase, ProjectDependency,
    ProjectStatus, ProjectPriority, RepositoryRole,
    calculate_project_complexity, estimate_project_duration, create_default_phases
)
from app.models.business_rule_trace import BusinessRuleTrace, FlowStep
from app.models.architectural_insight import ArchitecturalInsight
from app.services.knowledge_graph_service import get_knowledge_graph_service

logger = logging.getLogger(__name__)

@dataclass
class ProjectProgress:
    """Project progress tracking data"""
    project_id: str
    overall_progress: float
    repositories_completed: int
    repositories_total: int
    business_rules_discovered: int
    insights_generated: int
    current_phase: str
    estimated_completion: Optional[datetime]
    blocking_issues: List[str]
    resource_utilization: Dict[str, float]

@dataclass 
class RepositoryAnalysisJob:
    """Repository analysis job configuration"""
    repository_id: str
    project_id: str
    priority: int
    analysis_type: str  # full, incremental, targeted
    dependencies: List[str]  # Repository IDs this depends on
    estimated_duration: int  # Minutes
    retry_count: int = 0
    max_retries: int = 3

class JobPriority(Enum):
    """Job priority levels"""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4

class ProjectCoordinatorService:
    """
    Advanced project coordination service for enterprise modernization
    
    Capabilities:
    - Multi-repository job orchestration
    - Dependency-aware scheduling
    - Progress tracking and reporting
    - Resource allocation and load balancing
    - Failure isolation and recovery
    """
    
    def __init__(self):
        self.redis_client = None
        self.job_queue = None
        self.max_concurrent_repos = settings.MAX_CONCURRENT_REPOS
        self.batch_size = settings.BATCH_SIZE
        self._initialize_queue()
        
        # Progress tracking
        self._active_projects: Dict[str, ProjectProgress] = {}
        self._job_monitor_task = None
    
    def _initialize_queue(self):
        """Initialize Redis connection and job queue"""
        try:
            self.redis_client = redis.from_url(settings.RQ_REDIS_URL)
            self.job_queue = Queue('docxp_projects', connection=self.redis_client)
            logger.info("Project coordinator queue initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize project queue: {e}. Running in offline mode.")
            # Graceful degradation - continue without Redis queue
            self.redis_client = None
            self.job_queue = None
    
    async def create_project(
        self,
        name: str,
        description: str,
        repository_ids: List[str],
        modernization_goals: Dict[str, Any],
        business_sponsor: str = None,
        technical_lead: str = None,
        created_by: str = None
    ) -> str:
        """Create new enterprise modernization project"""
        try:
            async with get_async_session() as session:
                # Generate project ID
                from app.models.project import generate_project_id
                project_id = generate_project_id(name)
                
                # Create project record
                project = Project(
                    project_id=project_id,
                    name=name,
                    description=description,
                    business_sponsor=business_sponsor,
                    technical_lead=technical_lead,
                    modernization_goals=modernization_goals,
                    created_by=created_by,
                    status=ProjectStatus.PLANNING.value
                )
                
                session.add(project)
                await session.flush()  # Get the ID
                
                # Create repository assignments
                repo_assignments = []
                for i, repo_id in enumerate(repository_ids):
                    assignment = ProjectRepository(
                        project_id=project.id,
                        repository_id=repo_id,
                        repository_role=RepositoryRole.PRIMARY.value if i == 0 else RepositoryRole.DEPENDENCY.value,
                        priority=i + 1
                    )
                    repo_assignments.append(assignment)
                    session.add(assignment)
                
                # Analyze repository relationships
                await self._analyze_repository_dependencies(session, project.id, repository_ids)
                
                # Calculate project complexity
                complexity = await self._calculate_project_complexity(session, project.id)
                project.complexity_score = complexity
                
                # Create default phases
                default_phases = create_default_phases("phased")
                for phase_data in default_phases:
                    phase = ProjectPhase(
                        project_id=project.id,
                        **phase_data
                    )
                    session.add(phase)
                
                await session.commit()
                
                logger.info(f"Created project {project_id} with {len(repository_ids)} repositories")
                return project_id
                
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            raise
    
    async def start_project_analysis(
        self,
        project_id: str,
        analysis_type: str = "full",
        priority: JobPriority = JobPriority.NORMAL
    ) -> Dict[str, Any]:
        """Start comprehensive analysis for all repositories in project"""
        try:
            async with get_async_session() as session:
                # Get project with repositories
                result = await session.execute(
                    select(Project)
                    .options(selectinload(Project.repository_assignments))
                    .where(Project.project_id == project_id)
                )
                project = result.scalar_one_or_none()
                
                if not project:
                    raise ValueError(f"Project {project_id} not found")
                
                # Update project status
                project.status = ProjectStatus.ANALYSIS.value
                project.actual_start_date = datetime.utcnow()
                
                # Create analysis jobs for each repository
                jobs_created = []
                dependency_graph = await self._build_dependency_graph(session, project.id)
                
                # Schedule jobs in dependency order
                scheduled_jobs = await self._schedule_repository_jobs(
                    project_id,
                    dependency_graph,
                    analysis_type,
                    priority
                )
                
                # Initialize progress tracking
                self._active_projects[project_id] = ProjectProgress(
                    project_id=project_id,
                    overall_progress=0.0,
                    repositories_completed=0,
                    repositories_total=len(project.repository_assignments),
                    business_rules_discovered=0,
                    insights_generated=0,
                    current_phase="Analysis",
                    estimated_completion=None,
                    blocking_issues=[],
                    resource_utilization={}
                )
                
                await session.commit()
                
                # Start job monitoring
                if not self._job_monitor_task:
                    self._job_monitor_task = asyncio.create_task(self._monitor_project_jobs())
                
                logger.info(f"Started analysis for project {project_id} with {len(scheduled_jobs)} jobs")
                
                return {
                    "project_id": project_id,
                    "jobs_scheduled": len(scheduled_jobs),
                    "estimated_duration_hours": sum(job.estimated_duration for job in scheduled_jobs) / 60,
                    "job_ids": [job.repository_id for job in scheduled_jobs]
                }
                
        except Exception as e:
            logger.error(f"Error starting project analysis: {e}")
            raise
    
    async def _analyze_repository_dependencies(
        self,
        session: AsyncSession,
        project_id: str,
        repository_ids: List[str]
    ):
        """Analyze dependencies between repositories in project"""
        try:
            # Use knowledge graph to find cross-repository dependencies
            kg_service = await get_knowledge_graph_service()
            dependencies = await kg_service.get_cross_repository_dependencies(repository_ids)
            
            # Update repository assignments with dependency information
            for repo_id, repo_deps in dependencies.items():
                # Find the project repository record
                result = await session.execute(
                    select(ProjectRepository).where(
                        and_(
                            ProjectRepository.project_id == project_id,
                            ProjectRepository.repository_id == repo_id
                        )
                    )
                )
                project_repo = result.scalar_one_or_none()
                
                if project_repo:
                    dep_repo_ids = [dep["target_repository"] for dep in repo_deps]
                    project_repo.depends_on_repositories = dep_repo_ids
                    
                    # Calculate dependency strength
                    if dep_repo_ids:
                        strength = min(len(dep_repo_ids) / 5.0, 1.0)  # Normalize to 0-1
                        project_repo.dependency_strength = strength
                        
                        # Identify shared components
                        shared_components = {}
                        for dep in repo_deps:
                            if dep["relationship_type"] in ["CALLS", "USES", "DEPENDS_ON"]:
                                shared_components[dep["target_entity"]] = dep["relationship_type"]
                        
                        project_repo.shared_components = shared_components
            
        except Exception as e:
            logger.error(f"Error analyzing repository dependencies: {e}")
    
    async def _calculate_project_complexity(self, session: AsyncSession, project_id: str) -> float:
        """Calculate overall project complexity score"""
        try:
            # Get repository assignments
            result = await session.execute(
                select(ProjectRepository).where(ProjectRepository.project_id == project_id)
            )
            repo_assignments = result.scalars().all()
            
            if not repo_assignments:
                return 0.0
            
            # Calculate complexity factors
            repo_count = len(repo_assignments)
            total_dependencies = sum(len(repo.depends_on_repositories or []) for repo in repo_assignments)
            avg_dependency_strength = sum(repo.dependency_strength or 0 for repo in repo_assignments) / len(repo_assignments)
            
            # Get technology diversity from graph
            kg_service = await get_knowledge_graph_service()
            stats = await kg_service.get_graph_statistics()
            technology_diversity = len(stats.get("node_types", {}).get("TechnologyComponent", 0))
            
            # Calculate complexity (0-10 scale)
            complexity = (
                min(repo_count / 10, 1.0) * 2.5 +
                min(total_dependencies / 50, 1.0) * 2.0 +
                avg_dependency_strength * 2.0 +
                min(technology_diversity / 20, 1.0) * 2.5 +
                1.0  # Base complexity
            )
            
            return min(complexity, 10.0)
            
        except Exception as e:
            logger.error(f"Error calculating project complexity: {e}")
            return 5.0  # Default moderate complexity
    
    async def _build_dependency_graph(self, session: AsyncSession, project_id: str) -> Dict[str, List[str]]:
        """Build dependency graph for repository processing order"""
        try:
            result = await session.execute(
                select(ProjectRepository).where(ProjectRepository.project_id == project_id)
            )
            repo_assignments = result.scalars().all()
            
            dependency_graph = {}
            for repo in repo_assignments:
                repo_id = str(repo.repository_id)
                dependencies = repo.depends_on_repositories or []
                dependency_graph[repo_id] = dependencies
            
            return dependency_graph
            
        except Exception as e:
            logger.error(f"Error building dependency graph: {e}")
            return {}
    
    async def _schedule_repository_jobs(
        self,
        project_id: str,
        dependency_graph: Dict[str, List[str]],
        analysis_type: str,
        priority: JobPriority
    ) -> List[RepositoryAnalysisJob]:
        """Schedule repository analysis jobs respecting dependencies"""
        try:
            # Topological sort for dependency order
            scheduled_order = self._topological_sort(dependency_graph)
            
            jobs = []
            for i, repo_id in enumerate(scheduled_order):
                dependencies = dependency_graph.get(repo_id, [])
                
                # Estimate duration based on repository size and complexity
                estimated_duration = await self._estimate_analysis_duration(repo_id, analysis_type)
                
                job = RepositoryAnalysisJob(
                    repository_id=repo_id,
                    project_id=project_id,
                    priority=priority.value + i,  # Dependency order affects priority
                    analysis_type=analysis_type,
                    dependencies=dependencies,
                    estimated_duration=estimated_duration
                )
                
                jobs.append(job)
                
                # Queue the actual job
                self.job_queue.enqueue(
                    'app.workers.repository_analysis_worker.analyze_repository',
                    repo_id,
                    project_id,
                    analysis_type,
                    job_timeout=estimated_duration * 60,  # Convert to seconds
                    job_id=f"repo_analysis_{project_id}_{repo_id}",
                    depends_on=[f"repo_analysis_{project_id}_{dep}" for dep in dependencies]
                )
            
            return jobs
            
        except Exception as e:
            logger.error(f"Error scheduling repository jobs: {e}")
            return []
    
    def _topological_sort(self, dependency_graph: Dict[str, List[str]]) -> List[str]:
        """Perform topological sort on dependency graph"""
        # Kahn's algorithm for topological sorting
        in_degree = {node: 0 for node in dependency_graph}
        
        # Calculate in-degrees
        for node, dependencies in dependency_graph.items():
            for dep in dependencies:
                if dep in in_degree:
                    in_degree[dep] += 1
        
        # Queue nodes with no dependencies
        queue = [node for node, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            node = queue.pop(0)
            result.append(node)
            
            # Update in-degrees for dependent nodes
            for other_node, dependencies in dependency_graph.items():
                if node in dependencies:
                    in_degree[other_node] -= 1
                    if in_degree[other_node] == 0:
                        queue.append(other_node)
        
        # Check for cycles
        if len(result) != len(dependency_graph):
            logger.warning("Circular dependency detected in project repositories")
            # Return original order as fallback
            return list(dependency_graph.keys())
        
        return result
    
    async def _estimate_analysis_duration(self, repository_id: str, analysis_type: str) -> int:
        """Estimate analysis duration in minutes for repository"""
        try:
            # Base durations by analysis type
            base_durations = {
                "full": 120,      # 2 hours for full analysis
                "incremental": 30, # 30 minutes for incremental
                "targeted": 60    # 1 hour for targeted analysis
            }
            
            base_duration = base_durations.get(analysis_type, 60)
            
            # TODO: Adjust based on repository size and complexity
            # This would require repository metadata
            
            return base_duration
            
        except Exception as e:
            logger.error(f"Error estimating analysis duration: {e}")
            return 60  # Default 1 hour
    
    async def _monitor_project_jobs(self):
        """Monitor project job progress and update status"""
        try:
            while True:
                for project_id in list(self._active_projects.keys()):
                    await self._update_project_progress(project_id)
                
                # Sleep before next check
                await asyncio.sleep(30)  # Check every 30 seconds
                
        except asyncio.CancelledError:
            logger.info("Project job monitoring cancelled")
        except Exception as e:
            logger.error(f"Error in project job monitoring: {e}")
    
    async def _update_project_progress(self, project_id: str):
        """Update progress for a specific project"""
        try:
            async with get_async_session() as session:
                # Get project and repository assignments
                result = await session.execute(
                    select(Project)
                    .options(selectinload(Project.repository_assignments))
                    .where(Project.project_id == project_id)
                )
                project = result.scalar_one_or_none()
                
                if not project:
                    # Remove from active projects if not found
                    self._active_projects.pop(project_id, None)
                    return
                
                # Count completed repositories
                completed_repos = sum(
                    1 for repo in project.repository_assignments
                    if repo.analysis_status == "completed"
                )
                
                total_repos = len(project.repository_assignments)
                overall_progress = (completed_repos / total_repos * 100) if total_repos > 0 else 0
                
                # Count business rules and insights
                business_rules_count = await session.scalar(
                    select(BusinessRuleTrace).where(
                        BusinessRuleTrace.repository_id.in_([
                            repo.repository_id for repo in project.repository_assignments
                        ])
                    ).count()
                )
                
                insights_count = await session.scalar(
                    select(ArchitecturalInsight).where(
                        ArchitecturalInsight.repository_id.in_([
                            repo.repository_id for repo in project.repository_assignments
                        ])
                    ).count()
                )
                
                # Update project progress
                project.progress_percentage = overall_progress
                project.repositories_analyzed = completed_repos
                project.business_rules_discovered = business_rules_count or 0
                project.insights_generated = insights_count or 0
                
                # Update in-memory progress
                if project_id in self._active_projects:
                    progress = self._active_projects[project_id]
                    progress.overall_progress = overall_progress
                    progress.repositories_completed = completed_repos
                    progress.business_rules_discovered = business_rules_count or 0
                    progress.insights_generated = insights_count or 0
                
                # Check if project is complete
                if completed_repos == total_repos and project.status != ProjectStatus.COMPLETED.value:
                    project.status = ProjectStatus.COMPLETED.value
                    project.actual_end_date = datetime.utcnow()
                    
                    # Remove from active monitoring
                    self._active_projects.pop(project_id, None)
                    
                    logger.info(f"Project {project_id} completed")
                
                await session.commit()
                
        except Exception as e:
            logger.error(f"Error updating project progress for {project_id}: {e}")
    
    async def get_project_progress(self, project_id: str) -> Optional[ProjectProgress]:
        """Get current progress for project"""
        return self._active_projects.get(project_id)
    
    async def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """Get comprehensive project status"""
        try:
            async with get_async_session() as session:
                result = await session.execute(
                    select(Project)
                    .options(
                        selectinload(Project.repository_assignments),
                        selectinload(Project.project_phases)
                    )
                    .where(Project.project_id == project_id)
                )
                project = result.scalar_one_or_none()
                
                if not project:
                    return {}
                
                # Get in-memory progress if available
                progress = self._active_projects.get(project_id)
                
                status = {
                    "project_id": project_id,
                    "name": project.name,
                    "status": project.status,
                    "progress_percentage": project.progress_percentage,
                    "repositories": {
                        "total": len(project.repository_assignments),
                        "analyzed": project.repositories_analyzed,
                        "in_progress": len([
                            repo for repo in project.repository_assignments
                            if repo.analysis_status == "in_progress"
                        ]),
                        "pending": len([
                            repo for repo in project.repository_assignments
                            if repo.analysis_status == "pending"
                        ])
                    },
                    "discoveries": {
                        "business_rules": project.business_rules_discovered,
                        "insights": project.insights_generated
                    },
                    "timeline": {
                        "planned_start": project.planned_start_date.isoformat() if project.planned_start_date else None,
                        "actual_start": project.actual_start_date.isoformat() if project.actual_start_date else None,
                        "planned_end": project.planned_end_date.isoformat() if project.planned_end_date else None,
                        "actual_end": project.actual_end_date.isoformat() if project.actual_end_date else None
                    },
                    "phases": [
                        {
                            "name": phase.phase_name,
                            "status": phase.status,
                            "progress": phase.progress_percentage
                        }
                        for phase in project.project_phases
                    ]
                }
                
                # Add real-time progress if available
                if progress:
                    status["real_time"] = {
                        "estimated_completion": progress.estimated_completion.isoformat() if progress.estimated_completion else None,
                        "blocking_issues": progress.blocking_issues,
                        "resource_utilization": progress.resource_utilization
                    }
                
                return status
                
        except Exception as e:
            logger.error(f"Error getting project status: {e}")
            return {}
    
    async def list_active_projects(self) -> List[Dict[str, Any]]:
        """List all active projects with summary information"""
        try:
            async with get_async_session() as session:
                result = await session.execute(
                    select(Project).where(
                        Project.status.in_([
                            ProjectStatus.PLANNING.value,
                            ProjectStatus.ANALYSIS.value,
                            ProjectStatus.DISCOVERY.value,
                            ProjectStatus.ASSESSMENT.value,
                            ProjectStatus.DESIGN.value,
                            ProjectStatus.IMPLEMENTATION.value
                        ])
                    ).order_by(Project.created_at.desc())
                )
                projects = result.scalars().all()
                
                project_summaries = []
                for project in projects:
                    summary = {
                        "project_id": project.project_id,
                        "name": project.name,
                        "status": project.status,
                        "priority": project.priority,
                        "progress_percentage": project.progress_percentage,
                        "complexity_score": project.complexity_score,
                        "created_at": project.created_at.isoformat(),
                        "business_sponsor": project.business_sponsor,
                        "technical_lead": project.technical_lead
                    }
                    project_summaries.append(summary)
                
                return project_summaries
                
        except Exception as e:
            logger.error(f"Error listing active projects: {e}")
            return []
    
    async def pause_project(self, project_id: str, reason: str = None) -> bool:
        """Pause project analysis"""
        try:
            async with get_async_session() as session:
                result = await session.execute(
                    select(Project).where(Project.project_id == project_id)
                )
                project = result.scalar_one_or_none()
                
                if not project:
                    return False
                
                project.status = ProjectStatus.ON_HOLD.value
                
                # Cancel pending jobs for this project
                # TODO: Implement job cancellation in RQ
                
                await session.commit()
                
                logger.info(f"Paused project {project_id}: {reason}")
                return True
                
        except Exception as e:
            logger.error(f"Error pausing project: {e}")
            return False
    
    async def resume_project(self, project_id: str) -> bool:
        """Resume paused project"""
        try:
            async with get_async_session() as session:
                result = await session.execute(
                    select(Project).where(Project.project_id == project_id)
                )
                project = result.scalar_one_or_none()
                
                if not project or project.status != ProjectStatus.ON_HOLD.value:
                    return False
                
                project.status = ProjectStatus.ANALYSIS.value
                
                # Restart analysis for incomplete repositories
                await self.start_project_analysis(project_id, "incremental")
                
                await session.commit()
                
                logger.info(f"Resumed project {project_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error resuming project: {e}")
            return False

# Global service instance
_project_coordinator_service = None

async def get_project_coordinator_service() -> ProjectCoordinatorService:
    """Get project coordinator service instance"""
    global _project_coordinator_service
    if _project_coordinator_service is None:
        _project_coordinator_service = ProjectCoordinatorService()
    return _project_coordinator_service