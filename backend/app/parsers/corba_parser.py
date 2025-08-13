"""
CORBA IDL parser for distributed object interfaces
"""

import logging
import re
from pathlib import Path
from typing import List, Dict, Any

from app.parsers.base_parser import BaseParser

logger = logging.getLogger(__name__)

class CorbaParser(BaseParser):
    """Parser for CORBA IDL (Interface Definition Language) files"""
    
    def parse(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse CORBA IDL files and extract entities"""
        entities = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Remove comments
            content = self._remove_comments(content)
            
            # Extract modules
            modules = self._extract_modules(content, str(file_path))
            entities.extend(modules)
            
            # Extract interfaces
            interfaces = self._extract_interfaces(content, str(file_path))
            entities.extend(interfaces)
            
            # Extract structs
            structs = self._extract_structs(content, str(file_path))
            entities.extend(structs)
            
            # Extract exceptions
            exceptions = self._extract_exceptions(content, str(file_path))
            entities.extend(exceptions)
            
            # Extract typedefs
            typedefs = self._extract_typedefs(content, str(file_path))
            entities.extend(typedefs)
            
            # Extract enums
            enums = self._extract_enums(content, str(file_path))
            entities.extend(enums)
            
        except Exception as e:
            logger.warning(f"Error parsing {file_path}: {e}")
        
        return entities
    
    def extract_dependencies(self, file_path: Path) -> List[str]:
        """Extract dependencies from CORBA IDL files"""
        dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extract #include statements
            include_pattern = r'#include\s+[<"]([^>"]+)[>"]'
            includes = re.findall(include_pattern, content)
            dependencies.extend(includes)
            
            # Extract inherited interfaces
            inheritance_pattern = r'interface\s+\w+\s*:\s*([\w:,\s]+)\s*{'
            for match in re.finditer(inheritance_pattern, content):
                parents = match.group(1).split(',')
                dependencies.extend([p.strip() for p in parents])
        
        except Exception as e:
            logger.warning(f"Error extracting dependencies from {file_path}: {e}")
        
        return list(set(dependencies))
    
    def _remove_comments(self, content: str) -> str:
        """Remove IDL comments from content"""
        # Remove single-line comments
        content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
        # Remove multi-line comments
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        return content
    
    def _extract_modules(self, content: str, file_path: str) -> List[Dict]:
        """Extract CORBA modules"""
        entities = []
        
        # Match module declarations
        module_pattern = r'module\s+(\w+)\s*{'
        matches = re.finditer(module_pattern, content)
        
        for match in matches:
            module_name = match.group(1)
            line_number = content[:match.start()].count('\n') + 1
            
            entity = self.create_entity(
                name=module_name,
                entity_type='corba_module',
                file_path=file_path,
                line_number=line_number,
                idl_type='module'
            )
            entities.append(entity)
        
        return entities
    
    def _extract_interfaces(self, content: str, file_path: str) -> List[Dict]:
        """Extract CORBA interfaces"""
        entities = []
        
        # Match interface declarations
        interface_pattern = r'interface\s+(\w+)(?:\s*:\s*([\w:,\s]+))?\s*{'
        matches = re.finditer(interface_pattern, content)
        
        for match in matches:
            interface_name = match.group(1)
            inheritance = match.group(2) if match.group(2) else None
            line_number = content[:match.start()].count('\n') + 1
            
            entity = self.create_entity(
                name=interface_name,
                entity_type='corba_interface',
                file_path=file_path,
                line_number=line_number,
                inheritance=inheritance.strip() if inheritance else None,
                idl_type='interface'
            )
            entities.append(entity)
            
            # Extract methods within interface
            interface_end = content.find('}', match.end())
            if interface_end != -1:
                interface_body = content[match.end():interface_end]
                methods = self._extract_interface_methods(interface_body, interface_name, file_path, line_number)
                entities.extend(methods)
        
        return entities
    
    def _extract_interface_methods(self, interface_body: str, interface_name: str, file_path: str, base_line: int) -> List[Dict]:
        """Extract methods from interface body"""
        entities = []
        
        # Match method declarations
        method_pattern = r'(\w+(?:\s*::\s*\w+)*)\s+(\w+)\s*\(([^)]*)\)'
        matches = re.finditer(method_pattern, interface_body)
        
        for match in matches:
            return_type = match.group(1)
            method_name = match.group(2)
            parameters = match.group(3)
            line_offset = interface_body[:match.start()].count('\n')
            
            # Check for oneway methods
            is_oneway = 'oneway' in interface_body[max(0, match.start()-20):match.start()]
            
            entity = self.create_entity(
                name=f"{interface_name}::{method_name}",
                entity_type='corba_method',
                file_path=file_path,
                line_number=base_line + line_offset + 1,
                return_type=return_type,
                parameters=parameters.strip(),
                interface=interface_name,
                is_oneway=is_oneway
            )
            entities.append(entity)
        
        # Extract attributes
        attribute_pattern = r'(?:readonly\s+)?attribute\s+(\w+(?:\s*::\s*\w+)*)\s+(\w+)'
        for match in re.finditer(attribute_pattern, interface_body):
            attr_type = match.group(1)
            attr_name = match.group(2)
            is_readonly = 'readonly' in interface_body[max(0, match.start()-10):match.start()]
            line_offset = interface_body[:match.start()].count('\n')
            
            entity = self.create_entity(
                name=f"{interface_name}::{attr_name}",
                entity_type='corba_attribute',
                file_path=file_path,
                line_number=base_line + line_offset + 1,
                attribute_type=attr_type,
                interface=interface_name,
                is_readonly=is_readonly
            )
            entities.append(entity)
        
        return entities
    
    def _extract_structs(self, content: str, file_path: str) -> List[Dict]:
        """Extract CORBA structs"""
        entities = []
        
        # Match struct declarations
        struct_pattern = r'struct\s+(\w+)\s*{'
        matches = re.finditer(struct_pattern, content)
        
        for match in matches:
            struct_name = match.group(1)
            line_number = content[:match.start()].count('\n') + 1
            
            # Extract struct members
            struct_end = content.find('}', match.end())
            if struct_end != -1:
                struct_body = content[match.end():struct_end]
                members = []
                member_pattern = r'(\w+(?:\s*::\s*\w+)*)\s+(\w+)\s*;'
                for member_match in re.finditer(member_pattern, struct_body):
                    member_type = member_match.group(1)
                    member_name = member_match.group(2)
                    members.append(f"{member_type} {member_name}")
                
                entity = self.create_entity(
                    name=struct_name,
                    entity_type='corba_struct',
                    file_path=file_path,
                    line_number=line_number,
                    members=members,
                    idl_type='struct'
                )
                entities.append(entity)
        
        return entities
    
    def _extract_exceptions(self, content: str, file_path: str) -> List[Dict]:
        """Extract CORBA exceptions"""
        entities = []
        
        # Match exception declarations
        exception_pattern = r'exception\s+(\w+)\s*{'
        matches = re.finditer(exception_pattern, content)
        
        for match in matches:
            exception_name = match.group(1)
            line_number = content[:match.start()].count('\n') + 1
            
            # Extract exception members
            exception_end = content.find('}', match.end())
            if exception_end != -1:
                exception_body = content[match.end():exception_end]
                members = []
                member_pattern = r'(\w+(?:\s*::\s*\w+)*)\s+(\w+)\s*;'
                for member_match in re.finditer(member_pattern, exception_body):
                    member_type = member_match.group(1)
                    member_name = member_match.group(2)
                    members.append(f"{member_type} {member_name}")
                
                entity = self.create_entity(
                    name=exception_name,
                    entity_type='corba_exception',
                    file_path=file_path,
                    line_number=line_number,
                    members=members,
                    idl_type='exception'
                )
                entities.append(entity)
        
        return entities
    
    def _extract_typedefs(self, content: str, file_path: str) -> List[Dict]:
        """Extract CORBA typedefs"""
        entities = []
        
        # Match typedef declarations
        typedef_pattern = r'typedef\s+([\w:<>\[\],\s]+)\s+(\w+)\s*;'
        matches = re.finditer(typedef_pattern, content)
        
        for match in matches:
            base_type = match.group(1).strip()
            alias_name = match.group(2)
            line_number = content[:match.start()].count('\n') + 1
            
            entity = self.create_entity(
                name=alias_name,
                entity_type='corba_typedef',
                file_path=file_path,
                line_number=line_number,
                base_type=base_type,
                idl_type='typedef'
            )
            entities.append(entity)
        
        return entities
    
    def _extract_enums(self, content: str, file_path: str) -> List[Dict]:
        """Extract CORBA enums"""
        entities = []
        
        # Match enum declarations
        enum_pattern = r'enum\s+(\w+)\s*{([^}]+)}'
        matches = re.finditer(enum_pattern, content)
        
        for match in matches:
            enum_name = match.group(1)
            enum_values = match.group(2)
            line_number = content[:match.start()].count('\n') + 1
            
            # Extract enum values
            values = [v.strip() for v in enum_values.split(',') if v.strip()]
            
            entity = self.create_entity(
                name=enum_name,
                entity_type='corba_enum',
                file_path=file_path,
                line_number=line_number,
                values=values,
                idl_type='enum'
            )
            entities.append(entity)
        
        return entities
