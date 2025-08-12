"""
Diagram generation service for creating Mermaid diagrams
"""

import logging
from typing import List, Dict, Any

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
