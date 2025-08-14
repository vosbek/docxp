"""
Migration Dashboard Generator

Creates executive summaries, risk matrices, and migration roadmaps for enterprise legacy systems.
Transforms technical analysis into actionable business insights for stakeholders.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from app.core.logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class MigrationComponent:
    """Represents a component in the migration analysis"""
    name: str
    type: str  # interface, service, database, integration
    complexity: str  # Low, Medium, High, Very High
    dependencies: int
    risk_level: str  # Low, Medium, High, Critical
    effort_estimate: str  # hours or days
    modernization_approach: str
    priority: int  # 1-5, 1 being highest priority

@dataclass
class MigrationSummary:
    """Overall migration summary and metrics"""
    total_components: int
    migration_readiness_score: int  # 0-100
    estimated_effort_days: int
    critical_components: int
    high_risk_components: int
    modernization_opportunities: int
    recommended_approach: str
    timeline_estimate: str

class MigrationDashboard:
    """Generates migration dashboards and executive summaries"""
    
    def generate_migration_dashboard(self, entities: List[Dict[str, Any]], 
                                   database_analysis: Dict[str, Any],
                                   integration_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive migration dashboard"""
        logger.info("Generating migration dashboard")
        
        # Analyze all components
        components = self._analyze_components(entities, database_analysis, integration_analysis)
        
        # Generate summary metrics
        summary = self._generate_summary_metrics(components, database_analysis, integration_analysis)
        
        # Create risk assessment matrix
        risk_matrix = self._create_risk_matrix(components)
        
        # Generate migration roadmap
        roadmap = self._create_migration_roadmap(components, summary)
        
        # Create executive summary
        executive_summary = self._create_executive_summary(summary, components)
        
        # Generate effort estimation
        effort_breakdown = self._create_effort_breakdown(components)
        
        return {
            'summary': summary,
            'components': components,
            'risk_matrix': risk_matrix,
            'migration_roadmap': roadmap,
            'executive_summary': executive_summary,
            'effort_breakdown': effort_breakdown,
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def _analyze_components(self, entities: List[Dict[str, Any]], 
                          database_analysis: Dict[str, Any],
                          integration_analysis: Dict[str, Any]) -> List[MigrationComponent]:
        """Analyze all components for migration assessment"""
        components = []
        
        # Analyze code entities
        for entity in entities:
            if entity.get('entity_type') in ['class', 'function', 'corba_interface', 'corba_struct']:
                component = self._analyze_code_component(entity)
                if component:
                    components.append(component)
        
        # Analyze database components
        if database_analysis.get('total_queries_found', 0) > 0:
            db_components = self._analyze_database_components(database_analysis)
            components.extend(db_components)
        
        # Analyze integration components
        if integration_analysis.get('technology_breakdown', {}).get('integration_flows', 0) > 0:
            integration_components = self._analyze_integration_components(integration_analysis)
            components.extend(integration_components)
        
        return components
    
    def _analyze_code_component(self, entity: Dict[str, Any]) -> Optional[MigrationComponent]:
        """Analyze a code entity for migration complexity"""
        entity_type = entity.get('entity_type')
        name = entity.get('name', 'Unknown')
        
        # Skip analysis entities
        if 'analysis' in entity_type:
            return None
        
        # Determine complexity
        complexity = self._calculate_component_complexity(entity)
        
        # Estimate effort
        effort = self._estimate_component_effort(entity, complexity)
        
        # Determine risk level
        risk_level = self._assess_component_risk(entity, complexity)
        
        # Suggest modernization approach
        modernization_approach = self._suggest_modernization_approach(entity)
        
        # Calculate dependencies
        dependencies = self._count_dependencies(entity)
        
        # Determine priority
        priority = self._calculate_priority(complexity, risk_level, dependencies)
        
        return MigrationComponent(
            name=name,
            type=self._map_entity_type_to_component_type(entity_type),
            complexity=complexity,
            dependencies=dependencies,
            risk_level=risk_level,
            effort_estimate=effort,
            modernization_approach=modernization_approach,
            priority=priority
        )
    
    def _calculate_component_complexity(self, entity: Dict[str, Any]) -> str:
        """Calculate complexity score for a component"""
        complexity_score = 0
        entity_type = entity.get('entity_type', '')
        
        # Base complexity by type
        if entity_type == 'corba_interface':
            complexity_score += 15  # CORBA interfaces are inherently complex
            complexity_score += len(entity.get('methods', [])) * 2
            if entity.get('inheritance'):
                complexity_score += 10
        elif entity_type == 'class':
            complexity_score += 5
            complexity_score += len(entity.get('methods', [])) * 1
            complexity_score += entity.get('complexity', 0)
        elif entity_type == 'function':
            complexity_score += entity.get('complexity', 0)
        
        # Additional complexity factors
        if entity.get('design_patterns'):
            complexity_score += len(entity.get('design_patterns', [])) * 3
        
        if entity.get('business_logic_patterns'):
            complexity_score += len(entity.get('business_logic_patterns', [])) * 2
        
        # Convert to category
        if complexity_score < 10:
            return "Low"
        elif complexity_score < 25:
            return "Medium"
        elif complexity_score < 50:
            return "High"
        else:
            return "Very High"
    
    def _estimate_component_effort(self, entity: Dict[str, Any], complexity: str) -> str:
        """Estimate effort required to migrate component"""
        base_hours = {
            'Low': 8,
            'Medium': 24,
            'High': 56,
            'Very High': 120
        }
        
        hours = base_hours.get(complexity, 24)
        
        # Adjust based on entity type
        entity_type = entity.get('entity_type', '')
        if entity_type == 'corba_interface':
            hours *= 1.5  # CORBA requires more effort
        elif entity_type == 'class' and entity.get('methods', []):
            hours += len(entity.get('methods', [])) * 2
        
        # Format output
        if hours < 40:
            return f"{hours} hours"
        else:
            return f"{hours // 8} days"
    
    def _assess_component_risk(self, entity: Dict[str, Any], complexity: str) -> str:
        """Assess migration risk for component"""
        risk_score = 0
        
        # Complexity contributes to risk
        risk_scores = {'Low': 1, 'Medium': 2, 'High': 3, 'Very High': 4}
        risk_score += risk_scores.get(complexity, 2)
        
        # Entity type risk factors
        entity_type = entity.get('entity_type', '')
        if entity_type == 'corba_interface':
            risk_score += 2  # CORBA is high risk
        
        # Dependencies increase risk
        if entity.get('inheritance') or entity.get('base_classes'):
            risk_score += 1
        
        # Business logic increases risk
        if entity.get('business_logic_patterns'):
            risk_score += 1
        
        # Convert to category
        if risk_score <= 2:
            return "Low"
        elif risk_score <= 4:
            return "Medium"
        elif risk_score <= 6:
            return "High"
        else:
            return "Critical"
    
    def _suggest_modernization_approach(self, entity: Dict[str, Any]) -> str:
        """Suggest modernization approach for component"""
        entity_type = entity.get('entity_type', '')
        
        if entity_type == 'corba_interface':
            return "Convert to REST API with OpenAPI specification"
        elif entity_type == 'corba_struct':
            return "Convert to JSON schema or DTO class"
        elif entity_type == 'class' and entity.get('design_patterns'):
            patterns = entity.get('design_patterns', [])
            if 'Singleton' in patterns:
                return "Replace with dependency injection"
            elif 'Factory' in patterns:
                return "Modernize to use IoC container"
            else:
                return "Refactor to modern design patterns"
        else:
            return "Refactor with modern best practices"
    
    def _count_dependencies(self, entity: Dict[str, Any]) -> int:
        """Count component dependencies"""
        deps = 0
        
        # Count various dependency types
        if entity.get('inheritance'):
            deps += len(entity.get('inheritance', []))
        if entity.get('base_classes'):
            deps += len(entity.get('base_classes', []))
        if entity.get('function_calls'):
            deps += len(entity.get('function_calls', []))
        
        return min(deps, 99)  # Cap at 99 for display
    
    def _calculate_priority(self, complexity: str, risk_level: str, dependencies: int) -> int:
        """Calculate migration priority (1=highest, 5=lowest)"""
        priority_score = 0
        
        # Risk contributes most to priority
        risk_scores = {'Critical': 4, 'High': 3, 'Medium': 2, 'Low': 1}
        priority_score += risk_scores.get(risk_level, 2)
        
        # Complexity contributes
        complexity_scores = {'Very High': 3, 'High': 2, 'Medium': 1, 'Low': 0}
        priority_score += complexity_scores.get(complexity, 1)
        
        # High dependencies increase priority
        if dependencies > 10:
            priority_score += 1
        elif dependencies > 5:
            priority_score += 0.5
        
        # Convert to 1-5 scale
        if priority_score >= 6:
            return 1  # Highest priority
        elif priority_score >= 5:
            return 2
        elif priority_score >= 3:
            return 3
        elif priority_score >= 2:
            return 4
        else:
            return 5  # Lowest priority
    
    def _map_entity_type_to_component_type(self, entity_type: str) -> str:
        """Map entity types to component types"""
        mapping = {
            'corba_interface': 'CORBA Interface',
            'corba_struct': 'Data Structure',
            'corba_enum': 'Data Type',
            'class': 'Service Class',
            'function': 'Function',
            'interface': 'Interface',
            'struts_action': 'Web Action'
        }
        return mapping.get(entity_type, 'Component')
    
    def _analyze_database_components(self, database_analysis: Dict[str, Any]) -> List[MigrationComponent]:
        """Analyze database components"""
        components = []
        
        static_analysis = database_analysis.get('static_analysis', {})
        total_queries = len(static_analysis.get('queries', []))
        unique_tables = len(static_analysis.get('tables', []))
        
        if total_queries > 0:
            # Create component for database layer
            complexity = "Medium"
            if total_queries > 50:
                complexity = "High"
            elif total_queries > 100:
                complexity = "Very High"
            
            risk_level = "Medium"
            if unique_tables > 20:
                risk_level = "High"
            
            effort_days = max(5, (total_queries // 10) + (unique_tables // 5))
            
            component = MigrationComponent(
                name=f"Database Layer ({unique_tables} tables, {total_queries} queries)",
                type="Database",
                complexity=complexity,
                dependencies=unique_tables,
                risk_level=risk_level,
                effort_estimate=f"{effort_days} days",
                modernization_approach="API-first data access with ORM/repository pattern",
                priority=2
            )
            components.append(component)
        
        return components
    
    def _analyze_integration_components(self, integration_analysis: Dict[str, Any]) -> List[MigrationComponent]:
        """Analyze integration components"""
        components = []
        
        breakdown = integration_analysis.get('technology_breakdown', {})
        flows = breakdown.get('integration_flows', 0)
        
        if flows > 0:
            complexity = "Medium"
            if flows > 20:
                complexity = "High"
            elif flows > 50:
                complexity = "Very High"
            
            risk_level = "High"  # Integrations are typically high risk
            effort_days = max(10, flows // 2)
            
            component = MigrationComponent(
                name=f"Integration Layer ({flows} integration flows)",
                type="Integration",
                complexity=complexity,
                dependencies=flows,
                risk_level=risk_level,
                effort_estimate=f"{effort_days} days",
                modernization_approach="API gateway with microservices architecture",
                priority=1  # High priority
            )
            components.append(component)
        
        return components
    
    def _generate_summary_metrics(self, components: List[MigrationComponent],
                                database_analysis: Dict[str, Any],
                                integration_analysis: Dict[str, Any]) -> MigrationSummary:
        """Generate overall migration summary metrics"""
        total_components = len(components)
        critical_components = len([c for c in components if c.risk_level == 'Critical'])
        high_risk_components = len([c for c in components if c.risk_level in ['High', 'Critical']])
        
        # Calculate migration readiness score (0-100)
        readiness_score = self._calculate_readiness_score(components, database_analysis, integration_analysis)
        
        # Estimate total effort
        total_days = self._estimate_total_effort(components)
        
        # Count modernization opportunities
        modernization_opportunities = len([c for c in components if c.complexity in ['Low', 'Medium']])
        
        # Recommend approach
        recommended_approach = self._recommend_migration_approach(components, readiness_score)
        
        # Estimate timeline
        timeline_estimate = self._estimate_timeline(total_days, high_risk_components)
        
        return MigrationSummary(
            total_components=total_components,
            migration_readiness_score=readiness_score,
            estimated_effort_days=total_days,
            critical_components=critical_components,
            high_risk_components=high_risk_components,
            modernization_opportunities=modernization_opportunities,
            recommended_approach=recommended_approach,
            timeline_estimate=timeline_estimate
        )
    
    def _calculate_readiness_score(self, components: List[MigrationComponent],
                                 database_analysis: Dict[str, Any],
                                 integration_analysis: Dict[str, Any]) -> int:
        """Calculate migration readiness score (0-100)"""
        score = 50  # Start at 50
        
        # Factor in component complexity
        low_complexity = len([c for c in components if c.complexity == 'Low'])
        medium_complexity = len([c for c in components if c.complexity == 'Medium'])
        high_complexity = len([c for c in components if c.complexity in ['High', 'Very High']])
        
        if components:
            complexity_ratio = (low_complexity + medium_complexity * 0.7 + high_complexity * 0.3) / len(components)
            score += int(complexity_ratio * 30)
        
        # Factor in risk levels
        critical_risk = len([c for c in components if c.risk_level == 'Critical'])
        if critical_risk > 0:
            score -= min(30, critical_risk * 5)
        
        # Factor in database analysis
        if database_analysis.get('analysis_mode') == 'enhanced':
            score += 10  # Bonus for having database connectivity
        
        # Factor in integration patterns
        integration_insights = integration_analysis.get('migration_insights', {})
        if integration_insights.get('migration_complexity') == 'Low':
            score += 15
        elif integration_insights.get('migration_complexity') == 'High':
            score -= 15
        
        return max(0, min(100, score))
    
    def _estimate_total_effort(self, components: List[MigrationComponent]) -> int:
        """Estimate total effort in days"""
        total_hours = 0
        
        for component in components:
            effort_str = component.effort_estimate
            if 'hours' in effort_str:
                hours = int(effort_str.split()[0])
                total_hours += hours
            elif 'days' in effort_str:
                days = int(effort_str.split()[0])
                total_hours += days * 8
        
        # Add 20% buffer for project management and integration
        total_hours = int(total_hours * 1.2)
        
        return total_hours // 8  # Convert to days
    
    def _recommend_migration_approach(self, components: List[MigrationComponent], readiness_score: int) -> str:
        """Recommend migration approach based on analysis"""
        if readiness_score >= 80:
            return "Direct Migration - System is well-suited for modernization"
        elif readiness_score >= 60:
            return "Phased Migration - Migrate in stages starting with low-risk components"
        elif readiness_score >= 40:
            return "Hybrid Approach - Maintain legacy system while building new components"
        else:
            return "Strangler Fig Pattern - Gradually replace legacy system piece by piece"
    
    def _estimate_timeline(self, total_days: int, high_risk_components: int) -> str:
        """Estimate migration timeline"""
        # Add buffer for high-risk components
        buffered_days = total_days + (high_risk_components * 5)
        
        if buffered_days <= 30:
            return "1 month"
        elif buffered_days <= 90:
            return "2-3 months"
        elif buffered_days <= 180:
            return "4-6 months"
        elif buffered_days <= 365:
            return "6-12 months"
        else:
            return "12+ months (consider breaking into smaller projects)"
    
    def _create_risk_matrix(self, components: List[MigrationComponent]) -> Dict[str, Any]:
        """Create risk assessment matrix"""
        matrix = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': []
        }
        
        for component in components:
            risk_key = component.risk_level.lower()
            if risk_key in matrix:
                matrix[risk_key].append({
                    'name': component.name,
                    'type': component.type,
                    'complexity': component.complexity,
                    'effort': component.effort_estimate,
                    'dependencies': component.dependencies,
                    'approach': component.modernization_approach
                })
        
        return matrix
    
    def _create_migration_roadmap(self, components: List[MigrationComponent], 
                                summary: MigrationSummary) -> Dict[str, Any]:
        """Create migration roadmap with phases"""
        # Sort components by priority
        sorted_components = sorted(components, key=lambda x: (x.priority, x.risk_level != 'Critical'))
        
        # Divide into phases
        total_components = len(sorted_components)
        phase1_end = max(1, total_components // 3)
        phase2_end = max(phase1_end + 1, (2 * total_components) // 3)
        
        phases = {
            'phase_1': {
                'name': 'Foundation & Critical Components',
                'components': sorted_components[:phase1_end],
                'focus': 'High-risk components and infrastructure setup'
            },
            'phase_2': {
                'name': 'Core Business Logic',
                'components': sorted_components[phase1_end:phase2_end],
                'focus': 'Main business functionality migration'
            },
            'phase_3': {
                'name': 'Integration & Optimization',
                'components': sorted_components[phase2_end:],
                'focus': 'Integration testing and performance optimization'
            }
        }
        
        return phases
    
    def _create_executive_summary(self, summary: MigrationSummary, 
                                components: List[MigrationComponent]) -> Dict[str, Any]:
        """Create executive summary for stakeholders"""
        # Key insights
        insights = []
        
        if summary.migration_readiness_score >= 70:
            insights.append("System shows good readiness for modernization")
        elif summary.migration_readiness_score < 40:
            insights.append("System requires significant preparation before migration")
        
        if summary.critical_components > 0:
            insights.append(f"{summary.critical_components} critical components require immediate attention")
        
        # Technology breakdown
        tech_breakdown = {}
        for component in components:
            tech_breakdown[component.type] = tech_breakdown.get(component.type, 0) + 1
        
        return {
            'readiness_score': summary.migration_readiness_score,
            'timeline': summary.timeline_estimate,
            'effort_estimate': f"{summary.estimated_effort_days} days",
            'recommended_approach': summary.recommended_approach,
            'key_insights': insights,
            'technology_breakdown': tech_breakdown,
            'investment_required': self._estimate_investment(summary.estimated_effort_days),
            'business_impact': self._assess_business_impact(summary)
        }
    
    def _create_effort_breakdown(self, components: List[MigrationComponent]) -> Dict[str, Any]:
        """Create detailed effort breakdown"""
        breakdown = {}
        
        for component in components:
            comp_type = component.type
            if comp_type not in breakdown:
                breakdown[comp_type] = {
                    'components': 0,
                    'total_effort': 0,
                    'avg_effort': 0,
                    'complexity_distribution': {'Low': 0, 'Medium': 0, 'High': 0, 'Very High': 0}
                }
            
            # Extract effort in hours
            effort_str = component.effort_estimate
            if 'hours' in effort_str:
                hours = int(effort_str.split()[0])
            elif 'days' in effort_str:
                days = int(effort_str.split()[0])
                hours = days * 8
            else:
                hours = 24  # Default
            
            breakdown[comp_type]['components'] += 1
            breakdown[comp_type]['total_effort'] += hours
            breakdown[comp_type]['complexity_distribution'][component.complexity] += 1
        
        # Calculate averages
        for comp_type in breakdown:
            comp_count = breakdown[comp_type]['components']
            if comp_count > 0:
                breakdown[comp_type]['avg_effort'] = breakdown[comp_type]['total_effort'] // comp_count
        
        return breakdown
    
    def _estimate_investment(self, effort_days: int) -> str:
        """Estimate financial investment required"""
        # Rough estimate: $1000/day for development + overhead
        cost_per_day = 1000
        total_cost = effort_days * cost_per_day
        
        if total_cost < 50000:
            return f"${total_cost:,} (Small project)"
        elif total_cost < 250000:
            return f"${total_cost:,} (Medium project)"
        elif total_cost < 1000000:
            return f"${total_cost:,} (Large project)"
        else:
            return f"${total_cost:,} (Enterprise project)"
    
    def _assess_business_impact(self, summary: MigrationSummary) -> str:
        """Assess business impact of migration"""
        if summary.migration_readiness_score >= 70:
            return "Low disruption expected - system is migration-ready"
        elif summary.migration_readiness_score >= 50:
            return "Moderate disruption - requires careful planning"
        else:
            return "High disruption risk - consider phased approach"

# Singleton instance
migration_dashboard = MigrationDashboard()