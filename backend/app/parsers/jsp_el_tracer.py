"""
JSP EL Expression Parser and Cross-Reference Tracer

Analyzes JSP files to extract:
- EL expressions (${} and #{})
- Bean references and property access
- Method calls and function invocations
- Cross-references to Java classes and Spring beans
- Struts form bindings and action mappings
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
class ELExpression:
    """Represents an EL expression with context"""
    expression: str
    type: str  # 'bean_reference', 'property_access', 'method_call', 'function_call'
    bean_name: Optional[str] = None
    property_path: List[str] = None
    method_name: Optional[str] = None
    parameters: List[str] = None
    line_number: int = 0
    context: str = ""  # Surrounding JSP context

@dataclass  
class JSPBinding:
    """Represents a JSP-to-Java binding"""
    jsp_element: str
    java_reference: str
    binding_type: str  # 'form_bean', 'action_forward', 'include', 'tag_library'
    line_number: int
    attributes: Dict[str, str] = None

class JSPELTracer(BaseParser):
    """
    Advanced JSP EL expression parser with cross-reference tracing
    
    Provides deep analysis of JSP files including:
    - EL expression parsing and classification
    - Bean reference resolution
    - Cross-references to Java classes
    - Struts action mappings
    - Tag library usage
    """
    
    def __init__(self):
        # EL expression patterns
        self.el_patterns = {
            'dollar_expression': re.compile(r'\$\{([^}]+)\}'),
            'hash_expression': re.compile(r'#\{([^}]+)\}'),
            'bean_reference': re.compile(r'(\w+)\.'),
            'property_access': re.compile(r'(\w+(?:\.\w+)+)'),
            'method_call': re.compile(r'(\w+)\s*\([^)]*\)'),
            'function_call': re.compile(r'(\w+):(\w+)\s*\([^)]*\)')
        }
        
        # JSP directive and tag patterns
        self.jsp_patterns = {
            'page_directive': re.compile(r'<%@\s*page\s+([^%>]+)%>'),
            'taglib_directive': re.compile(r'<%@\s*taglib\s+([^%>]+)%>'),
            'include_directive': re.compile(r'<%@\s*include\s+([^%>]+)%>'),
            'jsp_include': re.compile(r'<jsp:include\s+([^>]+)>'),
            'jsp_forward': re.compile(r'<jsp:forward\s+([^>]+)>'),
            'jsp_useBean': re.compile(r'<jsp:useBean\s+([^>]+)>'),
            'struts_form': re.compile(r'<(?:html|s):form\s+([^>]+)>'),
            'struts_property': re.compile(r'<(?:bean|s):write\s+([^>]+)>'),
            'custom_tag': re.compile(r'<(\w+):(\w+)\s*([^>]*)>')
        }
        
        # Attribute parsing
        self.attribute_pattern = re.compile(r'(\w+)\s*=\s*["\']([^"\']*)["\']')
        
    def parse(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse JSP file and extract all entities with EL tracing"""
        entities = []
        
        if not self.validate_file(file_path):
            return entities
            
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
                lines = content.split('\n')
                
            # Extract EL expressions
            el_expressions = self._extract_el_expressions(content, lines)
            for el_expr in el_expressions:
                entities.append(self._create_el_entity(el_expr, file_path))
            
            # Extract JSP bindings (forms, includes, forwards)
            jsp_bindings = self._extract_jsp_bindings(content, lines)
            for binding in jsp_bindings:
                entities.append(self._create_binding_entity(binding, file_path))
            
            # Extract tag library usage
            tag_libraries = self._extract_tag_libraries(content, lines)
            for tag_lib in tag_libraries:
                entities.append(self._create_taglib_entity(tag_lib, file_path))
            
            # Extract Java scriptlet references
            scriptlet_refs = self._extract_scriptlet_references(content, lines)
            for ref in scriptlet_refs:
                entities.append(self._create_scriptlet_entity(ref, file_path))
                
        except Exception as e:
            logger.warning(f"Error parsing JSP file {file_path}: {e}")
        
        return entities
    
    def extract_dependencies(self, file_path: Path) -> List[str]:
        """Extract all dependencies from JSP file"""
        dependencies = []
        
        if not self.validate_file(file_path):
            return dependencies
            
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
            
            # Extract taglib dependencies
            for match in self.jsp_patterns['taglib_directive'].finditer(content):
                attributes = self._parse_attributes(match.group(1))
                if 'uri' in attributes:
                    dependencies.append(attributes['uri'])
            
            # Extract include dependencies  
            for match in self.jsp_patterns['include_directive'].finditer(content):
                attributes = self._parse_attributes(match.group(1))
                if 'file' in attributes:
                    dependencies.append(attributes['file'])
            
            # Extract jsp:include dependencies
            for match in self.jsp_patterns['jsp_include'].finditer(content):
                attributes = self._parse_attributes(match.group(1))
                if 'page' in attributes:
                    dependencies.append(attributes['page'])
                    
        except Exception as e:
            logger.warning(f"Error extracting dependencies from {file_path}: {e}")
        
        return list(set(dependencies))
    
    def _extract_el_expressions(self, content: str, lines: List[str]) -> List[ELExpression]:
        """Extract and classify EL expressions"""
        expressions = []
        
        # Find all EL expressions
        for pattern_name, pattern in [('dollar', self.el_patterns['dollar_expression']),
                                     ('hash', self.el_patterns['hash_expression'])]:
            for match in pattern.finditer(content):
                expr = match.group(1).strip()
                line_num = self._get_line_number(content, match.start(), lines)
                context = self._get_context(lines, line_num)
                
                # Classify the expression
                el_expr = self._classify_el_expression(expr, line_num, context)
                expressions.append(el_expr)
        
        return expressions
    
    def _classify_el_expression(self, expr: str, line_num: int, context: str) -> ELExpression:
        """Classify EL expression type and extract components"""
        
        # Function call: namespace:function()
        func_match = self.el_patterns['function_call'].search(expr)
        if func_match:
            return ELExpression(
                expression=expr,
                type='function_call',
                bean_name=func_match.group(1),  # namespace
                method_name=func_match.group(2),  # function name
                line_number=line_num,
                context=context
            )
        
        # Method call: object.method()
        method_match = self.el_patterns['method_call'].search(expr)
        if method_match:
            method_call = method_match.group(1)
            if '.' in method_call:
                parts = method_call.split('.')
                bean_name = parts[0]
                method_name = parts[-1].split('(')[0]
                property_path = parts[1:-1] if len(parts) > 2 else []
            else:
                bean_name = None
                method_name = method_call.split('(')[0]
                property_path = []
                
            return ELExpression(
                expression=expr,
                type='method_call',
                bean_name=bean_name,
                method_name=method_name,
                property_path=property_path,
                line_number=line_num,
                context=context
            )
        
        # Property access: object.property.subproperty
        prop_match = self.el_patterns['property_access'].search(expr)
        if prop_match:
            prop_path = prop_match.group(1).split('.')
            bean_name = prop_path[0]
            property_path = prop_path[1:]
            
            return ELExpression(
                expression=expr,
                type='property_access',
                bean_name=bean_name,
                property_path=property_path,
                line_number=line_num,
                context=context
            )
        
        # Simple bean reference
        bean_match = self.el_patterns['bean_reference'].search(expr)
        if bean_match:
            bean_name = bean_match.group(1)
            
            return ELExpression(
                expression=expr,
                type='bean_reference',
                bean_name=bean_name,
                line_number=line_num,
                context=context
            )
        
        # Fallback - unclassified expression
        return ELExpression(
            expression=expr,
            type='unclassified',
            line_number=line_num,
            context=context
        )
    
    def _extract_jsp_bindings(self, content: str, lines: List[str]) -> List[JSPBinding]:
        """Extract JSP-to-Java bindings"""
        bindings = []
        
        # Struts form bindings
        for match in self.jsp_patterns['struts_form'].finditer(content):
            attributes = self._parse_attributes(match.group(1))
            line_num = self._get_line_number(content, match.start(), lines)
            
            if 'action' in attributes:
                binding = JSPBinding(
                    jsp_element='struts_form',
                    java_reference=attributes['action'],
                    binding_type='action_forward',
                    line_number=line_num,
                    attributes=attributes
                )
                bindings.append(binding)
        
        # JSP useBean
        for match in self.jsp_patterns['jsp_useBean'].finditer(content):
            attributes = self._parse_attributes(match.group(1))
            line_num = self._get_line_number(content, match.start(), lines)
            
            if 'class' in attributes:
                binding = JSPBinding(
                    jsp_element='jsp_useBean',
                    java_reference=attributes['class'],
                    binding_type='form_bean',
                    line_number=line_num,
                    attributes=attributes
                )
                bindings.append(binding)
        
        # JSP forwards
        for match in self.jsp_patterns['jsp_forward'].finditer(content):
            attributes = self._parse_attributes(match.group(1))
            line_num = self._get_line_number(content, match.start(), lines)
            
            if 'page' in attributes:
                binding = JSPBinding(
                    jsp_element='jsp_forward',
                    java_reference=attributes['page'],
                    binding_type='action_forward',
                    line_number=line_num,
                    attributes=attributes
                )
                bindings.append(binding)
        
        return bindings
    
    def _extract_tag_libraries(self, content: str, lines: List[str]) -> List[Dict[str, Any]]:
        """Extract tag library declarations and usage"""
        tag_libraries = []
        declared_prefixes = {}
        
        # First pass: collect taglib declarations
        for match in self.jsp_patterns['taglib_directive'].finditer(content):
            attributes = self._parse_attributes(match.group(1))
            line_num = self._get_line_number(content, match.start(), lines)
            
            if 'prefix' in attributes and 'uri' in attributes:
                declared_prefixes[attributes['prefix']] = attributes['uri']
                tag_libraries.append({
                    'type': 'taglib_declaration',
                    'prefix': attributes['prefix'],
                    'uri': attributes['uri'],
                    'line_number': line_num
                })
        
        # Second pass: find custom tag usage
        for match in self.jsp_patterns['custom_tag'].finditer(content):
            prefix = match.group(1)
            tag_name = match.group(2)
            attributes_str = match.group(3)
            line_num = self._get_line_number(content, match.start(), lines)
            
            if prefix in declared_prefixes:
                tag_libraries.append({
                    'type': 'tag_usage',
                    'prefix': prefix,
                    'tag_name': tag_name,
                    'uri': declared_prefixes[prefix],
                    'attributes': self._parse_attributes(attributes_str),
                    'line_number': line_num
                })
        
        return tag_libraries
    
    def _extract_scriptlet_references(self, content: str, lines: List[str]) -> List[Dict[str, Any]]:
        """Extract Java references from scriptlets"""
        scriptlet_refs = []
        
        # Java scriptlets <%  %>
        scriptlet_pattern = re.compile(r'<%\s*([^%>]+)\s*%>')
        for match in scriptlet_pattern.finditer(content):
            java_code = match.group(1).strip()
            line_num = self._get_line_number(content, match.start(), lines)
            
            # Extract class references
            class_refs = re.findall(r'\b([A-Z][a-zA-Z0-9_]*(?:\.[A-Z][a-zA-Z0-9_]*)*)\b', java_code)
            for class_ref in class_refs:
                scriptlet_refs.append({
                    'type': 'java_class_reference',
                    'class_name': class_ref,
                    'java_code': java_code,
                    'line_number': line_num
                })
        
        return scriptlet_refs
    
    def _create_el_entity(self, el_expr: ELExpression, file_path: Path) -> Dict[str, Any]:
        """Create entity for EL expression"""
        return self.create_entity(
            name=f"EL: {el_expr.expression}",
            entity_type='jsp_el_expression',
            file_path=str(file_path),
            line_number=el_expr.line_number,
            expression=el_expr.expression,
            el_type=el_expr.type,
            bean_name=el_expr.bean_name,
            property_path=el_expr.property_path,
            method_name=el_expr.method_name,
            parameters=el_expr.parameters,
            context=el_expr.context,
            framework='JSP/EL'
        )
    
    def _create_binding_entity(self, binding: JSPBinding, file_path: Path) -> Dict[str, Any]:
        """Create entity for JSP binding"""
        return self.create_entity(
            name=f"{binding.jsp_element} -> {binding.java_reference}",
            entity_type='jsp_java_binding',
            file_path=str(file_path),
            line_number=binding.line_number,
            jsp_element=binding.jsp_element,
            java_reference=binding.java_reference,
            binding_type=binding.binding_type,
            attributes=binding.attributes,
            framework='JSP/Struts'
        )
    
    def _create_taglib_entity(self, tag_lib: Dict[str, Any], file_path: Path) -> Dict[str, Any]:
        """Create entity for tag library"""
        name = f"{tag_lib.get('prefix', '')}:{tag_lib.get('tag_name', tag_lib.get('uri', 'unknown'))}"
        return self.create_entity(
            name=name,
            entity_type='jsp_tag_library',
            file_path=str(file_path),
            line_number=tag_lib['line_number'],
            tag_type=tag_lib['type'],
            prefix=tag_lib.get('prefix'),
            tag_name=tag_lib.get('tag_name'),
            uri=tag_lib.get('uri'),
            attributes=tag_lib.get('attributes'),
            framework='JSP/TagLib'
        )
    
    def _create_scriptlet_entity(self, scriptlet: Dict[str, Any], file_path: Path) -> Dict[str, Any]:
        """Create entity for Java scriptlet reference"""
        return self.create_entity(
            name=f"Java ref: {scriptlet['class_name']}",
            entity_type='jsp_java_scriptlet',
            file_path=str(file_path),
            line_number=scriptlet['line_number'],
            class_name=scriptlet['class_name'],
            java_code=scriptlet['java_code'],
            framework='JSP/Java'
        )
    
    def _parse_attributes(self, attr_string: str) -> Dict[str, str]:
        """Parse HTML/JSP attributes"""
        attributes = {}
        for match in self.attribute_pattern.finditer(attr_string):
            attributes[match.group(1)] = match.group(2)
        return attributes
    
    def _get_line_number(self, content: str, position: int, lines: List[str]) -> int:
        """Get line number for a position in content"""
        line_num = content[:position].count('\n') + 1
        return min(line_num, len(lines))
    
    def _get_context(self, lines: List[str], line_num: int, context_size: int = 2) -> str:
        """Get surrounding context for a line"""
        start = max(0, line_num - context_size - 1)
        end = min(len(lines), line_num + context_size)
        context_lines = lines[start:end]
        return '\n'.join(context_lines)

    def get_cross_references(self, file_path: Path) -> Dict[str, List[str]]:
        """
        Get comprehensive cross-references from JSP to Java components
        
        Returns dict with categories of references found
        """
        cross_refs = {
            'bean_references': [],
            'action_forwards': [],
            'java_classes': [],
            'tag_libraries': [],
            'included_files': []
        }
        
        entities = self.parse(file_path)
        
        for entity in entities:
            if entity['type'] == 'jsp_el_expression' and entity.get('bean_name'):
                cross_refs['bean_references'].append(entity['bean_name'])
            elif entity['type'] == 'jsp_java_binding':
                if entity.get('binding_type') == 'action_forward':
                    cross_refs['action_forwards'].append(entity['java_reference'])
                elif entity.get('binding_type') == 'form_bean':
                    cross_refs['java_classes'].append(entity['java_reference'])
            elif entity['type'] == 'jsp_tag_library' and entity.get('uri'):
                cross_refs['tag_libraries'].append(entity['uri'])
            elif entity['type'] == 'jsp_java_scriptlet' and entity.get('class_name'):
                cross_refs['java_classes'].append(entity['class_name'])
        
        # Deduplicate
        for key in cross_refs:
            cross_refs[key] = list(set(cross_refs[key]))
        
        return cross_refs