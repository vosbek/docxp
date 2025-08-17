"""
Multi-Repository Processor Service with Parallel Processing
Handles concurrent processing of multiple repositories for enhanced analysis
"""

import asyncio
import logging
import os
import shutil
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import zipfile
import tarfile
import git
import json

from app.core.config import settings
from app.services.vector_service import get_vector_service
from app.services.semantic_ai_service import get_semantic_ai_service
from app.services.ai_service import AIService

logger = logging.getLogger(__name__)

class ProcessingStatus(Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    EXTRACTING = "extracting"
    ANALYZING = "analyzing"
    INDEXING = "indexing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class RepositoryInfo:
    id: str
    name: str
    source_type: str  # git, zip, directory
    source_path: str  # URL, file path, or directory path
    branch: str = "main"
    priority: int = 1  # 1=highest, 5=lowest
    processing_options: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ProcessingResult:
    repository_id: str
    status: ProcessingStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    entities_extracted: int = 0
    business_rules_found: int = 0
    files_processed: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_stats: Dict[str, Any] = field(default_factory=dict)

class RepositoryProcessor:
    """
    Advanced multi-repository processor with parallel processing capabilities
    Optimized for legacy migration analysis and large-scale codebase processing
    """
    
    def __init__(self):
        self.max_concurrent_repos = getattr(settings, 'MAX_CONCURRENT_REPOS', 4)
        self.batch_size = getattr(settings, 'BATCH_SIZE', 50)
        self.processing_timeout = getattr(settings, 'PROCESSING_TIMEOUT', 600)  # 10 minutes per repo
        
        self.vector_service = None
        self.semantic_ai_service = None
        self.ai_service = AIService()
        
        self.active_jobs: Dict[str, ProcessingResult] = {}
        self.job_history: List[ProcessingResult] = []
        
        # File type patterns for different languages
        self.supported_extensions = {
            'java': ['.java', '.jsp', '.jspx'],
            'javascript': ['.js', '.jsx', '.ts', '.tsx'],
            'python': ['.py', '.pyx'],
            'perl': ['.pl', '.pm'],
            'struts': ['.action', '.xml', '.properties'],
            'angular': ['.component.ts', '.service.ts', '.module.ts'],
            'config': ['.xml', '.properties', '.yaml', '.yml', '.json']
        }
        
        # Services will be initialized on first use
    
    async def _initialize_services(self):
        """Initialize required services"""
        try:
            self.vector_service = await get_vector_service()
            self.semantic_ai_service = await get_semantic_ai_service()
            logger.info("Repository processor services initialized")
        except Exception as e:
            logger.error(f"Failed to initialize repository processor services: {e}")
    
    async def process_repositories_batch(
        self,
        repositories: List[RepositoryInfo],
        batch_options: Dict[str, Any] = None
    ) -> Dict[str, ProcessingResult]:
        """
        Process multiple repositories in parallel with intelligent batching
        """
        batch_options = batch_options or {}
        
        # Initialize services if not already done
        if self.vector_service is None or self.semantic_ai_service is None:
            await self._initialize_services()
        
        logger.info(f"Starting batch processing of {len(repositories)} repositories")
        
        # Sort repositories by priority (1=highest priority)
        repositories.sort(key=lambda repo: repo.priority)
        
        # Create processing tasks
        results = {}
        semaphore = asyncio.Semaphore(self.max_concurrent_repos)
        
        async def process_single_repo(repo_info: RepositoryInfo) -> Tuple[str, ProcessingResult]:
            async with semaphore:
                result = await self.process_single_repository(repo_info)
                return repo_info.id, result
        
        # Execute all repository processing tasks
        tasks = [process_single_repo(repo) for repo in repositories]
        
        # Process with progress tracking
        completed_count = 0
        for task in asyncio.as_completed(tasks):
            try:
                repo_id, result = await task
                results[repo_id] = result
                completed_count += 1
                
                logger.info(
                    f"Repository processing progress: {completed_count}/{len(repositories)} "
                    f"({(completed_count/len(repositories)*100):.1f}%)"
                )
                
            except Exception as e:
                logger.error(f"Repository processing failed: {e}")
                # Continue processing other repositories
        
        # Generate batch summary
        await self._generate_batch_summary(results, batch_options)
        
        logger.info(f"Batch processing completed. {len(results)} repositories processed.")
        return results
    
    async def process_single_repository(
        self,
        repo_info: RepositoryInfo
    ) -> ProcessingResult:
        """
        Process a single repository with comprehensive analysis
        """
        result = ProcessingResult(
            repository_id=repo_info.id,
            status=ProcessingStatus.PENDING,
            start_time=datetime.utcnow()
        )
        
        # Register active job
        self.active_jobs[repo_info.id] = result
        
        try:
            # Step 1: Download/Prepare repository
            result.status = ProcessingStatus.DOWNLOADING
            local_path = await self._prepare_repository(repo_info)
            
            # Step 2: Extract and validate content
            result.status = ProcessingStatus.EXTRACTING
            file_inventory = await self._extract_file_inventory(local_path, repo_info)
            result.files_processed = len(file_inventory)
            
            # Step 3: Analyze code structure
            result.status = ProcessingStatus.ANALYZING
            analysis_results = await self._analyze_repository_structure(
                local_path, 
                file_inventory, 
                repo_info
            )
            
            result.entities_extracted = len(analysis_results.get('code_entities', []))
            result.business_rules_found = len(analysis_results.get('business_rules', []))
            
            # Step 4: Index into vector database
            result.status = ProcessingStatus.INDEXING
            indexing_results = await self._index_repository_content(
                repo_info.id,
                analysis_results
            )
            
            # Step 5: Generate processing statistics
            result.processing_stats = await self._generate_processing_stats(
                analysis_results,
                indexing_results,
                file_inventory
            )
            
            result.status = ProcessingStatus.COMPLETED
            result.end_time = datetime.utcnow()
            
            logger.info(f"Repository {repo_info.name} processed successfully")
            
        except asyncio.TimeoutError:
            result.status = ProcessingStatus.FAILED
            result.errors.append("Processing timeout exceeded")
            logger.error(f"Repository {repo_info.name} processing timed out")
            
        except Exception as e:
            result.status = ProcessingStatus.FAILED
            result.errors.append(str(e))
            result.end_time = datetime.utcnow()
            logger.error(f"Repository {repo_info.name} processing failed: {e}")
            
        finally:
            # Cleanup
            try:
                if 'local_path' in locals() and os.path.exists(local_path):
                    shutil.rmtree(local_path, ignore_errors=True)
            except Exception as cleanup_error:
                logger.warning(f"Cleanup failed for {repo_info.name}: {cleanup_error}")
            
            # Move to history
            self.job_history.append(result)
            if repo_info.id in self.active_jobs:
                del self.active_jobs[repo_info.id]
        
        return result
    
    async def _prepare_repository(self, repo_info: RepositoryInfo) -> str:
        """
        Download or prepare repository content for processing
        """
        temp_dir = tempfile.mkdtemp(prefix=f"docxp_repo_{repo_info.id}_")
        
        try:
            if repo_info.source_type == "git":
                # Clone Git repository
                logger.info(f"Cloning repository from {repo_info.source_path}")
                repo = git.Repo.clone_from(
                    repo_info.source_path,
                    temp_dir,
                    branch=repo_info.branch,
                    depth=1  # Shallow clone for faster processing
                )
                
            elif repo_info.source_type == "zip":
                # Extract ZIP file
                logger.info(f"Extracting ZIP file {repo_info.source_path}")
                with zipfile.ZipFile(repo_info.source_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                    
            elif repo_info.source_type == "tar":
                # Extract TAR file
                logger.info(f"Extracting TAR file {repo_info.source_path}")
                with tarfile.open(repo_info.source_path, 'r:*') as tar_ref:
                    tar_ref.extractall(temp_dir)
                    
            elif repo_info.source_type == "directory":
                # Copy local directory
                logger.info(f"Copying directory {repo_info.source_path}")
                if os.path.exists(repo_info.source_path):
                    shutil.copytree(repo_info.source_path, temp_dir, dirs_exist_ok=True)
                else:
                    raise FileNotFoundError(f"Directory not found: {repo_info.source_path}")
                    
            else:
                raise ValueError(f"Unsupported source type: {repo_info.source_type}")
            
            return temp_dir
            
        except Exception as e:
            # Cleanup on failure
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
            raise e
    
    async def _extract_file_inventory(
        self,
        repo_path: str,
        repo_info: RepositoryInfo
    ) -> List[Dict[str, Any]]:
        """
        Create comprehensive inventory of files in the repository
        """
        file_inventory = []
        repo_path_obj = Path(repo_path)
        
        # Define ignore patterns
        ignore_patterns = set(settings.IGNORE_PATTERNS + [
            '.git', '.svn', '.hg',
            'node_modules', '__pycache__', '.pytest_cache',
            'target', 'build', 'dist', 'out',
            '.idea', '.vscode', '.vs',
            '*.class', '*.pyc', '*.pyo', '*.pyd',
            '*.log', '*.tmp', '*.temp'
        ])
        
        def should_ignore(file_path: Path) -> bool:
            for pattern in ignore_patterns:
                if pattern.startswith('*'):
                    if file_path.name.endswith(pattern[1:]):
                        return True
                elif pattern in str(file_path):
                    return True
            return False
        
        # Walk through all files
        for file_path in repo_path_obj.rglob('*'):
            if file_path.is_file() and not should_ignore(file_path):
                try:
                    relative_path = file_path.relative_to(repo_path_obj)
                    file_size = file_path.stat().st_size
                    
                    # Skip very large files (> MAX_FILE_SIZE_MB)
                    if file_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
                        logger.warning(f"Skipping large file: {relative_path} ({file_size} bytes)")
                        continue
                    
                    # Detect file language/type
                    file_extension = file_path.suffix.lower()
                    detected_language = self._detect_file_language(file_extension)
                    
                    file_info = {
                        'path': str(relative_path),
                        'absolute_path': str(file_path),
                        'size': file_size,
                        'extension': file_extension,
                        'language': detected_language,
                        'modified_time': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                        'is_binary': self._is_binary_file(file_path)
                    }
                    
                    file_inventory.append(file_info)
                    
                except Exception as e:
                    logger.warning(f"Failed to process file {file_path}: {e}")
        
        logger.info(f"File inventory created: {len(file_inventory)} files")
        return file_inventory
    
    def _detect_file_language(self, extension: str) -> Optional[str]:
        """Detect programming language from file extension"""
        for language, extensions in self.supported_extensions.items():
            if extension in extensions:
                return language
        return None
    
    def _is_binary_file(self, file_path: Path) -> bool:
        """Check if file is binary"""
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                return b'\0' in chunk
        except:
            return True
    
    async def _analyze_repository_structure(
        self,
        repo_path: str,
        file_inventory: List[Dict[str, Any]],
        repo_info: RepositoryInfo
    ) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of repository structure
        """
        analysis_results = {
            'repository_info': {
                'id': repo_info.id,
                'name': repo_info.name,
                'analysis_timestamp': datetime.utcnow().isoformat()
            },
            'code_entities': [],
            'business_rules': [],
            'dependencies': [],
            'architecture_patterns': [],
            'technology_stack': [],
            'migration_opportunities': []
        }
        
        # Filter files for analysis
        code_files = [f for f in file_inventory if f['language'] and not f['is_binary']]
        
        logger.info(f"Analyzing {len(code_files)} code files")
        
        # Process files in batches to avoid memory issues
        for i in range(0, len(code_files), self.batch_size):
            batch = code_files[i:i + self.batch_size]
            batch_results = await self._process_file_batch(batch, repo_path, repo_info)
            
            # Merge batch results
            for key in ['code_entities', 'business_rules', 'dependencies']:
                if key in batch_results:
                    analysis_results[key].extend(batch_results[key])
        
        # Analyze overall architecture patterns
        architecture_analysis = await self._analyze_architecture_patterns(
            analysis_results['code_entities'],
            file_inventory
        )
        analysis_results['architecture_patterns'] = architecture_analysis
        
        # Detect technology stack
        tech_stack = await self._detect_technology_stack(file_inventory, analysis_results)
        analysis_results['technology_stack'] = tech_stack
        
        # Identify migration opportunities
        migration_opportunities = await self._identify_migration_opportunities(
            analysis_results,
            repo_info
        )
        analysis_results['migration_opportunities'] = migration_opportunities
        
        return analysis_results
    
    async def _process_file_batch(
        self,
        file_batch: List[Dict[str, Any]],
        repo_path: str,
        repo_info: RepositoryInfo
    ) -> Dict[str, Any]:
        """
        Process a batch of files for code analysis
        """
        batch_results = {
            'code_entities': [],
            'business_rules': [],
            'dependencies': []
        }
        
        # Use ThreadPoolExecutor for CPU-intensive file parsing
        with ThreadPoolExecutor(max_workers=settings.MAX_WORKERS) as executor:
            # Submit file processing tasks
            future_to_file = {
                executor.submit(self._analyze_single_file, file_info, repo_path): file_info
                for file_info in file_batch
            }
            
            # Collect results
            for future in as_completed(future_to_file):
                file_info = future_to_file[future]
                try:
                    file_analysis = future.result(timeout=30)  # 30 second timeout per file
                    
                    if file_analysis:
                        # Merge file analysis results
                        for key in batch_results:
                            if key in file_analysis:
                                batch_results[key].extend(file_analysis[key])
                                
                except Exception as e:
                    logger.warning(f"File analysis failed for {file_info['path']}: {e}")
        
        return batch_results
    
    def _analyze_single_file(
        self,
        file_info: Dict[str, Any],
        repo_path: str
    ) -> Dict[str, Any]:
        """
        Analyze a single file (runs in thread pool)
        """
        try:
            file_path = Path(file_info['absolute_path'])
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Basic entity extraction based on language
            entities = self._extract_code_entities(content, file_info)
            
            # Business rule detection
            business_rules = self._extract_business_rules(content, file_info)
            
            # Dependency analysis
            dependencies = self._extract_dependencies(content, file_info)
            
            return {
                'code_entities': entities,
                'business_rules': business_rules,
                'dependencies': dependencies
            }
            
        except Exception as e:
            logger.warning(f"Single file analysis failed: {e}")
            return {}
    
    def _extract_code_entities(
        self,
        content: str,
        file_info: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Extract code entities (classes, methods, functions) from file content
        """
        entities = []
        language = file_info['language']
        
        # Basic pattern matching for different languages
        if language == 'java':
            entities.extend(self._extract_java_entities(content, file_info))
        elif language == 'javascript' or language == 'typescript':
            entities.extend(self._extract_js_entities(content, file_info))
        elif language == 'python':
            entities.extend(self._extract_python_entities(content, file_info))
        
        return entities
    
    def _extract_java_entities(self, content: str, file_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract Java classes, methods, and interfaces"""
        import re
        entities = []
        
        # Extract classes
        class_pattern = r'(?:public\s+)?(?:abstract\s+)?class\s+(\w+)'
        for match in re.finditer(class_pattern, content):
            entities.append({
                'id': f"{file_info['path']}:class:{match.group(1)}",
                'name': match.group(1),
                'type': 'class',
                'language': 'java',
                'file_path': file_info['path'],
                'source_code': self._extract_surrounding_code(content, match.start(), match.end())
            })
        
        # Extract methods
        method_pattern = r'(?:public|private|protected)?\s*(?:static\s+)?(?:\w+\s+)*(\w+)\s*\([^)]*\)\s*\{'
        for match in re.finditer(method_pattern, content):
            entities.append({
                'id': f"{file_info['path']}:method:{match.group(1)}",
                'name': match.group(1),
                'type': 'method',
                'language': 'java',
                'file_path': file_info['path'],
                'source_code': self._extract_surrounding_code(content, match.start(), match.end())
            })
        
        return entities
    
    def _extract_js_entities(self, content: str, file_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract JavaScript/TypeScript functions and classes"""
        import re
        entities = []
        
        # Extract function declarations
        func_pattern = r'function\s+(\w+)\s*\([^)]*\)'
        for match in re.finditer(func_pattern, content):
            entities.append({
                'id': f"{file_info['path']}:function:{match.group(1)}",
                'name': match.group(1),
                'type': 'function',
                'language': file_info['language'],
                'file_path': file_info['path'],
                'source_code': self._extract_surrounding_code(content, match.start(), match.end())
            })
        
        return entities
    
    def _extract_python_entities(self, content: str, file_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract Python classes and functions"""
        import re
        entities = []
        
        # Extract class definitions
        class_pattern = r'class\s+(\w+)'
        for match in re.finditer(class_pattern, content):
            entities.append({
                'id': f"{file_info['path']}:class:{match.group(1)}",
                'name': match.group(1),
                'type': 'class',
                'language': 'python',
                'file_path': file_info['path'],
                'source_code': self._extract_surrounding_code(content, match.start(), match.end())
            })
        
        # Extract function definitions
        func_pattern = r'def\s+(\w+)\s*\([^)]*\):'
        for match in re.finditer(func_pattern, content):
            entities.append({
                'id': f"{file_info['path']}:function:{match.group(1)}",
                'name': match.group(1),
                'type': 'function',
                'language': 'python',
                'file_path': file_info['path'],
                'source_code': self._extract_surrounding_code(content, match.start(), match.end())
            })
        
        return entities
    
    def _extract_surrounding_code(self, content: str, start: int, end: int, context_lines: int = 5) -> str:
        """Extract code with surrounding context"""
        lines = content.split('\n')
        
        # Find line numbers
        start_line = content[:start].count('\n')
        end_line = content[:end].count('\n')
        
        # Extract with context
        context_start = max(0, start_line - context_lines)
        context_end = min(len(lines), end_line + context_lines + 1)
        
        return '\n'.join(lines[context_start:context_end])
    
    def _extract_business_rules(self, content: str, file_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract business rules from comments and documentation"""
        import re
        rules = []
        
        # Look for comments that might contain business rules
        comment_patterns = [
            r'//\s*(?:BUSINESS|RULE|LOGIC|REQUIREMENT):\s*(.+)',
            r'/\*\s*(?:BUSINESS|RULE|LOGIC|REQUIREMENT):\s*(.+?)\*/',
            r'#\s*(?:BUSINESS|RULE|LOGIC|REQUIREMENT):\s*(.+)',
            r'"""(?:.*?)(?:BUSINESS|RULE|LOGIC|REQUIREMENT):\s*(.+?)"""'
        ]
        
        for pattern in comment_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE | re.DOTALL):
                rule_text = match.group(1).strip()
                if len(rule_text) > 10:  # Filter out very short matches
                    rules.append({
                        'rule_id': f"{file_info['path']}:rule:{len(rules)}",
                        'description': rule_text,
                        'file_path': file_info['path'],
                        'category': 'extracted_comment',
                        'confidence_score': 0.7,
                        'plain_english': rule_text
                    })
        
        return rules
    
    def _extract_dependencies(self, content: str, file_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract dependencies from import statements"""
        import re
        dependencies = []
        language = file_info['language']
        
        if language == 'java':
            # Java imports
            import_pattern = r'import\s+([a-zA-Z0-9_.]+);'
            for match in re.finditer(import_pattern, content):
                dependencies.append({
                    'type': 'import',
                    'name': match.group(1),
                    'language': 'java',
                    'file_path': file_info['path']
                })
        
        elif language in ['javascript', 'typescript']:
            # JavaScript/TypeScript imports
            import_patterns = [
                r'import\s+.+\s+from\s+[\'"]([^\'"]+)[\'"]',
                r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)'
            ]
            for pattern in import_patterns:
                for match in re.finditer(pattern, content):
                    dependencies.append({
                        'type': 'import',
                        'name': match.group(1),
                        'language': language,
                        'file_path': file_info['path']
                    })
        
        elif language == 'python':
            # Python imports
            import_patterns = [
                r'import\s+([a-zA-Z0-9_.]+)',
                r'from\s+([a-zA-Z0-9_.]+)\s+import'
            ]
            for pattern in import_patterns:
                for match in re.finditer(pattern, content):
                    dependencies.append({
                        'type': 'import',
                        'name': match.group(1),
                        'language': 'python',
                        'file_path': file_info['path']
                    })
        
        return dependencies
    
    async def _analyze_architecture_patterns(
        self,
        code_entities: List[Dict[str, Any]],
        file_inventory: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Analyze architecture patterns in the codebase
        """
        patterns = []
        
        # Detect MVC pattern
        has_controllers = any('controller' in entity['name'].lower() for entity in code_entities)
        has_models = any('model' in entity['name'].lower() for entity in code_entities)
        has_views = any('view' in entity['name'].lower() for entity in code_entities)
        
        if has_controllers and has_models and has_views:
            patterns.append({
                'pattern': 'MVC',
                'confidence': 0.8,
                'description': 'Model-View-Controller pattern detected'
            })
        
        # Detect Struts framework
        struts_files = [f for f in file_inventory if 'struts' in f['path'].lower() or f['extension'] == '.action']
        if struts_files:
            patterns.append({
                'pattern': 'Struts',
                'confidence': 0.9,
                'description': f'Struts framework detected ({len(struts_files)} related files)'
            })
        
        # Detect Spring framework
        spring_indicators = [entity for entity in code_entities if 
                           'spring' in entity.get('source_code', '').lower()]
        if spring_indicators:
            patterns.append({
                'pattern': 'Spring',
                'confidence': 0.8,
                'description': f'Spring framework detected ({len(spring_indicators)} indicators)'
            })
        
        return patterns
    
    async def _detect_technology_stack(
        self,
        file_inventory: List[Dict[str, Any]],
        analysis_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Detect technology stack from file patterns and content
        """
        tech_stack = []
        
        # Language distribution
        language_counts = {}
        for file_info in file_inventory:
            lang = file_info.get('language')
            if lang:
                language_counts[lang] = language_counts.get(lang, 0) + 1
        
        for language, count in language_counts.items():
            tech_stack.append({
                'technology': language,
                'category': 'programming_language',
                'file_count': count,
                'confidence': min(1.0, count / 10)  # Higher confidence with more files
            })
        
        # Framework detection
        config_files = [f for f in file_inventory if f['extension'] in ['.xml', '.properties', '.yaml', '.yml']]
        
        for config_file in config_files:
            file_name = config_file['path'].lower()
            if 'spring' in file_name:
                tech_stack.append({
                    'technology': 'Spring Framework',
                    'category': 'framework',
                    'evidence': config_file['path'],
                    'confidence': 0.9
                })
            elif 'struts' in file_name:
                tech_stack.append({
                    'technology': 'Apache Struts',
                    'category': 'framework',
                    'evidence': config_file['path'],
                    'confidence': 0.9
                })
        
        return tech_stack
    
    async def _identify_migration_opportunities(
        self,
        analysis_results: Dict[str, Any],
        repo_info: RepositoryInfo
    ) -> List[Dict[str, Any]]:
        """
        Identify opportunities for legacy migration
        """
        opportunities = []
        
        # Check for legacy frameworks
        tech_stack = analysis_results.get('technology_stack', [])
        
        for tech in tech_stack:
            if tech['technology'] in ['Apache Struts', 'Struts']:
                opportunities.append({
                    'type': 'framework_migration',
                    'current_technology': 'Apache Struts',
                    'recommended_technology': 'Spring Boot',
                    'priority': 'high',
                    'effort_estimate': 'medium',
                    'description': 'Migrate from legacy Struts to modern Spring Boot framework'
                })
        
        # Check for CORBA usage
        corba_indicators = [entity for entity in analysis_results.get('code_entities', [])
                          if 'corba' in entity.get('source_code', '').lower()]
        
        if corba_indicators:
            opportunities.append({
                'type': 'communication_migration',
                'current_technology': 'CORBA',
                'recommended_technology': 'gRPC/REST API',
                'priority': 'high',
                'effort_estimate': 'high',
                'description': 'Replace CORBA with modern service communication'
            })
        
        return opportunities
    
    async def _index_repository_content(
        self,
        repository_id: str,
        analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Index repository analysis results into vector database
        """
        if not self.semantic_ai_service:
            logger.warning("Semantic AI service not available, skipping indexing")
            return {'success': False, 'reason': 'service_unavailable'}
        
        try:
            # Prepare data for indexing
            indexing_data = {
                'repository_id': repository_id,
                'code_entities': analysis_results.get('code_entities', []),
                'business_rules': analysis_results.get('business_rules', []),
                'dependencies': analysis_results.get('dependencies', []),
                'architecture_patterns': analysis_results.get('architecture_patterns', []),
                'technology_stack': analysis_results.get('technology_stack', [])
            }
            
            # Index through semantic AI service
            indexing_results = await self.semantic_ai_service.index_repository_content(indexing_data)
            
            logger.info(f"Repository {repository_id} indexed successfully")
            return indexing_results
            
        except Exception as e:
            logger.error(f"Repository indexing failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _generate_processing_stats(
        self,
        analysis_results: Dict[str, Any],
        indexing_results: Dict[str, Any],
        file_inventory: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive processing statistics
        """
        stats = {
            'file_statistics': {
                'total_files': len(file_inventory),
                'code_files': len([f for f in file_inventory if f['language']]),
                'binary_files': len([f for f in file_inventory if f['is_binary']]),
                'total_size_bytes': sum(f['size'] for f in file_inventory)
            },
            'language_distribution': {},
            'entity_statistics': {
                'total_entities': len(analysis_results.get('code_entities', [])),
                'entity_types': {}
            },
            'business_rule_statistics': {
                'total_rules': len(analysis_results.get('business_rules', [])),
                'categories': {}
            },
            'indexing_statistics': indexing_results
        }
        
        # Calculate language distribution
        for file_info in file_inventory:
            lang = file_info.get('language', 'unknown')
            stats['language_distribution'][lang] = stats['language_distribution'].get(lang, 0) + 1
        
        # Calculate entity type distribution
        for entity in analysis_results.get('code_entities', []):
            entity_type = entity.get('type', 'unknown')
            stats['entity_statistics']['entity_types'][entity_type] = \
                stats['entity_statistics']['entity_types'].get(entity_type, 0) + 1
        
        # Calculate business rule categories
        for rule in analysis_results.get('business_rules', []):
            category = rule.get('category', 'unknown')
            stats['business_rule_statistics']['categories'][category] = \
                stats['business_rule_statistics']['categories'].get(category, 0) + 1
        
        return stats
    
    async def _generate_batch_summary(
        self,
        batch_results: Dict[str, ProcessingResult],
        batch_options: Dict[str, Any]
    ) -> None:
        """
        Generate summary report for batch processing
        """
        successful = [r for r in batch_results.values() if r.status == ProcessingStatus.COMPLETED]
        failed = [r for r in batch_results.values() if r.status == ProcessingStatus.FAILED]
        
        summary = {
            'batch_id': batch_options.get('batch_id', 'unknown'),
            'timestamp': datetime.utcnow().isoformat(),
            'total_repositories': len(batch_results),
            'successful': len(successful),
            'failed': len(failed),
            'success_rate': len(successful) / len(batch_results) if batch_results else 0,
            'total_entities_extracted': sum(r.entities_extracted for r in successful),
            'total_business_rules_found': sum(r.business_rules_found for r in successful),
            'total_files_processed': sum(r.files_processed for r in successful),
            'processing_time_stats': {
                'min_duration': min((r.end_time - r.start_time).total_seconds() 
                                  for r in successful if r.end_time) if successful else 0,
                'max_duration': max((r.end_time - r.start_time).total_seconds() 
                                  for r in successful if r.end_time) if successful else 0,
                'avg_duration': sum((r.end_time - r.start_time).total_seconds() 
                                  for r in successful if r.end_time) / len(successful) if successful else 0
            }
        }
        
        logger.info(f"Batch processing summary: {json.dumps(summary, indent=2)}")
    
    async def get_processing_status(self, repository_id: str) -> Optional[ProcessingResult]:
        """Get current processing status for a repository"""
        if repository_id in self.active_jobs:
            return self.active_jobs[repository_id]
        
        # Check history
        for result in self.job_history:
            if result.repository_id == repository_id:
                return result
        
        return None
    
    async def cancel_processing(self, repository_id: str) -> bool:
        """Cancel processing for a specific repository"""
        if repository_id in self.active_jobs:
            self.active_jobs[repository_id].status = ProcessingStatus.CANCELLED
            logger.info(f"Processing cancelled for repository {repository_id}")
            return True
        return False
    
    async def get_batch_status(self) -> Dict[str, Any]:
        """Get overall batch processing status"""
        return {
            'active_jobs': len(self.active_jobs),
            'completed_jobs': len([r for r in self.job_history if r.status == ProcessingStatus.COMPLETED]),
            'failed_jobs': len([r for r in self.job_history if r.status == ProcessingStatus.FAILED]),
            'total_processed': len(self.job_history),
            'current_jobs': list(self.active_jobs.keys())
        }

# Global repository processor instance
repository_processor = RepositoryProcessor()

async def get_repository_processor() -> RepositoryProcessor:
    """Get repository processor instance"""
    return repository_processor