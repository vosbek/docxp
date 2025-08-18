"""
Flow Validator Service

This service validates the completeness of traced flows, identifies missing links
in chains, and provides confidence scoring for flow accuracy.

Part of Week 4, Task 4.3 implementation in the enterprise transformation plan.
"""

from typing import List, Dict, Optional, Set, Tuple, Any
import logging
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import re

from app.models.business_rule_trace import BusinessRuleTrace, FlowStep

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Severity levels for validation issues"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FlowValidationIssueType(Enum):
    """Types of flow validation issues"""
    MISSING_LINK = "missing_link"
    BROKEN_DEPENDENCY = "broken_dependency"
    CIRCULAR_REFERENCE = "circular_reference"
    INCOMPLETE_TRACE = "incomplete_trace"
    LOW_CONFIDENCE = "low_confidence"
    TECHNOLOGY_GAP = "technology_gap"
    ORPHANED_STEP = "orphaned_step"
    DUPLICATE_STEP = "duplicate_step"


@dataclass
class ValidationIssue:
    """Represents a validation issue found in a flow trace"""
    issue_type: FlowValidationIssueType
    severity: ValidationSeverity
    description: str
    affected_steps: List[int]  # Step orders affected
    suggested_fix: Optional[str] = None
    confidence_impact: float = 0.0  # How much this impacts overall confidence


@dataclass
class FlowValidationResult:
    """Result of flow validation"""
    is_valid: bool
    overall_confidence: float
    completeness_score: float
    issues: List[ValidationIssue]
    recommendations: List[str]
    validation_timestamp: datetime
    
    @property
    def critical_issues(self) -> List[ValidationIssue]:
        """Get only critical issues"""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.CRITICAL]
    
    @property
    def has_critical_issues(self) -> bool:
        """Check if there are critical issues"""
        return len(self.critical_issues) > 0


class FlowPatternValidator:
    """Validates common flow patterns in enterprise applications"""
    
    def __init__(self):
        self.expected_patterns = {
            'web_mvc': ['JSP', 'Struts Action', 'Java', 'Database'],
            'service_oriented': ['JSP', 'Struts Action', 'Service', 'DAO', 'Database'],
            'corba_integration': ['CORBA', 'Java Implementation', 'Service', 'Database'],
            'layered_architecture': ['Presentation', 'Business', 'Data']
        }
        
    def validate_pattern(self, flow_steps: List[FlowStep]) -> List[ValidationIssue]:
        """Validate flow against expected patterns"""
        issues = []
        technologies = [step.technology for step in flow_steps]
        
        # Check for common patterns
        pattern_match = self._identify_pattern(technologies)
        if pattern_match:
            issues.extend(self._validate_against_pattern(flow_steps, pattern_match))
        else:
            issues.append(ValidationIssue(
                issue_type=FlowValidationIssueType.TECHNOLOGY_GAP,
                severity=ValidationSeverity.MEDIUM,
                description="Flow doesn't match any recognized architectural pattern",
                affected_steps=list(range(len(flow_steps))),
                suggested_fix="Review architectural pattern and ensure all layers are traced"
            ))
        
        return issues
    
    def _identify_pattern(self, technologies: List[str]) -> Optional[str]:
        """Identify which pattern the flow most closely matches"""
        best_match = None
        best_score = 0
        
        for pattern_name, pattern_techs in self.expected_patterns.items():
            score = self._calculate_pattern_match_score(technologies, pattern_techs)
            if score > best_score:
                best_score = score
                best_match = pattern_name
        
        return best_match if best_score > 0.5 else None
    
    def _calculate_pattern_match_score(self, actual_techs: List[str], pattern_techs: List[str]) -> float:
        """Calculate how well actual technologies match a pattern"""
        matches = 0
        for pattern_tech in pattern_techs:
            if any(pattern_tech.lower() in actual_tech.lower() for actual_tech in actual_techs):
                matches += 1
        
        return matches / len(pattern_techs)
    
    def _validate_against_pattern(self, flow_steps: List[FlowStep], pattern: str) -> List[ValidationIssue]:
        """Validate flow steps against a specific pattern"""
        issues = []
        pattern_techs = self.expected_patterns[pattern]
        actual_techs = [step.technology for step in flow_steps]
        
        # Check for missing layers
        for expected_tech in pattern_techs:
            if not any(expected_tech.lower() in actual_tech.lower() for actual_tech in actual_techs):
                issues.append(ValidationIssue(
                    issue_type=FlowValidationIssueType.MISSING_LINK,
                    severity=ValidationSeverity.HIGH,
                    description=f"Missing expected technology layer: {expected_tech}",
                    affected_steps=[],
                    suggested_fix=f"Verify if {expected_tech} layer exists and should be included in trace",
                    confidence_impact=-0.2
                ))
        
        return issues


class FlowValidator:
    """
    Validates the completeness and accuracy of business rule flow traces.
    
    This service ensures that traced flows are complete, accurate, and follow
    expected architectural patterns for enterprise applications.
    """
    
    def __init__(self):
        self.pattern_validator = FlowPatternValidator()
        self.validation_rules = self._initialize_validation_rules()
        
    def _initialize_validation_rules(self) -> Dict[str, callable]:
        """Initialize validation rules"""
        return {
            'step_sequence': self._validate_step_sequence,
            'dependency_consistency': self._validate_dependency_consistency,
            'confidence_thresholds': self._validate_confidence_thresholds,
            'technology_transitions': self._validate_technology_transitions,
            'file_path_validity': self._validate_file_paths,
            'business_logic_completeness': self._validate_business_logic,
            'circular_dependencies': self._validate_circular_dependencies,
            'duplicate_steps': self._validate_duplicate_steps
        }
    
    async def validate_flow(self, business_rule_trace: BusinessRuleTrace) -> FlowValidationResult:
        """
        Validate a complete business rule flow trace.
        
        Args:
            business_rule_trace: The flow trace to validate
            
        Returns:
            FlowValidationResult with validation outcomes
        """
        logger.info(f"Validating flow trace: {business_rule_trace.rule_name}")
        
        issues = []
        
        # Run all validation rules
        for rule_name, rule_func in self.validation_rules.items():
            try:
                rule_issues = rule_func(business_rule_trace.flow_steps)
                issues.extend(rule_issues)
                logger.debug(f"Rule '{rule_name}' found {len(rule_issues)} issues")
            except Exception as e:
                logger.error(f"Error running validation rule '{rule_name}': {str(e)}")
                issues.append(ValidationIssue(
                    issue_type=FlowValidationIssueType.INCOMPLETE_TRACE,
                    severity=ValidationSeverity.HIGH,
                    description=f"Validation rule '{rule_name}' failed: {str(e)}",
                    affected_steps=[]
                ))
        
        # Run pattern validation
        pattern_issues = self.pattern_validator.validate_pattern(business_rule_trace.flow_steps)
        issues.extend(pattern_issues)
        
        # Calculate scores
        completeness_score = self._calculate_completeness_score(business_rule_trace.flow_steps, issues)
        overall_confidence = self._calculate_overall_confidence(business_rule_trace, issues)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(issues, business_rule_trace)
        
        # Determine if flow is valid
        is_valid = not any(issue.severity == ValidationSeverity.CRITICAL for issue in issues)
        
        result = FlowValidationResult(
            is_valid=is_valid,
            overall_confidence=overall_confidence,
            completeness_score=completeness_score,
            issues=issues,
            recommendations=recommendations,
            validation_timestamp=datetime.utcnow()
        )
        
        logger.info(f"Flow validation complete: {business_rule_trace.rule_name} - "
                   f"Valid: {is_valid}, Confidence: {overall_confidence:.2f}, "
                   f"Issues: {len(issues)}")
        
        return result
    
    def _validate_step_sequence(self, flow_steps: List[FlowStep]) -> List[ValidationIssue]:
        """Validate that flow steps are in correct sequence"""
        issues = []
        
        if not flow_steps:
            issues.append(ValidationIssue(
                issue_type=FlowValidationIssueType.INCOMPLETE_TRACE,
                severity=ValidationSeverity.CRITICAL,
                description="Flow trace has no steps",
                affected_steps=[],
                confidence_impact=-1.0
            ))
            return issues
        
        # Check step order continuity
        expected_order = 1
        for step in flow_steps:
            if step.step_order != expected_order:
                issues.append(ValidationIssue(
                    issue_type=FlowValidationIssueType.MISSING_LINK,
                    severity=ValidationSeverity.HIGH,
                    description=f"Step order gap: expected {expected_order}, found {step.step_order}",
                    affected_steps=[step.step_order],
                    suggested_fix="Check for missing intermediate steps in the flow",
                    confidence_impact=-0.1
                ))
            expected_order = step.step_order + 1
        
        return issues
    
    def _validate_dependency_consistency(self, flow_steps: List[FlowStep]) -> List[ValidationIssue]:
        """Validate that step dependencies are consistent"""
        issues = []
        
        # Create a map of components for dependency checking
        components_by_step = {step.step_order: step.component_name for step in flow_steps}
        
        for step in flow_steps:
            for dependency in step.dependencies:
                # Check if dependency exists in previous steps
                dependency_found = any(
                    dependency in components_by_step[prev_step]
                    for prev_step in range(1, step.step_order)
                    if prev_step in components_by_step
                )
                
                if not dependency_found:
                    issues.append(ValidationIssue(
                        issue_type=FlowValidationIssueType.BROKEN_DEPENDENCY,
                        severity=ValidationSeverity.MEDIUM,
                        description=f"Dependency '{dependency}' not found in previous steps",
                        affected_steps=[step.step_order],
                        suggested_fix="Verify dependency exists or add missing step",
                        confidence_impact=-0.1
                    ))
        
        return issues
    
    def _validate_confidence_thresholds(self, flow_steps: List[FlowStep]) -> List[ValidationIssue]:
        """Validate confidence scores meet minimum thresholds"""
        issues = []
        min_confidence_threshold = 0.3  # Minimum acceptable confidence
        
        for step in flow_steps:
            confidence = getattr(step, 'confidence_score', 0.5)  # Default if not set
            
            if confidence < min_confidence_threshold:
                severity = ValidationSeverity.CRITICAL if confidence < 0.1 else ValidationSeverity.HIGH
                issues.append(ValidationIssue(
                    issue_type=FlowValidationIssueType.LOW_CONFIDENCE,
                    severity=severity,
                    description=f"Step has low confidence score: {confidence:.2f}",
                    affected_steps=[step.step_order],
                    suggested_fix="Review parsing logic or add manual validation",
                    confidence_impact=-0.2
                ))
        
        return issues
    
    def _validate_technology_transitions(self, flow_steps: List[FlowStep]) -> List[ValidationIssue]:
        """Validate technology transitions make sense"""
        issues = []
        
        # Define valid technology transitions
        valid_transitions = {
            'JSP': ['Struts Action', 'Java', 'Servlet'],
            'Struts Action': ['Java', 'Service', 'DAO'],
            'Java': ['Database', 'Service', 'DAO', 'CORBA'],
            'CORBA': ['Java Implementation', 'Java'],
            'Service': ['DAO', 'Database'],
            'DAO': ['Database']
        }
        
        for i in range(len(flow_steps) - 1):
            current_tech = flow_steps[i].technology
            next_tech = flow_steps[i + 1].technology
            
            valid_next_techs = valid_transitions.get(current_tech, [])
            
            if valid_next_techs and next_tech not in valid_next_techs:
                # Check for partial matches (e.g., "Struts Action" contains "Action")
                partial_match = any(
                    valid_tech.lower() in next_tech.lower() or next_tech.lower() in valid_tech.lower()
                    for valid_tech in valid_next_techs
                )
                
                if not partial_match:
                    issues.append(ValidationIssue(
                        issue_type=FlowValidationIssueType.TECHNOLOGY_GAP,
                        severity=ValidationSeverity.MEDIUM,
                        description=f"Unusual technology transition: {current_tech} → {next_tech}",
                        affected_steps=[flow_steps[i].step_order, flow_steps[i + 1].step_order],
                        suggested_fix="Verify transition is correct or add intermediate steps"
                    ))
        
        return issues
    
    def _validate_file_paths(self, flow_steps: List[FlowStep]) -> List[ValidationIssue]:
        """Validate that file paths are reasonable"""
        issues = []
        
        for step in flow_steps:
            file_path = step.file_path
            
            if not file_path or file_path.strip() == '':
                issues.append(ValidationIssue(
                    issue_type=FlowValidationIssueType.INCOMPLETE_TRACE,
                    severity=ValidationSeverity.MEDIUM,
                    description="Step missing file path information",
                    affected_steps=[step.step_order],
                    suggested_fix="Ensure parser provides file path information"
                ))
            elif not self._is_reasonable_file_path(file_path):
                issues.append(ValidationIssue(
                    issue_type=FlowValidationIssueType.INCOMPLETE_TRACE,
                    severity=ValidationSeverity.LOW,
                    description=f"File path looks suspicious: {file_path}",
                    affected_steps=[step.step_order],
                    suggested_fix="Verify file path is correct"
                ))
        
        return issues
    
    def _is_reasonable_file_path(self, file_path: str) -> bool:
        """Check if a file path looks reasonable"""
        # Basic checks for reasonable file paths
        if len(file_path) < 3:
            return False
        
        # Should have some kind of file extension or be a recognized config file
        has_extension = '.' in file_path
        is_config_file = any(config in file_path.lower() for config in ['xml', 'properties', 'config'])
        
        return has_extension or is_config_file
    
    def _validate_business_logic(self, flow_steps: List[FlowStep]) -> List[ValidationIssue]:
        """Validate that business logic descriptions are meaningful"""
        issues = []
        
        for step in flow_steps:
            business_logic = step.business_logic
            
            if not business_logic or business_logic.strip() == '':
                issues.append(ValidationIssue(
                    issue_type=FlowValidationIssueType.INCOMPLETE_TRACE,
                    severity=ValidationSeverity.LOW,
                    description="Step missing business logic description",
                    affected_steps=[step.step_order],
                    suggested_fix="Add business logic description for better traceability"
                ))
            elif len(business_logic.strip()) < 10:
                issues.append(ValidationIssue(
                    issue_type=FlowValidationIssueType.INCOMPLETE_TRACE,
                    severity=ValidationSeverity.LOW,
                    description="Business logic description very brief",
                    affected_steps=[step.step_order],
                    suggested_fix="Consider expanding business logic description"
                ))
        
        return issues
    
    def _validate_circular_dependencies(self, flow_steps: List[FlowStep]) -> List[ValidationIssue]:
        """Check for circular dependencies in the flow"""
        issues = []
        
        # Build dependency graph
        dependency_graph = {}
        for step in flow_steps:
            dependency_graph[step.component_name] = step.dependencies
        
        # Check for circular dependencies using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(component):
            visited.add(component)
            rec_stack.add(component)
            
            for dependency in dependency_graph.get(component, []):
                if dependency not in visited:
                    if has_cycle(dependency):
                        return True
                elif dependency in rec_stack:
                    return True
            
            rec_stack.remove(component)
            return False
        
        for component in dependency_graph:
            if component not in visited:
                if has_cycle(component):
                    issues.append(ValidationIssue(
                        issue_type=FlowValidationIssueType.CIRCULAR_REFERENCE,
                        severity=ValidationSeverity.HIGH,
                        description=f"Circular dependency detected involving {component}",
                        affected_steps=[step.step_order for step in flow_steps 
                                      if step.component_name == component],
                        suggested_fix="Review and resolve circular dependencies"
                    ))
                    break  # Stop after finding first cycle
        
        return issues
    
    def _validate_duplicate_steps(self, flow_steps: List[FlowStep]) -> List[ValidationIssue]:
        """Check for duplicate steps in the flow"""
        issues = []
        
        seen_components = {}
        for step in flow_steps:
            key = (step.technology, step.component_name, step.file_path)
            
            if key in seen_components:
                issues.append(ValidationIssue(
                    issue_type=FlowValidationIssueType.DUPLICATE_STEP,
                    severity=ValidationSeverity.MEDIUM,
                    description=f"Duplicate step detected: {step.component_name}",
                    affected_steps=[seen_components[key], step.step_order],
                    suggested_fix="Remove duplicate step or differentiate if legitimately different"
                ))
            else:
                seen_components[key] = step.step_order
        
        return issues
    
    def _calculate_completeness_score(self, flow_steps: List[FlowStep], issues: List[ValidationIssue]) -> float:
        """Calculate completeness score based on flow steps and issues"""
        if not flow_steps:
            return 0.0
        
        base_score = 1.0
        
        # Deduct points for missing information
        for step in flow_steps:
            if not step.file_path:
                base_score -= 0.1
            if not step.business_logic:
                base_score -= 0.05
            if not step.dependencies:
                base_score -= 0.02
        
        # Deduct points for validation issues
        for issue in issues:
            if issue.issue_type == FlowValidationIssueType.MISSING_LINK:
                base_score -= 0.2
            elif issue.issue_type == FlowValidationIssueType.INCOMPLETE_TRACE:
                base_score -= 0.15
            elif issue.issue_type == FlowValidationIssueType.TECHNOLOGY_GAP:
                base_score -= 0.1
        
        return max(0.0, min(1.0, base_score))
    
    def _calculate_overall_confidence(self, trace: BusinessRuleTrace, issues: List[ValidationIssue]) -> float:
        """Calculate overall confidence score"""
        # Start with the trace's extraction confidence
        base_confidence = trace.extraction_confidence
        
        # Apply confidence impacts from issues
        for issue in issues:
            base_confidence += issue.confidence_impact
        
        # Factor in completeness and number of steps
        step_factor = min(1.0, len(trace.flow_steps) / 5.0)  # Prefer flows with multiple steps
        base_confidence *= (0.8 + 0.2 * step_factor)
        
        return max(0.0, min(1.0, base_confidence))
    
    def _generate_recommendations(self, issues: List[ValidationIssue], trace: BusinessRuleTrace) -> List[str]:
        """Generate recommendations based on validation issues"""
        recommendations = []
        
        critical_issues = [issue for issue in issues if issue.severity == ValidationSeverity.CRITICAL]
        high_issues = [issue for issue in issues if issue.severity == ValidationSeverity.HIGH]
        
        if critical_issues:
            recommendations.append("Address critical validation issues before using this flow trace")
        
        if high_issues:
            recommendations.append("Review high-severity issues to improve flow accuracy")
        
        if len(trace.flow_steps) < 3:
            recommendations.append("Consider expanding trace to include more flow steps for completeness")
        
        if trace.extraction_confidence < 0.7:
            recommendations.append("Low extraction confidence - consider manual review and enhancement")
        
        # Technology-specific recommendations
        technologies = set(step.technology for step in trace.flow_steps)
        if 'Database' not in [tech for tech in technologies]:
            recommendations.append("Consider tracing to data layer for complete business rule understanding")
        
        if not recommendations:
            recommendations.append("Flow trace appears complete and accurate")
        
        return recommendations
    
    async def validate_multiple_flows(self, traces: List[BusinessRuleTrace]) -> Dict[str, FlowValidationResult]:
        """Validate multiple flow traces"""
        results = {}
        
        for trace in traces:
            try:
                result = await self.validate_flow(trace)
                results[trace.trace_id] = result
            except Exception as e:
                logger.error(f"Error validating trace {trace.rule_name}: {str(e)}")
                results[trace.trace_id] = FlowValidationResult(
                    is_valid=False,
                    overall_confidence=0.0,
                    completeness_score=0.0,
                    issues=[ValidationIssue(
                        issue_type=FlowValidationIssueType.INCOMPLETE_TRACE,
                        severity=ValidationSeverity.CRITICAL,
                        description=f"Validation failed: {str(e)}",
                        affected_steps=[]
                    )],
                    recommendations=["Validation failed - review trace manually"],
                    validation_timestamp=datetime.utcnow()
                )
        
        return results
    
    def get_validation_statistics(self, results: Dict[str, FlowValidationResult]) -> Dict:
        """Get statistics about validation results"""
        if not results:
            return {"total_validated": 0}
        
        valid_count = sum(1 for result in results.values() if result.is_valid)
        avg_confidence = sum(result.overall_confidence for result in results.values()) / len(results)
        avg_completeness = sum(result.completeness_score for result in results.values()) / len(results)
        
        issue_counts = {}
        for result in results.values():
            for issue in result.issues:
                issue_type = issue.issue_type.value
                issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
        
        return {
            "total_validated": len(results),
            "valid_flows": valid_count,
            "invalid_flows": len(results) - valid_count,
            "average_confidence": avg_confidence,
            "average_completeness": avg_completeness,
            "common_issues": dict(sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5])
        }

# Global service instance
_flow_validator = None

def get_flow_validator() -> FlowValidator:
    """Get flow validator service instance"""
    global _flow_validator
    if _flow_validator is None:
        _flow_validator = FlowValidator()
    return _flow_validator