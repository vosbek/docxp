"""
CORBA IDL Interface Tracker for Distributed System Analysis

Enhanced CORBA analysis with focus on:
- IDL interface inheritance hierarchies
- Method signature tracing across modules
- Object reference dependencies
- Distributed service boundaries
- Client/Server binding analysis
- Legacy system integration points
"""

import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Set, Optional, Tuple
from dataclasses import dataclass

from app.parsers.base_parser import BaseParser

logger = logging.getLogger(__name__)

@dataclass
class IDLInterface:
    """Represents a CORBA IDL interface with full context"""
    name: str
    module: str
    base_interfaces: List[str]
    methods: List[Dict[str, Any]]
    attributes: List[Dict[str, Any]]
    exceptions: List[str]
    line_number: int
    is_abstract: bool = False

@dataclass
class IDLMethod:
    """Represents an IDL method with signature details"""
    name: str
    return_type: str
    parameters: List[Dict[str, str]]
    exceptions: List[str]
    oneway: bool = False
    line_number: int

@dataclass
class ServiceBinding:
    """Represents a client-server binding relationship"""
    client_interface: str
    server_interface: str
    binding_type: str  # 'inheritance', 'composition', 'reference', 'callback'
    method_calls: List[str]
    dependency_strength: str  # 'strong', 'weak', 'optional'

class CorbaIDLTracer(BaseParser):
    """
    Advanced CORBA IDL interface tracker for distributed system analysis
    
    Provides comprehensive analysis of:
    - Interface hierarchies and dependencies
    - Service boundaries and integration points
    - Method call patterns across modules
    - Object reference flows
    - Legacy modernization opportunities
    """
    
    def __init__(self):
        # IDL syntax patterns
        self.idl_patterns = {
            'module': re.compile(r'module\s+(\w+)\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', re.DOTALL),
            'interface': re.compile(r'interface\s+(\w+)(?:\s*:\s*([^{]+))?\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', re.DOTALL),
            'abstract_interface': re.compile(r'abstract\s+interface\s+(\w+)(?:\s*:\s*([^{]+))?\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', re.DOTALL),
            'method': re.compile(r'(?:(oneway)\s+)?(\w+(?:::\w+)*)\s+(\w+)\s*\(([^)]*)\)(?:\s+raises\s*\(([^)]+)\))?;'),
            'attribute': re.compile(r'(?:(readonly)\s+)?attribute\s+(\w+(?:::\w+)*)\s+(\w+);'),
            'exception': re.compile(r'exception\s+(\w+)\s*\{([^}]*)\}'),
            'struct': re.compile(r'struct\s+(\w+)\s*\{([^}]*)\}'),
            'typedef': re.compile(r'typedef\s+([^;]+);'),
            'enum': re.compile(r'enum\s+(\w+)\s*\{([^}]*)\}'),
            'const': re.compile(r'const\s+(\w+)\s+(\w+)\s*=\s*([^;]+);'),
            
            # Type and reference patterns
            'object_ref': re.compile(r'(\w+(?:::\w+)*)(?:\s*<([^>]+)>)?'),
            'parameter': re.compile(r'(in|out|inout)\s+(\w+(?:::\w+)*)\s+(\w+)'),
            'inheritance': re.compile(r'(\w+(?:::\w+)*)(?:\s*,\s*(\w+(?:::\w+)*))*'),
            
            # CORBA specific patterns
            'valuetype': re.compile(r'(?:(abstract|custom)\s+)?valuetype\s+(\w+)(?:\s*:\s*([^{]+))?\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', re.DOTALL),
            'eventtype': re.compile(r'(?:(abstract|custom)\s+)?eventtype\s+(\w+)(?:\s*:\s*([^{]+))?\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', re.DOTALL),
            'native': re.compile(r'native\s+(\w+);'),
        }
        
        # Comment removal
        self.comment_patterns = {
            'line_comment': re.compile(r'//.*$', re.MULTILINE),
            'block_comment': re.compile(r'/\*.*?\*/', re.DOTALL)
        }
        
    def parse(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse IDL file and extract all entities with interface tracking"""
        entities = []
        
        if not self.validate_file(file_path):
            return entities
            
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
                lines = content.split('\n')
            
            # Remove comments
            content = self._remove_comments(content)
            
            # Parse global scope first
            global_entities = self._parse_global_scope(content, lines, file_path)
            entities.extend(global_entities)
            
            # Parse modules and their contents
            modules = self._parse_modules(content, lines, file_path)
            entities.extend(modules)
            
            # Generate interface dependency graph
            interface_deps = self._generate_interface_dependencies(entities)
            entities.extend(interface_deps)
            
            # Generate service binding analysis
            service_bindings = self._analyze_service_bindings(entities)
            entities.extend(service_bindings)
            
        except Exception as e:
            logger.warning(f"Error parsing IDL file {file_path}: {e}")
        
        return entities
    
    def extract_dependencies(self, file_path: Path) -> List[str]:
        """Extract IDL dependencies and imports"""
        dependencies = []
        
        if not self.validate_file(file_path):
            return dependencies
            
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
            
            # Extract #include directives
            include_pattern = re.compile(r'#include\s*[<"]([^>"]+)[>"]')
            for match in include_pattern.finditer(content):
                dependencies.append(match.group(1))
            
            # Extract module references
            module_refs = re.findall(r'(\w+)::', content)
            dependencies.extend(list(set(module_refs)))
            
        except Exception as e:
            logger.warning(f"Error extracting dependencies from {file_path}: {e}")
        
        return list(set(dependencies))
    
    def _remove_comments(self, content: str) -> str:
        """Remove IDL comments"""
        # Remove block comments first
        content = self.comment_patterns['block_comment'].sub('', content)
        # Remove line comments
        content = self.comment_patterns['line_comment'].sub('', content)
        return content
    
    def _parse_global_scope(self, content: str, lines: List[str], file_path: Path) -> List[Dict[str, Any]]:
        """Parse global scope elements (outside modules)"""
        entities = []
        
        # Find content outside modules
        module_content = ""
        for match in self.idl_patterns['module'].finditer(content):
            module_content += match.group(0)
        
        # Remove module content to get global content
        global_content = content
        for match in self.idl_patterns['module'].finditer(content):
            global_content = global_content.replace(match.group(0), '', 1)
        
        # Parse global interfaces
        interfaces = self._parse_interfaces(global_content, lines, file_path, "")
        entities.extend(interfaces)
        
        # Parse global types
        types = self._parse_types(global_content, lines, file_path, "")
        entities.extend(types)
        
        return entities
    
    def _parse_modules(self, content: str, lines: List[str], file_path: Path) -> List[Dict[str, Any]]:
        """Parse IDL modules and their contents"""
        entities = []
        
        for match in self.idl_patterns['module'].finditer(content):
            module_name = match.group(1)
            module_content = match.group(2)
            line_num = self._get_line_number(content, match.start(), lines)
            
            # Create module entity
            module_entity = self.create_entity(
                name=module_name,
                entity_type='idl_module',
                file_path=str(file_path),
                line_number=line_num,
                module_content_length=len(module_content),
                framework='CORBA'
            )
            entities.append(module_entity)
            
            # Parse module contents
            module_lines = module_content.split('\n')
            
            # Parse interfaces within module
            interfaces = self._parse_interfaces(module_content, module_lines, file_path, module_name)
            entities.extend(interfaces)
            
            # Parse types within module
            types = self._parse_types(module_content, module_lines, file_path, module_name)
            entities.extend(types)
        
        return entities
    
    def _parse_interfaces(self, content: str, lines: List[str], file_path: Path, module_name: str) -> List[Dict[str, Any]]:
        """Parse IDL interfaces with full signature analysis"""
        entities = []
        
        # Parse regular interfaces
        for match in self.idl_patterns['interface'].finditer(content):
            interface = self._parse_single_interface(match, content, lines, file_path, module_name, False)
            entities.append(interface)
        
        # Parse abstract interfaces
        for match in self.idl_patterns['abstract_interface'].finditer(content):
            interface = self._parse_single_interface(match, content, lines, file_path, module_name, True)
            entities.append(interface)
        
        # Parse valuetypes (CORBA 3.x)
        for match in self.idl_patterns['valuetype'].finditer(content):
            valuetype = self._parse_valuetype(match, content, lines, file_path, module_name)
            entities.append(valuetype)
        
        return entities
    
    def _parse_single_interface(self, match: re.Match, content: str, lines: List[str], 
                               file_path: Path, module_name: str, is_abstract: bool) -> Dict[str, Any]:
        """Parse a single interface definition"""
        interface_name = match.group(1)
        inheritance = match.group(2) if match.group(2) else ""
        interface_body = match.group(3)
        line_num = self._get_line_number(content, match.start(), lines)
        
        # Parse base interfaces
        base_interfaces = []
        if inheritance:
            inheritance_matches = self.idl_patterns['inheritance'].findall(inheritance)
            for inherit_match in inheritance_matches:
                if inherit_match[0]:  # Not empty
                    base_interfaces.append(inherit_match[0].strip())
        
        # Parse methods
        methods = []
        for method_match in self.idl_patterns['method'].finditer(interface_body):
            method = self._parse_method(method_match, interface_body, lines)
            methods.append(method)
        
        # Parse attributes
        attributes = []
        for attr_match in self.idl_patterns['attribute'].finditer(interface_body):
            attribute = self._parse_attribute(attr_match)
            attributes.append(attribute)
        
        # Extract exceptions referenced
        exceptions = []
        exception_refs = re.findall(r'raises\s*\(([^)]+)\)', interface_body)
        for exc_ref in exception_refs:
            exceptions.extend([exc.strip() for exc in exc_ref.split(',')])
        
        full_name = f"{module_name}::{interface_name}" if module_name else interface_name
        
        return self.create_entity(
            name=full_name,
            entity_type='idl_interface',
            file_path=str(file_path),
            line_number=line_num,
            interface_name=interface_name,
            module=module_name,
            is_abstract=is_abstract,
            base_interfaces=base_interfaces,
            methods=methods,
            attributes=attributes,
            exceptions=list(set(exceptions)),
            method_count=len(methods),
            attribute_count=len(attributes),
            inheritance_depth=len(base_interfaces),
            framework='CORBA'
        )
    
    def _parse_method(self, match: re.Match, content: str, lines: List[str]) -> Dict[str, Any]:
        """Parse IDL method signature"""
        oneway = match.group(1) is not None
        return_type = match.group(2)
        method_name = match.group(3)
        params_str = match.group(4) if match.group(4) else ""
        raises_str = match.group(5) if match.group(5) else ""
        
        # Parse parameters
        parameters = []
        if params_str.strip():
            for param_match in self.idl_patterns['parameter'].finditer(params_str):
                direction = param_match.group(1)  # in, out, inout
                param_type = param_match.group(2)
                param_name = param_match.group(3)
                
                parameters.append({
                    'direction': direction,
                    'type': param_type,
                    'name': param_name
                })
        
        # Parse exceptions
        exceptions = []
        if raises_str:
            exceptions = [exc.strip() for exc in raises_str.split(',')]
        
        return {
            'name': method_name,
            'return_type': return_type,
            'parameters': parameters,
            'exceptions': exceptions,
            'oneway': oneway,
            'parameter_count': len(parameters),
            'complexity_score': self._calculate_method_complexity(parameters, exceptions, oneway)
        }
    
    def _parse_attribute(self, match: re.Match) -> Dict[str, Any]:
        """Parse IDL attribute"""
        readonly = match.group(1) is not None
        attr_type = match.group(2)
        attr_name = match.group(3)
        
        return {
            'name': attr_name,
            'type': attr_type,
            'readonly': readonly
        }
    
    def _parse_valuetype(self, match: re.Match, content: str, lines: List[str], 
                        file_path: Path, module_name: str) -> Dict[str, Any]:
        """Parse CORBA valuetype"""
        modifiers = match.group(1) if match.group(1) else ""
        valuetype_name = match.group(2)
        inheritance = match.group(3) if match.group(3) else ""
        valuetype_body = match.group(4)
        line_num = self._get_line_number(content, match.start(), lines)
        
        full_name = f"{module_name}::{valuetype_name}" if module_name else valuetype_name
        
        return self.create_entity(
            name=full_name,
            entity_type='idl_valuetype',
            file_path=str(file_path),
            line_number=line_num,
            valuetype_name=valuetype_name,
            module=module_name,
            modifiers=modifiers.split() if modifiers else [],
            inheritance=inheritance.strip() if inheritance else "",
            framework='CORBA'
        )
    
    def _parse_types(self, content: str, lines: List[str], file_path: Path, module_name: str) -> List[Dict[str, Any]]:
        """Parse IDL type definitions"""
        entities = []
        
        # Parse structs
        for match in self.idl_patterns['struct'].finditer(content):
            struct_name = match.group(1)
            struct_body = match.group(2)
            line_num = self._get_line_number(content, match.start(), lines)
            
            full_name = f"{module_name}::{struct_name}" if module_name else struct_name
            
            entity = self.create_entity(
                name=full_name,
                entity_type='idl_struct',
                file_path=str(file_path),
                line_number=line_num,
                struct_name=struct_name,
                module=module_name,
                fields=self._parse_struct_fields(struct_body),
                framework='CORBA'
            )
            entities.append(entity)
        
        # Parse exceptions
        for match in self.idl_patterns['exception'].finditer(content):
            exception_name = match.group(1)
            exception_body = match.group(2)
            line_num = self._get_line_number(content, match.start(), lines)
            
            full_name = f"{module_name}::{exception_name}" if module_name else exception_name
            
            entity = self.create_entity(
                name=full_name,
                entity_type='idl_exception',
                file_path=str(file_path),
                line_number=line_num,
                exception_name=exception_name,
                module=module_name,
                fields=self._parse_struct_fields(exception_body),
                framework='CORBA'
            )
            entities.append(entity)
        
        # Parse enums
        for match in self.idl_patterns['enum'].finditer(content):
            enum_name = match.group(1)
            enum_body = match.group(2)
            line_num = self._get_line_number(content, match.start(), lines)
            
            full_name = f"{module_name}::{enum_name}" if module_name else enum_name
            
            values = [v.strip() for v in enum_body.split(',') if v.strip()]
            
            entity = self.create_entity(
                name=full_name,
                entity_type='idl_enum',
                file_path=str(file_path),
                line_number=line_num,
                enum_name=enum_name,
                module=module_name,
                values=values,
                value_count=len(values),
                framework='CORBA'
            )
            entities.append(entity)
        
        return entities
    
    def _parse_struct_fields(self, struct_body: str) -> List[Dict[str, str]]:
        """Parse struct or exception fields"""
        fields = []
        field_pattern = re.compile(r'(\w+(?:::\w+)*)\s+(\w+);')
        
        for match in field_pattern.finditer(struct_body):
            field_type = match.group(1)
            field_name = match.group(2)
            
            fields.append({
                'type': field_type,
                'name': field_name
            })
        
        return fields
    
    def _generate_interface_dependencies(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate interface dependency relationships"""
        dependencies = []
        
        # Create lookup map of interfaces
        interfaces = {e['name']: e for e in entities if e['type'] == 'idl_interface'}
        
        for interface_name, interface in interfaces.items():
            # Check base interface dependencies
            for base_interface in interface.get('base_interfaces', []):
                dep = self.create_entity(
                    name=f"{interface_name} extends {base_interface}",
                    entity_type='idl_interface_dependency',
                    file_path=interface['file_path'],
                    line_number=interface['line_number'],
                    source_interface=interface_name,
                    target_interface=base_interface,
                    dependency_type='inheritance',
                    strength='strong',
                    framework='CORBA'
                )
                dependencies.append(dep)
            
            # Check method parameter dependencies
            for method in interface.get('methods', []):
                for param in method.get('parameters', []):
                    param_type = param['type']
                    if '::' in param_type or param_type in interfaces:
                        dep = self.create_entity(
                            name=f"{interface_name}.{method['name']} uses {param_type}",
                            entity_type='idl_interface_dependency',
                            file_path=interface['file_path'],
                            line_number=interface['line_number'],
                            source_interface=interface_name,
                            target_interface=param_type,
                            dependency_type='parameter',
                            strength='medium',
                            method_name=method['name'],
                            framework='CORBA'
                        )
                        dependencies.append(dep)
        
        return dependencies
    
    def _analyze_service_bindings(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze service binding patterns for distributed system architecture"""
        bindings = []
        
        interfaces = [e for e in entities if e['type'] == 'idl_interface']
        
        # Analyze callback patterns
        for interface in interfaces:
            callback_methods = []
            for method in interface.get('methods', []):
                # Look for callback-style parameters (interfaces passed as parameters)
                for param in method.get('parameters', []):
                    if param['direction'] == 'in' and '::' in param['type']:
                        callback_methods.append(method['name'])
            
            if callback_methods:
                binding = self.create_entity(
                    name=f"Callback Service: {interface['name']}",
                    entity_type='idl_service_binding',
                    file_path=interface['file_path'],
                    line_number=interface['line_number'],
                    service_pattern='callback',
                    interface_name=interface['name'],
                    callback_methods=callback_methods,
                    binding_strength='strong',
                    modernization_priority='high',
                    framework='CORBA'
                )
                bindings.append(binding)
        
        return bindings
    
    def _calculate_method_complexity(self, parameters: List[Dict], exceptions: List[str], oneway: bool) -> int:
        """Calculate method complexity score"""
        complexity = 1  # Base complexity
        complexity += len(parameters)  # Parameter complexity
        complexity += len(exceptions)  # Exception handling complexity
        
        # Oneway methods are simpler (no return handling)
        if oneway:
            complexity -= 1
        
        # Complex parameter types increase complexity
        for param in parameters:
            if param['direction'] in ['out', 'inout']:
                complexity += 1
            if '::' in param['type']:  # Custom type
                complexity += 1
        
        return max(1, complexity)
    
    def _get_line_number(self, content: str, position: int, lines: List[str]) -> int:
        """Get line number for a position in content"""
        line_num = content[:position].count('\n') + 1
        return min(line_num, len(lines))
    
    def get_distributed_system_analysis(self, idl_files: List[Path]) -> Dict[str, Any]:
        """
        Perform comprehensive distributed system analysis across multiple IDL files
        
        Returns analysis of service boundaries, integration patterns, and modernization opportunities
        """
        all_interfaces = []
        all_dependencies = []
        modules = set()
        
        # Parse all IDL files
        for idl_file in idl_files:
            entities = self.parse(idl_file)
            
            for entity in entities:
                if entity['type'] == 'idl_interface':
                    all_interfaces.append(entity)
                    modules.add(entity.get('module', 'global'))
                elif entity['type'] == 'idl_interface_dependency':
                    all_dependencies.append(entity)
        
        # Analyze service boundaries
        service_boundaries = {}
        for module in modules:
            module_interfaces = [i for i in all_interfaces if i.get('module') == module]
            service_boundaries[module] = {
                'interface_count': len(module_interfaces),
                'total_methods': sum(len(i.get('methods', [])) for i in module_interfaces),
                'complexity_score': sum(
                    sum(m.get('complexity_score', 1) for m in i.get('methods', []))
                    for i in module_interfaces
                )
            }
        
        # Identify integration patterns
        integration_patterns = []
        callback_interfaces = [i for i in all_interfaces 
                             if any('callback' in m['name'].lower() for m in i.get('methods', []))]
        
        if callback_interfaces:
            integration_patterns.append('event_driven_callbacks')
        
        # Modernization assessment
        modernization_score = self._calculate_modernization_score(all_interfaces, all_dependencies)
        
        return {
            'total_interfaces': len(all_interfaces),
            'total_modules': len(modules),
            'service_boundaries': service_boundaries,
            'integration_patterns': integration_patterns,
            'dependency_count': len(all_dependencies),
            'modernization_score': modernization_score,
            'recommendations': self._generate_modernization_recommendations(all_interfaces, service_boundaries)
        }
    
    def _calculate_modernization_score(self, interfaces: List[Dict], dependencies: List[Dict]) -> Dict[str, Any]:
        """Calculate modernization complexity score"""
        total_complexity = sum(
            sum(m.get('complexity_score', 1) for m in interface.get('methods', []))
            for interface in interfaces
        )
        
        strong_dependencies = len([d for d in dependencies if d.get('strength') == 'strong'])
        
        return {
            'complexity_score': total_complexity,
            'coupling_score': strong_dependencies,
            'modernization_difficulty': 'high' if total_complexity > 100 else 'medium' if total_complexity > 50 else 'low'
        }
    
    def _generate_modernization_recommendations(self, interfaces: List[Dict], boundaries: Dict) -> List[str]:
        """Generate modernization recommendations"""
        recommendations = []
        
        # Check for overly complex interfaces
        complex_interfaces = [i for i in interfaces if len(i.get('methods', [])) > 20]
        if complex_interfaces:
            recommendations.append(f"Consider breaking down {len(complex_interfaces)} complex interfaces into smaller services")
        
        # Check for callback patterns
        callback_count = sum(1 for i in interfaces 
                           if any('callback' in m['name'].lower() for m in i.get('methods', [])))
        if callback_count > 0:
            recommendations.append(f"Modernize {callback_count} callback interfaces to event-driven architecture")
        
        # Check module organization
        if len(boundaries) > 10:
            recommendations.append("Consider consolidating modules for better service boundaries")
        
        return recommendations