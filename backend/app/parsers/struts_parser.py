"""
Apache Struts/Struts2 parser for Java web framework files
"""

import logging
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any

from app.parsers.base_parser import BaseParser

logger = logging.getLogger(__name__)

class StrutsParser(BaseParser):
    """Parser for Apache Struts/Struts2 framework files"""
    
    def parse(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse Struts files and extract entities"""
        entities = []
        
        try:
            # Check file type
            if file_path.suffix == '.xml':
                # Parse struts.xml or struts-config.xml
                entities.extend(self._parse_struts_xml(file_path))
            elif file_path.suffix == '.java':
                # Parse Action classes
                entities.extend(self._parse_action_class(file_path))
            elif file_path.suffix == '.jsp':
                # Parse JSP files
                entities.extend(self._parse_jsp(file_path))
            
        except Exception as e:
            logger.warning(f"Error parsing {file_path}: {e}")
        
        return entities
    
    def extract_dependencies(self, file_path: Path) -> List[str]:
        """Extract dependencies from Struts files"""
        dependencies = []
        
        try:
            if file_path.suffix == '.xml':
                dependencies.extend(self._extract_xml_dependencies(file_path))
            elif file_path.suffix == '.java':
                dependencies.extend(self._extract_java_dependencies(file_path))
            
        except Exception as e:
            logger.warning(f"Error extracting dependencies from {file_path}: {e}")
        
        return list(set(dependencies))
    
    def _parse_struts_xml(self, file_path: Path) -> List[Dict]:
        """Parse struts.xml configuration file"""
        entities = []
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Extract actions (Struts 2)
            for action in root.findall('.//action'):
                action_name = action.get('name', 'unnamed')
                action_class = action.get('class', '')
                method = action.get('method', 'execute')
                
                entity = self.create_entity(
                    name=action_name,
                    entity_type='struts_action',
                    file_path=str(file_path),
                    line_number=1,
                    action_class=action_class,
                    method=method,
                    framework='Struts2'
                )
                entities.append(entity)
                
                # Extract results
                for result in action.findall('result'):
                    result_name = result.get('name', 'success')
                    result_type = result.get('type', 'dispatcher')
                    
                    result_entity = self.create_entity(
                        name=f"{action_name}_{result_name}",
                        entity_type='struts_result',
                        file_path=str(file_path),
                        line_number=1,
                        result_type=result_type,
                        parent_action=action_name
                    )
                    entities.append(result_entity)
            
            # Extract action mappings (Struts 1)
            for action_mapping in root.findall('.//action-mapping'):
                path = action_mapping.get('path', '')
                type_class = action_mapping.get('type', '')
                
                entity = self.create_entity(
                    name=path,
                    entity_type='struts_mapping',
                    file_path=str(file_path),
                    line_number=1,
                    action_class=type_class,
                    framework='Struts1'
                )
                entities.append(entity)
            
        except ET.ParseError as e:
            logger.warning(f"Error parsing XML {file_path}: {e}")
        
        return entities
    
    def _parse_action_class(self, file_path: Path) -> List[Dict]:
        """Parse Struts Action class"""
        entities = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Check if it's a Struts Action class
            if 'extends Action' in content or 'extends ActionSupport' in content:
                # Extract class name
                class_pattern = r"public\s+class\s+(\w+)\s+extends\s+(Action|ActionSupport)"
                match = re.search(class_pattern, content)
                
                if match:
                    class_name = match.group(1)
                    base_class = match.group(2)
                    line_number = content[:match.start()].count('\n') + 1
                    
                    entity = self.create_entity(
                        name=class_name,
                        entity_type='struts_action_class',
                        file_path=str(file_path),
                        line_number=line_number,
                        base_class=base_class,
                        framework='Struts' if base_class == 'Action' else 'Struts2'
                    )
                    entities.append(entity)
                    
                    # Extract execute methods
                    execute_pattern = r"public\s+\w+\s+(\w+)\s*\([^)]*\)\s*(?:throws\s+[^{]+)?\s*{"
                    for method_match in re.finditer(execute_pattern, content):
                        method_name = method_match.group(1)
                        if 'execute' in method_name.lower() or method_name in ['input', 'validate']:
                            method_line = content[:method_match.start()].count('\n') + 1
                            
                            method_entity = self.create_entity(
                                name=f"{class_name}.{method_name}",
                                entity_type='struts_method',
                                file_path=str(file_path),
                                line_number=method_line,
                                parent_class=class_name
                            )
                            entities.append(method_entity)
        
        except Exception as e:
            logger.warning(f"Error parsing Action class {file_path}: {e}")
        
        return entities
    
    def _parse_jsp(self, file_path: Path) -> List[Dict]:
        """Parse JSP files for Struts tags"""
        entities = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extract Struts tags
            struts_tags = re.findall(r'<s:(\w+)[^>]*>', content)
            unique_tags = set(struts_tags)
            
            if unique_tags:
                entity = self.create_entity(
                    name=file_path.stem,
                    entity_type='struts_jsp',
                    file_path=str(file_path),
                    line_number=1,
                    struts_tags=list(unique_tags),
                    tag_count=len(struts_tags)
                )
                entities.append(entity)
        
        except Exception as e:
            logger.warning(f"Error parsing JSP {file_path}: {e}")
        
        return entities
    
    def _extract_xml_dependencies(self, file_path: Path) -> List[str]:
        """Extract dependencies from XML configuration"""
        dependencies = []
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Extract action classes
            for action in root.findall('.//action'):
                action_class = action.get('class', '')
                if action_class:
                    dependencies.append(action_class)
            
            # Extract interceptor classes
            for interceptor in root.findall('.//interceptor'):
                interceptor_class = interceptor.get('class', '')
                if interceptor_class:
                    dependencies.append(interceptor_class)
        
        except Exception as e:
            logger.warning(f"Error extracting XML dependencies: {e}")
        
        return dependencies
    
    def _extract_java_dependencies(self, file_path: Path) -> List[str]:
        """Extract dependencies from Java files"""
        dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extract import statements
            import_pattern = r"import\s+([\w\.]+);"
            imports = re.findall(import_pattern, content)
            
            # Filter for Struts-related imports
            struts_imports = [imp for imp in imports if 'struts' in imp.lower() or 'apache' in imp.lower()]
            dependencies.extend(struts_imports)
        
        except Exception as e:
            logger.warning(f"Error extracting Java dependencies: {e}")
        
        return dependencies
