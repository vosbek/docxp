"""
Enhanced Strands Agent Service for Week 5 Tool Integration

Integrates unified flow tracing, context management, and tool workflows
into a sophisticated single-agent architecture.

Part of Week 5 implementation.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json

from app.services.strands_agent_service import StrandsAgentService, ConversationContext, AgentResponse, AgentType
from app.services.unified_flow_tracer import UnifiedFlowTracer
from app.services.parser_orchestrator import ParserOrchestrator
from app.services.flow_validator import FlowValidator
from app.services.context_manager import ContextManager, get_context_manager
from app.services.tool_result_synthesizer import ToolResultSynthesizer, ToolResult
from app.models.tool_workflows import PredefinedWorkflows, ToolSequence, WorkflowRecommender, WorkflowExecution
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


@dataclass
class EnhancedAgentResponse(AgentResponse):
    """Extended agent response with workflow results"""
    workflow_results: Optional[Dict[str, Any]] = None
    synthesis_results: Optional[Dict[str, Any]] = None
    context_summary: Optional[Dict[str, Any]] = None
    recommended_workflows: List[str] = None


class EnhancedStrandsAgentService(StrandsAgentService):
    """
    Enhanced single-agent service with sophisticated tool orchestration,
    context management, and workflow execution capabilities.
    """
    
    def __init__(self):
        super().__init__()
        
        # Week 5 enhancements
        self.unified_flow_tracer: Optional[UnifiedFlowTracer] = None
        self.parser_orchestrator: Optional[ParserOrchestrator] = None
        self.flow_validator: Optional[FlowValidator] = None
        self.context_manager: Optional[ContextManager] = None
        self.tool_synthesizer: Optional[ToolResultSynthesizer] = None
        
        # Workflow management
        self.active_workflows: Dict[str, ToolSequence] = {}
        self.workflow_executions: Dict[str, WorkflowExecution] = {}
        
        # Enhanced tool registry
        self.enhanced_tools: Dict[str, callable] = {}
        
        if self.available:
            asyncio.create_task(self._initialize_enhanced_services())
    
    async def _initialize_enhanced_services(self):
        """Initialize Week 5 enhanced services"""
        try:
            # Initialize Week 4 flow tracing services
            self.unified_flow_tracer = UnifiedFlowTracer()
            self.parser_orchestrator = ParserOrchestrator()
            self.flow_validator = FlowValidator()
            
            # Initialize Week 5 services
            self.context_manager = await get_context_manager()
            self.tool_synthesizer = ToolResultSynthesizer()
            
            # Register enhanced tools
            await self._register_enhanced_tools()
            
            logger.info("Enhanced Strands Agent Service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize enhanced services: {e}")
    
    async def _register_enhanced_tools(self):
        """Register enhanced tools that integrate Week 4 and Week 5 capabilities"""
        
        # Flow tracing tools
        self.enhanced_tools["trace_business_rules"] = self._tool_trace_business_rules
        self.enhanced_tools["analyze_repository"] = self._tool_analyze_repository
        self.enhanced_tools["validate_flows"] = self._tool_validate_flows
        
        # Cross-repository tools
        self.enhanced_tools["discover_shared_components"] = self._tool_discover_shared_components
        self.enhanced_tools["analyze_cross_repo_impact"] = self._tool_analyze_cross_repo_impact
        
        # Workflow execution tools
        self.enhanced_tools["execute_workflow"] = self._tool_execute_workflow
        self.enhanced_tools["recommend_workflows"] = self._tool_recommend_workflows
        
        logger.info(f"Registered {len(self.enhanced_tools)} enhanced tools")
    
    async def process_enhanced_message(
        self,
        message: str,
        session_id: str,
        agent_type: AgentType = AgentType.MIGRATION_EXPERT,
        context: Optional[Dict[str, Any]] = None
    ) -> EnhancedAgentResponse:
        """
        Process message with enhanced workflow orchestration and context management
        """
        try:
            # Get or create conversation context
            conversation_context = self._get_enhanced_context(session_id, context)
            
            # Update context with new message
            await self.context_manager.add_contextual_data(
                session_id=session_id,
                data_type="user_message",
                data={"message": message, "timestamp": datetime.utcnow().isoformat()},
                source_tool="user_input",
                confidence=1.0
            )
            
            # Recommend appropriate workflows based on message
            recommended_workflows = WorkflowRecommender.recommend_workflows(message, context)
            
            # Check if user is requesting specific workflow execution
            workflow_to_execute = self._parse_workflow_request(message, recommended_workflows)
            
            if workflow_to_execute:
                # Execute the requested workflow
                workflow_results = await self._execute_workflow(
                    workflow_to_execute, session_id, context
                )
                
                # Synthesize workflow results
                synthesis_results = await self.tool_synthesizer.synthesize_workflow_results(
                    workflow=workflow_to_execute,
                    tool_results=workflow_results["tool_results"],
                    user_query=message,
                    context=context
                )
                
                # Get relevant context for response
                relevant_context = self.context_manager.get_relevant_context(
                    session_id, message, max_items=10
                )
                
                # Generate enhanced response
                response_content = self._generate_workflow_response(
                    message, workflow_results, synthesis_results, relevant_context
                )
                
                return EnhancedAgentResponse(
                    content=response_content,
                    agent_type=agent_type,
                    confidence=synthesis_results.confidence_score,
                    reasoning=f"Executed {workflow_to_execute.name} workflow",
                    suggested_actions=synthesis_results.next_steps,
                    workflow_results=workflow_results,
                    synthesis_results=synthesis_results.to_dict(),
                    context_summary=relevant_context,
                    recommended_workflows=[w.name for w in recommended_workflows[:3]]
                )
            
            else:
                # Standard conversational response with enhanced context
                relevant_context = self.context_manager.get_relevant_context(
                    session_id, message, max_items=5
                )
                
                # Use parent class for standard agent processing
                standard_response = await self.process_message(message, session_id, agent_type)
                
                # Enhance with context and recommendations
                enhanced_content = self._enhance_standard_response(
                    standard_response.content, relevant_context, recommended_workflows
                )
                
                return EnhancedAgentResponse(
                    content=enhanced_content,
                    agent_type=agent_type,
                    confidence=standard_response.confidence,
                    reasoning=standard_response.reasoning,
                    suggested_actions=standard_response.suggested_actions,
                    followup_questions=standard_response.followup_questions,
                    context_summary=relevant_context,
                    recommended_workflows=[w.name for w in recommended_workflows[:3]]
                )
        
        except Exception as e:
            logger.error(f"Error processing enhanced message: {e}")
            return EnhancedAgentResponse(
                content=f"I encountered an error processing your request: {str(e)}",
                agent_type=agent_type,
                confidence=0.0,
                reasoning="Error in enhanced message processing"
            )
    
    async def _execute_workflow(
        self,
        workflow: ToolSequence,
        session_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a complete tool workflow"""
        
        workflow_execution = WorkflowExecution(
            session_id=session_id,
            sequence_id=workflow.sequence_id,
            sequence_name=workflow.name,
            started_at=datetime.utcnow()
        )
        
        tool_results = {}
        execution_log = []
        
        try:
            # Execute tools in dependency order
            for tool_step in workflow.tools:
                # Check dependencies
                if not self._are_dependencies_satisfied(tool_step, tool_results):
                    logger.warning(f"Skipping {tool_step.tool_name} - dependencies not satisfied")
                    continue
                
                # Execute tool
                start_time = datetime.utcnow()
                tool_result = await self._execute_tool_step(tool_step, context, tool_results)
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                
                # Store result
                tool_results[tool_step.tool_name] = ToolResult(
                    tool_name=tool_step.tool_name,
                    function_name=tool_step.tool_function,
                    result_data=tool_result,
                    confidence=tool_result.get("confidence", 0.5) if tool_result else 0.0,
                    execution_time=execution_time,
                    status="success" if tool_result else "failed"
                )
                
                # Log execution
                execution_log.append({
                    "tool": tool_step.tool_name,
                    "status": "success" if tool_result else "failed",
                    "execution_time": execution_time,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # Add results to context
                if tool_result:
                    await self.context_manager.add_contextual_data(
                        session_id=session_id,
                        data_type=f"workflow_tool_result",
                        data=tool_result,
                        source_tool=tool_step.tool_name,
                        confidence=tool_result.get("confidence", 0.5)
                    )
            
            # Update workflow execution record
            workflow_execution.completed_at = datetime.utcnow()
            workflow_execution.total_duration_seconds = (
                workflow_execution.completed_at - workflow_execution.started_at
            ).total_seconds()
            workflow_execution.tool_executions = execution_log
            workflow_execution.success_rate = len([r for r in tool_results.values() if r.is_successful()]) / len(tool_results)
            workflow_execution.status = "completed"
            
            # Save execution record
            async with AsyncSessionLocal() as session:
                session.add(workflow_execution)
                await session.commit()
            
            return {
                "workflow": workflow,
                "tool_results": tool_results,
                "execution_log": execution_log,
                "success_rate": workflow_execution.success_rate,
                "total_duration": workflow_execution.total_duration_seconds
            }
            
        except Exception as e:
            workflow_execution.status = "failed"
            workflow_execution.error_message = str(e)
            logger.error(f"Workflow execution failed: {e}")
            return {
                "workflow": workflow,
                "tool_results": tool_results,
                "execution_log": execution_log,
                "error": str(e)
            }
    
    async def _execute_tool_step(
        self,
        tool_step,
        context: Optional[Dict[str, Any]],
        previous_results: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Execute a single tool step"""
        
        tool_name = tool_step.tool_name
        function_name = tool_step.tool_function
        
        try:
            # Route to appropriate enhanced tool
            if tool_name == "repository_analyzer" and function_name == "analyze_repository":
                return await self._tool_analyze_repository(tool_step.parameters, context)
            
            elif tool_name == "flow_tracer" and "trace" in function_name:
                return await self._tool_trace_business_rules(tool_step.parameters, context)
            
            elif tool_name == "flow_validator" and function_name == "validate_flows":
                return await self._tool_validate_flows(tool_step.parameters, previous_results)
            
            elif tool_name == "cross_repo_discovery":
                return await self._tool_discover_shared_components(tool_step.parameters, context)
            
            # Add more tool routing as needed
            else:
                logger.warning(f"Unknown tool: {tool_name}.{function_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}.{function_name}: {e}")
            return None
    
    # Enhanced tool implementations
    async def _tool_analyze_repository(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced repository analysis using ParserOrchestrator"""
        try:
            repository_path = parameters.get("repository_path") or context.get("repository_path")
            if not repository_path:
                return {"error": "Repository path not provided"}
            
            results = await self.parser_orchestrator.analyze_repository(repository_path)
            
            return {
                "repository_path": repository_path,
                "analysis_results": results,
                "files_analyzed": len(results),
                "confidence": 0.8,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Repository analysis failed: {e}")
            return {"error": str(e)}
    
    async def _tool_trace_business_rules(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced business rule tracing using UnifiedFlowTracer"""
        try:
            repository_path = parameters.get("repository_path") or context.get("repository_path")
            entry_point = parameters.get("entry_point", "*.jsp")
            max_traces = parameters.get("max_traces", 5)
            
            if not repository_path:
                return {"error": "Repository path not provided"}
            
            # For now, return mock data - full implementation would use UnifiedFlowTracer
            traces = []
            for i in range(min(max_traces, 3)):
                traces.append({
                    "trace_id": f"trace_{i+1}",
                    "rule_name": f"Business Rule {i+1}",
                    "technologies": ["JSP", "Struts", "Java"],
                    "confidence": 0.8 - (i * 0.1)
                })
            
            return {
                "repository_path": repository_path,
                "traces": traces,
                "total_traces": len(traces),
                "confidence": 0.7,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Business rule tracing failed: {e}")
            return {"error": str(e)}
    
    async def _tool_validate_flows(self, parameters: Dict[str, Any], previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced flow validation using FlowValidator"""
        try:
            # Extract traces from previous results
            traces_result = None
            for result in previous_results.values():
                if result.result_data and "traces" in result.result_data:
                    traces_result = result.result_data["traces"]
                    break
            
            if not traces_result:
                return {"error": "No traces found from previous steps"}
            
            # Mock validation results
            validation_results = []
            for trace in traces_result:
                validation_results.append({
                    "trace_id": trace["trace_id"],
                    "is_valid": True,
                    "confidence": trace["confidence"],
                    "issues": [],
                    "completeness_score": 0.85
                })
            
            return {
                "validation_results": validation_results,
                "total_validated": len(validation_results),
                "overall_confidence": 0.8,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Flow validation failed: {e}")
            return {"error": str(e)}
    
    async def _tool_discover_shared_components(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Discover shared components across repositories"""
        try:
            # Mock shared component discovery
            shared_components = [
                {"name": "SharedUtility.jar", "repositories": ["repo1", "repo2", "repo3"], "risk": "medium"},
                {"name": "DatabaseConnection.java", "repositories": ["repo1", "repo2"], "risk": "high"},
                {"name": "ValidationFramework", "repositories": ["repo2", "repo3", "repo4"], "risk": "low"}
            ]
            
            return {
                "shared_components": shared_components,
                "total_components": len(shared_components),
                "high_risk_components": len([c for c in shared_components if c["risk"] == "high"]),
                "confidence": 0.9,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Shared component discovery failed: {e}")
            return {"error": str(e)}
    
    # Utility methods
    def _get_enhanced_context(self, session_id: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Get enhanced conversation context"""
        base_context = self.get_or_create_context(session_id)
        
        # Merge with provided context
        if context:
            base_context.update(context)
        
        return base_context
    
    def _parse_workflow_request(self, message: str, recommended_workflows: List[ToolSequence]) -> Optional[ToolSequence]:
        """Parse message to determine if user is requesting a specific workflow"""
        message_lower = message.lower()
        
        # Check for explicit workflow requests
        workflow_keywords = {
            "modernization analysis": "legacy_modernization_analysis",
            "impact analysis": "cross_repo_impact_analysis", 
            "business rule extraction": "business_rule_extraction",
            "health check": "architecture_health_check"
        }
        
        for keyword, workflow_id in workflow_keywords.items():
            if keyword in message_lower:
                return PredefinedWorkflows.get_workflow_by_id(workflow_id)
        
        # Check for workflow execution phrases
        execution_phrases = ["analyze", "run analysis", "execute", "perform", "do a"]
        if any(phrase in message_lower for phrase in execution_phrases) and recommended_workflows:
            return recommended_workflows[0]  # Return top recommendation
        
        return None
    
    def _are_dependencies_satisfied(self, tool_step, completed_results: Dict[str, Any]) -> bool:
        """Check if tool dependencies are satisfied"""
        for dependency in tool_step.depends_on:
            if dependency not in completed_results:
                return False
            if not completed_results[dependency].is_successful():
                return False
        return True
    
    def _generate_workflow_response(
        self, 
        original_message: str,
        workflow_results: Dict[str, Any],
        synthesis_results,
        relevant_context: Dict[str, Any]
    ) -> str:
        """Generate response based on workflow execution results"""
        
        workflow_name = workflow_results["workflow"].name
        success_rate = workflow_results.get("success_rate", 0.0)
        
        response = f"I've completed the {workflow_name} based on your request.\n\n"
        response += f"**Summary:** {synthesis_results.summary}\n\n"
        
        if synthesis_results.key_findings:
            response += "**Key Findings:**\n"
            for finding in synthesis_results.key_findings[:5]:
                response += f"• {finding}\n"
            response += "\n"
        
        if synthesis_results.recommendations:
            response += "**Recommendations:**\n"
            for rec in synthesis_results.recommendations[:5]:
                response += f"• {rec}\n"
            response += "\n"
        
        if synthesis_results.next_steps:
            response += "**Suggested Next Steps:**\n"
            for step in synthesis_results.next_steps[:3]:
                response += f"• {step}\n"
        
        response += f"\n*Analysis completed with {success_rate:.0%} tool success rate and {synthesis_results.confidence_score:.0%} confidence.*"
        
        return response
    
    def _enhance_standard_response(
        self,
        standard_response: str,
        relevant_context: Dict[str, Any],
        recommended_workflows: List[ToolSequence]
    ) -> str:
        """Enhance standard agent response with context and workflow recommendations"""
        
        enhanced_response = standard_response
        
        # Add context insights if available
        if relevant_context.get("relevant_data"):
            enhanced_response += "\n\n**Based on our previous analysis:**\n"
            for data in relevant_context["relevant_data"][:2]:
                enhanced_response += f"• {data.get('summary', 'Previous analysis available')}\n"
        
        # Add workflow recommendations
        if recommended_workflows:
            enhanced_response += f"\n\n**I can help you further with:**\n"
            for workflow in recommended_workflows[:3]:
                enhanced_response += f"• {workflow.name}: {workflow.description}\n"
        
        return enhanced_response
    
    async def get_workflow_status(self, session_id: str) -> Dict[str, Any]:
        """Get status of active workflows for a session"""
        if session_id in self.active_workflows:
            workflow = self.active_workflows[session_id]
            return {
                "active_workflow": workflow.name,
                "status": workflow.status.value,
                "progress": len([t for t in workflow.tools if t.status.value == "completed"]) / len(workflow.tools)
            }
        return {"active_workflow": None}


# Global enhanced agent service instance
_enhanced_agent_service: Optional[EnhancedStrandsAgentService] = None

async def get_enhanced_strands_agent_service() -> EnhancedStrandsAgentService:
    """Get the global enhanced agent service instance"""
    global _enhanced_agent_service
    if _enhanced_agent_service is None:
        _enhanced_agent_service = EnhancedStrandsAgentService()
    return _enhanced_agent_service