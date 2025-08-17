"""
Semantic AI Service combining ChromaDB vector search with AWS Bedrock
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from app.services.vector_service import get_vector_service
from app.services.ai_service import AIService
from app.core.config import settings

logger = logging.getLogger(__name__)

class SemanticAIService:
    """
    Enhanced AI service that combines semantic vector search with AWS Bedrock
    for intelligent legacy migration analysis and recommendations.
    """
    
    def __init__(self):
        self.vector_service = None
        self.ai_service = AIService()
        # Services will be initialized on first use
    
    async def _initialize(self):
        """Initialize the semantic AI service"""
        try:
            self.vector_service = await get_vector_service()
            logger.info("Semantic AI service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize semantic AI service: {e}")
            raise
    
    async def analyze_code_with_context(
        self,
        code_content: str,
        file_path: str,
        analysis_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Analyze code with semantic context from similar examples
        """
        try:
            # Initialize services if not already done
            if self.vector_service is None:
                await self._initialize()
            # Find similar code patterns for context
            similar_code = await self.vector_service.find_similar_code(
                code_content=code_content,
                n_results=3
            )
            
            # Build context-aware prompt
            context_info = ""
            if similar_code:
                context_info = "\n\nSimilar code patterns found in codebase:\n"
                for i, similar in enumerate(similar_code[:2], 1):
                    context_info += f"\n{i}. File: {similar['metadata'].get('file_path', 'Unknown')}"
                    context_info += f"\n   Type: {similar['metadata'].get('type', 'Unknown')}"
                    context_info += f"\n   Similarity: {similar['similarity_score']:.2f}"
                    if similar['metadata'].get('description'):
                        context_info += f"\n   Description: {similar['metadata']['description']}"
            
            # Create enhanced prompt
            prompt = f"""
            Analyze the following {analysis_type} code from file: {file_path}
            
            Code to analyze:
            ```
            {code_content}
            ```
            
            {context_info}
            
            Please provide:
            1. **Code Structure Analysis**: Classes, methods, dependencies
            2. **Legacy Pattern Detection**: Identify outdated patterns (Struts, CORBA, etc.)
            3. **Business Logic Extraction**: Key business rules and workflows
            4. **Migration Recommendations**: Specific modernization suggestions
            5. **Risk Assessment**: Potential migration risks and complexity
            6. **Similar Pattern Context**: How this relates to similar code in the codebase
            
            Format as structured JSON with clear sections.
            """
            
            # Get AI analysis
            ai_response = await self.ai_service.analyze_code(
                code_content, 
                file_path,
                additional_context=prompt
            )
            
            # Enhance response with vector context
            enhanced_response = {
                **ai_response,
                "semantic_context": {
                    "similar_patterns_found": len(similar_code),
                    "context_sources": [
                        {
                            "file": item['metadata'].get('file_path'),
                            "similarity": item['similarity_score'],
                            "type": item['metadata'].get('type')
                        } for item in similar_code
                    ]
                },
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
            return enhanced_response
            
        except Exception as e:
            logger.error(f"Code analysis with context failed: {e}")
            return {"error": str(e), "analysis_timestamp": datetime.utcnow().isoformat()}
    
    async def find_migration_recommendations(
        self,
        legacy_pattern: str,
        technology_stack: str,
        business_context: str = None
    ) -> Dict[str, Any]:
        """
        Find migration recommendations based on similar patterns and AI analysis
        """
        try:
            # Search for similar migration patterns
            migration_patterns = await self.vector_service.find_migration_patterns(
                legacy_pattern=legacy_pattern,
                technology_stack=technology_stack,
                n_results=5
            )
            
            # Build context from migration patterns
            pattern_context = ""
            if migration_patterns:
                pattern_context = "\n\nSimilar migration patterns:\n"
                for i, pattern in enumerate(migration_patterns, 1):
                    metadata = pattern['metadata']
                    pattern_context += f"\n{i}. {metadata.get('legacy_pattern', 'Unknown pattern')}"
                    pattern_context += f"\n   Modern equivalent: {metadata.get('modern_equivalent', 'Not specified')}"
                    pattern_context += f"\n   Complexity: {metadata.get('complexity_score', 'Unknown')}"
                    pattern_context += f"\n   Description: {metadata.get('description', 'No description')}"
            
            # Create AI prompt for migration recommendations
            prompt = f"""
            Provide migration recommendations for the following legacy pattern:
            
            **Legacy Pattern**: {legacy_pattern}
            **Technology Stack**: {technology_stack}
            **Business Context**: {business_context or 'Not specified'}
            
            {pattern_context}
            
            Please provide:
            1. **Migration Strategy**: Step-by-step approach
            2. **Modern Alternatives**: Recommended technologies and frameworks
            3. **Risk Assessment**: Potential challenges and mitigation strategies
            4. **Implementation Timeline**: Estimated effort and phases
            5. **Business Impact**: Effects on operations during migration
            6. **Testing Strategy**: How to validate the migration
            7. **Rollback Plan**: Safety measures if migration fails
            
            Base recommendations on the similar patterns found and industry best practices.
            Format as structured JSON.
            """
            
            # Get AI recommendations
            ai_response = await self.ai_service.generate_recommendations(prompt)
            
            # Structure the response
            recommendations = {
                "legacy_pattern": legacy_pattern,
                "technology_stack": technology_stack,
                "business_context": business_context,
                "ai_recommendations": ai_response,
                "similar_patterns": [
                    {
                        "pattern": pattern['metadata'].get('legacy_pattern'),
                        "modern_equivalent": pattern['metadata'].get('modern_equivalent'),
                        "complexity": pattern['metadata'].get('complexity_score'),
                        "similarity_score": pattern['similarity_score']
                    } for pattern in migration_patterns
                ],
                "confidence_score": len(migration_patterns) / 5.0,  # Based on available patterns
                "generated_at": datetime.utcnow().isoformat()
            }
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Migration recommendations failed: {e}")
            return {"error": str(e), "generated_at": datetime.utcnow().isoformat()}
    
    async def semantic_code_search(
        self,
        search_query: str,
        filters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Perform semantic search across code entities and business rules
        """
        try:
            # Search across different collections
            search_results = {}
            
            # Search code entities
            code_results = await self.vector_service.semantic_search(
                query=search_query,
                collection_name="code_entities",
                n_results=10,
                filter_metadata=filters
            )
            search_results["code_entities"] = code_results
            
            # Search business rules
            business_results = await self.vector_service.semantic_search(
                query=search_query,
                collection_name="business_rules",
                n_results=5,
                filter_metadata=filters
            )
            search_results["business_rules"] = business_results
            
            # Search documentation
            doc_results = await self.vector_service.semantic_search(
                query=search_query,
                collection_name="documentation",
                n_results=5,
                filter_metadata=filters
            )
            search_results["documentation"] = doc_results
            
            # Aggregate and rank results
            all_results = []
            for collection, results in search_results.items():
                for result in results:
                    result["source_collection"] = collection
                    all_results.append(result)
            
            # Sort by similarity score
            all_results.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
            
            # Generate AI summary of search results
            if all_results:
                summary_prompt = f"""
                Summarize the search results for query: "{search_query}"
                
                Found {len(all_results)} relevant items across code entities, business rules, and documentation.
                
                Top results:
                {json.dumps([{
                    'content': r.get('content', '')[:200] + '...',
                    'source': r.get('source_collection'),
                    'score': r.get('similarity_score')
                } for r in all_results[:5]], indent=2)}
                
                Provide a brief summary of what was found and key insights.
                """
                
                ai_summary = await self.ai_service.generate_summary(summary_prompt)
            else:
                ai_summary = "No relevant results found for the search query."
            
            return {
                "query": search_query,
                "total_results": len(all_results),
                "results_by_collection": {
                    collection: len(results) 
                    for collection, results in search_results.items()
                },
                "top_results": all_results[:10],
                "ai_summary": ai_summary,
                "search_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return {"error": str(e), "search_timestamp": datetime.utcnow().isoformat()}
    
    async def analyze_migration_impact(
        self,
        component_path: str,
        target_technology: str
    ) -> Dict[str, Any]:
        """
        Analyze the impact of migrating a specific component
        """
        try:
            # Find all related code entities
            related_code = await self.vector_service.semantic_search(
                query=f"component dependencies {component_path}",
                collection_name="code_entities",
                n_results=20
            )
            
            # Find business rules that might be affected
            affected_rules = await self.vector_service.semantic_search(
                query=f"business logic {component_path}",
                collection_name="business_rules",
                n_results=10
            )
            
            # Analyze dependencies and create impact map
            dependency_map = {}
            for code_item in related_code:
                file_path = code_item['metadata'].get('file_path', '')
                if file_path not in dependency_map:
                    dependency_map[file_path] = []
                dependency_map[file_path].append({
                    'entity': code_item['metadata'].get('name', 'Unknown'),
                    'type': code_item['metadata'].get('type', 'Unknown'),
                    'similarity': code_item['similarity_score']
                })
            
            # Generate AI impact analysis
            impact_prompt = f"""
            Analyze the migration impact for component: {component_path}
            Target technology: {target_technology}
            
            Related code entities found: {len(related_code)}
            Affected business rules: {len(affected_rules)}
            
            Dependencies detected:
            {json.dumps(list(dependency_map.keys())[:10], indent=2)}
            
            Business rules that may be affected:
            {json.dumps([rule['metadata'].get('description', '')[:100] for rule in affected_rules[:5]], indent=2)}
            
            Please provide:
            1. **Impact Scope**: What components will be affected
            2. **Risk Level**: High/Medium/Low with justification
            3. **Breaking Changes**: Potential compatibility issues
            4. **Testing Requirements**: What needs to be tested
            5. **Migration Order**: Sequence of changes needed
            6. **Rollback Complexity**: Difficulty of reverting changes
            
            Format as structured analysis.
            """
            
            ai_impact_analysis = await self.ai_service.analyze_impact(impact_prompt)
            
            return {
                "component_path": component_path,
                "target_technology": target_technology,
                "related_entities": len(related_code),
                "affected_business_rules": len(affected_rules),
                "dependency_map": dependency_map,
                "affected_rules_summary": [
                    {
                        "rule_id": rule['metadata'].get('rule_id'),
                        "description": rule['metadata'].get('description', '')[:200],
                        "impact_score": rule['similarity_score']
                    } for rule in affected_rules
                ],
                "ai_impact_analysis": ai_impact_analysis,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Migration impact analysis failed: {e}")
            return {"error": str(e), "analysis_timestamp": datetime.utcnow().isoformat()}
    
    async def index_repository_content(
        self,
        repository_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Index repository content into vector database for semantic search
        """
        try:
            indexing_results = {
                "code_entities_indexed": 0,
                "business_rules_indexed": 0,
                "errors": []
            }
            
            # Index code entities
            if "code_entities" in repository_data:
                entities_to_index = []
                
                for entity in repository_data["code_entities"]:
                    try:
                        # Prepare entity for vector indexing
                        entity_data = {
                            "id": entity.get("id"),
                            "content": f"""
                            Name: {entity.get('name', '')}
                            Type: {entity.get('type', '')}
                            File: {entity.get('file_path', '')}
                            Code: {entity.get('source_code', '')}
                            Documentation: {entity.get('docstring', '')}
                            """,
                            "metadata": {
                                "entity_id": entity.get("id"),
                                "name": entity.get("name"),
                                "type": entity.get("type"),
                                "file_path": entity.get("file_path"),
                                "language": entity.get("language"),
                                "complexity": entity.get("complexity", 0),
                                "indexed_at": datetime.utcnow().isoformat()
                            },
                            "collection_type": "code_entities"
                        }
                        entities_to_index.append(entity_data)
                        
                    except Exception as e:
                        indexing_results["errors"].append(f"Entity indexing error: {e}")
                
                # Bulk index entities
                if entities_to_index:
                    bulk_results = await self.vector_service.bulk_add_entities(entities_to_index)
                    indexing_results["code_entities_indexed"] = bulk_results["success"]
            
            # Index business rules
            if "business_rules" in repository_data:
                rules_to_index = []
                
                for rule in repository_data["business_rules"]:
                    try:
                        rule_data = {
                            "id": rule.get("rule_id"),
                            "content": f"""
                            Rule: {rule.get('description', '')}
                            Plain English: {rule.get('plain_english', '')}
                            Context: {rule.get('business_context', '')}
                            Implementation: {rule.get('implementation_details', '')}
                            """,
                            "metadata": {
                                "rule_id": rule.get("rule_id"),
                                "description": rule.get("description"),
                                "category": rule.get("category"),
                                "confidence_score": rule.get("confidence_score", 0),
                                "business_impact": rule.get("business_impact"),
                                "indexed_at": datetime.utcnow().isoformat()
                            },
                            "collection_type": "business_rules"
                        }
                        rules_to_index.append(rule_data)
                        
                    except Exception as e:
                        indexing_results["errors"].append(f"Rule indexing error: {e}")
                
                # Bulk index rules
                if rules_to_index:
                    bulk_results = await self.vector_service.bulk_add_entities(rules_to_index)
                    indexing_results["business_rules_indexed"] = bulk_results["success"]
            
            logger.info(f"Repository indexing completed: {indexing_results}")
            return indexing_results
            
        except Exception as e:
            logger.error(f"Repository indexing failed: {e}")
            return {"error": str(e)}

# Global semantic AI service instance
semantic_ai_service = SemanticAIService()

async def get_semantic_ai_service() -> SemanticAIService:
    """Get semantic AI service instance"""
    return semantic_ai_service