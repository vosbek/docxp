"""
Angular Component → Service Dependency Tracer

Advanced Angular application analysis with focus on:
- Component → Service injection patterns
- Service → Service dependencies
- HTTP client usage and API endpoint mapping
- Route dependencies and lazy loading analysis
- Template binding and method call tracing
- Angular lifecycle hook usage
- Cross-component communication patterns
"""

import logging
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Set, Optional, Tuple
from dataclasses import dataclass

from app.parsers.base_parser import BaseParser

logger = logging.getLogger(__name__)

@dataclass
class AngularComponent:
    """Represents an Angular component with dependencies"""
    name: str
    selector: str
    template_url: Optional[str]
    style_urls: List[str]
    injected_services: List[str]
    lifecycle_hooks: List[str]
    input_properties: List[str]
    output_events: List[str]
    methods: List[str]
    template_bindings: List[str]
    route_params: List[str]
    line_number: int

@dataclass
class AngularService:
    """Represents an Angular service with dependencies"""
    name: str
    injectable_scope: str  # 'root', 'platform', 'any', or module name
    injected_services: List[str]
    provided_methods: List[str]
    http_endpoints: List[Dict[str, str]]
    observables: List[str]
    subjects: List[str]
    line_number: int

@dataclass
class ComponentServiceBinding:
    """Represents a component-service relationship"""
    component_name: str
    service_name: str
    injection_type: str  # 'constructor', 'inject_function', 'viewchild'
    usage_methods: List[str]
    binding_strength: str  # 'strong', 'medium', 'weak'

class AngularDependencyTracer(BaseParser):
    """
    Advanced Angular dependency tracer for component architecture analysis
    
    Provides comprehensive analysis of:
    - Component hierarchies and service dependencies
    - Dependency injection patterns
    - HTTP service integration
    - Route and navigation dependencies
    - Template data flow
    - Cross-component communication
    """
    
    def __init__(self):
        # Angular patterns
        self.angular_patterns = {
            # Component patterns
            'component_decorator': re.compile(r'@Component\s*\(\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}\s*\)', re.DOTALL),
            'component_class': re.compile(r'export\s+class\s+(\w+)\s*(?:implements\s+([^{]+))?\s*\{', re.DOTALL),
            
            # Service patterns
            'injectable_decorator': re.compile(r'@Injectable\s*\(\s*\{([^}]*)\}\s*\)', re.DOTALL),
            'service_class': re.compile(r'export\s+class\s+(\w+)\s*\{', re.DOTALL),
            
            # Dependency injection patterns
            'constructor_injection': re.compile(r'constructor\s*\(([^)]+)\)', re.DOTALL),
            'inject_function': re.compile(r'inject\s*\(\s*(\w+)\s*\)'),
            'viewchild_injection': re.compile(r'@ViewChild\s*\(\s*[\'"]?(\w+)[\'"]?\s*\)'),
            
            # HTTP patterns
            'http_call': re.compile(r'this\.http\.(get|post|put|delete|patch)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]'),
            'http_client_import': re.compile(r'HttpClient'),
            
            # Lifecycle hooks
            'lifecycle_hooks': re.compile(r'(ngOnInit|ngOnDestroy|ngOnChanges|ngAfterViewInit|ngAfterContentInit|ngDoCheck|ngAfterViewChecked|ngAfterContentChecked)\s*\(\s*\)'),
            
            # Template bindings
            'property_binding': re.compile(r'\[(\w+)\]'),
            'event_binding': re.compile(r'\((\w+)\)'),
            'two_way_binding': re.compile(r'\[\((\w+)\)\]'),
            'interpolation': re.compile(r'\{\{\s*([^}]+)\s*\}\}'),
            
            # Route patterns
            'route_params': re.compile(r'this\.route\.params|this\.route\.paramMap'),
            'router_navigate': re.compile(r'this\.router\.navigate\s*\(\s*\[([^\]]+)\]'),
            
            # Input/Output decorators
            'input_decorator': re.compile(r'@Input\s*\(\s*[\'"]?(\w*)[\'"]?\s*\)\s*(\w+)'),
            'output_decorator': re.compile(r'@Output\s*\(\s*[\'"]?(\w*)[\'"]?\s*\)\s*(\w+)'),
            
            # Observable patterns
            'observable_declaration': re.compile(r'(\w+)\s*:\s*Observable\s*<'),
            'subject_declaration': re.compile(r'(\w+)\s*:\s*(Subject|BehaviorSubject|ReplaySubject)\s*<'),
            
            # Method declarations
            'method_declaration': re.compile(r'(\w+)\s*\([^)]*\)\s*:\s*\w+\s*\{|(\w+)\s*\([^)]*\)\s*\{'),
        }
        
        # TypeScript/Angular specific patterns
        self.typescript_patterns = {
            'import_statement': re.compile(r'import\s*\{([^}]+)\}\s*from\s*[\'"]([^\'"+]+)[\'"]'),
            'interface_declaration': re.compile(r'export\s+interface\s+(\w+)\s*(?:extends\s+([^{]+))?\s*\{([^}]+)\}', re.DOTALL),
            'type_declaration': re.compile(r'export\s+type\s+(\w+)\s*=\s*([^;]+);'),
            'property_declaration': re.compile(r'(\w+)\s*:\s*([^;=]+)(?:\s*=\s*([^;]+))?;'),
        }
        
        # Attribute parsing
        self.attribute_pattern = re.compile(r'(\w+)\s*:\s*[\'"`]?([^,\'"`\s}]+)[\'"`]?')
        
    def parse(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse Angular file and extract all entities with dependency tracking"""
        entities = []
        
        if not self.validate_file(file_path):
            return entities
            
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
                lines = content.split('\n')
            
            # Determine file type
            if file_path.suffix == '.component.ts' or '@Component' in content:
                # Parse Angular component
                component = self._parse_component(content, lines, file_path)
                if component:
                    entities.append(component)
                    
                    # Parse component template if inline
                    template_bindings = self._parse_template_bindings(content)
                    entities.extend(template_bindings)
                    
            elif file_path.suffix == '.service.ts' or '@Injectable' in content:
                # Parse Angular service
                service = self._parse_service(content, lines, file_path)
                if service:
                    entities.append(service)
                    
            elif file_path.suffix == '.module.ts' or '@NgModule' in content:
                # Parse Angular module
                module = self._parse_module(content, lines, file_path)
                if module:
                    entities.append(module)
                    
            elif file_path.suffix in ['.html', '.component.html']:
                # Parse component template
                template_entities = self._parse_template_file(content, lines, file_path)
                entities.extend(template_entities)
                
            # Parse TypeScript interfaces and types (common to all files)
            interfaces = self._parse_interfaces(content, lines, file_path)
            entities.extend(interfaces)
            
            # Extract dependency relationships
            dependencies = self._extract_dependency_relationships(content, lines, file_path)
            entities.extend(dependencies)
            
        except Exception as e:
            logger.warning(f"Error parsing Angular file {file_path}: {e}")
        
        return entities
    
    def extract_dependencies(self, file_path: Path) -> List[str]:
        """Extract import dependencies from Angular file"""
        dependencies = []
        
        if not self.validate_file(file_path):
            return dependencies
            
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
            
            # Extract import statements
            for match in self.typescript_patterns['import_statement'].finditer(content):
                imports = match.group(1)
                module_path = match.group(2)
                
                # Add module path
                dependencies.append(module_path)
                
                # Add individual imports
                import_items = [item.strip() for item in imports.split(',')]
                dependencies.extend(import_items)
                
        except Exception as e:
            logger.warning(f"Error extracting dependencies from {file_path}: {e}")
        
        return list(set(dependencies))
    
    def _parse_component(self, content: str, lines: List[str], file_path: Path) -> Optional[Dict[str, Any]]:
        """Parse Angular component"""
        # Find component decorator
        component_match = self.angular_patterns['component_decorator'].search(content)
        if not component_match:
            return None
        
        # Find component class
        class_match = self.angular_patterns['component_class'].search(content)
        if not class_match:
            return None
        
        component_name = class_match.group(1)
        implements = class_match.group(2) if class_match.group(2) else ""
        line_num = self._get_line_number(content, class_match.start(), lines)
        
        # Parse component decorator properties
        decorator_content = component_match.group(1)
        selector = self._extract_decorator_property(decorator_content, 'selector')
        template_url = self._extract_decorator_property(decorator_content, 'templateUrl')
        style_urls = self._extract_decorator_array(decorator_content, 'styleUrls')
        
        # Extract injected services
        injected_services = self._extract_constructor_injections(content)
        
        # Extract lifecycle hooks
        lifecycle_hooks = []
        for match in self.angular_patterns['lifecycle_hooks'].finditer(content):
            lifecycle_hooks.append(match.group(1))
        
        # Extract input/output properties
        input_properties = []
        output_events = []
        
        for match in self.angular_patterns['input_decorator'].finditer(content):
            input_name = match.group(1) or match.group(2)
            input_properties.append(input_name)
        
        for match in self.angular_patterns['output_decorator'].finditer(content):
            output_name = match.group(1) or match.group(2)
            output_events.append(output_name)
        
        # Extract methods
        methods = []
        for match in self.angular_patterns['method_declaration'].finditer(content):
            method_name = match.group(1) or match.group(2)
            if method_name and not method_name.startswith('ng'):  # Exclude lifecycle hooks
                methods.append(method_name)
        
        # Extract route parameter usage
        route_params = []
        if self.angular_patterns['route_params'].search(content):
            route_params.append('route_parameters')
        
        return self.create_entity(
            name=component_name,
            entity_type='angular_component',
            file_path=str(file_path),
            line_number=line_num,
            selector=selector,
            template_url=template_url,
            style_urls=style_urls,
            injected_services=injected_services,
            lifecycle_hooks=lifecycle_hooks,
            input_properties=input_properties,
            output_events=output_events,
            methods=methods,
            route_params=route_params,
            implements=implements.split(',') if implements else [],
            service_count=len(injected_services),
            method_count=len(methods),
            framework='Angular'
        )
    
    def _parse_service(self, content: str, lines: List[str], file_path: Path) -> Optional[Dict[str, Any]]:
        """Parse Angular service"""
        # Find injectable decorator
        injectable_match = self.angular_patterns['injectable_decorator'].search(content)
        
        # Find service class
        class_match = self.angular_patterns['service_class'].search(content)
        if not class_match:
            return None
        
        service_name = class_match.group(1)
        line_num = self._get_line_number(content, class_match.start(), lines)
        
        # Parse injectable scope
        injectable_scope = 'root'  # default
        if injectable_match:
            decorator_content = injectable_match.group(1)
            scope = self._extract_decorator_property(decorator_content, 'providedIn')
            if scope:
                injectable_scope = scope
        
        # Extract injected services
        injected_services = self._extract_constructor_injections(content)
        
        # Extract provided methods
        methods = []
        for match in self.angular_patterns['method_declaration'].finditer(content):
            method_name = match.group(1) or match.group(2)
            if method_name:
                methods.append(method_name)
        
        # Extract HTTP endpoints
        http_endpoints = []
        for match in self.angular_patterns['http_call'].finditer(content):
            http_method = match.group(1)
            endpoint = match.group(2)
            http_endpoints.append({
                'method': http_method.upper(),
                'endpoint': endpoint
            })
        
        # Extract observables and subjects
        observables = []
        subjects = []
        
        for match in self.angular_patterns['observable_declaration'].finditer(content):
            observables.append(match.group(1))
        
        for match in self.angular_patterns['subject_declaration'].finditer(content):
            subjects.append(match.group(1))
        
        return self.create_entity(
            name=service_name,
            entity_type='angular_service',
            file_path=str(file_path),
            line_number=line_num,
            injectable_scope=injectable_scope,
            injected_services=injected_services,
            provided_methods=methods,
            http_endpoints=http_endpoints,
            observables=observables,
            subjects=subjects,
            endpoint_count=len(http_endpoints),
            dependency_count=len(injected_services),
            framework='Angular'
        )
    
    def _parse_module(self, content: str, lines: List[str], file_path: Path) -> Optional[Dict[str, Any]]:
        """Parse Angular module"""
        # Find NgModule decorator
        module_pattern = re.compile(r'@NgModule\s*\(\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}\s*\)', re.DOTALL)
        module_match = module_pattern.search(content)
        
        if not module_match:
            return None
        
        # Find module class
        class_match = self.angular_patterns['service_class'].search(content)
        if not class_match:
            return None
        
        module_name = class_match.group(1)
        line_num = self._get_line_number(content, class_match.start(), lines)
        
        # Parse module decorator properties
        decorator_content = module_match.group(1)
        
        declarations = self._extract_decorator_array(decorator_content, 'declarations')
        imports = self._extract_decorator_array(decorator_content, 'imports')
        providers = self._extract_decorator_array(decorator_content, 'providers')
        exports = self._extract_decorator_array(decorator_content, 'exports')
        
        return self.create_entity(
            name=module_name,
            entity_type='angular_module',
            file_path=str(file_path),
            line_number=line_num,
            declarations=declarations,
            imports=imports,
            providers=providers,
            exports=exports,
            component_count=len(declarations),
            import_count=len(imports),
            framework='Angular'
        )
    
    def _parse_template_file(self, content: str, lines: List[str], file_path: Path) -> List[Dict[str, Any]]:
        """Parse Angular template file"""
        entities = []
        
        # Extract property bindings
        for match in self.angular_patterns['property_binding'].finditer(content):
            property_name = match.group(1)
            line_num = self._get_line_number(content, match.start(), lines)
            
            entity = self.create_entity(
                name=f"Property binding: {property_name}",
                entity_type='angular_template_binding',
                file_path=str(file_path),
                line_number=line_num,
                binding_type='property',
                binding_target=property_name,
                framework='Angular'
            )
            entities.append(entity)
        
        # Extract event bindings
        for match in self.angular_patterns['event_binding'].finditer(content):
            event_name = match.group(1)
            line_num = self._get_line_number(content, match.start(), lines)
            
            entity = self.create_entity(
                name=f"Event binding: {event_name}",
                entity_type='angular_template_binding',
                file_path=str(file_path),
                line_number=line_num,
                binding_type='event',
                binding_target=event_name,
                framework='Angular'
            )
            entities.append(entity)
        
        # Extract interpolations
        for match in self.angular_patterns['interpolation'].finditer(content):
            expression = match.group(1).strip()
            line_num = self._get_line_number(content, match.start(), lines)
            
            entity = self.create_entity(
                name=f"Interpolation: {expression}",
                entity_type='angular_template_binding',
                file_path=str(file_path),
                line_number=line_num,
                binding_type='interpolation',
                binding_target=expression,
                framework='Angular'
            )
            entities.append(entity)
        
        return entities
    
    def _parse_template_bindings(self, content: str) -> List[Dict[str, Any]]:
        """Parse inline template bindings"""
        entities = []
        
        # Look for inline template in component
        template_pattern = re.compile(r'template\s*:\s*[`\'"]([^`\'"]*)[`\'"]', re.DOTALL)
        template_match = template_pattern.search(content)
        
        if template_match:
            template_content = template_match.group(1)
            
            # Create a mock file path for template
            template_path = Path("inline_template.html")
            template_lines = template_content.split('\n')
            
            # Parse template content
            template_entities = self._parse_template_file(template_content, template_lines, template_path)
            entities.extend(template_entities)
        
        return entities
    
    def _parse_interfaces(self, content: str, lines: List[str], file_path: Path) -> List[Dict[str, Any]]:
        """Parse TypeScript interfaces"""
        entities = []
        
        for match in self.typescript_patterns['interface_declaration'].finditer(content):
            interface_name = match.group(1)
            extends = match.group(2) if match.group(2) else ""
            interface_body = match.group(3)
            line_num = self._get_line_number(content, match.start(), lines)
            
            # Parse properties
            properties = []
            for prop_match in self.typescript_patterns['property_declaration'].finditer(interface_body):
                prop_name = prop_match.group(1)
                prop_type = prop_match.group(2).strip()
                properties.append({
                    'name': prop_name,
                    'type': prop_type
                })
            
            entity = self.create_entity(
                name=interface_name,
                entity_type='typescript_interface',
                file_path=str(file_path),
                line_number=line_num,
                extends=extends.strip() if extends else "",
                properties=properties,
                property_count=len(properties),
                framework='TypeScript'
            )
            entities.append(entity)
        
        return entities
    
    def _extract_dependency_relationships(self, content: str, lines: List[str], file_path: Path) -> List[Dict[str, Any]]:
        """Extract component-service dependency relationships"""
        relationships = []
        
        # Find component or service name
        class_match = self.angular_patterns['component_class'].search(content)
        if not class_match:
            return relationships
        
        class_name = class_match.group(1)
        
        # Extract constructor injections and create relationships
        injected_services = self._extract_constructor_injections(content)
        
        for service_name in injected_services:
            relationship = self.create_entity(
                name=f"{class_name} → {service_name}",
                entity_type='angular_dependency_relationship',
                file_path=str(file_path),
                line_number=class_match.span()[0],
                source_class=class_name,
                target_service=service_name,
                dependency_type='constructor_injection',
                binding_strength='strong',
                framework='Angular'
            )
            relationships.append(relationship)
        
        return relationships
    
    def _extract_constructor_injections(self, content: str) -> List[str]:
        """Extract services injected through constructor"""
        injected_services = []
        
        constructor_match = self.angular_patterns['constructor_injection'].search(content)
        if constructor_match:
            params = constructor_match.group(1)
            
            # Parse constructor parameters
            param_pattern = re.compile(r'(?:private|public|protected|readonly)?\s*(\w+)\s*:\s*(\w+)')
            for param_match in param_pattern.finditer(params):
                param_name = param_match.group(1)
                param_type = param_match.group(2)
                
                # Service names typically end with 'Service' or are common Angular services
                if (param_type.endswith('Service') or 
                    param_type in ['HttpClient', 'Router', 'ActivatedRoute', 'FormBuilder', 'MatDialog']):
                    injected_services.append(param_type)
        
        return injected_services
    
    def _extract_decorator_property(self, decorator_content: str, property_name: str) -> Optional[str]:
        """Extract property value from decorator"""
        pattern = re.compile(rf'{property_name}\s*:\s*[\'"`]([^\'"`]+)[\'"`]')
        match = pattern.search(decorator_content)
        return match.group(1) if match else None
    
    def _extract_decorator_array(self, decorator_content: str, property_name: str) -> List[str]:
        """Extract array property from decorator"""
        pattern = re.compile(rf'{property_name}\s*:\s*\[([^\]]+)\]', re.DOTALL)
        match = pattern.search(decorator_content)
        
        if match:
            array_content = match.group(1)
            # Split by comma and clean up
            items = [item.strip().strip('\'"') for item in array_content.split(',')]
            return [item for item in items if item]
        
        return []
    
    def _get_line_number(self, content: str, position: int, lines: List[str]) -> int:
        """Get line number for a position in content"""
        line_num = content[:position].count('\n') + 1
        return min(line_num, len(lines))
    
    def get_component_service_map(self, angular_files: List[Path]) -> Dict[str, Any]:
        """
        Create comprehensive component-service dependency map
        
        Returns analysis of Angular application architecture
        """
        components = []
        services = []
        relationships = []
        
        # Parse all Angular files
        for angular_file in angular_files:
            entities = self.parse(angular_file)
            
            for entity in entities:
                if entity['type'] == 'angular_component':
                    components.append(entity)
                elif entity['type'] == 'angular_service':
                    services.append(entity)
                elif entity['type'] == 'angular_dependency_relationship':
                    relationships.append(entity)
        
        # Analyze service usage patterns
        service_usage = {}
        for relationship in relationships:
            target_service = relationship['target_service']
            if target_service not in service_usage:
                service_usage[target_service] = []
            service_usage[target_service].append(relationship['source_class'])
        
        # Find orphaned services (not used by any component)
        all_service_names = {s['name'] for s in services}
        used_services = set(service_usage.keys())
        orphaned_services = all_service_names - used_services
        
        # Analyze component complexity
        complex_components = [
            c for c in components 
            if c.get('service_count', 0) > 5 or c.get('method_count', 0) > 20
        ]
        
        return {
            'total_components': len(components),
            'total_services': len(services),
            'total_relationships': len(relationships),
            'service_usage': service_usage,
            'orphaned_services': list(orphaned_services),
            'complex_components': [c['name'] for c in complex_components],
            'most_used_services': sorted(
                service_usage.items(), 
                key=lambda x: len(x[1]), 
                reverse=True
            )[:10],
            'architecture_recommendations': self._generate_architecture_recommendations(
                components, services, relationships, orphaned_services
            )
        }
    
    def _generate_architecture_recommendations(self, components: List[Dict], services: List[Dict], 
                                             relationships: List[Dict], orphaned_services: Set[str]) -> List[str]:
        """Generate Angular architecture recommendations"""
        recommendations = []
        
        # Check for over-injected components
        over_injected = [c for c in components if c.get('service_count', 0) > 8]
        if over_injected:
            recommendations.append(f"Consider refactoring {len(over_injected)} components with too many service dependencies")
        
        # Check for orphaned services
        if orphaned_services:
            recommendations.append(f"Remove or refactor {len(orphaned_services)} unused services")
        
        # Check for missing HTTP error handling
        http_services = [s for s in services if s.get('endpoint_count', 0) > 0]
        if http_services:
            recommendations.append(f"Ensure proper error handling for {len(http_services)} HTTP services")
        
        # Check service injection patterns
        strong_dependencies = len([r for r in relationships if r.get('binding_strength') == 'strong'])
        if strong_dependencies > len(components) * 2:
            recommendations.append("Consider using service abstractions to reduce tight coupling")
        
        return recommendations