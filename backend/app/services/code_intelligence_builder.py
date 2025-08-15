"""
Code Intelligence Builder - Converts parsed entities to hierarchical intelligence graph
Integrates with existing parsers to build the CodeIntelligenceGraph
"""

import logging
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import re

from app.services.code_intelligence import (
    CodeIntelligenceGraph, CodeEntity, CodeRelationship, BusinessRuleContext,
    code_intelligence
)
from app.models.schemas import BusinessRule
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class CodeIntelligenceBuilder:
    """
    Builds the CodeIntelligenceGraph from existing parsed entities
    Converts flat entity lists into hierarchical, relationship-aware structures
    """
    
    def __init__(self, intelligence_graph: Optional[CodeIntelligenceGraph] = None):
        self.graph = intelligence_graph or code_intelligence
        self.entity_id_map: Dict[str, str] = {}  # Maps original entity keys to new IDs
        self.file_modules: Dict[str, str] = {}  # Maps file paths to module IDs
        
    def build_from_entities(self, entities: List[Dict[str, Any]]) -> CodeIntelligenceGraph:
        """
        Build the complete intelligence graph from parsed entities
        """
        logger.info(f"Building intelligence graph from {len(entities)} entities")
        
        # Clear existing graph
        self.graph = CodeIntelligenceGraph()
        self.entity_id_map.clear()
        self.file_modules.clear()
        
        # Phase 1: Create all entities and establish basic hierarchy
        self._create_entities_and_modules(entities)
        
        # Phase 2: Build relationships between entities
        self._build_relationships(entities)
        
        # Phase 3: Analyze call patterns and dependencies
        self._analyze_call_patterns(entities)
        
        # Phase 4: Build cross-references and navigation
        self._build_cross_references()
        
        stats = self.graph.get_statistics()
        logger.info(f"Built intelligence graph: {stats['total_entities']} entities, "
                   f"{stats['total_relationships']} relationships, "
                   f"{stats['modules_count']} modules")
        
        return self.graph
    
    def add_business_rules(self, business_rules: List[BusinessRule]) -> None:
        """
        Add business rules to the intelligence graph with proper hierarchy context
        """
        logger.info(f"Adding {len(business_rules)} business rules to intelligence graph")
        
        for rule in business_rules:
            # Find the entity this rule belongs to
            entity_id = self._find_entity_for_rule(rule)
            if not entity_id:
                logger.warning(f"Could not find entity for business rule {rule.id}")
                continue
            
            # Get hierarchy context
            entity = self.graph.entities.get(entity_id)
            hierarchy_path = self.graph.get_entity_hierarchy(entity_id) if entity else []
            
            # Extract class and method context
            class_context = None
            method_context = None
            for ancestor in hierarchy_path:
                if ancestor.type in ['class', 'interface']:
                    class_context = ancestor.name
                elif ancestor.type in ['method', 'function']:
                    method_context = ancestor.name
            
            # Create enhanced business rule context
            rule_context = BusinessRuleContext(
                rule_id=rule.id,
                description=rule.description,
                plain_english="",  # Will be filled by enhanced AI prompts
                confidence_score=rule.confidence_score,
                category=rule.category,
                code_entity_id=entity_id,
                module_path=self._extract_module_path(rule.code_reference),
                class_context=class_context,
                method_context=method_context,
                related_rules=[],  # Will be built from rule relationships
                business_impact=getattr(rule, 'business_impact', None),
                implementation_details=getattr(rule, 'validation_logic', None)
            )
            
            self.graph.add_business_rule(rule_context)
        
        # Build rule relationships
        self._build_rule_relationships()
        
        logger.info(f"Successfully added {len(self.graph.business_rules)} business rules")
    
    def _create_entities_and_modules(self, entities: List[Dict[str, Any]]) -> None:
        """Create entities and establish module hierarchy"""
        
        # First pass: Group entities by file to create modules
        entities_by_file = {}
        for entity in entities:
            file_path = entity.get('file_path', '')
            if file_path not in entities_by_file:
                entities_by_file[file_path] = []
            entities_by_file[file_path].append(entity)
        
        # Create module entities for each file
        for file_path, file_entities in entities_by_file.items():
            module_entity = self._create_module_entity(file_path)
            self.graph.add_entity(module_entity)
            self.file_modules[file_path] = module_entity.id
        
        # Second pass: Create all other entities with proper hierarchy
        for entity in entities:
            code_entity = self._convert_to_code_entity(entity)
            if code_entity:
                self.graph.add_entity(code_entity)
    
    def _create_module_entity(self, file_path: str) -> CodeEntity:
        """Create a module entity from a file path"""
        module_path = self._extract_module_path(file_path)
        module_id = f"module:{module_path}"
        
        return CodeEntity(
            id=module_id,
            name=Path(file_path).stem,
            type='module',
            file_path=file_path,
            metadata={
                'module_path': module_path,
                'full_path': file_path,
                'file_size': self._get_file_size(file_path)
            }
        )
    
    def _convert_to_code_entity(self, entity: Dict[str, Any]) -> Optional[CodeEntity]:
        """Convert a parsed entity to a CodeEntity"""
        name = entity.get('name', 'unknown')
        entity_type = entity.get('type', 'unknown')
        file_path = entity.get('file_path', '')
        
        # Generate stable ID
        entity_id = self._generate_entity_id(entity)
        
        # Determine parent (module or class)
        parent_id = self._determine_parent_id(entity)
        
        # Extract additional information
        parameters = entity.get('parameters', [])
        docstring = entity.get('docstring', '')
        complexity = entity.get('complexity', 0)
        dependencies = entity.get('dependencies', [])
        
        code_entity = CodeEntity(
            id=entity_id,
            name=name,
            type=entity_type,
            file_path=file_path,
            line_number=entity.get('line_number'),
            parent_id=parent_id,
            dependencies=dependencies,
            parameters=parameters,
            docstring=docstring,
            complexity=complexity if isinstance(complexity, int) else 0,
            metadata={
                'original_entity': entity,
                'language': self._detect_language(file_path),
                'visibility': entity.get('visibility', 'public'),
                'is_abstract': entity.get('is_abstract', False),
                'design_patterns': entity.get('design_patterns', [])
            }
        )
        
        # Store mapping for relationship building
        self.entity_id_map[self._get_entity_key(entity)] = entity_id
        
        return code_entity
    
    def _determine_parent_id(self, entity: Dict[str, Any]) -> Optional[str]:
        """Determine the parent entity ID for proper hierarchy"""
        file_path = entity.get('file_path', '')
        entity_type = entity.get('type', '')
        
        # Methods and functions belong to classes if available
        if entity_type in ['method', 'function']:
            # Look for class context in the entity
            class_name = entity.get('class_name') or entity.get('parent_class')
            if class_name:
                class_key = f"{file_path}:class:{class_name}"
                return self.entity_id_map.get(class_key)
        
        # Classes and top-level functions belong to modules
        if entity_type in ['class', 'interface', 'function'] or not entity.get('parent_class'):
            return self.file_modules.get(file_path)
        
        return None
    
    def _build_relationships(self, entities: List[Dict[str, Any]]) -> None:
        """Build relationships between entities"""
        logger.info("Building entity relationships")
        
        for entity in entities:
            entity_id = self.entity_id_map.get(self._get_entity_key(entity))
            if not entity_id:
                continue
            
            # Build dependency relationships
            dependencies = entity.get('dependencies', [])
            for dep in dependencies:
                target_id = self._find_dependency_target(dep, entity.get('file_path', ''))
                if target_id:
                    relationship = CodeRelationship(
                        source_id=entity_id,
                        target_id=target_id,
                        relationship_type='depends_on',
                        file_path=entity.get('file_path', ''),
                        line_number=entity.get('line_number'),
                        context=f"imports {dep}"
                    )
                    self.graph.add_relationship(relationship)
            
            # Build inheritance relationships
            if entity.get('base_classes'):
                for base_class in entity.get('base_classes', []):
                    target_id = self._find_class_target(base_class, entity.get('file_path', ''))
                    if target_id:
                        relationship = CodeRelationship(
                            source_id=entity_id,
                            target_id=target_id,
                            relationship_type='inherits',
                            file_path=entity.get('file_path', ''),
                            line_number=entity.get('line_number'),
                            context=f"extends {base_class}"
                        )
                        self.graph.add_relationship(relationship)
    
    def _analyze_call_patterns(self, entities: List[Dict[str, Any]]) -> None:
        """Analyze method calls and build call graph"""
        logger.info("Analyzing call patterns")
        
        for entity in entities:
            if entity.get('type') not in ['method', 'function']:
                continue
            
            entity_id = self.entity_id_map.get(self._get_entity_key(entity))
            if not entity_id:
                continue
            
            # Analyze method body for calls (simplified pattern matching)
            method_body = entity.get('body', '') or entity.get('implementation', '')
            if method_body:
                called_methods = self._extract_method_calls(method_body)
                
                for called_method in called_methods:
                    target_id = self._find_method_target(called_method, entity.get('file_path', ''))
                    if target_id:
                        relationship = CodeRelationship(
                            source_id=entity_id,
                            target_id=target_id,
                            relationship_type='calls',
                            file_path=entity.get('file_path', ''),
                            context=f"calls {called_method}"
                        )
                        self.graph.add_relationship(relationship)
    
    def _build_cross_references(self) -> None:
        """Build cross-reference indexes for fast navigation"""
        logger.info("Building cross-reference indexes")
        
        # This is already handled by the CodeIntelligenceGraph.add_relationship method
        # which automatically updates cross_references
        pass
    
    def _build_rule_relationships(self) -> None:
        """Build relationships between business rules"""
        logger.info("Building business rule relationships")
        
        # Find rules that might be related based on:
        # 1. Same entity or related entities
        # 2. Similar categories
        # 3. Shared keywords in descriptions
        
        rules_list = list(self.graph.business_rules.values())
        
        for i, rule1 in enumerate(rules_list):
            for j, rule2 in enumerate(rules_list[i+1:], i+1):
                if self._are_rules_related(rule1, rule2):
                    rule1.related_rules.append(rule2.rule_id)
                    rule2.related_rules.append(rule1.rule_id)
    
    def _are_rules_related(self, rule1: BusinessRuleContext, rule2: BusinessRuleContext) -> bool:
        """Determine if two business rules are related"""
        # Same entity or related entities
        if rule1.code_entity_id == rule2.code_entity_id:
            return True
        
        # Same class context
        if rule1.class_context and rule1.class_context == rule2.class_context:
            return True
        
        # Similar categories
        if rule1.category == rule2.category:
            return True
        
        # Shared keywords (simple approach)
        words1 = set(rule1.description.lower().split())
        words2 = set(rule2.description.lower().split())
        common_words = words1.intersection(words2)
        
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'cannot', 'this', 'that', 'these', 'those'}
        meaningful_words = common_words - stop_words
        
        return len(meaningful_words) >= 2
    
    def _generate_entity_id(self, entity: Dict[str, Any]) -> str:
        """Generate a stable, unique ID for an entity"""
        name = entity.get('name', 'unknown')
        entity_type = entity.get('type', 'unknown')
        file_path = entity.get('file_path', '')
        line_number = entity.get('line_number', 0)
        
        # Create a unique identifier
        unique_string = f"{file_path}:{entity_type}:{name}:{line_number}"
        return f"{entity_type}:{hashlib.md5(unique_string.encode()).hexdigest()[:8]}"
    
    def _get_entity_key(self, entity: Dict[str, Any]) -> str:
        """Get a key for entity lookup"""
        return f"{entity.get('file_path', '')}:{entity.get('type', '')}:{entity.get('name', '')}"
    
    def _extract_module_path(self, file_path: str) -> str:
        """Extract module path from file path"""
        path = Path(file_path)
        # Remove file extension and convert path separators to dots
        module_parts = path.with_suffix('').parts
        
        # Skip common source directories
        skip_dirs = {'src', 'app', 'backend', 'main', 'java', 'python', 'frontend', 'ui'}
        filtered_parts = [part for part in module_parts if part not in skip_dirs]
        
        return '.'.join(filtered_parts) if filtered_parts else path.stem
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file path"""
        extension = Path(file_path).suffix.lower()
        language_map = {
            '.py': 'python',
            '.java': 'java', 
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'react',
            '.tsx': 'react-typescript',
            '.jsp': 'jsp',
            '.sql': 'sql',
            '.xml': 'xml',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.less': 'less'
        }
        return language_map.get(extension, 'unknown')
    
    def _get_file_size(self, file_path: str) -> int:
        """Get file size safely"""
        try:
            return Path(file_path).stat().st_size
        except:
            return 0
    
    def _find_entity_for_rule(self, rule: BusinessRule) -> Optional[str]:
        """Find the entity ID that a business rule belongs to"""
        # Try to match by code reference
        code_ref = rule.code_reference
        
        # Parse code reference (format: file_path:function_name or file_path:class.method)
        if ':' in code_ref:
            file_part, code_part = code_ref.split(':', 1)
            
            # Look for exact matches in entities
            for entity_id, entity in self.graph.entities.items():
                if entity.file_path.endswith(file_part) or file_part in entity.file_path:
                    if code_part in entity.name or entity.name in code_part:
                        return entity_id
        
        # Fallback: match by file path only
        for entity_id, entity in self.graph.entities.items():
            if code_ref in entity.file_path:
                return entity_id
        
        return None
    
    def _find_dependency_target(self, dependency: str, source_file: str) -> Optional[str]:
        """Find the target entity for a dependency"""
        # This is simplified - in a real implementation, you'd need
        # sophisticated import resolution logic
        for entity_id, entity in self.graph.entities.items():
            if dependency in entity.name or entity.name in dependency:
                return entity_id
        return None
    
    def _find_class_target(self, class_name: str, source_file: str) -> Optional[str]:
        """Find the target entity for a class reference"""
        for entity_id, entity in self.graph.entities.items():
            if entity.type in ['class', 'interface'] and entity.name == class_name:
                return entity_id
        return None
    
    def _find_method_target(self, method_call: str, source_file: str) -> Optional[str]:
        """Find the target entity for a method call"""
        # Extract method name from call (remove parentheses, parameters)
        method_name = re.sub(r'\(.*\)', '', method_call).strip()
        
        for entity_id, entity in self.graph.entities.items():
            if entity.type in ['method', 'function'] and entity.name == method_name:
                return entity_id
        return None
    
    def _extract_method_calls(self, method_body: str) -> List[str]:
        """Extract method calls from method body (simplified)"""
        # This is a simplified pattern - real implementation would need
        # language-specific AST parsing
        pattern = r'(\w+)\s*\('
        matches = re.findall(pattern, method_body)
        
        # Filter out common keywords and built-in functions
        keywords = {'if', 'for', 'while', 'try', 'catch', 'switch', 'return', 'new', 'delete', 'typeof', 'instanceof'}
        return [match for match in matches if match not in keywords and len(match) > 1]

# Global instance
code_intelligence_builder = CodeIntelligenceBuilder()