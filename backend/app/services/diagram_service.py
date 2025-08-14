"""
Enterprise Diagram Generation Service

Creates comprehensive Mermaid diagrams for legacy system migration analysis.
Supports both technical documentation and executive migration planning.
"""

import logging
from typing import List, Dict, Any, Optional
from collections import defaultdict
import re

logger = logging.getLogger(__name__)

class DiagramService:
    """Service for generating various types of diagrams"""
    
    async def generate_class_diagram(self, entities: List[Dict]) -> str:
        """Generate Mermaid class diagram"""
        
        diagram = "classDiagram\n"
        classes = [e for e in entities if e.get('type') == 'class']
        
        # Add classes
        for cls in classes[:30]:  # Limit to prevent huge diagrams
            class_name = cls.get('name', 'Unknown')
            diagram += f"    class {class_name} {{\n"
            
            # Add methods
            methods = cls.get('methods', [])
            for method in methods[:10]:
                diagram += f"        +{method}()\n"
            
            # Add properties
            properties = cls.get('properties', [])
            for prop in properties[:10]:
                diagram += f"        -{prop}\n"
            
            diagram += "    }\n"
            
            # Add relationships
            dependencies = cls.get('dependencies', [])
            for dep in dependencies[:5]:
                if any(c.get('name') == dep for c in classes):
                    diagram += f"    {class_name} --> {dep}\n"
        
        return diagram
    
    async def generate_flow_diagram(self, entities: List[Dict]) -> str:
        """Generate Mermaid flow diagram"""
        
        diagram = "flowchart TD\n"
        
        # Create a simple flow based on function calls
        functions = [e for e in entities if e.get('type') == 'function']
        
        if functions:
            diagram += "    Start([Start])\n"
            
            for i, func in enumerate(functions[:20]):
                func_name = func.get('name', f'Function{i}')
                func_id = f"F{i}"
                
                diagram += f"    {func_id}[{func_name}]\n"
                
                if i == 0:
                    diagram += f"    Start --> {func_id}\n"
                elif i < len(functions) - 1:
                    diagram += f"    F{i-1} --> {func_id}\n"
            
            diagram += f"    F{min(19, len(functions)-1)} --> End([End])\n"
        
        return diagram

    
    async def generate_architecture_diagram(self, entities: List[Dict]) -> str:
        """Generate Mermaid architecture diagram"""
        
        diagram = "graph TB\n"
        diagram += "    subgraph \"Application Layer\"\n"
        
        # Group entities by file/module
        modules = {}
        for entity in entities:
            file_path = entity.get('file_path', 'unknown')
            module = file_path.split('/')[-1].replace('.py', '').replace('.java', '').replace('.js', '')
            
            if module not in modules:
                modules[module] = []
            modules[module].append(entity)
        
        # Create architecture blocks
        for i, (module, module_entities) in enumerate(list(modules.items())[:15]):
            module_id = f"M{i}"
            diagram += f"        {module_id}[{module}]\n"
        
        diagram += "    end\n"
        
        # Add data layer
        diagram += "    subgraph \"Data Layer\"\n"
        diagram += "        DB[(Database)]\n"
        diagram += "        Cache[(Cache)]\n"
        diagram += "    end\n"
        
        # Add external services
        diagram += "    subgraph \"External Services\"\n"
        diagram += "        API[External APIs]\n"
        diagram += "        Auth[Authentication]\n"
        diagram += "    end\n"
        
        # Add connections
        for i in range(min(5, len(modules))):
            diagram += f"        M{i} --> DB\n"
            if i < 3:
                diagram += f"        M{i} --> API\n"
        
        return diagram
    
    async def generate_sequence_diagram(self, entities: List[Dict]) -> str:
        """Generate Mermaid sequence diagram"""
        
        diagram = "sequenceDiagram\n"
        diagram += "    participant User\n"
        diagram += "    participant API\n"
        diagram += "    participant Service\n"
        diagram += "    participant Database\n\n"
        
        # Create a sample sequence
        diagram += "    User->>API: Request\n"
        diagram += "    API->>Service: Process\n"
        diagram += "    Service->>Database: Query\n"
        diagram += "    Database-->>Service: Result\n"
        diagram += "    Service-->>API: Response\n"
        diagram += "    API-->>User: Display\n"
        
        return diagram
    
    async def generate_er_diagram(self, entities: List[Dict]) -> str:
        """Generate Entity Relationship diagram"""
        
        diagram = "erDiagram\n"
        
        # Find classes that might be entities
        classes = [e for e in entities if e.get('type') == 'class']
        
        for cls in classes[:20]:
            class_name = cls.get('name', 'Unknown')
            properties = cls.get('properties', [])
            
            if properties:
                diagram += f"    {class_name} {{\n"
                for prop in properties[:10]:
                    diagram += f"        string {prop}\n"
                diagram += "    }\n"
        
        # Add some relationships
        for i, cls in enumerate(classes[:10]):
            if i > 0:
                diagram += f"    {classes[0].get('name')} ||--o{{ {cls.get('name')} : contains\n"
        
        return diagram

    # ================================
    # ENTERPRISE MIGRATION DIAGRAMS
    # ================================
    
    async def generate_migration_architecture_diagram(self, entities: List[Dict], 
                                                    integration_analysis: Optional[Dict] = None,
                                                    migration_analysis: Optional[Dict] = None) -> str:
        """Generate enterprise migration architecture diagram with technology layers and integration flows"""
        diagram = "graph TB\n"
        
        # Technology layer organization
        frontend_components = []
        backend_components = []
        data_components = []
        integration_components = []
        
        # Categorize components by technology and complexity
        for entity in entities:
            entity_type = entity.get('entity_type', entity.get('type', ''))
            file_path = entity.get('file_path', '')
            complexity = entity.get('complexity', 'Medium')
            
            # Determine component category and styling
            if any(tech in file_path.lower() for tech in ['.js', '.ts', '.html', '.angular', '.jsp']):
                frontend_components.append(self._format_diagram_component(entity, 'frontend', complexity))
            elif any(tech in file_path.lower() for tech in ['.java', '.py', '.corba', '.idl']):
                backend_components.append(self._format_diagram_component(entity, 'backend', complexity))
            elif any(tech in entity_type.lower() for tech in ['database', 'sql', 'query']):
                data_components.append(self._format_diagram_component(entity, 'data', complexity))
        
        # Add integration flows from IntegrationAnalyzer if available
        if integration_analysis and integration_analysis.get('integration_flows'):
            for flow in integration_analysis['integration_flows'][:10]:  # Limit for readability
                confidence = flow.get('confidence_score', 0.5)
                integration_components.append(self._format_integration_flow(flow, confidence))
        
        # Build diagram layers
        if frontend_components:
            diagram += "    subgraph \"Frontend Layer\"\n"
            for comp in frontend_components[:15]:
                diagram += f"        {comp}\n"
            diagram += "    end\n\n"
        
        if backend_components:
            diagram += "    subgraph \"Business Logic Layer\"\n"
            for comp in backend_components[:15]:
                diagram += f"        {comp}\n"
            diagram += "    end\n\n"
        
        if data_components:
            diagram += "    subgraph \"Data Layer\"\n"
            for comp in data_components[:10]:
                diagram += f"        {comp}\n"
            diagram += "    end\n\n"
        
        # Add external services and CORBA legacy systems
        diagram += "    subgraph \"Legacy Systems\"\n"
        diagram += "        CORBA[CORBA Services]:::legacy\n"
        diagram += "        DB_LEGACY[(Legacy Database)]:::legacy\n"
        diagram += "    end\n\n"
        
        diagram += "    subgraph \"Target Modern Architecture\"\n"
        diagram += "        REST_API[REST APIs]:::modern\n"
        diagram += "        MICROSERVICES[Microservices]:::modern\n"
        diagram += "        CLOUD_DB[(Cloud Database)]:::modern\n"
        diagram += "    end\n\n"
        
        # Add integration connections
        if integration_components:
            diagram += "    %% Integration Flows\n"
            for flow in integration_components[:10]:
                diagram += f"    {flow}\n"
        
        # Add migration path arrows
        diagram += "    %% Migration Paths\n"
        diagram += "    CORBA -.-> REST_API\n"
        diagram += "    DB_LEGACY -.-> CLOUD_DB\n"
        
        # Add styling
        diagram += "\n    %% Styling\n"
        diagram += "    classDef legacy fill:#ffcccc,stroke:#ff6666,stroke-width:2px\n"
        diagram += "    classDef modern fill:#ccffcc,stroke:#66ff66,stroke-width:2px\n"
        diagram += "    classDef frontend fill:#cce5ff,stroke:#0066cc,stroke-width:2px\n"
        diagram += "    classDef backend fill:#ffffcc,stroke:#cccc00,stroke-width:2px\n"
        diagram += "    classDef data fill:#ffccff,stroke:#cc00cc,stroke-width:2px\n"
        diagram += "    classDef high-risk fill:#ff9999,stroke:#cc0000,stroke-width:3px\n"
        
        return diagram
    
    async def generate_migration_risk_matrix(self, migration_analysis: Dict) -> str:
        """Generate risk assessment matrix diagram for migration planning"""
        diagram = "graph LR\n"
        
        components = migration_analysis.get('components', [])
        if not components:
            return "graph LR\n    A[No Risk Data Available]"
        
        # Organize components by risk level
        risk_groups = defaultdict(list)
        for comp in components:
            risk_level = comp.risk_level if hasattr(comp, 'risk_level') else comp.get('risk_level', 'Medium')
            complexity = comp.complexity if hasattr(comp, 'complexity') else comp.get('complexity', 'Medium')
            risk_groups[risk_level].append((comp.name if hasattr(comp, 'name') else comp.get('name', 'Unknown'), complexity))
        
        # Create risk matrix quadrants
        diagram += "    subgraph \"Critical Risk - Immediate Action Required\"\n"
        for i, (name, complexity) in enumerate(risk_groups.get('Critical', [])[:8]):
            safe_name = self._sanitize_mermaid_id(name)
            diagram += f"        CR{i}[\"{name}\\n({complexity} complexity)\"]:::critical\n"
        if not risk_groups.get('Critical'):
            diagram += "        CR_NONE[No Critical Risk Components]:::good\n"
        diagram += "    end\n\n"
        
        diagram += "    subgraph \"High Risk - Plan Carefully\"\n"
        for i, (name, complexity) in enumerate(risk_groups.get('High', [])[:8]):
            safe_name = self._sanitize_mermaid_id(name)
            diagram += f"        HR{i}[\"{name}\\n({complexity} complexity)\"]:::high\n"
        diagram += "    end\n\n"
        
        diagram += "    subgraph \"Medium Risk - Standard Process\"\n"
        for i, (name, complexity) in enumerate(risk_groups.get('Medium', [])[:8]):
            safe_name = self._sanitize_mermaid_id(name)
            diagram += f"        MR{i}[\"{name}\\n({complexity} complexity)\"]:::medium\n"
        diagram += "    end\n\n"
        
        diagram += "    subgraph \"Low Risk - Quick Wins\"\n"
        for i, (name, complexity) in enumerate(risk_groups.get('Low', [])[:8]):
            safe_name = self._sanitize_mermaid_id(name)
            diagram += f"        LR{i}[\"{name}\\n({complexity} complexity)\"]:::low\n"
        diagram += "    end\n\n"
        
        # Add styling
        diagram += "    %% Risk Level Styling\n"
        diagram += "    classDef critical fill:#ffcccc,stroke:#cc0000,stroke-width:3px\n"
        diagram += "    classDef high fill:#ffd9cc,stroke:#ff6600,stroke-width:2px\n"
        diagram += "    classDef medium fill:#ffffcc,stroke:#cccc00,stroke-width:2px\n"
        diagram += "    classDef low fill:#ccffcc,stroke:#00cc00,stroke-width:2px\n"
        diagram += "    classDef good fill:#ccffff,stroke:#00cccc,stroke-width:1px\n"
        
        return diagram
    
    async def generate_data_flow_diagram(self, entities: List[Dict], 
                                       database_analysis: Optional[Dict] = None,
                                       integration_analysis: Optional[Dict] = None) -> str:
        """Generate data flow diagram showing data movement across technology boundaries"""
        diagram = "flowchart TD\n"
        
        # Start with user interaction
        diagram += "    USER[👤 User]:::user\n\n"
        
        # Frontend data entry points
        diagram += "    subgraph \"Frontend Data Entry\"\n"
        diagram += "        FORMS[📝 Forms & UI]:::frontend\n"
        diagram += "        ANGULAR[🅰️ Angular Components]:::frontend\n"
        diagram += "        JSP[📄 JSP Pages]:::frontend\n"
        diagram += "    end\n\n"
        
        # API and Service layer
        diagram += "    subgraph \"API & Integration Layer\"\n"
        diagram += "        REST[🔗 REST APIs]:::api\n"
        diagram += "        STRUTS[⚙️ Struts Actions]:::api\n"
        diagram += "        CORBA[🏛️ CORBA Services]:::legacy\n"
        diagram += "    end\n\n"
        
        # Business Logic
        diagram += "    subgraph \"Business Logic\"\n"
        diagram += "        SERVICES[⚡ Java Services]:::backend\n"
        diagram += "        PROCESSORS[🔄 Data Processors]:::backend\n"
        diagram += "        VALIDATION[✅ Validation Logic]:::backend\n"
        diagram += "    end\n\n"
        
        # Data Storage
        diagram += "    subgraph \"Data Persistence\"\n"
        if database_analysis and database_analysis.get('static_analysis', {}).get('tables'):
            table_count = len(database_analysis['static_analysis']['tables'])
            diagram += f"        DB[(🗄️ Database\\n{table_count} tables)]:::database\n"
            
            # Show key tables if available
            tables = database_analysis['static_analysis']['tables'][:3]
            for i, table in enumerate(tables):
                diagram += f"        T{i}[(📊 {table})]:::table\n"
        else:
            diagram += "        DB[(🗄️ Database)]:::database\n"
        
        diagram += "        CACHE[(⚡ Cache)]:::cache\n"
        diagram += "        FILES[📁 File Storage]:::storage\n"
        diagram += "    end\n\n"
        
        # Data flow connections
        diagram += "    %% User Interaction Flows\n"
        diagram += "    USER --> FORMS\n"
        diagram += "    USER --> ANGULAR\n"
        diagram += "    USER --> JSP\n\n"
        
        diagram += "    %% Frontend to API Flows\n"
        diagram += "    FORMS --> REST\n"
        diagram += "    ANGULAR --> REST\n"
        diagram += "    JSP --> STRUTS\n\n"
        
        diagram += "    %% API to Business Logic Flows\n"
        diagram += "    REST --> SERVICES\n"
        diagram += "    STRUTS --> SERVICES\n"
        diagram += "    CORBA --> SERVICES\n\n"
        
        diagram += "    %% Business Logic Processing\n"
        diagram += "    SERVICES --> PROCESSORS\n"
        diagram += "    PROCESSORS --> VALIDATION\n\n"
        
        diagram += "    %% Data Persistence Flows\n"
        diagram += "    VALIDATION --> DB\n"
        diagram += "    SERVICES --> CACHE\n"
        diagram += "    PROCESSORS --> FILES\n\n"
        
        # Add database table connections if available
        if database_analysis and database_analysis.get('static_analysis', {}).get('tables'):
            tables = database_analysis['static_analysis']['tables'][:3]
            for i, table in enumerate(tables):
                diagram += f"    DB --> T{i}\n"
        
        # Add integration analysis flows if available
        if integration_analysis and integration_analysis.get('integration_flows'):
            diagram += "    %% Cross-Technology Integration Flows\n"
            flows = integration_analysis['integration_flows'][:5]
            for i, flow in enumerate(flows):
                confidence = flow.get('confidence_score', 0.5)
                if confidence > 0.7:
                    line_style = "==>"
                elif confidence > 0.4:
                    line_style = "-->"
                else:
                    line_style = "-.->"
                diagram += f"    %% {flow.get('description', 'Integration flow')} (confidence: {confidence:.1f})\n"
        
        # Styling
        diagram += "\n    %% Styling\n"
        diagram += "    classDef user fill:#e1f5fe,stroke:#0277bd,stroke-width:2px\n"
        diagram += "    classDef frontend fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px\n"
        diagram += "    classDef api fill:#fff3e0,stroke:#f57c00,stroke-width:2px\n"
        diagram += "    classDef backend fill:#e8f5e8,stroke:#388e3c,stroke-width:2px\n"
        diagram += "    classDef database fill:#fce4ec,stroke:#c2185b,stroke-width:2px\n"
        diagram += "    classDef legacy fill:#ffebee,stroke:#d32f2f,stroke-width:3px\n"
        diagram += "    classDef table fill:#f1f8e9,stroke:#689f38,stroke-width:1px\n"
        diagram += "    classDef cache fill:#fff8e1,stroke:#fbc02d,stroke-width:1px\n"
        diagram += "    classDef storage fill:#e0f2f1,stroke:#00695c,stroke-width:1px\n"
        
        return diagram
    
    async def generate_technology_integration_map(self, integration_analysis: Dict) -> str:
        """Generate technology integration mapping diagram"""
        diagram = "graph TB\n"
        
        if not integration_analysis:
            return "graph TB\n    A[No Integration Analysis Available]"
        
        # Extract integration data
        tech_breakdown = integration_analysis.get('technology_breakdown', {})
        integration_flows = integration_analysis.get('integration_flows', [])
        
        # Create technology nodes
        diagram += "    subgraph \"Frontend Technologies\"\n"
        angular_calls = tech_breakdown.get('angular_http_calls', 0)
        if angular_calls > 0:
            diagram += f"        ANG[🅰️ Angular\\n{angular_calls} HTTP calls]:::frontend\n"
        
        jquery_calls = tech_breakdown.get('jquery_calls', 0)
        if jquery_calls > 0:
            diagram += f"        JQ[💻 jQuery\\n{jquery_calls} AJAX calls]:::frontend\n"
        
        jsp_forms = tech_breakdown.get('jsp_forms', 0)
        if jsp_forms > 0:
            diagram += f"        JSP[📄 JSP\\n{jsp_forms} forms]:::frontend\n"
        diagram += "    end\n\n"
        
        # API Layer
        diagram += "    subgraph \"API Integration Layer\"\n"
        rest_endpoints = tech_breakdown.get('rest_endpoints', 0)
        if rest_endpoints > 0:
            diagram += f"        REST[🔗 REST APIs\\n{rest_endpoints} endpoints]:::api\n"
        
        struts_actions = tech_breakdown.get('struts_actions', 0)
        if struts_actions > 0:
            diagram += f"        STRUTS[⚙️ Struts Actions\\n{struts_actions} actions]:::api\n"
        diagram += "    end\n\n"
        
        # Backend Services
        diagram += "    subgraph \"Backend Services\"\n"
        java_services = tech_breakdown.get('java_services', 0)
        if java_services > 0:
            diagram += f"        JAVA[☕ Java Services\\n{java_services} services]:::backend\n"
        
        corba_interfaces = tech_breakdown.get('corba_interfaces', 0)
        if corba_interfaces > 0:
            diagram += f"        CORBA[🏛️ CORBA\\n{corba_interfaces} interfaces]:::legacy\n"
        diagram += "    end\n\n"
        
        # Add integration flow connections with confidence indicators
        diagram += "    %% Integration Flows with Confidence Scores\n"
        for i, flow in enumerate(integration_flows[:10]):
            confidence = flow.get('confidence_score', 0.5)
            source = flow.get('source_technology', 'Unknown')
            target = flow.get('target_technology', 'Unknown')
            
            # Map technology names to node IDs
            tech_mapping = {
                'angular': 'ANG', 'jquery': 'JQ', 'jsp': 'JSP',
                'rest': 'REST', 'struts': 'STRUTS',
                'java': 'JAVA', 'corba': 'CORBA'
            }
            
            source_id = tech_mapping.get(source.lower(), source.upper()[:4])
            target_id = tech_mapping.get(target.lower(), target.upper()[:4])
            
            # Choose line style based on confidence
            if confidence > 0.8:
                line_style = "==>"  # Solid thick line
                line_label = f"High confidence ({confidence:.1f})"
            elif confidence > 0.5:
                line_style = "-->"  # Solid line
                line_label = f"Medium confidence ({confidence:.1f})"
            else:
                line_style = "-.->"  # Dotted line
                line_label = f"Low confidence ({confidence:.1f})"
            
            diagram += f"    {source_id} {line_style} {target_id}\n"
        
        # Add migration recommendations
        migration_insights = integration_analysis.get('migration_insights', {})
        if migration_insights:
            diagram += "\n    subgraph \"Migration Recommendations\"\n"
            complexity = migration_insights.get('migration_complexity', 'Medium')
            diagram += f"        REC[📋 Migration Complexity: {complexity}]:::recommendation\n"
            diagram += "    end\n\n"
        
        # Styling
        diagram += "    %% Technology Integration Styling\n"
        diagram += "    classDef frontend fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px\n"
        diagram += "    classDef api fill:#fff3e0,stroke:#ff9800,stroke-width:2px\n"
        diagram += "    classDef backend fill:#e8f5e8,stroke:#4caf50,stroke-width:2px\n"
        diagram += "    classDef legacy fill:#ffebee,stroke:#f44336,stroke-width:3px\n"
        diagram += "    classDef recommendation fill:#f3e5f5,stroke:#9c27b0,stroke-width:2px\n"
        
        return diagram
    
    # ================================
    # HELPER METHODS
    # ================================
    
    def _format_diagram_component(self, entity: Dict, layer_type: str, complexity: str) -> str:
        """Format entity for diagram display with complexity indicators"""
        name = entity.get('name', 'Unknown')
        entity_type = entity.get('entity_type', entity.get('type', ''))
        
        # Sanitize name for Mermaid
        safe_name = self._sanitize_mermaid_id(name)
        
        # Add complexity and type indicators
        if complexity == 'Very High':
            complexity_icon = "🔥"
        elif complexity == 'High':
            complexity_icon = "⚠️"
        elif complexity == 'Medium':
            complexity_icon = "⚡"
        else:
            complexity_icon = "✅"
        
        # Format based on layer type
        if layer_type == 'frontend':
            return f'{safe_name}["{complexity_icon} {name}\\n({entity_type})"]:::frontend'
        elif layer_type == 'backend':
            return f'{safe_name}["{complexity_icon} {name}\\n({entity_type})"]:::backend'
        elif layer_type == 'data':
            return f'{safe_name}[("{complexity_icon} {name}\\n({entity_type})")]:::data'
        else:
            return f'{safe_name}["{complexity_icon} {name}"]'
    
    def _format_integration_flow(self, flow: Dict, confidence: float) -> str:
        """Format integration flow connection"""
        source = flow.get('source', 'Source')
        target = flow.get('target', 'Target')
        
        if confidence > 0.7:
            return f'{self._sanitize_mermaid_id(source)} ==> {self._sanitize_mermaid_id(target)}'
        elif confidence > 0.4:
            return f'{self._sanitize_mermaid_id(source)} --> {self._sanitize_mermaid_id(target)}'
        else:
            return f'{self._sanitize_mermaid_id(source)} -.-> {self._sanitize_mermaid_id(target)}'
    
    def _sanitize_mermaid_id(self, name: str) -> str:
        """Sanitize name for use as Mermaid node ID"""
        # Remove special characters and spaces, limit length
        sanitized = re.sub(r'[^\w]', '_', str(name))
        return sanitized[:20]  # Limit length for readability
