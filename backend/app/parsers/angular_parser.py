"""
Angular/TypeScript parser
"""

import logging
import re
from pathlib import Path
from typing import List, Dict, Any

from app.parsers.base_parser import BaseParser

logger = logging.getLogger(__name__)

class AngularParser(BaseParser):
    """Parser for Angular/TypeScript files"""
    
    def parse(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse Angular/TypeScript file and extract entities"""
        entities = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extract components
            components = self._extract_components(content, str(file_path))
            entities.extend(components)
            
            # Extract services
            services = self._extract_services(content, str(file_path))
            entities.extend(services)
            
            # Extract modules
            modules = self._extract_modules(content, str(file_path))
            entities.extend(modules)
            
            # Extract interfaces
            interfaces = self._extract_interfaces(content, str(file_path))
            entities.extend(interfaces)
            
        except Exception as e:
            logger.warning(f"Error parsing {file_path}: {e}")
        
        return entities
    
    def extract_dependencies(self, file_path: Path) -> List[str]:
        """Extract import statements from Angular/TypeScript file"""
        dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Match import statements
            import_pattern = r"import\s+.*?\s+from\s+['\"]([^'\"]+)['\"]"
            imports = re.findall(import_pattern, content)
            dependencies.extend(imports)
            
        except Exception as e:
            logger.warning(f"Error extracting dependencies from {file_path}: {e}")
        
        return list(set(dependencies))
    
    def _extract_components(self, content: str, file_path: str) -> List[Dict]:
        """Extract Angular components"""
        entities = []
        
        # Match @Component decorator
        component_pattern = r"@Component\s*\(\s*{[^}]*}\s*\)\s*export\s+class\s+(\w+)"
        matches = re.finditer(component_pattern, content, re.DOTALL)
        
        for match in matches:
            component_name = match.group(1)
            line_number = content[:match.start()].count('\n') + 1
            
            entity = self.create_entity(
                name=component_name,
                entity_type='component',
                file_path=file_path,
                line_number=line_number,
                framework='Angular'
            )
            entities.append(entity)
        
        return entities
    
    def _extract_services(self, content: str, file_path: str) -> List[Dict]:
        """Extract Angular services"""
        entities = []
        
        # Match @Injectable decorator
        service_pattern = r"@Injectable\s*\(\s*.*?\s*\)\s*export\s+class\s+(\w+)"
        matches = re.finditer(service_pattern, content, re.DOTALL)
        
        for match in matches:
            service_name = match.group(1)
            line_number = content[:match.start()].count('\n') + 1
            
            entity = self.create_entity(
                name=service_name,
                entity_type='service',
                file_path=file_path,
                line_number=line_number,
                framework='Angular'
            )
            entities.append(entity)
        
        return entities
    
    def _extract_modules(self, content: str, file_path: str) -> List[Dict]:
        """Extract Angular modules"""
        entities = []
        
        # Match @NgModule decorator
        module_pattern = r"@NgModule\s*\(\s*{[^}]*}\s*\)\s*export\s+class\s+(\w+)"
        matches = re.finditer(module_pattern, content, re.DOTALL)
        
        for match in matches:
            module_name = match.group(1)
            line_number = content[:match.start()].count('\n') + 1
            
            entity = self.create_entity(
                name=module_name,
                entity_type='module',
                file_path=file_path,
                line_number=line_number,
                framework='Angular'
            )
            entities.append(entity)
        
        return entities
    
    def _extract_interfaces(self, content: str, file_path: str) -> List[Dict]:
        """Extract TypeScript interfaces"""
        entities = []
        
        # Match interface declarations
        interface_pattern = r"export\s+interface\s+(\w+)"
        matches = re.finditer(interface_pattern, content)
        
        for match in matches:
            interface_name = match.group(1)
            line_number = content[:match.start()].count('\n') + 1
            
            entity = self.create_entity(
                name=interface_name,
                entity_type='interface',
                file_path=file_path,
                line_number=line_number,
                language='TypeScript'
            )
            entities.append(entity)
        
        return entities
