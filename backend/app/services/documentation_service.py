"""
Documentation generation service
"""

import os
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
import json
import hashlib
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.database import DocumentationJob, Repository
from app.models.schemas import DocumentationRequest, BusinessRule
from app.parsers.parser_factory import ParserFactory
from app.services.ai_service import ai_service_instance
from app.services.diagram_service import DiagramService
from app.services.database_analyzer import database_analyzer, DatabaseTable, SQLQuery
from app.services.integration_analyzer import integration_analyzer
from app.services.migration_dashboard import migration_dashboard
from app.services.enhanced_documentation_integration import get_enhanced_documentation_integration

logger = logging.getLogger(__name__)

class DocumentationService:
    """Enhanced main service for documentation generation with detailed progress tracking"""
    
    # Define all generation steps with weights for progress calculation
    GENERATION_STEPS = {
        'initializing': {'weight': 2, 'description': 'Initializing documentation generation'},
        'analyzing_repository': {'weight': 4, 'description': 'Analyzing repository structure and files'},
        'parsing_files': {'weight': 14, 'description': 'Parsing source code files'},
        'analyzing_database_usage': {'weight': 5, 'description': 'Analyzing database usage and SQL queries'},
        'analyzing_integration_flows': {'weight': 6, 'description': 'Analyzing cross-technology integration flows'},
        'extracting_business_rules': {'weight': 15, 'description': 'Extracting business rules with AI'},
        'generating_overview': {'weight': 8, 'description': 'Generating system overview'},
        'generating_api_docs': {'weight': 6, 'description': 'Generating API documentation'},
        'generating_business_rules_docs': {'weight': 4, 'description': 'Generating business rules documentation'},
        'generating_architecture_docs': {'weight': 6, 'description': 'Generating architecture documentation'},
        'generating_database_docs': {'weight': 3, 'description': 'Generating database documentation'},
        'generating_integration_docs': {'weight': 4, 'description': 'Generating integration flow documentation'},
        'generating_migration_dashboard': {'weight': 3, 'description': 'Generating migration dashboard and executive summary'},
        'generating_enhanced_docs': {'weight': 25, 'description': 'Generating enhanced enterprise documentation with code intelligence'},
        'generating_diagrams': {'weight': 4, 'description': 'Generating system diagrams'},
        'saving_documentation': {'weight': 3, 'description': 'Saving generated documentation'},
        'finalizing': {'weight': 2, 'description': 'Finalizing and completing generation'}
    }
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.parser_factory = ParserFactory()
        self.ai_service = ai_service_instance
        self.diagram_service = DiagramService()
        self.enhanced_integration = get_enhanced_documentation_integration()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Progress tracking
        self.current_job_id = None
        self.total_steps_weight = sum(step['weight'] for step in self.GENERATION_STEPS.values())
        self.completed_weight = 0
    
    async def _update_progress(self, step_key: str, progress_within_step: int = 0, additional_info: Dict = None):
        """Update job progress in database with detailed step information"""
        if not self.current_job_id or step_key not in self.GENERATION_STEPS:
            return
        
        step_info = self.GENERATION_STEPS[step_key]
        step_weight = step_info['weight']
        
        # Calculate overall progress percentage
        step_progress = self.completed_weight + (step_weight * progress_within_step / 100)
        overall_progress = min(100, int((step_progress / self.total_steps_weight) * 100))
        
        # Prepare progress data
        progress_data = {
            'current_step': step_key,
            'step_description': step_info['description'],
            'step_progress': progress_within_step,
            'overall_progress': overall_progress,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if additional_info:
            progress_data.update(additional_info)
        
        # Update database
        query = update(DocumentationJob).where(
            DocumentationJob.job_id == self.current_job_id
        ).values(
            progress_percentage=overall_progress,
            current_step=step_key,
            step_description=step_info['description'],
            progress_data=json.dumps(progress_data)
        )
        
        # Execute database update with error handling
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Validate session is still active
                await self.db.execute(select(1))
                
                # Execute update
                result = await self.db.execute(query)
                if result.rowcount == 0:
                    logger.warning(f"No job found for update: {self.current_job_id}")
                    return
                    
                await self.db.commit()
                
                # Log successful progress update
                logger.info(f"✅ DB UPDATED - Job {self.current_job_id} - Step: {step_key} ({overall_progress}%): {step_info['description']}")
                break  # Success, exit retry loop
                
            except Exception as e:
                logger.error(f"❌ DB UPDATE FAILED (attempt {attempt + 1}/{max_retries}) for job {self.current_job_id}: {e}")
                
                if attempt < max_retries - 1:
                    try:
                        await self.db.rollback()
                        await asyncio.sleep(1)  # Brief delay before retry
                    except:
                        pass
                else:
                    logger.error(f"🚨 CRITICAL: Failed to update progress after {max_retries} attempts. Job {self.current_job_id} progress tracking broken!")
                    # Still log the progress locally even if DB update fails
                    logger.info(f"📝 LOCAL PROGRESS - Job {self.current_job_id} - Step: {step_key} ({overall_progress}%)")
        if additional_info:
            logger.debug(f"Additional info: {additional_info}")
    
    @asynccontextmanager
    async def _progress_step(self, step_key: str, **kwargs):
        """Context manager for tracking progress through a step"""
        await self._update_progress(step_key, 0, kwargs)
        
        try:
            yield self._create_step_progress_updater(step_key)
        except Exception as e:
            logger.error(f"Error in step {step_key}: {e}")
            await self._update_progress(step_key, 0, {'error': str(e), **kwargs})
            raise
        else:
            # Mark step as complete
            await self._update_progress(step_key, 100, kwargs)
            self.completed_weight += self.GENERATION_STEPS[step_key]['weight']
    
    def _create_step_progress_updater(self, step_key: str):
        """Create a progress updater function for within-step progress"""
        async def update_step_progress(progress: int, **additional_info):
            await self._update_progress(step_key, progress, additional_info)
        
        return update_step_progress
    
    def _serialize_database_objects(self, obj):
        """Custom JSON serializer for database objects"""
        if isinstance(obj, DatabaseTable):
            return {
                'name': obj.name,
                'columns': obj.columns,
                'indexes': obj.indexes,
                'foreign_keys': obj.foreign_keys,
                'is_inferred': obj.is_inferred
            }
        elif isinstance(obj, SQLQuery):
            return {
                'file_path': obj.file_path,
                'line_number': obj.line_number,
                'query_text': obj.query_text,
                'query_type': obj.query_type,
                'tables': obj.tables,
                'parameters': obj.parameters,
                'is_prepared_statement': obj.is_prepared_statement,
                'context_function': obj.context_function,
                'context_class': obj.context_class
            }
        # For any other non-serializable objects, convert to string
        return str(obj)
    
    async def generate_documentation(self, job_id: str, request: DocumentationRequest):
        """
        Generate documentation for a repository with detailed progress tracking
        """
        start_time = datetime.utcnow()
        self.current_job_id = job_id
        self.completed_weight = 0
        
        try:
            # Update job status to processing
            await self._update_job_status(job_id, "processing")
            
            # Step 1: Initialize and validate
            async with self._progress_step('initializing', repository_path=request.repository_path) as update_progress:
                if not os.path.exists(request.repository_path):
                    raise Exception(f"Repository path does not exist: {request.repository_path}")
                
                logger.info(f"Starting documentation generation for repository: {request.repository_path}")
                await update_progress(100)
            
            # Step 2: Analyze repository structure
            async with self._progress_step('analyzing_repository') as update_progress:
                repo_analysis = await self._analyze_repository(request.repository_path, update_progress)
            
            # Step 3: Parse code files with detailed progress
            async with self._progress_step('parsing_files') as update_progress:
                entities = await self._parse_code_files(request, update_progress)
            
            # Step 4: Analyze database usage with graceful degradation
            async with self._progress_step('analyzing_database_usage') as update_progress:
                database_analysis = await self._analyze_database_usage(request, update_progress)
            
            # Step 5: Analyze cross-technology integration flows
            async with self._progress_step('analyzing_integration_flows') as update_progress:
                integration_analysis = await self._analyze_integration_flows(request, update_progress)
            
            # Step 6: Extract business rules using AI
            async with self._progress_step('extracting_business_rules') as update_progress:
                business_rules = await self._extract_business_rules(entities, request, update_progress)
            
            # Step 7: Generate documentation content
            documentation = {}
            
            # Generate overview
            async with self._progress_step('generating_overview') as update_progress:
                documentation['README.md'] = await self._generate_readme(entities, business_rules, request, update_progress)
            
            # Generate API docs if requested
            if request.include_api_docs:
                async with self._progress_step('generating_api_docs') as update_progress:
                    documentation['API.md'] = await self._generate_api_documentation(entities, update_progress)
            
            # Generate business rules docs
            if business_rules:
                async with self._progress_step('generating_business_rules_docs') as update_progress:
                    documentation['BUSINESS_RULES.md'] = await self._generate_business_rules_doc(business_rules, update_progress)
            
            # Generate architecture docs
            async with self._progress_step('generating_architecture_docs') as update_progress:
                documentation['ARCHITECTURE.md'] = await self._generate_architecture_doc(entities, request, update_progress)
            
            # Generate database documentation if database usage was found
            if database_analysis.get('total_queries_found', 0) > 0:
                async with self._progress_step('generating_database_docs') as update_progress:
                    documentation['DATABASE.md'] = await self._generate_database_documentation(database_analysis, update_progress)
            
            # Generate integration flow documentation if flows were found
            if integration_analysis.get('technology_breakdown', {}).get('integration_flows', 0) > 0:
                async with self._progress_step('generating_integration_docs') as update_progress:
                    documentation['INTEGRATION_FLOWS.md'] = await self._generate_integration_documentation(integration_analysis, update_progress)
            
            # Generate migration dashboard and executive summary
            async with self._progress_step('generating_migration_dashboard') as update_progress:
                migration_analysis = migration_dashboard.generate_migration_dashboard(
                    entities, database_analysis, integration_analysis
                )
                documentation['MIGRATION_SUMMARY.md'] = await self._generate_migration_summary_doc(migration_analysis, update_progress)
            
            # Check if enhanced documentation is requested (exhaustive depth gets enhanced)
            if request.depth.value == 'exhaustive':
                # Generate enhanced documentation with full intelligence
                async with self._progress_step('generating_enhanced_docs') as update_progress:
                    enhanced_docs = await self.enhanced_integration.generate_enhanced_documentation(
                        job_id, entities, request, update_progress
                    )
                    documentation.update(enhanced_docs)
            
            # Generate diagrams if requested
            diagrams = {}
            if request.include_diagrams:
                async with self._progress_step('generating_diagrams') as update_progress:
                    diagrams = await self._generate_diagrams(
                        entities, request, update_progress, 
                        integration_analysis=integration_analysis, 
                        database_analysis=database_analysis, 
                        migration_analysis=migration_analysis
                    )
            
            # Step 7: Save documentation
            async with self._progress_step('saving_documentation') as update_progress:
                output_path = await self._save_documentation(documentation, diagrams, request, job_id, update_progress)
            
            # Step 8: Finalize
            async with self._progress_step('finalizing') as update_progress:
                end_time = datetime.utcnow()
                processing_time = (end_time - start_time).total_seconds()
                
                await self._update_job_completion(
                    job_id=job_id,
                    status="completed",
                    entities_count=len(entities),
                    business_rules_count=len(business_rules),
                    files_processed=repo_analysis['total_files'],
                    output_path=output_path,
                    processing_time=processing_time
                )
                
                logger.info(f"Documentation generation completed successfully for job {job_id}")
                logger.info(f"Generated {len(entities)} entities, {len(business_rules)} business rules in {processing_time:.2f} seconds")
                await update_progress(100, 
                                    entities_count=len(entities),
                                    business_rules_count=len(business_rules), 
                                    processing_time=processing_time)
            
        except Exception as e:
            logger.error(f"Error generating documentation for job {job_id}: {e}")
            await self._update_job_error(job_id, str(e))

    
    async def _analyze_repository(self, repo_path: str, update_progress: Callable = None) -> Dict[str, Any]:
        """Analyze repository structure with detailed progress tracking"""
        analysis = {
            "total_files": 0,
            "total_lines": 0,
            "languages": {},
            "file_list": [],
            "directories": []
        }
        
        # First pass: count total items for progress calculation
        total_items = sum(len(files) for _, _, files in os.walk(repo_path))
        processed_items = 0
        
        logger.info(f"Analyzing repository structure: {repo_path}")
        
        for root, dirs, files in os.walk(repo_path):
            # Skip common non-source directories
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv', 'venv']]
            
            if dirs:
                analysis["directories"].extend([os.path.join(root, d) for d in dirs])
            
            for file in files:
                file_path = Path(root) / file
                
                # Update progress
                processed_items += 1
                if update_progress and total_items > 0:
                    progress = int((processed_items / total_items) * 100)
                    await update_progress(progress, 
                                        current_file=str(file_path), 
                                        processed_files=processed_items,
                                        total_files=total_items)
                
                # Skip non-source files
                if file_path.suffix in ['.pyc', '.class', '.exe', '.dll', '.bin']:
                    continue
                
                analysis["total_files"] += 1
                analysis["file_list"].append(str(file_path))
                
                # Count languages
                ext = file_path.suffix
                if ext:
                    analysis["languages"][ext] = analysis["languages"].get(ext, 0) + 1
                
                # Count lines
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = sum(1 for _ in f)
                        analysis["total_lines"] += lines
                except Exception as e:
                    logger.debug(f"Could not count lines in {file_path}: {e}")
        
        logger.info(f"Repository analysis complete: {analysis['total_files']} files, {analysis['total_lines']} lines, {len(analysis['languages'])} file types")
        return analysis
    
    async def _parse_code_files(self, request: DocumentationRequest, update_progress: Callable = None) -> List[Dict]:
        """Parse all code files in repository with enhanced analysis and progress tracking"""
        entities = []
        repo_path = Path(request.repository_path)
        
        # First pass: collect all parsable files
        parsable_files = []
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv', 'venv']]
            
            for file in files:
                file_path = Path(root) / file
                parser = self.parser_factory.get_parser(file_path)
                if parser:
                    parsable_files.append((file_path, parser))
        
        total_files = len(parsable_files)
        processed_files = 0
        
        logger.info(f"Parsing {total_files} code files")
        
        # Parse each file with progress tracking
        for file_path, parser in parsable_files:
            try:
                # Update progress
                if update_progress:
                    progress = int((processed_files / total_files) * 100) if total_files > 0 else 0
                    await update_progress(progress, 
                                        current_file=str(file_path),
                                        processed_files=processed_files,
                                        total_files=total_files)
                
                # Parse file with enhanced analysis
                file_entities = await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    self._enhanced_parse_file,
                    parser,
                    file_path
                )
                
                if file_entities:
                    entities.extend(file_entities)
                    logger.debug(f"Parsed {len(file_entities)} entities from {file_path}")
                
                processed_files += 1
                
            except Exception as e:
                logger.warning(f"Failed to parse {file_path}: {e}")
                processed_files += 1
        
        logger.info(f"Code parsing complete: {len(entities)} entities extracted from {total_files} files")
        return entities
    
    def _enhanced_parse_file(self, parser, file_path: Path) -> List[Dict]:
        """Enhanced file parsing with additional context extraction"""
        try:
            # Get basic entities from parser
            entities = parser.parse(file_path)
            
            # Enhance entities with additional analysis
            enhanced_entities = []
            for entity in entities:
                enhanced_entity = self._enhance_entity_data(entity, file_path)
                enhanced_entities.append(enhanced_entity)
            
            return enhanced_entities
            
        except Exception as e:
            logger.warning(f"Enhanced parsing failed for {file_path}: {e}")
            # Fallback to basic parsing
            return parser.parse(file_path) if hasattr(parser, 'parse') else []
    
    def _enhance_entity_data(self, entity: Dict, file_path: Path) -> Dict:
        """Enhance entity data with additional context"""
        enhanced_entity = entity.copy()
        
        # Add file context
        enhanced_entity['file_size'] = file_path.stat().st_size if file_path.exists() else 0
        enhanced_entity['file_extension'] = file_path.suffix
        enhanced_entity['relative_path'] = str(file_path)
        
        # Add timestamp
        enhanced_entity['parsed_at'] = datetime.utcnow().isoformat()
        
        # TODO: Add method body analysis, business logic patterns, etc.
        # This is where we'll add deeper code analysis in the next phase
        
        return enhanced_entity
    
    async def _extract_business_rules(
        self, 
        entities: List[Dict], 
        request: DocumentationRequest,
        update_progress: Callable = None
    ) -> List[BusinessRule]:
        """Extract business rules using AI with enhanced context and progress tracking"""
        if not request.include_business_rules:
            logger.info("Business rule extraction skipped (not requested)")
            return []
        
        rules = []
        
        # Group entities by file for context
        entities_by_file = {}
        for entity in entities:
            file_path = entity.get('file_path')
            if file_path not in entities_by_file:
                entities_by_file[file_path] = []
            entities_by_file[file_path].append(entity)
        
        total_files = len(entities_by_file)
        processed_files = 0
        
        logger.info(f"Extracting business rules from {total_files} files using AI")
        
        # Process each file with AI
        for file_path, file_entities in entities_by_file.items():
            try:
                # Update progress
                if update_progress:
                    progress = int((processed_files / total_files) * 100) if total_files > 0 else 0
                    await update_progress(progress, 
                                        current_file=file_path,
                                        processed_files=processed_files,
                                        total_files=total_files)
                
                # Read file content
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Skip very large files to avoid AI context limits
                if len(content) > 50000:  # 50KB limit
                    logger.warning(f"Skipping large file for business rules extraction: {file_path} ({len(content)} chars)")
                    processed_files += 1
                    continue
                
                # Extract rules using AI with enhanced context
                logger.debug(f"Processing {file_path} for business rules ({len(content)} chars, {len(file_entities)} entities)")
                
                file_rules = await self.ai_service.extract_business_rules(
                    code=content,
                    entities=file_entities,
                    keywords=request.keywords
                )
                
                if file_rules:
                    rules.extend(file_rules)
                    logger.info(f"Extracted {len(file_rules)} business rules from {file_path}")
                
                processed_files += 1
                
            except Exception as e:
                logger.warning(f"Failed to extract rules from {file_path}: {e}")
                processed_files += 1
        
        logger.info(f"Business rule extraction complete: {len(rules)} total rules extracted from {total_files} files")
        
        # Sort rules by confidence score (highest first)
        rules.sort(key=lambda r: r.confidence_score, reverse=True)
        
        return rules

    
    async def _generate_documentation_content(
        self,
        entities: List[Dict],
        business_rules: List[BusinessRule],
        request: DocumentationRequest
    ) -> Dict[str, str]:
        """Generate documentation content"""
        documentation = {}
        
        # Generate main README
        documentation['README.md'] = await self._generate_readme(
            entities, business_rules, request
        )
        
        # Generate API documentation if requested
        if request.include_api_docs:
            documentation['API.md'] = await self._generate_api_documentation(entities)
        
        # Generate business rules documentation
        if business_rules:
            documentation['BUSINESS_RULES.md'] = await self._generate_business_rules_doc(
                business_rules
            )
        
        # Generate architecture documentation
        documentation['ARCHITECTURE.md'] = await self._generate_architecture_doc(
            entities, request
        )
        
        return documentation
    
    async def _generate_readme(
        self,
        entities: List[Dict],
        business_rules: List[BusinessRule],
        request: DocumentationRequest,
        update_progress: Callable = None
    ) -> str:
        """Generate main README documentation with progress tracking"""
        
        logger.info("Generating README documentation with AI")
        
        # Step 1: Generate AI overview
        if update_progress:
            await update_progress(20, current_task="Generating AI overview")
        
        overview = await self.ai_service.generate_overview(
            entities=entities,
            business_rules=business_rules,
            depth=request.depth
        )
        
        # Step 2: Generate repository structure
        if update_progress:
            await update_progress(40, current_task="Analyzing repository structure")
        
        tree_structure = await self._generate_tree_structure(request.repository_path)
        
        # Step 3: Generate component summary
        if update_progress:
            await update_progress(60, current_task="Summarizing key components")
        
        component_summary = await self._generate_component_summary(entities)
        
        # Step 4: Generate dependency analysis
        if update_progress:
            await update_progress(80, current_task="Analyzing dependencies")
        
        dependency_list = await self._generate_dependency_list(entities)
        
        # Step 5: Compile final README
        if update_progress:
            await update_progress(95, current_task="Compiling README")
        
        # Calculate detailed statistics
        entity_stats = self._calculate_entity_statistics(entities)
        
        readme = f"""# Repository Documentation

Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
Documentation Depth: {request.depth.value}

## Overview

{overview}

## Statistics

- **Total Code Entities**: {len(entities)}
- **Classes**: {entity_stats['classes']}
- **Functions**: {entity_stats['functions']}
- **Methods**: {entity_stats['methods']}
- **Interfaces**: {entity_stats['interfaces']}
- **Business Rules Identified**: {len(business_rules)}
- **High-Confidence Business Rules**: {len([r for r in business_rules if r.confidence_score >= 0.8])}

## Documentation Index

- [API Documentation](API.md)
- [Business Rules](BUSINESS_RULES.md)
- [Architecture](ARCHITECTURE.md)

## Repository Structure

```
{tree_structure}
```

## Key Components

{component_summary}

## Dependencies

{dependency_list}

## Business Rules Summary

{self._generate_business_rules_summary(business_rules)}
"""
        
        if update_progress:
            await update_progress(100, current_task="README generation complete")
        
        logger.info(f"README generated successfully ({len(readme)} characters)")
        return readme
    
    def _calculate_entity_statistics(self, entities: List[Dict]) -> Dict[str, int]:
        """Calculate detailed entity statistics"""
        stats = {
            'classes': 0,
            'functions': 0,
            'methods': 0,
            'interfaces': 0,
            'enums': 0,
            'variables': 0
        }
        
        for entity in entities:
            entity_type = entity.get('type', '').lower()
            if entity_type in stats:
                stats[entity_type] += 1
        
        return stats
    
    def _generate_business_rules_summary(self, business_rules: List[BusinessRule]) -> str:
        """Generate a summary of business rules by category"""
        if not business_rules:
            return "No business rules were identified in this codebase."
        
        from collections import Counter
        categories = Counter(rule.category for rule in business_rules)
        
        summary = f"Identified {len(business_rules)} business rules across {len(categories)} categories:\n\n"
        for category, count in categories.most_common():
            avg_confidence = sum(r.confidence_score for r in business_rules if r.category == category) / count
            summary += f"- **{category}**: {count} rules (avg confidence: {avg_confidence:.1%})\n"
        
        return summary
    
    async def _generate_api_documentation(self, entities: List[Dict], update_progress: Callable = None) -> str:
        """Generate API documentation with progress tracking"""
        logger.info("Generating API documentation")
        
        api_doc = "# API Documentation\n\n"
        api_doc += f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n"
        
        # Filter API-relevant entities (functions, classes, methods)
        api_entities = [e for e in entities if e.get('type') in ['function', 'class', 'method', 'interface']]
        
        if update_progress:
            await update_progress(10, current_task="Filtering API entities", api_entities_count=len(api_entities))
        
        # Group by file
        by_file = {}
        for entity in api_entities:
            file_path = entity.get('file_path', 'unknown')
            if file_path not in by_file:
                by_file[file_path] = []
            by_file[file_path].append(entity)
        
        total_files = len(by_file)
        processed_files = 0
        
        for file_path, file_entities in sorted(by_file.items()):
            if update_progress:
                progress = 10 + int((processed_files / total_files) * 80) if total_files > 0 else 90
                await update_progress(progress, 
                                    current_file=file_path,
                                    processed_files=processed_files,
                                    total_files=total_files)
            
            api_doc += f"\n## {file_path}\n\n"
            
            # Sort entities by type and name
            file_entities.sort(key=lambda x: (x.get('type', ''), x.get('name', '')))
            
            for entity in file_entities:
                entity_type = entity.get('type', 'unknown')
                name = entity.get('name', 'unnamed')
                docstring = entity.get('docstring', '')
                
                api_doc += f"### {entity_type.title()}: `{name}`\n\n"
                
                if docstring:
                    api_doc += f"**Description:** {docstring}\n\n"
                
                # Add parameters if function/method
                if entity_type in ['function', 'method'] and entity.get('parameters'):
                    api_doc += "**Parameters:**\n"
                    for param in entity.get('parameters', []):
                        api_doc += f"- `{param}`\n"
                    api_doc += "\n"
                
                # Add complexity info if available
                if entity.get('complexity'):
                    api_doc += f"**Complexity:** {entity.get('complexity')}\n\n"
                
                # Add file location
                if entity.get('line_number'):
                    api_doc += f"**Location:** Line {entity.get('line_number')}\n\n"
            
            processed_files += 1
        
        if update_progress:
            await update_progress(100, current_task="API documentation complete")
        
        logger.info(f"API documentation generated ({len(api_doc)} characters, {len(api_entities)} entities)")
        return api_doc

    
    async def _generate_business_rules_doc(self, rules: List[BusinessRule], update_progress: Callable = None) -> str:
        """Generate business rules documentation with progress tracking"""
        logger.info(f"Generating business rules documentation for {len(rules)} rules")
        
        doc = "# Business Rules Documentation\n\n"
        doc += f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n"
        
        if update_progress:
            await update_progress(10, current_task="Organizing business rules by category")
        
        # Group by category and sort by confidence
        by_category = {}
        for rule in rules:
            category = rule.category
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(rule)
        
        # Sort categories by number of rules (most rules first)
        sorted_categories = sorted(by_category.items(), key=lambda x: len(x[1]), reverse=True)
        
        # Add summary
        doc += f"## Summary\n\n"
        doc += f"Total business rules identified: **{len(rules)}**\n\n"
        doc += f"Categories: **{len(by_category)}**\n\n"
        
        for category, category_rules in sorted_categories:
            avg_confidence = sum(r.confidence_score for r in category_rules) / len(category_rules)
            high_confidence_count = len([r for r in category_rules if r.confidence_score >= 0.8])
            doc += f"- **{category}**: {len(category_rules)} rules (avg confidence: {avg_confidence:.1%}, high confidence: {high_confidence_count})\n"
        
        doc += "\n---\n\n"
        
        total_categories = len(sorted_categories)
        processed_categories = 0
        
        for category, category_rules in sorted_categories:
            if update_progress:
                progress = 10 + int((processed_categories / total_categories) * 80) if total_categories > 0 else 90
                await update_progress(progress, 
                                    current_category=category,
                                    processed_categories=processed_categories,
                                    total_categories=total_categories)
            
            # Sort rules within category by confidence (highest first)
            category_rules.sort(key=lambda r: r.confidence_score, reverse=True)
            
            doc += f"\n## {category}\n\n"
            doc += f"*{len(category_rules)} rules in this category*\n\n"
            
            for rule in category_rules:
                doc += f"### {rule.id}\n\n"
                doc += f"**Description:** {rule.description}\n\n"
                doc += f"**Confidence Score:** {rule.confidence_score:.1%}"
                
                # Add confidence indicator
                if rule.confidence_score >= 0.9:
                    doc += " 🟢 (Very High)\n\n"
                elif rule.confidence_score >= 0.7:
                    doc += " 🟡 (High)\n\n"
                elif rule.confidence_score >= 0.5:
                    doc += " 🟠 (Medium)\n\n"
                else:
                    doc += " 🔴 (Low)\n\n"
                
                doc += f"**Code Reference:** `{rule.code_reference}`\n\n"
                
                if rule.validation_logic:
                    doc += f"**Implementation Details:**\n```\n{rule.validation_logic}\n```\n\n"
                
                if rule.related_entities:
                    doc += f"**Related Components:** {', '.join(rule.related_entities)}\n\n"
                
                # Add business impact if available
                if hasattr(rule, 'business_impact') and rule.business_impact:
                    doc += f"**Business Impact:** {rule.business_impact}\n\n"
                
                doc += "---\n\n"
            
            processed_categories += 1
        
        if update_progress:
            await update_progress(100, current_task="Business rules documentation complete")
        
        logger.info(f"Business rules documentation generated ({len(doc)} characters)")
        return doc
    
    async def _generate_architecture_doc(
        self, 
        entities: List[Dict], 
        request: DocumentationRequest,
        update_progress: Callable = None
    ) -> str:
        """Generate architecture documentation with progress tracking"""
        logger.info(f"Generating architecture documentation (depth: {request.depth.value})")
        
        if update_progress:
            await update_progress(20, current_task="Preparing architecture analysis")
        
        # Enhanced architecture documentation with AI
        architecture_doc = await self.ai_service.generate_architecture_doc(entities, request.depth)
        
        if update_progress:
            await update_progress(100, current_task="Architecture documentation complete")
        
        logger.info(f"Architecture documentation generated ({len(architecture_doc)} characters)")
        return architecture_doc
    
    async def _generate_diagrams(
        self,
        entities: List[Dict],
        request: DocumentationRequest,
        update_progress: Callable = None,
        integration_analysis: Optional[Dict] = None,
        database_analysis: Optional[Dict] = None,
        migration_analysis: Optional[Dict] = None
    ) -> Dict[str, str]:
        """Generate comprehensive Mermaid diagrams with enterprise migration focus"""
        logger.info("Generating enterprise migration diagrams")
        diagrams = {}
        
        # Original technical diagrams
        if update_progress:
            await update_progress(10, current_task="Generating class diagram")
        diagrams['class_diagram.mmd'] = await self.diagram_service.generate_class_diagram(entities)
        
        if update_progress:
            await update_progress(20, current_task="Generating flow diagram")
        diagrams['flow_diagram.mmd'] = await self.diagram_service.generate_flow_diagram(entities)
        
        # Enhanced migration architecture diagram
        if update_progress:
            await update_progress(35, current_task="Generating migration architecture diagram")
        diagrams['migration_architecture.mmd'] = await self.diagram_service.generate_migration_architecture_diagram(
            entities, integration_analysis, migration_analysis
        )
        
        # Migration risk assessment matrix
        if migration_analysis and migration_analysis.get('components'):
            if update_progress:
                await update_progress(50, current_task="Generating migration risk matrix")
            diagrams['migration_risk_matrix.mmd'] = await self.diagram_service.generate_migration_risk_matrix(
                migration_analysis
            )
        
        # Data flow diagram with actual database and integration data
        if update_progress:
            await update_progress(65, current_task="Generating data flow diagram")
        diagrams['data_flow_diagram.mmd'] = await self.diagram_service.generate_data_flow_diagram(
            entities, database_analysis, integration_analysis
        )
        
        # Technology integration mapping
        if integration_analysis and integration_analysis.get('integration_flows'):
            if update_progress:
                await update_progress(80, current_task="Generating technology integration map")
            diagrams['technology_integration_map.mmd'] = await self.diagram_service.generate_technology_integration_map(
                integration_analysis
            )
        
        # Legacy architecture diagram for comparison
        if update_progress:
            await update_progress(90, current_task="Generating legacy architecture diagram")
        diagrams['legacy_architecture.mmd'] = await self.diagram_service.generate_architecture_diagram(entities)
        
        if update_progress:
            await update_progress(100, current_task="Enterprise diagram generation complete")
        
        logger.info(f"Generated {len(diagrams)} enterprise migration diagrams")
        return diagrams
    
    async def _save_documentation(
        self,
        documentation: Dict[str, str],
        diagrams: Dict[str, str],
        request: DocumentationRequest,
        job_id: str,
        update_progress: Callable = None
    ) -> str:
        """Save documentation to files with progress tracking"""
        output_dir = Path(request.output_path) / job_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Saving documentation to {output_dir}")
        
        total_files = len(documentation) + len(diagrams)
        saved_files = 0
        
        # Save documentation files
        if update_progress:
            await update_progress(10, current_task="Saving documentation files")
        
        for filename, content in documentation.items():
            file_path = output_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            saved_files += 1
            if update_progress and total_files > 0:
                progress = 10 + int((saved_files / total_files) * 80)
                await update_progress(progress, 
                                    current_file=filename,
                                    saved_files=saved_files,
                                    total_files=total_files)
        
        # Save diagrams
        if diagrams:
            diagrams_dir = output_dir / 'diagrams'
            diagrams_dir.mkdir(exist_ok=True)
            
            for filename, content in diagrams.items():
                file_path = diagrams_dir / filename
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                saved_files += 1
                if update_progress and total_files > 0:
                    progress = 10 + int((saved_files / total_files) * 80)
                    await update_progress(progress, 
                                        current_file=f"diagrams/{filename}",
                                        saved_files=saved_files,
                                        total_files=total_files)
        
        if update_progress:
            await update_progress(100, current_task="Documentation saved successfully")
        
        logger.info(f"Saved {len(documentation)} documentation files and {len(diagrams)} diagrams to {output_dir}")
        return str(output_dir)
    
    async def _generate_tree_structure(self, repo_path: str) -> str:
        """Generate repository tree structure"""
        tree = []
        repo_path = Path(repo_path)
        
        def add_tree(path: Path, prefix: str = "", is_last: bool = True):
            if path.name in ['.git', '__pycache__', 'node_modules', '.venv']:
                return
            
            connector = "└── " if is_last else "├── "
            tree.append(f"{prefix}{connector}{path.name}")
            
            if path.is_dir():
                children = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
                for i, child in enumerate(children[:10]):  # Limit to 10 items
                    is_last_child = i == len(children) - 1
                    extension = "    " if is_last else "│   "
                    add_tree(child, prefix + extension, is_last_child)
        
        add_tree(repo_path)
        return '\n'.join(tree[:50])  # Limit output

    
    async def _generate_component_summary(self, entities: List[Dict]) -> str:
        """Generate component summary"""
        classes = [e for e in entities if e.get('type') == 'class']
        
        summary = ""
        for cls in classes[:20]:  # Top 20 classes
            summary += f"- **{cls.get('name')}**: {cls.get('file_path', 'unknown')}\n"
        
        return summary
    
    async def _generate_dependency_list(self, entities: List[Dict]) -> str:
        """Generate dependency list"""
        dependencies = set()
        
        for entity in entities:
            deps = entity.get('dependencies', [])
            dependencies.update(deps)
        
        dep_list = ""
        for dep in sorted(list(dependencies)[:20]):  # Top 20 dependencies
            dep_list += f"- {dep}\n"
        
        return dep_list
    
    async def _analyze_database_usage(self, request: DocumentationRequest, update_progress: Callable = None) -> Dict[str, Any]:
        """
        Analyze database usage in the repository with graceful degradation
        Always works regardless of database connectivity
        """
        repo_path = Path(request.repository_path)
        
        # Collect all source files for database analysis
        source_files = []
        supported_extensions = ['.py', '.java', '.js', '.ts', '.sql', '.jsp', '.jsf']
        
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv', 'venv']]
            
            for file in files:
                file_path = Path(root) / file
                if any(str(file_path).endswith(ext) for ext in supported_extensions):
                    source_files.append(file_path)
        
        if update_progress:
            await update_progress(25, total_files=len(source_files), status="Scanning files for database usage")
        
        logger.info(f"Analyzing database usage in {len(source_files)} files")
        
        try:
            # Perform database analysis with graceful degradation
            analysis_result = await database_analyzer.analyze_database_usage(source_files)
            
            if update_progress:
                await update_progress(75, 
                                    queries_found=analysis_result['total_queries_found'],
                                    tables_found=analysis_result['unique_tables'],
                                    analysis_mode=analysis_result['analysis_mode'])
            
            # Log database analysis results
            logger.info(f"Database analysis completed: {analysis_result['analysis_mode']} mode")
            logger.info(f"Found {analysis_result['total_queries_found']} SQL queries across {analysis_result['unique_tables']} tables")
            
            if analysis_result['available_connections']:
                logger.info(f"Database connections available: {analysis_result['available_connections']}")
            else:
                logger.info("No database connections configured - using static analysis only")
            
            if update_progress:
                await update_progress(100, status="Database analysis completed")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error during database analysis: {e}")
            if update_progress:
                await update_progress(100, status=f"Database analysis failed: {str(e)}", error=True)
            
            # Return minimal result even on error
            return {
                'static_analysis': {'queries': [], 'tables': []},
                'live_analysis': {},
                'analysis_mode': 'error',
                'total_queries_found': 0,
                'unique_tables': 0,
                'error': str(e)
            }
    
    async def _generate_database_documentation(self, database_analysis: Dict[str, Any], update_progress: Callable = None) -> str:
        """Generate comprehensive database documentation from analysis results"""
        if update_progress:
            await update_progress(10, status="Generating database documentation")
        
        # Prepare context for AI
        context = {
            'database_analysis': database_analysis,
            'analysis_mode': database_analysis.get('analysis_mode', 'static_only'),
            'total_queries': database_analysis.get('total_queries_found', 0),
            'unique_tables': database_analysis.get('unique_tables', 0),
        }
        
        if update_progress:
            await update_progress(30, status="Analyzing query patterns")
        
        # Enhanced prompt for database documentation
        prompt = f"""
You are a database architecture expert creating documentation for enterprise legacy migration.

## Database Analysis Context

**Analysis Mode**: {context['analysis_mode']}
**Total SQL Queries Found**: {context['total_queries']}
**Unique Tables Referenced**: {context['unique_tables']}

## Detailed Analysis Results

{json.dumps(database_analysis, indent=2, default=self._serialize_database_objects)}

## Requirements

Create comprehensive database documentation that helps migration architects understand:

1. **Database Usage Overview**
   - Summary of database interaction patterns
   - Most frequently accessed tables
   - Query complexity analysis
   - Database technology dependencies

2. **SQL Query Analysis**
   - Query types and patterns (SELECT, INSERT, UPDATE, DELETE)
   - Prepared statement usage
   - Parameter binding patterns
   - Complex query identification

3. **Schema Insights** 
   - Tables and relationships (inferred from queries)
   - Data flow patterns
   - Database access patterns by application layer

4. **Migration Considerations**
   - Database modernization opportunities
   - Query optimization candidates
   - Schema migration complexity assessment
   - Technology stack dependencies

5. **Risk Assessment**
   - Hard-coded queries vs parameterized
   - Complex joins and subqueries
   - Database-specific feature usage
   - Data integrity constraints

## Output Format

Generate a complete DATABASE.md file in markdown format with:
- Clear sections with proper headings
- Tables and lists for structured data
- Code blocks for SQL examples
- Migration recommendations
- Risk assessments

Focus on providing actionable insights for legacy system migration scenarios.
"""
        
        if update_progress:
            await update_progress(50, status="Generating documentation with AI")
        
        try:
            documentation = await self.ai_service.generate_content(
                prompt=prompt,
                max_tokens=4000,
                temperature=0.3
            )
            
            if update_progress:
                await update_progress(90, status="Formatting documentation")
            
            # Add metadata header
            header = f"""# Database Documentation

**Generated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
**Analysis Mode**: {context['analysis_mode']}
**Queries Found**: {context['total_queries']}
**Tables Identified**: {context['unique_tables']}

---

"""
            
            final_doc = header + documentation
            
            if update_progress:
                await update_progress(100, status="Database documentation completed")
            
            logger.info(f"Generated database documentation: {len(final_doc)} characters")
            return final_doc
            
        except Exception as e:
            logger.error(f"Error generating database documentation: {e}")
            error_doc = f"""# Database Documentation

**Generated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
**Status**: Error during generation

## Error
Failed to generate database documentation: {str(e)}

## Analysis Summary
- **Analysis Mode**: {context['analysis_mode']}
- **Queries Found**: {context['total_queries']}
- **Tables Identified**: {context['unique_tables']}

Please check the logs for more details.
"""
            return error_doc
    
    async def _analyze_integration_flows(self, request: DocumentationRequest, update_progress: Callable = None) -> Dict[str, Any]:
        """
        Analyze cross-technology integration flows for enterprise migration insights
        """
        repo_path = Path(request.repository_path)
        
        # Collect all source files for integration analysis
        source_files = []
        integration_extensions = ['.ts', '.js', '.html', '.java', '.jsp', '.jsf', '.jspx', '.xml']
        
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv', 'venv', 'target', 'dist', 'build']]
            
            for file in files:
                file_path = Path(root) / file
                if any(str(file_path).endswith(ext) for ext in integration_extensions):
                    source_files.append(file_path)
        
        if update_progress:
            await update_progress(20, total_files=len(source_files), status="Scanning files for integration patterns")
        
        logger.info(f"Analyzing integration flows in {len(source_files)} files")
        
        try:
            # Perform cross-technology integration analysis
            analysis_result = await integration_analyzer.analyze_integration_flows(source_files)
            
            if update_progress:
                await update_progress(80, 
                                    flows_found=analysis_result['technology_breakdown']['integration_flows'],
                                    http_calls=analysis_result['technology_breakdown']['http_calls'],
                                    rest_endpoints=analysis_result['technology_breakdown']['rest_endpoints'],
                                    struts_actions=analysis_result['technology_breakdown']['struts_actions'])
            
            # Log integration analysis results
            breakdown = analysis_result['technology_breakdown']
            logger.info(f"Integration analysis completed: {breakdown['integration_flows']} flows discovered")
            logger.info(f"Found {breakdown['http_calls']} HTTP calls, {breakdown['rest_endpoints']} REST endpoints, {breakdown['struts_actions']} Struts actions")
            
            if update_progress:
                await update_progress(100, status="Integration flow analysis completed")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error during integration flow analysis: {e}")
            if update_progress:
                await update_progress(100, status=f"Integration analysis failed: {str(e)}", error=True)
            
            # Return minimal result even on error
            return {
                'integration_flows': [],
                'flow_analysis': {},
                'technology_breakdown': {
                    'http_calls': 0,
                    'rest_endpoints': 0,
                    'struts_actions': 0,
                    'jsp_components': 0,
                    'integration_flows': 0
                },
                'migration_insights': {},
                'error': str(e)
            }
    
    async def _generate_integration_documentation(self, integration_analysis: Dict[str, Any], update_progress: Callable = None) -> str:
        """Generate comprehensive integration flow documentation for enterprise migration"""
        if update_progress:
            await update_progress(10, status="Generating integration flow documentation")
        
        # Prepare context for AI
        context = {
            'integration_analysis': integration_analysis,
            'total_flows': integration_analysis['technology_breakdown']['integration_flows'],
            'total_http_calls': integration_analysis['technology_breakdown']['http_calls'],
            'total_endpoints': integration_analysis['technology_breakdown']['rest_endpoints'],
            'total_struts': integration_analysis['technology_breakdown']['struts_actions'],
            'migration_insights': integration_analysis.get('migration_insights', {})
        }
        
        if update_progress:
            await update_progress(30, status="Analyzing integration patterns")
        
        # Enhanced prompt for integration flow documentation focused on enterprise migration
        prompt = f"""
You are an enterprise integration architect creating documentation for legacy system migration.

## Integration Analysis Context

**Total Integration Flows Found**: {context['total_flows']}
**HTTP Client Calls**: {context['total_http_calls']}
**REST Endpoints**: {context['total_endpoints']}
**Struts Actions**: {context['total_struts']}

## Detailed Integration Analysis Results

{json.dumps(integration_analysis, indent=2, default=self._serialize_database_objects)}

## Requirements

Create comprehensive integration flow documentation that helps migration architects understand:

1. **Integration Flow Overview**
   - Summary of all discovered integration patterns
   - Technology stack integration points
   - Data flow patterns across system boundaries
   - Most critical integration pathways

2. **Frontend → Backend Integration Mapping**
   - Angular/JavaScript HTTP calls mapped to REST endpoints
   - JSP forms and links mapped to Struts actions
   - UI component → backend service traceability
   - Parameter passing patterns and data contracts

3. **Technology Transition Points**
   - Legacy framework integration patterns (Struts, JSP)
   - Modern API integration patterns (REST, Angular)
   - Cross-cutting concerns (authentication, validation, error handling)
   - Session and state management patterns

4. **Enterprise Migration Assessment**
   - Migration complexity analysis for each integration flow
   - High-risk integration points requiring special attention
   - Modernization opportunities and recommended approaches
   - Integration testing strategy recommendations

5. **Data Flow Analysis**
   - End-to-end data flow tracing from UI to database
   - Integration dependency mapping
   - Critical business process integration flows
   - Error propagation and handling patterns

6. **Migration Strategy Recommendations**
   - Phased migration approach for integration modernization
   - API-first migration strategy recommendations
   - Risk mitigation for critical integration points
   - Testing and validation strategies for integration changes

## Output Format

Generate a complete INTEGRATION_FLOWS.md file in markdown format with:
- Clear sections with proper headings and subheadings
- Integration flow diagrams in text format
- Tables for integration mapping and analysis
- Code examples showing integration patterns
- Risk assessments and migration recommendations
- Actionable migration strategies

Focus on providing critical insights that help enterprise architects understand how to modernize complex legacy integration patterns while maintaining system functionality and business continuity.
"""
        
        if update_progress:
            await update_progress(50, status="Generating documentation with AI")
        
        try:
            documentation = await self.ai_service.generate_content(
                prompt=prompt,
                max_tokens=5000,
                temperature=0.2
            )
            
            if update_progress:
                await update_progress(90, status="Formatting integration documentation")
            
            # Add metadata header
            header = f"""# Integration Flow Documentation

**Generated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
**Integration Flows Found**: {context['total_flows']}
**HTTP Calls Mapped**: {context['total_http_calls']}
**REST Endpoints Found**: {context['total_endpoints']}
**Struts Actions Found**: {context['total_struts']}

---

"""
            
            final_doc = header + documentation
            
            if update_progress:
                await update_progress(100, status="Integration flow documentation completed")
            
            logger.info(f"Generated integration flow documentation: {len(final_doc)} characters")
            return final_doc
            
        except Exception as e:
            logger.error(f"Error generating integration documentation: {e}")
            error_doc = f"""# Integration Flow Documentation

**Generated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
**Status**: Error during generation

## Error
Failed to generate integration flow documentation: {str(e)}

## Analysis Summary
- **Integration Flows Found**: {context['total_flows']}
- **HTTP Calls Mapped**: {context['total_http_calls']}
- **REST Endpoints Found**: {context['total_endpoints']}
- **Struts Actions Found**: {context['total_struts']}

Please check the logs for more details.
"""
            return error_doc
    
    async def _generate_migration_summary_doc(self, migration_analysis: Dict[str, Any], update_progress: Callable = None) -> str:
        """Generate executive migration summary documentation"""
        if update_progress:
            await update_progress(10, status="Generating migration summary")
        
        summary = migration_analysis['summary']
        executive_summary = migration_analysis['executive_summary']
        risk_matrix = migration_analysis['risk_matrix']
        roadmap = migration_analysis['migration_roadmap']
        
        if update_progress:
            await update_progress(30, status="Creating executive dashboard")
        
        # Create rich markdown documentation with tables and charts
        content = f"""# Enterprise Migration Summary & Dashboard

**Generated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
**Migration Readiness Score**: {summary.migration_readiness_score}/100
**Estimated Timeline**: {summary.timeline_estimate}
**Total Effort**: {summary.estimated_effort_days} days

---

## 📊 Executive Summary

| Metric | Value | Status |
|--------|-------|--------|
| **Migration Readiness** | {summary.migration_readiness_score}/100 | {'✅ Ready' if summary.migration_readiness_score >= 70 else '⚠️  Needs Preparation' if summary.migration_readiness_score >= 40 else '❌ High Risk'} |
| **Total Components** | {summary.total_components} | Analysis Complete |
| **Critical Components** | {summary.critical_components} | {'❌ Action Required' if summary.critical_components > 0 else '✅ Good'} |
| **High Risk Components** | {summary.high_risk_components} | {'⚠️  Monitor Closely' if summary.high_risk_components > 0 else '✅ Low Risk'} |
| **Estimated Investment** | {executive_summary['investment_required']} | Budget Planning |
| **Business Impact** | {executive_summary['business_impact']} | Risk Assessment |

### 🎯 **Recommended Approach**: {summary.recommended_approach}

### 💡 Key Insights
"""
        
        for insight in executive_summary['key_insights']:
            content += f"- {insight}\n"
        
        if update_progress:
            await update_progress(50, status="Building risk assessment matrix")
        
        content += f"""
---

## 🚨 Risk Assessment Matrix

### Critical Risk Components ({len(risk_matrix['critical'])})
"""
        if risk_matrix['critical']:
            content += """
| Component | Type | Complexity | Effort | Modernization Approach |
|-----------|------|------------|--------|------------------------|
"""
            for comp in risk_matrix['critical'][:10]:  # Limit to top 10
                content += f"| {comp['name']} | {comp['type']} | {comp['complexity']} | {comp['effort']} | {comp['approach']} |\n"
        else:
            content += "✅ No critical risk components identified.\n"
        
        content += f"""
### High Risk Components ({len(risk_matrix['high'])})
"""
        if risk_matrix['high']:
            content += """
| Component | Type | Complexity | Effort | Dependencies |
|-----------|------|------------|--------|--------------|
"""
            for comp in risk_matrix['high'][:10]:  # Limit to top 10
                content += f"| {comp['name']} | {comp['type']} | {comp['complexity']} | {comp['effort']} | {comp['dependencies']} |\n"
        else:
            content += "✅ No high risk components identified.\n"
        
        if update_progress:
            await update_progress(70, status="Creating migration roadmap")
        
        content += """
---

## 🗺️  Migration Roadmap

"""
        
        for phase_key, phase_data in roadmap.items():
            phase_num = phase_key.split('_')[1]
            content += f"""### Phase {phase_num}: {phase_data['name']}

**Focus**: {phase_data['focus']}  
**Components**: {len(phase_data['components'])} components

| Priority | Component | Type | Effort | Risk Level |
|----------|-----------|------|--------|------------|
"""
            for comp in phase_data['components']:
                priority_icon = "🔴" if comp.priority == 1 else "🟡" if comp.priority <= 2 else "🟢"
                content += f"| {priority_icon} P{comp.priority} | {comp.name} | {comp.type} | {comp.effort_estimate} | {comp.risk_level} |\n"
            
            content += "\n"
        
        if update_progress:
            await update_progress(85, status="Adding technology breakdown")
        
        content += """
---

## 🔧 Technology Breakdown

| Technology Type | Components | Percentage |
|----------------|------------|------------|
"""
        
        total_components = sum(executive_summary['technology_breakdown'].values())
        for tech_type, count in executive_summary['technology_breakdown'].items():
            percentage = (count / total_components * 100) if total_components > 0 else 0
            content += f"| {tech_type} | {count} | {percentage:.1f}% |\n"
        
        content += f"""
---

## 📈 Effort Breakdown

**Total Estimated Effort**: {summary.estimated_effort_days} days  
**Timeline**: {summary.timeline_estimate}  
**Team Size Recommendation**: {max(2, summary.estimated_effort_days // 60)} developers

### Effort Distribution
"""
        
        effort_breakdown = migration_analysis.get('effort_breakdown', {})
        for comp_type, breakdown in effort_breakdown.items():
            total_days = breakdown['total_effort'] // 8
            content += f"- **{comp_type}**: {total_days} days ({breakdown['components']} components)\n"
        
        content += f"""
---

## 🎯 Next Steps & Recommendations

### Immediate Actions (Next 30 Days)
1. **Stakeholder Alignment**: Present this analysis to key stakeholders
2. **Team Assembly**: Identify migration team members and technical leads
3. **Risk Mitigation**: Address critical and high-risk components first
4. **Environment Setup**: Prepare development and testing environments

### Phase 1 Preparation (Next 60 Days)
1. **Detailed Design**: Create detailed technical designs for Phase 1 components
2. **Proof of Concept**: Build POC for the most complex integrations
3. **Testing Strategy**: Define comprehensive testing approach
4. **Change Management**: Prepare business users for upcoming changes

### Success Criteria
- [ ] All critical risk components addressed
- [ ] Modern API architecture implemented
- [ ] Database modernization completed
- [ ] Integration testing passed
- [ ] User acceptance testing completed
- [ ] Performance benchmarks met

---

## 📋 Migration Checklist

### Pre-Migration
- [ ] Backup current system
- [ ] Document current business processes
- [ ] Set up monitoring and rollback procedures
- [ ] Train team on new technologies

### During Migration
- [ ] Implement components in priority order
- [ ] Continuous integration testing
- [ ] Regular stakeholder communication
- [ ] Monitor system performance

### Post-Migration
- [ ] Performance optimization
- [ ] Documentation updates
- [ ] Team knowledge transfer
- [ ] Support process establishment

---

*This migration analysis was generated by DocXP Enterprise Migration Platform. For questions or updates, please review the detailed technical documentation files.*
"""
        
        if update_progress:
            await update_progress(100, status="Migration summary completed")
        
        logger.info(f"Generated migration summary documentation: {len(content)} characters")
        return content
    
    async def _update_job_status(self, job_id: str, status: str):
        """Update job status in database"""
        query = update(DocumentationJob).where(
            DocumentationJob.job_id == job_id
        ).values(status=status)
        
        await self.db.execute(query)
        await self.db.commit()
    
    async def _update_job_completion(
        self,
        job_id: str,
        status: str,
        entities_count: int,
        business_rules_count: int,
        files_processed: int,
        output_path: str,
        processing_time: float
    ):
        """Update job with completion details"""
        query = update(DocumentationJob).where(
            DocumentationJob.job_id == job_id
        ).values(
            status=status,
            completed_at=datetime.utcnow(),
            entities_count=entities_count,
            business_rules_count=business_rules_count,
            files_processed=files_processed,
            output_path=output_path,
            processing_time_seconds=processing_time
        )
        
        # Execute with robust error handling for job completion
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Validate session is still active
                await self.db.execute(select(1))
                
                result = await self.db.execute(query)
                if result.rowcount == 0:
                    logger.error(f"🚨 CRITICAL: No job found to complete: {job_id}")
                    return
                    
                await self.db.commit()
                logger.info(f"✅ JOB COMPLETION UPDATED - {job_id}: Entities: {entities_count}, Rules: {business_rules_count}, Status: {status}")
                return  # Success
                
            except Exception as e:
                logger.error(f"❌ JOB COMPLETION UPDATE FAILED (attempt {attempt + 1}/{max_retries}) for {job_id}: {e}")
                
                if attempt < max_retries - 1:
                    try:
                        await self.db.rollback()
                        await asyncio.sleep(2)  # Longer delay for completion updates
                    except:
                        pass
                else:
                    logger.error(f"🚨 CRITICAL: Failed to update job completion after {max_retries} attempts!")
                    logger.error(f"📊 LOST METRICS - Job {job_id}: {entities_count} entities, {business_rules_count} rules, {files_processed} files")
                    
                    # Try one last simple status update
                    try:
                        await self.db.rollback()
                        simple_query = update(DocumentationJob).where(
                            DocumentationJob.job_id == job_id
                        ).values(status="completed", completed_at=datetime.utcnow())
                        
                        await self.db.execute(simple_query)
                        await self.db.commit()
                        logger.warning(f"⚠️ FALLBACK: Updated job {job_id} to completed status only (metrics lost)")
                    except Exception as fallback_error:
                        logger.critical(f"💥 COMPLETE FAILURE: Cannot update job {job_id} completion: {fallback_error}")
    
    async def _update_job_error(self, job_id: str, error_message: str):
        """Update job with error status"""
        query = update(DocumentationJob).where(
            DocumentationJob.job_id == job_id
        ).values(
            status="failed",
            completed_at=datetime.utcnow(),
            error_message=error_message
        )
        
        await self.db.execute(query)
        await self.db.commit()
