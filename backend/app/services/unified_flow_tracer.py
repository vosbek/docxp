"""
Unified Flow Tracer Service

This service orchestrates existing parsers to build complete end-to-end business rule traces
across different technology stacks (JSP, Struts, Java, CORBA, etc.)

Part of Week 4 implementation in the enterprise transformation plan.
"""

from typing import List, Dict, Optional, Set, Tuple
import logging
import asyncio
from datetime import datetime
import uuid

from app.core.database import AsyncSessionLocal
from app.models.business_rule_trace import BusinessRuleTrace, FlowStep
from app.models.graph_entities import (
    GraphNodeType, GraphRelationshipType, 
    CodeEntityProperties, BusinessRuleProperties, TechnologyComponentProperties
)
from app.services.knowledge_graph_service import KnowledgeGraphService

# Import existing parsers
from app.parsers.struts_parser import StrutsParser
from app.parsers.struts2_parser import Struts2Parser
from app.parsers.jsp_el_tracer import JSPELTracer
from app.parsers.struts_action_tracer import StrutsActionTracer
from app.parsers.corba_parser import CorbaParser
from app.parsers.python_parser import PythonParser

logger = logging.getLogger(__name__)


class FlowChain:
    """Represents a chain of flow steps in a business rule trace"""
    
    def __init__(self):
        self.steps: List[FlowStep] = []
        self.confidence_score: float = 0.0
        self.complexity_score: float = 0.0
        self.technologies: Set[str] = set()
    
    def add_step(self, step: FlowStep):
        """Add a step to the flow chain"""
        self.steps.append(step)
        self.technologies.add(step.technology)
        self._recalculate_scores()
    
    def _recalculate_scores(self):
        """Recalculate confidence and complexity scores"""
        if not self.steps:
            return
        
        # Average confidence across all steps
        self.confidence_score = sum(step.confidence_score for step in self.steps) / len(self.steps)
        
        # Complexity based on number of steps and technologies
        self.complexity_score = len(self.steps) * 0.3 + len(self.technologies) * 0.7


class UnifiedFlowTracer:
    """
    Orchestrates multiple parsers to build complete flow chains for business rules.
    
    This service represents the core of Week 4's flow tracing infrastructure,
    connecting different technology layers into coherent business rule traces.
    """
    
    def __init__(self):
        self.knowledge_graph = KnowledgeGraphService()
        self.parsers = self._initialize_parsers()
        self.flow_chains: Dict[str, FlowChain] = {}
        
    def _initialize_parsers(self) -> Dict[str, object]:
        """Initialize all available parsers"""
        return {
            'struts': StrutsParser(),
            'struts2': Struts2Parser(),
            'jsp': JSPELTracer(),
            'struts_action': StrutsActionTracer(),
            'corba': CorbaParser(),
            'python': PythonParser()
        }
    
    async def trace_business_rule(
        self, 
        repository_path: str, 
        entry_point: str,
        rule_name: str,
        business_domain: str = None
    ) -> BusinessRuleTrace:
        """
        Trace a complete business rule flow from entry point through all technology layers.
        
        Args:
            repository_path: Path to the repository to analyze
            entry_point: Starting point (e.g., JSP file, REST endpoint)
            rule_name: Human-readable name for the business rule
            business_domain: Business domain classification
        
        Returns:
            Complete BusinessRuleTrace with all flow steps
        """
        logger.info(f"Starting business rule trace for: {rule_name}")
        
        trace_id = str(uuid.uuid4())
        flow_chain = FlowChain()
        
        try:
            # Determine entry point technology and start tracing
            entry_tech = self._detect_entry_technology(entry_point)
            
            if entry_tech == 'jsp':
                await self._trace_from_jsp(repository_path, entry_point, flow_chain)
            elif entry_tech == 'struts':
                await self._trace_from_struts(repository_path, entry_point, flow_chain)
            elif entry_tech == 'corba':
                await self._trace_from_corba(repository_path, entry_point, flow_chain)
            else:
                logger.warning(f"Unknown entry point technology: {entry_tech}")
                return None
            
            # Create the BusinessRuleTrace
            business_rule_trace = BusinessRuleTrace(
                trace_id=trace_id,
                rule_name=rule_name,
                technology_stack=list(flow_chain.technologies),
                flow_steps=flow_chain.steps,
                business_domain=business_domain or "Unknown",
                complexity_score=flow_chain.complexity_score,
                extraction_confidence=flow_chain.confidence_score,
                created_at=datetime.utcnow()
            )
            
            # Store in knowledge graph
            await self._store_in_knowledge_graph(business_rule_trace)
            
            # Persist to database
            await self._persist_trace(business_rule_trace)
            
            logger.info(f"Completed business rule trace: {rule_name} with {len(flow_chain.steps)} steps")
            return business_rule_trace
            
        except Exception as e:
            logger.error(f"Error tracing business rule {rule_name}: {str(e)}")
            raise
    
    def _detect_entry_technology(self, entry_point: str) -> str:
        """Detect the technology type based on file extension or path"""
        if entry_point.endswith('.jsp'):
            return 'jsp'
        elif entry_point.endswith('.java') and 'action' in entry_point.lower():
            return 'struts'
        elif entry_point.endswith('.idl'):
            return 'corba'
        elif 'struts-config.xml' in entry_point or 'struts.xml' in entry_point:
            return 'struts'
        else:
            return 'unknown'
    
    async def _trace_from_jsp(self, repository_path: str, jsp_file: str, flow_chain: FlowChain):
        """Trace flow starting from a JSP file"""
        logger.debug(f"Tracing from JSP: {jsp_file}")
        
        # Use JSP EL Tracer to analyze the JSP file
        jsp_analysis = await self._run_parser('jsp', repository_path, jsp_file)
        
        if jsp_analysis:
            # Create JSP flow step
            jsp_step = FlowStep(
                step_order=len(flow_chain.steps) + 1,
                technology="JSP",
                component_name=jsp_file,
                file_path=jsp_file,
                line_range=(1, jsp_analysis.get('line_count', 0)),
                business_logic=jsp_analysis.get('description', ''),
                dependencies=jsp_analysis.get('dependencies', []),
                confidence_score=0.8
            )
            flow_chain.add_step(jsp_step)
            
            # Look for Struts actions referenced in the JSP
            struts_actions = jsp_analysis.get('struts_actions', [])
            for action in struts_actions:
                await self._trace_struts_action(repository_path, action, flow_chain)
    
    async def _trace_from_struts(self, repository_path: str, struts_file: str, flow_chain: FlowChain):
        """Trace flow starting from a Struts configuration"""
        logger.debug(f"Tracing from Struts: {struts_file}")
        
        # Determine Struts version and use appropriate parser
        parser_key = 'struts2' if 'struts.xml' in struts_file else 'struts'
        struts_analysis = await self._run_parser(parser_key, repository_path, struts_file)
        
        if struts_analysis:
            # Create Struts flow step
            struts_step = FlowStep(
                step_order=len(flow_chain.steps) + 1,
                technology="Struts",
                component_name=struts_file,
                file_path=struts_file,
                line_range=(1, struts_analysis.get('line_count', 0)),
                business_logic=struts_analysis.get('description', ''),
                dependencies=struts_analysis.get('dependencies', []),
                confidence_score=0.9
            )
            flow_chain.add_step(struts_step)
            
            # Trace to Java action classes
            action_classes = struts_analysis.get('action_classes', [])
            for action_class in action_classes:
                await self._trace_java_action(repository_path, action_class, flow_chain)
    
    async def _trace_from_corba(self, repository_path: str, corba_file: str, flow_chain: FlowChain):
        """Trace flow starting from a CORBA IDL file"""
        logger.debug(f"Tracing from CORBA: {corba_file}")
        
        corba_analysis = await self._run_parser('corba', repository_path, corba_file)
        
        if corba_analysis:
            # Create CORBA flow step
            corba_step = FlowStep(
                step_order=len(flow_chain.steps) + 1,
                technology="CORBA",
                component_name=corba_file,
                file_path=corba_file,
                line_range=(1, corba_analysis.get('line_count', 0)),
                business_logic=corba_analysis.get('description', ''),
                dependencies=corba_analysis.get('dependencies', []),
                confidence_score=0.7
            )
            flow_chain.add_step(corba_step)
            
            # Look for Java implementations
            implementations = corba_analysis.get('implementations', [])
            for impl in implementations:
                await self._trace_java_implementation(repository_path, impl, flow_chain)
    
    async def _trace_struts_action(self, repository_path: str, action_name: str, flow_chain: FlowChain):
        """Trace a specific Struts action"""
        action_tracer_analysis = await self._run_parser('struts_action', repository_path, action_name)
        
        if action_tracer_analysis:
            action_step = FlowStep(
                step_order=len(flow_chain.steps) + 1,
                technology="Struts Action",
                component_name=action_name,
                file_path=action_tracer_analysis.get('file_path', ''),
                line_range=action_tracer_analysis.get('line_range', (0, 0)),
                business_logic=action_tracer_analysis.get('business_logic', ''),
                dependencies=action_tracer_analysis.get('dependencies', []),
                confidence_score=0.8
            )
            flow_chain.add_step(action_step)
    
    async def _trace_java_action(self, repository_path: str, action_class: str, flow_chain: FlowChain):
        """Trace Java action class implementation"""
        # This would use a Java parser (to be implemented) or the Python parser as fallback
        java_analysis = await self._run_parser('python', repository_path, action_class)  # Placeholder
        
        if java_analysis:
            java_step = FlowStep(
                step_order=len(flow_chain.steps) + 1,
                technology="Java",
                component_name=action_class,
                file_path=java_analysis.get('file_path', ''),
                line_range=java_analysis.get('line_range', (0, 0)),
                business_logic=java_analysis.get('business_logic', ''),
                dependencies=java_analysis.get('dependencies', []),
                confidence_score=0.7
            )
            flow_chain.add_step(java_step)
    
    async def _trace_java_implementation(self, repository_path: str, impl_class: str, flow_chain: FlowChain):
        """Trace Java implementation class"""
        java_analysis = await self._run_parser('python', repository_path, impl_class)  # Placeholder
        
        if java_analysis:
            impl_step = FlowStep(
                step_order=len(flow_chain.steps) + 1,
                technology="Java Implementation",
                component_name=impl_class,
                file_path=java_analysis.get('file_path', ''),
                line_range=java_analysis.get('line_range', (0, 0)),
                business_logic=java_analysis.get('business_logic', ''),
                dependencies=java_analysis.get('dependencies', []),
                confidence_score=0.7
            )
            flow_chain.add_step(impl_step)
    
    async def _run_parser(self, parser_key: str, repository_path: str, target_file: str) -> Dict:
        """Run a specific parser and return results"""
        try:
            parser = self.parsers.get(parser_key)
            if not parser:
                logger.warning(f"Parser not found: {parser_key}")
                return None
            
            # Call parser's analyze method (assuming common interface)
            if hasattr(parser, 'analyze_file'):
                result = await parser.analyze_file(repository_path, target_file)
            elif hasattr(parser, 'parse_file'):
                result = await parser.parse_file(repository_path, target_file)
            else:
                logger.warning(f"Parser {parser_key} doesn't have expected methods")
                return None
            
            return result
            
        except Exception as e:
            logger.error(f"Error running parser {parser_key}: {str(e)}")
            return None
    
    async def _store_in_knowledge_graph(self, trace: BusinessRuleTrace):
        """Store the business rule trace in the knowledge graph"""
        try:
            # Create business rule node
            rule_node = await self.knowledge_graph.create_node(
                "BusinessRule",
                {
                    "rule_id": trace.trace_id,
                    "rule_name": trace.rule_name,
                    "business_domain": trace.business_domain,
                    "complexity_score": trace.complexity_score,
                    "confidence_score": trace.extraction_confidence,
                    "technology_stack": trace.technology_stack
                }
            )
            
            # Create nodes and relationships for each flow step
            previous_step_node = None
            for step in trace.flow_steps:
                step_node = await self.knowledge_graph.create_node(
                    "FlowStep",
                    {
                        "step_order": step.step_order,
                        "technology": step.technology,
                        "component_name": step.component_name,
                        "file_path": step.file_path,
                        "business_logic": step.business_logic
                    }
                )
                
                # Connect step to business rule
                await self.knowledge_graph.create_relationship(
                    rule_node["id"], step_node["id"], "CONTAINS"
                )
                
                # Connect steps in sequence
                if previous_step_node:
                    await self.knowledge_graph.create_relationship(
                        previous_step_node["id"], step_node["id"], "FLOWS_TO"
                    )
                
                previous_step_node = step_node
                
        except Exception as e:
            logger.error(f"Error storing trace in knowledge graph: {str(e)}")
    
    async def _persist_trace(self, trace: BusinessRuleTrace):
        """Persist the business rule trace to the database"""
        try:
            async with AsyncSessionLocal() as session:
                session.add(trace)
                await session.commit()
                logger.debug(f"Persisted business rule trace: {trace.rule_name}")
        except Exception as e:
            logger.error(f"Error persisting trace to database: {str(e)}")
    
    async def trace_multiple_rules(
        self, 
        repository_path: str, 
        entry_points: List[Tuple[str, str]]  # (entry_point, rule_name) pairs
    ) -> List[BusinessRuleTrace]:
        """Trace multiple business rules concurrently"""
        logger.info(f"Tracing {len(entry_points)} business rules")
        
        tasks = [
            self.trace_business_rule(repository_path, entry_point, rule_name)
            for entry_point, rule_name in entry_points
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful_traces = [
            result for result in results 
            if isinstance(result, BusinessRuleTrace)
        ]
        
        logger.info(f"Successfully traced {len(successful_traces)} out of {len(entry_points)} rules")
        return successful_traces
    
    def get_trace_statistics(self) -> Dict:
        """Get statistics about traced flows"""
        total_chains = len(self.flow_chains)
        if total_chains == 0:
            return {"total_chains": 0}
        
        avg_confidence = sum(chain.confidence_score for chain in self.flow_chains.values()) / total_chains
        avg_complexity = sum(chain.complexity_score for chain in self.flow_chains.values()) / total_chains
        
        technology_usage = {}
        for chain in self.flow_chains.values():
            for tech in chain.technologies:
                technology_usage[tech] = technology_usage.get(tech, 0) + 1
        
        return {
            "total_chains": total_chains,
            "average_confidence": avg_confidence,
            "average_complexity": avg_complexity,
            "technology_usage": technology_usage
        }

# Global service instance
_unified_flow_tracer = None

def get_unified_flow_tracer() -> UnifiedFlowTracer:
    """Get unified flow tracer service instance"""
    global _unified_flow_tracer
    if _unified_flow_tracer is None:
        _unified_flow_tracer = UnifiedFlowTracer()
    return _unified_flow_tracer