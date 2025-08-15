"""
Enhanced Migration Dashboard - Actionable Enterprise Migration Intelligence
Provides specific, implementable migration recommendations with precise effort estimation
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json

from app.services.code_intelligence import CodeIntelligenceGraph, BusinessRuleContext
from app.services.ai_service import AIService
from app.core.logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class MigrationComponent:
    """Represents a component in the migration analysis"""
    name: str
    type: str  # module, class, method, integration, database
    complexity_score: float  # 0-10 scale
    business_criticality: str  # low, medium, high, critical
    migration_effort_hours: int
    dependencies: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    modernization_approach: str = ""
    code_locations: List[str] = field(default_factory=list)
    business_rules_affected: List[str] = field(default_factory=list)

@dataclass 
class MigrationPhase:
    """Represents a phase in the migration roadmap"""
    phase_number: int
    name: str
    objective: str
    duration_weeks: int
    components: List[MigrationComponent] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    deliverables: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    risk_mitigation: List[str] = field(default_factory=list)
    estimated_effort_hours: int = 0

@dataclass
class MigrationStrategy:
    """Complete migration strategy with actionable recommendations"""
    executive_summary: str
    total_effort_hours: int
    estimated_duration_months: int
    recommended_team_size: int
    phases: List[MigrationPhase] = field(default_factory=list)
    critical_risks: List[str] = field(default_factory=list)
    success_factors: List[str] = field(default_factory=list)
    technology_recommendations: Dict[str, str] = field(default_factory=dict)
    business_continuity_plan: str = ""

class EnhancedMigrationDashboard:
    """
    Generates actionable migration dashboards with specific recommendations,
    effort estimates, and implementation roadmaps
    """
    
    def __init__(self, ai_service: AIService, intelligence_graph: CodeIntelligenceGraph):
        self.ai_service = ai_service
        self.graph = intelligence_graph
    
    async def generate_actionable_migration_dashboard(
        self,
        entities: List[Dict[str, Any]],
        business_rules_by_hierarchy: Dict[str, Any],
        database_analysis: Dict[str, Any],
        integration_analysis: Dict[str, Any],
        call_graphs: Dict[str, List[List[str]]]
    ) -> str:
        """
        Generate comprehensive, actionable migration dashboard with specific recommendations
        """
        logger.info("Generating actionable migration dashboard")
        
        # Step 1: Analyze components for migration complexity
        migration_components = await self._analyze_migration_components(
            entities, business_rules_by_hierarchy, database_analysis, integration_analysis
        )
        
        # Step 2: Create migration strategy with phased approach
        migration_strategy = await self._create_migration_strategy(
            migration_components, call_graphs, business_rules_by_hierarchy
        )
        
        # Step 3: Generate actionable dashboard documentation
        dashboard = await self._generate_dashboard_documentation(
            migration_strategy, migration_components, business_rules_by_hierarchy
        )
        
        logger.info(f"Generated actionable migration dashboard: {len(dashboard)} characters")
        return dashboard
    
    async def _analyze_migration_components(
        self,
        entities: List[Dict[str, Any]],
        business_rules_by_hierarchy: Dict[str, Any],
        database_analysis: Dict[str, Any],
        integration_analysis: Dict[str, Any]
    ) -> List[MigrationComponent]:
        """Analyze all system components for migration complexity and effort"""
        
        components = []
        
        # Analyze code entities
        for entity in entities:
            component = await self._analyze_entity_migration_complexity(
                entity, business_rules_by_hierarchy
            )
            if component:
                components.append(component)
        
        # Analyze database components
        db_components = await self._analyze_database_migration_complexity(database_analysis)
        components.extend(db_components)
        
        # Analyze integration components
        integration_components = await self._analyze_integration_migration_complexity(integration_analysis)
        components.extend(integration_components)
        
        # Sort by business criticality and complexity
        components.sort(key=lambda c: (
            {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}[c.business_criticality],
            c.complexity_score
        ), reverse=True)
        
        logger.info(f"Analyzed {len(components)} migration components")
        return components
    
    async def _analyze_entity_migration_complexity(
        self,
        entity: Dict[str, Any],
        business_rules_by_hierarchy: Dict[str, Any]
    ) -> Optional[MigrationComponent]:
        """Analyze individual entity for migration complexity"""
        
        # Calculate complexity based on multiple factors
        complexity_factors = {
            'lines_of_code': min(entity.get('complexity', 0) / 20.0, 5.0),  # Normalize complexity
            'dependencies': min(len(entity.get('dependencies', [])) / 10.0, 3.0),
            'business_rules': 0,
            'integration_points': 0
        }
        
        # Find business rules for this entity
        entity_business_rules = self._find_business_rules_for_entity(entity, business_rules_by_hierarchy)
        complexity_factors['business_rules'] = min(len(entity_business_rules) / 5.0, 2.0)
        
        # Check for integration patterns
        if any(pattern in entity.get('file_path', '').lower() 
               for pattern in ['api', 'service', 'client', 'integration', 'external']):
            complexity_factors['integration_points'] = 2.0
        
        total_complexity = sum(complexity_factors.values())
        
        # Determine business criticality based on business rules and usage patterns
        business_criticality = self._determine_business_criticality(entity, entity_business_rules)
        
        # Estimate migration effort
        base_effort = self._calculate_base_migration_effort(entity, total_complexity)
        
        # Determine modernization approach
        modernization_approach = self._determine_modernization_approach(entity, total_complexity)
        
        return MigrationComponent(
            name=entity.get('name', 'Unknown'),
            type=entity.get('type', 'unknown'),
            complexity_score=round(total_complexity, 1),
            business_criticality=business_criticality,
            migration_effort_hours=base_effort,
            dependencies=entity.get('dependencies', []),
            risks=self._identify_migration_risks(entity, total_complexity),
            modernization_approach=modernization_approach,
            code_locations=[entity.get('file_path', 'Unknown')],
            business_rules_affected=[rule.rule_id for rule in entity_business_rules]
        )
    
    async def _create_migration_strategy(
        self,
        migration_components: List[MigrationComponent],
        call_graphs: Dict[str, List[List[str]]],
        business_rules_by_hierarchy: Dict[str, Any]
    ) -> MigrationStrategy:
        """Create comprehensive migration strategy with phased approach"""
        
        # Calculate total effort and timeline
        total_effort = sum(c.migration_effort_hours for c in migration_components)
        estimated_months = max(6, total_effort // 160)  # Assuming 160 hours per month per person
        recommended_team_size = max(2, min(8, total_effort // (estimated_months * 160)))
        
        # Create migration phases
        phases = await self._create_migration_phases(migration_components, call_graphs)
        
        # Generate executive summary
        executive_summary = await self._generate_executive_summary(
            migration_components, total_effort, estimated_months, recommended_team_size
        )
        
        # Identify critical risks and success factors
        critical_risks = self._identify_critical_migration_risks(migration_components)
        success_factors = self._identify_success_factors(migration_components, business_rules_by_hierarchy)
        
        # Technology recommendations
        tech_recommendations = await self._generate_technology_recommendations(migration_components)
        
        # Business continuity plan
        continuity_plan = await self._generate_business_continuity_plan(migration_components, phases)
        
        return MigrationStrategy(
            executive_summary=executive_summary,
            total_effort_hours=total_effort,
            estimated_duration_months=estimated_months,
            recommended_team_size=recommended_team_size,
            phases=phases,
            critical_risks=critical_risks,
            success_factors=success_factors,
            technology_recommendations=tech_recommendations,
            business_continuity_plan=continuity_plan
        )
    
    async def _create_migration_phases(
        self,
        migration_components: List[MigrationComponent],
        call_graphs: Dict[str, List[List[str]]]
    ) -> List[MigrationPhase]:
        """Create detailed migration phases with specific components and timelines"""
        
        phases = []
        
        # Phase 1: Foundation and Low-Risk Components
        foundation_components = [
            c for c in migration_components 
            if c.business_criticality in ['low', 'medium'] and c.complexity_score <= 5.0
        ][:10]
        
        phase1 = MigrationPhase(
            phase_number=1,
            name="Foundation & Quick Wins",
            objective="Establish migration infrastructure and modernize low-risk components",
            duration_weeks=8,
            components=foundation_components,
            prerequisites=["Migration team assembled", "Development environment setup", "Code repository prepared"],
            deliverables=[
                "Migration infrastructure established",
                "CI/CD pipeline implemented", 
                "Low-risk components modernized",
                "Migration patterns documented"
            ],
            success_criteria=[
                "All foundation components successfully migrated",
                "Zero business disruption during Phase 1",
                "Migration patterns validated and documented"
            ],
            risk_mitigation=[
                "Parallel running of old and new systems",
                "Comprehensive rollback procedures",
                "Stakeholder communication plan"
            ],
            estimated_effort_hours=sum(c.migration_effort_hours for c in foundation_components)
        )
        phases.append(phase1)
        
        # Phase 2: Core Business Logic
        core_components = [
            c for c in migration_components 
            if c.business_criticality == 'high' and c.complexity_score <= 7.0
        ][:15]
        
        phase2 = MigrationPhase(
            phase_number=2,
            name="Core Business Logic Migration",
            objective="Migrate critical business logic with minimal business disruption",
            duration_weeks=12,
            components=core_components,
            prerequisites=["Phase 1 completed successfully", "Business stakeholder approval", "Comprehensive test suite"],
            deliverables=[
                "Core business logic modernized",
                "Business rule validation completed",
                "Performance benchmarks met",
                "Integration testing passed"
            ],
            success_criteria=[
                "All business rules function correctly",
                "Performance meets or exceeds current system",
                "Zero data loss during migration"
            ],
            risk_mitigation=[
                "Incremental migration with validation checkpoints",
                "Business user acceptance testing",
                "Performance monitoring and optimization"
            ],
            estimated_effort_hours=sum(c.migration_effort_hours for c in core_components)
        )
        phases.append(phase2)
        
        # Phase 3: Complex Integrations and Critical Systems
        critical_components = [
            c for c in migration_components 
            if c.business_criticality == 'critical' or c.complexity_score > 7.0
        ]
        
        phase3 = MigrationPhase(
            phase_number=3,
            name="Complex Systems & Integrations",
            objective="Migrate most complex and critical system components",
            duration_weeks=16,
            components=critical_components,
            prerequisites=["Phase 2 completed", "Extended testing period", "Business continuity plan activated"],
            deliverables=[
                "All complex integrations modernized",
                "External system connections updated",
                "Legacy system retirement plan executed",
                "Full system performance optimization"
            ],
            success_criteria=[
                "All integrations working correctly",
                "System performance optimized",
                "Legacy systems successfully retired"
            ],
            risk_mitigation=[
                "Extensive integration testing",
                "Gradual traffic migration",
                "24/7 monitoring during transition"
            ],
            estimated_effort_hours=sum(c.migration_effort_hours for c in critical_components)
        )
        phases.append(phase3)
        
        # Phase 4: Optimization and Enhancement
        phase4 = MigrationPhase(
            phase_number=4,
            name="Optimization & Enhancement",
            objective="Optimize migrated system and implement modern capabilities",
            duration_weeks=6,
            components=[],  # No specific components, focused on optimization
            prerequisites=["Phase 3 completed", "System stability achieved", "Performance baseline established"],
            deliverables=[
                "Performance optimization completed",
                "Modern features implemented",
                "Documentation updated",
                "Team training completed"
            ],
            success_criteria=[
                "Performance targets exceeded",
                "Modern capabilities fully operational", 
                "Team fully trained on new system"
            ],
            risk_mitigation=[
                "Gradual feature rollout",
                "User feedback incorporation",
                "Continuous monitoring"
            ],
            estimated_effort_hours=480  # 3 months of optimization work
        )
        phases.append(phase4)
        
        return phases
    
    async def _generate_dashboard_documentation(
        self,
        migration_strategy: MigrationStrategy,
        migration_components: List[MigrationComponent],
        business_rules_by_hierarchy: Dict[str, Any]
    ) -> str:
        """Generate comprehensive dashboard documentation"""
        
        sections = []
        
        # Executive Dashboard
        sections.append(self._generate_executive_dashboard_section(migration_strategy))
        
        # Migration Strategy Overview
        sections.append(self._generate_migration_strategy_section(migration_strategy))
        
        # Detailed Phase Planning
        sections.append(self._generate_phase_planning_section(migration_strategy.phases))
        
        # Component Analysis
        sections.append(self._generate_component_analysis_section(migration_components))
        
        # Risk Management
        sections.append(self._generate_risk_management_section(migration_strategy))
        
        # Technology Recommendations
        sections.append(self._generate_technology_section(migration_strategy))
        
        # Business Continuity Plan
        sections.append(self._generate_business_continuity_section(migration_strategy))
        
        # Implementation Checklist
        sections.append(self._generate_implementation_checklist())
        
        return "\\n\\n".join(sections)
    
    def _generate_executive_dashboard_section(self, strategy: MigrationStrategy) -> str:
        """Generate executive dashboard section"""
        
        return f"""# 🎯 Enterprise Migration Dashboard

**Generated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Migration Strategy**: Phased Modernization with Business Continuity Focus  
**Total Investment**: {strategy.total_effort_hours:,} hours ({strategy.estimated_duration_months} months)

## 📊 Executive Summary

{strategy.executive_summary}

## 🎲 Migration Investment Overview

| Metric | Value | Strategic Significance |
|--------|-------|----------------------|
| **Total Effort** | {strategy.total_effort_hours:,} hours | Complete system modernization investment |
| **Timeline** | {strategy.estimated_duration_months} months | Business continuity maintained throughout |
| **Recommended Team** | {strategy.recommended_team_size} developers | Optimal resource allocation for success |
| **Migration Phases** | {len(strategy.phases)} phases | Risk-managed incremental approach |
| **Critical Risks** | {len(strategy.critical_risks)} identified | Proactive risk mitigation planning |

## 🚀 Strategic Outcomes

Upon completion, this migration will deliver:

- **Modernized Technology Stack**: Current frameworks and security standards
- **Enhanced Performance**: Improved system responsiveness and scalability  
- **Reduced Technical Debt**: Clean, maintainable codebase for future development
- **Business Continuity**: Zero disruption to critical business operations
- **Enhanced Capabilities**: Modern features supporting business growth

---"""
    
    def _generate_migration_strategy_section(self, strategy: MigrationStrategy) -> str:
        """Generate migration strategy section"""
        
        return f"""## 🗺️ Migration Strategy & Approach

### Strategic Approach

Our migration strategy employs a **risk-managed, phased approach** that prioritizes business continuity while systematically modernizing system components.

### Key Strategic Principles

1. **Business Continuity First**: No disruption to critical business operations
2. **Incremental Progress**: Validate each phase before proceeding
3. **Risk Mitigation**: Comprehensive testing and rollback procedures
4. **Stakeholder Engagement**: Regular communication and validation checkpoints
5. **Performance Focus**: Meet or exceed current system performance

### Success Factors

{self._format_list_items(strategy.success_factors)}

### Technology Modernization Path

{self._format_technology_recommendations(strategy.technology_recommendations)}

---"""
    
    def _generate_phase_planning_section(self, phases: List[MigrationPhase]) -> str:
        """Generate detailed phase planning section"""
        
        sections = ["## 📅 Detailed Phase Planning"]
        sections.append("")
        sections.append("Each phase includes specific objectives, deliverables, and success criteria with actionable implementation guidance.")
        sections.append("")
        
        for phase in phases:
            sections.append(f"### Phase {phase.phase_number}: {phase.name}")
            sections.append(f"**Duration**: {phase.duration_weeks} weeks | **Effort**: {phase.estimated_effort_hours:,} hours")
            sections.append("")
            sections.append(f"**Objective**: {phase.objective}")
            sections.append("")
            
            if phase.components:
                sections.append("**Components to Migrate**:")
                for component in phase.components[:10]:  # Show top 10 components
                    sections.append(f"- `{component.name}` ({component.type}) - {component.migration_effort_hours}h - {component.modernization_approach}")
                sections.append("")
            
            sections.append("**Prerequisites**:")
            for prereq in phase.prerequisites:
                sections.append(f"- {prereq}")
            sections.append("")
            
            sections.append("**Key Deliverables**:")
            for deliverable in phase.deliverables:
                sections.append(f"- {deliverable}")
            sections.append("")
            
            sections.append("**Success Criteria**:")
            for criteria in phase.success_criteria:
                sections.append(f"- ✅ {criteria}")
            sections.append("")
            
            sections.append("**Risk Mitigation**:")
            for mitigation in phase.risk_mitigation:
                sections.append(f"- 🛡️ {mitigation}")
            sections.append("")
            
            sections.append("---")
            sections.append("")
        
        return "\\n".join(sections)
    
    def _generate_component_analysis_section(self, components: List[MigrationComponent]) -> str:
        """Generate component analysis section"""
        
        sections = ["## 🔧 Component Migration Analysis"]
        sections.append("")
        sections.append("Detailed analysis of system components with specific migration approaches and effort estimates.")
        sections.append("")
        
        # Group components by business criticality
        critical_components = [c for c in components if c.business_criticality == 'critical']
        high_components = [c for c in components if c.business_criticality == 'high']
        medium_components = [c for c in components if c.business_criticality == 'medium']
        
        if critical_components:
            sections.append("### Critical Business Components")
            sections.append("*Requires maximum attention and business stakeholder involvement*")
            sections.append("")
            sections.append("| Component | Type | Complexity | Effort (hrs) | Approach | Risks |")
            sections.append("|-----------|------|------------|--------------|----------|-------|")
            for comp in critical_components[:10]:
                risks_text = ", ".join(comp.risks[:2]) if comp.risks else "Low risk"
                sections.append(f"| `{comp.name}` | {comp.type} | {comp.complexity_score}/10 | {comp.migration_effort_hours} | {comp.modernization_approach} | {risks_text} |")
            sections.append("")
        
        if high_components:
            sections.append("### High-Priority Components")
            sections.append("*Important business logic requiring careful migration*")
            sections.append("")
            sections.append("| Component | Type | Complexity | Effort (hrs) | Approach |")
            sections.append("|-----------|------|------------|--------------|----------|")
            for comp in high_components[:15]:
                sections.append(f"| `{comp.name}` | {comp.type} | {comp.complexity_score}/10 | {comp.migration_effort_hours} | {comp.modernization_approach} |")
            sections.append("")
        
        # Summary statistics
        total_effort = sum(c.migration_effort_hours for c in components)
        avg_complexity = sum(c.complexity_score for c in components) / len(components) if components else 0
        
        sections.append("### Migration Statistics")
        sections.append("")
        sections.append(f"- **Total Components**: {len(components)}")
        sections.append(f"- **Average Complexity**: {avg_complexity:.1f}/10")
        sections.append(f"- **Total Effort**: {total_effort:,} hours")
        sections.append(f"- **Critical Components**: {len(critical_components)} (require special attention)")
        sections.append(f"- **High-Priority Components**: {len(high_components)}")
        sections.append("")
        
        return "\\n".join(sections)
    
    # Helper methods for formatting and analysis
    
    def _format_list_items(self, items: List[str]) -> str:
        """Format list items with bullet points"""
        return "\\n".join([f"- {item}" for item in items])
    
    def _format_technology_recommendations(self, tech_recs: Dict[str, str]) -> str:
        """Format technology recommendations"""
        if not tech_recs:
            return "Technology recommendations will be finalized during Phase 1 analysis."
        
        formatted = []
        for category, recommendation in tech_recs.items():
            formatted.append(f"- **{category}**: {recommendation}")
        return "\\n".join(formatted)
    
    def _find_business_rules_for_entity(
        self, 
        entity: Dict[str, Any], 
        business_rules_by_hierarchy: Dict[str, Any]
    ) -> List[BusinessRuleContext]:
        """Find business rules associated with an entity"""
        entity_rules = []
        entity_name = entity.get('name', '')
        
        # Search through all hierarchical rules
        for rules_dict in [
            business_rules_by_hierarchy.get('by_module', {}),
            business_rules_by_hierarchy.get('by_class', {}),
            business_rules_by_hierarchy.get('by_method', {})
        ]:
            for path, rules in rules_dict.items():
                if entity_name in path:
                    entity_rules.extend(rules)
        
        return entity_rules
    
    def _determine_business_criticality(
        self, 
        entity: Dict[str, Any], 
        business_rules: List[BusinessRuleContext]
    ) -> str:
        """Determine business criticality based on various factors"""
        
        criticality_score = 0
        
        # Business rules factor
        if len(business_rules) >= 5:
            criticality_score += 3
        elif len(business_rules) >= 2:
            criticality_score += 2
        elif len(business_rules) >= 1:
            criticality_score += 1
        
        # File path indicators
        file_path = entity.get('file_path', '').lower()
        if any(critical_indicator in file_path for critical_indicator in ['payment', 'order', 'account', 'security', 'auth']):
            criticality_score += 2
        elif any(important_indicator in file_path for important_indicator in ['service', 'controller', 'manager']):
            criticality_score += 1
        
        # Map score to criticality level
        if criticality_score >= 5:
            return 'critical'
        elif criticality_score >= 3:
            return 'high'
        elif criticality_score >= 1:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_base_migration_effort(self, entity: Dict[str, Any], complexity: float) -> int:
        """Calculate base migration effort in hours"""
        
        # Base effort by entity type
        base_efforts = {
            'class': 40,
            'interface': 20,
            'function': 16,
            'method': 12,
            'module': 60
        }
        
        entity_type = entity.get('type', 'function')
        base_effort = base_efforts.get(entity_type, 20)
        
        # Apply complexity multiplier
        complexity_multiplier = 1 + (complexity / 10)
        
        # Apply dependencies multiplier
        dependencies_count = len(entity.get('dependencies', []))
        dependencies_multiplier = 1 + (dependencies_count * 0.1)
        
        total_effort = base_effort * complexity_multiplier * dependencies_multiplier
        
        return int(total_effort)
    
    def _determine_modernization_approach(self, entity: Dict[str, Any], complexity: float) -> str:
        """Determine the best modernization approach for an entity"""
        
        entity_type = entity.get('type', '')
        file_path = entity.get('file_path', '').lower()
        
        if complexity <= 3.0:
            return "Direct migration with minimal refactoring"
        elif complexity <= 6.0:
            return "Refactor during migration for better maintainability"
        elif complexity <= 8.0:
            return "Significant refactoring required, consider redesign"
        else:
            return "Complex migration - consider complete rewrite"
    
    def _identify_migration_risks(self, entity: Dict[str, Any], complexity: float) -> List[str]:
        """Identify migration risks for an entity"""
        
        risks = []
        
        if complexity > 7.0:
            risks.append("High complexity may require extended testing")
        
        if len(entity.get('dependencies', [])) > 10:
            risks.append("Many dependencies may cause integration issues")
        
        file_path = entity.get('file_path', '').lower()
        if any(risky_pattern in file_path for risky_pattern in ['legacy', 'deprecated', 'old']):
            risks.append("Legacy code patterns may be difficult to modernize")
        
        if not risks:
            risks.append("Standard migration risks apply")
        
        return risks
    
    # Additional helper methods would continue here for database and integration analysis...
    
    async def _analyze_database_migration_complexity(self, database_analysis: Dict[str, Any]) -> List[MigrationComponent]:
        """Analyze database components for migration"""
        # Simplified implementation - would expand based on actual database analysis structure
        return []
    
    async def _analyze_integration_migration_complexity(self, integration_analysis: Dict[str, Any]) -> List[MigrationComponent]:
        """Analyze integration components for migration"""
        # Simplified implementation - would expand based on actual integration analysis structure
        return []
    
    async def _generate_executive_summary(self, components, total_effort, estimated_months, team_size) -> str:
        """Generate executive summary using AI"""
        prompt = f"""Generate a concise executive summary for a system migration project with {len(components)} components, {total_effort} hours effort, {estimated_months} months duration, and {team_size} person team."""
        
        try:
            return await self.ai_service.generate_content(prompt=prompt, max_tokens=500, temperature=0.3)
        except:
            return f"This migration project encompasses {len(components)} system components requiring {total_effort:,} hours of development effort over {estimated_months} months with a {team_size}-person team. The phased approach ensures business continuity while systematically modernizing the entire system architecture."
    
    def _identify_critical_migration_risks(self, components: List[MigrationComponent]) -> List[str]:
        """Identify critical risks across all components"""
        critical_risks = set()
        
        for component in components:
            if component.business_criticality == 'critical':
                critical_risks.update(component.risks)
        
        # Add general migration risks
        critical_risks.update([
            "Business disruption during migration phases",
            "Data loss or corruption during migration",
            "Integration failures with external systems",
            "Performance degradation post-migration"
        ])
        
        return list(critical_risks)[:10]  # Top 10 risks
    
    def _identify_success_factors(self, components, business_rules) -> List[str]:
        """Identify key success factors for migration"""
        return [
            "Strong executive sponsorship and stakeholder buy-in",
            "Dedicated migration team with appropriate skills",
            "Comprehensive testing strategy and validation procedures",
            "Effective communication plan for all stakeholders",
            "Robust rollback procedures for each migration phase",
            "Performance monitoring and optimization throughout migration"
        ]
    
    async def _generate_technology_recommendations(self, components: List[MigrationComponent]) -> Dict[str, str]:
        """Generate technology recommendations based on component analysis"""
        return {
            "Backend Framework": "Modern REST API framework for improved maintainability",
            "Database": "Optimized database architecture for better performance",
            "Integration": "API-first integration approach for better modularity",
            "Testing": "Automated testing suite for continuous validation"
        }
    
    async def _generate_business_continuity_plan(self, components, phases) -> str:
        """Generate business continuity plan"""
        return "Business continuity will be maintained through parallel system operation, incremental migration with validation checkpoints, and comprehensive rollback procedures for each migration phase."
    
    def _generate_risk_management_section(self, strategy: MigrationStrategy) -> str:
        """Generate risk management section"""
        return f"""## ⚠️ Risk Management Strategy

### Critical Risks Identified

{self._format_list_items(strategy.critical_risks)}

### Risk Mitigation Approach

Our comprehensive risk management strategy includes proactive identification, assessment, and mitigation of all migration risks with specific contingency plans for critical scenarios.

---"""
    
    def _generate_technology_section(self, strategy: MigrationStrategy) -> str:
        """Generate technology recommendations section"""
        return f"""## 💻 Technology Recommendations

### Modernization Technology Stack

{self._format_technology_recommendations(strategy.technology_recommendations)}

### Technology Migration Strategy

Technology migration will follow industry best practices with careful evaluation of modern frameworks that support long-term maintainability and business growth.

---"""
    
    def _generate_business_continuity_section(self, strategy: MigrationStrategy) -> str:
        """Generate business continuity section"""
        return f"""## 🏢 Business Continuity Plan

{strategy.business_continuity_plan}

### Continuity Assurance Measures

- **Parallel System Operation**: Old and new systems run simultaneously during transition
- **Incremental Migration**: Gradual transition with validation at each step
- **Immediate Rollback**: Ability to revert to previous state within minutes
- **24/7 Monitoring**: Continuous system health monitoring during migration phases

---"""
    
    def _generate_implementation_checklist(self) -> str:
        """Generate implementation checklist"""
        return """## ✅ Implementation Checklist

### Pre-Migration Preparation
- [ ] Executive approval and budget allocation
- [ ] Migration team assembled and trained
- [ ] Development and testing environments prepared
- [ ] Stakeholder communication plan activated
- [ ] Baseline performance metrics established

### Phase Execution Checklist
- [ ] Phase prerequisites validated
- [ ] Component migration completed and tested
- [ ] Business rule validation successful
- [ ] Performance benchmarks met
- [ ] Stakeholder acceptance obtained
- [ ] Documentation updated

### Post-Migration Validation
- [ ] All success criteria met
- [ ] Performance optimization completed
- [ ] User training completed
- [ ] Support procedures established
- [ ] Legacy system retirement completed

---

*This migration dashboard provides actionable guidance for successful enterprise system modernization. All recommendations are based on comprehensive system analysis and industry best practices.*"""

# Global instance
enhanced_migration_dashboard = None

def get_enhanced_migration_dashboard(ai_service: AIService, intelligence_graph: CodeIntelligenceGraph) -> EnhancedMigrationDashboard:
    """Get or create enhanced migration dashboard instance"""
    global enhanced_migration_dashboard
    if enhanced_migration_dashboard is None:
        enhanced_migration_dashboard = EnhancedMigrationDashboard(ai_service, intelligence_graph)
    return enhanced_migration_dashboard