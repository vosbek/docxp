"""
Enhanced Diagram Service - AI-Powered Comprehensive Diagram Generation
Creates enterprise-grade diagrams with deep system understanding
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import json

from app.services.code_intelligence import CodeIntelligenceGraph, CodeEntityData, BusinessRuleContext
from app.services.ai_service import AIService
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class EnhancedDiagramService:
    """
    AI-powered diagram generation service that creates comprehensive, 
    enterprise-grade diagrams with deep system understanding
    """
    
    def __init__(self, ai_service: AIService, intelligence_graph: CodeIntelligenceGraph):
        self.ai_service = ai_service
        self.graph = intelligence_graph
    
    async def generate_comprehensive_diagram_suite(
        self,
        entities: List[Dict[str, Any]],
        business_rules_by_hierarchy: Dict[str, Any],
        call_graphs: Dict[str, List[List[str]]],
        database_analysis: Dict[str, Any],
        integration_analysis: Dict[str, Any],
        migration_analysis: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Generate comprehensive diagram suite with AI-powered analysis
        """
        logger.info("Generating comprehensive AI-powered diagram suite")
        
        diagrams = {}
        
        # Core Architecture Diagrams
        diagrams.update(await self._generate_core_architecture_diagrams(
            entities, business_rules_by_hierarchy, migration_analysis
        ))
        
        # Business Process & Flow Diagrams
        diagrams.update(await self._generate_business_process_diagrams(
            business_rules_by_hierarchy, call_graphs
        ))
        
        # Data & Integration Diagrams  
        diagrams.update(await self._generate_data_integration_diagrams(
            database_analysis, integration_analysis
        ))
        
        # Migration & Modernization Diagrams
        diagrams.update(await self._generate_migration_diagrams(
            migration_analysis, entities, business_rules_by_hierarchy
        ))
        
        # System Analysis Diagrams
        diagrams.update(await self._generate_system_analysis_diagrams(
            entities, call_graphs, business_rules_by_hierarchy
        ))
        
        logger.info(f"Generated {len(diagrams)} comprehensive diagrams")
        return diagrams
    
    async def _generate_core_architecture_diagrams(
        self,
        entities: List[Dict[str, Any]],
        business_rules_by_hierarchy: Dict[str, Any],
        migration_analysis: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate core architecture diagrams with AI analysis"""
        
        diagrams = {}
        
        # C4 Context Diagram
        diagrams['c4_context.mmd'] = await self._generate_c4_context_diagram(entities, migration_analysis)
        
        # C4 Container Diagram
        diagrams['c4_container.mmd'] = await self._generate_c4_container_diagram(entities, migration_analysis)
        
        # C4 Component Diagram
        diagrams['c4_component.mmd'] = await self._generate_c4_component_diagram(entities, business_rules_by_hierarchy)
        
        # Enterprise Architecture Overview
        diagrams['enterprise_architecture.mmd'] = await self._generate_enterprise_architecture_diagram(
            entities, business_rules_by_hierarchy, migration_analysis
        )
        
        # Layered Architecture Diagram
        diagrams['layered_architecture.mmd'] = await self._generate_layered_architecture_diagram(
            entities, business_rules_by_hierarchy
        )
        
        return diagrams
    
    async def _generate_business_process_diagrams(
        self,
        business_rules_by_hierarchy: Dict[str, Any],
        call_graphs: Dict[str, List[List[str]]]
    ) -> Dict[str, str]:
        """Generate business process and workflow diagrams"""
        
        diagrams = {}
        
        # Business Process Flowchart
        diagrams['business_process_flow.mmd'] = await self._generate_business_process_flowchart(
            business_rules_by_hierarchy, call_graphs
        )
        
        # Dynamic Sequence Diagrams (AI-generated from actual call graphs)
        diagrams['sequence_critical_flows.mmd'] = await self._generate_dynamic_sequence_diagram(
            call_graphs, business_rules_by_hierarchy
        )
        
        # Business Rule Interaction Diagram
        diagrams['business_rule_interactions.mmd'] = await self._generate_business_rule_interaction_diagram(
            business_rules_by_hierarchy
        )
        
        # User Journey Mapping
        diagrams['user_journey_mapping.mmd'] = await self._generate_user_journey_mapping(
            business_rules_by_hierarchy, call_graphs
        )
        
        return diagrams
    
    async def _generate_data_integration_diagrams(
        self,
        database_analysis: Dict[str, Any],
        integration_analysis: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate data flow and integration diagrams"""
        
        diagrams = {}
        
        # Data Flow Diagram
        diagrams['data_flow_diagram.mmd'] = await self._generate_intelligent_data_flow_diagram(
            database_analysis, integration_analysis
        )
        
        # Entity Relationship Diagram (AI-enhanced)
        diagrams['entity_relationship.mmd'] = await self._generate_enhanced_er_diagram(database_analysis)
        
        # Integration Architecture Diagram
        diagrams['integration_architecture.mmd'] = await self._generate_integration_architecture_diagram(
            integration_analysis
        )
        
        # API Interaction Diagram
        diagrams['api_interactions.mmd'] = await self._generate_api_interaction_diagram(integration_analysis)
        
        return diagrams
    
    async def _generate_migration_diagrams(
        self,
        migration_analysis: Dict[str, Any],
        entities: List[Dict[str, Any]],
        business_rules_by_hierarchy: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate migration and modernization diagrams"""
        
        diagrams = {}
        
        # Migration Strategy Roadmap
        diagrams['migration_roadmap.mmd'] = await self._generate_migration_roadmap_diagram(migration_analysis)
        
        # Technology Modernization Path
        diagrams['technology_modernization.mmd'] = await self._generate_technology_modernization_diagram(
            migration_analysis, entities
        )
        
        # Risk Assessment Matrix
        diagrams['migration_risk_matrix.mmd'] = await self._generate_migration_risk_matrix_diagram(
            migration_analysis, business_rules_by_hierarchy
        )
        
        # Legacy vs Modern Architecture Comparison
        diagrams['architecture_comparison.mmd'] = await self._generate_architecture_comparison_diagram(
            entities, migration_analysis
        )
        
        return diagrams
    
    async def _generate_system_analysis_diagrams(
        self,
        entities: List[Dict[str, Any]],
        call_graphs: Dict[str, List[List[str]]],
        business_rules_by_hierarchy: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate system analysis and metrics diagrams"""
        
        diagrams = {}
        
        # Complexity Analysis Heatmap
        diagrams['complexity_heatmap.mmd'] = await self._generate_complexity_heatmap(entities, call_graphs)
        
        # Dependency Graph
        diagrams['dependency_graph.mmd'] = await self._generate_intelligent_dependency_graph(entities)
        
        # Business Logic Distribution
        diagrams['business_logic_distribution.mmd'] = await self._generate_business_logic_distribution(
            business_rules_by_hierarchy
        )
        
        # System Metrics Dashboard
        diagrams['system_metrics_dashboard.mmd'] = await self._generate_system_metrics_dashboard(
            entities, business_rules_by_hierarchy, call_graphs
        )
        
        return diagrams
    
    async def _generate_c4_context_diagram(
        self,
        entities: List[Dict[str, Any]],
        migration_analysis: Dict[str, Any]
    ) -> str:
        """Generate AI-powered C4 Context diagram"""
        
        prompt = f"""# 🏗️ ENTERPRISE C4 CONTEXT DIAGRAM ARCHITECT

You are a senior enterprise architect creating a C4 Context diagram that shows the system in its business and technical environment.

## 📊 SYSTEM ANALYSIS DATA

### System Components
{self._summarize_entities_for_diagram(entities[:20])}

### Migration Context
{json.dumps(migration_analysis.get('business_context', {}), indent=2)}

## 🎯 C4 CONTEXT DIAGRAM REQUIREMENTS

Create a Mermaid C4 Context diagram that shows:

1. **The System** - The software system being documented
2. **Users/Actors** - People who interact with the system
3. **External Systems** - Other software systems that this system interacts with
4. **Relationships** - How the system, users, and external systems interact

## 📝 MERMAID C4 CONTEXT FORMAT

```mermaid
C4Context
    title System Context Diagram for [System Name]
    
    Person(user, "User Type", "Description of user role and responsibilities")
    System(system, "Primary System", "Core business capabilities and purpose")
    System_Ext(external, "External System", "Integration purpose and data exchange")
    
    Rel(user, system, "Interacts with", "HTTP/Web interface")
    Rel(system, external, "Integrates with", "REST API/Database")
```

## ⭐ QUALITY REQUIREMENTS

1. **Business-Focused**: Use business language for actors and systems
2. **Clear Relationships**: Show how data and control flow between systems
3. **Strategic Context**: Include all major external dependencies
4. **Migration Relevance**: Highlight systems that will be affected during modernization

Generate a comprehensive C4 Context diagram that provides strategic understanding of the system's position in the enterprise ecosystem.
"""
        
        try:
            return await self._call_ai_for_diagram(prompt)
        except Exception as e:
            logger.error(f"Error generating C4 context diagram: {e}")
            return self._generate_fallback_c4_context()
    
    async def _generate_c4_container_diagram(
        self,
        entities: List[Dict[str, Any]],
        migration_analysis: Dict[str, Any]
    ) -> str:
        """Generate AI-powered C4 Container diagram"""
        
        # Analyze entities to identify containers (web apps, APIs, databases, etc.)
        containers = self._identify_containers_from_entities(entities)
        
        prompt = f"""# 🏗️ ENTERPRISE C4 CONTAINER DIAGRAM ARCHITECT

You are creating a C4 Container diagram that shows the high-level technology choices and how responsibilities are distributed across them.

## 📊 IDENTIFIED CONTAINERS

{json.dumps(containers, indent=2)}

## 🎯 C4 CONTAINER DIAGRAM REQUIREMENTS

Create a Mermaid C4 Container diagram showing:

1. **Web Applications** - Frontend user interfaces
2. **API Applications** - Backend services and APIs  
3. **Databases** - Data storage systems
4. **External Services** - Third-party integrations
5. **Technology Choices** - Programming languages, frameworks, protocols

## 📝 MERMAID C4 CONTAINER FORMAT

```mermaid
C4Container
    title Container Diagram for [System Name]
    
    Person(user, "User", "System users")
    
    Container(web, "Web Application", "React/Angular", "User interface")
    Container(api, "API Application", "Java/Python", "Business logic and API")
    Container(db, "Database", "PostgreSQL/Oracle", "Data storage")
    
    Rel(user, web, "Uses", "HTTPS")
    Rel(web, api, "Calls", "REST API")
    Rel(api, db, "Reads/Writes", "SQL")
```

## ⭐ ARCHITECTURE INSIGHTS

Based on the entity analysis, include:
- Specific technology stacks identified in the code
- Data flow patterns between containers
- Security boundaries and protocols
- Integration patterns with external systems

Generate a detailed C4 Container diagram that serves as a foundation for technical migration planning.
"""
        
        try:
            return await self._call_ai_for_diagram(prompt)
        except Exception as e:
            logger.error(f"Error generating C4 container diagram: {e}")
            return self._generate_fallback_c4_container()
    
    async def _generate_dynamic_sequence_diagram(
        self,
        call_graphs: Dict[str, List[List[str]]],
        business_rules_by_hierarchy: Dict[str, Any]
    ) -> str:
        """Generate dynamic sequence diagram from actual call graphs"""
        
        # Find the most important call chains for sequence diagrams
        critical_flows = self._identify_critical_call_flows(call_graphs)
        
        prompt = f"""# 🔄 DYNAMIC SEQUENCE DIAGRAM ARCHITECT

You are creating sequence diagrams based on ACTUAL call graphs extracted from the codebase, not generic examples.

## 📊 CRITICAL CALL FLOWS

{json.dumps(critical_flows[:5], indent=2)}

## 🎯 SEQUENCE DIAGRAM REQUIREMENTS

Create Mermaid sequence diagrams showing:

1. **Real Method Calls** - Actual method invocation sequences from the code
2. **Actor Participation** - Which classes/components participate
3. **Message Flow** - Actual method calls and data exchange
4. **Business Context** - What business process each sequence supports
5. **Error Handling** - Exception paths where identified

## 📝 MERMAID SEQUENCE FORMAT

```mermaid
sequenceDiagram
    participant User
    participant Controller
    participant Service
    participant Repository
    participant Database
    
    User->>Controller: HTTP Request
    Controller->>Service: businessMethod()
    Service->>Repository: dataAccess()
    Repository->>Database: SQL Query
    Database-->>Repository: Results
    Repository-->>Service: Domain Objects
    Service-->>Controller: Response Data
    Controller-->>User: HTTP Response
```

## ⭐ CRITICAL REQUIREMENTS

1. **Use Actual Method Names** from the call graphs provided
2. **Show Real Class Names** not generic placeholders
3. **Include Business Context** - what business operation this represents
4. **Multiple Scenarios** - show 2-3 most important business flows
5. **Error Paths** - include exception handling where critical

Generate sequence diagrams that accurately represent the actual system behavior for the most critical business processes.
"""
        
        try:
            return await self._call_ai_for_diagram(prompt)
        except Exception as e:
            logger.error(f"Error generating dynamic sequence diagram: {e}")
            return self._generate_fallback_sequence_diagram()
    
    async def _generate_business_process_flowchart(
        self,
        business_rules_by_hierarchy: Dict[str, Any],
        call_graphs: Dict[str, List[List[str]]]
    ) -> str:
        """Generate business process flowchart with actual business rules"""
        
        # Extract business processes from rules
        business_processes = self._extract_business_processes(business_rules_by_hierarchy)
        
        prompt = f"""# 📋 BUSINESS PROCESS FLOWCHART ARCHITECT

You are creating business process flowcharts that map actual business rules to process steps and system execution flows.

## 📊 BUSINESS PROCESSES IDENTIFIED

{json.dumps(business_processes, indent=2)}

## 🎯 BUSINESS PROCESS FLOWCHART REQUIREMENTS

Create Mermaid flowcharts showing:

1. **Business Process Steps** - Actual business operations from the rules
2. **Decision Points** - Where business rules create conditional logic
3. **System Actions** - What the system does at each step
4. **Validation Points** - Where business rule validation occurs
5. **Integration Points** - External system interactions

## 📝 MERMAID FLOWCHART FORMAT

```mermaid
flowchart TD
    Start([User Initiates Process]) --> Validate{{Business Rule Validation}}
    Validate -->|Valid| Process[Execute Business Logic]
    Validate -->|Invalid| Error[Handle Business Rule Violation]
    Process --> Integration[External System Integration]
    Integration --> Complete([Process Complete])
    Error --> End([Process Terminated])
```

## ⭐ BUSINESS RULE INTEGRATION

For each flowchart:
1. **Reference Actual Business Rules** by ID where they apply
2. **Show Decision Logic** based on extracted business rule categories
3. **Include Error Handling** for business rule violations
4. **Map to Code Implementation** where business rules are enforced

Generate comprehensive business process flowcharts that bridge business understanding with technical implementation.
"""
        
        try:
            return await self._call_ai_for_diagram(prompt)
        except Exception as e:
            logger.error(f"Error generating business process flowchart: {e}")
            return self._generate_fallback_business_process()
    
    async def _generate_migration_roadmap_diagram(self, migration_analysis: Dict[str, Any]) -> str:
        """Generate migration roadmap diagram with specific phases and timelines"""
        
        prompt = f"""# 🗺️ MIGRATION ROADMAP DIAGRAM ARCHITECT

You are creating a comprehensive migration roadmap diagram that shows the phased approach to system modernization.

## 📊 MIGRATION ANALYSIS DATA

{json.dumps(migration_analysis, indent=2)}

## 🎯 MIGRATION ROADMAP REQUIREMENTS

Create a Mermaid timeline/Gantt diagram showing:

1. **Migration Phases** - Clear phases with objectives and deliverables
2. **Dependencies** - What must be completed before next phase
3. **Risk Mitigation** - Critical checkpoints and validation gates
4. **Business Continuity** - How business operations continue during migration
5. **Technology Transition** - Old to new technology migration paths

## 📝 MERMAID GANTT FORMAT

```mermaid
gantt
    title Migration Roadmap
    dateFormat YYYY-MM-DD
    section Phase 1: Foundation
    Infrastructure Setup     :milestone, m1, 2024-01-01, 0d
    Team Training           :active, train, 2024-01-01, 2w
    Environment Setup       :env, after train, 2w
    
    section Phase 2: Core Migration
    Legacy Analysis         :analysis, after env, 3w
    Business Logic Migration :logic, after analysis, 6w
    Data Migration          :data, after logic, 4w
    
    section Phase 3: Integration
    API Integration         :api, after data, 4w
    External System Testing :testing, after api, 3w
    Go-Live Preparation     :golive, after testing, 2w
```

## ⭐ STRATEGIC FOCUS

Include:
- **Specific deliverables** for each phase based on the analysis
- **Risk checkpoints** where business validation is required
- **Technology milestones** showing legacy retirement and modern system activation
- **Business impact windows** and mitigation strategies

Generate a comprehensive migration roadmap that provides clear guidance for enterprise migration execution.
"""
        
        try:
            return await self._call_ai_for_diagram(prompt)
        except Exception as e:
            logger.error(f"Error generating migration roadmap: {e}")
            return self._generate_fallback_migration_roadmap()
    
    async def _call_ai_for_diagram(self, prompt: str) -> str:
        """Call AI service for diagram generation with enhanced prompting"""
        try:
            # Use the enhanced AI service for better context awareness
            return await self.ai_service.generate_content(
                prompt=prompt,
                max_tokens=4000,
                temperature=0.2
            )
        except AttributeError:
            # Fallback if generate_content doesn't exist
            logger.warning("Using fallback AI service call for diagram generation")
            return "# Generated Diagram\n\n```mermaid\ngraph TD\n    A[System Component] --> B[Business Logic]\n    B --> C[Data Layer]\n```"
    
    # Helper methods for entity and data analysis
    
    def _summarize_entities_for_diagram(self, entities: List[Dict[str, Any]]) -> str:
        """Summarize entities for diagram context"""
        summary = []
        for entity in entities[:15]:
            summary.append(f"- {entity.get('type', 'unknown')}: {entity.get('name', 'unnamed')} "
                         f"({entity.get('file_path', 'unknown location')})")
        return "\\n".join(summary)
    
    def _identify_containers_from_entities(self, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Identify architectural containers from code entities"""
        containers = {
            'web_applications': [],
            'api_services': [],
            'databases': [],
            'external_integrations': []
        }
        
        for entity in entities:
            file_path = entity.get('file_path', '').lower()
            entity_type = entity.get('type', '')
            
            if any(web_indicator in file_path for web_indicator in ['controller', 'web', 'ui', 'frontend']):
                containers['web_applications'].append(entity.get('name', 'Unknown'))
            elif any(api_indicator in file_path for api_indicator in ['service', 'api', 'rest', 'endpoint']):
                containers['api_services'].append(entity.get('name', 'Unknown'))
            elif any(db_indicator in file_path for db_indicator in ['repository', 'dao', 'database', 'entity']):
                containers['databases'].append(entity.get('name', 'Unknown'))
        
        return containers
    
    def _identify_critical_call_flows(self, call_graphs: Dict[str, List[List[str]]]) -> List[Dict[str, Any]]:
        """Identify the most critical call flows for sequence diagrams"""
        critical_flows = []
        
        for source_method, call_chains in call_graphs.items():
            for chain in call_chains:
                if len(chain) >= 3:  # Focus on meaningful call chains
                    critical_flows.append({
                        'source': source_method,
                        'call_chain': chain,
                        'complexity': len(chain),
                        'business_significance': 'high' if len(chain) > 5 else 'medium'
                    })
        
        # Sort by complexity and return top flows
        critical_flows.sort(key=lambda x: x['complexity'], reverse=True)
        return critical_flows[:10]
    
    def _extract_business_processes(self, business_rules_by_hierarchy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract business processes from business rules"""
        processes = []
        
        # Extract from cross-cutting rules (often represent processes)
        for rule in business_rules_by_hierarchy.get('cross_cutting', []):
            if hasattr(rule, 'business_process') and rule.business_process:
                processes.append({
                    'name': rule.business_process,
                    'category': rule.category,
                    'rule_id': rule.rule_id,
                    'implementation': rule.method_call_chain or 'Multiple components'
                })
        
        return processes[:10]  # Top 10 processes
    
    # Fallback diagram methods
    
    def _generate_fallback_c4_context(self) -> str:
        """Generate fallback C4 context diagram"""
        return """```mermaid
C4Context
    title System Context Diagram
    
    Person(users, "System Users", "Business stakeholders using the system")
    System(system, "Legacy Business System", "Core business operations and data management")
    System_Ext(database, "Database System", "Data storage and retrieval")
    System_Ext(external, "External Systems", "Third-party integrations")
    
    Rel(users, system, "Uses", "Web interface")
    Rel(system, database, "Reads/Writes", "Database connection")
    Rel(system, external, "Integrates", "API calls")
```"""
    
    def _generate_fallback_c4_container(self) -> str:
        """Generate fallback C4 container diagram"""
        return """```mermaid
C4Container
    title Container Diagram
    
    Person(users, "Users", "System users")
    
    Container(web, "Web Application", "Frontend", "User interface")
    Container(api, "API Application", "Backend", "Business logic")
    Container(db, "Database", "Data Store", "Data persistence")
    
    Rel(users, web, "Uses", "HTTPS")
    Rel(web, api, "Calls", "REST API")
    Rel(api, db, "Reads/Writes", "SQL")
```"""
    
    def _generate_fallback_sequence_diagram(self) -> str:
        """Generate fallback sequence diagram"""
        return """```mermaid
sequenceDiagram
    participant User
    participant WebApp
    participant API
    participant Database
    
    User->>WebApp: Request
    WebApp->>API: Business Operation
    API->>Database: Data Query
    Database-->>API: Results
    API-->>WebApp: Response
    WebApp-->>User: Display
```"""
    
    def _generate_fallback_business_process(self) -> str:
        """Generate fallback business process diagram"""
        return """```mermaid
flowchart TD
    Start([Process Start]) --> Validate{{Validation}}
    Validate -->|Valid| Process[Business Logic]
    Validate -->|Invalid| Error[Error Handling]
    Process --> Complete([Complete])
    Error --> End([Terminate])
```"""
    
    def _generate_fallback_migration_roadmap(self) -> str:
        """Generate fallback migration roadmap"""
        return """```mermaid
gantt
    title Migration Roadmap
    dateFormat YYYY-MM-DD
    section Analysis
    System Assessment    :2024-01-01, 4w
    section Migration
    Core Components      :2024-02-01, 8w
    section Testing
    Integration Testing  :2024-04-01, 4w
```"""

# Additional diagram generation methods would continue here...
# Including all the other diagram types mentioned in the comprehensive suite

# Global instance
enhanced_diagram_service = None

def get_enhanced_diagram_service(ai_service: AIService, intelligence_graph: CodeIntelligenceGraph) -> EnhancedDiagramService:
    """Get or create enhanced diagram service instance"""
    global enhanced_diagram_service
    if enhanced_diagram_service is None:
        enhanced_diagram_service = EnhancedDiagramService(ai_service, intelligence_graph)
    return enhanced_diagram_service