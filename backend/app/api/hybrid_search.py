"""
Hybrid Search API for V1 Local-First Architecture

RRF (BM25 + k-NN) search endpoints with grounded citations
Supporting the golden questions demo scenario and enterprise search needs.
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.services.hybrid_search_service import get_hybrid_search_service, RRFHybridSearchService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/search", tags=["V1 Hybrid Search"])

# Request/Response Models
class HybridSearchRequest(BaseModel):
    query: str = Field(..., description="Search query text", min_length=1, max_length=1000)
    repo_filters: Optional[List[str]] = Field(
        default=None, 
        description="Repository IDs to filter by",
        max_items=50
    )
    commit_filters: Optional[List[str]] = Field(
        default=None,
        description="Commit hashes to filter by", 
        max_items=20
    )
    file_types: Optional[List[str]] = Field(
        default=None,
        description="File types/extensions to filter by (e.g., ['java', 'jsp', 'sql'])",
        max_items=20
    )
    max_results: int = Field(
        default=20, 
        ge=1, 
        le=100, 
        description="Maximum results to return"
    )
    bm25_boost: float = Field(
        default=1.0,
        ge=0.1,
        le=5.0,
        description="Boost factor for BM25 text search"
    )
    knn_boost: float = Field(
        default=1.0,
        ge=0.1, 
        le=5.0,
        description="Boost factor for k-NN vector search"
    )

class RepositorySearchRequest(BaseModel):
    query: str = Field(..., description="Search query text")
    repo_id: str = Field(..., description="Repository ID to search within")
    max_results: int = Field(default=10, ge=1, le=50)

class CommitSearchRequest(BaseModel):
    query: str = Field(..., description="Search query text")
    commit_hash: str = Field(..., description="Commit hash to search within") 
    max_results: int = Field(default=10, ge=1, le=50)

class GoldenQuestionRequest(BaseModel):
    question: str = Field(..., description="Golden question to search for")
    expected_repos: Optional[List[str]] = Field(
        default=None,
        description="Expected repositories that should contain the answer"
    )
    max_results: int = Field(default=3, ge=1, le=10, description="Top-N results for accuracy measurement")

@router.post("/hybrid")
async def hybrid_search(
    request: HybridSearchRequest,
    search_service: RRFHybridSearchService = Depends(get_hybrid_search_service)
):
    """
    Perform RRF hybrid search combining BM25 and k-NN vector search
    
    Returns results with grounded citations and performance metrics.
    Implements GPT-5 specified RRF parameters (k=60, w_bm25=1.2, w_knn=1.0).
    """
    try:
        logger.info(f"Hybrid search request: '{request.query[:50]}...'")
        
        results = await search_service.hybrid_search(
            query=request.query,
            repo_filters=request.repo_filters,
            commit_filters=request.commit_filters,
            file_types=request.file_types,
            max_results=request.max_results,
            bm25_boost=request.bm25_boost,
            knn_boost=request.knn_boost
        )
        
        return {
            "success": True,
            "data": results
        }
        
    except Exception as e:
        logger.error(f"Hybrid search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/repository")
async def repository_search(
    request: RepositorySearchRequest,
    search_service: RRFHybridSearchService = Depends(get_hybrid_search_service)
):
    """
    Search within a specific repository
    
    Optimized for repository-scoped searches with full hybrid RRF functionality.
    """
    try:
        results = await search_service.repository_search(
            query=request.query,
            repo_id=request.repo_id,
            max_results=request.max_results
        )
        
        return {
            "success": True,
            "data": results
        }
        
    except Exception as e:
        logger.error(f"Repository search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Repository search failed: {str(e)}")

@router.post("/commit")
async def commit_search(
    request: CommitSearchRequest,
    search_service: RRFHybridSearchService = Depends(get_hybrid_search_service)
):
    """
    Search within a specific commit
    
    Useful for change analysis and commit-specific code exploration.
    """
    try:
        results = await search_service.commit_search(
            query=request.query,
            commit_hash=request.commit_hash,
            max_results=request.max_results
        )
        
        return {
            "success": True,
            "data": results
        }
        
    except Exception as e:
        logger.error(f"Commit search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Commit search failed: {str(e)}")

@router.post("/golden-questions")
async def golden_questions_search(
    request: GoldenQuestionRequest,
    search_service: RRFHybridSearchService = Depends(get_hybrid_search_service)
):
    """
    Search optimized for golden questions regression testing
    
    Designed for demo questions like "Where does Specified Amount come from?"
    with emphasis on finding grounded citations in code files.
    
    Target: ≥8/10 questions should have correct answer in Top-3 results.
    """
    try:
        results = await search_service.golden_questions_search(
            question=request.question,
            expected_repos=request.expected_repos,
            max_results=request.max_results
        )
        
        return {
            "success": True,
            "data": results,
            "testing_metadata": {
                "target_accuracy": "top_3_contains_answer",
                "regression_threshold": "8_of_10_questions",
                "optimization": "code_files_preferred"
            }
        }
        
    except Exception as e:
        logger.error(f"Golden questions search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Golden questions search failed: {str(e)}")

@router.get("/health")
async def search_health_check(
    search_service: RRFHybridSearchService = Depends(get_hybrid_search_service)
):
    """
    Health check for V1 hybrid search system
    
    Tests OpenSearch, Bedrock, and RRF configuration.
    """
    try:
        health_status = await search_service.health_check()
        
        if health_status["status"] == "healthy":
            return {
                "success": True,
                "status": "healthy",
                "data": health_status
            }
        else:
            return {
                "success": False,
                "status": "unhealthy", 
                "data": health_status
            }
        
    except Exception as e:
        logger.error(f"Search health check failed: {e}")
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e)
        }

@router.get("/metrics")
async def search_metrics():
    """
    Get search performance metrics and SLO status
    
    Returns Prometheus metrics and performance validation.
    """
    try:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        
        metrics_data = generate_latest()
        
        return {
            "success": True,
            "metrics_format": "prometheus",
            "data": metrics_data.decode('utf-8')
        }
        
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics collection failed: {str(e)}")

# Convenience endpoints for UI integration
@router.get("/quick-search")
async def quick_search(
    q: str = Query(..., description="Search query", min_length=1),
    repos: Optional[str] = Query(None, description="Comma-separated repository IDs"),
    types: Optional[str] = Query(None, description="Comma-separated file types"),
    limit: int = Query(10, ge=1, le=50, description="Result limit"),
    search_service: RRFHybridSearchService = Depends(get_hybrid_search_service)
):
    """
    Quick search endpoint for simple GET requests
    
    Convenient for frontend integration and testing.
    """
    try:
        # Parse comma-separated parameters
        repo_filters = repos.split(",") if repos else None
        file_types = types.split(",") if types else None
        
        results = await search_service.hybrid_search(
            query=q,
            repo_filters=repo_filters,
            file_types=file_types,
            max_results=limit
        )
        
        return {
            "success": True,
            "data": results
        }
        
    except Exception as e:
        logger.error(f"Quick search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Quick search failed: {str(e)}")

@router.get("/demo-questions")
async def get_demo_questions():
    """
    Get predefined demo questions for testing the golden questions functionality
    
    Returns sample questions that showcase the system's capabilities.
    """
    demo_questions = [
        {
            "id": "jsp_el_demo",
            "question": "Where does Specified Amount come from?",
            "description": "Traces JSP EL expression to Java source",
            "expected_files": ["*.jsp", "*.java", "*.sql"],
            "category": "jsp_el_tracing"
        },
        {
            "id": "struts_action_demo", 
            "question": "How is customer data validated in the registration form?",
            "description": "Traces Struts action to validation logic",
            "expected_files": ["*.java", "*.xml", "*.jsp"],
            "category": "struts_validation"
        },
        {
            "id": "sql_query_demo",
            "question": "What tables are used for customer order processing?",
            "description": "Finds SQL queries and table relationships",
            "expected_files": ["*.sql", "*.java"],
            "category": "sql_analysis"
        },
        {
            "id": "business_logic_demo",
            "question": "How is the discount calculation implemented?",
            "description": "Traces business logic across multiple layers",
            "expected_files": ["*.java", "*.jsp", "*.js"],
            "category": "business_logic"
        },
        {
            "id": "config_demo",
            "question": "Where are database connection settings configured?",
            "description": "Finds configuration files and properties",
            "expected_files": ["*.xml", "*.properties", "*.java"],
            "category": "configuration"
        }
    ]
    
    return {
        "success": True,
        "data": {
            "demo_questions": demo_questions,
            "total_questions": len(demo_questions),
            "usage": "Use these questions with /golden-questions endpoint for testing"
        }
    }