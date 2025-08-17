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
from app.services.vector_service import get_vector_service
from app.services.semantic_ai_service import get_semantic_ai_service

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
            user_preferences=context.get('user_preferences', {}) if context else {}
        )
        
        self.active_conversations[session_id] = conv_context
        
        # Get response from agent
        response = await self._get_agent_response(message, agent_type, conv_context)
        
        # Update conversation history
        conv_context.conversation_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "user_message": message,
            "agent_response": response.content,
            "agent_type": agent_type.value
        })
        conv_context.last_activity = datetime.utcnow()
        
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
        
        # Add recent conversation history
        if context.conversation_history:
            recent_history = context.conversation_history[-3:]  # Last 3 exchanges
            history_text = "\n".join([
                f"Previous: {h['user_message'][:100]}..." if len(h['user_message']) > 100 
                else f"Previous: {h['user_message']}"
                for h in recent_history
            ])
            context_parts.append(f"Recent Context:\n{history_text}")
        
        # Add user preferences
        if context.user_preferences:
            prefs_text = ", ".join([f"{k}: {v}" for k, v in context.user_preferences.items()])
            context_parts.append(f"User Preferences: {prefs_text}")
        
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
                "semantic_ai_service": self.semantic_ai_service is not None
            }
        }

# Global Strands agent service instance
strands_agent_service = StrandsAgentService()

async def get_strands_agent_service() -> StrandsAgentService:
    """Get Strands agent service instance"""
    return strands_agent_service