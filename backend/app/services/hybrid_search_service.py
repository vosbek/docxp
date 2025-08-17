"""
RRF Hybrid Search Service for V1 Local-First Architecture

Implements BM25 + k-NN vector search with Reciprocal Rank Fusion (RRF)
as specified by GPT-5 recommendations:
- k=60, w_bm25=1.2, w_knn=1.0
- Repository and commit filtering
- Citation metadata with grounded responses
- Performance targets: p50 < 700ms, p95 < 1.2s
"""

import asyncio
import json
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import hashlib

import boto3
from opensearchpy import AsyncOpenSearch, RequestError
from botocore.exceptions import ClientError
from prometheus_client import Counter, Histogram, Gauge

from app.core.config import settings
from app.core.opensearch_setup import get_opensearch_client, get_embedding_dimension

logger = logging.getLogger(__name__)

# Prometheus metrics
SEARCH_REQUESTS = Counter('docxp_search_requests_total', 'Total search requests', ['search_type'])
SEARCH_LATENCY = Histogram('docxp_search_duration_seconds', 'Search request duration', ['search_type'])
SEARCH_RESULTS = Histogram('docxp_search_results_count', 'Number of search results returned', ['search_type'])
RRF_FUSION_LATENCY = Histogram('docxp_rrf_fusion_duration_seconds', 'RRF fusion duration')
BEDROCK_EMBED_LATENCY = Histogram('docxp_bedrock_embed_duration_seconds', 'Bedrock embedding generation duration')

class RRFHybridSearchService:
    """
    OpenSearch-based hybrid search service with RRF fusion
    
    Combines BM25 text search and k-NN vector search for optimal precision.
    Implements GPT-5 specified parameters and grounded citations.
    """
    
    def __init__(self):
        self.opensearch_client: Optional[AsyncOpenSearch] = None
        self.bedrock_client: Optional[boto3.client] = None
        self.embedding_dimension: Optional[int] = None
        self.index_name = getattr(settings, 'OPENSEARCH_INDEX_NAME', 'docxp_chunks')
        
        # RRF parameters as specified by GPT-5
        self.rrf_k = getattr(settings, 'RRF_K', 60)
        self.rrf_bm25_weight = getattr(settings, 'RRF_BM25_WEIGHT', 1.2)
        self.rrf_knn_weight = getattr(settings, 'RRF_KNN_WEIGHT', 1.0)
        
        # Performance targets
        self.target_p50_ms = getattr(settings, 'TARGET_SEARCH_LATENCY_P50_MS', 700)
        self.target_p95_ms = getattr(settings, 'TARGET_SEARCH_LATENCY_P95_MS', 1200)
        
        # Initialize clients
        asyncio.create_task(self._initialize_clients())
    
    async def _initialize_clients(self):
        """Initialize OpenSearch and Bedrock clients"""
        try:
            self.opensearch_client = await get_opensearch_client()
            self.embedding_dimension = get_embedding_dimension()
            
            # Initialize Bedrock client for embeddings
            self.bedrock_client = boto3.client(
                'bedrock-runtime',
                region_name=getattr(settings, 'AWS_REGION', 'us-east-1')
            )
            
            logger.info(f"✅ RRF Hybrid Search initialized with {self.embedding_dimension}D embeddings")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize RRF Hybrid Search: {e}")
            raise
    
    async def hybrid_search(
        self,
        query: str,
        repo_filters: Optional[List[str]] = None,
        commit_filters: Optional[List[str]] = None,
        file_types: Optional[List[str]] = None,
        max_results: int = 20,
        bm25_boost: float = 1.0,
        knn_boost: float = 1.0
    ) -> Dict[str, Any]:
        """
        Perform hybrid search with RRF fusion
        
        Args:
            query: Search query text
            repo_filters: List of repository IDs to filter by
            commit_filters: List of commit hashes to filter by  
            file_types: List of file extensions/types to filter by
            max_results: Maximum results to return (default 20)
            bm25_boost: Boost factor for BM25 results
            knn_boost: Boost factor for k-NN results
            
        Returns:
            Dict containing search results with citations and performance metrics
        """
        start_time = time.time()
        search_id = hashlib.md5(f"{query}{time.time()}".encode()).hexdigest()[:8]
        
        try:
            SEARCH_REQUESTS.labels(search_type='hybrid').inc()
            logger.info(f"🔍 Starting hybrid search [{search_id}]: '{query[:50]}...'")
            
            # Ensure clients are initialized
            if not self.opensearch_client:
                await self._initialize_clients()
            
            # Generate query embedding for k-NN search
            embed_start = time.time()
            query_embedding = await self._generate_embedding(query)
            BEDROCK_EMBED_LATENCY.observe(time.time() - embed_start)
            
            # Build OpenSearch filters
            filters = self._build_filters(repo_filters, commit_filters, file_types)
            
            # Execute BM25 and k-NN searches in parallel
            bm25_task = self._bm25_search(query, filters, max_results * 2, bm25_boost)
            knn_task = self._knn_search(query_embedding, filters, max_results * 2, knn_boost)
            
            bm25_results, knn_results = await asyncio.gather(bm25_task, knn_task)
            
            # Apply RRF fusion
            fusion_start = time.time()
            fused_results = self._apply_rrf_fusion(bm25_results, knn_results, max_results)
            RRF_FUSION_LATENCY.observe(time.time() - fusion_start)
            
            # Enhance results with citation metadata
            enhanced_results = await self._enhance_with_citations(fused_results)
            
            # Calculate performance metrics
            total_time_ms = (time.time() - start_time) * 1000
            SEARCH_LATENCY.labels(search_type='hybrid').observe(time.time() - start_time)
            SEARCH_RESULTS.labels(search_type='hybrid').observe(len(enhanced_results))
            
            # Performance validation
            performance_status = self._validate_performance(total_time_ms)
            
            logger.info(f"✅ Hybrid search [{search_id}] completed in {total_time_ms:.1f}ms, {len(enhanced_results)} results")
            
            return {
                "search_id": search_id,
                "query": query,
                "results": enhanced_results,
                "total_results": len(enhanced_results),
                "performance": {
                    "total_time_ms": total_time_ms,
                    "meets_slo": performance_status["meets_slo"],
                    "target_p50_ms": self.target_p50_ms,
                    "target_p95_ms": self.target_p95_ms
                },
                "fusion_details": {
                    "bm25_results": len(bm25_results),
                    "knn_results": len(knn_results),
                    "rrf_k": self.rrf_k,
                    "bm25_weight": self.rrf_bm25_weight,
                    "knn_weight": self.rrf_knn_weight
                },
                "filters_applied": {
                    "repositories": repo_filters,
                    "commits": commit_filters,
                    "file_types": file_types
                }
            }
            
        except Exception as e:
            error_time_ms = (time.time() - start_time) * 1000
            logger.error(f"❌ Hybrid search [{search_id}] failed after {error_time_ms:.1f}ms: {e}")
            raise
    
    async def _bm25_search(
        self,
        query: str,
        filters: Dict[str, Any],
        max_results: int,
        boost: float = 1.0
    ) -> List[Dict[str, Any]]:
        """Perform BM25 text search"""
        try:
            search_body = {
                "size": max_results,
                "query": {
                    "bool": {
                        "must": [
                            {
                                "multi_match": {
                                    "query": query,
                                    "fields": ["content^2", "path", "lang", "kind"],
                                    "type": "best_fields",
                                    "boost": boost
                                }
                            }
                        ],
                        "filter": filters["filter"] if filters else []
                    }
                },
                "_source": ["content", "path", "repo_id", "commit", "lang", "kind", "start", "end", "tool", "content_hash"],
                "highlight": {
                    "fields": {
                        "content": {
                            "fragment_size": 150,
                            "number_of_fragments": 3,
                            "pre_tags": ["<mark>"],
                            "post_tags": ["</mark>"]
                        }
                    }
                }
            }
            
            response = await self.opensearch_client.search(
                index=self.index_name,
                body=search_body
            )
            
            results = []
            for hit in response["hits"]["hits"]:
                result = {
                    "id": hit["_id"],
                    "score": hit["_score"],
                    "source": hit["_source"],
                    "highlight": hit.get("highlight", {}),
                    "search_type": "bm25"
                }
                results.append(result)
            
            logger.debug(f"BM25 search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"BM25 search failed: {e}")
            return []
    
    async def _knn_search(
        self,
        query_embedding: List[float],
        filters: Dict[str, Any],
        max_results: int,
        boost: float = 1.0
    ) -> List[Dict[str, Any]]:
        """Perform k-NN vector search"""
        try:
            search_body = {
                "size": max_results,
                "query": {
                    "bool": {
                        "must": [
                            {
                                "knn": {
                                    "embedding": {
                                        "vector": query_embedding,
                                        "k": max_results,
                                        "boost": boost
                                    }
                                }
                            }
                        ],
                        "filter": filters["filter"] if filters else []
                    }
                },
                "_source": ["content", "path", "repo_id", "commit", "lang", "kind", "start", "end", "tool", "content_hash"]
            }
            
            response = await self.opensearch_client.search(
                index=self.index_name,
                body=search_body
            )
            
            results = []
            for hit in response["hits"]["hits"]:
                result = {
                    "id": hit["_id"],
                    "score": hit["_score"],
                    "source": hit["_source"],
                    "search_type": "knn"
                }
                results.append(result)
            
            logger.debug(f"k-NN search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"k-NN search failed: {e}")
            return []
    
    def _apply_rrf_fusion(
        self,
        bm25_results: List[Dict[str, Any]],
        knn_results: List[Dict[str, Any]],
        max_results: int
    ) -> List[Dict[str, Any]]:
        """
        Apply Reciprocal Rank Fusion (RRF) with GPT-5 specified parameters
        
        RRF Score = w_bm25 * (1 / (k + rank_bm25)) + w_knn * (1 / (k + rank_knn))
        """
        try:
            # Create document score maps
            bm25_ranks = {result["id"]: rank + 1 for rank, result in enumerate(bm25_results)}
            knn_ranks = {result["id"]: rank + 1 for rank, result in enumerate(knn_results)}
            
            # Combine all unique documents
            all_docs = {}
            
            # Add BM25 results
            for result in bm25_results:
                doc_id = result["id"]
                all_docs[doc_id] = result
                all_docs[doc_id]["bm25_rank"] = bm25_ranks[doc_id]
                all_docs[doc_id]["knn_rank"] = None
            
            # Add k-NN results
            for result in knn_results:
                doc_id = result["id"]
                if doc_id in all_docs:
                    all_docs[doc_id]["knn_rank"] = knn_ranks[doc_id]
                else:
                    all_docs[doc_id] = result
                    all_docs[doc_id]["bm25_rank"] = None
                    all_docs[doc_id]["knn_rank"] = knn_ranks[doc_id]
            
            # Calculate RRF scores
            fused_results = []
            for doc_id, doc in all_docs.items():
                rrf_score = 0.0
                
                # BM25 component
                if doc["bm25_rank"] is not None:
                    rrf_score += self.rrf_bm25_weight * (1 / (self.rrf_k + doc["bm25_rank"]))
                
                # k-NN component  
                if doc["knn_rank"] is not None:
                    rrf_score += self.rrf_knn_weight * (1 / (self.rrf_k + doc["knn_rank"]))
                
                doc["rrf_score"] = rrf_score
                fused_results.append(doc)
            
            # Sort by RRF score and limit results
            fused_results.sort(key=lambda x: x["rrf_score"], reverse=True)
            
            logger.debug(f"RRF fusion combined {len(bm25_results)} BM25 + {len(knn_results)} k-NN = {len(fused_results)} unique results")
            
            return fused_results[:max_results]
            
        except Exception as e:
            logger.error(f"RRF fusion failed: {e}")
            # Fallback: return BM25 results
            return bm25_results[:max_results]
    
    async def _enhance_with_citations(
        self,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Enhance results with grounded citation metadata
        
        Citation format: {path, start, end, commit, tool, model}
        """
        try:
            enhanced_results = []
            
            for result in results:
                source = result["source"]
                
                # Build grounded citation
                citation = {
                    "path": source.get("path", ""),
                    "start": source.get("start", 0),
                    "end": source.get("end", 0),
                    "commit": source.get("commit", ""),
                    "tool": source.get("tool", "docxp-v1-hybrid-search"),
                    "model": getattr(settings, 'BEDROCK_MODEL_ID', 'claude-3-5-sonnet'),
                    "search_type": result.get("search_type", "hybrid"),
                    "confidence": result.get("rrf_score", result.get("score", 0))
                }
                
                # Enhance result with citation and metadata
                enhanced_result = {
                    "id": result["id"],
                    "content": source.get("content", ""),
                    "citation": citation,
                    "metadata": {
                        "repo_id": source.get("repo_id", ""),
                        "language": source.get("lang", ""),
                        "kind": source.get("kind", ""),
                        "content_hash": source.get("content_hash", ""),
                        "indexed_at": source.get("indexed_at", "")
                    },
                    "scores": {
                        "rrf_score": result.get("rrf_score", 0),
                        "bm25_rank": result.get("bm25_rank"),
                        "knn_rank": result.get("knn_rank"),
                        "original_score": result.get("score", 0)
                    },
                    "highlight": result.get("highlight", {}),
                    "search_context": {
                        "search_id": result.get("search_id", ""),
                        "timestamp": datetime.utcnow().isoformat(),
                        "fusion_params": {
                            "k": self.rrf_k,
                            "bm25_weight": self.rrf_bm25_weight,
                            "knn_weight": self.rrf_knn_weight
                        }
                    }
                }
                
                enhanced_results.append(enhanced_result)
            
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Citation enhancement failed: {e}")
            return results
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using Bedrock Titan model"""
        try:
            embed_model = getattr(settings, 'BEDROCK_EMBED_MODEL_ID', 'amazon.titan-embed-text-v2:0')
            
            payload = {
                "inputText": text,
                "dimensions": self.embedding_dimension,
                "normalize": True
            }
            
            response = self.bedrock_client.invoke_model(
                modelId=embed_model,
                contentType='application/json',
                accept='application/json',
                body=json.dumps(payload)
            )
            
            result = json.loads(response['body'].read().decode('utf-8'))
            return result['embedding']
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise
    
    def _build_filters(
        self,
        repo_filters: Optional[List[str]] = None,
        commit_filters: Optional[List[str]] = None,
        file_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Build OpenSearch filters for repository/commit/file type filtering"""
        filters = []
        
        if repo_filters:
            filters.append({"terms": {"repo_id": repo_filters}})
        
        if commit_filters:
            filters.append({"terms": {"commit": commit_filters}})
        
        if file_types:
            filters.append({"terms": {"lang": file_types}})
        
        return {"filter": filters} if filters else {}
    
    def _validate_performance(self, time_ms: float) -> Dict[str, Any]:
        """Validate search performance against SLOs"""
        meets_p50 = time_ms <= self.target_p50_ms
        meets_p95 = time_ms <= self.target_p95_ms
        
        status = {
            "meets_slo": meets_p50,  # Use p50 as primary SLO
            "meets_p50": meets_p50,
            "meets_p95": meets_p95,
            "time_ms": time_ms,
            "target_p50_ms": self.target_p50_ms,
            "target_p95_ms": self.target_p95_ms
        }
        
        if not meets_p50:
            logger.warning(f"⚠️  Search exceeded p50 SLO: {time_ms:.1f}ms > {self.target_p50_ms}ms")
        
        if not meets_p95:
            logger.warning(f"⚠️  Search exceeded p95 SLO: {time_ms:.1f}ms > {self.target_p95_ms}ms")
        
        return status
    
    async def repository_search(
        self,
        query: str,
        repo_id: str,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """Search within a specific repository"""
        return await self.hybrid_search(
            query=query,
            repo_filters=[repo_id],
            max_results=max_results
        )
    
    async def commit_search(
        self,
        query: str,
        commit_hash: str,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """Search within a specific commit"""
        return await self.hybrid_search(
            query=query,
            commit_filters=[commit_hash],
            max_results=max_results
        )
    
    async def golden_questions_search(
        self,
        question: str,
        expected_repos: Optional[List[str]] = None,
        max_results: int = 3
    ) -> Dict[str, Any]:
        """
        Search optimized for golden questions demo scenario
        
        Designed for questions like "Where does Specified Amount come from?"
        with grounded citations from SQL, JSP, and Struts files.
        """
        try:
            # Golden questions optimization: prefer code files
            file_types = ["java", "jsp", "sql", "xml", "js"]
            
            results = await self.hybrid_search(
                query=question,
                repo_filters=expected_repos,
                file_types=file_types,
                max_results=max_results,
                bm25_boost=1.5,  # Boost text matching for golden questions
                knn_boost=0.8    # Reduce semantic weight for precision
            )
            
            # Add golden question metadata
            results["golden_question"] = {
                "question": question,
                "expected_repos": expected_repos,
                "optimization": "code_files_preferred",
                "target_accuracy": "top_3_contains_answer"
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Golden questions search failed: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for hybrid search service"""
        try:
            # Test OpenSearch connection
            cluster_health = await self.opensearch_client.cluster.health()
            
            # Test Bedrock connection with a simple embedding
            test_embedding = await self._generate_embedding("health check test")
            
            return {
                "status": "healthy",
                "opensearch": {
                    "status": cluster_health["status"],
                    "cluster_name": cluster_health["cluster_name"]
                },
                "bedrock": {
                    "embedding_dimension": len(test_embedding),
                    "model": getattr(settings, 'BEDROCK_EMBED_MODEL_ID', 'titan-embed-text-v2')
                },
                "configuration": {
                    "rrf_k": self.rrf_k,
                    "bm25_weight": self.rrf_bm25_weight,
                    "knn_weight": self.rrf_knn_weight,
                    "target_p50_ms": self.target_p50_ms,
                    "target_p95_ms": self.target_p95_ms
                }
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Global service instance
hybrid_search_service = RRFHybridSearchService()

async def get_hybrid_search_service() -> RRFHybridSearchService:
    """Get hybrid search service instance"""
    return hybrid_search_service