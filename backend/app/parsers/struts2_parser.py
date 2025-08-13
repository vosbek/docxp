"""
Apache Struts2 specific parser for modern Struts framework
"""

import logging
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any

from app.parsers.base_parser import BaseParser

logger = logging.getLogger(__name__)

class Struts2Parser(BaseParser):
    """Parser specifically for Struts2 framework files"""
    
    def parse(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse Struts2 files and extract entities"""
        entities = []
        
        try:
            if file_path.suffix == '.xml':
                entities.extend(self._parse_struts2_xml(file_path))
            elif file_path.suffix == '.java':
                entities.extend(self._parse_struts2_action(file_path))
            elif file_path.suffix == '.jsp':
                entities.extend(self._parse_struts2_jsp(file_path))
            
        except Exception as e:
            logger.warning(f"Error parsing {file_path}: {e}")
        
        return entities
    
    def extract_dependencies(self, file_path: Path) -> List[str]:
        """Extract dependencies from Struts2 files"""
        dependencies = []
        
        try:
            if file_path.suffix == '.java':
                content = self.read_file_safe(file_path)
                if not content:
                    return dependencies
                
                # Extract Struts2 annotations
                annotations = re.findall(r'@(Action|Result|Results|Namespace|ParentPackage)\s*\(', content)
                if annotations:
                    dependencies.append('org.apache.struts2.convention.annotation')
                
                # Extract imports
                imports = re.findall(r'import\s+(org\.apache\.struts2[.\w]+);', content)
                dependencies.extend(imports)
        
        except Exception as e:
            logger.warning(f"Error extracting dependencies: {e}")
        
        return list(set(dependencies))
    
    def _parse_struts2_xml(self, file_path: Path) -> List[Dict]:
        """Parse struts.xml for Struts2 specific features"""
        entities = []
        
        # Validate XML content first
        xml_content = self.validate_xml_content(file_path)
        if not xml_content:
            logger.debug(f"Skipping invalid or empty XML file: {file_path}")
            return entities
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Extract packages
            for package in root.findall('.//package'):
                package_name = package.get('name', 'default')
                namespace = package.get('namespace', '/')
                extends = package.get('extends', 'struts-default')
                
                package_entity = self.create_entity(
                    name=package_name,
                    entity_type='struts2_package',
                    file_path=str(file_path),
                    line_number=1,
                    namespace=namespace,
                    extends=extends
                )
                entities.append(package_entity)
                
                # Extract actions in package
                for action in package.findall('action'):
                    action_name = action.get('name', 'unnamed')
                    action_class = action.get('class', '')
                    method = action.get('method', 'execute')
                    
                    action_entity = self.create_entity(
                        name=f"{package_name}.{action_name}",
                        entity_type='struts2_action',
                        file_path=str(file_path),
                        line_number=1,
                        action_class=action_class,
                        method=method,
                        package=package_name,
                        namespace=namespace
                    )
                    entities.append(action_entity)
                    
                    # Extract interceptor refs
                    for interceptor_ref in action.findall('interceptor-ref'):
                        interceptor_name = interceptor_ref.get('name', '')
                        if interceptor_name:
                            interceptor_entity = self.create_entity(
                                name=f"{action_name}_interceptor_{interceptor_name}",
                                entity_type='struts2_interceptor_ref',
                                file_path=str(file_path),
                                line_number=1,
                                interceptor=interceptor_name,
                                action=action_name
                            )
                            entities.append(interceptor_entity)
            
            # Extract global results
            for global_result in root.findall('.//global-results/result'):
                result_name = global_result.get('name', 'success')
                result_type = global_result.get('type', 'dispatcher')
                
                global_result_entity = self.create_entity(
                    name=f"global_{result_name}",
                    entity_type='struts2_global_result',
                    file_path=str(file_path),
                    line_number=1,
                    result_type=result_type
                )
                entities.append(global_result_entity)
            
            # Extract interceptor stacks
            for interceptor_stack in root.findall('.//interceptor-stack'):
                stack_name = interceptor_stack.get('name', '')
                
                stack_entity = self.create_entity(
                    name=stack_name,
                    entity_type='struts2_interceptor_stack',
                    file_path=str(file_path),
                    line_number=1,
                    interceptors=[ref.get('name', '') for ref in interceptor_stack.findall('interceptor-ref')]
                )
                entities.append(stack_entity)
        
        except ET.ParseError as e:
            logger.warning(f"Error parsing XML {file_path}: {e}")
        
        return entities
    
    def _parse_struts2_action(self, file_path: Path) -> List[Dict]:
        """Parse Struts2 Action classes with annotations"""
        entities = []
        
        # Safely read file content
        content = self.read_file_safe(file_path)
        if not content:
            logger.debug(f"Skipping invalid or empty Java file: {file_path}")
            return entities
        
        try:
            
            # Check for Struts2 ActionSupport
            if 'extends ActionSupport' in content or '@Action' in content:
                # Extract class with annotations
                class_pattern = r'(?:@\w+(?:\([^)]*\))?\s*)*public\s+class\s+(\w+)'
                match = re.search(class_pattern, content)
                
                if match:
                    class_name = match.group(1)
                    line_number = content[:match.start()].count('\n') + 1
                    
                    # Extract annotations
                    annotations = []
                    annotation_pattern = r'@(\w+)(?:\(([^)]*)\))?'
                    for ann_match in re.finditer(annotation_pattern, content[:match.start()]):
                        annotations.append(ann_match.group(1))
                    
                    entity = self.create_entity(
                        name=class_name,
                        entity_type='struts2_action_class',
                        file_path=str(file_path),
                        line_number=line_number,
                        annotations=annotations,
                        framework='Struts2'
                    )
                    entities.append(entity)
                    
                    # Extract action methods with @Action annotation
                    action_method_pattern = r'@Action\s*(?:\([^)]*\))?\s*public\s+\w+\s+(\w+)\s*\('
                    for method_match in re.finditer(action_method_pattern, content):
                        method_name = method_match.group(1)
                        method_line = content[:method_match.start()].count('\n') + 1
                        
                        method_entity = self.create_entity(
                            name=f"{class_name}.{method_name}",
                            entity_type='struts2_action_method',
                            file_path=str(file_path),
                            line_number=method_line,
                            parent_class=class_name,
                            annotation='@Action'
                        )
                        entities.append(method_entity)
                    
                    # Extract validation methods
                    validation_pattern = r'public\s+void\s+(validate\w*)\s*\('
                    for val_match in re.finditer(validation_pattern, content):
                        val_method = val_match.group(1)
                        val_line = content[:val_match.start()].count('\n') + 1
                        
                        val_entity = self.create_entity(
                            name=f"{class_name}.{val_method}",
                            entity_type='struts2_validation_method',
                            file_path=str(file_path),
                            line_number=val_line,
                            parent_class=class_name
                        )
                        entities.append(val_entity)
        
        except Exception as e:
            logger.warning(f"Error parsing Struts2 action {file_path}: {e}")
        
        return entities
    
    def _parse_struts2_jsp(self, file_path: Path) -> List[Dict]:
        """Parse JSP files with Struts2 tags"""
        entities = []
        
        # Safely read file content
        content = self.read_file_safe(file_path)
        if not content:
            logger.debug(f"Skipping invalid or empty JSP file: {file_path}")
            return entities
        
        try:
            
            # Extract Struts2 tags (s: prefix)
            s_tags = re.findall(r'<s:(\w+)[^>]*>', content)
            
            # Extract OGNL expressions
            ognl_expressions = re.findall(r'%{([^}]+)}', content)
            
            if s_tags or ognl_expressions:
                entity = self.create_entity(
                    name=file_path.stem,
                    entity_type='struts2_jsp',
                    file_path=str(file_path),
                    line_number=1,
                    struts2_tags=list(set(s_tags)),
                    ognl_expressions=ognl_expressions[:10],  # Limit to first 10
                    tag_count=len(s_tags),
                    ognl_count=len(ognl_expressions)
                )
                entities.append(entity)
        
        except Exception as e:
            logger.warning(f"Error parsing Struts2 JSP {file_path}: {e}")
        
        return entities
