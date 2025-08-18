"""
Parser Orchestrator Service

This service manages parser execution order, handles parser dependencies,
and aggregates results into unified format.

Part of Week 4, Task 4.2 implementation in the enterprise transformation plan.
"""

from typing import List, Dict, Optional, Set, Any, Tuple
import logging
import asyncio
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import os

from app.parsers.struts_parser import StrutsParser
from app.parsers.struts2_parser import Struts2Parser
from app.parsers.jsp_el_tracer import JSPELTracer
from app.parsers.struts_action_tracer import StrutsActionTracer
from app.parsers.corba_parser import CorbaParser
from app.parsers.python_parser import PythonParser

logger = logging.getLogger(__name__)


class ParserType(Enum):
    """Enumeration of supported parser types"""
    JSP = "jsp"
    STRUTS = "struts"
    STRUTS2 = "struts2"
    STRUTS_ACTION = "struts_action"
    CORBA = "corba"
    JAVA = "java"
    PYTHON = "python"


class ParserPriority(Enum):
    """Parser execution priority levels"""
    HIGH = 1
    MEDIUM = 2
    LOW = 3


@dataclass
class ParserConfig:
    """Configuration for a parser"""
    parser_type: ParserType
    parser_class: type
    file_patterns: List[str]
    dependencies: List[ParserType]
    priority: ParserPriority
    timeout_seconds: int = 300
    max_retries: int = 3


@dataclass
class ParserResult:
    """Result from a parser execution"""
    parser_type: ParserType
    file_path: str
    success: bool
    data: Dict[str, Any]
    error_message: Optional[str] = None
    execution_time: float = 0.0
    confidence_score: float = 0.0


class ParserExecutionPlan:
    """Represents an execution plan for parsing a repository"""
    
    def __init__(self):
        self.phases: List[List[ParserConfig]] = []
        self.total_parsers: int = 0
        
    def add_phase(self, parsers: List[ParserConfig]):
        """Add a phase of parsers that can run in parallel"""
        self.phases.append(parsers)
        self.total_parsers += len(parsers)


class ParserOrchestrator:
    """
    Orchestrates multiple parsers to analyze codebases systematically.
    
    This service manages parser execution order, handles dependencies,
    and aggregates results into a unified format for the UnifiedFlowTracer.
    """
    
    def __init__(self):
        self.parser_configs = self._initialize_parser_configs()
        self.parser_instances = self._initialize_parser_instances()
        self.execution_history: List[Dict] = []
        
    def _initialize_parser_configs(self) -> Dict[ParserType, ParserConfig]:
        """Initialize parser configurations with dependencies and priorities"""
        return {
            ParserType.JSP: ParserConfig(
                parser_type=ParserType.JSP,
                parser_class=JSPELTracer,
                file_patterns=["*.jsp", "*.jspx"],
                dependencies=[],  # JSP can run independently
                priority=ParserPriority.HIGH
            ),
            ParserType.STRUTS: ParserConfig(
                parser_type=ParserType.STRUTS,
                parser_class=StrutsParser,
                file_patterns=["struts-config.xml", "validation.xml"],
                dependencies=[],  # Struts config can run independently
                priority=ParserPriority.HIGH
            ),
            ParserType.STRUTS2: ParserConfig(
                parser_type=ParserType.STRUTS2,
                parser_class=Struts2Parser,
                file_patterns=["struts.xml"],
                dependencies=[],  # Struts2 config can run independently
                priority=ParserPriority.HIGH
            ),
            ParserType.STRUTS_ACTION: ParserConfig(
                parser_type=ParserType.STRUTS_ACTION,
                parser_class=StrutsActionTracer,
                file_patterns=["*Action.java"],
                dependencies=[ParserType.STRUTS, ParserType.STRUTS2],  # Needs Struts config first
                priority=ParserPriority.MEDIUM
            ),
            ParserType.CORBA: ParserConfig(
                parser_type=ParserType.CORBA,
                parser_class=CorbaParser,
                file_patterns=["*.idl"],
                dependencies=[],  # CORBA IDL can run independently
                priority=ParserPriority.HIGH
            ),
            ParserType.PYTHON: ParserConfig(
                parser_type=ParserType.PYTHON,
                parser_class=PythonParser,
                file_patterns=["*.py"],
                dependencies=[],  # Python can run independently
                priority=ParserPriority.LOW
            )
        }
    
    def _initialize_parser_instances(self) -> Dict[ParserType, Any]:
        """Initialize parser instances"""
        instances = {}
        for parser_type, config in self.parser_configs.items():
            try:
                instances[parser_type] = config.parser_class()
                logger.debug(f"Initialized parser: {parser_type.value}")
            except Exception as e:
                logger.error(f"Failed to initialize parser {parser_type.value}: {str(e)}")
        return instances
    
    async def analyze_repository(self, repository_path: str) -> Dict[str, List[ParserResult]]:
        """
        Analyze a complete repository using all applicable parsers.
        
        Args:
            repository_path: Path to the repository to analyze
            
        Returns:
            Dictionary mapping file paths to their parser results
        """
        logger.info(f"Starting repository analysis: {repository_path}")
        
        # Discover files to parse
        file_discovery = await self._discover_files(repository_path)
        
        if not file_discovery:
            logger.warning(f"No parseable files found in repository: {repository_path}")
            return {}
        
        # Create execution plan
        execution_plan = self._create_execution_plan(file_discovery)
        
        # Execute parsing in phases
        all_results = {}
        
        for phase_idx, phase_parsers in enumerate(execution_plan.phases):
            logger.info(f"Executing phase {phase_idx + 1}/{len(execution_plan.phases)} "
                       f"with {len(phase_parsers)} parsers")
            
            phase_results = await self._execute_phase(repository_path, phase_parsers, file_discovery)
            
            # Merge phase results
            for file_path, results in phase_results.items():
                if file_path not in all_results:
                    all_results[file_path] = []
                all_results[file_path].extend(results)
        
        # Store execution history
        self._record_execution_history(repository_path, execution_plan, all_results)
        
        logger.info(f"Completed repository analysis: {len(all_results)} files processed")
        return all_results
    
    async def _discover_files(self, repository_path: str) -> Dict[ParserType, List[str]]:
        """Discover files that can be parsed by each parser type"""
        file_discovery = {}
        
        for parser_type, config in self.parser_configs.items():
            matching_files = []
            
            for pattern in config.file_patterns:
                # Simple file pattern matching
                found_files = await self._find_files_by_pattern(repository_path, pattern)
                matching_files.extend(found_files)
            
            if matching_files:
                file_discovery[parser_type] = matching_files
                logger.debug(f"Found {len(matching_files)} files for {parser_type.value}")
        
        return file_discovery
    
    async def _find_files_by_pattern(self, repository_path: str, pattern: str) -> List[str]:
        """Find files matching a pattern in the repository"""
        import glob
        import fnmatch
        
        matching_files = []
        
        try:
            # Handle exact filenames (like struts.xml)
            if '.' in pattern and '*' not in pattern:
                for root, dirs, files in os.walk(repository_path):
                    if pattern in files:
                        matching_files.append(os.path.join(root, pattern))
            else:
                # Handle wildcard patterns
                for root, dirs, files in os.walk(repository_path):
                    for file in files:
                        if fnmatch.fnmatch(file, pattern):
                            matching_files.append(os.path.join(root, file))
            
        except Exception as e:
            logger.error(f"Error finding files with pattern {pattern}: {str(e)}")
        
        return matching_files
    
    def _create_execution_plan(self, file_discovery: Dict[ParserType, List[str]]) -> ParserExecutionPlan:
        """Create an execution plan based on parser dependencies and priorities"""
        plan = ParserExecutionPlan()
        
        # Get available parser types that have files to process
        available_parsers = set(file_discovery.keys())
        processed_parsers = set()
        
        while available_parsers - processed_parsers:
            # Find parsers whose dependencies have been satisfied
            ready_parsers = []
            
            for parser_type in available_parsers - processed_parsers:
                config = self.parser_configs[parser_type]
                dependencies_satisfied = all(
                    dep in processed_parsers or dep not in available_parsers
                    for dep in config.dependencies
                )
                
                if dependencies_satisfied:
                    ready_parsers.append(config)
            
            if not ready_parsers:
                # Handle circular dependencies by taking remaining parsers
                logger.warning("Possible circular dependencies detected, forcing remaining parsers")
                remaining_types = available_parsers - processed_parsers
                ready_parsers = [self.parser_configs[pt] for pt in remaining_types]
            
            # Sort by priority
            ready_parsers.sort(key=lambda x: x.priority.value)
            
            # Add to execution plan
            plan.add_phase(ready_parsers)
            
            # Mark as processed
            for parser_config in ready_parsers:
                processed_parsers.add(parser_config.parser_type)
        
        logger.info(f"Created execution plan with {len(plan.phases)} phases, "
                   f"{plan.total_parsers} parsers total")
        return plan
    
    async def _execute_phase(
        self, 
        repository_path: str, 
        phase_parsers: List[ParserConfig],
        file_discovery: Dict[ParserType, List[str]]
    ) -> Dict[str, List[ParserResult]]:
        """Execute a phase of parsers in parallel"""
        
        tasks = []
        for parser_config in phase_parsers:
            files_to_parse = file_discovery.get(parser_config.parser_type, [])
            
            for file_path in files_to_parse:
                task = self._execute_single_parser(
                    parser_config, repository_path, file_path
                )
                tasks.append(task)
        
        # Execute all tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Organize results by file path
        organized_results = {}
        for result in results:
            if isinstance(result, ParserResult) and result.success:
                file_path = result.file_path
                if file_path not in organized_results:
                    organized_results[file_path] = []
                organized_results[file_path].append(result)
            elif isinstance(result, Exception):
                logger.error(f"Parser execution failed: {str(result)}")
        
        return organized_results
    
    async def _execute_single_parser(
        self, 
        parser_config: ParserConfig, 
        repository_path: str, 
        file_path: str
    ) -> ParserResult:
        """Execute a single parser on a single file"""
        start_time = datetime.utcnow()
        
        try:
            parser_instance = self.parser_instances.get(parser_config.parser_type)
            if not parser_instance:
                raise Exception(f"Parser instance not found: {parser_config.parser_type.value}")
            
            # Execute parser with timeout
            result_data = await asyncio.wait_for(
                self._call_parser_method(parser_instance, repository_path, file_path),
                timeout=parser_config.timeout_seconds
            )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return ParserResult(
                parser_type=parser_config.parser_type,
                file_path=file_path,
                success=True,
                data=result_data,
                execution_time=execution_time,
                confidence_score=result_data.get('confidence_score', 0.5)
            )
            
        except asyncio.TimeoutError:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Parser timeout: {parser_config.parser_type.value} on {file_path}")
            return ParserResult(
                parser_type=parser_config.parser_type,
                file_path=file_path,
                success=False,
                data={},
                error_message="Parser execution timeout",
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Parser error: {parser_config.parser_type.value} on {file_path}: {str(e)}")
            return ParserResult(
                parser_type=parser_config.parser_type,
                file_path=file_path,
                success=False,
                data={},
                error_message=str(e),
                execution_time=execution_time
            )
    
    async def _call_parser_method(self, parser_instance: Any, repository_path: str, file_path: str) -> Dict:
        """Call the appropriate method on a parser instance"""
        # Try common parser method names
        if hasattr(parser_instance, 'analyze_file'):
            result = parser_instance.analyze_file(repository_path, file_path)
        elif hasattr(parser_instance, 'parse_file'):
            result = parser_instance.parse_file(repository_path, file_path)
        elif hasattr(parser_instance, 'analyze'):
            result = parser_instance.analyze(file_path)
        elif hasattr(parser_instance, 'parse'):
            result = parser_instance.parse(file_path)
        else:
            raise Exception(f"Parser instance has no recognized parsing method")
        
        # Handle both sync and async results
        if asyncio.iscoroutine(result):
            return await result
        else:
            return result
    
    def _record_execution_history(
        self, 
        repository_path: str, 
        execution_plan: ParserExecutionPlan, 
        results: Dict[str, List[ParserResult]]
    ):
        """Record execution history for analysis and debugging"""
        history_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "repository_path": repository_path,
            "phases_executed": len(execution_plan.phases),
            "total_parsers": execution_plan.total_parsers,
            "files_processed": len(results),
            "success_rate": self._calculate_success_rate(results),
            "average_execution_time": self._calculate_average_execution_time(results)
        }
        
        self.execution_history.append(history_entry)
        
        # Keep only last 100 executions
        if len(self.execution_history) > 100:
            self.execution_history = self.execution_history[-100:]
    
    def _calculate_success_rate(self, results: Dict[str, List[ParserResult]]) -> float:
        """Calculate the overall success rate of parsing"""
        total_attempts = sum(len(file_results) for file_results in results.values())
        if total_attempts == 0:
            return 0.0
        
        successful_attempts = sum(
            sum(1 for result in file_results if result.success)
            for file_results in results.values()
        )
        
        return successful_attempts / total_attempts
    
    def _calculate_average_execution_time(self, results: Dict[str, List[ParserResult]]) -> float:
        """Calculate average execution time across all parsers"""
        all_times = [
            result.execution_time 
            for file_results in results.values()
            for result in file_results
        ]
        
        return sum(all_times) / len(all_times) if all_times else 0.0
    
    async def analyze_specific_files(
        self, 
        repository_path: str, 
        file_paths: List[str]
    ) -> Dict[str, List[ParserResult]]:
        """Analyze specific files rather than a whole repository"""
        logger.info(f"Analyzing {len(file_paths)} specific files")
        
        # Group files by parser type
        files_by_parser = {}
        for file_path in file_paths:
            for parser_type, config in self.parser_configs.items():
                for pattern in config.file_patterns:
                    if self._file_matches_pattern(file_path, pattern):
                        if parser_type not in files_by_parser:
                            files_by_parser[parser_type] = []
                        files_by_parser[parser_type].append(file_path)
                        break
        
        # Create execution plan for specific files
        execution_plan = self._create_execution_plan(files_by_parser)
        
        # Execute parsing
        all_results = {}
        for phase_parsers in execution_plan.phases:
            phase_results = await self._execute_phase(repository_path, phase_parsers, files_by_parser)
            
            for file_path, results in phase_results.items():
                if file_path not in all_results:
                    all_results[file_path] = []
                all_results[file_path].extend(results)
        
        return all_results
    
    def _file_matches_pattern(self, file_path: str, pattern: str) -> bool:
        """Check if a file matches a pattern"""
        import fnmatch
        filename = os.path.basename(file_path)
        return fnmatch.fnmatch(filename, pattern)
    
    def get_parser_statistics(self) -> Dict:
        """Get statistics about parser orchestration"""
        if not self.execution_history:
            return {"total_executions": 0}
        
        recent_executions = self.execution_history[-10:]  # Last 10 executions
        
        return {
            "total_executions": len(self.execution_history),
            "average_success_rate": sum(ex["success_rate"] for ex in recent_executions) / len(recent_executions),
            "average_execution_time": sum(ex["average_execution_time"] for ex in recent_executions) / len(recent_executions),
            "total_files_processed": sum(ex["files_processed"] for ex in recent_executions),
            "configured_parsers": list(self.parser_configs.keys())
        }

# Global service instance
_parser_orchestrator = None

def get_parser_orchestrator() -> ParserOrchestrator:
    """Get parser orchestrator service instance"""
    global _parser_orchestrator
    if _parser_orchestrator is None:
        _parser_orchestrator = ParserOrchestrator()
    return _parser_orchestrator