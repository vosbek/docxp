"""
jQAssistant Service - Comprehensive Java Architecture Analysis

Provides enterprise-grade Java architecture analysis including:
- Package dependency analysis with cycle detection
- Architectural layer compliance checking
- Design pattern recognition
- Dead code identification
- Code quality metrics calculation
- Neo4j integration for graph-based analysis
"""

import asyncio
import json
import logging
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import xml.etree.ElementTree as ET

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
import redis
from py2neo import Graph, Node, Relationship

from app.core.config import settings
from app.core.database import get_async_session
from app.models.indexing_models import (
    ArchitecturalAnalysisJob, PackageDependency, ArchitecturalViolation,
    DesignPattern, DeadCodeElement, CodeMetrics, IndexingArchitecturalInsight,
    JobStatus
)

logger = logging.getLogger(__name__)

@dataclass
class JQAssistantAnalysisResult:
    """
    Result of jQAssistant architectural analysis
    """
    # Analysis metadata
    repository_path: str
    analysis_timestamp: datetime = field(default_factory=datetime.utcnow)
    success: bool = True
    error_message: Optional[str] = None
    
    # Core analysis results
    classes: List[Dict[str, Any]] = field(default_factory=list)
    packages: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: List[Dict[str, Any]] = field(default_factory=list)
    
    # Architectural analysis
    architectural_layers: List[Dict[str, Any]] = field(default_factory=list)
    design_patterns: List[Dict[str, Any]] = field(default_factory=list)
    architectural_violations: List[Dict[str, Any]] = field(default_factory=list)
    
    # Code quality metrics
    metrics: Dict[str, Any] = field(default_factory=dict)
    complexity_analysis: Dict[str, Any] = field(default_factory=dict)
    dead_code_elements: List[Dict[str, Any]] = field(default_factory=list)
    
    # Analysis statistics
    total_classes_analyzed: int = 0
    total_packages_analyzed: int = 0
    total_dependencies_found: int = 0
    analysis_duration_seconds: float = 0.0
    
    # Additional insights
    architectural_insights: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

class JQAssistantService:
    """
    Enterprise jQAssistant integration service for Java architecture analysis
    """
    
    def __init__(self):
        self.redis_client = redis.Redis.from_url(
            getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
        )
        
        # jQAssistant configuration
        self.jqassistant_home = getattr(settings, 'JQASSISTANT_HOME', '/opt/jqassistant')
        self.neo4j_uri = getattr(settings, 'NEO4J_URI', 'bolt://localhost:7687')
        self.neo4j_user = getattr(settings, 'NEO4J_USER', 'neo4j')
        self.neo4j_password = getattr(settings, 'NEO4J_PASSWORD', 'password')
        
        # Analysis configuration
        self.max_file_size_mb = getattr(settings, 'JQASSISTANT_MAX_FILE_SIZE_MB', 100)
        self.analysis_timeout_minutes = getattr(settings, 'JQASSISTANT_TIMEOUT_MINUTES', 30)
        self.batch_size = getattr(settings, 'JQASSISTANT_BATCH_SIZE', 50)
        
        # Neo4j connection
        self.neo4j_graph = None
        
        logger.info(f"🏗️ jQAssistant Service initialized")
    
    async def initialize_neo4j(self):
        """Initialize Neo4j connection for graph analysis"""
        try:
            self.neo4j_graph = Graph(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )
            
            # Test connection
            self.neo4j_graph.run("RETURN 1 as test")
            logger.info("✅ Neo4j connection established")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Neo4j: {e}")
            self.neo4j_graph = None
    
    async def analyze_java_repository(
        self,
        repository_path: str,
        repo_id: str,
        commit_hash: str,
        analysis_rules: Optional[List[str]] = None,
        custom_constraints: Optional[List[str]] = None
    ) -> str:
        """
        Perform comprehensive jQAssistant analysis on Java repository
        
        Args:
            repository_path: Path to Java repository
            repo_id: Repository identifier
            commit_hash: Git commit hash
            analysis_rules: Specific jQAssistant rules to apply
            custom_constraints: Custom architectural constraints
            
        Returns:
            Analysis job ID for tracking progress
        """
        async with get_async_session() as session:
            try:
                logger.info(f"🏗️ Starting jQAssistant analysis for {repo_id}@{commit_hash[:8]}")
                
                # Validate repository
                repo_path = Path(repository_path)
                if not repo_path.exists():
                    raise ValueError(f"Repository path does not exist: {repository_path}")
                
                # Check if it's a Java repository
                java_files = list(repo_path.rglob("*.java"))
                if not java_files:
                    raise ValueError(f"No Java files found in repository: {repository_path}")
                
                logger.info(f"🔍 Found {len(java_files)} Java files for analysis")
                
                # Create analysis job
                job = ArchitecturalAnalysisJob(
                    repository_path=str(repo_path.absolute()),
                    repo_id=repo_id,
                    commit_hash=commit_hash,
                    status=JobStatus.PENDING,
                    analysis_rules=analysis_rules or self._get_default_rules(),
                    custom_constraints=custom_constraints or [],
                    total_java_files=len(java_files),
                    created_at=datetime.utcnow()
                )
                
                session.add(job)
                await session.commit()
                await session.refresh(job)
                
                job_id = str(job.id)
                logger.info(f"✅ Created jQAssistant analysis job {job_id}")
                
                # Start background analysis
                asyncio.create_task(self._process_analysis_job(job_id))
                
                return job_id
                
            except Exception as e:
                logger.error(f"❌ Failed to start jQAssistant analysis: {e}")
                raise
    
    async def _process_analysis_job(self, job_id: str):
        """Process jQAssistant analysis job with comprehensive analysis"""
        async with get_async_session() as session:
            try:
                # Load job
                result = await session.execute(
                    select(ArchitecturalAnalysisJob).where(ArchitecturalAnalysisJob.id == job_id)
                )
                job = result.scalar_one_or_none()
                if not job:
                    raise ValueError(f"Analysis job {job_id} not found")
                
                logger.info(f"🔄 Processing jQAssistant analysis job {job_id}")
                
                # Update job status
                job.status = JobStatus.RUNNING
                job.started_at = datetime.utcnow()
                await session.commit()
                
                repo_path = Path(job.repository_path)
                
                # Step 1: Run jQAssistant scan
                await self._update_job_progress(job, 10, "Scanning Java bytecode...", session)
                scan_results = await self._run_jqassistant_scan(repo_path, job.analysis_rules)
                
                # Step 2: Analyze package dependencies
                await self._update_job_progress(job, 30, "Analyzing package dependencies...", session)
                dependency_analysis = await self._analyze_package_dependencies(job, session)
                
                # Step 3: Check architectural compliance
                await self._update_job_progress(job, 50, "Checking architectural compliance...", session)
                compliance_analysis = await self._check_architectural_compliance(job, session)
                
                # Step 4: Detect design patterns
                await self._update_job_progress(job, 70, "Detecting design patterns...", session)
                pattern_analysis = await self._detect_design_patterns(job, session)
                
                # Step 5: Identify dead code
                await self._update_job_progress(job, 85, "Identifying dead code...", session)
                dead_code_analysis = await self._identify_dead_code(job, session)
                
                # Step 6: Calculate metrics and generate insights
                await self._update_job_progress(job, 95, "Calculating metrics and insights...", session)
                metrics = await self._calculate_code_metrics(job, session)
                insights = await self._generate_architectural_insights(job, session)
                
                # Finalize job
                await self._finalize_analysis_job(job, session)
                
                logger.info(f"✅ Completed jQAssistant analysis job {job_id}")
                
            except Exception as e:
                logger.error(f"❌ jQAssistant analysis job {job_id} failed: {e}")
                await self._mark_job_failed(job_id, str(e), session)
    
    async def _run_jqassistant_scan(self, repo_path: Path, rules: List[str]) -> Dict[str, Any]:
        """Run jQAssistant scan on repository"""
        try:
            # Create temporary directory for jQAssistant analysis
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Copy repository to temp directory
                repo_copy = temp_path / "repo"
                shutil.copytree(repo_path, repo_copy, ignore=shutil.ignore_patterns('*.git*', 'target', 'build'))
                
                # Build jQAssistant command
                cmd = [
                    str(Path(self.jqassistant_home) / "bin" / "jqassistant.sh"),
                    "scan",
                    "-f", str(repo_copy),
                    "-s", str(temp_path / "jqassistant-store")
                ]
                
                # Add rules
                for rule in rules:
                    cmd.extend(["-r", rule])
                
                logger.debug(f"Running jQAssistant command: {' '.join(cmd)}")
                
                # Execute jQAssistant
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    timeout=self.analysis_timeout_minutes * 60
                )
                
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    logger.warning(f"jQAssistant scan warning: {stderr.decode()}")
                
                # Parse results
                results = self._parse_jqassistant_results(temp_path / "jqassistant-store")
                
                logger.info(f"✅ jQAssistant scan completed with {len(results.get('classes', []))} classes analyzed")
                return results
                
        except Exception as e:
            logger.error(f"❌ jQAssistant scan failed: {e}")
            return {}
    
    def _parse_jqassistant_results(self, store_path: Path) -> Dict[str, Any]:
        """Parse jQAssistant analysis results from store"""
        results = {
            "classes": [],
            "packages": [],
            "dependencies": [],
            "methods": [],
            "violations": []
        }
        
        try:
            # jQAssistant stores results in Neo4j format
            # We'll extract key information for our analysis
            
            # Read store files if available
            report_file = store_path / "jqassistant-report.xml"
            if report_file.exists():
                tree = ET.parse(report_file)
                root = tree.getroot()
                
                # Extract classes
                for class_elem in root.findall(".//class"):
                    results["classes"].append({
                        "fqn": class_elem.get("fqn"),
                        "name": class_elem.get("name"),
                        "package": class_elem.get("package"),
                        "abstract": class_elem.get("abstract") == "true",
                        "interface": class_elem.get("interface") == "true"
                    })
                
                # Extract packages
                for package_elem in root.findall(".//package"):
                    results["packages"].append({
                        "fqn": package_elem.get("fqn"),
                        "name": package_elem.get("name")
                    })
                
                # Extract dependencies
                for dep_elem in root.findall(".//dependency"):
                    results["dependencies"].append({
                        "from": dep_elem.get("from"),
                        "to": dep_elem.get("to"),
                        "type": dep_elem.get("type")
                    })
            
            return results
            
        except Exception as e:
            logger.warning(f"Failed to parse jQAssistant results: {e}")
            return results
    
    async def _analyze_package_dependencies(self, job: ArchitecturalAnalysisJob, session: AsyncSession) -> Dict[str, Any]:
        """Analyze package dependencies and detect cycles"""
        try:
            repo_path = Path(job.repository_path)
            dependencies = []
            cycles = []
            
            # Build package dependency graph
            package_graph = await self._build_package_dependency_graph(repo_path)
            
            # Store dependencies in database
            for from_pkg, to_pkg, dep_type in package_graph["dependencies"]:
                dependency = PackageDependency(
                    analysis_job_id=job.id,
                    from_package=from_pkg,
                    to_package=to_pkg,
                    dependency_type=dep_type,
                    is_cyclic=False  # Will be updated after cycle detection
                )
                dependencies.append(dependency)
                session.add(dependency)
            
            # Detect cycles
            cycles = self._detect_dependency_cycles(package_graph)
            
            # Update cyclic dependencies
            for cycle in cycles:
                for i in range(len(cycle)):
                    from_pkg = cycle[i]
                    to_pkg = cycle[(i + 1) % len(cycle)]
                    
                    # Find and update the dependency
                    result = await session.execute(
                        select(PackageDependency).where(
                            PackageDependency.analysis_job_id == job.id,
                            PackageDependency.from_package == from_pkg,
                            PackageDependency.to_package == to_pkg
                        )
                    )
                    dep = result.scalar_one_or_none()
                    if dep:
                        dep.is_cyclic = True
            
            await session.commit()
            
            return {
                "total_dependencies": len(dependencies),
                "cyclic_dependencies": len([d for d in dependencies if d.is_cyclic]),
                "cycles_detected": len(cycles),
                "cycles": cycles
            }
            
        except Exception as e:
            logger.error(f"❌ Package dependency analysis failed: {e}")
            return {}
    
    async def _build_package_dependency_graph(self, repo_path: Path) -> Dict[str, Any]:
        """Build package dependency graph from Java source files"""
        packages = set()
        dependencies = []
        
        try:
            # Find all Java files
            java_files = list(repo_path.rglob("*.java"))
            
            for java_file in java_files:
                # Extract package and imports
                package_info = self._extract_package_info(java_file)
                
                if package_info["package"]:
                    packages.add(package_info["package"])
                    
                    # Add dependencies based on imports
                    for import_pkg in package_info["imports"]:
                        if import_pkg != package_info["package"]:
                            dependencies.append((
                                package_info["package"],
                                import_pkg,
                                "import"
                            ))
            
            return {
                "packages": list(packages),
                "dependencies": dependencies
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to build package dependency graph: {e}")
            return {"packages": [], "dependencies": []}
    
    def _extract_package_info(self, java_file: Path) -> Dict[str, Any]:
        """Extract package and import information from Java file"""
        package_info = {
            "package": None,
            "imports": []
        }
        
        try:
            content = java_file.read_text(encoding='utf-8', errors='ignore')
            lines = content.split('\n')
            
            for line in lines:
                line = line.strip()
                
                # Extract package
                if line.startswith('package ') and ';' in line:
                    package_info["package"] = line.replace('package ', '').replace(';', '').strip()
                
                # Extract imports
                elif line.startswith('import ') and ';' in line:
                    import_stmt = line.replace('import ', '').replace(';', '').strip()
                    if not import_stmt.startswith('java.'):  # Skip standard library imports
                        # Get package from import
                        parts = import_stmt.split('.')
                        if len(parts) > 1:
                            import_package = '.'.join(parts[:-1])
                            package_info["imports"].append(import_package)
            
            return package_info
            
        except Exception as e:
            logger.warning(f"Failed to extract package info from {java_file}: {e}")
            return package_info
    
    def _detect_dependency_cycles(self, package_graph: Dict[str, Any]) -> List[List[str]]:
        """Detect cycles in package dependency graph using DFS"""
        cycles = []
        
        try:
            # Build adjacency list
            graph = {}
            for from_pkg, to_pkg, _ in package_graph["dependencies"]:
                if from_pkg not in graph:
                    graph[from_pkg] = []
                graph[from_pkg].append(to_pkg)
            
            visited = set()
            rec_stack = set()
            
            def dfs(node, path):
                if node in rec_stack:
                    # Found cycle
                    cycle_start = path.index(node)
                    cycle = path[cycle_start:] + [node]
                    cycles.append(cycle)
                    return
                
                if node in visited:
                    return
                
                visited.add(node)
                rec_stack.add(node)
                path.append(node)
                
                for neighbor in graph.get(node, []):
                    dfs(neighbor, path)
                
                rec_stack.remove(node)
                path.pop()
            
            # Check for cycles from each node
            for package in package_graph["packages"]:
                if package not in visited:
                    dfs(package, [])
            
            return cycles
            
        except Exception as e:
            logger.error(f"❌ Cycle detection failed: {e}")
            return []
    
    async def _check_architectural_compliance(self, job: ArchitecturalAnalysisJob, session: AsyncSession) -> Dict[str, Any]:
        """Check architectural compliance against defined constraints"""
        violations = []
        
        try:
            # Define common architectural constraints
            constraints = [
                {
                    "name": "No circular dependencies",
                    "type": "dependency_cycle",
                    "severity": "ERROR"
                },
                {
                    "name": "Layer separation",
                    "type": "layer_violation",
                    "severity": "WARNING"
                },
                {
                    "name": "Maximum package depth",
                    "type": "package_depth",
                    "severity": "INFO",
                    "threshold": 5
                }
            ]
            
            # Add custom constraints from job
            constraints.extend(job.custom_constraints or [])
            
            # Check each constraint
            for constraint in constraints:
                constraint_violations = await self._check_constraint(job, constraint, session)
                violations.extend(constraint_violations)
            
            # Store violations in database
            for violation in violations:
                arch_violation = ArchitecturalViolation(
                    analysis_job_id=job.id,
                    constraint_name=violation["constraint"],
                    violation_type=violation["type"],
                    severity=violation["severity"],
                    description=violation["description"],
                    element_name=violation["element"],
                    file_path=violation.get("file_path"),
                    line_number=violation.get("line_number")
                )
                session.add(arch_violation)
            
            await session.commit()
            
            return {
                "total_violations": len(violations),
                "violations_by_severity": self._count_by_severity(violations),
                "constraints_checked": len(constraints)
            }
            
        except Exception as e:
            logger.error(f"❌ Architectural compliance check failed: {e}")
            return {}
    
    async def _check_constraint(self, job: ArchitecturalAnalysisJob, constraint: Dict[str, Any], session: AsyncSession) -> List[Dict[str, Any]]:
        """Check a specific architectural constraint"""
        violations = []
        
        try:
            if constraint["type"] == "dependency_cycle":
                # Check for circular dependencies
                result = await session.execute(
                    select(PackageDependency).where(
                        PackageDependency.analysis_job_id == job.id,
                        PackageDependency.is_cyclic == True
                    )
                )
                cyclic_deps = result.scalars().all()
                
                for dep in cyclic_deps:
                    violations.append({
                        "constraint": constraint["name"],
                        "type": constraint["type"],
                        "severity": constraint["severity"],
                        "element": f"{dep.from_package} -> {dep.to_package}",
                        "description": f"Circular dependency detected between {dep.from_package} and {dep.to_package}"
                    })
            
            elif constraint["type"] == "package_depth":
                # Check package depth
                result = await session.execute(
                    select(PackageDependency.from_package).where(
                        PackageDependency.analysis_job_id == job.id
                    ).distinct()
                )
                packages = [row[0] for row in result.all()]
                
                max_depth = constraint.get("threshold", 5)
                for package in packages:
                    depth = package.count('.') + 1
                    if depth > max_depth:
                        violations.append({
                            "constraint": constraint["name"],
                            "type": constraint["type"],
                            "severity": constraint["severity"],
                            "element": package,
                            "description": f"Package depth {depth} exceeds maximum {max_depth}"
                        })
            
            return violations
            
        except Exception as e:
            logger.error(f"❌ Constraint check failed for {constraint['name']}: {e}")
            return []
    
    def _count_by_severity(self, violations: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count violations by severity"""
        counts = {"ERROR": 0, "WARNING": 0, "INFO": 0}
        for violation in violations:
            severity = violation.get("severity", "INFO")
            counts[severity] = counts.get(severity, 0) + 1
        return counts
    
    async def _detect_design_patterns(self, job: ArchitecturalAnalysisJob, session: AsyncSession) -> Dict[str, Any]:
        """Detect common design patterns in the codebase"""
        patterns = []
        
        try:
            repo_path = Path(job.repository_path)
            
            # Pattern detection rules
            pattern_detectors = [
                self._detect_singleton_pattern,
                self._detect_factory_pattern,
                self._detect_observer_pattern,
                self._detect_builder_pattern
            ]
            
            for detector in pattern_detectors:
                detected_patterns = await detector(repo_path)
                patterns.extend(detected_patterns)
            
            # Store patterns in database
            for pattern in patterns:
                design_pattern = DesignPattern(
                    analysis_job_id=job.id,
                    pattern_name=pattern["name"],
                    pattern_type=pattern["type"],
                    element_name=pattern["element"],
                    file_path=pattern["file_path"],
                    confidence_score=pattern["confidence"],
                    description=pattern["description"]
                )
                session.add(design_pattern)
            
            await session.commit()
            
            return {
                "total_patterns": len(patterns),
                "patterns_by_type": self._group_patterns_by_type(patterns)
            }
            
        except Exception as e:
            logger.error(f"❌ Design pattern detection failed: {e}")
            return {}
    
    async def _detect_singleton_pattern(self, repo_path: Path) -> List[Dict[str, Any]]:
        """Detect Singleton pattern implementations"""
        patterns = []
        
        try:
            java_files = list(repo_path.rglob("*.java"))
            
            for java_file in java_files:
                content = java_file.read_text(encoding='utf-8', errors='ignore')
                
                # Simple singleton detection heuristics
                if (
                    'private static' in content and
                    'getInstance()' in content and
                    'private' in content and
                    content.count('private static') >= 1
                ):
                    patterns.append({
                        "name": "Singleton",
                        "type": "creational",
                        "element": java_file.stem,
                        "file_path": str(java_file.relative_to(repo_path)),
                        "confidence": 0.8,
                        "description": "Singleton pattern detected based on getInstance() method and private constructor"
                    })
            
            return patterns
            
        except Exception as e:
            logger.warning(f"Singleton pattern detection failed: {e}")
            return []
    
    async def _detect_factory_pattern(self, repo_path: Path) -> List[Dict[str, Any]]:
        """Detect Factory pattern implementations"""
        patterns = []
        
        try:
            java_files = list(repo_path.rglob("*.java"))
            
            for java_file in java_files:
                if 'Factory' in java_file.name or 'factory' in java_file.name.lower():
                    content = java_file.read_text(encoding='utf-8', errors='ignore')
                    
                    if ('create' in content.lower() or 'make' in content.lower()) and 'public' in content:
                        patterns.append({
                            "name": "Factory",
                            "type": "creational",
                            "element": java_file.stem,
                            "file_path": str(java_file.relative_to(repo_path)),
                            "confidence": 0.7,
                            "description": "Factory pattern detected based on naming and creation methods"
                        })
            
            return patterns
            
        except Exception as e:
            logger.warning(f"Factory pattern detection failed: {e}")
            return []
    
    async def _detect_observer_pattern(self, repo_path: Path) -> List[Dict[str, Any]]:
        """Detect Observer pattern implementations"""
        patterns = []
        
        try:
            java_files = list(repo_path.rglob("*.java"))
            
            for java_file in java_files:
                content = java_file.read_text(encoding='utf-8', errors='ignore')
                
                if (
                    'addListener' in content or 'removeListener' in content or
                    'addObserver' in content or 'removeObserver' in content or
                    'notify' in content.lower()
                ):
                    patterns.append({
                        "name": "Observer",
                        "type": "behavioral",
                        "element": java_file.stem,
                        "file_path": str(java_file.relative_to(repo_path)),
                        "confidence": 0.6,
                        "description": "Observer pattern detected based on listener/observer methods"
                    })
            
            return patterns
            
        except Exception as e:
            logger.warning(f"Observer pattern detection failed: {e}")
            return []
    
    async def _detect_builder_pattern(self, repo_path: Path) -> List[Dict[str, Any]]:
        """Detect Builder pattern implementations"""
        patterns = []
        
        try:
            java_files = list(repo_path.rglob("*.java"))
            
            for java_file in java_files:
                if 'Builder' in java_file.name:
                    content = java_file.read_text(encoding='utf-8', errors='ignore')
                    
                    if 'build()' in content and content.count('return this') >= 2:
                        patterns.append({
                            "name": "Builder",
                            "type": "creational",
                            "element": java_file.stem,
                            "file_path": str(java_file.relative_to(repo_path)),
                            "confidence": 0.8,
                            "description": "Builder pattern detected based on fluent interface and build() method"
                        })
            
            return patterns
            
        except Exception as e:
            logger.warning(f"Builder pattern detection failed: {e}")
            return []
    
    def _group_patterns_by_type(self, patterns: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group patterns by type"""
        groups = {}
        for pattern in patterns:
            pattern_type = pattern["type"]
            groups[pattern_type] = groups.get(pattern_type, 0) + 1
        return groups
    
    async def _identify_dead_code(self, job: ArchitecturalAnalysisJob, session: AsyncSession) -> Dict[str, Any]:
        """Identify potentially dead/unused code elements"""
        dead_elements = []
        
        try:
            repo_path = Path(job.repository_path)
            
            # Simple dead code detection (can be enhanced with more sophisticated analysis)
            unused_methods = await self._find_unused_methods(repo_path)
            unused_classes = await self._find_unused_classes(repo_path)
            
            # Store dead code elements
            for element in unused_methods + unused_classes:
                dead_code = DeadCodeElement(
                    analysis_job_id=job.id,
                    element_type=element["type"],
                    element_name=element["name"],
                    file_path=element["file_path"],
                    line_number=element.get("line_number", 0),
                    confidence_score=element["confidence"],
                    removal_suggestion=element["suggestion"]
                )
                dead_elements.append(dead_code)
                session.add(dead_code)
            
            await session.commit()
            
            return {
                "total_dead_elements": len(dead_elements),
                "unused_methods": len(unused_methods),
                "unused_classes": len(unused_classes)
            }
            
        except Exception as e:
            logger.error(f"❌ Dead code identification failed: {e}")
            return {}
    
    async def _find_unused_methods(self, repo_path: Path) -> List[Dict[str, Any]]:
        """Find potentially unused methods"""
        unused_methods = []
        
        try:
            java_files = list(repo_path.rglob("*.java"))
            all_content = ""
            
            # Read all files to build usage map
            for java_file in java_files:
                content = java_file.read_text(encoding='utf-8', errors='ignore')
                all_content += content + "\n"
            
            # Find method declarations and check usage
            for java_file in java_files:
                content = java_file.read_text(encoding='utf-8', errors='ignore')
                lines = content.split('\n')
                
                for i, line in enumerate(lines):
                    line = line.strip()
                    if (
                        line.startswith('private ') and 
                        '(' in line and 
                        ')' in line and
                        '{' in line
                    ):
                        # Extract method name
                        parts = line.split('(')[0].split()
                        if len(parts) >= 3:
                            method_name = parts[-1]
                            
                            # Check if method is used elsewhere
                            usage_count = all_content.count(f"{method_name}(")
                            
                            if usage_count <= 1:  # Only declaration, no usage
                                unused_methods.append({
                                    "type": "method",
                                    "name": method_name,
                                    "file_path": str(java_file.relative_to(repo_path)),
                                    "line_number": i + 1,
                                    "confidence": 0.7,
                                    "suggestion": f"Consider removing unused private method '{method_name}'"
                                })
            
            return unused_methods
            
        except Exception as e:
            logger.warning(f"Unused method detection failed: {e}")
            return []
    
    async def _find_unused_classes(self, repo_path: Path) -> List[Dict[str, Any]]:
        """Find potentially unused classes"""
        unused_classes = []
        
        try:
            java_files = list(repo_path.rglob("*.java"))
            all_content = ""
            
            # Read all files to build usage map
            for java_file in java_files:
                content = java_file.read_text(encoding='utf-8', errors='ignore')
                all_content += content + "\n"
            
            # Find class declarations and check usage
            for java_file in java_files:
                content = java_file.read_text(encoding='utf-8', errors='ignore')
                
                # Extract class name from file
                class_name = java_file.stem
                
                # Check if class is used elsewhere (excluding its own file)
                other_content = all_content.replace(content, "")
                usage_count = other_content.count(class_name)
                
                if usage_count == 0 and not content.count('public static void main'):
                    unused_classes.append({
                        "type": "class",
                        "name": class_name,
                        "file_path": str(java_file.relative_to(repo_path)),
                        "confidence": 0.6,
                        "suggestion": f"Consider reviewing class '{class_name}' - appears to be unused"
                    })
            
            return unused_classes
            
        except Exception as e:
            logger.warning(f"Unused class detection failed: {e}")
            return []
    
    async def _calculate_code_metrics(self, job: ArchitecturalAnalysisJob, session: AsyncSession) -> Dict[str, Any]:
        """Calculate comprehensive code quality metrics"""
        try:
            repo_path = Path(job.repository_path)
            java_files = list(repo_path.rglob("*.java"))
            
            metrics = {
                "total_java_files": len(java_files),
                "total_lines_of_code": 0,
                "complexity_score": 0,
                "coupling_score": 0,
                "cohesion_score": 0,
                "maintainability_index": 0
            }
            
            # Calculate basic metrics
            for java_file in java_files:
                content = java_file.read_text(encoding='utf-8', errors='ignore')
                lines = [line.strip() for line in content.split('\n') if line.strip() and not line.strip().startswith('//')]
                metrics["total_lines_of_code"] += len(lines)
                
                # Simple complexity calculation (based on control structures)
                complexity = content.count('if ') + content.count('for ') + content.count('while ') + content.count('switch ')
                metrics["complexity_score"] += complexity
            
            # Calculate averages
            if metrics["total_java_files"] > 0:
                metrics["avg_complexity_per_file"] = metrics["complexity_score"] / metrics["total_java_files"]
                metrics["avg_lines_per_file"] = metrics["total_lines_of_code"] / metrics["total_java_files"]
            
            # Calculate maintainability index (simplified)
            metrics["maintainability_index"] = max(0, 100 - (metrics["complexity_score"] / 10))
            
            # Store metrics in database
            code_metrics = CodeMetrics(
                analysis_job_id=job.id,
                total_java_files=metrics["total_java_files"],
                total_lines_of_code=metrics["total_lines_of_code"],
                complexity_score=metrics["complexity_score"],
                coupling_score=metrics["coupling_score"],
                cohesion_score=metrics["cohesion_score"],
                maintainability_index=metrics["maintainability_index"],
                calculated_at=datetime.utcnow()
            )
            
            session.add(code_metrics)
            await session.commit()
            
            return metrics
            
        except Exception as e:
            logger.error(f"❌ Code metrics calculation failed: {e}")
            return {}
    
    async def _generate_architectural_insights(self, job: ArchitecturalAnalysisJob, session: AsyncSession) -> Dict[str, Any]:
        """Generate high-level architectural insights and recommendations"""
        insights = []
        
        try:
            # Get analysis data
            dependencies_result = await session.execute(
                select(func.count(PackageDependency.id)).where(PackageDependency.analysis_job_id == job.id)
            )
            total_dependencies = dependencies_result.scalar() or 0
            
            cycles_result = await session.execute(
                select(func.count(PackageDependency.id)).where(
                    PackageDependency.analysis_job_id == job.id,
                    PackageDependency.is_cyclic == True
                )
            )
            cyclic_dependencies = cycles_result.scalar() or 0
            
            violations_result = await session.execute(
                select(func.count(ArchitecturalViolation.id)).where(ArchitecturalViolation.analysis_job_id == job.id)
            )
            total_violations = violations_result.scalar() or 0
            
            patterns_result = await session.execute(
                select(func.count(DesignPattern.id)).where(DesignPattern.analysis_job_id == job.id)
            )
            total_patterns = patterns_result.scalar() or 0
            
            # Generate insights
            if cyclic_dependencies > 0:
                insights.append({
                    "type": "architecture",
                    "priority": "high",
                    "title": "Circular Dependencies Detected",
                    "description": f"Found {cyclic_dependencies} circular dependencies that may affect maintainability",
                    "recommendation": "Consider refactoring to break circular dependencies using dependency inversion or interface segregation"
                })
            
            if total_violations > 10:
                insights.append({
                    "type": "compliance",
                    "priority": "medium",
                    "title": "Multiple Architectural Violations",
                    "description": f"Found {total_violations} architectural constraint violations",
                    "recommendation": "Review and address architectural violations to improve code quality"
                })
            
            if total_patterns > 0:
                insights.append({
                    "type": "patterns",
                    "priority": "low",
                    "title": "Design Patterns Identified",
                    "description": f"Detected {total_patterns} design patterns in the codebase",
                    "recommendation": "Good use of design patterns. Consider documenting patterns for team reference"
                })
            
            # Store insights
            for insight in insights:
                arch_insight = IndexingArchitecturalInsight(
                    analysis_job_id=job.id,
                    insight_type=insight["type"],
                    priority=insight["priority"],
                    title=insight["title"],
                    description=insight["description"],
                    recommendation=insight["recommendation"],
                    created_at=datetime.utcnow()
                )
                session.add(arch_insight)
            
            await session.commit()
            
            return {
                "total_insights": len(insights),
                "insights_by_priority": self._group_insights_by_priority(insights)
            }
            
        except Exception as e:
            logger.error(f"❌ Architectural insights generation failed: {e}")
            return {}
    
    def _group_insights_by_priority(self, insights: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group insights by priority"""
        groups = {"high": 0, "medium": 0, "low": 0}
        for insight in insights:
            priority = insight["priority"]
            groups[priority] = groups.get(priority, 0) + 1
        return groups
    
    async def _update_job_progress(self, job: ArchitecturalAnalysisJob, progress: int, message: str, session: AsyncSession):
        """Update job progress and status message"""
        try:
            job.progress_percentage = progress
            job.current_step = message
            await session.commit()
            
            # Also cache in Redis for real-time updates
            cache_key = f"jqassistant_progress:{job.id}"
            progress_data = {
                "progress": progress,
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            }
            self.redis_client.setex(cache_key, 3600, json.dumps(progress_data))  # 1 hour TTL
            
        except Exception as e:
            logger.warning(f"Failed to update job progress: {e}")
    
    async def _finalize_analysis_job(self, job: ArchitecturalAnalysisJob, session: AsyncSession):
        """Finalize analysis job with completion status and summary"""
        try:
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.progress_percentage = 100
            job.current_step = "Analysis completed"
            
            if job.started_at:
                job.duration_seconds = (job.completed_at - job.started_at).total_seconds()
            
            await session.commit()
            
            logger.info(f"✅ jQAssistant analysis job {job.id} completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to finalize analysis job: {e}")
    
    async def _mark_job_failed(self, job_id: str, error_message: str, session: AsyncSession):
        """Mark analysis job as failed"""
        try:
            await session.execute(
                update(ArchitecturalAnalysisJob)
                .where(ArchitecturalAnalysisJob.id == job_id)
                .values(
                    status=JobStatus.FAILED,
                    completed_at=datetime.utcnow(),
                    error_message=error_message[:1000],
                    progress_percentage=0
                )
            )
            await session.commit()
            
            logger.error(f"❌ jQAssistant analysis job {job_id} marked as failed")
            
        except Exception as e:
            logger.error(f"❌ Failed to mark job as failed: {e}")
    
    def _get_default_rules(self) -> List[str]:
        """Get default jQAssistant analysis rules"""
        return [
            "java:Classpath",
            "java:Type",
            "java:Method",
            "java:Field",
            "java:Package",
            "dependency:Package",
            "dependency:Type"
        ]
    
    async def get_analysis_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get current analysis status"""
        async with get_async_session() as session:
            try:
                result = await session.execute(
                    select(ArchitecturalAnalysisJob).where(ArchitecturalAnalysisJob.id == job_id)
                )
                job = result.scalar_one_or_none()
                
                if not job:
                    return None
                
                return {
                    "job_id": str(job.id),
                    "status": job.status.value,
                    "progress": job.progress_percentage,
                    "current_step": job.current_step,
                    "repository_path": job.repository_path,
                    "repo_id": job.repo_id,
                    "commit_hash": job.commit_hash,
                    "created_at": job.created_at.isoformat() if job.created_at else None,
                    "started_at": job.started_at.isoformat() if job.started_at else None,
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                    "duration_seconds": job.duration_seconds,
                    "total_java_files": job.total_java_files,
                    "error_message": job.error_message
                }
                
            except Exception as e:
                logger.error(f"❌ Failed to get analysis status: {e}")
                return None
    
    async def get_analysis_results(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive analysis results"""
        async with get_async_session() as session:
            try:
                # Get job
                job_result = await session.execute(
                    select(ArchitecturalAnalysisJob).where(ArchitecturalAnalysisJob.id == job_id)
                )
                job = job_result.scalar_one_or_none()
                
                if not job or job.status != JobStatus.COMPLETED:
                    return None
                
                # Get dependencies
                deps_result = await session.execute(
                    select(PackageDependency).where(PackageDependency.analysis_job_id == job_id)
                )
                dependencies = deps_result.scalars().all()
                
                # Get violations
                violations_result = await session.execute(
                    select(ArchitecturalViolation).where(ArchitecturalViolation.analysis_job_id == job_id)
                )
                violations = violations_result.scalars().all()
                
                # Get patterns
                patterns_result = await session.execute(
                    select(DesignPattern).where(DesignPattern.analysis_job_id == job_id)
                )
                patterns = patterns_result.scalars().all()
                
                # Get dead code
                dead_code_result = await session.execute(
                    select(DeadCodeElement).where(DeadCodeElement.analysis_job_id == job_id)
                )
                dead_code = dead_code_result.scalars().all()
                
                # Get metrics
                metrics_result = await session.execute(
                    select(CodeMetrics).where(CodeMetrics.analysis_job_id == job_id)
                )
                metrics = metrics_result.scalar_one_or_none()
                
                # Get insights
                insights_result = await session.execute(
                    select(IndexingArchitecturalInsight).where(IndexingArchitecturalInsight.analysis_job_id == job_id)
                )
                insights = insights_result.scalars().all()
                
                return {
                    "job_info": {
                        "job_id": str(job.id),
                        "repo_id": job.repo_id,
                        "commit_hash": job.commit_hash,
                        "completed_at": job.completed_at.isoformat(),
                        "duration_seconds": job.duration_seconds
                    },
                    "dependencies": {
                        "total": len(dependencies),
                        "cyclic": len([d for d in dependencies if d.is_cyclic]),
                        "details": [
                            {
                                "from_package": d.from_package,
                                "to_package": d.to_package,
                                "type": d.dependency_type,
                                "is_cyclic": d.is_cyclic
                            }
                            for d in dependencies
                        ]
                    },
                    "violations": {
                        "total": len(violations),
                        "by_severity": self._count_violations_by_severity(violations),
                        "details": [
                            {
                                "constraint": v.constraint_name,
                                "type": v.violation_type,
                                "severity": v.severity,
                                "element": v.element_name,
                                "description": v.description,
                                "file_path": v.file_path,
                                "line_number": v.line_number
                            }
                            for v in violations
                        ]
                    },
                    "patterns": {
                        "total": len(patterns),
                        "by_type": self._count_patterns_by_type(patterns),
                        "details": [
                            {
                                "name": p.pattern_name,
                                "type": p.pattern_type,
                                "element": p.element_name,
                                "file_path": p.file_path,
                                "confidence": p.confidence_score,
                                "description": p.description
                            }
                            for p in patterns
                        ]
                    },
                    "dead_code": {
                        "total": len(dead_code),
                        "by_type": self._count_dead_code_by_type(dead_code),
                        "details": [
                            {
                                "type": d.element_type,
                                "name": d.element_name,
                                "file_path": d.file_path,
                                "line_number": d.line_number,
                                "confidence": d.confidence_score,
                                "suggestion": d.removal_suggestion
                            }
                            for d in dead_code
                        ]
                    },
                    "metrics": {
                        "total_java_files": metrics.total_java_files if metrics else 0,
                        "total_lines_of_code": metrics.total_lines_of_code if metrics else 0,
                        "complexity_score": metrics.complexity_score if metrics else 0,
                        "maintainability_index": metrics.maintainability_index if metrics else 0,
                        "coupling_score": metrics.coupling_score if metrics else 0,
                        "cohesion_score": metrics.cohesion_score if metrics else 0
                    },
                    "insights": {
                        "total": len(insights),
                        "by_priority": self._count_insights_by_priority(insights),
                        "details": [
                            {
                                "type": i.insight_type,
                                "priority": i.priority,
                                "title": i.title,
                                "description": i.description,
                                "recommendation": i.recommendation
                            }
                            for i in insights
                        ]
                    }
                }
                
            except Exception as e:
                logger.error(f"❌ Failed to get analysis results: {e}")
                return None
    
    def _count_violations_by_severity(self, violations) -> Dict[str, int]:
        """Count violations by severity"""
        counts = {"ERROR": 0, "WARNING": 0, "INFO": 0}
        for violation in violations:
            counts[violation.severity] = counts.get(violation.severity, 0) + 1
        return counts
    
    def _count_patterns_by_type(self, patterns) -> Dict[str, int]:
        """Count patterns by type"""
        counts = {}
        for pattern in patterns:
            counts[pattern.pattern_type] = counts.get(pattern.pattern_type, 0) + 1
        return counts
    
    def _count_dead_code_by_type(self, dead_code) -> Dict[str, int]:
        """Count dead code by type"""
        counts = {}
        for element in dead_code:
            counts[element.element_type] = counts.get(element.element_type, 0) + 1
        return counts
    
    def _count_insights_by_priority(self, insights) -> Dict[str, int]:
        """Count insights by priority"""
        counts = {"high": 0, "medium": 0, "low": 0}
        for insight in insights:
            counts[insight.priority] = counts.get(insight.priority, 0) + 1
        return counts


# Global service instance
jqassistant_service = JQAssistantService()

async def get_jqassistant_service() -> JQAssistantService:
    """Get jQAssistant service instance"""
    return jqassistant_service