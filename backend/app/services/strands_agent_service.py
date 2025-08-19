"""
AWS Strands Agents Service for Conversational AI
Integrates Strands Agents SDK for production-ready multi-agent orchestration
"""

import logging
import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum

# Try importing strands-agents with graceful fallback
try:
    from strands import Agent, MessageFlow, ConversationMemory
    from strands.providers.bedrock import BedrockProvider
    from strands.providers.anthropic import AnthropicProvider
    from strands.core.agent import AgentConfig
    from strands.core.message import Message, MessageType
    from strands.core.tools import Tool, ToolResult
    STRANDS_AVAILABLE = True
except ImportError:
    STRANDS_AVAILABLE = False
    logging.warning("Strands Agents SDK not available. Install with: pip install strands-agents")
    
    # Create placeholder classes when Strands is not available
    class Tool:
        def __init__(self, name: str, description: str, function: Any, parameters: Dict[str, Any]):
            self.name = name
            self.description = description
            self.function = function
            self.parameters = parameters
    
    class ToolResult:
        def __init__(self, success: bool, data: Any = None, message: str = ""):
            self.success = success
            self.data = data
            self.message = message
    
    class Agent:
        def __init__(self, config: Any, provider: Any):
            pass
        def add_tool(self, tool: Tool):
            pass
        async def process_message(self, message: str):
            return type('Response', (), {'content': 'Strands not available'})()
    
    class AgentConfig:
        def __init__(self, name: str, system_prompt: str, max_tokens: int, temperature: float):
            pass
    
    class BedrockProvider:
        def __init__(self, model_id: str, region: str):
            pass

from app.core.config import settings
# NOTE: Vector operations now handled by OpenSearch - ChromaDB removed  
# from app.services.vector_service import get_vector_service
from app.services.semantic_ai_service import get_semantic_ai_service
from app.core.database import AsyncSessionLocal
from app.services.project_coordinator_service import get_project_coordinator_service
from app.services.cross_repository_discovery_service import get_cross_repository_discovery_service

logger = logging.getLogger(__name__)

class AgentType(Enum):
    MIGRATION_EXPERT = "migration_expert"
    CODE_ANALYZER = "code_analyzer"
    ARCHITECTURE_ADVISOR = "architecture_advisor"
    BUSINESS_ANALYST = "business_analyst"
    TECHNICAL_WRITER = "technical_writer"

@dataclass
class ConversationContext:
    session_id: str
    repository_ids: List[str] = field(default_factory=list)
    current_agent: Optional[AgentType] = None
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    analysis_cache: Dict[str, Any] = field(default_factory=dict)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    
    # WEEK 4 ENHANCEMENTS: Advanced context management
    project_id: Optional[str] = None
    business_rules_context: List[Dict[str, Any]] = field(default_factory=list)
    architectural_insights_context: List[Dict[str, Any]] = field(default_factory=list)
    domain_classification_context: Dict[str, Any] = field(default_factory=dict)
    cross_repository_insights: List[Dict[str, Any]] = field(default_factory=list)
    conversation_focus: Optional[str] = None  # "migration", "analysis", "architecture", "business", "documentation"
    context_embeddings: List[float] = field(default_factory=list)
    related_sessions: List[str] = field(default_factory=list)  # Related conversation sessions
    knowledge_base_references: List[str] = field(default_factory=list)
    conversation_sentiment: Optional[str] = None  # "positive", "neutral", "frustrated"
    user_expertise_level: str = "intermediate"  # "beginner", "intermediate", "expert"
    conversation_tags: List[str] = field(default_factory=list)

@dataclass
class AgentResponse:
    content: str
    agent_type: AgentType
    confidence: float
    reasoning: Optional[str] = None
    suggested_actions: List[str] = field(default_factory=list)
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    followup_questions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class StrandsAgentService:
    """
    Production-ready conversational AI service using AWS Strands Agents
    Provides specialized agents for legacy migration and code analysis
    """
    
    def __init__(self):
        self.available = STRANDS_AVAILABLE
        self.agents: Dict[AgentType, Any] = {}
        self.active_conversations: Dict[str, ConversationContext] = {}
        self.vector_service = None
        self.semantic_ai_service = None
        
        # WEEK 4 ENHANCEMENTS: Business rule and project integration
        self.project_coordinator_service = None
        self.cross_repo_discovery_service = None
        self.conversation_memory_store: Dict[str, List[Dict[str, Any]]] = {}  # Long-term memory across sessions
        self.business_rule_cache: Dict[str, List[Dict[str, Any]]] = {}
        self.architectural_insights_cache: Dict[str, List[Dict[str, Any]]] = {}
        
        if self.available:
            asyncio.create_task(self._initialize_agents())
        else:
            logger.warning("Strands Agents not available - using fallback implementation")
    
    async def _initialize_agents(self):
        """Initialize all specialized agents"""
        try:
            # Initialize services
            self.vector_service = await get_vector_service()
            self.semantic_ai_service = await get_semantic_ai_service()
            
            # WEEK 4 ENHANCEMENTS: Initialize business rule and project services
            self.project_coordinator_service = await get_project_coordinator_service()
            self.cross_repo_discovery_service = await get_cross_repository_discovery_service()
            
            # Create Bedrock provider for all agents
            provider = BedrockProvider(
                model_id=settings.BEDROCK_MODEL_ID,
                region=settings.AWS_REGION
            )
            
            # Initialize specialized agents
            await self._create_migration_expert_agent(provider)
            await self._create_code_analyzer_agent(provider)
            await self._create_architecture_advisor_agent(provider)
            await self._create_business_analyst_agent(provider)
            await self._create_technical_writer_agent(provider)
            
            logger.info("Strands Agents initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Strands Agents: {e}")
            self.available = False
    
    async def _create_migration_expert_agent(self, provider):
        """Create specialized migration expert agent"""
        system_prompt = """You are an expert legacy system migration consultant with 20+ years of experience modernizing enterprise applications. Your expertise includes:

🎯 **Core Specializations:**
- Legacy framework migration (Struts → Spring Boot, CORBA → gRPC/REST)
- Database modernization (Oracle → PostgreSQL/MongoDB)
- Architecture transformation (Monolith → Microservices)
- Cloud migration strategies (On-premise → AWS/Azure/GCP)

🔧 **Technical Expertise:**
- Java Enterprise (J2EE, EJB, JSF, Struts, Spring)
- .NET Framework → .NET Core migration
- COBOL and mainframe modernization
- Legacy CORBA and RMI system replacement
- Database schema evolution and data migration

💼 **Business Focus:**
- Risk assessment and mitigation strategies
- ROI analysis and cost-benefit calculations
- Timeline estimation and project planning
- Stakeholder communication and change management

🎯 **Your Approach:**
1. **Assess Current State**: Analyze legacy architecture and dependencies
2. **Define Target Architecture**: Recommend modern, scalable solutions
3. **Create Migration Strategy**: Phased approach with minimal business disruption
4. **Risk Mitigation**: Identify potential issues and provide solutions
5. **Success Metrics**: Define measurable outcomes and KPIs

Always provide:
- Specific, actionable recommendations
- Risk assessment with mitigation strategies
- Timeline estimates with milestones
- Technology recommendations with rationale
- Business impact analysis

Be direct, practical, and focus on delivering business value while managing technical complexity."""

        config = AgentConfig(
            name="Migration Expert",
            system_prompt=system_prompt,
            max_tokens=3000,
            temperature=0.2
        )
        
        agent = Agent(config=config, provider=provider)
        
        # Add custom tools for migration analysis
        agent.add_tool(self._create_migration_analysis_tool())
        agent.add_tool(self._create_technology_recommendation_tool())
        agent.add_tool(self._create_risk_assessment_tool())
        
        # WEEK 4 ENHANCEMENTS: Add business rule context tools
        agent.add_tool(self._create_business_rule_context_tool())
        agent.add_tool(self._create_architectural_insights_tool())
        agent.add_tool(self._create_project_context_tool())
        agent.add_tool(self._create_cross_repository_insights_tool())
        
        self.agents[AgentType.MIGRATION_EXPERT] = agent
    
    async def _create_code_analyzer_agent(self, provider):
        """Create specialized code analysis agent"""
        system_prompt = """You are a senior software engineer and code analysis expert specializing in legacy codebase assessment. Your expertise includes:

🔍 **Code Analysis Specializations:**
- Static code analysis and quality assessment
- Technical debt identification and quantification
- Design pattern recognition and anti-pattern detection
- Performance bottleneck identification
- Security vulnerability assessment

🏗️ **Architecture Analysis:**
- Component dependency mapping
- Coupling and cohesion analysis
- Layer violation detection
- Interface and API design evaluation
- Data flow and control flow analysis

📊 **Metrics & Quality Assessment:**
- Cyclomatic complexity analysis
- Code coverage assessment
- Maintainability index calculation
- Code duplication detection
- Documentation quality evaluation

🔧 **Technology Stack Analysis:**
- Framework usage patterns and best practices
- Library dependency analysis and recommendations
- Version compatibility assessment
- Performance optimization opportunities
- Modernization pathway identification

🎯 **Your Methodology:**
1. **Code Structure Analysis**: Examine package organization and class hierarchies
2. **Quality Metrics**: Calculate complexity, maintainability, and technical debt
3. **Pattern Recognition**: Identify design patterns and architectural styles
4. **Dependency Analysis**: Map component relationships and coupling
5. **Improvement Recommendations**: Suggest specific refactoring opportunities

Always provide:
- Specific code examples and references
- Quantitative metrics and measurements
- Prioritized improvement recommendations
- Refactoring strategies with effort estimates
- Technology upgrade pathways"""

        config = AgentConfig(
            name="Code Analyzer",
            system_prompt=system_prompt,
            max_tokens=3000,
            temperature=0.1
        )
        
        agent = Agent(config=config, provider=provider)
        
        # Add code analysis tools
        agent.add_tool(self._create_code_quality_analysis_tool())
        agent.add_tool(self._create_dependency_analysis_tool())
        agent.add_tool(self._create_pattern_detection_tool())
        
        # WEEK 4 ENHANCEMENTS: Add business rule context tools
        agent.add_tool(self._create_business_rule_context_tool())
        agent.add_tool(self._create_architectural_insights_tool())
        agent.add_tool(self._create_project_context_tool())
        agent.add_tool(self._create_cross_repository_insights_tool())
        
        self.agents[AgentType.CODE_ANALYZER] = agent
    
    async def _create_architecture_advisor_agent(self, provider):
        """Create specialized architecture advisor agent"""
        system_prompt = """You are a principal software architect with expertise in enterprise system design and modernization. Your specializations include:

🏛️ **Architecture Expertise:**
- Enterprise architecture patterns (SOA, Microservices, Event-Driven)
- Cloud-native architecture design (12-factor apps, containerization)
- Scalability and performance architecture
- Security architecture and compliance frameworks
- Integration patterns and API design

🔧 **Modern Architecture Patterns:**
- Domain-Driven Design (DDD) and bounded contexts
- CQRS and Event Sourcing patterns
- Serverless and Function-as-a-Service (FaaS)
- Container orchestration (Kubernetes, Docker Swarm)
- Service mesh and observability patterns

📈 **Scalability & Performance:**
- Load balancing and auto-scaling strategies
- Caching patterns and data partitioning
- Database scaling (sharding, read replicas, CQRS)
- CDN and edge computing strategies
- Performance monitoring and optimization

🔐 **Security & Compliance:**
- Zero-trust security architecture
- Identity and access management (IAM) patterns
- Data encryption and key management
- Compliance frameworks (SOC 2, GDPR, HIPAA)
- Secure development lifecycle (SDLC)

🎯 **Your Approach:**
1. **Current State Assessment**: Analyze existing architecture and constraints
2. **Future State Design**: Define target architecture with modern patterns
3. **Gap Analysis**: Identify differences and transformation requirements
4. **Implementation Roadmap**: Phased approach with dependency management
5. **Quality Attributes**: Ensure scalability, security, and maintainability

Always provide:
- Architecture diagrams in text format
- Technology stack recommendations with rationale
- Quality attribute analysis (performance, security, scalability)
- Implementation patterns and best practices
- Risk assessment and mitigation strategies"""

        config = AgentConfig(
            name="Architecture Advisor",
            system_prompt=system_prompt,
            max_tokens=3500,
            temperature=0.25
        )
        
        agent = Agent(config=config, provider=provider)
        
        # Add architecture analysis tools
        agent.add_tool(self._create_architecture_analysis_tool())
        agent.add_tool(self._create_scalability_assessment_tool())
        agent.add_tool(self._create_technology_recommendation_tool())
        
        # WEEK 4 ENHANCEMENTS: Add business rule context tools
        agent.add_tool(self._create_business_rule_context_tool())
        agent.add_tool(self._create_architectural_insights_tool())
        agent.add_tool(self._create_project_context_tool())
        agent.add_tool(self._create_cross_repository_insights_tool())
        
        self.agents[AgentType.ARCHITECTURE_ADVISOR] = agent
    
    async def _create_business_analyst_agent(self, provider):
        """Create specialized business analyst agent"""
        system_prompt = """You are a senior business analyst specializing in enterprise software systems and digital transformation. Your expertise includes:

💼 **Business Analysis Expertise:**
- Business process modeling and optimization
- Requirements gathering and stakeholder management
- Business rule extraction and documentation
- Workflow analysis and improvement recommendations
- Impact assessment and change management

📊 **Domain Analysis:**
- Business capability mapping
- Value stream analysis
- Process automation opportunities
- Digital transformation strategy
- Business-IT alignment assessment

🎯 **Stakeholder Management:**
- Executive communication and reporting
- User experience and adoption strategies
- Training and change management planning
- Success metrics and KPI definition
- ROI analysis and business case development

🔄 **Process Optimization:**
- Current state vs. future state analysis
- Process bottleneck identification
- Automation opportunity assessment
- Workflow simplification recommendations
- Integration point analysis

🎯 **Your Methodology:**
1. **Business Context Analysis**: Understand the business domain and objectives
2. **Process Mapping**: Document current workflows and business rules
3. **Gap Analysis**: Identify inefficiencies and improvement opportunities
4. **Future State Design**: Define optimized processes and workflows
5. **Implementation Planning**: Create actionable transformation roadmap

Always provide:
- Business-focused language and explanations
- Process diagrams and workflow descriptions
- Business rule documentation with examples
- Impact assessment with quantified benefits
- Implementation recommendations with success metrics"""

        config = AgentConfig(
            name="Business Analyst",
            system_prompt=system_prompt,
            max_tokens=3000,
            temperature=0.3
        )
        
        agent = Agent(config=config, provider=provider)
        
        # Add business analysis tools
        agent.add_tool(self._create_business_rule_extraction_tool())
        agent.add_tool(self._create_process_analysis_tool())
        agent.add_tool(self._create_impact_assessment_tool())
        
        # WEEK 4 ENHANCEMENTS: Add business rule context tools
        agent.add_tool(self._create_business_rule_context_tool())
        agent.add_tool(self._create_architectural_insights_tool())
        agent.add_tool(self._create_project_context_tool())
        agent.add_tool(self._create_cross_repository_insights_tool())
        
        self.agents[AgentType.BUSINESS_ANALYST] = agent
    
    async def _create_technical_writer_agent(self, provider):
        """Create specialized technical documentation agent"""
        system_prompt = """You are an expert technical writer and documentation specialist with extensive experience in software documentation. Your expertise includes:

📝 **Documentation Specializations:**
- API documentation and developer guides
- Architecture documentation and design documents
- User manuals and operational runbooks
- Migration guides and implementation procedures
- Knowledge base articles and troubleshooting guides

🎯 **Writing Excellence:**
- Clear, concise, and audience-appropriate language
- Structured information architecture
- Visual documentation with diagrams and examples
- Interactive tutorials and step-by-step guides
- Cross-referencing and information linking

👥 **Audience Adaptation:**
- Executive summaries for leadership
- Technical deep-dives for developers
- Process guides for operations teams
- Training materials for end users
- Troubleshooting guides for support teams

🔧 **Documentation Types:**
- System overviews and architecture guides
- Installation and configuration procedures
- Best practices and coding standards
- Migration playbooks and checklists
- Performance tuning and optimization guides

🎯 **Your Approach:**
1. **Audience Analysis**: Understand who will use the documentation
2. **Information Architecture**: Organize content logically and intuitively
3. **Clear Communication**: Use simple language and concrete examples
4. **Visual Enhancement**: Include diagrams, code samples, and screenshots
5. **Continuous Improvement**: Make documentation maintainable and updatable

Always provide:
- Well-structured content with clear headings
- Code examples and practical demonstrations
- Step-by-step procedures with verification steps
- Cross-references to related documentation
- Maintenance and update recommendations"""

        config = AgentConfig(
            name="Technical Writer",
            system_prompt=system_prompt,
            max_tokens=4000,
            temperature=0.2
        )
        
        agent = Agent(config=config, provider=provider)
        
        # Add documentation tools
        agent.add_tool(self._create_documentation_generation_tool())
        agent.add_tool(self._create_content_organization_tool())
        
        # WEEK 4 ENHANCEMENTS: Add business rule context tools
        agent.add_tool(self._create_business_rule_context_tool())
        agent.add_tool(self._create_architectural_insights_tool())
        agent.add_tool(self._create_project_context_tool())
        agent.add_tool(self._create_cross_repository_insights_tool())
        
        self.agents[AgentType.TECHNICAL_WRITER] = agent
    
    def _create_migration_analysis_tool(self) -> Tool:
        """Create tool for migration analysis"""
        async def migration_analysis(legacy_technology: str, target_technology: str) -> ToolResult:
            try:
                if self.semantic_ai_service:
                    results = await self.semantic_ai_service.find_migration_recommendations(
                        legacy_pattern=legacy_technology,
                        technology_stack=target_technology
                    )
                    return ToolResult(
                        success=True,
                        data=results,
                        message=f"Migration analysis completed for {legacy_technology} → {target_technology}"
                    )
                else:
                    return ToolResult(
                        success=False,
                        message="Semantic AI service not available"
                    )
            except Exception as e:
                return ToolResult(
                    success=False,
                    message=f"Migration analysis failed: {e}"
                )
        
        return Tool(
            name="migration_analysis",
            description="Analyze migration from legacy technology to modern alternatives",
            function=migration_analysis,
            parameters={
                "legacy_technology": {"type": "string", "description": "Current legacy technology"},
                "target_technology": {"type": "string", "description": "Target modern technology"}
            }
        )
    
    def _create_technology_recommendation_tool(self) -> Tool:
        """Create tool for technology recommendations"""
        async def technology_recommendation(requirements: str, constraints: str = "") -> ToolResult:
            try:
                # Use semantic search to find similar patterns
                if self.semantic_ai_service:
                    results = await self.semantic_ai_service.semantic_code_search(
                        search_query=f"technology stack {requirements} {constraints}"
                    )
                    return ToolResult(
                        success=True,
                        data=results,
                        message="Technology recommendations generated"
                    )
                else:
                    return ToolResult(
                        success=False,
                        message="Semantic AI service not available"
                    )
            except Exception as e:
                return ToolResult(
                    success=False,
                    message=f"Technology recommendation failed: {e}"
                )
        
        return Tool(
            name="technology_recommendation",
            description="Recommend modern technologies based on requirements and constraints",
            function=technology_recommendation,
            parameters={
                "requirements": {"type": "string", "description": "Technical requirements and needs"},
                "constraints": {"type": "string", "description": "Constraints and limitations"}
            }
        )
    
    def _create_risk_assessment_tool(self) -> Tool:
        """Create tool for risk assessment"""
        async def risk_assessment(component_path: str, migration_target: str) -> ToolResult:
            try:
                if self.semantic_ai_service:
                    results = await self.semantic_ai_service.analyze_migration_impact(
                        component_path=component_path,
                        target_technology=migration_target
                    )
                    return ToolResult(
                        success=True,
                        data=results,
                        message=f"Risk assessment completed for {component_path}"
                    )
                else:
                    return ToolResult(
                        success=False,
                        message="Semantic AI service not available"
                    )
            except Exception as e:
                return ToolResult(
                    success=False,
                    message=f"Risk assessment failed: {e}"
                )
        
        return Tool(
            name="risk_assessment",
            description="Assess migration risks and impact for specific components",
            function=risk_assessment,
            parameters={
                "component_path": {"type": "string", "description": "Path to component being assessed"},
                "migration_target": {"type": "string", "description": "Target technology for migration"}
            }
        )
    
    def _create_code_quality_analysis_tool(self) -> Tool:
        """Create tool for code quality analysis"""
        async def code_quality_analysis(code_content: str, file_path: str) -> ToolResult:
            try:
                if self.semantic_ai_service:
                    results = await self.semantic_ai_service.analyze_code_with_context(
                        code_content=code_content,
                        file_path=file_path,
                        analysis_type="quality_assessment"
                    )
                    return ToolResult(
                        success=True,
                        data=results,
                        message=f"Code quality analysis completed for {file_path}"
                    )
                else:
                    return ToolResult(
                        success=False,
                        message="Semantic AI service not available"
                    )
            except Exception as e:
                return ToolResult(
                    success=False,
                    message=f"Code quality analysis failed: {e}"
                )
        
        return Tool(
            name="code_quality_analysis",
            description="Analyze code quality metrics and identify improvement opportunities",
            function=code_quality_analysis,
            parameters={
                "code_content": {"type": "string", "description": "Code content to analyze"},
                "file_path": {"type": "string", "description": "Path to the code file"}
            }
        )
    
    def _create_dependency_analysis_tool(self) -> Tool:
        """Create tool for dependency analysis"""
        async def dependency_analysis(search_query: str) -> ToolResult:
            try:
                if self.vector_service:
                    results = await self.vector_service.semantic_search(
                        query=f"dependencies imports {search_query}",
                        collection_name="code_entities",
                        n_results=10
                    )
                    return ToolResult(
                        success=True,
                        data=results,
                        message="Dependency analysis completed"
                    )
                else:
                    return ToolResult(
                        success=False,
                        message="Vector service not available"
                    )
            except Exception as e:
                return ToolResult(
                    success=False,
                    message=f"Dependency analysis failed: {e}"
                )
        
        return Tool(
            name="dependency_analysis",
            description="Analyze component dependencies and relationships",
            function=dependency_analysis,
            parameters={
                "search_query": {"type": "string", "description": "Component or dependency to analyze"}
            }
        )
    
    def _create_pattern_detection_tool(self) -> Tool:
        """Create tool for design pattern detection"""
        async def pattern_detection(code_context: str) -> ToolResult:
            try:
                if self.vector_service:
                    results = await self.vector_service.semantic_search(
                        query=f"design patterns {code_context}",
                        collection_name="code_entities",
                        n_results=5
                    )
                    return ToolResult(
                        success=True,
                        data=results,
                        message="Pattern detection completed"
                    )
                else:
                    return ToolResult(
                        success=False,
                        message="Vector service not available"
                    )
            except Exception as e:
                return ToolResult(
                    success=False,
                    message=f"Pattern detection failed: {e}"
                )
        
        return Tool(
            name="pattern_detection",
            description="Detect design patterns and architectural styles in code",
            function=pattern_detection,
            parameters={
                "code_context": {"type": "string", "description": "Code context to analyze for patterns"}
            }
        )
    
    def _create_architecture_analysis_tool(self) -> Tool:
        """Create tool for architecture analysis"""
        async def architecture_analysis(system_scope: str) -> ToolResult:
            try:
                if self.semantic_ai_service:
                    results = await self.semantic_ai_service.semantic_code_search(
                        search_query=f"architecture components {system_scope}"
                    )
                    return ToolResult(
                        success=True,
                        data=results,
                        message=f"Architecture analysis completed for {system_scope}"
                    )
                else:
                    return ToolResult(
                        success=False,
                        message="Semantic AI service not available"
                    )
            except Exception as e:
                return ToolResult(
                    success=False,
                    message=f"Architecture analysis failed: {e}"
                )
        
        return Tool(
            name="architecture_analysis",
            description="Analyze system architecture and component relationships",
            function=architecture_analysis,
            parameters={
                "system_scope": {"type": "string", "description": "Scope of system to analyze"}
            }
        )
    
    def _create_scalability_assessment_tool(self) -> Tool:
        """Create tool for scalability assessment"""
        async def scalability_assessment(component_type: str, usage_patterns: str) -> ToolResult:
            try:
                # Simulate scalability analysis based on component patterns
                assessment = {
                    "scalability_score": 7.5,
                    "bottlenecks": ["Database queries", "Session management"],
                    "recommendations": [
                        "Implement caching layer",
                        "Use read replicas for database",
                        "Implement stateless design"
                    ],
                    "effort_estimate": "Medium (2-3 months)"
                }
                return ToolResult(
                    success=True,
                    data=assessment,
                    message=f"Scalability assessment completed for {component_type}"
                )
            except Exception as e:
                return ToolResult(
                    success=False,
                    message=f"Scalability assessment failed: {e}"
                )
        
        return Tool(
            name="scalability_assessment",
            description="Assess system scalability and identify bottlenecks",
            function=scalability_assessment,
            parameters={
                "component_type": {"type": "string", "description": "Type of component to assess"},
                "usage_patterns": {"type": "string", "description": "Expected usage patterns and load"}
            }
        )
    
    def _create_business_rule_extraction_tool(self) -> Tool:
        """Create tool for business rule extraction"""
        async def business_rule_extraction(domain_context: str) -> ToolResult:
            try:
                if self.vector_service:
                    results = await self.vector_service.semantic_search(
                        query=f"business rules {domain_context}",
                        collection_name="business_rules",
                        n_results=10
                    )
                    return ToolResult(
                        success=True,
                        data=results,
                        message=f"Business rule extraction completed for {domain_context}"
                    )
                else:
                    return ToolResult(
                        success=False,
                        message="Vector service not available"
                    )
            except Exception as e:
                return ToolResult(
                    success=False,
                    message=f"Business rule extraction failed: {e}"
                )
        
        return Tool(
            name="business_rule_extraction",
            description="Extract and analyze business rules from domain context",
            function=business_rule_extraction,
            parameters={
                "domain_context": {"type": "string", "description": "Business domain context to analyze"}
            }
        )
    
    def _create_process_analysis_tool(self) -> Tool:
        """Create tool for process analysis"""
        async def process_analysis(process_description: str) -> ToolResult:
            try:
                # Simulate process analysis
                analysis = {
                    "process_steps": ["Input validation", "Business logic", "Data persistence", "Response"],
                    "bottlenecks": ["Manual approval step", "Legacy system integration"],
                    "optimization_opportunities": [
                        "Automate validation steps",
                        "Implement parallel processing",
                        "Cache frequently accessed data"
                    ],
                    "efficiency_score": 6.5
                }
                return ToolResult(
                    success=True,
                    data=analysis,
                    message=f"Process analysis completed"
                )
            except Exception as e:
                return ToolResult(
                    success=False,
                    message=f"Process analysis failed: {e}"
                )
        
        return Tool(
            name="process_analysis",
            description="Analyze business processes and identify optimization opportunities",
            function=process_analysis,
            parameters={
                "process_description": {"type": "string", "description": "Description of the process to analyze"}
            }
        )
    
    def _create_impact_assessment_tool(self) -> Tool:
        """Create tool for impact assessment"""
        async def impact_assessment(change_description: str, scope: str) -> ToolResult:
            try:
                # Simulate impact assessment
                assessment = {
                    "affected_systems": ["Customer management", "Billing system", "Reporting"],
                    "impact_level": "Medium",
                    "risk_factors": ["Data migration complexity", "User training required"],
                    "mitigation_strategies": [
                        "Phased rollout approach",
                        "Comprehensive testing",
                        "User training program"
                    ],
                    "estimated_effort": "4-6 weeks"
                }
                return ToolResult(
                    success=True,
                    data=assessment,
                    message=f"Impact assessment completed for {scope}"
                )
            except Exception as e:
                return ToolResult(
                    success=False,
                    message=f"Impact assessment failed: {e}"
                )
        
        return Tool(
            name="impact_assessment",
            description="Assess impact of proposed changes on business and systems",
            function=impact_assessment,
            parameters={
                "change_description": {"type": "string", "description": "Description of proposed changes"},
                "scope": {"type": "string", "description": "Scope of impact analysis"}
            }
        )
    
    def _create_documentation_generation_tool(self) -> Tool:
        """Create tool for documentation generation"""
        async def documentation_generation(content_type: str, target_audience: str, topic: str) -> ToolResult:
            try:
                if self.semantic_ai_service:
                    # Use semantic search to gather relevant information
                    search_results = await self.semantic_ai_service.semantic_code_search(
                        search_query=f"{content_type} {topic}",
                        filters={"documentation_type": content_type}
                    )
                    
                    return ToolResult(
                        success=True,
                        data=search_results,
                        message=f"Documentation content generated for {topic}"
                    )
                else:
                    return ToolResult(
                        success=False,
                        message="Semantic AI service not available"
                    )
            except Exception as e:
                return ToolResult(
                    success=False,
                    message=f"Documentation generation failed: {e}"
                )
        
        return Tool(
            name="documentation_generation",
            description="Generate technical documentation based on content type and audience",
            function=documentation_generation,
            parameters={
                "content_type": {"type": "string", "description": "Type of documentation (guide, reference, tutorial)"},
                "target_audience": {"type": "string", "description": "Intended audience for the documentation"},
                "topic": {"type": "string", "description": "Topic or subject to document"}
            }
        )
    
    def _create_content_organization_tool(self) -> Tool:
        """Create tool for content organization"""
        async def content_organization(content_elements: str, organization_type: str) -> ToolResult:
            try:
                # Simulate content organization
                organization = {
                    "structure": {
                        "introduction": ["Overview", "Prerequisites", "Scope"],
                        "main_content": ["Step-by-step guide", "Examples", "Best practices"],
                        "conclusion": ["Summary", "Next steps", "Additional resources"]
                    },
                    "recommended_format": "Hierarchical with clear sections",
                    "cross_references": ["Related topics", "See also", "Dependencies"],
                    "maintenance_notes": ["Update frequency", "Review schedule", "Ownership"]
                }
                return ToolResult(
                    success=True,
                    data=organization,
                    message=f"Content organization plan created"
                )
            except Exception as e:
                return ToolResult(
                    success=False,
                    message=f"Content organization failed: {e}"
                )
        
        return Tool(
            name="content_organization",
            description="Organize and structure content for optimal readability and navigation",
            function=content_organization,
            parameters={
                "content_elements": {"type": "string", "description": "Elements to organize"},
                "organization_type": {"type": "string", "description": "Type of organization structure"}
            }
        )
    
    # WEEK 4 ENHANCEMENTS: New tools integrating with business rule models
    
    def _create_business_rule_context_tool(self) -> Tool:
        """Create tool for business rule context retrieval"""
        async def business_rule_context(domain: str, repository_id: str = None) -> ToolResult:
            try:
                async with AsyncSessionLocal() as session:
                    from sqlalchemy import text
                    
                    # Use raw SQL to avoid SQLAlchemy model conflicts
                    if repository_id:
                        query = text("""
                            SELECT rule_name, business_domain, technology_stack, 
                                   entry_point, business_description, impact_level, 
                                   extraction_confidence
                            FROM business_rule_traces 
                            WHERE business_domain = :domain AND repository_id = :repo_id
                            LIMIT 20
                        """)
                        result = await session.execute(query, {"domain": domain, "repo_id": int(repository_id)})
                    else:
                        query = text("""
                            SELECT rule_name, business_domain, technology_stack, 
                                   entry_point, business_description, impact_level, 
                                   extraction_confidence
                            FROM business_rule_traces 
                            WHERE business_domain = :domain
                            LIMIT 20
                        """)
                        result = await session.execute(query, {"domain": domain})
                    
                    context_data = []
                    for row in result:
                        context_data.append({
                            "rule_name": row.rule_name,
                            "business_domain": row.business_domain,
                            "technology_stack": row.technology_stack,
                            "entry_point": row.entry_point,
                            "business_description": row.business_description,
                            "impact_level": row.impact_level,
                            "extraction_confidence": row.extraction_confidence
                        })
                    
                    return ToolResult(
                        success=True,
                        data=context_data,
                        message=f"Retrieved {len(context_data)} business rules for domain {domain}"
                    )
            except Exception as e:
                return ToolResult(
                    success=False,
                    message=f"Business rule context retrieval failed: {e}"
                )
        
        return Tool(
            name="business_rule_context",
            description="Retrieve business rules context for specific domains and repositories",
            function=business_rule_context,
            parameters={
                "domain": {"type": "string", "description": "Business domain to query"},
                "repository_id": {"type": "string", "description": "Optional repository ID to filter by"}
            }
        )
    
    def _create_architectural_insights_tool(self) -> Tool:
        """Create tool for architectural insights retrieval"""
        async def architectural_insights(insight_type: str = None, repository_id: str = None) -> ToolResult:
            try:
                async with AsyncSessionLocal() as session:
                    from sqlalchemy import text
                    
                    # Use raw SQL to avoid SQLAlchemy model conflicts
                    base_query = """
                        SELECT title, insight_type, description, business_context, 
                               technical_details, modernization_impact, modernization_priority, 
                               confidence_score
                        FROM enterprise_architectural_insights 
                        WHERE 1=1
                    """
                    
                    params = {}
                    if insight_type:
                        base_query += " AND insight_type = :insight_type"
                        params["insight_type"] = insight_type
                    
                    if repository_id:
                        base_query += " AND repository_id = :repo_id"
                        params["repo_id"] = int(repository_id)
                    
                    base_query += " LIMIT 15"
                    
                    query = text(base_query)
                    result = await session.execute(query, params)
                    
                    insights_data = []
                    for row in result:
                        insights_data.append({
                            "title": row.title,
                            "insight_type": row.insight_type,
                            "description": row.description,
                            "business_context": row.business_context,
                            "technical_details": row.technical_details,
                            "modernization_impact": row.modernization_impact,
                            "modernization_priority": row.modernization_priority,
                            "confidence_score": row.confidence_score
                        })
                    
                    return ToolResult(
                        success=True,
                        data=insights_data,
                        message=f"Retrieved {len(insights_data)} architectural insights"
                    )
            except Exception as e:
                return ToolResult(
                    success=False,
                    message=f"Architectural insights retrieval failed: {e}"
                )
        
        return Tool(
            name="architectural_insights",
            description="Retrieve architectural insights for modernization planning",
            function=architectural_insights,
            parameters={
                "insight_type": {"type": "string", "description": "Optional insight type filter"},
                "repository_id": {"type": "string", "description": "Optional repository ID to filter by"}
            }
        )
    
    def _create_project_context_tool(self) -> Tool:
        """Create tool for project context retrieval"""
        async def project_context(project_id: str) -> ToolResult:
            try:
                if self.project_coordinator_service:
                    project_status = await self.project_coordinator_service.get_project_status(project_id)
                    
                    if project_status:
                        return ToolResult(
                            success=True,
                            data=project_status,
                            message=f"Retrieved project context for {project_id}"
                        )
                    else:
                        return ToolResult(
                            success=False,
                            message=f"Project {project_id} not found"
                        )
                else:
                    return ToolResult(
                        success=False,
                        message="Project coordinator service not available"
                    )
            except Exception as e:
                return ToolResult(
                    success=False,
                    message=f"Project context retrieval failed: {e}"
                )
        
        return Tool(
            name="project_context",
            description="Retrieve comprehensive project context and status information",
            function=project_context,
            parameters={
                "project_id": {"type": "string", "description": "Project ID to retrieve context for"}
            }
        )
    
    def _create_cross_repository_insights_tool(self) -> Tool:
        """Create tool for cross-repository insights"""
        async def cross_repository_insights(project_id: str) -> ToolResult:
            try:
                if self.cross_repo_discovery_service:
                    analysis_results = await self.cross_repo_discovery_service.analyze_project_repositories(project_id)
                    
                    return ToolResult(
                        success=True,
                        data=analysis_results,
                        message=f"Retrieved cross-repository insights for project {project_id}"
                    )
                else:
                    return ToolResult(
                        success=False,
                        message="Cross-repository discovery service not available"
                    )
            except Exception as e:
                return ToolResult(
                    success=False,
                    message=f"Cross-repository insights retrieval failed: {e}"
                )
        
        return Tool(
            name="cross_repository_insights",
            description="Analyze relationships and dependencies across multiple repositories in a project",
            function=cross_repository_insights,
            parameters={
                "project_id": {"type": "string", "description": "Project ID to analyze"}
            }
        )
    
    async def start_conversation(
        self,
        message: str,
        agent_type: AgentType = AgentType.MIGRATION_EXPERT,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """Start a new conversation with a specialized agent"""
        session_id = str(uuid.uuid4())
        
        # Create conversation context
        conv_context = ConversationContext(
            session_id=session_id,
            current_agent=agent_type,
            repository_ids=context.get('repository_ids', []) if context else [],
            user_preferences=context.get('user_preferences', {}) if context else {},
            # WEEK 4 ENHANCEMENTS: Enhanced context
            project_id=context.get('project_id') if context else None,
            conversation_focus=self._infer_conversation_focus(message, agent_type),
            user_expertise_level=context.get('user_expertise_level', 'intermediate') if context else 'intermediate'
        )
        
        self.active_conversations[session_id] = conv_context
        
        # WEEK 4 ENHANCEMENTS: Load enhanced context
        await asyncio.gather(
            self._load_business_rule_context(conv_context),
            self._load_architectural_insights_context(conv_context),
            self._load_project_context(conv_context)
        )
        
        # Get response from agent
        response = await self._get_agent_response(message, agent_type, conv_context)
        
        # Update conversation history
        interaction = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_message": message,
            "agent_response": response.content,
            "agent_type": agent_type.value,
            # WEEK 4 ENHANCEMENTS: Enhanced interaction tracking
            "conversation_focus": conv_context.conversation_focus,
            "repository_ids": conv_context.repository_ids,
            "project_id": conv_context.project_id,
            "business_rules_used": len(conv_context.business_rules_context),
            "insights_referenced": len(conv_context.architectural_insights_context),
            "confidence": response.confidence
        }
        
        conv_context.conversation_history.append(interaction)
        conv_context.last_activity = datetime.utcnow()
        
        # Store in long-term memory
        await self._store_conversation_memory(session_id, interaction)
        
        # Add session ID to response metadata
        response.metadata["session_id"] = session_id
        
        return response
    
    async def continue_conversation(
        self,
        session_id: str,
        message: str,
        agent_type: Optional[AgentType] = None
    ) -> AgentResponse:
        """Continue an existing conversation"""
        if session_id not in self.active_conversations:
            raise ValueError(f"Conversation session {session_id} not found")
        
        conv_context = self.active_conversations[session_id]
        
        # Switch agent if requested
        if agent_type and agent_type != conv_context.current_agent:
            conv_context.current_agent = agent_type
        
        # Get response from agent
        response = await self._get_agent_response(
            message, 
            conv_context.current_agent, 
            conv_context
        )
        
        # Update conversation history
        conv_context.conversation_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "user_message": message,
            "agent_response": response.content,
            "agent_type": conv_context.current_agent.value
        })
        conv_context.last_activity = datetime.utcnow()
        
        # Add session context to response metadata
        response.metadata.update({
            "session_id": session_id,
            "conversation_length": len(conv_context.conversation_history),
            "current_agent": conv_context.current_agent.value
        })
        
        return response
    
    async def _get_agent_response(
        self,
        message: str,
        agent_type: AgentType,
        context: ConversationContext
    ) -> AgentResponse:
        """Get response from the specified agent"""
        try:
            if not self.available:
                return await self._fallback_response(message, agent_type, context)
            
            # Get the agent
            agent = self.agents.get(agent_type)
            if not agent:
                return AgentResponse(
                    content=f"Agent {agent_type.value} is not available",
                    agent_type=agent_type,
                    confidence=0.0
                )
            
            # Prepare context message with conversation history
            context_message = self._prepare_context_message(message, context)
            
            # Get response from Strands agent
            response = await agent.process_message(context_message)
            
            # Parse response and create AgentResponse
            return AgentResponse(
                content=response.content,
                agent_type=agent_type,
                confidence=0.9,  # High confidence for Strands responses
                reasoning=f"Response generated by {agent_type.value} agent",
                suggested_actions=self._extract_suggested_actions(response.content),
                followup_questions=self._extract_followup_questions(response.content),
                metadata={
                    "agent_type": agent_type.value,
                    "response_length": len(response.content),
                    "tool_calls_made": len(getattr(response, 'tool_calls', []))
                }
            )
            
        except Exception as e:
            logger.error(f"Agent response failed: {e}")
            return await self._fallback_response(message, agent_type, context)
    
    def _prepare_context_message(self, message: str, context: ConversationContext) -> str:
        """Prepare context-aware message for the agent"""
        context_parts = [f"User Message: {message}"]
        
        # Add repository context if available
        if context.repository_ids:
            context_parts.append(f"Repository Context: Analyzing {len(context.repository_ids)} repositories")
        
        # WEEK 4 ENHANCEMENTS: Add business rule context
        if context.business_rules_context:
            business_context = f"Business Rules Context: Found {len(context.business_rules_context)} business rules across domains: "
            domains = list(set([rule["business_domain"] for rule in context.business_rules_context]))
            business_context += ", ".join(domains[:5])  # Top 5 domains
            context_parts.append(business_context)
            
            # Add sample business rules for context
            sample_rules = []
            for rule in context.business_rules_context[:3]:  # Top 3 rules
                sample_rules.append(f"- {rule['rule_name']} ({rule['business_domain']})")
            if sample_rules:
                context_parts.append(f"Sample Rules:\n" + "\n".join(sample_rules))
        
        # Add architectural insights context
        if context.architectural_insights_context:
            insights_context = f"Architectural Insights: {len(context.architectural_insights_context)} insights available"
            high_priority = [i for i in context.architectural_insights_context if i.get("modernization_priority", 0) > 70]
            if high_priority:
                insights_context += f" (including {len(high_priority)} high-priority modernization items)"
            context_parts.append(insights_context)
        
        # Add project context
        if context.project_id and context.domain_classification_context:
            project_info = context.domain_classification_context
            project_context = f"Project Context: {project_info.get('project_name', 'Unknown')} - Status: {project_info.get('project_status', 'Unknown')}"
            if project_info.get('business_rules_discovered', 0) > 0:
                project_context += f", {project_info['business_rules_discovered']} business rules discovered"
            context_parts.append(project_context)
        
        # Add conversation focus
        if context.conversation_focus:
            context_parts.append(f"Conversation Focus: {context.conversation_focus}")
        
        # Add recent conversation history
        if context.conversation_history:
            recent_history = context.conversation_history[-3:]  # Last 3 exchanges
            history_text = "\n".join([
                f"Previous: {h['user_message'][:100]}..." if len(h['user_message']) > 100 
                else f"Previous: {h['user_message']}"
                for h in recent_history
            ])
            context_parts.append(f"Recent Context:\n{history_text}")
        
        # Add user preferences and expertise level
        if context.user_preferences:
            prefs_text = ", ".join([f"{k}: {v}" for k, v in context.user_preferences.items()])
            context_parts.append(f"User Preferences: {prefs_text}")
        
        context_parts.append(f"User Expertise Level: {context.user_expertise_level}")
        
        # Add conversation tags for context
        if context.conversation_tags:
            context_parts.append(f"Conversation Tags: {', '.join(context.conversation_tags[:5])}")  # Top 5 tags
        
        return "\n\n".join(context_parts)
    
    def _extract_suggested_actions(self, content: str) -> List[str]:
        """Extract suggested actions from agent response"""
        actions = []
        
        # Look for action indicators
        action_patterns = [
            r"(?:recommend|suggest|should|could|action).*?(?:\n|$)",
            r"(?:next steps?).*?(?:\n|$)",
            r"(?:consider|try|implement).*?(?:\n|$)"
        ]
        
        import re
        for pattern in action_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            actions.extend([match.strip() for match in matches[:3]])  # Limit to 3 per pattern
        
        return actions[:5]  # Return top 5 suggested actions
    
    def _extract_followup_questions(self, content: str) -> List[str]:
        """Extract potential followup questions from agent response"""
        questions = []
        
        # Look for question indicators
        question_patterns = [
            r"[?][^\n]*",  # Direct questions
            r"(?:would you like|do you want|shall we|should we)[^?]*[?]?",
            r"(?:more information|additional details|further analysis)[^.]*[?]?"
        ]
        
        import re
        for pattern in question_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            questions.extend([match.strip() for match in matches[:2]])  # Limit per pattern
        
        return questions[:3]  # Return top 3 followup questions
    
    async def _fallback_response(
        self,
        message: str,
        agent_type: AgentType,
        context: ConversationContext
    ) -> AgentResponse:
        """Provide fallback response when Strands is not available"""
        fallback_responses = {
            AgentType.MIGRATION_EXPERT: "I'm a migration expert ready to help with legacy system modernization. I can assist with framework migrations, architecture transformation, and migration planning. However, the full Strands agent is currently unavailable. Please install strands-agents for enhanced capabilities.",
            
            AgentType.CODE_ANALYZER: "I'm a code analysis expert ready to review your codebase for quality, patterns, and improvement opportunities. The enhanced Strands agent is not available, but I can still provide basic analysis. Install strands-agents for comprehensive code analysis capabilities.",
            
            AgentType.ARCHITECTURE_ADVISOR: "I'm an architecture advisor specializing in enterprise system design and modernization. While the full Strands agent is unavailable, I can provide architectural guidance. Install strands-agents for advanced architecture analysis.",
            
            AgentType.BUSINESS_ANALYST: "I'm a business analyst expert in process optimization and requirements analysis. The Strands agent system is not fully available, but I can help with business analysis. Install strands-agents for enhanced business intelligence.",
            
            AgentType.TECHNICAL_WRITER: "I'm a technical writing specialist ready to help with documentation and communication. The enhanced Strands agent is unavailable, but I can assist with basic documentation needs. Install strands-agents for comprehensive documentation generation."
        }
        
        return AgentResponse(
            content=fallback_responses.get(agent_type, "Agent system unavailable. Please install strands-agents."),
            agent_type=agent_type,
            confidence=0.3,
            reasoning="Fallback response - Strands Agents not available",
            suggested_actions=["Install strands-agents: pip install strands-agents"],
            metadata={"fallback": True, "strands_available": False}
        )
    
    async def get_conversation_history(self, session_id: str) -> Optional[ConversationContext]:
        """Get conversation history for a session"""
        return self.active_conversations.get(session_id)
    
    async def end_conversation(self, session_id: str) -> bool:
        """End a conversation session"""
        if session_id in self.active_conversations:
            del self.active_conversations[session_id]
            return True
        return False
    
    async def get_available_agents(self) -> Dict[str, Dict[str, Any]]:
        """Get information about available agents"""
        agents_info = {}
        
        for agent_type in AgentType:
            agents_info[agent_type.value] = {
                "name": agent_type.value.replace('_', ' ').title(),
                "available": self.available and agent_type in self.agents,
                "description": self._get_agent_description(agent_type),
                "capabilities": self._get_agent_capabilities(agent_type)
            }
        
        return agents_info
    
    def _get_agent_description(self, agent_type: AgentType) -> str:
        """Get description for an agent type"""
        descriptions = {
            AgentType.MIGRATION_EXPERT: "Expert in legacy system migration and modernization strategies",
            AgentType.CODE_ANALYZER: "Specialist in code quality assessment and improvement recommendations",
            AgentType.ARCHITECTURE_ADVISOR: "Principal architect for system design and architecture guidance",
            AgentType.BUSINESS_ANALYST: "Business analysis expert for process optimization and requirements",
            AgentType.TECHNICAL_WRITER: "Technical documentation specialist and communication expert"
        }
        return descriptions.get(agent_type, "Specialized AI agent")
    
    def _get_agent_capabilities(self, agent_type: AgentType) -> List[str]:
        """Get capabilities for an agent type"""
        capabilities = {
            AgentType.MIGRATION_EXPERT: [
                "Legacy framework analysis",
                "Migration strategy planning",
                "Risk assessment",
                "Technology recommendations",
                "ROI analysis"
            ],
            AgentType.CODE_ANALYZER: [
                "Code quality metrics",
                "Pattern detection",
                "Dependency analysis",
                "Refactoring recommendations",
                "Technical debt assessment"
            ],
            AgentType.ARCHITECTURE_ADVISOR: [
                "Architecture assessment",
                "Scalability planning",
                "Technology selection",
                "Design pattern guidance",
                "Performance optimization"
            ],
            AgentType.BUSINESS_ANALYST: [
                "Business rule extraction",
                "Process analysis",
                "Requirements gathering",
                "Impact assessment",
                "Workflow optimization"
            ],
            AgentType.TECHNICAL_WRITER: [
                "Documentation generation",
                "Content organization",
                "Audience adaptation",
                "Style consistency",
                "Knowledge management"
            ]
        }
        return capabilities.get(agent_type, [])
    
    async def get_service_health(self) -> Dict[str, Any]:
        """Get health status of the Strands Agent service"""
        return {
            "service_available": self.available,
            "strands_installed": STRANDS_AVAILABLE,
            "active_conversations": len(self.active_conversations),
            "available_agents": len(self.agents),
            "agent_types": [agent_type.value for agent_type in AgentType],
            "dependencies": {
                "vector_service": self.vector_service is not None,
                "semantic_ai_service": self.semantic_ai_service is not None,
                # WEEK 4 ENHANCEMENTS: New service dependencies
                "project_coordinator_service": self.project_coordinator_service is not None,
                "cross_repo_discovery_service": self.cross_repo_discovery_service is not None
            },
            "conversation_memory_entries": len(self.conversation_memory_store),
            "business_rule_cache_entries": len(self.business_rule_cache),
            "architectural_insights_cache_entries": len(self.architectural_insights_cache)
        }
    
    # WEEK 4 ENHANCEMENTS: Advanced conversation management methods
    
    def _infer_conversation_focus(self, message: str, agent_type: AgentType) -> str:
        """Infer the conversation focus from the message and agent type"""
        message_lower = message.lower()
        
        # Keyword-based focus detection
        if any(word in message_lower for word in ['migrate', 'migration', 'modernize', 'legacy']):
            return "migration"
        elif any(word in message_lower for word in ['architecture', 'design', 'scalability', 'pattern']):
            return "architecture"
        elif any(word in message_lower for word in ['business', 'process', 'rule', 'workflow']):
            return "business"
        elif any(word in message_lower for word in ['code', 'quality', 'refactor', 'technical debt']):
            return "analysis"
        elif any(word in message_lower for word in ['document', 'documentation', 'guide', 'manual']):
            return "documentation"
        
        # Default based on agent type
        focus_map = {
            AgentType.MIGRATION_EXPERT: "migration",
            AgentType.CODE_ANALYZER: "analysis",
            AgentType.ARCHITECTURE_ADVISOR: "architecture", 
            AgentType.BUSINESS_ANALYST: "business",
            AgentType.TECHNICAL_WRITER: "documentation"
        }
        
        return focus_map.get(agent_type, "general")
    
    async def _load_business_rule_context(self, conv_context: ConversationContext) -> None:
        """Load business rule context for the conversation"""
        try:
            if not conv_context.repository_ids:
                return
                
            async with AsyncSessionLocal() as session:
                from sqlalchemy import text
                
                # Use raw SQL to avoid model conflicts
                if len(conv_context.repository_ids) == 1:
                    query = text("""
                        SELECT rule_name, business_domain, technology_stack, 
                               entry_point, extraction_confidence
                        FROM business_rule_traces 
                        WHERE repository_id = :repo_id
                        LIMIT 20
                    """)
                    result = await session.execute(query, {"repo_id": int(conv_context.repository_ids[0])})
                else:
                    # For multiple repos, use a different approach
                    placeholders = ",".join([":repo_id_" + str(i) for i in range(len(conv_context.repository_ids))])
                    query_str = f"""
                        SELECT rule_name, business_domain, technology_stack, 
                               entry_point, extraction_confidence
                        FROM business_rule_traces 
                        WHERE repository_id IN ({placeholders})
                        LIMIT 20
                    """
                    query = text(query_str)
                    params = {f"repo_id_{i}": int(repo_id) for i, repo_id in enumerate(conv_context.repository_ids)}
                    result = await session.execute(query, params)
                
                for row in result:
                    conv_context.business_rules_context.append({
                        "rule_name": row.rule_name,
                        "business_domain": row.business_domain,
                        "technology_stack": row.technology_stack,
                        "entry_point": row.entry_point,
                        "extraction_confidence": row.extraction_confidence
                    })
                    
                # Update conversation tags based on business rules
                domains = list(set([rule["business_domain"] for rule in conv_context.business_rules_context]))
                conv_context.conversation_tags.extend(domains)
                
        except Exception as e:
            logger.warning(f"Failed to load business rule context: {e}")
    
    async def _load_architectural_insights_context(self, conv_context: ConversationContext) -> None:
        """Load architectural insights context for the conversation"""
        try:
            if not conv_context.repository_ids:
                return
                
            async with AsyncSessionLocal() as session:
                from sqlalchemy import text
                
                # Use raw SQL to avoid model conflicts
                if len(conv_context.repository_ids) == 1:
                    query = text("""
                        SELECT title, insight_type, modernization_impact, 
                               modernization_priority, confidence_score
                        FROM enterprise_architectural_insights 
                        WHERE repository_id = :repo_id
                        LIMIT 15
                    """)
                    result = await session.execute(query, {"repo_id": int(conv_context.repository_ids[0])})
                else:
                    # For multiple repos, use parameterized query
                    placeholders = ",".join([":repo_id_" + str(i) for i in range(len(conv_context.repository_ids))])
                    query_str = f"""
                        SELECT title, insight_type, modernization_impact, 
                               modernization_priority, confidence_score
                        FROM enterprise_architectural_insights 
                        WHERE repository_id IN ({placeholders})
                        LIMIT 15
                    """
                    query = text(query_str)
                    params = {f"repo_id_{i}": int(repo_id) for i, repo_id in enumerate(conv_context.repository_ids)}
                    result = await session.execute(query, params)
                
                for row in result:
                    conv_context.architectural_insights_context.append({
                        "title": row.title,
                        "insight_type": row.insight_type,
                        "modernization_impact": row.modernization_impact,
                        "modernization_priority": row.modernization_priority,
                        "confidence_score": row.confidence_score
                    })
                    
        except Exception as e:
            logger.warning(f"Failed to load architectural insights context: {e}")
    
    async def _load_project_context(self, conv_context: ConversationContext) -> None:
        """Load project context if project_id is available"""
        try:
            if not conv_context.project_id or not self.project_coordinator_service:
                return
                
            project_status = await self.project_coordinator_service.get_project_status(conv_context.project_id)
            
            if project_status:
                conv_context.domain_classification_context = {
                    "project_name": project_status.get("name", ""),
                    "project_status": project_status.get("status", ""),
                    "repositories_analyzed": project_status.get("repositories", {}).get("analyzed", 0),
                    "business_rules_discovered": project_status.get("discoveries", {}).get("business_rules", 0),
                    "insights_generated": project_status.get("discoveries", {}).get("insights", 0)
                }
                
                # Add project-level tags
                conv_context.conversation_tags.append(f"project:{conv_context.project_id}")
                
        except Exception as e:
            logger.warning(f"Failed to load project context: {e}")
    
    async def _store_conversation_memory(self, session_id: str, interaction: Dict[str, Any]) -> None:
        """Store conversation interaction in long-term memory"""
        try:
            if session_id not in self.conversation_memory_store:
                self.conversation_memory_store[session_id] = []
            
            # Add timestamp and metadata
            interaction["stored_at"] = datetime.utcnow().isoformat()
            interaction["session_id"] = session_id
            
            self.conversation_memory_store[session_id].append(interaction)
            
            # Limit memory size per session (keep last 50 interactions)
            if len(self.conversation_memory_store[session_id]) > 50:
                self.conversation_memory_store[session_id] = self.conversation_memory_store[session_id][-50:]
                
        except Exception as e:
            logger.warning(f"Failed to store conversation memory: {e}")
    
    async def _retrieve_related_conversations(self, conv_context: ConversationContext) -> List[Dict[str, Any]]:
        """Retrieve related conversations based on context similarity"""
        related = []
        
        try:
            for session_id, memory_entries in self.conversation_memory_store.items():
                if session_id == conv_context.session_id:
                    continue
                    
                # Check for overlap in repository IDs, project IDs, or conversation tags
                for entry in memory_entries[-5:]:  # Check recent entries only
                    if (entry.get("repository_ids") and 
                        set(entry["repository_ids"]).intersection(set(conv_context.repository_ids))):
                        related.append({
                            "session_id": session_id,
                            "snippet": entry.get("user_message", "")[:100],
                            "relevance": "repository_overlap"
                        })
                        break
                    elif (entry.get("project_id") == conv_context.project_id and conv_context.project_id):
                        related.append({
                            "session_id": session_id,
                            "snippet": entry.get("user_message", "")[:100],
                            "relevance": "project_overlap"
                        })
                        break
                        
        except Exception as e:
            logger.warning(f"Failed to retrieve related conversations: {e}")
        
        return related[:3]  # Return top 3 related conversations

# Global Strands agent service instance
strands_agent_service = StrandsAgentService()

async def get_strands_agent_service() -> StrandsAgentService:
    """Get Strands agent service instance"""
    return strands_agent_service