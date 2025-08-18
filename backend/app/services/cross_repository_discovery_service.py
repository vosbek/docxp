"""
Cross-Repository Discovery Service for DocXP Enterprise
Implements Task 3.2: Repository Federation and Cross-Repository Analysis

Features:
- Identify shared libraries and dependencies across repositories
- API call mapping between repositories  
- Database schema relationship discovery
- Inter-repository dependency tracking
- Shared component analysis
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Set, Tuple, NamedTuple
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path
import json
import re
from collections import defaultdict, Counter

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
import aiofiles

from app.core.database import AsyncSessionLocal
from app.models.project import Project, ProjectRepository
from app.models.business_rule_trace import BusinessRuleTrace, FlowStep, CrossTechnologyMapping
from app.models.architectural_insight import ArchitecturalInsight
from app.services.knowledge_graph_service import KnowledgeGraphService

logger = logging.getLogger(__name__)

# Data structures for cross-repository analysis

@dataclass
class SharedLibrary:
    """Represents a shared library across repositories"""
    name: str
    version: Optional[str]
    repositories: Set[str]  # Repository IDs
    import_patterns: List[str]
    usage_frequency: int
    risk_level: str  # "low", "medium", "high"
    modernization_notes: Optional[str]

@dataclass
class APICallMapping:
    """Represents API calls between repositories"""
    source_repository: str
    target_repository: str
    api_endpoint: str
    http_method: str
    call_frequency: int
    data_exchanged: List[str]  # Data types/fields
    authentication_method: Optional[str]
    coupling_strength: float  # 0.0 to 1.0

@dataclass
class DatabaseRelationship:
    """Represents database relationships across repositories"""
    source_repository: str
    target_repository: str
    relationship_type: str  # "shared_table", "foreign_key", "view_dependency"
    database_objects: List[str]  # Tables, views, procedures
    data_flow_direction: str  # "bidirectional", "source_to_target", "target_to_source"
    impact_level: str  # "low", "medium", "high"

@dataclass
class CrossRepositoryInsight:
    """High-level insights from cross-repository analysis"""
    insight_type: str  # "shared_dependency", "api_coupling", "data_coupling"
    severity: str
    title: str
    description: str
    affected_repositories: List[str]
    modernization_impact: str
    recommended_action: str
    estimated_effort: str

class CrossRepositoryDiscoveryService:
    """Service for discovering relationships and dependencies across repositories"""
    
    def __init__(self):
        self.logger = logger
        self.knowledge_graph_service = None
        
    async def get_knowledge_graph_service(self) -> KnowledgeGraphService:
        """Get knowledge graph service instance"""
        if not self.knowledge_graph_service:
            from app.services.knowledge_graph_service import get_knowledge_graph_service
            self.knowledge_graph_service = await get_knowledge_graph_service()
        return self.knowledge_graph_service

    async def analyze_project_repositories(self, project_id: str) -> Dict[str, Any]:
        """
        Main entry point for cross-repository analysis
        Implements comprehensive discovery as specified in TODO.md Task 3.2
        """
        async with AsyncSessionLocal() as session:
            # Get project and its repositories
            project = await self._get_project_with_repositories(session, project_id)
            if not project:
                raise ValueError(f"Project {project_id} not found")
                
            repositories = [pr.repository_id for pr in project.repository_assignments]
            
            self.logger.info(f"Starting cross-repository analysis for project {project_id} with {len(repositories)} repositories")
            
            # Run parallel analysis
            shared_libs_task = self._discover_shared_libraries(session, repositories)
            api_mappings_task = self._discover_api_call_mappings(session, repositories) 
            db_relationships_task = self._discover_database_relationships(session, repositories)
            
            shared_libraries, api_mappings, db_relationships = await asyncio.gather(
                shared_libs_task, api_mappings_task, db_relationships_task
            )
            
            # Generate high-level insights
            insights = await self._generate_cross_repository_insights(
                session, repositories, shared_libraries, api_mappings, db_relationships
            )
            
            # Update knowledge graph
            await self._update_knowledge_graph(project_id, shared_libraries, api_mappings, db_relationships)
            
            # Store results in database
            await self._store_analysis_results(session, project_id, {
                'shared_libraries': [self._serialize_shared_library(lib) for lib in shared_libraries],
                'api_mappings': [self._serialize_api_mapping(mapping) for mapping in api_mappings],
                'database_relationships': [self._serialize_db_relationship(rel) for rel in db_relationships],
                'insights': [self._serialize_insight(insight) for insight in insights]
            })
            
            return {
                'project_id': project_id,
                'repositories_analyzed': len(repositories),
                'shared_libraries_found': len(shared_libraries),
                'api_mappings_found': len(api_mappings),
                'database_relationships_found': len(db_relationships),
                'insights_generated': len(insights),
                'analysis_timestamp': datetime.utcnow().isoformat(),
                'shared_libraries': shared_libraries,
                'api_mappings': api_mappings,
                'database_relationships': db_relationships,
                'insights': insights
            }

    async def _get_project_with_repositories(self, session: AsyncSession, project_id: str) -> Optional[Project]:
        """Get project with its repository assignments"""
        stmt = select(Project).where(Project.project_id == project_id).options(
            selectinload(Project.repository_assignments)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def _discover_shared_libraries(self, session: AsyncSession, repositories: List[str]) -> List[SharedLibrary]:
        """
        Discover shared libraries and dependencies across repositories
        Analyzes import statements, package.json, pom.xml, etc.
        """
        self.logger.info(f"Discovering shared libraries across {len(repositories)} repositories")
        
        shared_libraries = []
        library_usage = defaultdict(lambda: {'repos': set(), 'imports': [], 'frequency': 0})
        
        # Get all business rule traces and flow steps for dependency analysis
        for repo_id in repositories:
            stmt = select(BusinessRuleTrace).where(BusinessRuleTrace.repository_id == int(repo_id))
            traces = await session.execute(stmt)
            
            for trace in traces.scalars():
                # Analyze technology stack for shared components
                tech_stack = json.loads(trace.technology_stack) if trace.technology_stack else []
                for tech in tech_stack:
                    library_usage[tech]['repos'].add(repo_id)
                    library_usage[tech]['frequency'] += 1
                
                # Get flow steps for detailed dependency analysis
                flow_stmt = select(FlowStep).where(FlowStep.trace_id == trace.id)
                flow_result = await session.execute(flow_stmt)
                
                for step in flow_result.scalars():
                    if step.dependencies:
                        deps = json.loads(step.dependencies) if step.dependencies else []
                        for dep in deps:
                            library_usage[dep]['repos'].add(repo_id)
                            library_usage[dep]['imports'].append(step.file_path)
                            library_usage[dep]['frequency'] += 1
        
        # Convert to SharedLibrary objects for libraries used by multiple repositories
        for lib_name, usage_data in library_usage.items():
            if len(usage_data['repos']) > 1:  # Shared across multiple repos
                shared_lib = SharedLibrary(
                    name=lib_name,
                    version=None,  # TODO: Extract version info
                    repositories=usage_data['repos'],
                    import_patterns=list(set(usage_data['imports'])),
                    usage_frequency=usage_data['frequency'],
                    risk_level=self._assess_library_risk(lib_name, len(usage_data['repos'])),
                    modernization_notes=self._generate_modernization_notes(lib_name)
                )
                shared_libraries.append(shared_lib)
        
        self.logger.info(f"Found {len(shared_libraries)} shared libraries")
        return shared_libraries

    async def _discover_api_call_mappings(self, session: AsyncSession, repositories: List[str]) -> List[APICallMapping]:
        """
        Discover API calls between repositories
        Analyzes HTTP calls, REST endpoints, service communications
        """
        self.logger.info(f"Discovering API call mappings across {len(repositories)} repositories")
        
        api_mappings = []
        
        # Get cross-technology mappings for API analysis
        for repo_id in repositories:
            stmt = select(CrossTechnologyMapping).where(
                CrossTechnologyMapping.repository_id == int(repo_id)
            )
            mappings = await session.execute(stmt)
            
            for mapping in mappings.scalars():
                # Look for HTTP/API patterns in relationship types
                if self._is_api_relationship(mapping.relationship_type):
                    api_mapping = APICallMapping(
                        source_repository=repo_id,
                        target_repository=self._extract_target_repository(mapping, repositories),
                        api_endpoint=self._extract_api_endpoint(mapping),
                        http_method=self._extract_http_method(mapping),
                        call_frequency=1,  # TODO: Calculate actual frequency
                        data_exchanged=self._extract_data_types(mapping),
                        authentication_method=self._extract_auth_method(mapping),
                        coupling_strength=mapping.relationship_strength
                    )
                    if api_mapping.target_repository:
                        api_mappings.append(api_mapping)
        
        # Consolidate duplicate mappings
        api_mappings = self._consolidate_api_mappings(api_mappings)
        
        self.logger.info(f"Found {len(api_mappings)} API call mappings")
        return api_mappings

    async def _discover_database_relationships(self, session: AsyncSession, repositories: List[str]) -> List[DatabaseRelationship]:
        """
        Discover database schema relationships across repositories
        Analyzes shared tables, foreign keys, views, procedures
        """
        self.logger.info(f"Discovering database relationships across {len(repositories)} repositories")
        
        db_relationships = []
        database_objects = defaultdict(lambda: {'repos': set(), 'operations': []})
        
        # Analyze flow steps for database operations
        for repo_id in repositories:
            stmt = select(FlowStep).where(
                and_(
                    FlowStep.step_type == 'database_query',
                    # Get flow steps that belong to traces in this repository
                    FlowStep.trace_id.in_(
                        select(BusinessRuleTrace.id).where(BusinessRuleTrace.repository_id == int(repo_id))
                    )
                )
            )
            flow_steps = await session.execute(stmt)
            
            for step in flow_steps.scalars():
                if step.database_tables:
                    tables = json.loads(step.database_tables) if step.database_tables else []
                    for table in tables:
                        database_objects[table]['repos'].add(repo_id)
                        database_objects[table]['operations'].append({
                            'type': step.step_type,
                            'file': step.file_path,
                            'component': step.component_name
                        })
        
        # Create database relationships for shared objects
        for db_object, usage_data in database_objects.items():
            repos_using = list(usage_data['repos'])
            if len(repos_using) > 1:
                # Create relationships between each pair of repositories
                for i in range(len(repos_using)):
                    for j in range(i + 1, len(repos_using)):
                        db_rel = DatabaseRelationship(
                            source_repository=repos_using[i],
                            target_repository=repos_using[j],
                            relationship_type='shared_table',
                            database_objects=[db_object],
                            data_flow_direction='bidirectional',
                            impact_level=self._assess_db_impact(db_object, usage_data['operations'])
                        )
                        db_relationships.append(db_rel)
        
        self.logger.info(f"Found {len(db_relationships)} database relationships")
        return db_relationships

    async def _generate_cross_repository_insights(
        self,
        session: AsyncSession,
        repositories: List[str],
        shared_libraries: List[SharedLibrary],
        api_mappings: List[APICallMapping],
        db_relationships: List[DatabaseRelationship]
    ) -> List[CrossRepositoryInsight]:
        """Generate high-level insights from cross-repository analysis"""
        
        insights = []
        
        # Insight 1: High-risk shared dependencies
        high_risk_libs = [lib for lib in shared_libraries if lib.risk_level == 'high']
        if high_risk_libs:
            insights.append(CrossRepositoryInsight(
                insight_type='shared_dependency',
                severity='high',
                title=f'High-Risk Shared Dependencies Found',
                description=f'Found {len(high_risk_libs)} high-risk shared libraries across repositories',
                affected_repositories=list(set().union(*[lib.repositories for lib in high_risk_libs])),
                modernization_impact='high',
                recommended_action='Prioritize modernization of high-risk shared dependencies',
                estimated_effort='large'
            ))
        
        # Insight 2: High API coupling
        high_coupling_apis = [api for api in api_mappings if api.coupling_strength > 0.7]
        if high_coupling_apis:
            insights.append(CrossRepositoryInsight(
                insight_type='api_coupling',
                severity='medium',
                title=f'High API Coupling Detected',
                description=f'Found {len(high_coupling_apis)} high-coupling API relationships',
                affected_repositories=list(set([api.source_repository for api in high_coupling_apis] + 
                                             [api.target_repository for api in high_coupling_apis])),
                modernization_impact='medium',
                recommended_action='Consider API versioning and backward compatibility strategies',
                estimated_effort='medium'
            ))
        
        # Insight 3: Complex database relationships
        high_impact_db = [rel for rel in db_relationships if rel.impact_level == 'high']
        if high_impact_db:
            insights.append(CrossRepositoryInsight(
                insight_type='data_coupling',
                severity='high', 
                title=f'Complex Database Coupling Found',
                description=f'Found {len(high_impact_db)} high-impact database relationships',
                affected_repositories=list(set([rel.source_repository for rel in high_impact_db] + 
                                             [rel.target_repository for rel in high_impact_db])),
                modernization_impact='high',
                recommended_action='Plan database modernization with careful migration strategy',
                estimated_effort='large'
            ))
        
        return insights

    # Helper methods for analysis

    def _assess_library_risk(self, lib_name: str, repo_count: int) -> str:
        """Assess risk level of a shared library"""
        # Simple heuristic - can be enhanced with CVE databases, etc.
        legacy_patterns = ['struts', 'corba', 'jsp', 'legacy', 'deprecated']
        if any(pattern in lib_name.lower() for pattern in legacy_patterns):
            return 'high'
        elif repo_count > 3:
            return 'medium'
        else:
            return 'low'
    
    def _generate_modernization_notes(self, lib_name: str) -> str:
        """Generate modernization notes for a library"""
        modernization_map = {
            'struts': 'Consider migration to Spring MVC or modern web framework',
            'jsp': 'Consider migration to modern templating (Thymeleaf, React)',
            'corba': 'Consider migration to REST APIs or gRPC',
            'hibernate': 'Consider JPA standardization or Spring Data'
        }
        
        for pattern, note in modernization_map.items():
            if pattern in lib_name.lower():
                return note
        return 'Evaluate for modern alternatives'
    
    def _is_api_relationship(self, relationship_type: str) -> bool:
        """Check if relationship type indicates API communication"""
        api_patterns = ['http', 'rest', 'api', 'service_call', 'web_service']
        return any(pattern in relationship_type.lower() for pattern in api_patterns)
    
    def _extract_target_repository(self, mapping: CrossTechnologyMapping, repositories: List[str]) -> Optional[str]:
        """Extract target repository from mapping (simplified heuristic)"""
        # This would need more sophisticated logic in practice
        return repositories[1] if len(repositories) > 1 else None
    
    def _extract_api_endpoint(self, mapping: CrossTechnologyMapping) -> str:
        """Extract API endpoint from mapping"""
        return mapping.target_file_path or mapping.target_component
    
    def _extract_http_method(self, mapping: CrossTechnologyMapping) -> str:
        """Extract HTTP method from mapping"""
        # Simple heuristic - could be enhanced
        if 'post' in mapping.relationship_type.lower():
            return 'POST'
        elif 'get' in mapping.relationship_type.lower():
            return 'GET'
        else:
            return 'UNKNOWN'
    
    def _extract_data_types(self, mapping: CrossTechnologyMapping) -> List[str]:
        """Extract data types from mapping"""
        if mapping.meta_data:
            try:
                meta = json.loads(mapping.meta_data)
                return meta.get('data_types', [])
            except:
                pass
        return []
    
    def _extract_auth_method(self, mapping: CrossTechnologyMapping) -> Optional[str]:
        """Extract authentication method from mapping"""
        if mapping.meta_data:
            try:
                meta = json.loads(mapping.meta_data)
                return meta.get('auth_method')
            except:
                pass
        return None
    
    def _consolidate_api_mappings(self, mappings: List[APICallMapping]) -> List[APICallMapping]:
        """Consolidate duplicate API mappings"""
        consolidated = {}
        for mapping in mappings:
            key = (mapping.source_repository, mapping.target_repository, mapping.api_endpoint)
            if key in consolidated:
                consolidated[key].call_frequency += mapping.call_frequency
            else:
                consolidated[key] = mapping
        return list(consolidated.values())
    
    def _assess_db_impact(self, db_object: str, operations: List[Dict]) -> str:
        """Assess impact level of database relationship"""
        operation_count = len(operations)
        operation_types = set(op['type'] for op in operations)
        
        if operation_count > 10 or len(operation_types) > 3:
            return 'high'
        elif operation_count > 5:
            return 'medium'
        else:
            return 'low'
    
    # Knowledge Graph Integration
    
    async def _update_knowledge_graph(
        self,
        project_id: str,
        shared_libraries: List[SharedLibrary],
        api_mappings: List[APICallMapping],
        db_relationships: List[DatabaseRelationship]
    ):
        """Update knowledge graph with cross-repository relationships"""
        try:
            kg_service = await self.get_knowledge_graph_service()
            
            # Add shared library nodes and relationships
            for lib in shared_libraries:
                await kg_service.create_node(
                    'SharedLibrary',
                    lib.name,
                    {
                        'version': lib.version,
                        'usage_frequency': lib.usage_frequency,
                        'risk_level': lib.risk_level,
                        'project_id': project_id
                    }
                )
                
                # Create relationships to repositories
                for repo_id in lib.repositories:
                    await kg_service.create_relationship(
                        f'Repository_{repo_id}',
                        'USES_LIBRARY',
                        f'SharedLibrary_{lib.name}',
                        {'frequency': lib.usage_frequency}
                    )
            
            # Add API relationships
            for api in api_mappings:
                await kg_service.create_relationship(
                    f'Repository_{api.source_repository}',
                    'CALLS_API',
                    f'Repository_{api.target_repository}',
                    {
                        'endpoint': api.api_endpoint,
                        'method': api.http_method,
                        'coupling_strength': api.coupling_strength
                    }
                )
            
            # Add database relationships
            for db_rel in db_relationships:
                await kg_service.create_relationship(
                    f'Repository_{db_rel.source_repository}',
                    'SHARES_DATABASE',
                    f'Repository_{db_rel.target_repository}',
                    {
                        'objects': db_rel.database_objects,
                        'impact_level': db_rel.impact_level
                    }
                )
            
        except Exception as e:
            self.logger.error(f"Error updating knowledge graph: {e}")
    
    # Serialization methods for database storage
    
    def _serialize_shared_library(self, lib: SharedLibrary) -> Dict[str, Any]:
        """Serialize SharedLibrary for JSON storage"""
        return {
            'name': lib.name,
            'version': lib.version,
            'repositories': list(lib.repositories),
            'import_patterns': lib.import_patterns,
            'usage_frequency': lib.usage_frequency,
            'risk_level': lib.risk_level,
            'modernization_notes': lib.modernization_notes
        }
    
    def _serialize_api_mapping(self, api: APICallMapping) -> Dict[str, Any]:
        """Serialize APICallMapping for JSON storage"""
        return {
            'source_repository': api.source_repository,
            'target_repository': api.target_repository,
            'api_endpoint': api.api_endpoint,
            'http_method': api.http_method,
            'call_frequency': api.call_frequency,
            'data_exchanged': api.data_exchanged,
            'authentication_method': api.authentication_method,
            'coupling_strength': api.coupling_strength
        }
    
    def _serialize_db_relationship(self, rel: DatabaseRelationship) -> Dict[str, Any]:
        """Serialize DatabaseRelationship for JSON storage"""
        return {
            'source_repository': rel.source_repository,
            'target_repository': rel.target_repository,
            'relationship_type': rel.relationship_type,
            'database_objects': rel.database_objects,
            'data_flow_direction': rel.data_flow_direction,
            'impact_level': rel.impact_level
        }
    
    def _serialize_insight(self, insight: CrossRepositoryInsight) -> Dict[str, Any]:
        """Serialize CrossRepositoryInsight for JSON storage"""
        return {
            'insight_type': insight.insight_type,
            'severity': insight.severity,
            'title': insight.title,
            'description': insight.description,
            'affected_repositories': insight.affected_repositories,
            'modernization_impact': insight.modernization_impact,
            'recommended_action': insight.recommended_action,
            'estimated_effort': insight.estimated_effort
        }
    
    async def _store_analysis_results(self, session: AsyncSession, project_id: str, results: Dict[str, Any]):
        """Store cross-repository analysis results"""
        try:
            # Create architectural insight for the cross-repository analysis
            from app.models.architectural_insight import ArchitecturalInsight
            import uuid
            
            insight = ArchitecturalInsight(
                id=str(uuid.uuid4()),
                insight_id=f"{project_id}_cross_repo_analysis_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                insight_type='cross_repository_analysis',
                severity='medium',
                title=f'Cross-Repository Analysis Results for Project {project_id}',
                description=f'Comprehensive cross-repository analysis identifying {results["shared_libraries_found"]} shared libraries, {results["api_mappings_found"]} API mappings, and {results["database_relationships_found"]} database relationships',
                business_context=f'Multi-repository modernization project analysis',
                technical_details=json.dumps(results),
                repository_id=1,  # System insight
                commit_hash='cross_repo_analysis',
                discovered_by='CrossRepositoryDiscoveryService',
                discovery_method='automated_analysis',
                meta_data=json.dumps({'analysis_timestamp': datetime.utcnow().isoformat()})
            )
            
            session.add(insight)
            await session.commit()
            
        except Exception as e:
            self.logger.error(f"Error storing analysis results: {e}")


# Service factory
_cross_repository_discovery_service = None

async def get_cross_repository_discovery_service() -> CrossRepositoryDiscoveryService:
    """Get or create cross-repository discovery service instance"""
    global _cross_repository_discovery_service
    if _cross_repository_discovery_service is None:
        _cross_repository_discovery_service = CrossRepositoryDiscoveryService()
    return _cross_repository_discovery_service