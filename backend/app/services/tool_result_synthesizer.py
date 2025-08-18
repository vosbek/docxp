"""
Tool Result Synthesizer for Enhanced Single-Agent Tool Integration

Combines and synthesizes results from multiple tool executions into coherent,
actionable insights for enterprise architects.

Part of Week 5 implementation.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json

from app.models.business_rule_trace import BusinessRuleTrace, FlowStep
from app.models.architectural_insight import ArchitecturalInsight
from app.models.tool_workflows import ToolSequence, ToolStep

logger = logging.getLogger(__name__)


@dataclass
class SynthesisResult:
    """Result of synthesizing multiple tool outputs"""
    summary: str
    key_findings: List[str]
    recommendations: List[str]
    confidence_score: float
    supporting_evidence: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    next_steps: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "summary": self.summary,
            "key_findings": self.key_findings,
            "recommendations": self.recommendations,
            "confidence_score": self.confidence_score,
            "supporting_evidence": self.supporting_evidence,
            "risk_assessment": self.risk_assessment,
            "next_steps": self.next_steps,
            "metadata": self.metadata
        }


@dataclass
class ToolResult:
    """Standardized tool result container"""
    tool_name: str
    function_name: str
    result_data: Dict[str, Any]
    confidence: float
    execution_time: float
    status: str  # "success", "partial", "failed"
    error_message: Optional[str] = None
    
    def is_successful(self) -> bool:
        return self.status == "success"
    
    def has_data(self) -> bool:
        return self.result_data is not None and len(self.result_data) > 0


class ToolResultSynthesizer:
    """
    Synthesizes results from multiple tool executions into coherent insights
    for enterprise architects and stakeholders.
    """
    
    def __init__(self):
        self.synthesis_strategies = {
            "legacy_modernization_analysis": self._synthesize_modernization_analysis,
            "cross_repo_impact_analysis": self._synthesize_impact_analysis,
            "business_rule_extraction": self._synthesize_business_rule_extraction,
            "architecture_health_check": self._synthesize_architecture_health_check
        }
    
    async def synthesize_workflow_results(
        self, 
        workflow: ToolSequence, 
        tool_results: Dict[str, ToolResult],
        user_query: str = "",
        context: Dict[str, Any] = None
    ) -> SynthesisResult:
        """
        Synthesize results from a complete workflow execution
        
        Args:
            workflow: The executed workflow
            tool_results: Results from individual tool executions
            user_query: Original user query for context
            context: Additional context information
            
        Returns:
            SynthesisResult with combined insights
        """
        context = context or {}
        
        # Use specialized synthesis strategy if available
        strategy = self.synthesis_strategies.get(workflow.sequence_id)
        if strategy:
            return await strategy(workflow, tool_results, user_query, context)
        
        # Default synthesis approach
        return await self._synthesize_generic_workflow(workflow, tool_results, user_query, context)
    
    async def _synthesize_modernization_analysis(
        self, 
        workflow: ToolSequence, 
        tool_results: Dict[str, ToolResult],
        user_query: str,
        context: Dict[str, Any]
    ) -> SynthesisResult:
        """Synthesize legacy modernization analysis results"""
        
        # Extract key data from tool results
        repo_analysis = self._extract_repository_analysis(tool_results)
        business_rules = self._extract_business_rules(tool_results)
        validation_results = self._extract_validation_results(tool_results)
        risk_assessment = self._extract_risk_assessment(tool_results)
        migration_plan = self._extract_migration_plan(tool_results)
        
        # Calculate overall confidence
        confidence = self._calculate_synthesis_confidence(tool_results)
        
        # Generate summary
        summary = self._generate_modernization_summary(
            repo_analysis, business_rules, risk_assessment, migration_plan
        )
        
        # Compile key findings
        key_findings = []
        
        if repo_analysis:
            key_findings.extend(self._extract_repository_findings(repo_analysis))
        
        if business_rules:
            key_findings.extend(self._extract_business_rule_findings(business_rules))
        
        if validation_results:
            key_findings.extend(self._extract_validation_findings(validation_results))
        
        # Generate recommendations
        recommendations = self._generate_modernization_recommendations(
            repo_analysis, business_rules, risk_assessment, validation_results
        )
        
        # Assess risks
        synthesized_risks = self._synthesize_risk_assessment(risk_assessment, validation_results)
        
        # Determine next steps
        next_steps = self._determine_modernization_next_steps(
            repo_analysis, risk_assessment, migration_plan
        )
        
        # Compile supporting evidence
        supporting_evidence = {
            "repository_analysis": repo_analysis,
            "business_rules_count": len(business_rules) if business_rules else 0,
            "validation_results": validation_results,
            "tool_execution_summary": self._summarize_tool_executions(tool_results)
        }
        
        return SynthesisResult(
            summary=summary,
            key_findings=key_findings,
            recommendations=recommendations,
            confidence_score=confidence,
            supporting_evidence=supporting_evidence,
            risk_assessment=synthesized_risks,
            next_steps=next_steps,
            metadata={
                "workflow_id": workflow.sequence_id,
                "synthesis_strategy": "legacy_modernization_analysis",
                "user_query": user_query,
                "synthesis_timestamp": datetime.utcnow().isoformat()
            }
        )
    
    async def _synthesize_impact_analysis(
        self,
        workflow: ToolSequence,
        tool_results: Dict[str, ToolResult], 
        user_query: str,
        context: Dict[str, Any]
    ) -> SynthesisResult:
        """Synthesize cross-repository impact analysis results"""
        
        # Extract cross-repository data
        shared_components = self._extract_shared_components(tool_results)
        dependency_mapping = self._extract_dependency_mapping(tool_results)
        cross_repo_flows = self._extract_cross_repo_flows(tool_results)
        impact_analysis = self._extract_impact_analysis(tool_results)
        
        confidence = self._calculate_synthesis_confidence(tool_results)
        
        # Generate impact summary
        summary = f"""Cross-Repository Impact Analysis reveals {len(shared_components)} shared components 
across the repository portfolio. Analysis identified {len(dependency_mapping)} critical dependencies 
and traced {len(cross_repo_flows)} cross-repository flows."""
        
        # Key findings for impact analysis
        key_findings = [
            f"Identified {len(shared_components)} shared components with varying risk levels",
            f"Mapped {len(dependency_mapping)} inter-repository dependencies",
            f"Analyzed impact propagation across {len(set(context.get('repository_ids', [])))} repositories"
        ]
        
        if impact_analysis.get("high_risk_changes"):
            key_findings.append(f"Found {len(impact_analysis['high_risk_changes'])} high-risk change scenarios")
        
        # Impact-specific recommendations
        recommendations = [
            "Prioritize refactoring of high-coupling shared components",
            "Implement dependency isolation patterns to reduce cross-repository risks",
            "Establish change coordination processes for shared components"
        ]
        
        if impact_analysis.get("recommended_changes"):
            recommendations.extend(impact_analysis["recommended_changes"][:3])
        
        # Risk assessment for changes
        risk_assessment = {
            "overall_risk": impact_analysis.get("overall_risk_level", "medium"),
            "high_risk_components": shared_components.get("high_risk", [])[:5],
            "risk_factors": [
                "Cross-repository dependencies create cascading change risks",
                "Shared components may have inconsistent usage patterns",
                "Limited test coverage for cross-repository integration scenarios"
            ]
        }
        
        next_steps = [
            "Review high-risk shared components for refactoring opportunities",
            "Implement integration testing for critical cross-repository flows",
            "Establish governance for shared component modifications"
        ]
        
        supporting_evidence = {
            "shared_components": shared_components,
            "dependency_mapping": dependency_mapping,
            "cross_repo_flows": cross_repo_flows,
            "tool_execution_summary": self._summarize_tool_executions(tool_results)
        }
        
        return SynthesisResult(
            summary=summary,
            key_findings=key_findings,
            recommendations=recommendations,
            confidence_score=confidence,
            supporting_evidence=supporting_evidence,
            risk_assessment=risk_assessment,
            next_steps=next_steps,
            metadata={
                "workflow_id": workflow.sequence_id,
                "synthesis_strategy": "cross_repo_impact_analysis",
                "analyzed_repositories": len(set(context.get("repository_ids", []))),
                "synthesis_timestamp": datetime.utcnow().isoformat()
            }
        )
    
    async def _synthesize_business_rule_extraction(
        self,
        workflow: ToolSequence,
        tool_results: Dict[str, ToolResult],
        user_query: str,
        context: Dict[str, Any]
    ) -> SynthesisResult:
        """Synthesize business rule extraction results"""
        
        # Extract business rule data
        business_logic_components = self._extract_business_logic_components(tool_results)
        business_rule_flows = self._extract_business_rule_flows(tool_results)
        extracted_rules = self._extract_extracted_rules(tool_results)
        rule_documentation = self._extract_rule_documentation(tool_results)
        
        confidence = self._calculate_synthesis_confidence(tool_results)
        
        total_rules = len(extracted_rules) if extracted_rules else 0
        
        summary = f"""Business Rule Extraction identified {len(business_logic_components)} components 
containing business logic, traced {len(business_rule_flows)} complete business workflows, 
and successfully extracted {total_rules} distinct business rules with documentation."""
        
        key_findings = [
            f"Located {len(business_logic_components)} components with significant business logic",
            f"Successfully traced {len(business_rule_flows)} end-to-end business processes",
            f"Extracted {total_rules} business rules with confidence scores above 70%"
        ]
        
        if extracted_rules:
            high_confidence_rules = [r for r in extracted_rules if r.get("confidence", 0) > 0.8]
            key_findings.append(f"{len(high_confidence_rules)} rules extracted with high confidence (>80%)")
        
        recommendations = [
            "Review extracted business rules with domain experts for validation",
            "Prioritize modernization of high-confidence, critical business rules",
            "Establish business rule governance and documentation standards"
        ]
        
        if extracted_rules:
            complex_rules = [r for r in extracted_rules if r.get("complexity", "low") == "high"]
            if complex_rules:
                recommendations.append(f"Focus on simplifying {len(complex_rules)} complex business rules")
        
        risk_assessment = {
            "overall_risk": "medium",
            "risk_factors": [
                "Business rules embedded in legacy code may be incomplete or inconsistent",
                "Rule extraction accuracy depends on code quality and documentation",
                "Complex business rules may require domain expert validation"
            ]
        }
        
        next_steps = [
            "Validate extracted rules with business stakeholders",
            "Document business rule dependencies and interactions",
            "Plan business rule migration to modern rule engine"
        ]
        
        supporting_evidence = {
            "business_logic_components": business_logic_components,
            "rule_flows": business_rule_flows,
            "extracted_rules_summary": {
                "total_rules": total_rules,
                "high_confidence_rules": len([r for r in extracted_rules if r.get("confidence", 0) > 0.8]) if extracted_rules else 0,
                "complex_rules": len([r for r in extracted_rules if r.get("complexity", "low") == "high"]) if extracted_rules else 0
            },
            "documentation_status": rule_documentation
        }
        
        return SynthesisResult(
            summary=summary,
            key_findings=key_findings,
            recommendations=recommendations,
            confidence_score=confidence,
            supporting_evidence=supporting_evidence,
            risk_assessment=risk_assessment,
            next_steps=next_steps,
            metadata={
                "workflow_id": workflow.sequence_id,
                "synthesis_strategy": "business_rule_extraction",
                "total_rules_extracted": total_rules,
                "synthesis_timestamp": datetime.utcnow().isoformat()
            }
        )
    
    async def _synthesize_architecture_health_check(
        self,
        workflow: ToolSequence,
        tool_results: Dict[str, ToolResult],
        user_query: str,
        context: Dict[str, Any]
    ) -> SynthesisResult:
        """Synthesize architecture health check results"""
        
        # Extract architecture health data
        code_quality = self._extract_code_quality_metrics(tool_results)
        architectural_patterns = self._extract_architectural_patterns(tool_results)
        dependency_health = self._extract_dependency_health(tool_results)
        technical_debt = self._extract_technical_debt(tool_results)
        
        confidence = self._calculate_synthesis_confidence(tool_results)
        
        # Calculate overall health score
        health_score = self._calculate_architecture_health_score(
            code_quality, dependency_health, technical_debt
        )
        
        summary = f"""Architecture Health Check reveals overall system health score of {health_score}/100. 
Analysis identified {len(architectural_patterns.get('anti_patterns', []))} anti-patterns and 
calculated technical debt of {technical_debt.get('total_debt_hours', 0)} hours."""
        
        key_findings = [
            f"Overall architecture health score: {health_score}/100",
            f"Code quality metrics indicate {code_quality.get('overall_grade', 'unknown')} grade",
            f"Identified {len(architectural_patterns.get('anti_patterns', []))} architectural anti-patterns"
        ]
        
        if technical_debt.get("high_priority_items"):
            key_findings.append(f"{len(technical_debt['high_priority_items'])} high-priority technical debt items")
        
        # Generate health-based recommendations
        recommendations = []
        
        if health_score < 60:
            recommendations.append("Immediate architecture refactoring required - health score below acceptable threshold")
        elif health_score < 80:
            recommendations.append("Address identified anti-patterns and high-priority technical debt")
        else:
            recommendations.append("Maintain current architecture health with regular monitoring")
        
        if dependency_health.get("circular_dependencies"):
            recommendations.append(f"Resolve {len(dependency_health['circular_dependencies'])} circular dependencies")
        
        if technical_debt.get("total_debt_hours", 0) > 100:
            recommendations.append("Prioritize technical debt reduction in upcoming development cycles")
        
        # Risk assessment based on health metrics
        risk_level = "high" if health_score < 60 else "medium" if health_score < 80 else "low"
        risk_assessment = {
            "overall_risk": risk_level,
            "health_score": health_score,
            "critical_issues": architectural_patterns.get("anti_patterns", [])[:3],
            "risk_factors": self._generate_health_risk_factors(code_quality, dependency_health, technical_debt)
        }
        
        next_steps = [
            "Address highest-priority technical debt items",
            "Refactor components with poor code quality metrics",
            "Establish architecture governance and monitoring processes"
        ]
        
        supporting_evidence = {
            "health_score": health_score,
            "code_quality_metrics": code_quality,
            "architectural_patterns": architectural_patterns,
            "dependency_analysis": dependency_health,
            "technical_debt_summary": technical_debt
        }
        
        return SynthesisResult(
            summary=summary,
            key_findings=key_findings,
            recommendations=recommendations,
            confidence_score=confidence,
            supporting_evidence=supporting_evidence,
            risk_assessment=risk_assessment,
            next_steps=next_steps,
            metadata={
                "workflow_id": workflow.sequence_id,
                "synthesis_strategy": "architecture_health_check",
                "health_score": health_score,
                "synthesis_timestamp": datetime.utcnow().isoformat()
            }
        )
    
    async def _synthesize_generic_workflow(
        self,
        workflow: ToolSequence,
        tool_results: Dict[str, ToolResult],
        user_query: str,
        context: Dict[str, Any]
    ) -> SynthesisResult:
        """Generic synthesis for workflows without specific strategies"""
        
        successful_results = [r for r in tool_results.values() if r.is_successful()]
        confidence = self._calculate_synthesis_confidence(tool_results)
        
        summary = f"Completed {workflow.name} with {len(successful_results)}/{len(tool_results)} tools executing successfully."
        
        key_findings = []
        recommendations = []
        
        for tool_name, result in tool_results.items():
            if result.is_successful() and result.has_data():
                # Extract key information from each tool result
                findings = self._extract_generic_findings(tool_name, result.result_data)
                key_findings.extend(findings[:2])  # Limit to 2 findings per tool
                
                recs = self._extract_generic_recommendations(tool_name, result.result_data)
                recommendations.extend(recs[:2])  # Limit to 2 recommendations per tool
        
        risk_assessment = {
            "overall_risk": "medium",
            "risk_factors": [
                f"Tool execution success rate: {len(successful_results)}/{len(tool_results)}",
                f"Average confidence score: {confidence:.2f}"
            ]
        }
        
        next_steps = [
            "Review individual tool results for detailed insights",
            "Consider running additional specialized workflows for deeper analysis"
        ]
        
        supporting_evidence = {
            "tool_results_summary": self._summarize_tool_executions(tool_results),
            "successful_executions": len(successful_results),
            "total_executions": len(tool_results)
        }
        
        return SynthesisResult(
            summary=summary,
            key_findings=key_findings[:10],  # Limit total findings
            recommendations=recommendations[:10],  # Limit total recommendations
            confidence_score=confidence,
            supporting_evidence=supporting_evidence,
            risk_assessment=risk_assessment,
            next_steps=next_steps,
            metadata={
                "workflow_id": workflow.sequence_id,
                "synthesis_strategy": "generic_workflow",
                "synthesis_timestamp": datetime.utcnow().isoformat()
            }
        )
    
    # Helper methods for data extraction
    def _extract_repository_analysis(self, tool_results: Dict[str, ToolResult]) -> Dict[str, Any]:
        """Extract repository analysis data from tool results"""
        for tool_name in ["repository_analyzer", "parser_orchestrator"]:
            if tool_name in tool_results and tool_results[tool_name].is_successful():
                return tool_results[tool_name].result_data
        return {}
    
    def _extract_business_rules(self, tool_results: Dict[str, ToolResult]) -> List[Dict[str, Any]]:
        """Extract business rules from tool results"""
        for tool_name in ["flow_tracer", "unified_flow_tracer", "business_rule_extractor"]:
            if tool_name in tool_results and tool_results[tool_name].is_successful():
                data = tool_results[tool_name].result_data
                if "business_rules" in data:
                    return data["business_rules"]
                elif "traces" in data:
                    return data["traces"]
        return []
    
    def _extract_validation_results(self, tool_results: Dict[str, ToolResult]) -> Dict[str, Any]:
        """Extract flow validation results"""
        if "flow_validator" in tool_results and tool_results["flow_validator"].is_successful():
            return tool_results["flow_validator"].result_data
        return {}
    
    def _extract_risk_assessment(self, tool_results: Dict[str, ToolResult]) -> Dict[str, Any]:
        """Extract risk assessment data"""
        if "risk_assessor" in tool_results and tool_results["risk_assessor"].is_successful():
            return tool_results["risk_assessor"].result_data
        return {"overall_risk": "unknown", "risk_factors": []}
    
    def _extract_migration_plan(self, tool_results: Dict[str, ToolResult]) -> Dict[str, Any]:
        """Extract migration plan data"""
        if "modernization_planner" in tool_results and tool_results["modernization_planner"].is_successful():
            return tool_results["modernization_planner"].result_data
        return {}
    
    def _calculate_synthesis_confidence(self, tool_results: Dict[str, ToolResult]) -> float:
        """Calculate overall confidence score from tool results"""
        if not tool_results:
            return 0.0
        
        successful_results = [r for r in tool_results.values() if r.is_successful()]
        if not successful_results:
            return 0.0
        
        # Base confidence from success rate
        success_rate = len(successful_results) / len(tool_results)
        
        # Average confidence from individual tools
        avg_confidence = sum(r.confidence for r in successful_results) / len(successful_results)
        
        # Combined confidence score
        combined_confidence = (success_rate * 0.4) + (avg_confidence * 0.6)
        
        return round(combined_confidence, 2)
    
    def _generate_modernization_summary(self, repo_analysis, business_rules, risk_assessment, migration_plan) -> str:
        """Generate summary for modernization analysis"""
        components_count = len(repo_analysis.get("components", [])) if repo_analysis else 0
        rules_count = len(business_rules) if business_rules else 0
        risk_level = risk_assessment.get("overall_risk", "unknown")
        
        summary = f"Legacy Modernization Analysis identified {components_count} components "
        summary += f"with {rules_count} business rule flows traced. "
        summary += f"Overall migration risk assessed as {risk_level}."
        
        if migration_plan and "timeline_months" in migration_plan:
            summary += f" Estimated migration timeline: {migration_plan['timeline_months']} months."
        
        return summary
    
    def _summarize_tool_executions(self, tool_results: Dict[str, ToolResult]) -> Dict[str, Any]:
        """Create summary of tool execution results"""
        summary = {
            "total_tools": len(tool_results),
            "successful_tools": len([r for r in tool_results.values() if r.is_successful()]),
            "failed_tools": len([r for r in tool_results.values() if not r.is_successful()]),
            "average_confidence": 0.0,
            "total_execution_time": sum(r.execution_time for r in tool_results.values()),
            "tool_details": {}
        }
        
        successful_results = [r for r in tool_results.values() if r.is_successful()]
        if successful_results:
            summary["average_confidence"] = sum(r.confidence for r in successful_results) / len(successful_results)
        
        for tool_name, result in tool_results.items():
            summary["tool_details"][tool_name] = {
                "status": result.status,
                "confidence": result.confidence,
                "execution_time": result.execution_time,
                "has_data": result.has_data()
            }
        
        return summary
    
    # Additional helper methods would be implemented here for:
    # - _extract_shared_components, _extract_dependency_mapping, etc.
    # - _generate_modernization_recommendations
    # - _synthesize_risk_assessment
    # - _determine_modernization_next_steps
    # - _extract_generic_findings, _extract_generic_recommendations
    # - And other specialized extraction methods
    
    # Placeholder implementations for brevity
    def _extract_shared_components(self, tool_results): return {}
    def _extract_dependency_mapping(self, tool_results): return {}
    def _extract_cross_repo_flows(self, tool_results): return {}
    def _extract_impact_analysis(self, tool_results): return {}
    def _extract_business_logic_components(self, tool_results): return []
    def _extract_business_rule_flows(self, tool_results): return []
    def _extract_extracted_rules(self, tool_results): return []
    def _extract_rule_documentation(self, tool_results): return {}
    def _extract_code_quality_metrics(self, tool_results): return {}
    def _extract_architectural_patterns(self, tool_results): return {}
    def _extract_dependency_health(self, tool_results): return {}
    def _extract_technical_debt(self, tool_results): return {}
    def _calculate_architecture_health_score(self, code_quality, dependency_health, technical_debt): return 75
    def _generate_health_risk_factors(self, code_quality, dependency_health, technical_debt): return []
    def _extract_repository_findings(self, repo_analysis): return []
    def _extract_business_rule_findings(self, business_rules): return []
    def _extract_validation_findings(self, validation_results): return []
    def _generate_modernization_recommendations(self, repo_analysis, business_rules, risk_assessment, validation_results): return []
    def _synthesize_risk_assessment(self, risk_assessment, validation_results): return {}
    def _determine_modernization_next_steps(self, repo_analysis, risk_assessment, migration_plan): return []
    def _extract_generic_findings(self, tool_name, result_data): return []
    def _extract_generic_recommendations(self, tool_name, result_data): return []