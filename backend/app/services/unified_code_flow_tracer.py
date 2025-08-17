"""
Unified Code Flow Visualization with Cross-Technology Tracing

Integrates all language-specific tracers to provide comprehensive code flow analysis:
- JSP EL → Java Action → Result JSP flows
- Struts Action → Service → Database patterns
- CORBA Interface → Implementation mappings
- Angular Component → Service → HTTP API chains
- Cross-technology integration points
- End-to-end request flow visualization
"""

import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Set, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque

from app.parsers.jsp_el_tracer import JSPELTracer
from app.parsers.struts_action_tracer import StrutsActionTracer
from app.parsers.corba_idl_tracer import CorbaIDLTracer
from app.parsers.angular_dependency_tracer import AngularDependencyTracer

logger = logging.getLogger(__name__)

@dataclass
class FlowNode:
    """Represents a node in the code flow graph"""
    id: str
    name: str
    type: str  # 'jsp', 'action', 'service', 'component', 'interface', 'endpoint'
    technology: str  # 'JSP', 'Struts', 'Angular', 'CORBA', 'Java'
    file_path: str
    line_number: int
    metadata: Dict[str, Any]

@dataclass
class FlowEdge:
    """Represents a connection between flow nodes"""
    source_id: str
    target_id: str
    relationship_type: str  # 'calls', 'forwards_to', 'injects', 'implements', 'renders'
    strength: str  # 'strong', 'medium', 'weak'
    metadata: Dict[str, Any]

@dataclass
class CodeFlowPath:
    """Represents a complete end-to-end flow path"""
    path_id: str
    name: str
    start_node: str
    end_node: str
    nodes: List[str]
    edges: List[str]
    technologies: List[str]
    flow_type: str  # 'request_response', 'data_flow', 'service_call', 'navigation'
    complexity_score: int

class UnifiedCodeFlowTracer:
    """
    Unified tracer that combines all technology-specific tracers
    
    Provides comprehensive code flow analysis across:
    - Web tier: JSP → Struts → Services
    - Service tier: Java Services → CORBA interfaces
    - Client tier: Angular → HTTP APIs
    - Cross-cutting: Error handling, security, transactions
    """
    
    def __init__(self):
        # Initialize all tracers
        self.jsp_tracer = JSPELTracer()
        self.struts_tracer = StrutsActionTracer()
        self.corba_tracer = CorbaIDLTracer()
        self.angular_tracer = AngularDependencyTracer()
        
        # Flow graph
        self.nodes: Dict[str, FlowNode] = {}
        self.edges: Dict[str, FlowEdge] = {}
        self.paths: Dict[str, CodeFlowPath] = {}
        
        # Technology mappings
        self.technology_nodes = defaultdict(list)
        self.cross_tech_bindings = []
        
    def analyze_codebase(self, codebase_path: Path) -> Dict[str, Any]:
        """
        Perform comprehensive codebase analysis with unified flow tracing
        
        Returns complete flow analysis with cross-technology mappings
        """
        logger.info(f"🔍 Starting unified code flow analysis of {codebase_path}")
        
        # Clear previous analysis
        self._reset_analysis()
        
        # Discover and categorize files
        file_categories = self._categorize_files(codebase_path)
        
        # Analyze each technology
        jsp_analysis = self._analyze_jsp_files(file_categories.get('jsp', []))
        struts_analysis = self._analyze_struts_files(file_categories.get('struts', []))
        angular_analysis = self._analyze_angular_files(file_categories.get('angular', []))
        corba_analysis = self._analyze_corba_files(file_categories.get('corba', []))
        
        # Build unified flow graph
        self._build_flow_graph(jsp_analysis, struts_analysis, angular_analysis, corba_analysis)
        
        # Identify cross-technology integration points
        integration_points = self._identify_integration_points()
        
        # Generate end-to-end flow paths
        flow_paths = self._generate_flow_paths()
        
        # Analyze architectural patterns
        architectural_patterns = self._analyze_architectural_patterns()
        
        # Generate modernization recommendations
        modernization_recommendations = self._generate_modernization_recommendations()
        
        analysis_result = {
            'summary': {
                'total_nodes': len(self.nodes),
                'total_edges': len(self.edges),
                'total_paths': len(flow_paths),
                'technologies': list(self.technology_nodes.keys()),
                'integration_points': len(integration_points)
            },
            'technology_analysis': {
                'jsp': jsp_analysis,
                'struts': struts_analysis,
                'angular': angular_analysis,
                'corba': corba_analysis
            },
            'flow_graph': {
                'nodes': [asdict(node) for node in self.nodes.values()],
                'edges': [asdict(edge) for edge in self.edges.values()],
                'technology_distribution': {
                    tech: len(nodes) for tech, nodes in self.technology_nodes.items()
                }
            },
            'integration_points': integration_points,
            'flow_paths': [asdict(path) for path in flow_paths],
            'architectural_patterns': architectural_patterns,
            'modernization_recommendations': modernization_recommendations
        }
        
        logger.info(f"✅ Unified analysis complete: {len(self.nodes)} nodes, {len(self.edges)} edges, {len(flow_paths)} paths")
        
        return analysis_result
    
    def _reset_analysis(self):
        """Reset analysis state"""
        self.nodes.clear()
        self.edges.clear()
        self.paths.clear()
        self.technology_nodes.clear()
        self.cross_tech_bindings.clear()
    
    def _categorize_files(self, codebase_path: Path) -> Dict[str, List[Path]]:
        """Categorize files by technology"""
        categories = {
            'jsp': [],
            'struts': [],
            'angular': [],
            'corba': [],
            'java': []
        }
        
        for file_path in codebase_path.rglob('*'):
            if not file_path.is_file():
                continue
                
            suffix = file_path.suffix.lower()
            name = file_path.name.lower()
            
            # JSP files
            if suffix == '.jsp':
                categories['jsp'].append(file_path)
            
            # Struts configuration files
            elif 'struts' in name and suffix == '.xml':
                categories['struts'].append(file_path)
            
            # Angular files
            elif suffix in ['.component.ts', '.service.ts', '.module.ts'] or 'angular' in str(file_path):
                categories['angular'].append(file_path)
            
            # CORBA IDL files
            elif suffix == '.idl':
                categories['corba'].append(file_path)
            
            # Java files (for Struts actions)
            elif suffix == '.java':
                categories['java'].append(file_path)
                if 'action' in name or 'Action' in file_path.stem:
                    categories['struts'].append(file_path)
        
        return categories
    
    def _analyze_jsp_files(self, jsp_files: List[Path]) -> Dict[str, Any]:
        """Analyze JSP files and extract entities"""
        logger.info(f"📄 Analyzing {len(jsp_files)} JSP files")
        
        jsp_entities = []
        cross_references = {}
        
        for jsp_file in jsp_files:
            try:
                entities = self.jsp_tracer.parse(jsp_file)
                jsp_entities.extend(entities)
                
                # Add nodes to flow graph
                for entity in entities:
                    node_id = f"jsp_{entity['name']}_{entity['line_number']}"
                    node = FlowNode(
                        id=node_id,
                        name=entity['name'],
                        type='jsp_element',
                        technology='JSP',
                        file_path=entity['file_path'],
                        line_number=entity['line_number'],
                        metadata=entity
                    )
                    self.nodes[node_id] = node
                    self.technology_nodes['JSP'].append(node_id)
                
                # Get cross-references
                cross_refs = self.jsp_tracer.get_cross_references(jsp_file)
                if cross_refs:
                    cross_references[str(jsp_file)] = cross_refs
                    
            except Exception as e:
                logger.warning(f"Error analyzing JSP file {jsp_file}: {e}")
        
        return {
            'file_count': len(jsp_files),
            'entity_count': len(jsp_entities),
            'cross_references': cross_references,
            'entities': jsp_entities
        }
    
    def _analyze_struts_files(self, struts_files: List[Path]) -> Dict[str, Any]:
        """Analyze Struts configuration and Action files"""
        logger.info(f"🏗️ Analyzing {len(struts_files)} Struts files")
        
        struts_entities = []
        action_flows = {}
        
        for struts_file in struts_files:
            try:
                entities = self.struts_tracer.parse(struts_file)
                struts_entities.extend(entities)
                
                # Add nodes to flow graph
                for entity in entities:
                    node_id = f"struts_{entity['name']}_{entity['line_number']}"
                    
                    # Determine node type
                    if entity['type'].endswith('_action_mapping'):
                        node_type = 'action_mapping'
                    elif entity['type'].endswith('_action_flow'):
                        node_type = 'action_flow'
                    elif entity['type'] == 'struts_action_method':
                        node_type = 'action_method'
                    else:
                        node_type = 'struts_element'
                    
                    node = FlowNode(
                        id=node_id,
                        name=entity['name'],
                        type=node_type,
                        technology='Struts',
                        file_path=entity['file_path'],
                        line_number=entity['line_number'],
                        metadata=entity
                    )
                    self.nodes[node_id] = node
                    self.technology_nodes['Struts'].append(node_id)
                
                # Get action flow mappings
                if struts_file.suffix == '.xml':
                    flows = self.struts_tracer.get_action_flow_map(struts_file.parent)
                    action_flows.update(flows)
                    
            except Exception as e:
                logger.warning(f"Error analyzing Struts file {struts_file}: {e}")
        
        return {
            'file_count': len(struts_files),
            'entity_count': len(struts_entities),
            'action_flows': {k: asdict(v) for k, v in action_flows.items()},
            'entities': struts_entities
        }
    
    def _analyze_angular_files(self, angular_files: List[Path]) -> Dict[str, Any]:
        """Analyze Angular files and extract dependencies"""
        logger.info(f"🅰️ Analyzing {len(angular_files)} Angular files")
        
        angular_entities = []
        component_service_map = {}
        
        for angular_file in angular_files:
            try:
                entities = self.angular_tracer.parse(angular_file)
                angular_entities.extend(entities)
                
                # Add nodes to flow graph
                for entity in entities:
                    node_id = f"angular_{entity['name']}_{entity['line_number']}"
                    
                    # Determine node type
                    if entity['type'] == 'angular_component':
                        node_type = 'component'
                    elif entity['type'] == 'angular_service':
                        node_type = 'service'
                    elif entity['type'] == 'angular_dependency_relationship':
                        node_type = 'dependency'
                    else:
                        node_type = 'angular_element'
                    
                    node = FlowNode(
                        id=node_id,
                        name=entity['name'],
                        type=node_type,
                        technology='Angular',
                        file_path=entity['file_path'],
                        line_number=entity['line_number'],
                        metadata=entity
                    )
                    self.nodes[node_id] = node
                    self.technology_nodes['Angular'].append(node_id)
                    
            except Exception as e:
                logger.warning(f"Error analyzing Angular file {angular_file}: {e}")
        
        # Get component-service mappings
        if angular_files:
            component_service_map = self.angular_tracer.get_component_service_map(angular_files)
        
        return {
            'file_count': len(angular_files),
            'entity_count': len(angular_entities),
            'component_service_map': component_service_map,
            'entities': angular_entities
        }
    
    def _analyze_corba_files(self, corba_files: List[Path]) -> Dict[str, Any]:
        """Analyze CORBA IDL files"""
        logger.info(f"🌐 Analyzing {len(corba_files)} CORBA files")
        
        corba_entities = []
        distributed_analysis = {}
        
        for corba_file in corba_files:
            try:
                entities = self.corba_tracer.parse(corba_file)
                corba_entities.extend(entities)
                
                # Add nodes to flow graph
                for entity in entities:
                    node_id = f"corba_{entity['name']}_{entity['line_number']}"
                    
                    # Determine node type
                    if entity['type'] == 'idl_interface':
                        node_type = 'interface'
                    elif entity['type'] == 'idl_module':
                        node_type = 'module'
                    elif entity['type'] == 'idl_service_binding':
                        node_type = 'service_binding'
                    else:
                        node_type = 'corba_element'
                    
                    node = FlowNode(
                        id=node_id,
                        name=entity['name'],
                        type=node_type,
                        technology='CORBA',
                        file_path=entity['file_path'],
                        line_number=entity['line_number'],
                        metadata=entity
                    )
                    self.nodes[node_id] = node
                    self.technology_nodes['CORBA'].append(node_id)
                    
            except Exception as e:
                logger.warning(f"Error analyzing CORBA file {corba_file}: {e}")
        
        # Get distributed system analysis
        if corba_files:
            distributed_analysis = self.corba_tracer.get_distributed_system_analysis(corba_files)
        
        return {
            'file_count': len(corba_files),
            'entity_count': len(corba_entities),
            'distributed_analysis': distributed_analysis,
            'entities': corba_entities
        }
    
    def _build_flow_graph(self, jsp_analysis: Dict, struts_analysis: Dict, 
                         angular_analysis: Dict, corba_analysis: Dict):
        """Build unified flow graph with cross-technology edges"""
        logger.info("🔗 Building unified flow graph")
        
        # Create edges within each technology
        self._create_jsp_edges(jsp_analysis)
        self._create_struts_edges(struts_analysis)
        self._create_angular_edges(angular_analysis)
        self._create_corba_edges(corba_analysis)
        
        # Create cross-technology edges
        self._create_cross_technology_edges(jsp_analysis, struts_analysis, angular_analysis)
    
    def _create_jsp_edges(self, jsp_analysis: Dict):
        """Create edges for JSP element relationships"""
        # Connect JSP forms to actions
        for entity in jsp_analysis.get('entities', []):
            if entity['type'] == 'jsp_java_binding' and entity.get('binding_type') == 'action_forward':
                source_id = f"jsp_{entity['name']}_{entity['line_number']}"
                
                # Find matching Struts action
                target_action = entity.get('java_reference', '')
                if target_action:
                    edge_id = f"edge_{source_id}_to_action_{target_action}"
                    edge = FlowEdge(
                        source_id=source_id,
                        target_id=f"action_{target_action}",
                        relationship_type='forwards_to',
                        strength='strong',
                        metadata={'action_path': target_action}
                    )
                    self.edges[edge_id] = edge
    
    def _create_struts_edges(self, struts_analysis: Dict):
        """Create edges for Struts action flows"""
        for entity in struts_analysis.get('entities', []):
            if entity['type'].endswith('_action_flow'):
                source_action = entity.get('source_action', '')
                target_jsp = entity.get('target_jsp', '')
                
                if source_action and target_jsp:
                    edge_id = f"edge_{source_action}_to_{target_jsp}"
                    edge = FlowEdge(
                        source_id=f"action_{source_action}",
                        target_id=f"jsp_{target_jsp}",
                        relationship_type='forwards_to',
                        strength='strong',
                        metadata={
                            'flow_type': entity.get('flow_type', ''),
                            'result_type': entity.get('result_type', '')
                        }
                    )
                    self.edges[edge_id] = edge
    
    def _create_angular_edges(self, angular_analysis: Dict):
        """Create edges for Angular dependencies"""
        for entity in angular_analysis.get('entities', []):
            if entity['type'] == 'angular_dependency_relationship':
                source_id = f"angular_{entity['source_class']}_{entity['line_number']}"
                target_id = f"angular_{entity['target_service']}_service"
                
                edge_id = f"edge_{source_id}_to_{target_id}"
                edge = FlowEdge(
                    source_id=source_id,
                    target_id=target_id,
                    relationship_type='injects',
                    strength=entity.get('binding_strength', 'medium'),
                    metadata={'dependency_type': entity.get('dependency_type', '')}
                )
                self.edges[edge_id] = edge
    
    def _create_corba_edges(self, corba_analysis: Dict):
        """Create edges for CORBA interface relationships"""
        for entity in corba_analysis.get('entities', []):
            if entity['type'] == 'idl_interface_dependency':
                source_interface = entity.get('source_interface', '')
                target_interface = entity.get('target_interface', '')
                
                if source_interface and target_interface:
                    edge_id = f"edge_{source_interface}_to_{target_interface}"
                    edge = FlowEdge(
                        source_id=f"corba_{source_interface}_interface",
                        target_id=f"corba_{target_interface}_interface",
                        relationship_type='depends_on',
                        strength=entity.get('strength', 'medium'),
                        metadata={'dependency_type': entity.get('dependency_type', '')}
                    )
                    self.edges[edge_id] = edge
    
    def _create_cross_technology_edges(self, jsp_analysis: Dict, struts_analysis: Dict, angular_analysis: Dict):
        """Create edges between different technologies"""
        # Connect JSP to Struts actions
        for jsp_entity in jsp_analysis.get('entities', []):
            if jsp_entity['type'] == 'jsp_java_binding':
                action_ref = jsp_entity.get('java_reference', '')
                
                # Find matching Struts action
                for struts_entity in struts_analysis.get('entities', []):
                    if struts_entity['type'].endswith('_action_mapping'):
                        action_path = struts_entity.get('action_path', '')
                        if action_ref == action_path:
                            # Create cross-technology edge
                            self.cross_tech_bindings.append({
                                'source_tech': 'JSP',
                                'target_tech': 'Struts',
                                'source_entity': jsp_entity['name'],
                                'target_entity': struts_entity['name'],
                                'binding_type': 'action_forward'
                            })
        
        # Connect Angular HTTP services to backend APIs
        for angular_entity in angular_analysis.get('entities', []):
            if angular_entity['type'] == 'angular_service':
                endpoints = angular_entity.get('http_endpoints', [])
                for endpoint in endpoints:
                    # Check if endpoint matches known Struts actions
                    endpoint_path = endpoint.get('endpoint', '')
                    for struts_entity in struts_analysis.get('entities', []):
                        if struts_entity['type'].endswith('_action_mapping'):
                            action_path = struts_entity.get('action_path', '')
                            if endpoint_path.endswith(action_path):
                                self.cross_tech_bindings.append({
                                    'source_tech': 'Angular',
                                    'target_tech': 'Struts',
                                    'source_entity': angular_entity['name'],
                                    'target_entity': struts_entity['name'],
                                    'binding_type': 'http_api_call'
                                })
    
    def _identify_integration_points(self) -> List[Dict[str, Any]]:
        """Identify cross-technology integration points"""
        integration_points = []
        
        # Add cross-technology bindings as integration points
        for binding in self.cross_tech_bindings:
            integration_points.append({
                'type': 'cross_technology_binding',
                'source_technology': binding['source_tech'],
                'target_technology': binding['target_tech'],
                'binding_type': binding['binding_type'],
                'source_entity': binding['source_entity'],
                'target_entity': binding['target_entity'],
                'integration_complexity': self._calculate_integration_complexity(binding)
            })
        
        # Identify potential modernization bridges
        for tech in ['JSP', 'Struts']:
            if tech in self.technology_nodes and 'Angular' in self.technology_nodes:
                integration_points.append({
                    'type': 'modernization_opportunity',
                    'legacy_technology': tech,
                    'modern_technology': 'Angular',
                    'migration_priority': 'high' if tech == 'JSP' else 'medium',
                    'affected_components': len(self.technology_nodes[tech])
                })
        
        return integration_points
    
    def _generate_flow_paths(self) -> List[CodeFlowPath]:
        """Generate end-to-end flow paths through the system"""
        flow_paths = []
        
        # Find JSP → Struts → JSP flows
        jsp_nodes = [node_id for node_id in self.technology_nodes.get('JSP', []) 
                    if 'form' in self.nodes[node_id].name.lower()]
        
        for jsp_start in jsp_nodes:
            paths = self._find_paths_from_node(jsp_start, max_depth=5)
            for path in paths:
                if len(path) >= 3:  # At least JSP → Action → JSP
                    flow_path = CodeFlowPath(
                        path_id=f"flow_{len(flow_paths)}",
                        name=f"Flow from {self.nodes[path[0]].name}",
                        start_node=path[0],
                        end_node=path[-1],
                        nodes=path,
                        edges=[],  # Would need to calculate edges in path
                        technologies=list(set(self.nodes[node_id].technology for node_id in path)),
                        flow_type='request_response',
                        complexity_score=len(path)
                    )
                    flow_paths.append(flow_path)
        
        # Find Angular → Backend API flows
        angular_components = [node_id for node_id in self.technology_nodes.get('Angular', [])
                            if self.nodes[node_id].type == 'component']
        
        for component in angular_components:
            backend_paths = self._find_cross_tech_paths(component, 'Struts')
            for path in backend_paths:
                flow_path = CodeFlowPath(
                    path_id=f"api_flow_{len(flow_paths)}",
                    name=f"API flow from {self.nodes[path[0]].name}",
                    start_node=path[0],
                    end_node=path[-1],
                    nodes=path,
                    edges=[],
                    technologies=['Angular', 'Struts'],
                    flow_type='api_call',
                    complexity_score=len(path) + 2  # API calls are more complex
                )
                flow_paths.append(flow_path)
        
        return flow_paths[:20]  # Limit to prevent overwhelming output
    
    def _find_paths_from_node(self, start_node: str, max_depth: int = 5) -> List[List[str]]:
        """Find all paths from a starting node using BFS"""
        paths = []
        queue = deque([(start_node, [start_node])])
        visited = set()
        
        while queue and len(paths) < 100:  # Limit paths to prevent explosion
            current_node, path = queue.popleft()
            
            if len(path) > max_depth:
                continue
            
            # Find outgoing edges
            outgoing_edges = [edge for edge in self.edges.values() 
                            if edge.source_id == current_node]
            
            if not outgoing_edges:
                # End of path
                if len(path) > 1:
                    paths.append(path)
            else:
                for edge in outgoing_edges:
                    target_node = edge.target_id
                    if target_node not in path:  # Avoid cycles
                        new_path = path + [target_node]
                        queue.append((target_node, new_path))
        
        return paths
    
    def _find_cross_tech_paths(self, start_node: str, target_tech: str) -> List[List[str]]:
        """Find paths from one technology to another"""
        paths = []
        
        # This is a simplified implementation
        # In practice, would use the cross_tech_bindings to find connections
        for binding in self.cross_tech_bindings:
            if (binding['source_tech'] == self.nodes[start_node].technology and 
                binding['target_tech'] == target_tech):
                # Create a simple 2-node path
                target_nodes = [node_id for node_id in self.technology_nodes[target_tech]
                              if binding['target_entity'] in self.nodes[node_id].name]
                if target_nodes:
                    paths.append([start_node, target_nodes[0]])
        
        return paths
    
    def _analyze_architectural_patterns(self) -> Dict[str, Any]:
        """Analyze architectural patterns in the codebase"""
        patterns = {
            'mvc_pattern': self._detect_mvc_pattern(),
            'layered_architecture': self._detect_layered_architecture(),
            'service_oriented': self._detect_service_orientation(),
            'microservices_ready': self._assess_microservices_readiness()
        }
        
        return patterns
    
    def _detect_mvc_pattern(self) -> Dict[str, Any]:
        """Detect MVC pattern implementation"""
        jsp_count = len(self.technology_nodes.get('JSP', []))
        struts_count = len(self.technology_nodes.get('Struts', []))
        
        return {
            'detected': jsp_count > 0 and struts_count > 0,
            'view_components': jsp_count,
            'controller_components': struts_count,
            'pattern_completeness': 'complete' if jsp_count > 0 and struts_count > 0 else 'partial'
        }
    
    def _detect_layered_architecture(self) -> Dict[str, Any]:
        """Detect layered architecture"""
        layers = {
            'presentation': len(self.technology_nodes.get('JSP', [])) + len(self.technology_nodes.get('Angular', [])),
            'business': len(self.technology_nodes.get('Struts', [])),
            'integration': len(self.technology_nodes.get('CORBA', []))
        }
        
        return {
            'detected': all(count > 0 for count in layers.values()),
            'layers': layers,
            'layer_separation': 'good' if len(self.cross_tech_bindings) < 10 else 'needs_improvement'
        }
    
    def _detect_service_orientation(self) -> Dict[str, Any]:
        """Detect service-oriented architecture patterns"""
        angular_services = len([node for node in self.technology_nodes.get('Angular', [])
                              if self.nodes[node].type == 'service'])
        corba_interfaces = len([node for node in self.technology_nodes.get('CORBA', [])
                              if self.nodes[node].type == 'interface'])
        
        return {
            'detected': angular_services > 0 or corba_interfaces > 0,
            'frontend_services': angular_services,
            'distributed_interfaces': corba_interfaces,
            'service_maturity': 'high' if corba_interfaces > 5 else 'medium' if angular_services > 5 else 'low'
        }
    
    def _assess_microservices_readiness(self) -> Dict[str, Any]:
        """Assess readiness for microservices architecture"""
        service_boundaries = len(self.technology_nodes)
        cross_cutting_concerns = len(self.cross_tech_bindings)
        
        readiness_score = min(100, max(0, (service_boundaries * 20) - (cross_cutting_concerns * 5)))
        
        return {
            'readiness_score': readiness_score,
            'service_boundaries': service_boundaries,
            'coupling_issues': cross_cutting_concerns,
            'readiness_level': 'high' if readiness_score > 70 else 'medium' if readiness_score > 40 else 'low'
        }
    
    def _generate_modernization_recommendations(self) -> List[Dict[str, Any]]:
        """Generate modernization recommendations based on analysis"""
        recommendations = []
        
        # JSP to Angular migration
        if 'JSP' in self.technology_nodes and 'Angular' in self.technology_nodes:
            jsp_count = len(self.technology_nodes['JSP'])
            recommendations.append({
                'type': 'technology_migration',
                'priority': 'high',
                'source_technology': 'JSP',
                'target_technology': 'Angular',
                'affected_components': jsp_count,
                'recommendation': f"Migrate {jsp_count} JSP components to Angular for better maintainability",
                'effort_estimate': 'high' if jsp_count > 20 else 'medium'
            })
        
        # Struts to Spring Boot migration
        if 'Struts' in self.technology_nodes:
            struts_count = len(self.technology_nodes['Struts'])
            recommendations.append({
                'type': 'framework_modernization',
                'priority': 'medium',
                'source_technology': 'Struts',
                'target_technology': 'Spring Boot',
                'affected_components': struts_count,
                'recommendation': f"Modernize {struts_count} Struts actions to Spring Boot REST APIs",
                'effort_estimate': 'medium' if struts_count < 15 else 'high'
            })
        
        # CORBA to REST API migration
        if 'CORBA' in self.technology_nodes:
            corba_count = len(self.technology_nodes['CORBA'])
            recommendations.append({
                'type': 'integration_modernization',
                'priority': 'high',
                'source_technology': 'CORBA',
                'target_technology': 'REST/GraphQL',
                'affected_components': corba_count,
                'recommendation': f"Replace {corba_count} CORBA interfaces with REST APIs",
                'effort_estimate': 'high'
            })
        
        # Architecture improvements
        if len(self.cross_tech_bindings) > 10:
            recommendations.append({
                'type': 'architecture_improvement',
                'priority': 'medium',
                'recommendation': f"Reduce coupling between technologies ({len(self.cross_tech_bindings)} integration points)",
                'target_pattern': 'microservices',
                'effort_estimate': 'high'
            })
        
        return recommendations
    
    def _calculate_integration_complexity(self, binding: Dict[str, Any]) -> str:
        """Calculate complexity of cross-technology integration"""
        binding_type = binding['binding_type']
        
        complexity_map = {
            'action_forward': 'medium',
            'http_api_call': 'high',
            'form_submit': 'low',
            'service_call': 'high'
        }
        
        return complexity_map.get(binding_type, 'medium')
    
    def export_flow_visualization(self, output_path: Path, format: str = 'json') -> bool:
        """Export flow visualization data for external tools"""
        try:
            visualization_data = {
                'nodes': [asdict(node) for node in self.nodes.values()],
                'edges': [asdict(edge) for edge in self.edges.values()],
                'paths': [asdict(path) for path in self.paths.values()],
                'technology_summary': {
                    tech: len(nodes) for tech, nodes in self.technology_nodes.items()
                },
                'integration_points': len(self.cross_tech_bindings),
                'metadata': {
                    'generated_at': str(datetime.now()),
                    'total_nodes': len(self.nodes),
                    'total_edges': len(self.edges)
                }
            }
            
            if format == 'json':
                with open(output_path, 'w') as f:
                    json.dump(visualization_data, f, indent=2)
            
            logger.info(f"✅ Flow visualization exported to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to export visualization: {e}")
            return False