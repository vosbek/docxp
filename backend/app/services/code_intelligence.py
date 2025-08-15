"""
Code Intelligence Service - Enhanced In-Memory Analysis
Provides hierarchical organization and relationship tracking for code entities
"""

import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict, deque
from pathlib import Path
from dataclasses import dataclass, field
import re

from app.core.logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class CodeEntity:
    """Enhanced code entity with hierarchy and relationship information"""
    id: str
    name: str
    type: str  # module, class, method, function, interface, etc.
    file_path: str
    line_number: Optional[int] = None
    parent_id: Optional[str] = None
    children: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    parameters: List[str] = field(default_factory=list)
    docstring: Optional[str] = None
    complexity: Optional[int] = None
    business_rules: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CodeRelationship:
    """Represents a relationship between code entities"""
    source_id: str
    target_id: str
    relationship_type: str  # calls, inherits, implements, uses, creates, depends_on
    file_path: str
    line_number: Optional[int] = None
    context: Optional[str] = None  # additional context about the relationship

@dataclass
class BusinessRuleContext:
    """Enhanced business rule with hierarchical context and code traceability"""
    rule_id: str
    description: str
    plain_english: str
    confidence_score: float
    category: str
    code_entity_id: str
    module_path: str
    class_context: Optional[str] = None
    method_context: Optional[str] = None
    related_rules: List[str] = field(default_factory=list)
    business_impact: Optional[str] = None
    implementation_details: Optional[str] = None
    
    # Enhanced code traceability fields
    method_call_chain: Optional[str] = None  # Complete execution path
    boundary_spans: List[str] = field(default_factory=list)  # ["controller→service", "service→data"]
    file_locations: List[str] = field(default_factory=list)  # Specific file:line references
    integration_points: Optional[str] = None  # External system connections
    business_process: Optional[str] = None  # Business workflow mapping
    failure_impact: Optional[str] = None  # Business failure handling
    compliance_requirements: Optional[str] = None  # Regulatory enforcement details

class CodeIntelligenceGraph:
    """
    Enhanced in-memory graph for code intelligence and hierarchical organization
    Maintains relationships, hierarchy, and provides intelligent querying capabilities
    """
    
    def __init__(self):
        self.entities: Dict[str, CodeEntity] = {}
        self.relationships: List[CodeRelationship] = []
        self.hierarchy: Dict[str, Dict[str, List[str]]] = defaultdict(lambda: defaultdict(list))
        self.business_rules: Dict[str, BusinessRuleContext] = {}
        self.call_graph: Dict[str, List[str]] = defaultdict(list)
        self.reverse_call_graph: Dict[str, List[str]] = defaultdict(list)
        self.module_index: Dict[str, List[str]] = defaultdict(list)
        self.cross_references: Dict[str, Set[str]] = defaultdict(set)
        
        logger.info("Initialized CodeIntelligenceGraph")
    
    def add_entity(self, entity: CodeEntity) -> None:
        """Add a code entity to the graph"""
        self.entities[entity.id] = entity
        
        # Build module index
        module_path = self._extract_module_path(entity.file_path)
        self.module_index[module_path].append(entity.id)
        
        # Update hierarchy
        if entity.parent_id:
            parent = self.entities.get(entity.parent_id)
            if parent and entity.id not in parent.children:
                parent.children.append(entity.id)
        
        # Build hierarchy index by type
        self.hierarchy[module_path][entity.type].append(entity.id)
        
        logger.debug(f"Added entity: {entity.id} ({entity.type}) in {module_path}")
    
    def add_relationship(self, relationship: CodeRelationship) -> None:
        """Add a relationship between code entities"""
        self.relationships.append(relationship)
        
        # Update call graph for method calls
        if relationship.relationship_type == 'calls':
            self.call_graph[relationship.source_id].append(relationship.target_id)
            self.reverse_call_graph[relationship.target_id].append(relationship.source_id)
        
        # Update cross-references
        self.cross_references[relationship.source_id].add(relationship.target_id)
        self.cross_references[relationship.target_id].add(relationship.source_id)
        
        logger.debug(f"Added relationship: {relationship.source_id} {relationship.relationship_type} {relationship.target_id}")
    
    def add_business_rule(self, rule: BusinessRuleContext) -> None:
        """Add a business rule with its context"""
        self.business_rules[rule.rule_id] = rule
        
        # Link rule to entity
        if rule.code_entity_id in self.entities:
            self.entities[rule.code_entity_id].business_rules.append(rule.rule_id)
        
        logger.debug(f"Added business rule: {rule.rule_id} for entity {rule.code_entity_id}")
    
    def get_entity_hierarchy(self, entity_id: str) -> List[CodeEntity]:
        """Get the complete hierarchy path for an entity (from root to entity)"""
        hierarchy_path = []
        current_entity = self.entities.get(entity_id)
        
        # Build path from entity to root
        path_ids = []
        while current_entity:
            path_ids.append(current_entity.id)
            current_entity = self.entities.get(current_entity.parent_id) if current_entity.parent_id else None
        
        # Reverse to get root-to-entity path
        path_ids.reverse()
        hierarchy_path = [self.entities[eid] for eid in path_ids if eid in self.entities]
        
        return hierarchy_path
    
    def get_module_structure(self, module_path: str) -> Dict[str, Any]:
        """Get the complete structure of a module"""
        structure = {
            'module_path': module_path,
            'entities_by_type': {},
            'hierarchy': {},
            'total_entities': 0,
            'business_rules_count': 0
        }
        
        # Get all entities in this module
        entity_ids = self.module_index.get(module_path, [])
        structure['total_entities'] = len(entity_ids)
        
        # Group by type
        for entity_id in entity_ids:
            entity = self.entities.get(entity_id)
            if entity:
                if entity.type not in structure['entities_by_type']:
                    structure['entities_by_type'][entity.type] = []
                structure['entities_by_type'][entity.type].append(entity)
                
                # Count business rules
                structure['business_rules_count'] += len(entity.business_rules)
        
        # Build hierarchical structure
        structure['hierarchy'] = self._build_module_hierarchy(entity_ids)
        
        return structure
    
    def get_business_rules_by_hierarchy(self) -> Dict[str, Any]:
        """Organize business rules by code hierarchy"""
        organized_rules = {
            'by_module': defaultdict(list),
            'by_class': defaultdict(list),
            'by_method': defaultdict(list),
            'cross_cutting': []
        }
        
        for rule_id, rule in self.business_rules.items():
            entity = self.entities.get(rule.code_entity_id)
            if not entity:
                continue
            
            # Get hierarchy path
            hierarchy_path = self.get_entity_hierarchy(rule.code_entity_id)
            
            # Categorize by hierarchy level
            if entity.type == 'module':
                organized_rules['by_module'][rule.module_path].append(rule)
            elif entity.type in ['class', 'interface']:
                class_name = f"{rule.module_path}.{entity.name}"
                organized_rules['by_class'][class_name].append(rule)
            elif entity.type in ['method', 'function']:
                method_key = f"{rule.module_path}.{rule.class_context or ''}.{entity.name}".strip('.')
                organized_rules['by_method'][method_key].append(rule)
            else:
                # Check if it's a cross-cutting concern
                if len(rule.related_rules) > 2:  # Rules that relate to multiple other rules
                    organized_rules['cross_cutting'].append(rule)
        
        return organized_rules
    
    def find_related_entities(self, entity_id: str, max_depth: int = 2) -> List[CodeEntity]:
        """Find entities related to the given entity within max_depth relationships"""
        visited = set()
        queue = deque([(entity_id, 0)])
        related_entities = []
        
        while queue:
            current_id, depth = queue.popleft()
            
            if current_id in visited or depth > max_depth:
                continue
            
            visited.add(current_id)
            
            if depth > 0:  # Don't include the starting entity
                entity = self.entities.get(current_id)
                if entity:
                    related_entities.append(entity)
            
            # Add related entities to queue
            for related_id in self.cross_references.get(current_id, set()):
                if related_id not in visited:
                    queue.append((related_id, depth + 1))
        
        return related_entities
    
    def get_call_chain(self, method_id: str, max_depth: int = 3) -> List[List[str]]:
        """Get call chains starting from the given method"""
        call_chains = []
        
        def dfs(current_id: str, path: List[str], depth: int):
            if depth > max_depth or current_id in path:  # Avoid cycles
                return
            
            new_path = path + [current_id]
            called_methods = self.call_graph.get(current_id, [])
            
            if not called_methods or depth == max_depth:
                call_chains.append(new_path)
            else:
                for called_method in called_methods:
                    dfs(called_method, new_path, depth + 1)
        
        dfs(method_id, [], 0)
        return call_chains
    
    def get_impact_analysis(self, entity_id: str) -> Dict[str, Any]:
        """Analyze the impact of changes to the given entity"""
        entity = self.entities.get(entity_id)
        if not entity:
            return {}
        
        # Find what depends on this entity
        dependents = self.reverse_call_graph.get(entity_id, [])
        dependent_entities = [self.entities[dep_id] for dep_id in dependents if dep_id in self.entities]
        
        # Find what this entity depends on
        dependencies = self.call_graph.get(entity_id, [])
        dependency_entities = [self.entities[dep_id] for dep_id in dependencies if dep_id in self.entities]
        
        # Calculate impact scope
        all_affected = set(dependents)
        for dep_id in dependents:
            # Recursively find dependents of dependents
            second_level = self.reverse_call_graph.get(dep_id, [])
            all_affected.update(second_level)
        
        return {
            'entity': entity,
            'direct_dependents': dependent_entities,
            'direct_dependencies': dependency_entities,
            'total_affected_entities': len(all_affected),
            'affected_modules': len(set(self._extract_module_path(self.entities[eid].file_path) 
                                       for eid in all_affected if eid in self.entities)),
            'business_rules_affected': len([rule_id for rule_id in entity.business_rules]),
            'risk_level': self._calculate_risk_level(len(dependents), len(all_affected))
        }
    
    def search_entities(self, query: str, entity_types: Optional[List[str]] = None) -> List[CodeEntity]:
        """Search entities by name, docstring, or other criteria"""
        query_lower = query.lower()
        results = []
        
        for entity in self.entities.values():
            if entity_types and entity.type not in entity_types:
                continue
            
            # Search in name, docstring, and metadata
            if (query_lower in entity.name.lower() or
                (entity.docstring and query_lower in entity.docstring.lower()) or
                any(query_lower in str(value).lower() for value in entity.metadata.values())):
                results.append(entity)
        
        # Sort by relevance (exact name matches first)
        results.sort(key=lambda e: (
            0 if query_lower == e.name.lower() else
            1 if e.name.lower().startswith(query_lower) else
            2 if query_lower in e.name.lower() else 3
        ))
        
        return results
    
    def _extract_module_path(self, file_path: str) -> str:
        """Extract module path from file path"""
        path = Path(file_path)
        # Remove file extension and convert path separators to dots
        module_parts = path.with_suffix('').parts
        
        # Skip common source directories
        skip_dirs = {'src', 'app', 'backend', 'main', 'java', 'python'}
        filtered_parts = [part for part in module_parts if part not in skip_dirs]
        
        return '.'.join(filtered_parts) if filtered_parts else path.stem
    
    def _build_module_hierarchy(self, entity_ids: List[str]) -> Dict[str, Any]:
        """Build hierarchical structure for entities in a module"""
        hierarchy = {}
        
        # Find root entities (those without parents in this module)
        root_entities = []
        for entity_id in entity_ids:
            entity = self.entities.get(entity_id)
            if entity and (not entity.parent_id or entity.parent_id not in entity_ids):
                root_entities.append(entity)
        
        # Build tree structure
        def build_tree(entity: CodeEntity) -> Dict[str, Any]:
            return {
                'entity': entity,
                'children': [build_tree(self.entities[child_id]) 
                           for child_id in entity.children 
                           if child_id in self.entities]
            }
        
        hierarchy['roots'] = [build_tree(entity) for entity in root_entities]
        return hierarchy
    
    def _calculate_risk_level(self, direct_dependents: int, total_affected: int) -> str:
        """Calculate risk level based on dependency metrics"""
        if direct_dependents == 0:
            return "Low"
        elif direct_dependents <= 2 and total_affected <= 5:
            return "Low"
        elif direct_dependents <= 5 and total_affected <= 15:
            return "Medium"
        elif direct_dependents <= 10 and total_affected <= 30:
            return "High"
        else:
            return "Critical"
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the code intelligence graph"""
        return {
            'total_entities': len(self.entities),
            'total_relationships': len(self.relationships),
            'total_business_rules': len(self.business_rules),
            'modules_count': len(self.module_index),
            'entities_by_type': {
                entity_type: len([e for e in self.entities.values() if e.type == entity_type])
                for entity_type in set(e.type for e in self.entities.values())
            },
            'relationships_by_type': {
                rel_type: len([r for r in self.relationships if r.relationship_type == rel_type])
                for rel_type in set(r.relationship_type for r in self.relationships)
            },
            'avg_complexity': sum(e.complexity for e in self.entities.values() if e.complexity) / 
                           len([e for e in self.entities.values() if e.complexity]) if 
                           [e for e in self.entities.values() if e.complexity] else 0
        }

# Global instance for use across the application
code_intelligence = CodeIntelligenceGraph()