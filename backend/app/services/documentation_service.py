"""
Documentation generation service
"""

import os
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import hashlib
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.database import DocumentationJob, Repository
from app.models.schemas import DocumentationRequest, BusinessRule
from app.parsers.parser_factory import ParserFactory
from app.services.ai_service import ai_service_instance
from app.services.diagram_service import DiagramService

logger = logging.getLogger(__name__)

class DocumentationService:
    """Main service for documentation generation"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.parser_factory = ParserFactory()
        self.ai_service = ai_service_instance
        self.diagram_service = DiagramService()
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def generate_documentation(self, job_id: str, request: DocumentationRequest):
        """
        Generate documentation for a repository
        """
        start_time = datetime.utcnow()
        
        try:
            # Update job status to processing
            await self._update_job_status(job_id, "processing")
            
            # Validate repository
            if not os.path.exists(request.repository_path):
                raise Exception(f"Repository path does not exist: {request.repository_path}")
            
            # Step 1: Analyze repository structure
            logger.info(f"Analyzing repository: {request.repository_path}")
            repo_analysis = await self._analyze_repository(request.repository_path)
            
            # Step 2: Parse code files
            logger.info("Parsing code files...")
            entities = await self._parse_code_files(request)
            
            # Step 3: Extract business rules using AI
            logger.info("Extracting business rules...")
            business_rules = await self._extract_business_rules(entities, request)
            
            # Step 4: Generate documentation
            logger.info("Generating documentation...")
            documentation = await self._generate_documentation_content(
                entities, business_rules, request
            )
            
            # Step 5: Generate diagrams if requested
            diagrams = {}
            if request.include_diagrams:
                logger.info("Generating diagrams...")
                diagrams = await self._generate_diagrams(entities, request)
            
            # Step 6: Save documentation
            output_path = await self._save_documentation(
                documentation, diagrams, request, job_id
            )
            
            # Calculate processing time
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds()
            
            # Update job with results
            await self._update_job_completion(
                job_id=job_id,
                status="completed",
                entities_count=len(entities),
                business_rules_count=len(business_rules),
                files_processed=repo_analysis['total_files'],
                output_path=output_path,
                processing_time=processing_time
            )
            
            logger.info(f"Documentation generation completed for job {job_id}")
            
        except Exception as e:
            logger.error(f"Error generating documentation for job {job_id}: {e}")
            await self._update_job_error(job_id, str(e))

    
    async def _analyze_repository(self, repo_path: str) -> Dict[str, Any]:
        """Analyze repository structure"""
        analysis = {
            "total_files": 0,
            "total_lines": 0,
            "languages": {},
            "file_list": []
        }
        
        for root, dirs, files in os.walk(repo_path):
            # Skip common non-source directories
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv', 'venv']]
            
            for file in files:
                file_path = Path(root) / file
                
                # Skip non-source files
                if file_path.suffix in ['.pyc', '.class', '.exe', '.dll']:
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
                        analysis["total_lines"] += sum(1 for _ in f)
                except:
                    pass
        
        return analysis
    
    async def _parse_code_files(self, request: DocumentationRequest) -> List[Dict]:
        """Parse all code files in repository"""
        entities = []
        repo_path = Path(request.repository_path)
        
        # Get parser for each file
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv', 'venv']]
            
            for file in files:
                file_path = Path(root) / file
                
                # Get appropriate parser
                parser = self.parser_factory.get_parser(file_path)
                if parser:
                    try:
                        file_entities = await asyncio.get_event_loop().run_in_executor(
                            self.executor,
                            parser.parse,
                            file_path
                        )
                        entities.extend(file_entities)
                    except Exception as e:
                        logger.warning(f"Failed to parse {file_path}: {e}")
        
        return entities
    
    async def _extract_business_rules(
        self, 
        entities: List[Dict], 
        request: DocumentationRequest
    ) -> List[BusinessRule]:
        """Extract business rules using AI"""
        if not request.include_business_rules:
            return []
        
        rules = []
        
        # Group entities by file for context
        entities_by_file = {}
        for entity in entities:
            file_path = entity.get('file_path')
            if file_path not in entities_by_file:
                entities_by_file[file_path] = []
            entities_by_file[file_path].append(entity)
        
        # Process each file with AI
        for file_path, file_entities in entities_by_file.items():
            try:
                # Read file content
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Extract rules using AI
                file_rules = await self.ai_service.extract_business_rules(
                    code=content,
                    entities=file_entities,
                    keywords=request.keywords
                )
                rules.extend(file_rules)
                
            except Exception as e:
                logger.warning(f"Failed to extract rules from {file_path}: {e}")
        
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
        request: DocumentationRequest
    ) -> str:
        """Generate main README documentation"""
        
        # Use AI to generate comprehensive overview
        overview = await self.ai_service.generate_overview(
            entities=entities,
            business_rules=business_rules,
            depth=request.depth
        )
        
        readme = f"""# Repository Documentation

Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

## Overview

{overview}

## Statistics

- **Total Code Entities**: {len(entities)}
- **Classes**: {len([e for e in entities if e.get('type') == 'class'])}
- **Functions**: {len([e for e in entities if e.get('type') == 'function'])}
- **Business Rules Identified**: {len(business_rules)}

## Documentation Index

- [API Documentation](API.md)
- [Business Rules](BUSINESS_RULES.md)
- [Architecture](ARCHITECTURE.md)

## Repository Structure

```
{await self._generate_tree_structure(request.repository_path)}
```

## Key Components

{await self._generate_component_summary(entities)}

## Dependencies

{await self._generate_dependency_list(entities)}
"""
        return readme
    
    async def _generate_api_documentation(self, entities: List[Dict]) -> str:
        """Generate API documentation"""
        api_doc = "# API Documentation\n\n"
        
        # Group by file
        by_file = {}
        for entity in entities:
            file_path = entity.get('file_path', 'unknown')
            if file_path not in by_file:
                by_file[file_path] = []
            by_file[file_path].append(entity)
        
        for file_path, file_entities in sorted(by_file.items()):
            api_doc += f"\n## {file_path}\n\n"
            
            for entity in file_entities:
                entity_type = entity.get('type', 'unknown')
                name = entity.get('name', 'unnamed')
                docstring = entity.get('docstring', '')
                
                api_doc += f"### {entity_type.title()}: `{name}`\n\n"
                if docstring:
                    api_doc += f"{docstring}\n\n"
                
                # Add parameters if function
                if entity_type == 'function' and entity.get('parameters'):
                    api_doc += "**Parameters:**\n"
                    for param in entity.get('parameters', []):
                        api_doc += f"- `{param}`\n"
                    api_doc += "\n"
        
        return api_doc

    
    async def _generate_business_rules_doc(self, rules: List[BusinessRule]) -> str:
        """Generate business rules documentation"""
        doc = "# Business Rules Documentation\n\n"
        
        # Group by category
        by_category = {}
        for rule in rules:
            category = rule.category
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(rule)
        
        for category, category_rules in sorted(by_category.items()):
            doc += f"\n## {category}\n\n"
            
            for rule in category_rules:
                doc += f"### {rule.id}\n\n"
                doc += f"**Description:** {rule.description}\n\n"
                doc += f"**Confidence Score:** {rule.confidence_score:.2%}\n\n"
                doc += f"**Code Reference:** `{rule.code_reference}`\n\n"
                
                if rule.validation_logic:
                    doc += f"**Validation Logic:**\n```\n{rule.validation_logic}\n```\n\n"
                
                if rule.related_entities:
                    doc += f"**Related Components:** {', '.join(rule.related_entities)}\n\n"
        
        return doc
    
    async def _generate_architecture_doc(
        self, 
        entities: List[Dict], 
        request: DocumentationRequest
    ) -> str:
        """Generate architecture documentation"""
        return await self.ai_service.generate_architecture_doc(entities, request.depth)
    
    async def _generate_diagrams(
        self,
        entities: List[Dict],
        request: DocumentationRequest
    ) -> Dict[str, str]:
        """Generate Mermaid diagrams"""
        diagrams = {}
        
        # Class diagram
        diagrams['class_diagram.mmd'] = await self.diagram_service.generate_class_diagram(
            entities
        )
        
        # Flow diagram
        diagrams['flow_diagram.mmd'] = await self.diagram_service.generate_flow_diagram(
            entities
        )
        
        # Architecture diagram
        diagrams['architecture.mmd'] = await self.diagram_service.generate_architecture_diagram(
            entities
        )
        
        return diagrams
    
    async def _save_documentation(
        self,
        documentation: Dict[str, str],
        diagrams: Dict[str, str],
        request: DocumentationRequest,
        job_id: str
    ) -> str:
        """Save documentation to files"""
        output_dir = Path(request.output_path) / job_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save documentation files
        for filename, content in documentation.items():
            file_path = output_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # Save diagrams
        if diagrams:
            diagrams_dir = output_dir / 'diagrams'
            diagrams_dir.mkdir(exist_ok=True)
            
            for filename, content in diagrams.items():
                file_path = diagrams_dir / filename
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
        
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
        
        await self.db.execute(query)
        await self.db.commit()
    
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
