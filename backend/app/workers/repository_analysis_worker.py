"""
Repository Analysis Worker for DocXP Enterprise
Background worker for comprehensive repository analysis and knowledge extraction
"""

import logging
import asyncio
import traceback
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
import tempfile
import shutil
import git
from pathlib import Path

from app.services.unified_flow_tracer import get_unified_flow_tracer
from app.services.parser_orchestrator import get_parser_orchestrator
from app.services.flow_validator import get_flow_validator
from app.services.knowledge_graph_service import get_knowledge_graph_service
from app.core.database import get_async_session
from app.models.business_rule_trace import BusinessRuleTrace, FlowStep
from app.models.architectural_insight import ArchitecturalInsight

logger = logging.getLogger(__name__)

async def analyze_repository(
    repository_id: str,
    project_id: str,
    analysis_type: str = "full",
    repository_url: Optional[str] = None,
    local_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main repository analysis worker function
    
    Args:
        repository_id: Unique repository identifier
        project_id: Parent project identifier
        analysis_type: Type of analysis (full, incremental, targeted)
        repository_url: Git repository URL (if cloning needed)
        local_path: Local path to repository (if already available)
    
    Returns:
        Analysis results dictionary
    """
    start_time = datetime.utcnow()
    logger.info(f"Starting {analysis_type} analysis for repository {repository_id}")
    
    analysis_results = {
        "repository_id": repository_id,
        "project_id": project_id,
        "analysis_type": analysis_type,
        "start_time": start_time.isoformat(),
        "status": "in_progress",
        "business_rules_discovered": 0,
        "insights_generated": 0,
        "files_analyzed": 0,
        "errors": [],
        "warnings": []
    }
    
    temp_dir = None
    
    try:
        # Step 1: Ensure repository is available locally
        if local_path and os.path.exists(local_path):
            repo_path = local_path
            logger.info(f"Using existing local repository at {repo_path}")
        elif repository_url:
            temp_dir = tempfile.mkdtemp(prefix=f"docxp_analysis_{repository_id}_")
            repo_path = await clone_repository(repository_url, temp_dir)
            logger.info(f"Cloned repository to {repo_path}")
        else:
            raise ValueError("Either repository_url or valid local_path must be provided")
        
        # Step 2: Initialize services
        flow_tracer = get_unified_flow_tracer()
        parser_orchestrator = get_parser_orchestrator()
        flow_validator = get_flow_validator()
        kg_service = await get_knowledge_graph_service()
        
        # Step 3: Repository-level analysis using parser orchestrator
        logger.info("Starting parser orchestration")
        parser_results = await parser_orchestrator.analyze_repository(repo_path)
        analysis_results["files_analyzed"] = sum(len(results) for results in parser_results.values())
        
        # Step 4: Business rule flow tracing
        logger.info("Starting business rule flow tracing")
        business_rules = []
        
        # Find entry points for flow tracing
        entry_points = await discover_entry_points(repo_path, parser_results)
        
        for entry_point in entry_points:
            try:
                rule_name = f"flow_from_{os.path.basename(entry_point)}"
                business_rule = await flow_tracer.trace_business_rule(
                    repository_path=repo_path,
                    entry_point=entry_point,
                    rule_name=rule_name,
                    business_domain="integration"  # Default, could be inferred
                )
                
                if business_rule:
                    # Step 5: Validate the traced flow
                    validation_result = await flow_validator.validate_flow(business_rule)
                    business_rule.extraction_confidence = validation_result.overall_confidence
                    
                    business_rules.append(business_rule)
                    logger.info(f"Successfully traced business rule: {rule_name}")
                    
            except Exception as e:
                error_msg = f"Failed to trace flow from {entry_point}: {str(e)}"
                logger.error(error_msg)
                analysis_results["errors"].append(error_msg)
        
        analysis_results["business_rules_discovered"] = len(business_rules)
        
        # Step 6: Store results in knowledge graph and database
        logger.info("Storing analysis results")
        await store_analysis_results(
            repository_id,
            project_id,
            business_rules,
            parser_results,
            kg_service
        )
        
        # Step 7: Generate architectural insights
        logger.info("Generating architectural insights")
        insights = await generate_insights(repo_path, business_rules, parser_results)
        analysis_results["insights_generated"] = len(insights)
        
        # Step 8: Update project progress
        await update_project_progress(project_id, repository_id, "completed")
        
        analysis_results["status"] = "completed"
        analysis_results["end_time"] = datetime.utcnow().isoformat()
        
        logger.info(f"Repository analysis completed for {repository_id}")
        return analysis_results
        
    except Exception as e:
        error_msg = f"Repository analysis failed: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        
        analysis_results["status"] = "failed"
        analysis_results["error"] = error_msg
        analysis_results["end_time"] = datetime.utcnow().isoformat()
        
        # Update project progress to reflect failure
        await update_project_progress(project_id, repository_id, "failed")
        
        return analysis_results
        
    finally:
        # Cleanup temporary directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temporary directory {temp_dir}: {e}")

async def clone_repository(repository_url: str, target_dir: str) -> str:
    """Clone repository to target directory"""
    try:
        repo = git.Repo.clone_from(repository_url, target_dir)
        logger.info(f"Successfully cloned {repository_url} to {target_dir}")
        return target_dir
    except Exception as e:
        logger.error(f"Failed to clone repository {repository_url}: {e}")
        raise

async def discover_entry_points(repo_path: str, parser_results: Dict[str, Any]) -> List[str]:
    """
    Discover entry points for business rule flow tracing
    
    Args:
        repo_path: Path to repository
        parser_results: Results from parser orchestrator
    
    Returns:
        List of entry point file paths
    """
    entry_points = []
    
    try:
        # Look for JSP pages (UI entry points)
        if "jsp" in parser_results:
            for jsp_result in parser_results["jsp"]:
                if jsp_result.get("file_path"):
                    entry_points.append(jsp_result["file_path"])
        
        # Look for Struts actions (controller entry points)
        if "struts" in parser_results:
            for struts_result in parser_results["struts"]:
                if struts_result.get("file_path"):
                    entry_points.append(struts_result["file_path"])
        
        # Look for REST API endpoints
        if "java" in parser_results:
            for java_result in parser_results["java"]:
                if java_result.get("annotations", {}).get("rest_endpoint"):
                    entry_points.append(java_result["file_path"])
        
        # Fallback: find main application entry points
        if not entry_points:
            main_files = []
            for root, dirs, files in os.walk(repo_path):
                for file in files:
                    if file.lower() in ["main.java", "application.java", "app.java"]:
                        main_files.append(os.path.join(root, file))
            entry_points.extend(main_files[:5])  # Limit to first 5
        
        logger.info(f"Discovered {len(entry_points)} entry points")
        return entry_points[:10]  # Limit to first 10 for performance
        
    except Exception as e:
        logger.error(f"Failed to discover entry points: {e}")
        return []

async def store_analysis_results(
    repository_id: str,
    project_id: str,
    business_rules: List[BusinessRuleTrace],
    parser_results: Dict[str, Any],
    kg_service
):
    """Store analysis results in database and knowledge graph"""
    try:
        async with get_async_session() as session:
            # Store business rule traces
            for business_rule in business_rules:
                session.add(business_rule)
            
            await session.commit()
            logger.info(f"Stored {len(business_rules)} business rule traces")
        
        # Store in knowledge graph
        await store_in_knowledge_graph(repository_id, business_rules, parser_results, kg_service)
        
    except Exception as e:
        logger.error(f"Failed to store analysis results: {e}")
        raise

async def store_in_knowledge_graph(
    repository_id: str,
    business_rules: List[BusinessRuleTrace],
    parser_results: Dict[str, Any],
    kg_service
):
    """Store analysis results in Neo4j knowledge graph"""
    try:
        from app.services.knowledge_graph_service import GraphNode, GraphRelationship, NodeType, RelationshipType
        
        # Create repository node
        repo_node = GraphNode(
            id=repository_id,
            node_type=NodeType.REPOSITORY,
            properties={
                "name": f"repository_{repository_id}",
                "analysis_date": datetime.utcnow().isoformat()
            }
        )
        await kg_service.create_node(repo_node)
        
        # Create business rule nodes and relationships
        for business_rule in business_rules:
            # Create business rule node
            rule_node = GraphNode(
                id=business_rule.trace_id,
                node_type=NodeType.BUSINESS_RULE,
                properties={
                    "name": business_rule.rule_name,
                    "domain": business_rule.business_domain,
                    "complexity": business_rule.flow_complexity,
                    "confidence": business_rule.extraction_confidence
                }
            )
            await kg_service.create_node(rule_node)
            
            # Create relationship to repository
            repo_relationship = GraphRelationship(
                source_id=business_rule.trace_id,
                target_id=repository_id,
                relationship_type=RelationshipType.BELONGS_TO
            )
            await kg_service.create_relationship(repo_relationship)
            
            # Create flow step nodes and relationships
            for flow_step in business_rule.flow_steps:
                step_node = GraphNode(
                    id=f"{business_rule.trace_id}_{flow_step.step_order}",
                    node_type=NodeType.CODE_ENTITY,
                    properties={
                        "component_name": flow_step.component_name,
                        "technology": flow_step.technology,
                        "file_path": flow_step.file_path,
                        "business_logic": flow_step.business_logic
                    }
                )
                await kg_service.create_node(step_node)
                
                # Create flow relationship
                flow_relationship = GraphRelationship(
                    source_id=business_rule.trace_id,
                    target_id=f"{business_rule.trace_id}_{flow_step.step_order}",
                    relationship_type=RelationshipType.CONTAINS
                )
                await kg_service.create_relationship(flow_relationship)
        
        logger.info(f"Stored {len(business_rules)} business rules in knowledge graph")
        
    except Exception as e:
        logger.error(f"Failed to store in knowledge graph: {e}")
        raise

async def generate_insights(
    repo_path: str,
    business_rules: List[BusinessRuleTrace],
    parser_results: Dict[str, Any]
) -> List[ArchitecturalInsight]:
    """Generate architectural insights from analysis results"""
    insights = []
    
    try:
        # Insight 1: Technology diversity analysis
        technologies = set()
        for business_rule in business_rules:
            technologies.update(business_rule.technology_stack)
        
        if len(technologies) > 5:
            insight = ArchitecturalInsight(
                insight_id=f"tech_diversity_{len(technologies)}",
                insight_type="complexity",
                severity="medium",
                title="High Technology Diversity",
                description=f"Repository uses {len(technologies)} different technologies: {', '.join(technologies)}",
                modernization_impact="moderate_change",
                modernization_priority=60,
                repository_id=1,  # This would be the actual repository DB ID
                commit_hash="HEAD",
                discovered_by="repository_analysis_worker"
            )
            insights.append(insight)
        
        # Insight 2: Flow complexity analysis
        complex_flows = [br for br in business_rules if br.flow_complexity > 7.0]
        if complex_flows:
            insight = ArchitecturalInsight(
                insight_id=f"complex_flows_{len(complex_flows)}",
                insight_type="performance",
                severity="high",
                title="Complex Business Rule Flows Detected",
                description=f"Found {len(complex_flows)} business rule flows with high complexity",
                modernization_impact="breaking_change",
                modernization_priority=80,
                repository_id=1,
                commit_hash="HEAD",
                discovered_by="repository_analysis_worker"
            )
            insights.append(insight)
        
        logger.info(f"Generated {len(insights)} architectural insights")
        return insights
        
    except Exception as e:
        logger.error(f"Failed to generate insights: {e}")
        return []

async def update_project_progress(project_id: str, repository_id: str, status: str):
    """Update project progress for repository analysis completion"""
    try:
        async with get_async_session() as session:
            # This would update the ProjectRepository table
            # Implementation depends on the exact schema
            logger.info(f"Updated project {project_id} repository {repository_id} status to {status}")
            
    except Exception as e:
        logger.error(f"Failed to update project progress: {e}")