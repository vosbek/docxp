"""
Struts Action → JSP Forward Mapping Analyzer

Provides comprehensive tracing of Struts action flows:
- Action class → JSP forward mappings
- Form bean → Action → JSP chains
- Struts configuration analysis
- Action result mapping
- Error handling flow tracing
"""

import logging
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Set, Optional, Tuple
from dataclasses import dataclass

from app.parsers.base_parser import BaseParser

logger = logging.getLogger(__name__)

@dataclass
class ActionMapping:
    """Represents a Struts action mapping"""
    path: str
    action_class: str
    method: str
    form_bean: Optional[str] = None
    scope: Optional[str] = None
    validate: bool = True
    input_page: Optional[str] = None
    results: List[Dict[str, str]] = None
    line_number: int = 0

@dataclass
class ActionFlow:
    """Represents complete action flow from request to JSP"""
    action_path: str
    action_class: str
    method: str
    input_jsp: Optional[str] = None
    success_jsp: Optional[str] = None
    error_jsp: Optional[str] = None
    form_bean_class: Optional[str] = None
    validation_rules: List[str] = None
    interceptors: List[str] = None

class StrutsActionTracer(BaseParser):
    """
    Advanced Struts action flow analyzer
    
    Traces complete request flows:
    1. HTTP request → Action mapping
    2. Action class → method execution  
    3. Form bean binding and validation
    4. Result forwarding to JSP
    5. Error handling and exception flows
    """
    
    def __init__(self):
        # Struts configuration patterns
        self.struts_patterns = {
            # Struts 1 patterns
            'action_mapping_v1': re.compile(r'<action-mapping\s+([^>]+)>'),
            'forward_v1': re.compile(r'<forward\s+([^>]+)>'),
            'form_bean_v1': re.compile(r'<form-bean\s+([^>]+)>'),
            
            # Struts 2 patterns
            'action_v2': re.compile(r'<action\s+([^>]*?)>.*?</action>', re.DOTALL),
            'result_v2': re.compile(r'<result\s*([^>]*?)>([^<]*)</result>'),
            'interceptor_v2': re.compile(r'<interceptor-ref\s+([^>]+)>'),
            
            # Java Action class patterns
            'class_declaration': re.compile(r'public\s+class\s+(\w+)\s+extends\s+(Action|ActionSupport|DispatchAction)'),
            'execute_method': re.compile(r'public\s+(?:ActionForward|String)\s+(\w+)\s*\([^)]+\)'),
            'forward_creation': re.compile(r'new\s+ActionForward\s*\(\s*["\']([^"\']+)["\']'),
            'mapping_forward': re.compile(r'mapping\.findForward\s*\(\s*["\']([^"\']+)["\']'),
            'return_mapping': re.compile(r'return\s+["\']([^"\']+)["\']'),
            
            # Form bean patterns
            'form_property': re.compile(r'(?:get|set)(\w+)\s*\('),
            'form_validation': re.compile(r'ActionErrors\s+(\w+)'),
        }
        
        # Attribute parsing
        self.attribute_pattern = re.compile(r'(\w+)\s*=\s*["\']([^"\']*)["\']')
        
    def parse(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse Struts files and extract action flow entities"""
        entities = []
        
        if not self.validate_file(file_path):
            return entities
            
        try:
            if file_path.suffix == '.xml':
                # Parse Struts configuration files
                entities.extend(self._parse_struts_config(file_path))
            elif file_path.suffix == '.java':
                # Parse Action classes
                entities.extend(self._parse_action_class(file_path))
            elif file_path.suffix == '.jsp':
                # Parse JSP for action references
                entities.extend(self._parse_jsp_actions(file_path))
                
        except Exception as e:
            logger.warning(f"Error parsing {file_path}: {e}")
        
        return entities
    
    def extract_dependencies(self, file_path: Path) -> List[str]:
        """Extract action flow dependencies"""
        dependencies = []
        
        if not self.validate_file(file_path):
            return dependencies
            
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
            
            if file_path.suffix == '.xml':
                dependencies.extend(self._extract_config_dependencies(content))
            elif file_path.suffix == '.java':
                dependencies.extend(self._extract_action_dependencies(content))
            elif file_path.suffix == '.jsp':
                dependencies.extend(self._extract_jsp_dependencies(content))
                
        except Exception as e:
            logger.warning(f"Error extracting dependencies from {file_path}: {e}")
        
        return list(set(dependencies))
    
    def _parse_struts_config(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse struts-config.xml or struts.xml"""
        entities = []
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Detect Struts version
            if root.tag == 'struts-config':
                entities.extend(self._parse_struts1_config(root, file_path))
            elif root.tag == 'struts':
                entities.extend(self._parse_struts2_config(root, file_path))
                
        except ET.ParseError as e:
            logger.warning(f"Error parsing XML {file_path}: {e}")
        
        return entities
    
    def _parse_struts1_config(self, root: ET.Element, file_path: Path) -> List[Dict[str, Any]]:
        """Parse Struts 1.x configuration"""
        entities = []
        form_beans = {}
        
        # First pass: collect form beans
        for form_bean in root.findall('.//form-bean'):
            name = form_bean.get('name')
            type_class = form_bean.get('type')
            if name and type_class:
                form_beans[name] = type_class
        
        # Second pass: parse action mappings
        for action in root.findall('.//action'):
            path = action.get('path', '')
            type_class = action.get('type', '')
            name = action.get('name', '')  # form bean name
            scope = action.get('scope', 'request')
            validate = action.get('validate', 'true').lower() == 'true'
            input_page = action.get('input', '')
            
            # Get form bean class
            form_bean_class = form_beans.get(name) if name else None
            
            # Extract forwards
            forwards = []
            for forward in action.findall('forward'):
                forward_name = forward.get('name', '')
                forward_path = forward.get('path', '')
                forwards.append({
                    'name': forward_name,
                    'path': forward_path,
                    'redirect': forward.get('redirect', 'false').lower() == 'true'
                })
            
            # Create action mapping entity
            entity = self.create_entity(
                name=f"Action: {path}",
                entity_type='struts1_action_mapping',
                file_path=str(file_path),
                line_number=1,
                action_path=path,
                action_class=type_class,
                form_bean_name=name,
                form_bean_class=form_bean_class,
                scope=scope,
                validate=validate,
                input_page=input_page,
                forwards=forwards,
                framework='Struts1'
            )
            entities.append(entity)
            
            # Create flow entity for each forward
            for forward in forwards:
                flow_entity = self.create_entity(
                    name=f"Flow: {path} → {forward['path']}",
                    entity_type='struts1_action_flow',
                    file_path=str(file_path),
                    line_number=1,
                    source_action=path,
                    target_jsp=forward['path'],
                    flow_type=forward['name'],
                    is_redirect=forward['redirect'],
                    framework='Struts1'
                )
                entities.append(flow_entity)
        
        return entities
    
    def _parse_struts2_config(self, root: ET.Element, file_path: Path) -> List[Dict[str, Any]]:
        """Parse Struts 2.x configuration"""
        entities = []
        
        for package in root.findall('.//package'):
            package_name = package.get('name', '')
            namespace = package.get('namespace', '')
            
            for action in package.findall('action'):
                name = action.get('name', '')
                class_name = action.get('class', '')
                method = action.get('method', 'execute')
                
                # Extract results
                results = []
                for result in action.findall('result'):
                    result_name = result.get('name', 'success')
                    result_type = result.get('type', 'dispatcher')
                    result_value = result.text.strip() if result.text else ''
                    
                    results.append({
                        'name': result_name,
                        'type': result_type,
                        'value': result_value
                    })
                
                # Extract interceptors
                interceptors = []
                for interceptor_ref in action.findall('.//interceptor-ref'):
                    interceptor_name = interceptor_ref.get('name', '')
                    interceptors.append(interceptor_name)
                
                # Create action entity
                entity = self.create_entity(
                    name=f"Action: {namespace}/{name}",
                    entity_type='struts2_action_mapping',
                    file_path=str(file_path),
                    line_number=1,
                    package_name=package_name,
                    namespace=namespace,
                    action_name=name,
                    action_class=class_name,
                    method=method,
                    results=results,
                    interceptors=interceptors,
                    framework='Struts2'
                )
                entities.append(entity)
                
                # Create flow entities for each result
                for result in results:
                    if result['value']:  # Only if there's a target
                        flow_entity = self.create_entity(
                            name=f"Flow: {namespace}/{name} → {result['value']}",
                            entity_type='struts2_action_flow',
                            file_path=str(file_path),
                            line_number=1,
                            source_action=f"{namespace}/{name}",
                            target_jsp=result['value'],
                            flow_type=result['name'],
                            result_type=result['type'],
                            framework='Struts2'
                        )
                        entities.append(flow_entity)
        
        return entities
    
    def _parse_action_class(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse Java Action class implementation"""
        entities = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
                lines = content.split('\n')
            
            # Check if it's a Struts Action class
            class_match = self.struts_patterns['class_declaration'].search(content)
            if not class_match:
                return entities
            
            class_name = class_match.group(1)
            base_class = class_match.group(2)
            
            # Extract execute methods
            for method_match in self.struts_patterns['execute_method'].finditer(content):
                method_name = method_match.group(1)
                line_num = self._get_line_number(content, method_match.start(), lines)
                
                # Extract forwards used in this method
                method_start = method_match.start()
                # Find method end (simplistic - look for next method or class end)
                method_end = self._find_method_end(content, method_start)
                method_content = content[method_start:method_end]
                
                forwards = self._extract_method_forwards(method_content)
                returns = self._extract_method_returns(method_content)
                
                entity = self.create_entity(
                    name=f"{class_name}.{method_name}()",
                    entity_type='struts_action_method',
                    file_path=str(file_path),
                    line_number=line_num,
                    class_name=class_name,
                    method_name=method_name,
                    base_class=base_class,
                    forwards=forwards,
                    returns=returns,
                    framework=f'Struts-{base_class}'
                )
                entities.append(entity)
                
                # Create flow entities for each forward/return
                for forward in forwards:
                    flow_entity = self.create_entity(
                        name=f"Method Flow: {class_name}.{method_name} → {forward}",
                        entity_type='struts_method_flow',
                        file_path=str(file_path),
                        line_number=line_num,
                        source_method=f"{class_name}.{method_name}",
                        target_forward=forward,
                        flow_type='forward',
                        framework=f'Struts-{base_class}'
                    )
                    entities.append(flow_entity)
                
                for return_val in returns:
                    flow_entity = self.create_entity(
                        name=f"Method Return: {class_name}.{method_name} → {return_val}",
                        entity_type='struts_method_flow',
                        file_path=str(file_path),
                        line_number=line_num,
                        source_method=f"{class_name}.{method_name}",
                        target_forward=return_val,
                        flow_type='return',
                        framework=f'Struts-{base_class}'
                    )
                    entities.append(flow_entity)
                    
        except Exception as e:
            logger.warning(f"Error parsing Action class {file_path}: {e}")
        
        return entities
    
    def _parse_jsp_actions(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse JSP for action references and form submissions"""
        entities = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
                lines = content.split('\n')
            
            # Find HTML forms with action attributes
            form_pattern = re.compile(r'<form\s+([^>]+)>', re.IGNORECASE)
            for match in form_pattern.finditer(content):
                attributes = self._parse_attributes(match.group(1))
                line_num = self._get_line_number(content, match.start(), lines)
                
                if 'action' in attributes:
                    action_path = attributes['action']
                    method = attributes.get('method', 'GET').upper()
                    
                    entity = self.create_entity(
                        name=f"Form → {action_path}",
                        entity_type='jsp_form_action',
                        file_path=str(file_path),
                        line_number=line_num,
                        action_path=action_path,
                        method=method,
                        form_attributes=attributes,
                        framework='JSP/HTML'
                    )
                    entities.append(entity)
            
            # Find Struts HTML tags
            struts_form_pattern = re.compile(r'<html:form\s+([^>]+)>', re.IGNORECASE)
            for match in struts_form_pattern.finditer(content):
                attributes = self._parse_attributes(match.group(1))
                line_num = self._get_line_number(content, match.start(), lines)
                
                if 'action' in attributes:
                    action_path = attributes['action']
                    
                    entity = self.create_entity(
                        name=f"Struts Form → {action_path}",
                        entity_type='jsp_struts_form',
                        file_path=str(file_path),
                        line_number=line_num,
                        action_path=action_path,
                        form_attributes=attributes,
                        framework='JSP/Struts'
                    )
                    entities.append(entity)
                    
        except Exception as e:
            logger.warning(f"Error parsing JSP actions {file_path}: {e}")
        
        return entities
    
    def _extract_method_forwards(self, method_content: str) -> List[str]:
        """Extract ActionForward references from method"""
        forwards = []
        
        # Look for mapping.findForward calls
        for match in self.struts_patterns['mapping_forward'].finditer(method_content):
            forwards.append(match.group(1))
        
        # Look for new ActionForward creation
        for match in self.struts_patterns['forward_creation'].finditer(method_content):
            forwards.append(match.group(1))
        
        return forwards
    
    def _extract_method_returns(self, method_content: str) -> List[str]:
        """Extract return values from method (for Struts 2)"""
        returns = []
        
        for match in self.struts_patterns['return_mapping'].finditer(method_content):
            returns.append(match.group(1))
        
        return returns
    
    def _find_method_end(self, content: str, method_start: int) -> int:
        """Find the end of a method (simplified)"""
        brace_count = 0
        in_method = False
        
        for i, char in enumerate(content[method_start:], method_start):
            if char == '{':
                brace_count += 1
                in_method = True
            elif char == '}':
                brace_count -= 1
                if in_method and brace_count == 0:
                    return i + 1
        
        return len(content)  # Fallback
    
    def _extract_config_dependencies(self, content: str) -> List[str]:
        """Extract dependencies from Struts config"""
        dependencies = []
        
        # Extract JSP file references
        jsp_refs = re.findall(r'["\']([^"\']*\.jsp)["\']', content)
        dependencies.extend(jsp_refs)
        
        # Extract class references
        class_refs = re.findall(r'class\s*=\s*["\']([^"\']+)["\']', content)
        dependencies.extend(class_refs)
        
        return dependencies
    
    def _extract_action_dependencies(self, content: str) -> List[str]:
        """Extract dependencies from Action class"""
        dependencies = []
        
        # Extract import statements
        import_pattern = re.compile(r'import\s+([^;]+);')
        for match in import_pattern.finditer(content):
            dependencies.append(match.group(1).strip())
        
        return dependencies
    
    def _extract_jsp_dependencies(self, content: str) -> List[str]:
        """Extract action dependencies from JSP"""
        dependencies = []
        
        # Extract action references from forms
        action_refs = re.findall(r'action\s*=\s*["\']([^"\']+)["\']', content, re.IGNORECASE)
        dependencies.extend(action_refs)
        
        return dependencies
    
    def _parse_attributes(self, attr_string: str) -> Dict[str, str]:
        """Parse HTML/XML attributes"""
        attributes = {}
        for match in self.attribute_pattern.finditer(attr_string):
            attributes[match.group(1)] = match.group(2)
        return attributes
    
    def _get_line_number(self, content: str, position: int, lines: List[str]) -> int:
        """Get line number for a position in content"""
        line_num = content[:position].count('\n') + 1
        return min(line_num, len(lines))
    
    def get_action_flow_map(self, config_dir: Path) -> Dict[str, ActionFlow]:
        """
        Create comprehensive action flow map from Struts configuration
        
        Returns mapping of action paths to complete flow information
        """
        flow_map = {}
        
        # Parse all configuration files in directory
        for config_file in config_dir.glob('**/*.xml'):
            if 'struts' in config_file.name.lower():
                entities = self.parse(config_file)
                
                for entity in entities:
                    if entity['type'] in ['struts1_action_mapping', 'struts2_action_mapping']:
                        action_path = entity.get('action_path') or f"{entity.get('namespace', '')}/{entity.get('action_name', '')}"
                        
                        # Build ActionFlow
                        flow = ActionFlow(
                            action_path=action_path,
                            action_class=entity.get('action_class', ''),
                            method=entity.get('method', 'execute'),
                            form_bean_class=entity.get('form_bean_class'),
                            input_jsp=entity.get('input_page'),
                            validation_rules=[],
                            interceptors=entity.get('interceptors', [])
                        )
                        
                        # Extract JSP forwards
                        forwards = entity.get('forwards', entity.get('results', []))
                        for forward in forwards:
                            if forward.get('name') == 'success':
                                flow.success_jsp = forward.get('path', forward.get('value'))
                            elif forward.get('name') in ['error', 'failure']:
                                flow.error_jsp = forward.get('path', forward.get('value'))
                        
                        flow_map[action_path] = flow
        
        return flow_map