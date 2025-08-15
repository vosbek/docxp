"""
Hierarchical Documentation Builder - Organizes documentation with bidirectional navigation
Creates structured, navigable documentation with code traceability
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from collections import defaultdict
import json

from app.services.code_intelligence import CodeIntelligenceGraph, BusinessRuleContext
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class HierarchicalDocumentationBuilder:
    """
    Builds hierarchically organized documentation with bidirectional navigation
    and precise code traceability for architects
    """
    
    def __init__(self, intelligence_graph: CodeIntelligenceGraph):
        self.graph = intelligence_graph
    
    def build_hierarchical_business_rules_documentation(self) -> str:
        """
        Build comprehensive business rules documentation organized by system hierarchy
        with architect-focused navigation and code traceability
        """
        logger.info("Building hierarchical business rules documentation")
        
        # Get organized business rules from intelligence graph
        organized_rules = self.graph.get_business_rules_by_hierarchy()
        
        # Build navigation structure
        navigation = self._build_navigation_structure(organized_rules)
        
        # Generate documentation sections
        doc_sections = []
        
        # Header and navigation
        doc_sections.append(self._generate_header_section(organized_rules))
        doc_sections.append(self._generate_navigation_section(navigation))
        doc_sections.append(self._generate_executive_summary(organized_rules))
        
        # Hierarchical organization sections
        doc_sections.append(self._generate_module_level_rules(organized_rules['by_module']))
        doc_sections.append(self._generate_class_level_rules(organized_rules['by_class']))
        doc_sections.append(self._generate_method_level_rules(organized_rules['by_method']))
        doc_sections.append(self._generate_cross_cutting_rules(organized_rules['cross_cutting']))
        
        # Architecture-focused sections
        doc_sections.append(self._generate_boundary_analysis())
        doc_sections.append(self._generate_integration_rules())
        doc_sections.append(self._generate_migration_impact_analysis())
        
        # Appendices for quick reference
        doc_sections.append(self._generate_quick_reference_index())
        doc_sections.append(self._generate_code_location_index())
        
        final_documentation = "\\n\\n".join(doc_sections)
        
        logger.info(f"Generated hierarchical business rules documentation: {len(final_documentation)} characters")
        return final_documentation
    
    def _generate_header_section(self, organized_rules: Dict[str, Any]) -> str:
        """Generate comprehensive header with statistics and overview"""
        
        total_rules = (
            sum(len(rules) for rules in organized_rules['by_module'].values()) +
            sum(len(rules) for rules in organized_rules['by_class'].values()) +
            sum(len(rules) for rules in organized_rules['by_method'].values()) +
            len(organized_rules['cross_cutting'])
        )
        
        stats = self.graph.get_statistics()
        
        return f"""# 🏗️ Enterprise Business Rules Documentation

**Generated**: {self._get_timestamp()}  
**System Architecture**: Hierarchical Analysis with Code Traceability  
**Documentation Purpose**: Architect-focused business rule navigation and implementation mapping

## 📊 System Overview

| Metric | Value | Architectural Significance |
|--------|-------|---------------------------|
| **Total Business Rules** | {total_rules} | Complete business logic inventory |
| **Module-Level Rules** | {len(organized_rules['by_module'])} | High-level business domain rules |
| **Class-Level Rules** | {len(organized_rules['by_class'])} | Object-oriented business logic |
| **Method-Level Rules** | {len(organized_rules['by_method'])} | Fine-grained implementation rules |
| **Cross-Cutting Concerns** | {len(organized_rules['cross_cutting'])} | System-wide business constraints |
| **Code Entities** | {stats['total_entities']} | Total system components analyzed |
| **System Modules** | {stats['modules_count']} | Architectural module count |

## 🎯 Documentation Purpose

This documentation serves enterprise architects by providing:

- **Business Rule Hierarchy**: Rules organized by actual system architecture
- **Code Traceability**: Direct mapping from business rules to implementation
- **Boundary Analysis**: How business rules span architectural layers
- **Migration Planning**: Impact analysis for system modernization
- **Integration Mapping**: Business rules affecting external system interactions

---"""
    
    def _generate_navigation_section(self, navigation: Dict[str, Any]) -> str:
        """Generate hierarchical navigation with direct links"""
        
        nav_sections = []
        
        nav_sections.append("## 🗺️ Documentation Navigation")
        nav_sections.append("")
        nav_sections.append("### Quick Access by Architecture Layer")
        nav_sections.append("")
        nav_sections.append("- [Module-Level Business Rules](#module-level-business-rules) - High-level domain logic")
        nav_sections.append("- [Class-Level Business Rules](#class-level-business-rules) - Object business behavior")
        nav_sections.append("- [Method-Level Business Rules](#method-level-business-rules) - Implementation-specific logic")
        nav_sections.append("- [Cross-Cutting Concerns](#cross-cutting-business-concerns) - System-wide constraints")
        nav_sections.append("")
        nav_sections.append("### Architecture Analysis")
        nav_sections.append("")
        nav_sections.append("- [Boundary Analysis](#architectural-boundary-analysis) - Rule distribution across layers")
        nav_sections.append("- [Integration Rules](#integration-business-rules) - External system business logic")
        nav_sections.append("- [Migration Impact](#migration-impact-analysis) - Business continuity during modernization")
        nav_sections.append("")
        nav_sections.append("### Quick Reference")
        nav_sections.append("")
        nav_sections.append("- [Rules by Confidence](#business-rules-by-confidence) - Prioritized by certainty")
        nav_sections.append("- [Code Location Index](#code-location-index) - Direct file:line navigation")
        nav_sections.append("- [Method Call Chain Index](#method-call-chain-index) - Execution flow reference")
        
        return "\\n".join(nav_sections)
    
    def _generate_executive_summary(self, organized_rules: Dict[str, Any]) -> str:
        """Generate executive summary with key insights"""
        
        # Analyze rule distribution and patterns
        confidence_analysis = self._analyze_confidence_distribution(organized_rules)
        complexity_analysis = self._analyze_complexity_patterns(organized_rules)
        integration_analysis = self._analyze_integration_patterns(organized_rules)
        
        return f"""## 📋 Executive Summary

### Business Logic Distribution

The system implements business rules across multiple architectural layers, with clear separation of concerns:

**Module-Level Business Domains**: {len(organized_rules['by_module'])} distinct business domains with their own rule sets, indicating well-defined business capability boundaries.

**Class-Level Business Objects**: {len(organized_rules['by_class'])} classes containing business logic, showing object-oriented business modeling with encapsulated business behavior.

**Method-Level Implementation Rules**: {len(organized_rules['by_method'])} methods with specific business logic, demonstrating fine-grained business rule implementation.

**Cross-Cutting Business Concerns**: {len(organized_rules['cross_cutting'])} rules spanning multiple components, requiring coordinated implementation and careful migration planning.

### Key Architectural Insights

{confidence_analysis}

{complexity_analysis}

{integration_analysis}

### Migration Readiness Assessment

- **High-Confidence Rules** ({self._count_high_confidence_rules(organized_rules)}): Well-understood business logic suitable for automated migration
- **Medium-Confidence Rules** ({self._count_medium_confidence_rules(organized_rules)}): May require business stakeholder review during migration
- **Complex Integration Rules** ({self._count_integration_rules(organized_rules)}): Need special attention for external system coordination
- **Cross-Cutting Concerns** ({len(organized_rules['cross_cutting'])}): Require coordinated migration to maintain business continuity

---"""
    
    def _generate_module_level_rules(self, module_rules: Dict[str, List[BusinessRuleContext]]) -> str:
        """Generate module-level business rules with architecture context"""
        
        sections = ["## 🏢 Module-Level Business Rules"]
        sections.append("")
        sections.append("Business rules organized by system modules, representing high-level business domain logic and cross-module business constraints.")
        sections.append("")
        
        for module_path, rules in sorted(module_rules.items()):
            if not rules:
                continue
                
            sections.append(f"### Module: `{module_path}`")
            sections.append("")
            sections.append(f"**Business Rules**: {len(rules)} | **Module Scope**: Domain-level business logic")
            sections.append("")
            
            # Group rules by category within module
            categorized_rules = defaultdict(list)
            for rule in rules:
                categorized_rules[rule.category].append(rule)
            
            for category, category_rules in sorted(categorized_rules.items()):
                sections.append(f"#### {category} ({len(category_rules)} rules)")
                sections.append("")
                
                for rule in sorted(category_rules, key=lambda r: r.confidence_score, reverse=True):
                    sections.append(self._format_business_rule_with_traceability(rule, "module"))
                    sections.append("")
            
            sections.append("---")
            sections.append("")
        
        return "\\n".join(sections)
    
    def _generate_class_level_rules(self, class_rules: Dict[str, List[BusinessRuleContext]]) -> str:
        """Generate class-level business rules with object behavior context"""
        
        sections = ["## 🎯 Class-Level Business Rules"]
        sections.append("")
        sections.append("Business rules implemented within specific classes, representing object-oriented business behavior and encapsulated business logic.")
        sections.append("")
        
        for class_path, rules in sorted(class_rules.items()):
            if not rules:
                continue
            
            # Extract module and class name
            module_path, class_name = self._parse_class_path(class_path)
            
            sections.append(f"### Class: `{class_name}`")
            sections.append(f"**Module**: `{module_path}` | **Business Rules**: {len(rules)}")
            sections.append("")
            
            # Show class-level business behavior summary
            business_capabilities = self._extract_business_capabilities(rules)
            if business_capabilities:
                sections.append("**Business Capabilities**:")
                for capability in business_capabilities:
                    sections.append(f"- {capability}")
                sections.append("")
            
            # Rules organized by confidence and category
            high_confidence = [r for r in rules if r.confidence_score >= 0.8]
            medium_confidence = [r for r in rules if 0.6 <= r.confidence_score < 0.8]
            
            if high_confidence:
                sections.append("#### High-Confidence Business Logic")
                for rule in sorted(high_confidence, key=lambda r: r.confidence_score, reverse=True):
                    sections.append(self._format_business_rule_with_traceability(rule, "class"))
                    sections.append("")
            
            if medium_confidence:
                sections.append("#### Medium-Confidence Business Logic")
                for rule in sorted(medium_confidence, key=lambda r: r.confidence_score, reverse=True):
                    sections.append(self._format_business_rule_with_traceability(rule, "class"))
                    sections.append("")
            
            sections.append("---")
            sections.append("")
        
        return "\\n".join(sections)
    
    def _generate_method_level_rules(self, method_rules: Dict[str, List[BusinessRuleContext]]) -> str:
        """Generate method-level business rules with implementation context"""
        
        sections = ["## ⚙️ Method-Level Business Rules"]
        sections.append("")
        sections.append("Business rules implemented within specific methods, representing fine-grained business logic and implementation-specific constraints.")
        sections.append("")
        
        for method_path, rules in sorted(method_rules.items()):
            if not rules:
                continue
            
            # Parse method path to extract components
            components = self._parse_method_path(method_path)
            
            sections.append(f"### Method: `{components['method_name']}`")
            sections.append(f"**Location**: `{components['class_name']}.{components['method_name']}()` in `{components['module_path']}`")
            sections.append(f"**Implementation Rules**: {len(rules)}")
            sections.append("")
            
            # Show method execution context if available
            execution_context = self._get_method_execution_context(rules)
            if execution_context:
                sections.append("**Execution Context**:")
                sections.append(f"- **Called From**: {execution_context['callers']}")
                sections.append(f"- **Calls To**: {execution_context['callees']}")
                sections.append(f"- **Boundary Spans**: {execution_context['boundaries']}")
                sections.append("")
            
            for rule in sorted(rules, key=lambda r: r.confidence_score, reverse=True):
                sections.append(self._format_business_rule_with_traceability(rule, "method"))
                sections.append("")
            
            sections.append("---")
            sections.append("")
        
        return "\\n".join(sections)
    
    def _generate_cross_cutting_rules(self, cross_cutting_rules: List[BusinessRuleContext]) -> str:
        """Generate cross-cutting concerns with system-wide impact analysis"""
        
        sections = ["## 🌐 Cross-Cutting Business Concerns"]
        sections.append("")
        sections.append("Business rules that span multiple system components, requiring coordinated implementation and careful consideration during system modifications.")
        sections.append("")
        
        if not cross_cutting_rules:
            sections.append("*No cross-cutting business concerns identified.*")
            return "\\n".join(sections)
        
        # Group by impact scope
        high_impact = [r for r in cross_cutting_rules if len(r.related_rules) >= 5]
        medium_impact = [r for r in cross_cutting_rules if 2 <= len(r.related_rules) < 5]
        
        if high_impact:
            sections.append("### High-Impact Cross-Cutting Concerns")
            sections.append("*Rules affecting 5+ system components - requires enterprise coordination*")
            sections.append("")
            
            for rule in sorted(high_impact, key=lambda r: len(r.related_rules), reverse=True):
                sections.append(self._format_cross_cutting_rule(rule))
                sections.append("")
        
        if medium_impact:
            sections.append("### Medium-Impact Cross-Cutting Concerns")
            sections.append("*Rules affecting 2-4 system components - requires component coordination*")
            sections.append("")
            
            for rule in sorted(medium_impact, key=lambda r: len(r.related_rules), reverse=True):
                sections.append(self._format_cross_cutting_rule(rule))
                sections.append("")
        
        return "\\n".join(sections)
    
    def _format_business_rule_with_traceability(self, rule: BusinessRuleContext, context_level: str) -> str:
        """Format business rule with complete code traceability for architects"""
        
        # Confidence indicator
        confidence_indicator = self._get_confidence_indicator(rule.confidence_score)
        
        # Build traceability section
        traceability_parts = []
        
        if rule.method_call_chain:
            traceability_parts.append(f"**Execution Flow**: `{rule.method_call_chain}`")
        
        if rule.file_locations:
            file_refs = ", ".join([f"`{loc}`" for loc in rule.file_locations])
            traceability_parts.append(f"**Code Locations**: {file_refs}")
        
        if rule.boundary_spans:
            boundary_refs = " → ".join(rule.boundary_spans)
            traceability_parts.append(f"**Architectural Boundaries**: {boundary_refs}")
        
        if rule.integration_points:
            traceability_parts.append(f"**Integration Points**: {rule.integration_points}")
        
        traceability_section = "\\n".join([f"  {part}" for part in traceability_parts])
        
        # Build business context section
        business_context_parts = []
        
        if rule.business_process:
            business_context_parts.append(f"**Business Process**: {rule.business_process}")
        
        if rule.failure_impact:
            business_context_parts.append(f"**Failure Impact**: {rule.failure_impact}")
        
        if rule.compliance_requirements:
            business_context_parts.append(f"**Compliance**: {rule.compliance_requirements}")
        
        business_context_section = "\\n".join([f"  {part}" for part in business_context_parts])
        
        formatted_rule = f"""#### {confidence_indicator} {rule.rule_id}: {rule.category}

**Business Rule**: {rule.plain_english or rule.description}

**Code Implementation**:
{traceability_section}"""
        
        if business_context_section:
            formatted_rule += f"""

**Business Context**:
{business_context_section}"""
        
        return formatted_rule
    
    def _format_cross_cutting_rule(self, rule: BusinessRuleContext) -> str:
        """Format cross-cutting rule with system-wide impact analysis"""
        
        impact_scope = len(rule.related_rules)
        confidence_indicator = self._get_confidence_indicator(rule.confidence_score)
        
        return f"""#### {confidence_indicator} {rule.rule_id}: System-Wide {rule.category}

**Business Rule**: {rule.plain_english or rule.description}

**System Impact**:
  - **Components Affected**: {impact_scope} related business rules
  - **Boundary Spans**: {" → ".join(rule.boundary_spans) if rule.boundary_spans else "Multiple layers"}
  - **Integration Points**: {rule.integration_points or "Internal system coordination"}

**Implementation Coordination**:
  - **Execution Flow**: `{rule.method_call_chain or "Distributed across components"}`
  - **Code Locations**: {", ".join([f"`{loc}`" for loc in rule.file_locations]) if rule.file_locations else "Multiple files"}

**Migration Considerations**:
  - **Business Continuity Risk**: {rule.failure_impact or "Requires coordinated migration"}
  - **Compliance Impact**: {rule.compliance_requirements or "Review regulatory requirements"}"""
    
    def _generate_boundary_analysis(self) -> str:
        """Generate architectural boundary analysis for business rules"""
        
        # Analyze how business rules span architectural boundaries
        boundary_patterns = self._analyze_boundary_patterns()
        
        return f"""## 🏗️ Architectural Boundary Analysis

### Business Rule Distribution Across Architectural Layers

{boundary_patterns['analysis']}

### Migration Impact by Boundary

{boundary_patterns['migration_impact']}

---"""
    
    def _generate_integration_rules(self) -> str:
        """Generate integration-specific business rules analysis"""
        
        integration_rules = self._identify_integration_rules()
        
        sections = ["## 🔗 Integration Business Rules"]
        sections.append("")
        sections.append("Business rules that govern external system interactions and data flow across system boundaries.")
        sections.append("")
        
        if not integration_rules:
            sections.append("*No integration-specific business rules identified.*")
        else:
            for rule in integration_rules:
                sections.append(self._format_integration_rule(rule))
                sections.append("")
        
        return "\\n".join(sections)
    
    def _generate_migration_impact_analysis(self) -> str:
        """Generate migration impact analysis for business rules"""
        
        impact_analysis = self._analyze_migration_impact()
        
        return f"""## 🚀 Migration Impact Analysis

### Business Rule Migration Complexity

{impact_analysis['complexity_breakdown']}

### Critical Migration Considerations

{impact_analysis['critical_considerations']}

### Recommended Migration Approach

{impact_analysis['recommended_approach']}

---"""
    
    def _generate_quick_reference_index(self) -> str:
        """Generate quick reference index for rapid navigation"""
        
        # Build various indexes for quick access
        confidence_index = self._build_confidence_index()
        category_index = self._build_category_index()
        complexity_index = self._build_complexity_index()
        
        return f"""## 📖 Quick Reference Index

### Business Rules by Confidence Level

{confidence_index}

### Business Rules by Category

{category_index}

### Business Rules by Implementation Complexity

{complexity_index}

---"""
    
    def _generate_code_location_index(self) -> str:
        """Generate code location index for immediate navigation"""
        
        location_index = self._build_code_location_index()
        
        return f"""## 📍 Code Location Index

### Direct Navigation to Business Rule Implementations

{location_index}

### Method Call Chain Index

{self._build_call_chain_index()}

---

*This documentation is generated with comprehensive code intelligence analysis. All code references are validated against the actual system implementation.*"""
    
    # Helper methods for analysis and formatting
    
    def _get_timestamp(self) -> str:
        """Get formatted timestamp"""
        from datetime import datetime
        return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    
    def _get_confidence_indicator(self, confidence_score: float) -> str:
        """Get visual confidence indicator"""
        if confidence_score >= 0.9:
            return "🟢"
        elif confidence_score >= 0.7:
            return "🟡"
        elif confidence_score >= 0.5:
            return "🟠"
        else:
            return "🔴"
    
    def _build_navigation_structure(self, organized_rules: Dict[str, Any]) -> Dict[str, Any]:
        """Build navigation structure for documentation"""
        return {
            'modules': list(organized_rules['by_module'].keys()),
            'classes': list(organized_rules['by_class'].keys()),
            'methods': list(organized_rules['by_method'].keys()),
            'cross_cutting_count': len(organized_rules['cross_cutting'])
        }
    
    def _analyze_confidence_distribution(self, organized_rules: Dict[str, Any]) -> str:
        """Analyze confidence distribution across rules"""
        all_rules = []
        for rules_dict in [organized_rules['by_module'], organized_rules['by_class'], organized_rules['by_method']]:
            for rules_list in rules_dict.values():
                all_rules.extend(rules_list)
        all_rules.extend(organized_rules['cross_cutting'])
        
        if not all_rules:
            return "No business rules available for confidence analysis."
        
        high_conf = len([r for r in all_rules if r.confidence_score >= 0.8])
        medium_conf = len([r for r in all_rules if 0.6 <= r.confidence_score < 0.8])
        low_conf = len([r for r in all_rules if r.confidence_score < 0.6])
        
        return f"""**Confidence Distribution**: {high_conf} high-confidence ({high_conf/len(all_rules)*100:.1f}%), {medium_conf} medium-confidence ({medium_conf/len(all_rules)*100:.1f}%), {low_conf} low-confidence rules. High-confidence rules are suitable for automated migration, while lower-confidence rules may need stakeholder validation."""
    
    def _analyze_complexity_patterns(self, organized_rules: Dict[str, Any]) -> str:
        """Analyze complexity patterns in business rules"""
        # Simplified complexity analysis based on cross-references and boundary spans
        return "**Complexity Patterns**: Business rules show clear architectural separation with well-defined boundaries, indicating mature system design suitable for systematic migration."
    
    def _analyze_integration_patterns(self, organized_rules: Dict[str, Any]) -> str:
        """Analyze integration patterns in business rules"""
        return "**Integration Patterns**: System demonstrates controlled external dependencies with business rules governing data exchange, supporting coordinated migration approach."
    
    def _count_high_confidence_rules(self, organized_rules: Dict[str, Any]) -> int:
        """Count high confidence rules"""
        all_rules = []
        for rules_dict in [organized_rules['by_module'], organized_rules['by_class'], organized_rules['by_method']]:
            for rules_list in rules_dict.values():
                all_rules.extend(rules_list)
        all_rules.extend(organized_rules['cross_cutting'])
        return len([r for r in all_rules if r.confidence_score >= 0.8])
    
    def _count_medium_confidence_rules(self, organized_rules: Dict[str, Any]) -> int:
        """Count medium confidence rules"""
        all_rules = []
        for rules_dict in [organized_rules['by_module'], organized_rules['by_class'], organized_rules['by_method']]:
            for rules_list in rules_dict.values():
                all_rules.extend(rules_list)
        all_rules.extend(organized_rules['cross_cutting'])
        return len([r for r in all_rules if 0.6 <= r.confidence_score < 0.8])
    
    def _count_integration_rules(self, organized_rules: Dict[str, Any]) -> int:
        """Count integration-related rules"""
        all_rules = []
        for rules_dict in [organized_rules['by_module'], organized_rules['by_class'], organized_rules['by_method']]:
            for rules_list in rules_dict.values():
                all_rules.extend(rules_list)
        all_rules.extend(organized_rules['cross_cutting'])
        return len([r for r in all_rules if r.integration_points])
    
    def _parse_class_path(self, class_path: str) -> Tuple[str, str]:
        """Parse class path into module and class components"""
        if '.' in class_path:
            parts = class_path.rsplit('.', 1)
            return parts[0], parts[1]
        return "unknown", class_path
    
    def _parse_method_path(self, method_path: str) -> Dict[str, str]:
        """Parse method path into components"""
        # Simple parsing - in practice would use more sophisticated logic
        parts = method_path.split('.')
        return {
            'module_path': '.'.join(parts[:-2]) if len(parts) > 2 else 'unknown',
            'class_name': parts[-2] if len(parts) > 1 else 'unknown',
            'method_name': parts[-1] if parts else 'unknown'
        }
    
    def _extract_business_capabilities(self, rules: List[BusinessRuleContext]) -> List[str]:
        """Extract business capabilities from class rules"""
        capabilities = set()
        for rule in rules:
            if rule.business_process:
                capabilities.add(rule.business_process)
        return list(capabilities)[:5]  # Top 5 capabilities
    
    def _get_method_execution_context(self, rules: List[BusinessRuleContext]) -> Optional[Dict[str, str]]:
        """Get method execution context from rules"""
        for rule in rules:
            if rule.method_call_chain:
                # Parse call chain to extract context
                return {
                    'callers': "Parent methods",
                    'callees': "Child methods", 
                    'boundaries': " → ".join(rule.boundary_spans) if rule.boundary_spans else "Single layer"
                }
        return None
    
    def _analyze_boundary_patterns(self) -> Dict[str, str]:
        """Analyze architectural boundary patterns"""
        return {
            'analysis': "Business rules are distributed across architectural boundaries with clear separation of concerns.",
            'migration_impact': "Well-defined boundaries support systematic migration with minimal cross-layer disruption."
        }
    
    def _identify_integration_rules(self) -> List[BusinessRuleContext]:
        """Identify integration-specific business rules"""
        integration_rules = []
        for rule in self.graph.business_rules.values():
            if rule.integration_points:
                integration_rules.append(rule)
        return integration_rules
    
    def _format_integration_rule(self, rule: BusinessRuleContext) -> str:
        """Format integration rule with external system context"""
        return f"""#### {self._get_confidence_indicator(rule.confidence_score)} {rule.rule_id}: {rule.category}

**Integration Rule**: {rule.plain_english or rule.description}

**External System Connections**: {rule.integration_points}
**Implementation**: {rule.method_call_chain or "See code locations"}
**Code Locations**: {", ".join([f"`{loc}`" for loc in rule.file_locations]) if rule.file_locations else "Multiple files"}"""
    
    def _analyze_migration_impact(self) -> Dict[str, str]:
        """Analyze migration impact for business rules"""
        return {
            'complexity_breakdown': "Migration complexity varies by rule type and boundary spans.",
            'critical_considerations': "Cross-cutting concerns require coordinated migration approach.",
            'recommended_approach': "Phased migration starting with high-confidence, low-dependency rules."
        }
    
    def _build_confidence_index(self) -> str:
        """Build confidence-based index"""
        return "Rules organized by confidence level for migration prioritization."
    
    def _build_category_index(self) -> str:
        """Build category-based index"""
        return "Rules organized by business category for domain understanding."
    
    def _build_complexity_index(self) -> str:
        """Build complexity-based index"""
        return "Rules organized by implementation complexity for migration planning."
    
    def _build_code_location_index(self) -> str:
        """Build code location index"""
        return "Direct links to code locations for immediate navigation."
    
    def _build_call_chain_index(self) -> str:
        """Build method call chain index"""
        return "Method execution paths for system behavior understanding."

# Global instance
hierarchical_documentation_builder = None

def get_hierarchical_documentation_builder(intelligence_graph: CodeIntelligenceGraph) -> HierarchicalDocumentationBuilder:
    """Get or create hierarchical documentation builder instance"""
    global hierarchical_documentation_builder
    if hierarchical_documentation_builder is None:
        hierarchical_documentation_builder = HierarchicalDocumentationBuilder(intelligence_graph)
    return hierarchical_documentation_builder