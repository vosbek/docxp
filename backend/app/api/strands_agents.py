"""
AWS Strands Agents API endpoints for conversational AI
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from datetime import datetime

from app.services.strands_agent_service import (
    get_strands_agent_service, 
    StrandsAgentService, 
    AgentType, 
    AgentResponse,
    ConversationContext
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["Strands Agents"])

# Request/Response Models
class StartConversationRequest(BaseModel):
    message: str = Field(..., description="Initial message to the agent")
    agent_type: str = Field(default="migration_expert", description="Type of agent to use")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "I need help migrating our legacy Struts application to Spring Boot",
                "agent_type": "migration_expert",
                "context": {
                    "repository_ids": ["legacy-customer-service"],
                    "user_preferences": {
                        "technical_depth": "detailed",
                        "focus_area": "backend_migration"
                    }
                }
            }
        }

class ContinueConversationRequest(BaseModel):
    message: str = Field(..., description="Message to continue the conversation")
    agent_type: Optional[str] = Field(default=None, description="Switch to different agent type")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "What are the main risks with this migration approach?",
                "agent_type": "migration_expert"
            }
        }

class AgentResponseModel(BaseModel):
    content: str
    agent_type: str
    confidence: float
    reasoning: Optional[str] = None
    suggested_actions: List[str] = []
    tool_calls: List[Dict[str, Any]] = []
    followup_questions: List[str] = []
    metadata: Dict[str, Any] = {}

class ConversationHistoryResponse(BaseModel):
    session_id: str
    repository_ids: List[str]
    current_agent: Optional[str]
    conversation_history: List[Dict[str, Any]]
    created_at: datetime
    last_activity: datetime
    total_exchanges: int

class AgentInfoResponse(BaseModel):
    name: str
    available: bool
    description: str
    capabilities: List[str]

@router.post("/start")
async def start_conversation(
    request: StartConversationRequest,
    strands_service: StrandsAgentService = Depends(get_strands_agent_service)
) -> AgentResponseModel:
    """
    Start a new conversation with a specialized agent
    """
    try:
        # Validate agent type
        try:
            agent_type = AgentType(request.agent_type)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid agent type: {request.agent_type}. Valid types: {[t.value for t in AgentType]}"
            )
        
        # Start conversation
        response = await strands_service.start_conversation(
            message=request.message,
            agent_type=agent_type,
            context=request.context
        )
        
        # Convert to response model
        return AgentResponseModel(
            content=response.content,
            agent_type=response.agent_type.value,
            confidence=response.confidence,
            reasoning=response.reasoning,
            suggested_actions=response.suggested_actions,
            tool_calls=response.tool_calls,
            followup_questions=response.followup_questions,
            metadata=response.metadata
        )
        
    except Exception as e:
        logger.error(f"Failed to start conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start conversation: {str(e)}")

@router.post("/continue/{session_id}")
async def continue_conversation(
    session_id: str,
    request: ContinueConversationRequest,
    strands_service: StrandsAgentService = Depends(get_strands_agent_service)
) -> AgentResponseModel:
    """
    Continue an existing conversation with an agent
    """
    try:
        # Parse agent type if provided
        agent_type = None
        if request.agent_type:
            try:
                agent_type = AgentType(request.agent_type)
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid agent type: {request.agent_type}"
                )
        
        # Continue conversation
        response = await strands_service.continue_conversation(
            session_id=session_id,
            message=request.message,
            agent_type=agent_type
        )
        
        # Convert to response model
        return AgentResponseModel(
            content=response.content,
            agent_type=response.agent_type.value,
            confidence=response.confidence,
            reasoning=response.reasoning,
            suggested_actions=response.suggested_actions,
            tool_calls=response.tool_calls,
            followup_questions=response.followup_questions,
            metadata=response.metadata
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to continue conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to continue conversation: {str(e)}")

@router.get("/conversation/{session_id}")
async def get_conversation_history(
    session_id: str,
    strands_service: StrandsAgentService = Depends(get_strands_agent_service)
) -> ConversationHistoryResponse:
    """
    Get conversation history for a session
    """
    try:
        context = await strands_service.get_conversation_history(session_id)
        
        if not context:
            raise HTTPException(status_code=404, detail=f"Conversation {session_id} not found")
        
        return ConversationHistoryResponse(
            session_id=context.session_id,
            repository_ids=context.repository_ids,
            current_agent=context.current_agent.value if context.current_agent else None,
            conversation_history=context.conversation_history,
            created_at=context.created_at,
            last_activity=context.last_activity,
            total_exchanges=len(context.conversation_history)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get conversation history: {str(e)}")

@router.delete("/conversation/{session_id}")
async def end_conversation(
    session_id: str,
    strands_service: StrandsAgentService = Depends(get_strands_agent_service)
):
    """
    End a conversation session
    """
    try:
        success = await strands_service.end_conversation(session_id)
        
        if success:
            return {
                "success": True,
                "message": f"Conversation {session_id} ended successfully"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Conversation {session_id} not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to end conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to end conversation: {str(e)}")

@router.get("/available")
async def get_available_agents(
    strands_service: StrandsAgentService = Depends(get_strands_agent_service)
) -> Dict[str, AgentInfoResponse]:
    """
    Get information about available agents
    """
    try:
        agents_info = await strands_service.get_available_agents()
        
        # Convert to response format
        response = {}
        for agent_id, info in agents_info.items():
            response[agent_id] = AgentInfoResponse(
                name=info["name"],
                available=info["available"],
                description=info["description"],
                capabilities=info["capabilities"]
            )
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to get available agents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get available agents: {str(e)}")

@router.get("/health")
async def agents_health_check(
    strands_service: StrandsAgentService = Depends(get_strands_agent_service)
):
    """
    Health check for Strands Agents service
    """
    try:
        health = await strands_service.get_service_health()
        
        return {
            "success": True,
            "status": "healthy" if health["service_available"] else "degraded",
            "service_info": health,
            "installation_status": {
                "strands_installed": health["strands_installed"],
                "installation_command": "pip install strands-agents" if not health["strands_installed"] else None
            }
        }
        
    except Exception as e:
        logger.error(f"Strands agents health check failed: {e}")
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e)
        }

@router.post("/demo")
async def demo_conversation(
    strands_service: StrandsAgentService = Depends(get_strands_agent_service)
):
    """
    Demo conversation showcasing different agent capabilities
    """
    try:
        demo_scenarios = [
            {
                "agent_type": "migration_expert",
                "message": "We have a legacy Struts 1.x application with CORBA services. What's the best migration approach?",
                "description": "Migration Expert analyzing legacy modernization"
            },
            {
                "agent_type": "code_analyzer",
                "message": "Can you analyze the code quality of our Java services and identify technical debt?",
                "description": "Code Analyzer assessing codebase quality"
            },
            {
                "agent_type": "architecture_advisor",
                "message": "How should we design our microservices architecture for scalability?",
                "description": "Architecture Advisor providing system design guidance"
            },
            {
                "agent_type": "business_analyst",
                "message": "What business processes would be affected by migrating our customer management system?",
                "description": "Business Analyst evaluating process impact"
            },
            {
                "agent_type": "technical_writer",
                "message": "We need comprehensive migration documentation for our development team.",
                "description": "Technical Writer creating migration guides"
            }
        ]
        
        demo_responses = []
        
        for scenario in demo_scenarios:
            try:
                agent_type = AgentType(scenario["agent_type"])
                response = await strands_service.start_conversation(
                    message=scenario["message"],
                    agent_type=agent_type,
                    context={"demo_mode": True}
                )
                
                demo_responses.append({
                    "scenario": scenario["description"],
                    "agent_type": scenario["agent_type"],
                    "user_message": scenario["message"],
                    "agent_response": response.content[:300] + "..." if len(response.content) > 300 else response.content,
                    "confidence": response.confidence,
                    "suggested_actions": response.suggested_actions[:3],  # Top 3 actions
                    "session_id": response.metadata.get("session_id")
                })
                
            except Exception as scenario_error:
                logger.warning(f"Demo scenario failed for {scenario['agent_type']}: {scenario_error}")
                demo_responses.append({
                    "scenario": scenario["description"],
                    "agent_type": scenario["agent_type"],
                    "error": str(scenario_error)
                })
        
        return {
            "success": True,
            "message": "Demo conversations completed",
            "demo_responses": demo_responses,
            "service_status": await strands_service.get_service_health()
        }
        
    except Exception as e:
        logger.error(f"Demo conversation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Demo conversation failed: {str(e)}")

@router.get("/capabilities/{agent_type}")
async def get_agent_capabilities(
    agent_type: str,
    strands_service: StrandsAgentService = Depends(get_strands_agent_service)
):
    """
    Get detailed capabilities for a specific agent type
    """
    try:
        # Validate agent type
        try:
            agent_enum = AgentType(agent_type)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid agent type: {agent_type}. Valid types: {[t.value for t in AgentType]}"
            )
        
        agents_info = await strands_service.get_available_agents()
        agent_info = agents_info.get(agent_type)
        
        if not agent_info:
            raise HTTPException(status_code=404, detail=f"Agent {agent_type} not found")
        
        # Add detailed capability information
        detailed_capabilities = {
            "migration_expert": {
                "primary_focus": "Legacy system modernization and migration strategy",
                "tools": [
                    "Migration pattern analysis",
                    "Technology recommendation engine",
                    "Risk assessment framework",
                    "ROI calculation tools"
                ],
                "expertise_areas": [
                    "Struts to Spring Boot migration",
                    "CORBA to gRPC/REST transformation",
                    "Database modernization strategies",
                    "Cloud migration planning",
                    "Microservices decomposition"
                ],
                "deliverables": [
                    "Migration roadmap with phases",
                    "Risk assessment with mitigation plans",
                    "Technology selection recommendations",
                    "Effort estimation and timeline",
                    "Business case and ROI analysis"
                ]
            },
            "code_analyzer": {
                "primary_focus": "Code quality assessment and improvement recommendations",
                "tools": [
                    "Static code analysis",
                    "Pattern detection algorithms",
                    "Dependency mapping tools",
                    "Quality metrics calculator"
                ],
                "expertise_areas": [
                    "Code quality metrics and standards",
                    "Design pattern identification",
                    "Technical debt quantification",
                    "Performance bottleneck detection",
                    "Security vulnerability assessment"
                ],
                "deliverables": [
                    "Code quality assessment report",
                    "Refactoring recommendations",
                    "Technical debt prioritization",
                    "Performance optimization plan",
                    "Security improvement roadmap"
                ]
            },
            "architecture_advisor": {
                "primary_focus": "System architecture design and scalability planning",
                "tools": [
                    "Architecture pattern analysis",
                    "Scalability assessment tools",
                    "Technology evaluation framework",
                    "Performance modeling tools"
                ],
                "expertise_areas": [
                    "Microservices architecture design",
                    "Cloud-native patterns",
                    "Scalability and performance optimization",
                    "Security architecture frameworks",
                    "Integration and API design"
                ],
                "deliverables": [
                    "Architecture blueprints",
                    "Scalability assessment report",
                    "Technology selection guide",
                    "Performance optimization plan",
                    "Security architecture design"
                ]
            },
            "business_analyst": {
                "primary_focus": "Business process analysis and requirements management",
                "tools": [
                    "Process mapping tools",
                    "Business rule extraction",
                    "Impact assessment framework",
                    "Stakeholder analysis tools"
                ],
                "expertise_areas": [
                    "Business process optimization",
                    "Requirements gathering and analysis",
                    "Stakeholder communication",
                    "Change impact assessment",
                    "ROI and benefit realization"
                ],
                "deliverables": [
                    "Process improvement recommendations",
                    "Business requirements documentation",
                    "Impact assessment reports",
                    "Change management plans",
                    "Success metrics and KPIs"
                ]
            },
            "technical_writer": {
                "primary_focus": "Technical documentation and knowledge management",
                "tools": [
                    "Documentation generation tools",
                    "Content organization framework",
                    "Style guide enforcement",
                    "Knowledge management systems"
                ],
                "expertise_areas": [
                    "API documentation and developer guides",
                    "Architecture documentation",
                    "Migration and implementation guides",
                    "User manuals and training materials",
                    "Knowledge base management"
                ],
                "deliverables": [
                    "Comprehensive documentation suites",
                    "Migration playbooks",
                    "API reference guides",
                    "Training materials",
                    "Documentation maintenance plans"
                ]
            }
        }
        
        detailed_info = detailed_capabilities.get(agent_type, {})
        
        return {
            "success": True,
            "agent_type": agent_type,
            "basic_info": agent_info,
            "detailed_capabilities": detailed_info,
            "availability": {
                "service_available": strands_service.available,
                "agent_ready": agent_info["available"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent capabilities: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent capabilities: {str(e)}")

@router.post("/bulk-analyze")
async def bulk_analyze_with_agents(
    background_tasks: BackgroundTasks,
    repository_ids: List[str],
    analysis_types: List[str],
    strands_service: StrandsAgentService = Depends(get_strands_agent_service)
):
    """
    Perform bulk analysis using multiple agents across repositories
    """
    try:
        # Validate analysis types
        valid_agent_types = [t.value for t in AgentType]
        invalid_types = [at for at in analysis_types if at not in valid_agent_types]
        if invalid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid analysis types: {invalid_types}. Valid types: {valid_agent_types}"
            )
        
        # Create analysis plan
        analysis_plan = {
            "analysis_id": f"bulk_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "repository_ids": repository_ids,
            "analysis_types": analysis_types,
            "status": "queued",
            "created_at": datetime.utcnow().isoformat(),
            "estimated_completion": "15-30 minutes depending on repository size"
        }
        
        # Queue background analysis
        background_tasks.add_task(
            _perform_bulk_analysis,
            strands_service,
            analysis_plan
        )
        
        return {
            "success": True,
            "message": f"Bulk analysis queued for {len(repository_ids)} repositories",
            "analysis_plan": analysis_plan,
            "agents_to_use": analysis_types,
            "next_steps": [
                "Analysis will be performed in the background",
                "Check status using the analysis_id",
                "Results will be available via conversation sessions"
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk analysis setup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk analysis setup failed: {str(e)}")

async def _perform_bulk_analysis(
    strands_service: StrandsAgentService,
    analysis_plan: Dict[str, Any]
):
    """
    Background task for performing bulk analysis
    """
    try:
        logger.info(f"Starting bulk analysis: {analysis_plan['analysis_id']}")
        
        # Simulate bulk analysis process
        for repo_id in analysis_plan["repository_ids"]:
            for agent_type_str in analysis_plan["analysis_types"]:
                try:
                    agent_type = AgentType(agent_type_str)
                    
                    # Start analysis conversation for each repository/agent combination
                    message = f"Please analyze repository {repo_id} and provide comprehensive insights."
                    
                    await strands_service.start_conversation(
                        message=message,
                        agent_type=agent_type,
                        context={
                            "repository_ids": [repo_id],
                            "bulk_analysis": True,
                            "analysis_id": analysis_plan["analysis_id"]
                        }
                    )
                    
                    logger.info(f"Completed {agent_type_str} analysis for {repo_id}")
                    
                except Exception as agent_error:
                    logger.error(f"Agent analysis failed for {repo_id}/{agent_type_str}: {agent_error}")
        
        logger.info(f"Bulk analysis completed: {analysis_plan['analysis_id']}")
        
    except Exception as e:
        logger.error(f"Bulk analysis background task failed: {e}")

@router.get("/agent-types")
async def get_agent_types():
    """
    Get all available agent types and their descriptions
    """
    return {
        "success": True,
        "agent_types": [
            {
                "id": agent_type.value,
                "name": agent_type.value.replace('_', ' ').title(),
                "description": _get_agent_type_description(agent_type)
            }
            for agent_type in AgentType
        ],
        "total_agents": len(AgentType)
    }

def _get_agent_type_description(agent_type: AgentType) -> str:
    """Get detailed description for agent type"""
    descriptions = {
        AgentType.MIGRATION_EXPERT: "Specialized in legacy system modernization, framework migrations, and cloud transformation strategies",
        AgentType.CODE_ANALYZER: "Expert in code quality assessment, technical debt analysis, and refactoring recommendations",
        AgentType.ARCHITECTURE_ADVISOR: "Principal architect for system design, scalability planning, and technology selection",
        AgentType.BUSINESS_ANALYST: "Business process expert for requirements analysis, impact assessment, and change management",
        AgentType.TECHNICAL_WRITER: "Documentation specialist for creating comprehensive technical guides and user documentation"
    }
    return descriptions.get(agent_type, "Specialized AI agent for software development tasks")