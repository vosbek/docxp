"""
Semantic Search API endpoints for vector-powered code analysis
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.services.semantic_ai_service import get_semantic_ai_service, SemanticAIService
from app.services.vector_service import get_vector_service, VectorService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/semantic", tags=["Semantic Search"])

# Request/Response Models
class SemanticSearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    collections: Optional[List[str]] = Field(
        default=["code_entities", "business_rules"], 
        description="Collections to search"
    )
    max_results: int = Field(default=10, ge=1, le=50, description="Maximum results to return")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Metadata filters")

class SimilarCodeRequest(BaseModel):
    code_content: str = Field(..., description="Code content to find similarities for")
    entity_type: Optional[str] = Field(default=None, description="Filter by entity type")
    max_results: int = Field(default=5, ge=1, le=20, description="Maximum results")

class MigrationPatternRequest(BaseModel):
    legacy_pattern: str = Field(..., description="Legacy pattern to migrate")
    technology_stack: str = Field(..., description="Current technology stack")
    business_context: Optional[str] = Field(default=None, description="Business context")

class CodeAnalysisRequest(BaseModel):
    code_content: str = Field(..., description="Code to analyze")
    file_path: str = Field(..., description="File path of the code")
    analysis_type: str = Field(default="comprehensive", description="Type of analysis")

class MigrationImpactRequest(BaseModel):
    component_path: str = Field(..., description="Component to analyze")
    target_technology: str = Field(..., description="Target technology")

class IndexRepositoryRequest(BaseModel):
    repository_data: Dict[str, Any] = Field(..., description="Repository data to index")

@router.post("/search")
async def semantic_search(
    request: SemanticSearchRequest,
    semantic_service: SemanticAIService = Depends(get_semantic_ai_service)
):
    """
    Perform semantic search across code entities and business rules
    """
    try:
        results = await semantic_service.semantic_code_search(
            search_query=request.query,
            filters=request.filters
        )
        
        return {
            "success": True,
            "data": results
        }
        
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/similar-code")
async def find_similar_code(
    request: SimilarCodeRequest,
    vector_service: VectorService = Depends(get_vector_service)
):
    """
    Find code entities similar to the provided code content
    """
    try:
        results = await vector_service.find_similar_code(
            code_content=request.code_content,
            entity_type=request.entity_type,
            n_results=request.max_results
        )
        
        return {
            "success": True,
            "data": {
                "query_code": request.code_content[:200] + "...",
                "similar_entities": results,
                "total_found": len(results)
            }
        }
        
    except Exception as e:
        logger.error(f"Similar code search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Similar code search failed: {str(e)}")

@router.post("/migration-recommendations")
async def get_migration_recommendations(
    request: MigrationPatternRequest,
    semantic_service: SemanticAIService = Depends(get_semantic_ai_service)
):
    """
    Get AI-powered migration recommendations based on similar patterns
    """
    try:
        recommendations = await semantic_service.find_migration_recommendations(
            legacy_pattern=request.legacy_pattern,
            technology_stack=request.technology_stack,
            business_context=request.business_context
        )
        
        return {
            "success": True,
            "data": recommendations
        }
        
    except Exception as e:
        logger.error(f"Migration recommendations failed: {e}")
        raise HTTPException(status_code=500, detail=f"Migration recommendations failed: {str(e)}")

@router.post("/analyze-code")
async def analyze_code_with_context(
    request: CodeAnalysisRequest,
    semantic_service: SemanticAIService = Depends(get_semantic_ai_service)
):
    """
    Analyze code with semantic context from similar examples
    """
    try:
        analysis = await semantic_service.analyze_code_with_context(
            code_content=request.code_content,
            file_path=request.file_path,
            analysis_type=request.analysis_type
        )
        
        return {
            "success": True,
            "data": analysis
        }
        
    except Exception as e:
        logger.error(f"Code analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Code analysis failed: {str(e)}")

@router.post("/migration-impact")
async def analyze_migration_impact(
    request: MigrationImpactRequest,
    semantic_service: SemanticAIService = Depends(get_semantic_ai_service)
):
    """
    Analyze the impact of migrating a specific component
    """
    try:
        impact_analysis = await semantic_service.analyze_migration_impact(
            component_path=request.component_path,
            target_technology=request.target_technology
        )
        
        return {
            "success": True,
            "data": impact_analysis
        }
        
    except Exception as e:
        logger.error(f"Migration impact analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Migration impact analysis failed: {str(e)}")

@router.post("/index-repository")
async def index_repository(
    request: IndexRepositoryRequest,
    semantic_service: SemanticAIService = Depends(get_semantic_ai_service)
):
    """
    Index repository content into vector database for semantic search
    """
    try:
        indexing_results = await semantic_service.index_repository_content(
            repository_data=request.repository_data
        )
        
        return {
            "success": True,
            "data": indexing_results
        }
        
    except Exception as e:
        logger.error(f"Repository indexing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Repository indexing failed: {str(e)}")

@router.get("/collections/stats")
async def get_collection_statistics(
    vector_service: VectorService = Depends(get_vector_service)
):
    """
    Get statistics about vector database collections
    """
    try:
        stats = await vector_service.get_collection_stats()
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"Collection stats failed: {e}")
        raise HTTPException(status_code=500, detail=f"Collection stats failed: {str(e)}")

@router.delete("/collections/{collection_name}")
async def clear_collection(
    collection_name: str,
    vector_service: VectorService = Depends(get_vector_service)
):
    """
    Clear all documents from a specific collection
    """
    try:
        success = await vector_service.clear_collection(collection_name)
        
        if success:
            return {
                "success": True,
                "message": f"Collection {collection_name} cleared successfully"
            }
        else:
            raise HTTPException(status_code=400, detail=f"Failed to clear collection {collection_name}")
        
    except Exception as e:
        logger.error(f"Clear collection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Clear collection failed: {str(e)}")

@router.get("/health")
async def semantic_search_health():
    """
    Health check for semantic search services
    """
    try:
        # Test vector service
        vector_service = await get_vector_service()
        stats = await vector_service.get_collection_stats()
        
        # Test semantic AI service
        semantic_service = await get_semantic_ai_service()
        
        return {
            "success": True,
            "status": "healthy",
            "services": {
                "vector_database": "operational",
                "semantic_ai": "operational",
                "collections": len(stats)
            },
            "collection_stats": stats
        }
        
    except Exception as e:
        logger.error(f"Semantic search health check failed: {e}")
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e)
        }