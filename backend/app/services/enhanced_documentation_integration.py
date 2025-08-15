"""
Enhanced Documentation Integration Service
Orchestrates all enhanced services to produce comprehensive, architect-focused documentation
"""

import logging
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
import asyncio
from datetime import datetime

from app.services.code_intelligence import CodeIntelligenceGraph, code_intelligence
from app.services.code_intelligence_builder import CodeIntelligenceBuilder, code_intelligence_builder
from app.services.enhanced_ai_service import EnhancedAIService, get_enhanced_ai_service
from app.services.enhanced_diagram_service import EnhancedDiagramService, get_enhanced_diagram_service
from app.services.hierarchical_documentation_builder import HierarchicalDocumentationBuilder, get_hierarchical_documentation_builder
from app.services.enhanced_migration_dashboard import EnhancedMigrationDashboard, get_enhanced_migration_dashboard
from app.services.ai_service import ai_service_instance
from app.models.schemas import DocumentationRequest, BusinessRule
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class EnhancedDocumentationIntegration:
    """
    Master service that orchestrates all enhanced documentation services
    to produce comprehensive, enterprise-grade documentation with code traceability
    """
    
    def __init__(self):
        self.intelligence_graph = code_intelligence
        self.intelligence_builder = code_intelligence_builder
        self.enhanced_ai_service = get_enhanced_ai_service(ai_service_instance, self.intelligence_graph)
        self.enhanced_diagram_service = get_enhanced_diagram_service(ai_service_instance, self.intelligence_graph)
        self.hierarchical_doc_builder = get_hierarchical_documentation_builder(self.intelligence_graph)
        self.enhanced_migration_dashboard = get_enhanced_migration_dashboard(ai_service_instance, self.intelligence_graph)
    
    async def generate_enhanced_documentation(
        self,
        job_id: str,
        entities: List[Dict[str, Any]],
        request: DocumentationRequest,
        update_progress: Optional[Callable] = None
    ) -> Dict[str, str]:
        """
        Generate comprehensive enhanced documentation with full intelligence analysis
        """
        logger.info(f"Starting enhanced documentation generation for job {job_id}")
        
        documentation = {}
        
        try:
            # Step 1: Build Code Intelligence Graph
            if update_progress:
                await update_progress(10, status="Building code intelligence graph", 
                                    current_task="Analyzing code structure and relationships")
            
            await self._build_intelligence_graph(entities)
            
            # Step 2: Enhanced Business Rule Extraction with Full Context
            if update_progress:
                await update_progress(25, status="Extracting enhanced business rules", 
                                    current_task="Analyzing business logic with full code context")
            
            enhanced_business_rules = await self._extract_enhanced_business_rules(entities)
            
            # Step 3: Generate Hierarchical Business Rules Documentation
            if update_progress:
                await update_progress(40, status="Generating hierarchical business rules", 
                                    current_task="Organizing rules by system architecture")
            
            documentation['BUSINESS_RULES_ENHANCED.md'] = await self._generate_hierarchical_business_rules()
            
            # Step 4: Generate Enhanced System Overview
            if update_progress:
                await update_progress(55, status="Generating enhanced overview", 
                                    current_task="Creating comprehensive system analysis")
            
            documentation['SYSTEM_OVERVIEW_ENHANCED.md'] = await self._generate_enhanced_overview(
                entities, enhanced_business_rules, request
            )
            
            # Step 5: Generate Comprehensive Diagram Suite
            if update_progress:
                await update_progress(70, status="Generating comprehensive diagrams", 
                                    current_task="Creating enterprise-grade visual documentation")
            
            diagrams = await self._generate_comprehensive_diagrams(entities, enhanced_business_rules)
            documentation.update(diagrams)
            
            # Step 6: Generate Actionable Migration Dashboard
            if update_progress:
                await update_progress(85, status="Generating migration dashboard", 
                                    current_task="Creating actionable migration strategy")
            
            documentation['MIGRATION_STRATEGY.md'] = await self._generate_migration_dashboard(
                entities, enhanced_business_rules
            )
            
            # Step 7: Generate Cross-Reference Navigation
            if update_progress:
                await update_progress(95, status="Building navigation system", 
                                    current_task="Creating bidirectional documentation links")
            
            documentation['NAVIGATION_INDEX.md'] = await self._generate_navigation_index(documentation)
            
            if update_progress:
                await update_progress(100, status="Enhanced documentation complete", 
                                    current_task="All enhanced documentation generated successfully")
            
            logger.info(f"Enhanced documentation generation complete for job {job_id}: "
                       f"{len(documentation)} documents generated")
            
            return documentation
            
        except Exception as e:
            logger.error(f"Error in enhanced documentation generation for job {job_id}: {e}")
            if update_progress:
                await update_progress(100, status="Error in enhanced documentation", 
                                    current_task=f"Error: {str(e)}")
            raise
    
    async def _build_intelligence_graph(self, entities: List[Dict[str, Any]]) -> None:
        """Build the code intelligence graph from parsed entities"""
        logger.info("Building code intelligence graph")
        
        # Build graph from entities
        self.intelligence_graph = self.intelligence_builder.build_from_entities(entities)
        
        # Update all service instances to use the new graph
        self.enhanced_ai_service.graph = self.intelligence_graph
        self.enhanced_diagram_service.graph = self.intelligence_graph
        self.hierarchical_doc_builder.graph = self.intelligence_graph
        self.enhanced_migration_dashboard.graph = self.intelligence_graph
        
        stats = self.intelligence_graph.get_statistics()
        logger.info(f"Code intelligence graph built: {stats}")
    
    async def _extract_enhanced_business_rules(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract business rules using enhanced AI service with full context"""
        logger.info("Extracting enhanced business rules with full code context")
        
        enhanced_rules = []
        
        # Process entities in batches to manage memory and API calls
        batch_size = 10
        for i in range(0, len(entities), batch_size):
            batch = entities[i:i + batch_size]
            
            for entity in batch:
                try:
                    # Get entity from intelligence graph
                    entity_key = f"{entity.get('file_path', '')}:{entity.get('type', '')}:{entity.get('name', '')}"
                    entity_id = self.intelligence_builder.entity_id_map.get(entity_key)
                    
                    if not entity_id:
                        continue
                    
                    # Get full code content (no 4KB limit)
                    full_code = await self._get_full_code_content(entity.get('file_path', ''))
                    
                    # Get related entities for cross-file context
                    related_entities = self.intelligence_graph.find_related_entities(entity_id, max_depth=2)
                    
                    # Extract rules with enhanced context
                    entity_rules = await self.enhanced_ai_service.extract_business_rules_with_context(
                        entity_id=entity_id,
                        full_code=full_code,
                        related_entities=related_entities,
                        keywords=None  # Could be extracted from request
                    )
                    
                    # Add rules to intelligence graph
                    for rule in entity_rules:
                        self.intelligence_graph.add_business_rule(rule)
                        enhanced_rules.append({
                            'rule_context': rule,
                            'entity': entity
                        })
                    
                except Exception as e:
                    logger.warning(f"Error extracting enhanced rules for entity {entity.get('name', 'unknown')}: {e}")
                    continue
        
        logger.info(f"Extracted {len(enhanced_rules)} enhanced business rules")
        return enhanced_rules
    
    async def _generate_hierarchical_business_rules(self) -> str:
        """Generate hierarchical business rules documentation"""
        logger.info("Generating hierarchical business rules documentation")
        
        return self.hierarchical_doc_builder.build_hierarchical_business_rules_documentation()
    
    async def _generate_enhanced_overview(
        self,
        entities: List[Dict[str, Any]],
        enhanced_business_rules: List[Dict[str, Any]],
        request: DocumentationRequest
    ) -> str:
        """Generate enhanced system overview with comprehensive analysis"""
        logger.info("Generating enhanced system overview")
        
        # Get module structures from intelligence graph
        module_structures = {}
        for module_path in self.intelligence_graph.module_index.keys():
            module_structures[module_path] = self.intelligence_graph.get_module_structure(module_path)
        
        # Get organized business rules
        business_rules_by_hierarchy = self.intelligence_graph.get_business_rules_by_hierarchy()
        
        # Get call graphs
        call_graphs = {}
        for entity_id, entity in self.intelligence_graph.entities.items():
            if entity.type in ['method', 'function']:
                call_chains = self.intelligence_graph.get_call_chain(entity_id, max_depth=5)
                if call_chains:
                    call_graphs[entity_id] = call_chains
        
        # Generate migration insights
        migration_insights = await self._generate_migration_insights(entities, business_rules_by_hierarchy)
        
        # Generate comprehensive overview
        return await self.enhanced_ai_service.generate_comprehensive_overview(
            depth=request.documentation_depth,
            module_structures=module_structures,
            business_rules_by_hierarchy=business_rules_by_hierarchy,
            call_graphs=call_graphs,
            migration_insights=migration_insights
        )
    
    async def _generate_comprehensive_diagrams(
        self,
        entities: List[Dict[str, Any]],
        enhanced_business_rules: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """Generate comprehensive diagram suite"""
        logger.info("Generating comprehensive diagram suite")
        
        # Prepare data for diagram generation
        business_rules_by_hierarchy = self.intelligence_graph.get_business_rules_by_hierarchy()
        
        # Get call graphs
        call_graphs = {}
        for entity_id, entity in self.intelligence_graph.entities.items():
            if entity.type in ['method', 'function']:
                call_chains = self.intelligence_graph.get_call_chain(entity_id, max_depth=3)
                if call_chains:
                    call_graphs[entity_id] = call_chains
        
        # Mock database and integration analysis (would be real in full implementation)
        database_analysis = {"analysis_mode": "code_analysis", "tables": [], "queries": []}
        integration_analysis = {"flows": [], "apis": [], "external_systems": []}
        migration_analysis = {"complexity": "medium", "risks": [], "opportunities": []}
        
        # Generate comprehensive diagrams
        return await self.enhanced_diagram_service.generate_comprehensive_diagram_suite(
            entities=entities,
            business_rules_by_hierarchy=business_rules_by_hierarchy,
            call_graphs=call_graphs,
            database_analysis=database_analysis,
            integration_analysis=integration_analysis,
            migration_analysis=migration_analysis
        )
    
    async def _generate_migration_dashboard(
        self,
        entities: List[Dict[str, Any]],
        enhanced_business_rules: List[Dict[str, Any]]
    ) -> str:
        """Generate actionable migration dashboard"""
        logger.info("Generating actionable migration dashboard")
        
        # Prepare data for migration analysis
        business_rules_by_hierarchy = self.intelligence_graph.get_business_rules_by_hierarchy()
        
        # Get call graphs
        call_graphs = {}
        for entity_id, entity in self.intelligence_graph.entities.items():
            if entity.type in ['method', 'function']:
                call_chains = self.intelligence_graph.get_call_chain(entity_id, max_depth=3)
                if call_chains:
                    call_graphs[entity_id] = call_chains
        
        # Mock additional analysis data (would be real in full implementation)
        database_analysis = {"complexity": "medium", "tables": [], "migration_effort": "moderate"}
        integration_analysis = {"external_systems": [], "api_complexity": "medium"}
        
        # Generate migration dashboard
        return await self.enhanced_migration_dashboard.generate_actionable_migration_dashboard(
            entities=entities,
            business_rules_by_hierarchy=business_rules_by_hierarchy,
            database_analysis=database_analysis,
            integration_analysis=integration_analysis,
            call_graphs=call_graphs
        )
    
    async def _generate_navigation_index(self, documentation: Dict[str, str]) -> str:
        """Generate bidirectional navigation index"""
        logger.info("Generating navigation index")
        
        sections = []
        
        # Header
        sections.append("# 🗺️ Documentation Navigation Index")
        sections.append("")
        sections.append(f"**Generated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        sections.append("**Purpose**: Bidirectional navigation between documentation, code, and business rules")
        sections.append("")
        
        # Main documentation sections
        sections.append("## 📚 Main Documentation")
        sections.append("")
        for doc_name, content in documentation.items():
            if doc_name.endswith('.md'):
                # Extract first heading as description
                first_line = content.split('\\n')[0] if content else "Documentation"
                sections.append(f"- **[{doc_name}]({doc_name})**: {first_line.replace('#', '').strip()}")
        sections.append("")
        
        # Diagram navigation
        diagram_files = [name for name in documentation.keys() if name.endswith('.mmd')]
        if diagram_files:
            sections.append("## 📊 Diagrams & Visualizations")
            sections.append("")
            for diagram_name in sorted(diagram_files):
                diagram_type = diagram_name.replace('.mmd', '').replace('_', ' ').title()
                sections.append(f"- **[{diagram_type}]({diagram_name})**: Visual representation")
            sections.append("")
        
        # Business rules navigation
        sections.append("## 🎯 Business Rules Quick Access")
        sections.append("")
        
        # Get rule statistics from intelligence graph
        organized_rules = self.intelligence_graph.get_business_rules_by_hierarchy()
        sections.append(f"- **Module-Level Rules**: {len(organized_rules.get('by_module', {}))} modules with business logic")
        sections.append(f"- **Class-Level Rules**: {len(organized_rules.get('by_class', {}))} classes with business behavior")
        sections.append(f"- **Method-Level Rules**: {len(organized_rules.get('by_method', {}))} methods with specific logic")
        sections.append(f"- **Cross-Cutting Concerns**: {len(organized_rules.get('cross_cutting', []))} system-wide rules")
        sections.append("")
        
        # Code location index
        sections.append("## 📍 Code Location Quick Reference")
        sections.append("")
        sections.append("### High-Impact Business Logic Locations")
        
        # Show top modules by business rule count
        module_rule_counts = {}
        for module_path, rules in organized_rules.get('by_module', {}).items():
            module_rule_counts[module_path] = len(rules)
        
        top_modules = sorted(module_rule_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        for module_path, rule_count in top_modules:
            sections.append(f"- **{module_path}**: {rule_count} business rules")
        sections.append("")
        
        # Migration navigation
        sections.append("## 🚀 Migration Planning Navigation")
        sections.append("")
        sections.append("- **[Migration Strategy](MIGRATION_STRATEGY.md)**: Complete migration roadmap and implementation guide")
        sections.append("- **[Business Rules Impact](BUSINESS_RULES_ENHANCED.md)**: How business rules affect migration planning")
        sections.append("- **[System Architecture](SYSTEM_OVERVIEW_ENHANCED.md)**: Current state analysis for migration planning")
        sections.append("")
        
        # Usage instructions
        sections.append("## 📖 How to Use This Documentation")
        sections.append("")
        sections.append("### For Business Stakeholders")
        sections.append("1. Start with **SYSTEM_OVERVIEW_ENHANCED.md** for business context")
        sections.append("2. Review **BUSINESS_RULES_ENHANCED.md** for business logic understanding")
        sections.append("3. Check **MIGRATION_STRATEGY.md** for business impact planning")
        sections.append("")
        sections.append("### For Architects & Developers")
        sections.append("1. Review **SYSTEM_OVERVIEW_ENHANCED.md** for technical architecture")
        sections.append("2. Use **BUSINESS_RULES_ENHANCED.md** for code-to-business mapping")
        sections.append("3. Reference diagrams for visual system understanding")
        sections.append("4. Follow **MIGRATION_STRATEGY.md** for implementation planning")
        sections.append("")
        sections.append("### For Migration Teams")
        sections.append("1. **MIGRATION_STRATEGY.md** provides complete implementation roadmap")
        sections.append("2. **BUSINESS_RULES_ENHANCED.md** shows business continuity requirements")
        sections.append("3. Diagrams provide visual migration planning support")
        sections.append("")
        
        # Footer
        sections.append("---")
        sections.append("")
        sections.append("*This navigation index provides bidirectional access to all documentation components with precise code traceability for enterprise migration planning.*")
        
        return "\\n".join(sections)
    
    async def _get_full_code_content(self, file_path: str) -> str:
        """Get full code content from file (removes 4KB limit)"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            logger.warning(f"Could not read file {file_path}: {e}")
            return ""
    
    async def _generate_migration_insights(
        self,
        entities: List[Dict[str, Any]],
        business_rules_by_hierarchy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate migration insights for overview generation"""
        
        # Count critical components
        critical_entities = [e for e in entities if 'critical' in str(e).lower()]
        
        # Count business rules
        total_rules = (
            len(business_rules_by_hierarchy.get('cross_cutting', [])) +
            sum(len(rules) for rules in business_rules_by_hierarchy.get('by_module', {}).values()) +
            sum(len(rules) for rules in business_rules_by_hierarchy.get('by_class', {}).values()) +
            sum(len(rules) for rules in business_rules_by_hierarchy.get('by_method', {}).values())
        )
        
        return {
            'modernization_opportunities': [
                "Legacy framework modernization",
                "API architecture improvement", 
                "Database optimization",
                "Integration pattern modernization"
            ],
            'critical_risks': [
                "Business continuity during migration",
                "Data integrity maintenance",
                "Integration stability"
            ],
            'integration_complexity': 'Medium',
            'total_components': len(entities),
            'critical_components': len(critical_entities),
            'total_business_rules': total_rules
        }

# Global integration service instance
enhanced_documentation_integration = EnhancedDocumentationIntegration()

def get_enhanced_documentation_integration() -> EnhancedDocumentationIntegration:
    """Get the enhanced documentation integration service"""
    return enhanced_documentation_integration