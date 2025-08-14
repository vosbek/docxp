"""
CORBA IDL Parser for Enterprise Legacy Migration Analysis

Enhanced parser for CORBA Interface Definition Language (IDL) files with focus on:
- Legacy system migration assessment
- Modernization opportunity identification  
- Integration pattern analysis
- Service dependency mapping
"""

import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.parsers.base_parser import BaseParser
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class CorbaParser(BaseParser):
    """Enhanced parser for CORBA IDL files with enterprise migration analysis"""
    
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
            
            # Perform enterprise migration analysis
            migration_analysis = self._analyze_migration_patterns(
                content, modules, interfaces, structs, exceptions, enums, str(file_path)
            )
            if migration_analysis:
                entities.append(migration_analysis)
            
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
    
    def _analyze_migration_patterns(self, content: str, modules: List[Dict], interfaces: List[Dict], 
                                   structs: List[Dict], exceptions: List[Dict], enums: List[Dict], 
                                   file_path: str) -> Optional[Dict[str, Any]]:
        """Analyze CORBA patterns for enterprise migration planning"""
        if not interfaces and not structs and not enums:
            return None
        
        # Calculate migration complexity
        complexity_score = self._calculate_migration_complexity(interfaces, structs, enums)
        
        # Identify modernization opportunities
        modernization_ops = self._identify_modernization_opportunities(interfaces, structs)
        
        # Analyze service patterns
        service_patterns = self._analyze_service_patterns(interfaces, content)
        
        # Analyze data structure complexity
        data_analysis = self._analyze_data_structures(structs, enums)
        
        # Generate migration recommendations
        recommendations = self._generate_migration_recommendations(
            interfaces, structs, complexity_score, modernization_ops
        )
        
        return self.create_entity(
            name="CORBA_Migration_Analysis",
            entity_type='corba_migration_analysis',
            file_path=file_path,
            line_number=1,
            docstring="Enterprise CORBA migration analysis and recommendations",
            complexity_score=complexity_score,
            total_interfaces=len(interfaces),
            total_structs=len(structs),
            total_enums=len(enums),
            modernization_opportunities=modernization_ops,
            service_patterns=service_patterns,
            data_analysis=data_analysis,
            migration_recommendations=recommendations,
            migration_priority=self._determine_migration_priority(complexity_score, len(interfaces))
        )
    
    def _calculate_migration_complexity(self, interfaces: List[Dict], structs: List[Dict], 
                                       enums: List[Dict]) -> str:
        """Calculate migration complexity based on CORBA constructs"""
        complexity_points = 0
        
        # Interface complexity (methods and inheritance add complexity)
        for interface in interfaces:
            complexity_points += 5  # Base complexity per interface
            if interface.get('inheritance'):
                complexity_points += 10  # Inheritance increases complexity
        
        # Data structure complexity
        complexity_points += len(structs) * 3
        complexity_points += len(enums) * 1
        
        # Determine complexity level
        if complexity_points < 15:
            return "Low"
        elif complexity_points < 40:
            return "Medium"
        elif complexity_points < 80:
            return "High"
        else:
            return "Very High"
    
    def _identify_modernization_opportunities(self, interfaces: List[Dict], 
                                            structs: List[Dict]) -> List[str]:
        """Identify specific modernization opportunities"""
        opportunities = []
        
        # REST API conversion opportunities
        if interfaces:
            opportunities.append(f"Convert {len(interfaces)} CORBA interfaces to REST APIs")
            
            # Look for CRUD-like operations
            crud_keywords = ['create', 'read', 'update', 'delete', 'get', 'set', 'list', 'find']
            crud_candidates = 0
            
            for interface in interfaces:
                interface_name = interface.get('name', '').lower()
                if any(keyword in interface_name for keyword in crud_keywords):
                    crud_candidates += 1
            
            if crud_candidates > 0:
                opportunities.append(f"{crud_candidates} interfaces are candidates for RESTful API conversion")
        
        # Data structure modernization
        if structs:
            opportunities.append(f"Modernize {len(structs)} data structures to JSON/XML schemas")
            
            # Check for simple structures suitable for JSON
            json_suitable = sum(1 for struct in structs if len(struct.get('members', [])) <= 10)
            if json_suitable > 0:
                opportunities.append(f"{json_suitable} structs are suitable for JSON serialization")
        
        # Microservices decomposition
        if len(interfaces) > 5:
            opportunities.append("Large interface count suggests microservices decomposition opportunities")
        
        return opportunities
    
    def _analyze_service_patterns(self, interfaces: List[Dict], content: str) -> Dict[str, Any]:
        """Analyze CORBA service patterns"""
        patterns = {
            'synchronous_services': 0,
            'asynchronous_services': 0,
            'callback_patterns': 0,
            'service_registry_patterns': 0,
            'legacy_patterns': []
        }
        
        # Count oneway (asynchronous) vs regular (synchronous) operations
        oneway_count = content.lower().count('oneway')
        patterns['asynchronous_services'] = oneway_count
        patterns['synchronous_services'] = len(interfaces) - oneway_count
        
        # Look for callback patterns
        callback_keywords = ['callback', 'notify', 'event', 'signal', 'observer']
        for interface in interfaces:
            interface_name = interface.get('name', '').lower()
            if any(keyword in interface_name for keyword in callback_keywords):
                patterns['callback_patterns'] += 1
        
        # Look for service registry patterns
        registry_keywords = ['registry', 'locator', 'finder', 'resolver', 'directory']
        for interface in interfaces:
            interface_name = interface.get('name', '').lower()
            if any(keyword in interface_name for keyword in registry_keywords):
                patterns['service_registry_patterns'] += 1
        
        # Identify legacy patterns that need modernization
        if patterns['synchronous_services'] > patterns['asynchronous_services']:
            patterns['legacy_patterns'].append("Heavy reliance on synchronous calls - consider async patterns")
        
        if patterns['callback_patterns'] > 0:
            patterns['legacy_patterns'].append("Callback patterns detected - consider event-driven architecture")
        
        return patterns
    
    def _analyze_data_structures(self, structs: List[Dict], enums: List[Dict]) -> Dict[str, Any]:
        """Analyze data structure patterns for migration assessment"""
        analysis = {
            'total_structures': len(structs) + len(enums),
            'complex_structures': 0,
            'simple_structures': 0,
            'json_compatible': 0,
            'migration_challenges': []
        }
        
        # Analyze struct complexity
        for struct in structs:
            member_count = len(struct.get('members', []))
            if member_count > 10:
                analysis['complex_structures'] += 1
            else:
                analysis['simple_structures'] += 1
            
            # Check for JSON compatibility (simplified heuristic)
            members = struct.get('members', [])
            if members and all(self._is_basic_type(member) for member in members):
                analysis['json_compatible'] += 1
        
        # Identify migration challenges
        if analysis['complex_structures'] > analysis['simple_structures']:
            analysis['migration_challenges'].append("Many complex data structures may require careful schema design")
        
        if analysis['json_compatible'] < len(structs) / 2:
            analysis['migration_challenges'].append("Some data structures may not directly map to JSON")
        
        return analysis
    
    def _is_basic_type(self, member: str) -> bool:
        """Check if a struct member uses basic types suitable for JSON"""
        basic_types = ['string', 'long', 'short', 'boolean', 'double', 'float', 'char']
        return any(basic_type in member.lower() for basic_type in basic_types)
    
    def _generate_migration_recommendations(self, interfaces: List[Dict], structs: List[Dict], 
                                          complexity_score: str, modernization_ops: List[str]) -> List[str]:
        """Generate specific migration recommendations"""
        recommendations = []
        
        # Complexity-based recommendations
        if complexity_score in ["High", "Very High"]:
            recommendations.append("High complexity detected - recommend phased migration approach")
            recommendations.append("Consider creating API gateway to abstract CORBA complexity during transition")
        else:
            recommendations.append("Moderate complexity - direct migration to REST APIs feasible")
        
        # Interface-specific recommendations
        if interfaces:
            recommendations.append(f"Migrate {len(interfaces)} CORBA interfaces using these strategies:")
            recommendations.append("  1. Create REST API endpoints for each interface method")
            recommendations.append("  2. Implement request/response DTOs based on existing structs")
            recommendations.append("  3. Add proper error handling and status codes")
        
        # Data structure recommendations
        if structs:
            recommendations.append("Data structure migration strategy:")
            recommendations.append("  1. Convert CORBA structs to JSON schemas or DTOs")
            recommendations.append("  2. Validate data transformation mappings")
            recommendations.append("  3. Consider using OpenAPI/Swagger for API documentation")
        
        # Technology stack recommendations
        recommendations.append("Consider modern alternatives:")
        recommendations.append("  - REST APIs with JSON for simple request/response patterns")
        recommendations.append("  - gRPC for high-performance, strongly-typed service communication")
        recommendations.append("  - GraphQL for flexible data querying requirements")
        recommendations.append("  - Message queues (Kafka/RabbitMQ) for asynchronous communication")
        
        return recommendations
    
    def _determine_migration_priority(self, complexity_score: str, interface_count: int) -> str:
        """Determine migration priority based on analysis"""
        if complexity_score == "Very High" or interface_count > 20:
            return "High Priority - Complex legacy system requiring immediate attention"
        elif complexity_score == "High" or interface_count > 10:
            return "Medium Priority - Significant modernization effort required"
        elif complexity_score == "Medium" or interface_count > 5:
            return "Low Priority - Manageable migration effort"
        else:
            return "Very Low Priority - Simple migration candidate"
